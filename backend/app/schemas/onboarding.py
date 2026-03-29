"""
Onboarding Pydantic schemas for API requests/responses.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryOption(BaseModel):
    """Product category option for selection."""
    id: str
    name: str
    icon: str
    description: str


class CategoriesResponse(BaseModel):
    """Response with available categories."""
    categories: List[CategoryOption]


class ProductForSelection(BaseModel):
    """Product for onboarding selection."""
    id: str
    name: str
    image_url: Optional[str] = None
    current_price: float
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    platform: str
    category: str


class PopularProductsResponse(BaseModel):
    """Response with popular products for a category."""
    category: str
    products: List[ProductForSelection]
    total_count: int


class OnboardingStepRequest(BaseModel):
    """Request to complete an onboarding step."""
    step: str = Field(..., description="Step name: welcome, preferences, budget, products, notifications")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Step-specific data")


class BudgetRange(BaseModel):
    """Budget range for a category."""
    min: Optional[int] = None
    max: Optional[int] = None


class QuietHours(BaseModel):
    """Quiet hours for notifications."""
    start: str = Field(..., description="Time in HH:MM format")
    end: str = Field(..., description="Time in HH:MM format")


# Specific step request schemas
class PreferencesStepData(BaseModel):
    """Data for preferences onboarding step."""
    categories: List[str] = Field(..., description="Selected product categories")
    interests: List[str] = Field(default_factory=list, description="Specific interests in format 'category:interest'")


class BudgetStepData(BaseModel):
    """Data for budget onboarding step."""
    budget_ranges: Dict[str, BudgetRange] = Field(default_factory=dict, description="Budget ranges per category")


class ProductSelectionStepData(BaseModel):
    """Data for product selection onboarding step."""
    product_ids: List[str] = Field(..., description="IDs of selected products")


class NotificationStepData(BaseModel):
    """Data for notification preferences onboarding step."""
    websocket_enabled: bool = True
    email_enabled: bool = True
    max_notifications_per_day: int = Field(5, ge=1, le=50)
    price_drop_threshold: int = Field(10, ge=1, le=50, description="Percentage threshold")
    quiet_hours: Optional[QuietHours] = None


class OnboardingStep(BaseModel):
    """Single onboarding step information."""
    key: str
    order: int
    name: str
    required: bool


class OnboardingProgressResponse(BaseModel):
    """Current onboarding progress response."""
    user_id: str
    current_step: str = Field(..., description="Current step name")
    completed_steps: List[str] = Field(default_factory=list)
    is_completed: bool = False
    steps: Dict[str, Dict] = Field(default_factory=dict, description="All available steps")
    progress_percentage: int = Field(0, ge=0, le=100)
    last_updated: Optional[str] = None


class OnboardingCompleteResponse(BaseModel):
    """Response when onboarding is completed."""
    success: bool
    message: str
    user_id: str
    completed_at: datetime
    redirect_to: str = Field("dashboard", description="Where to redirect user after onboarding")


class OnboardingStartRequest(BaseModel):
    """Request to start/initialize onboarding for a user."""
    full_name: Optional[str] = None
    age: Optional[int] = None


class OnboardingResumeRequest(BaseModel):
    """Request to resume onboarding from a specific step."""
    from_step: str = Field(default="welcome", description="Step to resume from")


# Analytics for onboarding
class OnboardingAnalytics(BaseModel):
    """Onboarding completion analytics."""
    total_users_started: int
    total_users_completed: int
    completion_rate: float = Field(..., ge=0, le=100)
    avg_completion_time_seconds: int
    step_completion_rates: Dict[str, float] = Field(default_factory=dict)
    most_common_drop_off_step: Optional[str] = None


class OnboardingFeedback(BaseModel):
    """User feedback on onboarding experience."""
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = None
    features_requested: List[str] = Field(default_factory=list)
    submitted_at: datetime