"""
Myntra scraper implementation.

Scrapes fashion products from Myntra.com.
"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import re
import structlog

from app.scrapers.base_scraper import BaseScraper, ParsingError

logger = structlog.get_logger()


class MyntraScraper(BaseScraper):
    """
    Myntra scraper for fashion products.
    """

    def __init__(self):
        """Initialize Myntra scraper."""
        super().__init__(
            platform="myntra",
            base_url="https://www.myntra.com",
            rate_limit=8,  # 8 requests per minute
            use_proxy=False,
            retry_attempts=3,
            backoff_factor=2.0,
        )

    async def search_products(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for products on Myntra."""
        self.logger.info("searching_products", query=query, max_results=max_results)

        encoded_query = quote_plus(query)
        search_url = f"{self.base_url}/{encoded_query}"

        try:
            html = await self.fetch_page(search_url)
            soup = self.parse_html(html)

            products = []

            # Myntra uses different class names
            product_cards = soup.select('li.product-base')

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
        """Parse a single product card from Myntra search results."""
        try:
            # Product URL to extract ID
            link_elem = card.select_one('a')
            product_url = ""
            external_id = ""

            if link_elem:
                relative_url = link_elem.get('href', '')
                product_url = f"{self.base_url}/{relative_url}"

                # Extract product ID from URL
                match = re.search(r'/(\d+)/buy', relative_url)
                if match:
                    external_id = match.group(1)

            # Product name
            name_elem = card.select_one('.product-product')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Brand
            brand_elem = card.select_one('.product-brand')
            brand = brand_elem.get_text(strip=True) if brand_elem else None

            if not name:
                return None

            # Current price
            current_price = None
            price_elem = card.select_one('.product-discountedPrice')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Original price
            original_price = None
            original_elem = card.select_one('.product-strike')
            if original_elem:
                original_price_text = original_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)

            # Discount percentage
            discount_percentage = None
            discount_elem = card.select_one('.product-discountPercentage')
            if discount_elem:
                discount_text = discount_elem.get_text(strip=True)
                discount_percentage = self._extract_discount(discount_text)

            # Image URL
            image_url = ""
            img_elem = card.select_one('img')
            if img_elem:
                image_url = img_elem.get('src', '')

            # Rating
            rating = None
            rating_elem = card.select_one('.product-rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except (ValueError, TypeError):
                    pass

            # Reviews count
            reviews_count = None
            reviews_elem = card.select_one('.product-ratingCount')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_count = self._extract_number(reviews_text)

            return {
                "external_id": external_id or f"myntra_{hash(name)}",
                "platform": "myntra",
                "name": name,
                "description": None,
                "category": "Fashion",  # Myntra is fashion-focused
                "brand": brand,
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

            # Basic details extraction (Myntra's detail page structure)
            name_elem = soup.select_one('.pdp-title')
            name = name_elem.get_text(strip=True) if name_elem else ""

            return {
                "name": name,
                "product_url": product_url,
            }

        except Exception as e:
            self.logger.error("product_details_failed", url=product_url, error=str(e))
            raise ParsingError(f"Failed to fetch product details: {str(e)}")

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract numeric price from text."""
        if not text:
            return None

        price_str = re.sub(r'[₹Rs.,\s]', '', text)

        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None

    def _extract_discount(self, text: str) -> Optional[float]:
        """Extract discount percentage from text."""
        if not text:
            return None

        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                pass

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
