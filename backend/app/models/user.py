"""
User model for authentication and user management.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin, TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    age = Column(Integer)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(String)  # Will store timestamp

    # Relationships
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    tracked_products = relationship("UserTrackedProduct", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserPreference(Base, IDMixin, TimestampMixin):
    """User preferences for personalized recommendations."""

    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100))
    interest = Column(String(255))
    priority = Column(Integer, default=1)  # 1-5 scale

    # Relationships
    user = relationship("User", back_populates="preferences")

    __table_args__ = (
        UniqueConstraint("user_id", "category", "interest", name="unique_user_preference"),
    )

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, category={self.category}, interest={self.interest})>"


class UserTrackedProduct(Base, IDMixin):
    """User's tracked products (watchlist)."""

    __tablename__ = "user_tracked_products"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="tracked_products")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="unique_tracked_product"),
    )

    def __repr__(self):
        return f"<UserTrackedProduct(user_id={self.user_id}, product_id={self.product_id})>"
