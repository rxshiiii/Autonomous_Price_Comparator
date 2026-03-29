"""
Analytics models for tracking user interactions and engagement metrics.
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.db.base import IDMixin


class UserInteraction(Base, IDMixin):
    """Track all user interactions for analytics and engagement insights."""

    __tablename__ = "user_interactions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # click, view, search, purchase, track, untrack
    resource_type = Column(String(50), nullable=False)  # product, recommendation, alert, notification
    resource_id = Column(UUID(as_uuid=True), index=True)  # ID of the resource being interacted with
    metadata = Column(JSONB)  # Additional context data (search query, product details, etc.)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = Column(String(255))  # Track session for user flow analysis
    ip_address = Column(String(45))  # IPv4/IPv6 for geographic analysis (optional)
    user_agent = Column(String(500))  # Browser/device info (optional)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("idx_user_interactions_user_timestamp", "user_id", "timestamp"),
        Index("idx_user_interactions_action_resource", "action_type", "resource_type"),
        Index("idx_user_interactions_analytics", "user_id", "action_type", "timestamp"),
    )

    def __repr__(self):
        return f"<UserInteraction(user_id={self.user_id}, action={self.action_type}, resource={self.resource_type})>"


class UserAnalyticsSummary(Base, IDMixin):
    """Daily aggregated user engagement metrics for quick dashboard insights."""

    __tablename__ = "user_analytics_summary"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Recommendation engagement
    recommendations_viewed = Column(Integer, default=0, nullable=False)
    recommendations_clicked = Column(Integer, default=0, nullable=False)
    recommendations_tracked = Column(Integer, default=0, nullable=False)

    # Product interactions
    products_searched = Column(Integer, default=0, nullable=False)
    products_viewed = Column(Integer, default=0, nullable=False)
    products_compared = Column(Integer, default=0, nullable=False)

    # Alert and tracking activity
    alerts_created = Column(Integer, default=0, nullable=False)
    alerts_triggered = Column(Integer, default=0, nullable=False)
    products_tracked = Column(Integer, default=0, nullable=False)
    products_untracked = Column(Integer, default=0, nullable=False)

    # Session metrics
    sessions_count = Column(Integer, default=0, nullable=False)
    total_session_duration_minutes = Column(Integer, default=0, nullable=False)
    avg_session_duration_minutes = Column(Integer, default=0, nullable=False)

    # Notification engagement
    notifications_received = Column(Integer, default=0, nullable=False)
    notifications_read = Column(Integer, default=0, nullable=False)
    notifications_clicked = Column(Integer, default=0, nullable=False)

    # Calculated metrics (derived from interactions)
    engagement_score = Column(Integer, default=0, nullable=False)  # 0-100 scale
    recommendation_ctr = Column(Integer, default=0, nullable=False)  # Click-through rate as percentage

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("idx_analytics_summary_user_date", "user_id", "date", unique=True),
        Index("idx_analytics_summary_date", "date"),
        Index("idx_analytics_summary_engagement", "engagement_score", "date"),
    )

    def __repr__(self):
        return f"<UserAnalyticsSummary(user_id={self.user_id}, date={self.date}, engagement={self.engagement_score})>"


class SystemAnalytics(Base, IDMixin):
    """System-wide analytics for monitoring platform health and usage trends."""

    __tablename__ = "system_analytics"

    date = Column(Date, nullable=False, unique=True, index=True)

    # User metrics
    total_users = Column(Integer, default=0, nullable=False)
    active_users = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    returning_users = Column(Integer, default=0, nullable=False)

    # Product and search metrics
    total_products = Column(Integer, default=0, nullable=False)
    searches_count = Column(Integer, default=0, nullable=False)
    unique_searches = Column(Integer, default=0, nullable=False)
    avg_search_results = Column(Integer, default=0, nullable=False)

    # Recommendation metrics
    recommendations_generated = Column(Integer, default=0, nullable=False)
    recommendations_shown = Column(Integer, default=0, nullable=False)
    recommendations_clicked = Column(Integer, default=0, nullable=False)
    avg_recommendation_score = Column(Integer, default=0, nullable=False)  # Average score * 100

    # Alert and notification metrics
    alerts_created = Column(Integer, default=0, nullable=False)
    alerts_triggered = Column(Integer, default=0, nullable=False)
    notifications_sent = Column(Integer, default=0, nullable=False)
    notifications_delivered = Column(Integer, default=0, nullable=False)

    # Performance metrics
    avg_response_time_ms = Column(Integer, default=0, nullable=False)
    cache_hit_rate = Column(Integer, default=0, nullable=False)  # Percentage
    error_rate = Column(Integer, default=0, nullable=False)  # Percentage

    # Scraping metrics
    scraping_jobs_count = Column(Integer, default=0, nullable=False)
    scraping_success_rate = Column(Integer, default=0, nullable=False)  # Percentage
    products_scraped = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<SystemAnalytics(date={self.date}, active_users={self.active_users})>"


class UserEngagementTrend(Base, IDMixin):
    """Track user engagement trends over time for personalization insights."""

    __tablename__ = "user_engagement_trends"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False, index=True)  # Monday of the week

    # Engagement patterns
    most_active_hour = Column(Integer)  # 0-23
    most_active_day = Column(String(10))  # monday, tuesday, etc.
    avg_daily_sessions = Column(Integer, default=0, nullable=False)

    # Preference trends
    top_category = Column(String(100))
    top_brand = Column(String(100))
    avg_price_range_min = Column(Integer, default=0)
    avg_price_range_max = Column(Integer, default=0)

    # Behavioral insights
    search_frequency = Column(String(20))  # low, medium, high
    recommendation_responsiveness = Column(String(20))  # low, medium, high
    alert_sensitivity = Column(String(20))  # low, medium, high

    # Trend metadata
    trends_confidence = Column(Integer, default=0, nullable=False)  # 0-100 confidence score
    data_points_count = Column(Integer, default=0, nullable=False)  # Number of interactions used

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("idx_engagement_trends_user_week", "user_id", "week_start_date", unique=True),
        Index("idx_engagement_trends_week", "week_start_date"),
    )

    def __repr__(self):
        return f"<UserEngagementTrend(user_id={self.user_id}, week={self.week_start_date})>"