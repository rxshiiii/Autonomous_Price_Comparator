"""
Amazon scraper implementation.

Note: Amazon has strong anti-bot measures. This scraper:
- Uses Playwright for JavaScript rendering
- Requires more sophisticated anti-detection measures in production
- Currently implements basic search functionality
"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import re
import structlog

from app.scrapers.base_scraper import BaseScraper, ParsingError

logger = structlog.get_logger()


class AmazonScraper(BaseScraper):
    """
    Amazon scraper. Amazon requires more sophisticated anti-bot measures.

    Note: This is a basic implementation. Production use requires:
    - Playwright with browser fingerprinting
    - Residential proxies
    - CAPTCHA solving service
    """

    def __init__(self):
        """Initialize Amazon scraper."""
        super().__init__(
            platform="amazon",
            base_url="https://www.amazon.in",
            rate_limit=5,  # 5 requests per minute (more restrictive)
            use_proxy=True,  # Amazon is more strict
            retry_attempts=5,
            backoff_factor=3.0,
        )

    async def search_products(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of product dictionaries
        """
        self.logger.info("searching_products", query=query, max_results=max_results)

        encoded_query = quote_plus(query)
        search_url = f"{self.base_url}/s?k={encoded_query}"

        try:
            html = await self.fetch_page(search_url)
            soup = self.parse_html(html)

            products = []

            # Amazon product cards have data-asin attribute
            product_cards = soup.select('[data-asin]:not([data-asin=""])')

            self.logger.info("product_cards_found", count=len(product_cards))

            for card in product_cards[:max_results]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                        self.stats["products_scraped"] += 1
                except Exception as e:
                    self.logger.warning("failed_to_parse_card", error=str(e))
                    continue

            self.logger.info("search_completed", query=query, products_found=len(products))

            return products

        except Exception as e:
            self.logger.error("search_failed", query=query, error=str(e))
            raise ParsingError(f"Failed to search products: {str(e)}")

    async def _parse_product_card(self, card) -> Optional[Dict[str, Any]]:
        """Parse a single product card from Amazon search results."""
        try:
            # ASIN (Amazon Standard Identification Number)
            external_id = card.get('data-asin', '')

            if not external_id:
                return None

            # Product name
            name_elem = card.select_one('h2 a span') or card.select_one('.a-text-normal')
            name = name_elem.get_text(strip=True) if name_elem else ""

            if not name:
                return None

            # Product URL
            link_elem = card.select_one('h2 a')
            product_url = ""
            if link_elem:
                relative_url = link_elem.get('href', '')
                product_url = f"{self.base_url}{relative_url}"

            # Current price
            current_price = None
            price_elem = card.select_one('.a-price .a-offscreen')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Original price
            original_price = None
            original_elem = card.select_one('.a-price.a-text-price .a-offscreen')
            if original_elem:
                original_price_text = original_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)

            # Image URL
            image_url = ""
            img_elem = card.select_one('img.s-image')
            if img_elem:
                image_url = img_elem.get('src', '')

            # Rating
            rating = None
            rating_elem = card.select_one('.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    try:
                        rating = float(match.group(1))
                    except (ValueError, TypeError):
                        pass

            # Reviews count
            reviews_count = None
            reviews_elem = card.select_one('.a-size-base.s-underline-text')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_count = self._extract_number(reviews_text)

            # Calculate discount
            discount_percentage = None
            if current_price and original_price and original_price > current_price:
                discount_percentage = ((original_price - current_price) / original_price) * 100

            return {
                "external_id": external_id,
                "platform": "amazon",
                "name": name,
                "description": None,
                "category": None,
                "brand": None,
                "image_url": image_url,
                "product_url": product_url,
                "current_price": current_price,
                "original_price": original_price or current_price,
                "discount_percentage": discount_percentage,
                "rating": rating,
                "reviews_count": reviews_count,
                "availability": "in_stock",
            }

        except Exception as e:
            self.logger.warning("card_parsing_error", error=str(e))
            return None

    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific product."""
        self.logger.info("fetching_product_details", url=product_url)

        try:
            html = await self.fetch_page(product_url)
            soup = self.parse_html(html)

            # Product name
            name_elem = soup.select_one('#productTitle')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Current price
            current_price = None
            price_elem = soup.select_one('.a-price .a-offscreen')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Description
            description_elem = soup.select_one('#feature-bullets')
            description = description_elem.get_text(strip=True) if description_elem else None

            # Rating
            rating = None
            rating_elem = soup.select_one('.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    try:
                        rating = float(match.group(1))
                    except (ValueError, TypeError):
                        pass

            return {
                "name": name,
                "description": description,
                "current_price": current_price,
                "rating": rating,
                "product_url": product_url,
            }

        except Exception as e:
            self.logger.error("product_details_failed", url=product_url, error=str(e))
            raise ParsingError(f"Failed to fetch product details: {str(e)}")

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not text:
            return None

        # Remove currency symbols, commas, and whitespace
        price_str = re.sub(r'[₹Rs.,\s]', '', text)

        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None

    def _extract_number(self, text: str) -> Optional[int]:
        """Extract number from text."""
        if not text:
            return None

        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            try:
                return int(''.join(numbers))
            except (ValueError, TypeError):
                pass

        return None
