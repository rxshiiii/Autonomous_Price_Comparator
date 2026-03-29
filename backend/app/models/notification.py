"""
Notification model for user notifications.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin, TimestampMixin


class Notification(Base, IDMixin, TimestampMixin):
    """Notification model for user notifications."""

    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # price_drop, recommendation, back_in_stock
    title = Column(String(255), nullable=False)
    message = Column(Text)
    data = Column(JSONB)  # Additional structured data
    is_read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notifications_user_unread", "user_id", "is_read", "created_at", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, type={self.notification_type}, title={self.title})>"
