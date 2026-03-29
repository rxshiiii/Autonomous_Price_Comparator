"""
Price Alert Pydantic schemas for API requests and responses.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from decimal import Decimal


class PriceAlertCreate(BaseModel):
    """Create price alert request schema."""
    product_id: UUID
    alert_type: str = Field(..., description="Alert type: below_price, percentage_drop, back_in_stock")
    target_price: Optional[Decimal] = Field(None, description="Target price for below_price alerts")
    threshold_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage threshold for percentage_drop alerts")


class PriceAlertUpdate(BaseModel):
    """Update price alert request schema."""
    target_price: Optional[Decimal] = None
    threshold_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class PriceAlertResponse(BaseModel):
    """Price alert response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    product_id: UUID
    alert_type: str
    target_price: Optional[Decimal]
    threshold_percentage: Optional[Decimal]
    is_active: bool
    triggered_at: Optional[datetime]
    created_at: datetime
