"""
Proxy Manager for rotating proxies to avoid IP bans.
"""
import random
from typing import Optional, List
import structlog

from app.config import settings

logger = structlog.get_logger()


class ProxyManager:
    """
    Manages proxy rotation for web scraping.

    Supports:
    - Multiple proxy providers
    - Proxy rotation (round-robin or random)
    - Proxy health tracking (future)
    """

    def __init__(self):
        """Initialize proxy manager with proxy list."""
        self.proxies: List[str] = []
        self.current_index = 0

        # Load proxies from environment or configuration
        if settings.PROXY_URL:
            self.proxies.append(settings.PROXY_URL)

        # You can add more proxies here or load from a file
        # Example:
        # self.proxies = [
        #     "http://proxy1.example.com:8080",
        #     "http://proxy2.example.com:8080",
        #     "http://proxy3.example.com:8080",
        # ]

        self.logger = logger.bind(proxy_count=len(self.proxies))

        if self.proxies:
            self.logger.info("proxy_manager_initialized")
        else:
            self.logger.warning("no_proxies_configured")

    async def get_proxy(self) -> Optional[str]:
        """
        Get a proxy from the pool.

        Returns:
            Proxy URL or None if no proxies available
        """
        if not self.proxies:
            return None

        # Random selection
        proxy = random.choice(self.proxies)

        self.logger.debug("proxy_selected", proxy=self._mask_proxy(proxy))

        return proxy

    def get_next_proxy(self) -> Optional[str]:
        """
        Get the next proxy in sequence (round-robin).

        Returns:
            Proxy URL or None if no proxies available
        """
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)

        return proxy

    def add_proxy(self, proxy_url: str):
        """
        Add a proxy to the pool.

        Args:
            proxy_url: Proxy URL (e.g., "http://user:pass@host:port")
        """
        if proxy_url not in self.proxies:
            self.proxies.append(proxy_url)
            self.logger.info("proxy_added", total_proxies=len(self.proxies))

    def remove_proxy(self, proxy_url: str):
        """
        Remove a proxy from the pool.

        Args:
            proxy_url: Proxy URL to remove
        """
        if proxy_url in self.proxies:
            self.proxies.remove(proxy_url)
            self.logger.info("proxy_removed", total_proxies=len(self.proxies))

    def _mask_proxy(self, proxy: str) -> str:
        """
        Mask sensitive information in proxy URL for logging.

        Args:
            proxy: Proxy URL

        Returns:
            Masked proxy URL
        """
        if "@" in proxy:
            # Format: http://user:pass@host:port
            protocol, rest = proxy.split("://")
            auth, server = rest.split("@")
            return f"{protocol}://***:***@{server}"
        return proxy

    def get_proxy_count(self) -> int:
        """
        Get the number of proxies in the pool.

        Returns:
            Number of proxies
        """
        return len(self.proxies)

    def has_proxies(self) -> bool:
        """
        Check if any proxies are configured.

        Returns:
            True if proxies are available
        """
        return len(self.proxies) > 0
