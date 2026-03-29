"""
User Notification Preferences model for customizing notification behavior.
"""
from datetime import time, datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, Time, ForeignKey, UniqueConstraint, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class UserNotificationPreferences(Base, IDMixin):
    """Model for user notification preferences."""

    __tablename__ = "user_notification_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    max_notifications_per_day = Column(Integer, default=5, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    websocket_enabled = Column(Boolean, default=True, nullable=False)
    price_drop_threshold_percentage = Column(Numeric(5, 2), default=10, nullable=False)  # Minimum % drop to notify
    notification_quiet_hours_start = Column(Time, default=time(22, 0), nullable=False)  # 22:00
    notification_quiet_hours_end = Column(Time, default=time(9, 0), nullable=False)  # 09:00
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notification_preferences")

    __table_args__ = (
        UniqueConstraint("user_id", name="user_notification_preferences_user_id_unique"),
        Index("idx_user_notification_preferences_user", "user_id", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<UserNotificationPreferences(user_id={self.user_id})>"
