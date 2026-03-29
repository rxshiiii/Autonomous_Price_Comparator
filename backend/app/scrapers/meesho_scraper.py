"""
Meesho scraper implementation.

Scrapes products from Meesho.com (Indian reselling platform).
"""
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import re
import structlog

from app.scrapers.base_scraper import BaseScraper, ParsingError

logger = structlog.get_logger()


class MeeshoScraper(BaseScraper):
    """
    Meesho scraper for Indian e-commerce products.
    """

    def __init__(self):
        """Initialize Meesho scraper."""
        super().__init__(
            platform="meesho",
            base_url="https://www.meesho.com",
            rate_limit=10,  # 10 requests per minute
            use_proxy=False,
            retry_attempts=3,
            backoff_factor=2.0,
        )

    async def search_products(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for products on Meesho."""
        self.logger.info("searching_products", query=query, max_results=max_results)

        encoded_query = quote_plus(query)
        search_url = f"{self.base_url}/search?q={encoded_query}"

        try:
            html = await self.fetch_page(search_url)
            soup = self.parse_html(html)

            products = []

            # Meesho product cards
            product_cards = soup.select('[data-testid="productCard"]') or soup.select('div.sc-')

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
        """Parse a single product card from Meesho search results."""
        try:
            # Product URL
            link_elem = card.select_one('a')
            product_url = ""
            external_id = ""

            if link_elem:
                relative_url = link_elem.get('href', '')
                product_url = f"{self.base_url}{relative_url}"

                # Extract product ID from URL
                match = re.search(r'-p-(\d+)', relative_url)
                if match:
                    external_id = match.group(1)

            # Product name
            name_elem = card.select_one('[data-testid="productName"]') or card.select_one('h3')
            name = name_elem.get_text(strip=True) if name_elem else ""

            if not name:
                return None

            # Current price
            current_price = None
            price_elem = card.select_one('[data-testid="productPrice"]') or card.select_one('.sellingPrice')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Original price
            original_price = None
            original_elem = card.select_one('.originalPrice') or card.select_one('s')
            if original_elem:
                original_price_text = original_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)

            # Discount percentage
            discount_percentage = None
            if current_price and original_price and original_price > current_price:
                discount_percentage = ((original_price - current_price) / original_price) * 100

            # Image URL
            image_url = ""
            img_elem = card.select_one('img')
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')

            # Rating
            rating = None
            rating_elem = card.select_one('.rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text.split()[0])
                except (ValueError, TypeError, IndexError):
                    pass

            # Reviews count
            reviews_count = None
            reviews_elem = card.select_one('.reviewCount')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_count = self._extract_number(reviews_text)

            return {
                "external_id": external_id or f"meesho_{hash(name)}",
                "platform": "meesho",
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
            name_elem = soup.select_one('h1') or soup.select_one('[data-testid="productName"]')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Current price
            current_price = None
            price_elem = soup.select_one('.sellingPrice')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            return {
                "name": name,
                "current_price": current_price,
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
