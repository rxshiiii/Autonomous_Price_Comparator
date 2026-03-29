"""
Price Analytics model for storing price trend analysis and statistics.
"""
from datetime import date, datetime
from sqlalchemy import Column, Date, Numeric, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class PriceAnalytics(Base, IDMixin):
    """Model for storing price analysis and statistics."""

    __tablename__ = "price_analytics"

    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    min_price = Column(Numeric(12, 2), nullable=True)
    max_price = Column(Numeric(12, 2), nullable=True)
    avg_price = Column(Numeric(12, 2), nullable=True)
    trend = Column(String(10), nullable=True)  # up, down, stable
    views_count = Column(Integer, default=0, nullable=False)
    conversions_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    product = relationship("Product", backref="price_analytics")

    __table_args__ = (
        UniqueConstraint("product_id", "date", name="unique_price_analytics_product_date"),
        Index("idx_price_analytics_product_date", "product_id", "date", postgresql_using="btree"),
        Index("idx_price_analytics_trend", "trend", "date", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<PriceAnalytics(product_id={self.product_id}, date={self.date}, trend={self.trend})>"
