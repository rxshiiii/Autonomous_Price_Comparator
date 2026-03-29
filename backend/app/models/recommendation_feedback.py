"""
Recommendation Feedback model for tracking user interactions with recommendations.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class RecommendationFeedback(Base, IDMixin):
    """Model for tracking user feedback on recommendations."""

    __tablename__ = "recommendation_feedback"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(20), nullable=False)  # viewed, clicked, ignored, purchased
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="recommendation_feedbacks")
    recommendation = relationship("Recommendation", backref="feedbacks")

    __table_args__ = (
        UniqueConstraint("user_id", "recommendation_id", "action", name="unique_recommendation_feedback"),
        Index("idx_recommendation_feedback_user_action", "user_id", "action", "created_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<RecommendationFeedback(user_id={self.user_id}, action={self.action})>"
