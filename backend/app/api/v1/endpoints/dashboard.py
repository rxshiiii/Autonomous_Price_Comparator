"""
Dashboard API endpoints for comprehensive user dashboard data.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.price_alert import PriceAlert
from app.models.price_history import PriceHistory
from app.models.notification import Notification
from app.models.user import UserTrackedProduct
from app.models.analytics import UserInteraction, UserAnalyticsSummary
from app.services.cache_service import get_cache_service
from app.schemas.dashboard import (
    DashboardOverviewResponse,
    RecommendationWithProduct,
    TrackedProductWithTrend,
    PriceAlertWithStatus,
    UserAnalyticsResponse,
    RecommendationFeedbackRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache_service = Depends(get_cache_service)
):
    """
    Get comprehensive dashboard overview data for the user.

    Includes:
    - AI recommendations with reasoning
    - Tracked products with price trends
    - Active price alerts with status
    - Recent notification activity
    - User engagement analytics
    """
    try:
        # Try to get cached dashboard data first
        cached_data = await cache_service.get_dashboard_overview(str(current_user.id))
        if cached_data:
            logger.debug(f"Returning cached dashboard data for user {current_user.id}")
            return DashboardOverviewResponse(**cached_data)

        # Get AI recommendations (top 10 most recent, unviewed first)
        recommendations_query = await db.execute(
            db.query(Recommendation)
            .options(selectinload(Recommendation.product))
            .filter(
                Recommendation.user_id == current_user.id,
                or_(
                    Recommendation.expires_at.is_(None),
                    Recommendation.expires_at > datetime.utcnow()
                )
            )
            .order_by(desc(Recommendation.score), desc(Recommendation.generated_at))
            .limit(10)
        )
        recommendations = recommendations_query.scalars().all()

        # Get tracked products with price trends
        tracked_query = await db.execute(
            db.query(UserTrackedProduct)
            .options(selectinload(UserTrackedProduct.product))
            .filter(UserTrackedProduct.user_id == current_user.id)
            .order_by(desc(UserTrackedProduct.added_at))
            .limit(20)
        )
        tracked_products_raw = tracked_query.scalars().all()

        # Get price trends for tracked products
        tracked_products = []
        for tracked in tracked_products_raw:
            # Get recent price history (last 30 days)
            price_history_query = await db.execute(
                db.query(PriceHistory)
                .filter(
                    PriceHistory.product_id == tracked.product_id,
                    PriceHistory.recorded_at >= datetime.utcnow() - timedelta(days=30)
                )
                .order_by(desc(PriceHistory.recorded_at))
                .limit(30)
            )
            price_history = price_history_query.scalars().all()

            # Calculate trend
            trend = "stable"
            price_change_percent = 0
            if len(price_history) >= 2:
                latest_price = price_history[0].price
                previous_price = price_history[-1].price
                if latest_price != previous_price:
                    price_change_percent = ((latest_price - previous_price) / previous_price) * 100
                    trend = "up" if price_change_percent > 2 else "down" if price_change_percent < -2 else "stable"

            tracked_products.append(TrackedProductWithTrend(
                id=tracked.id,
                product=tracked.product,
                added_at=tracked.added_at,
                notes=tracked.notes,
                price_trend=trend,
                price_change_percent=round(price_change_percent, 2),
                recent_price_history=[
                    {"price": float(ph.price), "date": ph.recorded_at.isoformat()}
                    for ph in price_history[:10]  # Last 10 price points for chart
                ]
            ))

        # Get active price alerts with status
        alerts_query = await db.execute(
            db.query(PriceAlert)
            .options(selectinload(PriceAlert.product))
            .filter(
                PriceAlert.user_id == current_user.id,
                PriceAlert.is_active == True
            )
            .order_by(desc(PriceAlert.created_at))
            .limit(15)
        )
        alerts_raw = alerts_query.scalars().all()

        # Check alert status against current prices
        price_alerts = []
        for alert in alerts_raw:
            current_price = alert.product.current_price
            status = "waiting"

            if alert.alert_type == "below_price" and current_price <= alert.target_price:
                status = "triggered"
            elif alert.alert_type == "percentage_drop":
                # Calculate percentage drop from original price
                if alert.product.original_price and current_price:
                    drop_percent = ((alert.product.original_price - current_price) / alert.product.original_price) * 100
                    if drop_percent >= alert.target_price:  # target_price stores percentage for this type
                        status = "triggered"

            price_alerts.append(PriceAlertWithStatus(
                id=alert.id,
                product=alert.product,
                alert_type=alert.alert_type,
                target_price=alert.target_price,
                current_price=current_price,
                status=status,
                created_at=alert.created_at,
                triggered_at=alert.triggered_at
            ))

        # Get recent notifications (last 20)
        notifications_query = await db.execute(
            db.query(Notification)
            .filter(Notification.user_id == current_user.id)
            .order_by(desc(Notification.created_at))
            .limit(20)
        )
        recent_notifications = notifications_query.scalars().all()

        # Get user analytics summary (last 30 days)
        analytics_summary = await get_user_analytics_summary(current_user.id, db, 30)

        # Prepare dashboard data
        dashboard_data = {
            "recommendations": [
                RecommendationWithProduct(
                    id=rec.id,
                    product=rec.product,
                    score=float(rec.score),
                    reasoning=rec.reasoning,
                    generated_at=rec.generated_at,
                    shown_to_user=rec.shown_to_user,
                    user_action=rec.user_action
                ) for rec in recommendations
            ],
            "tracked_products": tracked_products,
            "price_alerts": price_alerts,
            "recent_notifications": [
                {
                    "id": str(notif.id),
                    "title": notif.title,
                    "message": notif.message,
                    "type": notif.notification_type,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at.isoformat(),
                    "data": notif.data
                } for notif in recent_notifications
            ],
            "analytics": analytics_summary,
            "summary": {
                "total_recommendations": len(recommendations),
                "unviewed_recommendations": len([r for r in recommendations if not r.shown_to_user]),
                "tracked_products_count": len(tracked_products),
                "active_alerts_count": len([a for a in price_alerts if a.status == "waiting"]),
                "triggered_alerts_count": len([a for a in price_alerts if a.status == "triggered"]),
                "unread_notifications": len([n for n in recent_notifications if not n.is_read])
            }
        }

        # Cache the dashboard data
        await cache_service.cache_dashboard_overview(str(current_user.id), dashboard_data, ttl=1800)

        return DashboardOverviewResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"Dashboard overview error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard data")


@router.get("/recommendations", response_model=List[RecommendationWithProduct])
async def get_user_recommendations(
    limit: int = Query(10, ge=1, le=50),
    include_viewed: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache_service = Depends(get_cache_service)
):
    """Get user's AI recommendations with product details and reasoning."""
    try:
        # Try cache first
        cache_key = f"user_recommendations:{current_user.id}:limit_{limit}:viewed_{include_viewed}"
        cached_recommendations = await cache_service.get(cache_key)
        if cached_recommendations:
            return [RecommendationWithProduct(**rec) for rec in cached_recommendations]

        # Build query
        query = db.query(Recommendation).options(selectinload(Recommendation.product)).filter(
            Recommendation.user_id == current_user.id,
            or_(
                Recommendation.expires_at.is_(None),
                Recommendation.expires_at > datetime.utcnow()
            )
        )

        # Filter by viewed status if specified
        if not include_viewed:
            query = query.filter(Recommendation.shown_to_user == False)

        # Execute query
        result = await db.execute(
            query.order_by(desc(Recommendation.score), desc(Recommendation.generated_at)).limit(limit)
        )
        recommendations = result.scalars().all()

        # Prepare response
        recommendation_data = [
            {
                "id": str(rec.id),
                "product": {
                    "id": str(rec.product.id),
                    "name": rec.product.name,
                    "description": rec.product.description,
                    "current_price": float(rec.product.current_price) if rec.product.current_price else None,
                    "original_price": float(rec.product.original_price) if rec.product.original_price else None,
                    "discount_percentage": float(rec.product.discount_percentage) if rec.product.discount_percentage else None,
                    "image_url": rec.product.image_url,
                    "product_url": rec.product.product_url,
                    "platform": rec.product.platform,
                    "category": rec.product.category,
                    "brand": rec.product.brand,
                    "rating": float(rec.product.rating) if rec.product.rating else None,
                    "reviews_count": rec.product.reviews_count
                },
                "score": float(rec.score),
                "reasoning": rec.reasoning,
                "generated_at": rec.generated_at.isoformat(),
                "shown_to_user": rec.shown_to_user,
                "user_action": rec.user_action
            } for rec in recommendations
        ]

        # Cache results
        await cache_service.set(cache_key, recommendation_data, ttl=3600)  # 1 hour TTL

        return [RecommendationWithProduct(**rec) for rec in recommendation_data]

    except Exception as e:
        logger.error(f"Get recommendations error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load recommendations")


