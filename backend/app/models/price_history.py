"""
Price history model for tracking product price changes over time.
"""
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class PriceHistory(Base, IDMixin):
    """Price history model for tracking price changes."""

    __tablename__ = "price_history"

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    discount_percentage = Column(Numeric(5, 2))
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = Column(String(50))  # scraping_job_id or "manual"

    # Relationships
    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index("idx_price_history_product_time", "product_id", "recorded_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, recorded_at={self.recorded_at})>"
