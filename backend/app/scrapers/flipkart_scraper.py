"""
Flipkart scraper implementation.

Scrapes product data from Flipkart.com using BeautifulSoup.
"""
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
import structlog

from app.scrapers.base_scraper import BaseScraper, ParsingError

logger = structlog.get_logger()


class FlipkartScraper(BaseScraper):
    """
    Flipkart scraper using BeautifulSoup for HTML parsing.

    Flipkart is relatively scraper-friendly and doesn't heavily
    rely on JavaScript rendering.
    """

    def __init__(self):
        """Initialize Flipkart scraper."""
        super().__init__(
            platform="flipkart",
            base_url="https://www.flipkart.com",
            rate_limit=10,  # 10 requests per minute
            use_proxy=False,  # Flipkart is less strict
            retry_attempts=3,
            backoff_factor=2.0,
        )

    async def search_products(
        self,
        query: str,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for products on Flipkart.

        Args:
            query: Search query (e.g., "Jordan shoes")
            max_results: Maximum number of results to return

        Returns:
            List of product dictionaries
        """
        self.logger.info("searching_products", query=query, max_results=max_results)

        # Construct search URL
        encoded_query = quote_plus(query)
        search_url = f"{self.base_url}/search?q={encoded_query}"

        try:
            # Fetch search page
            html = await self.fetch_page(search_url)
            soup = self.parse_html(html)

            products = []

            # Find all product cards
            # Flipkart uses different class names, so we try multiple selectors
            product_cards = soup.select('div[data-id]') or soup.select('div._1AtVbE')

            self.logger.info("product_cards_found", count=len(product_cards))

            for card in product_cards[:max_results]:
                try:
                    product = await self._parse_product_card(card)
                    if product:
                        products.append(product)
                        self.stats["products_scraped"] += 1
                except Exception as e:
                    self.logger.warning(
                        "failed_to_parse_card",
                        error=str(e)
                    )
                    continue

            self.logger.info(
                "search_completed",
                query=query,
                products_found=len(products)
            )

            return products

        except Exception as e:
            self.logger.error("search_failed", query=query, error=str(e))
            raise ParsingError(f"Failed to search products: {str(e)}")

    async def _parse_product_card(self, card) -> Optional[Dict[str, Any]]:
        """
        Parse a single product card from search results.

        Args:
            card: BeautifulSoup element representing a product card

        Returns:
            Product dictionary or None if parsing fails
        """
        try:
            # Extract product ID (data-id attribute)
            external_id = card.get('data-id', '')

            # Product name
            name_elem = card.select_one('div._4rR01T') or card.select_one('a.s1Q9rs')
            name = name_elem.get_text(strip=True) if name_elem else ""

            if not name:
                return None

            # Product URL
            link_elem = card.select_one('a[href]')
            product_url = ""
            if link_elem:
                relative_url = link_elem.get('href', '')
                product_url = urljoin(self.base_url, relative_url)

            # Current price
            current_price = None
            price_elem = card.select_one('div._30jeq3') or card.select_one('div._3I9_wc')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Original price (if discounted)
            original_price = None
            original_price_elem = card.select_one('div._3I9_wc._27UcVY')
            if original_price_elem:
                original_price_text = original_price_elem.get_text(strip=True)
                original_price = self._extract_price(original_price_text)

            # Discount percentage
            discount_percentage = None
            discount_elem = card.select_one('div._3Ay6Sb') or card.select_one('div._3jtDlsW')
            if discount_elem:
                discount_text = discount_elem.get_text(strip=True)
                discount_percentage = self._extract_discount(discount_text)

            # Image URL
            image_url = ""
            img_elem = card.select_one('img')
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')

            # Rating
            rating = None
            rating_elem = card.select_one('div._3LWZlK')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except (ValueError, TypeError):
                    pass

            # Reviews count
            reviews_count = None
            reviews_elem = card.select_one('span._2_R_DZ')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_count = self._extract_number(reviews_text)

            return {
                "external_id": external_id or f"flipkart_{hash(name)}",
                "platform": "flipkart",
                "name": name,
                "description": None,  # Not available in search results
                "category": None,  # Can be extracted from breadcrumbs in detail page
                "brand": self._extract_brand(name),
                "image_url": image_url,
                "product_url": product_url,
                "current_price": current_price,
                "original_price": original_price or current_price,
                "discount_percentage": discount_percentage,
                "rating": rating,
                "reviews_count": reviews_count,
                "availability": "in_stock",  # Assume in stock if showing in search
            }

        except Exception as e:
            self.logger.warning("card_parsing_error", error=str(e))
            return None

    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.

        Args:
            product_url: URL of the product page

        Returns:
            Dictionary with detailed product information
        """
        self.logger.info("fetching_product_details", url=product_url)

        try:
            html = await self.fetch_page(product_url)
            soup = self.parse_html(html)

            # Product name
            name_elem = soup.select_one('span.B_NuCI') or soup.select_one('h1.yhB1nd')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # Current price
            current_price = None
            price_elem = soup.select_one('div._30jeq3') or soup.select_one('div._16Jk6d')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                current_price = self._extract_price(price_text)

            # Description
            description_elem = soup.select_one('div._1mXcCf') or soup.select_one('div._1AN87F')
            description = description_elem.get_text(strip=True) if description_elem else None

            # Rating
            rating = None
            rating_elem = soup.select_one('div._3LWZlK')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                try:
                    rating = float(rating_text)
                except (ValueError, TypeError):
                    pass

            # Reviews count
            reviews_count = None
            reviews_elem = soup.select_one('span._2_R_DZ')
            if reviews_elem:
                reviews_text = reviews_elem.get_text(strip=True)
                reviews_count = self._extract_number(reviews_text)

            # Category (from breadcrumb)
            category = None
            breadcrumb_elem = soup.select('a._1QZ6fC')
            if breadcrumb_elem and len(breadcrumb_elem) > 0:
                category = breadcrumb_elem[-1].get_text(strip=True)

            return {
                "name": name,
                "description": description,
                "category": category,
                "current_price": current_price,
                "rating": rating,
                "reviews_count": reviews_count,
                "product_url": product_url,
            }

        except Exception as e:
            self.logger.error("product_details_failed", url=product_url, error=str(e))
            raise ParsingError(f"Failed to fetch product details: {str(e)}")

    def _extract_price(self, text: str) -> Optional[float]:
        """
        Extract numeric price from text.

        Args:
            text: Price text (e.g., "₹1,299", "Rs. 2,499")

        Returns:
            Price as float or None
        """
        if not text:
            return None

        # Remove currency symbols and commas
        price_str = re.sub(r'[₹Rs.,\s]', '', text)

        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None

    def _extract_discount(self, text: str) -> Optional[float]:
        """
        Extract discount percentage from text.

        Args:
            text: Discount text (e.g., "20% off", "50%")

        Returns:
            Discount as float or None
        """
        if not text:
            return None

        # Extract number followed by %
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                pass

        return None

    def _extract_number(self, text: str) -> Optional[int]:
        """
        Extract number from text (for reviews count, etc.).

        Args:
            text: Text containing a number

        Returns:
            Number as int or None
        """
        if not text:
            return None

        # Remove commas and extract numbers
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            try:
                return int(''.join(numbers))
            except (ValueError, TypeError):
                pass

        return None

    def _extract_brand(self, name: str) -> Optional[str]:
        """
        Extract brand from product name.

        Args:
            name: Product name

        Returns:
            Brand name or None
        """
        if not name:
            return None

        # Simple extraction: first word is often the brand
        words = name.split()
        if words:
            return words[0]

        return None
