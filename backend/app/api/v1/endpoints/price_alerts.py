"""
Price Alert API endpoints for managing price drop notifications.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.price_alert import PriceAlert
from app.models.product import Product
from app.schemas.price_alert import (
    PriceAlertCreate,
    PriceAlertResponse,
    PriceAlertUpdate,
)

router = APIRouter()


@router.post("/", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new price alert for a product.

    Alert Types:
    - **below_price**: Alert when price drops below target price
    - **percentage_drop**: Alert when price drops by X percentage
    - **back_in_stock**: Alert when product is back in stock

    Request Body:
    - **product_id**: Product UUID to track
    - **target_price**: Target price for 'below_price' alert
    - **alert_type**: Type of alert
    - **threshold_percentage**: For percentage_drop alerts

    Returns:
    - Created price alert object
    """
    # Verify product exists
    product_result = await db.execute(
        select(Product).where(Product.id == alert_data.product_id)
    )
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Check if alert already exists for this product
    existing_result = await db.execute(
        select(PriceAlert).where(
            (PriceAlert.user_id == current_user.id) &
            (PriceAlert.product_id == alert_data.product_id) &
            (PriceAlert.is_active == True)
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active price alert already exists for this product"
        )

    # Create new alert
    new_alert = PriceAlert(
        user_id=current_user.id,
        product_id=alert_data.product_id,
        alert_type=alert_data.alert_type,
        target_price=alert_data.target_price,
        threshold_percentage=alert_data.threshold_percentage,
        is_active=True,
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    return PriceAlertResponse.model_validate(new_alert)


@router.get("/", response_model=list[PriceAlertResponse])
async def get_user_price_alerts(
    active_only: bool = Query(True, description="Show only active alerts"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all price alerts for the current user.

    Query Parameters:
    - **active_only**: Show only active alerts (default: true)
    - **limit**: Number of results (1-100)
    - **offset**: Pagination offset

    Returns:
    - List of price alert objects
    """
    filters = [PriceAlert.user_id == current_user.id]

    if active_only:
        filters.append(PriceAlert.is_active == True)

    from sqlalchemy import and_
    stmt = (
        select(PriceAlert)
        .where(and_(*filters))
        .order_by(PriceAlert.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    alerts = result.scalars().all()

    return [PriceAlertResponse.model_validate(a) for a in alerts]


@router.get("/{alert_id}", response_model=PriceAlertResponse)
async def get_price_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific price alert.

    Path Parameters:
    - **alert_id**: Price alert UUID

    Returns:
    - Price alert object
    """
    result = await db.execute(
        select(PriceAlert).where(
            (PriceAlert.id == alert_id) &
            (PriceAlert.user_id == current_user.id)
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price alert not found"
        )

    return PriceAlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=PriceAlertResponse)
async def update_price_alert(
    alert_id: str,
    update_data: PriceAlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a price alert.

    Path Parameters:
    - **alert_id**: Price alert UUID

    Request Body:
    - **target_price**: New target price (optional)
    - **threshold_percentage**: New threshold percentage (optional)
    - **is_active**: Enable/disable alert (optional)

    Returns:
    - Updated price alert object
    """
    result = await db.execute(
        select(PriceAlert).where(
            (PriceAlert.id == alert_id) &
            (PriceAlert.user_id == current_user.id)
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price alert not found"
        )

    # Update fields
    if update_data.target_price is not None:
        alert.target_price = update_data.target_price

    if update_data.threshold_percentage is not None:
        alert.threshold_percentage = update_data.threshold_percentage

    if update_data.is_active is not None:
        alert.is_active = update_data.is_active

    await db.commit()
    await db.refresh(alert)

    return PriceAlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a price alert.

    Path Parameters:
    - **alert_id**: Price alert UUID

    Returns:
    - 204 No Content on success
    """
    result = await db.execute(
        select(PriceAlert).where(
            (PriceAlert.id == alert_id) &
            (PriceAlert.user_id == current_user.id)
        )
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price alert not found"
        )

    await db.delete(alert)
    await db.commit()


@router.get("/triggered")
async def get_triggered_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all triggered price alerts for the current user.

    Returns:
    - List of triggered price alerts (where alert was activated by price drop)
    """
    from sqlalchemy import and_
    result = await db.execute(
        select(PriceAlert)
        .where(
            and_(
                PriceAlert.user_id == current_user.id,
                PriceAlert.triggered_at.isnot(None)
            )
        )
        .order_by(PriceAlert.triggered_at.desc())
    )
    alerts = result.scalars().all()

    return [PriceAlertResponse.model_validate(a) for a in alerts]
