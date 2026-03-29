"""
Onboarding model for tracking user onboarding progress.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class OnboardingProgress(Base, IDMixin):
    """Track user onboarding progress and completed steps."""

    __tablename__ = "onboarding_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    current_step = Column(String(50), default='welcome', nullable=False)  # welcome, preferences, budget, products, notifications, complete
    completed_steps = Column(JSON, default=list, nullable=False)  # List of completed step names
    is_completed = Column(Boolean, default=False, nullable=False)
    skipped = Column(Boolean, default=False, nullable=False)  # Whether user skipped onboarding
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)  # When user finished onboarding

    # Metadata about onboarding
    metadata = Column(JSON, default=dict, nullable=False)  # Store additional onboarding data

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<OnboardingProgress(user_id={self.user_id}, step={self.current_step}, completed={self.is_completed})>"