@router.post("/recommendations/{recommendation_id}/feedback")
async def track_recommendation_feedback(
    recommendation_id: UUID,
    feedback: RecommendationFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache_service = Depends(get_cache_service)
):
    """Track user interaction with a recommendation (viewed, clicked, tracked, etc.)."""
    try:
        # Get the recommendation
        result = await db.execute(
            db.query(Recommendation).filter(
                Recommendation.id == recommendation_id,
                Recommendation.user_id == current_user.id
            )
        )
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Update recommendation action
        recommendation.user_action = feedback.action
        if feedback.action in ["viewed", "clicked"]:
            recommendation.shown_to_user = True

        # Track interaction in analytics
        interaction = UserInteraction(
            user_id=current_user.id,
            action_type=feedback.action,
            resource_type="recommendation",
            resource_id=recommendation_id,
            metadata={
                "product_id": str(recommendation.product_id),
                "recommendation_score": float(recommendation.score),
                "session_id": feedback.session_id
            }
        )
        db.add(interaction)

        await db.commit()

        # Invalidate relevant caches
        await cache_service.invalidate_user_cache(str(current_user.id))

        logger.info(f"Tracked recommendation feedback: user {current_user.id}, action {feedback.action}")

        return {"status": "success", "message": "Feedback recorded"}

    except Exception as e:
        logger.error(f"Recommendation feedback error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.get("/analytics", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    cache_service = Depends(get_cache_service)
):
    """Get user analytics and engagement insights."""
    try:
        # Try cache first
        cache_key = f"user_analytics:{current_user.id}:days_{days}"
        cached_analytics = await cache_service.get(cache_key)
        if cached_analytics:
            return UserAnalyticsResponse(**cached_analytics)

        analytics_data = await get_user_analytics_summary(current_user.id, db, days)

        # Cache results
        await cache_service.set(cache_key, analytics_data, ttl=900)  # 15 minutes TTL

        return UserAnalyticsResponse(**analytics_data)

    except Exception as e:
        logger.error(f"Get user analytics error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load analytics data")


