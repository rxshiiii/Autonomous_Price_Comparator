"""
Dashboard Pydantic schemas for API responses.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.product import ProductResponse
from app.schemas.user import UserResponse


class ProductSummary(BaseModel):
    """Simplified product information for dashboard use."""
    id: UUID
    name: str
    description: Optional[str] = None
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    image_url: Optional[str] = None
    product_url: str
    platform: str
    category: Optional[str] = None
    brand: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

    class Config:
        from_attributes = True


class RecommendationWithProduct(BaseModel):
    """AI recommendation with full product details and reasoning."""
    id: UUID
    product: ProductSummary
    score: float = Field(..., ge=0, le=1, description="AI recommendation score (0-1)")
    reasoning: Optional[str] = Field(None, description="GROQ-generated reasoning for the recommendation")
    generated_at: datetime
    shown_to_user: bool = False
    user_action: Optional[str] = Field(None, description="User action: viewed, clicked, tracked, purchased")

    class Config:
        from_attributes = True


class PriceHistoryPoint(BaseModel):
    """Single price history data point for charts."""
    price: float
    date: str
    discount_percentage: Optional[float] = None


class TrackedProductWithTrend(BaseModel):
    """User tracked product with price trend analysis."""
    id: UUID
    product: ProductSummary
    added_at: datetime
    notes: Optional[str] = None
    price_trend: str = Field(..., description="Price trend: up, down, stable")
    price_change_percent: float = Field(0, description="Percentage price change in tracking period")
    recent_price_history: List[PriceHistoryPoint] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PriceAlertWithStatus(BaseModel):
    """Price alert with current status evaluation."""
    id: UUID
    product: ProductSummary
    alert_type: str = Field(..., description="Alert type: below_price, percentage_drop, back_in_stock")
    target_price: float
    current_price: Optional[float] = None
    status: str = Field(..., description="Alert status: waiting, triggered")
    created_at: datetime
    triggered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationSummary(BaseModel):
    """Recent notification summary for dashboard."""
    id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: str
    data: Optional[Dict[str, Any]] = None


class DashboardSummary(BaseModel):
    """Dashboard summary statistics."""
    total_recommendations: int = 0
    unviewed_recommendations: int = 0
    tracked_products_count: int = 0
    active_alerts_count: int = 0
    triggered_alerts_count: int = 0
    unread_notifications: int = 0


class ActivityTrendPoint(BaseModel):
    """Daily activity trend data point."""
    date: str
    count: int


class UserAnalyticsResponse(BaseModel):
    """User analytics and engagement metrics."""
    period_days: int
    total_interactions: int = 0
    interaction_breakdown: Dict[str, int] = Field(default_factory=dict)
    recommendations_received: int = 0
    recommendations_viewed: int = 0
    recommendation_view_rate: float = 0  # Percentage
    recommendation_interaction_rate: float = 0  # Percentage
    activity_trend: List[ActivityTrendPoint] = Field(default_factory=list)
    engagement_score: float = Field(0, ge=0, le=100, description="Overall engagement score (0-100)")
    generated_at: str


class DashboardOverviewResponse(BaseModel):
    """Complete dashboard overview response."""
    recommendations: List[RecommendationWithProduct] = Field(default_factory=list)
    tracked_products: List[TrackedProductWithTrend] = Field(default_factory=list)
    price_alerts: List[PriceAlertWithStatus] = Field(default_factory=list)
    recent_notifications: List[NotificationSummary] = Field(default_factory=list)
    analytics: UserAnalyticsResponse
    summary: DashboardSummary


# Request schemas
class RecommendationFeedbackRequest(BaseModel):
    """Request schema for tracking recommendation user actions."""
    action: str = Field(..., description="User action: viewed, clicked, tracked, purchased, ignored")
    session_id: Optional[str] = Field(None, description="Optional session identifier for analytics")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context data")


class DashboardPreferencesRequest(BaseModel):
    """Request schema for updating dashboard preferences."""
    show_recommendations: bool = True
    show_price_alerts: bool = True
    show_tracked_products: bool = True
    show_notifications: bool = True
    recommendations_limit: int = Field(10, ge=1, le=50)
    tracked_products_limit: int = Field(20, ge=1, le=100)
    price_alerts_limit: int = Field(15, ge=1, le=50)
    notifications_limit: int = Field(20, ge=1, le=100)


class QuickActionRequest(BaseModel):
    """Request schema for quick dashboard actions."""
    action: str = Field(..., description="Action type: track_product, create_alert, mark_notification_read")
    resource_id: UUID = Field(..., description="ID of the resource (product, notification, etc.)")
    params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Action-specific parameters")


# Response schemas for quick actions
class QuickActionResponse(BaseModel):
    """Response for quick dashboard actions."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class DashboardHealthResponse(BaseModel):
    """Dashboard service health check response."""
    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    cache_status: str = Field(..., description="Cache service status")
    database_status: str = Field(..., description="Database status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    cache_hit_rate: float = Field(0, description="Cache hit rate percentage")
    timestamp: datetime


# Analytics schemas
class RecommendationEffectivenessResponse(BaseModel):
    """Recommendation system effectiveness metrics."""
    total_recommendations: int
    viewed_count: int
    clicked_count: int
    tracked_count: int
    purchased_count: int
    view_rate: float = Field(..., description="Percentage of recommendations viewed")
    click_through_rate: float = Field(..., description="CTR of viewed recommendations")
    conversion_rate: float = Field(..., description="Rate of recommendations leading to tracking/purchase")
    avg_recommendation_score: float
    top_performing_categories: List[Dict[str, Any]] = Field(default_factory=list)


class ProductEngagementResponse(BaseModel):
    """Product engagement analytics."""
    total_products_viewed: int
    total_products_tracked: int
    total_searches: int
    most_viewed_categories: List[Dict[str, Any]] = Field(default_factory=list)
    most_tracked_brands: List[Dict[str, Any]] = Field(default_factory=list)
    avg_price_range: Dict[str, float] = Field(default_factory=dict)
    engagement_by_platform: Dict[str, int] = Field(default_factory=dict)


class PersonalInsightsResponse(BaseModel):
    """Personalized insights for the user."""
    insights: List[Dict[str, Any]] = Field(default_factory=list, description="Generated insights")
    recommendations_for_improvement: List[str] = Field(default_factory=list)
    usage_patterns: Dict[str, Any] = Field(default_factory=dict)
    savings_potential: Optional[float] = Field(None, description="Estimated savings from recommendations")
    engagement_level: str = Field(..., description="User engagement level: low, medium, high")
    generated_at: datetime