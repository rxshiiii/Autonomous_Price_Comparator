"""
Base scraper class with retry logic, rate limiting, and error handling.
All platform-specific scrapers inherit from this class.
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import structlog

from app.scrapers.utils.user_agent_rotator import UserAgentRotator
from app.scrapers.utils.rate_limiter import RateLimiter
from app.scrapers.utils.proxy_manager import ProxyManager

logger = structlog.get_logger()


class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class RateLimitError(ScraperError):
    """Raised when rate limit is exceeded."""
    pass


class ParsingError(ScraperError):
    """Raised when parsing fails."""
    pass


class BaseScraper(ABC):
    """
    Abstract base class for all platform scrapers.

    Provides common functionality:
    - HTTP client with retry logic
    - Rate limiting
    - User agent rotation
    - Proxy support
    - Error handling
    - Logging
    """

    def __init__(
        self,
        platform: str,
        base_url: str,
        rate_limit: int = 10,  # requests per minute
        use_proxy: bool = False,
        retry_attempts: int = 3,
        backoff_factor: float = 2.0,
    ):
        """
        Initialize base scraper.

        Args:
            platform: Platform name (flipkart, amazon, myntra, meesho)
            base_url: Base URL for the platform
            rate_limit: Max requests per minute
            use_proxy: Whether to use proxy rotation
            retry_attempts: Max retry attempts on failure
            backoff_factor: Exponential backoff multiplier
        """
        self.platform = platform
        self.base_url = base_url
        self.retry_attempts = retry_attempts
        self.backoff_factor = backoff_factor

        # Initialize utilities
        self.user_agent_rotator = UserAgentRotator()
        self.rate_limiter = RateLimiter(platform, rate_limit)
        self.proxy_manager = ProxyManager() if use_proxy else None

        # HTTP client
        self.client: Optional[httpx.AsyncClient] = None

        # Statistics
        self.stats = {
            "requests_made": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "products_scraped": 0,
            "errors": []
        }

        self.logger = logger.bind(platform=platform)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize HTTP client."""
        headers = {
            "User-Agent": self.user_agent_rotator.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )

        self.logger.info("scraper_initialized", base_url=self.base_url)

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.logger.info(
                "scraper_closed",
                stats=self.stats
            )

    async def fetch_page(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> str:
        """
        Fetch a page with retry logic and rate limiting.

        Args:
            url: URL to fetch
            method: HTTP method (GET, POST)
            params: Query parameters
            data: Request body data

        Returns:
            HTML content as string

        Raises:
            ScraperError: On failure after all retries
        """
        # Check rate limit
        await self.rate_limiter.acquire()

        for attempt in range(1, self.retry_attempts + 1):
            try:
                # Rotate user agent
                if self.client:
                    self.client.headers["User-Agent"] = self.user_agent_rotator.get_random()

                # Get proxy if enabled
                proxy = None
                if self.proxy_manager:
                    proxy = await self.proxy_manager.get_proxy()

                # Make request
                self.logger.info(
                    "fetching_page",
                    url=url,
                    attempt=attempt,
                    proxy=proxy is not None
                )

                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    proxy=proxy
                )

                # Update statistics
                self.stats["requests_made"] += 1

                # Handle response
                if response.status_code == 200:
                    self.stats["requests_successful"] += 1
                    self.logger.info("page_fetched_successfully", url=url)
                    return response.text

                elif response.status_code == 429:
                    # Rate limited
                    self.logger.warning("rate_limited", url=url, attempt=attempt)
                    await self._backoff(attempt)
                    continue

                elif response.status_code in [500, 502, 503, 504]:
                    # Server error - retry
                    self.logger.warning(
                        "server_error",
                        url=url,
                        status_code=response.status_code,
                        attempt=attempt
                    )
                    await self._backoff(attempt)
                    continue

                else:
                    # Other error
                    self.stats["requests_failed"] += 1
                    raise ScraperError(
                        f"HTTP {response.status_code}: {url}"
                    )

            except httpx.TimeoutException:
                self.logger.warning("request_timeout", url=url, attempt=attempt)
                if attempt < self.retry_attempts:
                    await self._backoff(attempt)
                    continue
                raise ScraperError(f"Timeout after {self.retry_attempts} attempts: {url}")

            except httpx.NetworkError as e:
                self.logger.warning("network_error", url=url, error=str(e), attempt=attempt)
                if attempt < self.retry_attempts:
                    await self._backoff(attempt)
                    continue
                raise ScraperError(f"Network error: {url}")

            except Exception as e:
                self.stats["requests_failed"] += 1
                self.stats["errors"].append({
                    "url": url,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                self.logger.error("unexpected_error", url=url, error=str(e))
                raise ScraperError(f"Unexpected error: {url} - {str(e)}")

        # All retries exhausted
        self.stats["requests_failed"] += 1
        raise ScraperError(f"Failed after {self.retry_attempts} attempts: {url}")

    async def _backoff(self, attempt: int):
        """
        Exponential backoff with jitter.

        Args:
            attempt: Current attempt number
        """
        delay = (self.backoff_factor ** attempt) + random.uniform(0, 1)
        self.logger.info("backoff_delay", delay=delay, attempt=attempt)
        await asyncio.sleep(delay)

    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html: HTML content as string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def search_products(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for products on the platform.

        Args:
            query: Search query (e.g., "Jordan shoes")
            max_results: Maximum number of results to return

        Returns:
            List of product dictionaries with keys:
            - external_id: Platform-specific product ID
            - name: Product name
            - price: Current price
            - original_price: Original price (if available)
            - discount_percentage: Discount percentage
            - image_url: Product image URL
            - product_url: Product page URL
            - rating: Product rating
            - reviews_count: Number of reviews
            - availability: Stock status
        """
        pass

    @abstractmethod
    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.

        Args:
            product_url: URL of the product page

        Returns:
            Dictionary with detailed product information
        """
        pass

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scraping statistics.

        Returns:
            Dictionary with scraping statistics
        """
        return self.stats.copy()