async def get_user_analytics_summary(user_id: UUID, db: AsyncSession, days: int = 30) -> Dict:
    """Helper function to generate user analytics summary."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    try:
        # Get interaction counts by action type
        interaction_counts = await db.execute(
            db.query(
                UserInteraction.action_type,
                func.count(UserInteraction.id).label('count')
            )
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= start_date
            )
            .group_by(UserInteraction.action_type)
        )
        interaction_data = {row.action_type: row.count for row in interaction_counts}

        # Get recommendation metrics
        rec_stats = await db.execute(
            db.query(
                func.count(Recommendation.id).label('total'),
                func.count(func.nullif(Recommendation.shown_to_user, False)).label('viewed'),
                func.count(func.nullif(Recommendation.user_action, None)).label('interacted')
            )
            .filter(
                Recommendation.user_id == user_id,
                Recommendation.generated_at >= start_date
            )
        )
        rec_row = rec_stats.first()

        # Calculate engagement metrics
        total_recommendations = rec_row.total if rec_row else 0
        viewed_recommendations = rec_row.viewed if rec_row else 0
        interacted_recommendations = rec_row.interacted if rec_row else 0

        view_rate = (viewed_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0
        interaction_rate = (interacted_recommendations / viewed_recommendations * 100) if viewed_recommendations > 0 else 0

        # Get recent activity trend (last 7 days)
        recent_activity = await db.execute(
            db.query(
                func.date(UserInteraction.timestamp).label('date'),
                func.count(UserInteraction.id).label('activity_count')
            )
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= datetime.utcnow() - timedelta(days=7)
            )
            .group_by(func.date(UserInteraction.timestamp))
            .order_by(func.date(UserInteraction.timestamp))
        )
        activity_trend = [
            {"date": row.date.isoformat(), "count": row.activity_count}
            for row in recent_activity
        ]

        return {
            "period_days": days,
            "total_interactions": sum(interaction_data.values()),
            "interaction_breakdown": interaction_data,
            "recommendations_received": total_recommendations,
            "recommendations_viewed": viewed_recommendations,
            "recommendation_view_rate": round(view_rate, 1),
            "recommendation_interaction_rate": round(interaction_rate, 1),
            "activity_trend": activity_trend,
            "engagement_score": min(100, round((view_rate + interaction_rate) / 2, 1)),
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Analytics summary generation error: {e}")
        # Return empty analytics on error
        return {
            "period_days": days,
            "total_interactions": 0,
            "interaction_breakdown": {},
            "recommendations_received": 0,
            "recommendations_viewed": 0,
            "recommendation_view_rate": 0,
            "recommendation_interaction_rate": 0,
            "activity_trend": [],
            "engagement_score": 0,
            "generated_at": datetime.utcnow().isoformat()
        }