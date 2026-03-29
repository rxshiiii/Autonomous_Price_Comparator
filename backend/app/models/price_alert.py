"""
Price alert model for user price notifications.
"""
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin, TimestampMixin


class PriceAlert(Base, IDMixin, TimestampMixin):
    """Price alert model for notifying users about price changes."""

    __tablename__ = "price_alerts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    target_price = Column(Numeric(10, 2), nullable=False)
    alert_type = Column(String(50), default="below_price")  # below_price, percentage_drop, back_in_stock
    threshold_percentage = Column(Numeric(5, 2))  # For percentage_drop type
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="price_alerts")
    product = relationship("Product", back_populates="price_alerts")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "is_active", name="unique_active_alert"),
    )

    def __repr__(self):
        return f"<PriceAlert(user_id={self.user_id}, product_id={self.product_id}, target_price={self.target_price})>"
