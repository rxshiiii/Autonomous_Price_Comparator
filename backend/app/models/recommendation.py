"""
Recommendation model for AI-generated product recommendations.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class Recommendation(Base, IDMixin):
    """Recommendation model for storing AI-generated product recommendations."""

    __tablename__ = "recommendations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    reasoning = Column(Text)  # Why this product was recommended
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    shown_to_user = Column(Boolean, default=False, nullable=False)
    user_action = Column(String(50))  # viewed, clicked, purchased, ignored

    # Relationships
    user = relationship("User", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", "generated_at", name="unique_recommendation"),
        Index("idx_recommendations_user_score", "user_id", "score", "generated_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<Recommendation(user_id={self.user_id}, product_id={self.product_id}, score={self.score})>"
