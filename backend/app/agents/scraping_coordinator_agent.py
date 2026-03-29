"""
Scraping Coordinator Agent for intelligent product scraping orchestration.
"""
from typing import List, Dict, Any
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.models.product import Product
from app.models.price_alert import PriceAlert
import structlog


logger = structlog.get_logger()


class ScrapingCoordinatorAgent(BaseAgent):
    """Agent for coordinating multi-platform web scraping."""

    def __init__(self, db: AsyncSession):
        """Initialize scraping coordinator agent."""
        super().__init__()
        self.db = db
        self.logger = logger.bind(agent="scraping_coordinator")

    async def run(self) -> Dict[str, Any]:
        """Execute scraping coordination workflow."""
        self.logger.info("scraping_coordinator_started")

        try:
            # Fetch products that haven't been scraped recently (>2 hours)
            from datetime import datetime, timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=2)

            result = await self.db.execute(
                select(Product)
                .where(
                    and_(
                        Product.last_scraped_at < cutoff_time
                    )
                )
                .order_by(desc(Product.created_at))
                .limit(100)
            )
            stale_products = result.scalars().all()

            # Fetch products with active alerts (prioritize)
            result = await self.db.execute(
                select(Product)
                .join(PriceAlert, Product.id == PriceAlert.product_id)
                .where(PriceAlert.is_active == True)
                .distinct()
                .limit(50)
            )
            high_priority_products = result.scalars().all()

            # Prioritize by platform
            products_by_platform = self._group_by_platform(stale_products + high_priority_products)

            self.logger.info(
                "products_prioritized",
                platforms=list(products_by_platform.keys()),
                total=len(stale_products) + len(high_priority_products)
            )

            return {
                "status": "completed",
                "products_by_platform": {
                    platform: len(products)
                    for platform, products in products_by_platform.items()
                },
                "total_products": len(stale_products) + len(high_priority_products),
            }

        except Exception as e:
            self.logger.error("scraping_coordinator_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    def _group_by_platform(self, products: List[Product]) -> Dict[str, List[Product]]:
        """Group products by platform."""
        grouped: Dict[str, List[Product]] = {
            "flipkart": [],
            "amazon": [],
            "myntra": [],
            "meesho": [],
        }

        for product in products:
            platform = product.platform.lower()
            if platform in grouped:
                grouped[platform].append(product)

        return grouped
