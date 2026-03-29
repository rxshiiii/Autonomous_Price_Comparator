"""
Onboarding API endpoints for user preference collection and setup.
"""
import logging
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.onboarding_service import OnboardingService, get_onboarding_service
from app.schemas.onboarding import (
    OnboardingProgressResponse,
    OnboardingStepRequest,
    CategoriesResponse,
    PopularProductsResponse,
    OnboardingCompleteResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/progress", response_model=OnboardingProgressResponse)
async def get_onboarding_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """Get user's onboarding progress and current step."""
    try:
        progress = await onboarding_service.get_onboarding_progress(db, current_user.id)
        return OnboardingProgressResponse(**progress)

    except Exception as e:
        logger.error(f"Get onboarding progress error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding progress")


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(
    onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """Get available product categories for preference selection."""
    try:
        categories = await onboarding_service.get_category_suggestions()
        return CategoriesResponse(categories=categories)

    except Exception as e:
        logger.error(f"Get categories error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get categories")


@router.get("/popular-products/{category}", response_model=PopularProductsResponse)
async def get_popular_products_by_category(
    category: str,
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """Get popular products in a category for initial product selection."""
    try:
        products = await onboarding_service.get_popular_products_by_category(
            db, category, limit
        )
        return PopularProductsResponse(
            category=category,
            products=products,
            total_count=len(products)
        )

    except Exception as e:
        logger.error(f"Get popular products error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular products")


@router.post("/step/complete", response_model=OnboardingProgressResponse)
async def complete_onboarding_step(
    request: OnboardingStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """Complete an onboarding step and move to the next one."""
    try:
        progress = await onboarding_service.complete_onboarding_step(
            db, current_user.id, request.step, request.data
        )
        return OnboardingProgressResponse(**progress)

    except ValueError as e:
        logger.warning(f"Invalid onboarding step: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Complete onboarding step error: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding step")


@router.post("/skip", response_model=OnboardingProgressResponse)
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    onboarding_service: OnboardingService = Depends(get_onboarding_service)
):
    """Allow user to skip onboarding and go to dashboard."""
    try:
        progress = await onboarding_service.skip_onboarding(db, current_user.id)
        return OnboardingProgressResponse(**progress)

    except Exception as e:
        logger.error(f"Skip onboarding error: {e}")
        raise HTTPException(status_code=500, detail="Failed to skip onboarding")