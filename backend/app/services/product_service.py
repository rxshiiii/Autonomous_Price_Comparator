"""
Product service for business logic.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.product import Product
from app.models.price_history import PriceHistory
from app.schemas.product import ProductCreate, ProductResponse

logger = structlog.get_logger()


class ProductService:
    """Service for product operations."""

    def __init__(self, db: AsyncSession):
        """Initialize product service."""
        self.db = db
        self.logger = logger.bind(service="product_service")

    async def search_products(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        platforms: Optional[List[str]] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
    ) -> tuple[List[Product], int]:
        """
        Search for products by query and filters.

        Args:
            query: Search query
            limit: Number of results
            offset: Pagination offset
            platforms: Filter by platforms
            min_price: Minimum price filter
            max_price: Maximum price filter

        Returns:
            Tuple of (products, total_count)
        """
        self.logger.info("searching_products", query=query, limit=limit)

        filters = []

        # Full-text search on product name
        if query:
            from sqlalchemy import func
            filters.append(
                func.to_tsvector("english", Product.name).match(
                    func.plainto_tsquery("english", query)
                )
            )

        # Platform filter
        if platforms:
            filters.append(Product.platform.in_(platforms))

        # Price range filter
        if min_price is not None:
            filters.append(Product.current_price >= min_price)
        if max_price is not None:
            filters.append(Product.current_price <= max_price)

        # Count total results
        count_query = select(func.count(Product.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Fetch products
        query_stmt = select(Product)
        if filters:
            query_stmt = query_stmt.where(and_(*filters))

        query_stmt = (
            query_stmt
            .order_by(desc(Product.rating), desc(Product.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query_stmt)
        products = result.scalars().all()

        self.logger.info(
            "search_completed",
            query=query,
            results=len(products),
            total=total_count
        )

        return products, total_count

    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get a product by ID."""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_product_by_external_id(
        self,
        external_id: str,
        platform: str
    ) -> Optional[Product]:
        """Get a product by external ID and platform."""
        result = await self.db.execute(
            select(Product).where(
                and_(
                    Product.external_id == external_id,
                    Product.platform == platform
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_product(
        self,
        product_data: ProductCreate
    ) -> Product:
        """Create a new product."""
        # Check if product already exists
        existing = await self.get_product_by_external_id(
            product_data.external_id,
            product_data.platform
        )

        if existing:
            self.logger.warning(
                "product_already_exists",
                external_id=product_data.external_id,
                platform=product_data.platform
            )
            return existing

        # Create new product
        product = Product(**product_data.model_dump(), last_scraped_at=datetime.utcnow())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)

        self.logger.info("product_created", product_id=product.id, name=product.name)

        return product

    async def update_product(
        self,
        product_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Product]:
        """Update a product."""
        product = await self.get_product_by_id(product_id)

        if not product:
            return None

        for key, value in update_data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(product)

        self.logger.info("product_updated", product_id=product_id)

        return product

    async def get_price_history(
        self,
        product_id: UUID,
        days: int = 30
    ) -> List[PriceHistory]:
        """Get price history for a product."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(PriceHistory)
            .where(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.recorded_at >= cutoff_date
                )
            )
            .order_by(PriceHistory.recorded_at)
        )

        return result.scalars().all()

    async def get_price_statistics(self, product_id: UUID) -> Dict[str, Any]:
        """Get price statistics for a product."""
        histories = await self.get_price_history(product_id, days=90)

        if not histories:
            return {
                "lowest_price": None,
                "highest_price": None,
                "average_price": None,
                "current_trend": None,
            }

        prices = [float(h.price) for h in histories]

        lowest = min(prices)
        highest = max(prices)
        average = sum(prices) / len(prices)

        # Determine trend (price up or down)
        if len(prices) > 1:
            trend = "up" if prices[-1] > prices[0] else "down"
        else:
            trend = "stable"

        return {
            "lowest_price": Decimal(str(lowest)),
            "highest_price": Decimal(str(highest)),
            "average_price": Decimal(str(average)),
            "current_trend": trend,
            "days_tracked": len(histories),
        }

    async def get_products_by_category(
        self,
        category: str,
        limit: int = 20
    ) -> List[Product]:
        """Get products by category."""
        result = await self.db.execute(
            select(Product)
            .where(Product.category == category)
            .order_by(desc(Product.rating))
            .limit(limit)
        )

        return result.scalars().all()

    async def get_trending_products(self, limit: int = 10) -> List[Product]:
        """Get trending products based on ratings and reviews."""
        result = await self.db.execute(
            select(Product)
            .where(Product.reviews_count > 0)
            .order_by(
                desc(Product.rating),
                desc(Product.reviews_count)
            )
            .limit(limit)
        )

        return result.scalars().all()

    async def compare_products_across_platforms(
        self,
        query: str
    ) -> Dict[str, List[Product]]:
        """Get the same product across different platforms for price comparison."""
        products_by_platform = {}

        platforms = ["flipkart", "amazon", "myntra", "meesho"]

        for platform in platforms:
            result = await self.db.execute(
                select(Product)
                .where(
                    and_(
                        Product.platform == platform,
                        Product.name.ilike(f"%{query}%")
                    )
                )
                .limit(5)
            )

            products_by_platform[platform] = result.scalars().all()

        return products_by_platform
