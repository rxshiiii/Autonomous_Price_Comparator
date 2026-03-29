"""
Analytics service for tracking user interactions and generating insights.
"""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from uuid import UUID

from sqlalchemy import desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import coalesce

from app.models.user import User
from app.models.analytics import UserInteraction, UserAnalyticsSummary, SystemAnalytics, UserEngagementTrend
from app.models.recommendation import Recommendation
from app.models.product import Product
from app.models.notification import Notification
from app.services.cache_service import CacheService


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking user interactions and generating analytics insights."""

    def __init__(self, cache_service: CacheService):
        self.cache_service = cache_service

    async def track_interaction(
        self,
        db: AsyncSession,
        user_id: UUID,
        action_type: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Track a user interaction event.

        Args:
            user_id: User performing the action
            action_type: Type of action (click, view, search, track, purchase, etc.)
            resource_type: Type of resource (product, recommendation, alert, notification)
            resource_id: ID of the resource being interacted with
            metadata: Additional context data
            session_id: Session identifier for flow analysis
            ip_address: User's IP address (for geographic analysis)
            user_agent: User's browser/device info
        """
        try:
            # Create interaction record
            interaction = UserInteraction(
                user_id=user_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata=metadata or {},
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )

            db.add(interaction)
            await db.commit()

            # Invalidate user analytics cache
            await self.cache_service.invalidate_user_cache(str(user_id))

            logger.debug(f"Tracked interaction: user {user_id}, action {action_type}, resource {resource_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to track interaction: {e}")
            await db.rollback()
            return False

    async def get_user_engagement_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive user engagement summary."""
        try:
            # Try cache first
            cache_key = f"engagement_summary:{user_id}:days_{days}"
            cached_data = await self.cache_service.get(cache_key)
            if cached_data:
                return cached_data

            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get interaction counts by type
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

            interaction_breakdown = {row.action_type: row.count for row in interaction_counts}

            # Get recommendation metrics
            rec_metrics = await self._get_recommendation_metrics(db, user_id, start_date, end_date)

            # Get product engagement metrics
            product_metrics = await self._get_product_engagement_metrics(db, user_id, start_date, end_date)

            # Get session analytics
            session_metrics = await self._get_session_metrics(db, user_id, start_date, end_date)

            # Calculate engagement score (0-100)
            engagement_score = self._calculate_engagement_score(
                interaction_breakdown,
                rec_metrics,
                product_metrics,
                session_metrics
            )

            # Get daily activity trend
            daily_trend = await self._get_daily_activity_trend(db, user_id, 14)  # Last 14 days

            summary = {
                "user_id": str(user_id),
                "period_days": days,
                "total_interactions": sum(interaction_breakdown.values()),
                "interaction_breakdown": interaction_breakdown,
                "recommendation_metrics": rec_metrics,
                "product_metrics": product_metrics,
                "session_metrics": session_metrics,
                "engagement_score": engagement_score,
                "daily_activity_trend": daily_trend,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Cache for 15 minutes
            await self.cache_service.set(cache_key, summary, ttl=900)

            return summary

        except Exception as e:
            logger.error(f"Failed to get user engagement summary: {e}")
            return self._get_empty_engagement_summary(user_id, days)

    async def get_recommendation_effectiveness(
        self,
        db: AsyncSession,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze recommendation system effectiveness for the user."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get recommendation stats
            rec_stats = await db.execute(
                db.query(
                    func.count(Recommendation.id).label('total'),
                    func.count(func.nullif(Recommendation.shown_to_user, False)).label('viewed'),
                    func.avg(Recommendation.score).label('avg_score')
                )
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.generated_at >= start_date
                )
            )
            stats = rec_stats.first()

            # Get action breakdown
            action_stats = await db.execute(
                db.query(
                    Recommendation.user_action,
                    func.count(Recommendation.id).label('count')
                )
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.generated_at >= start_date,
                    Recommendation.user_action.isnot(None)
                )
                .group_by(Recommendation.user_action)
            )

            action_breakdown = {row.user_action: row.count for row in action_stats}

            # Get category performance
            category_stats = await db.execute(
                db.query(
                    Product.category,
                    func.count(Recommendation.id).label('rec_count'),
                    func.avg(Recommendation.score).label('avg_score'),
                    func.count(func.nullif(Recommendation.shown_to_user, False)).label('viewed_count')
                )
                .join(Product, Recommendation.product_id == Product.id)
                .filter(
                    Recommendation.user_id == user_id,
                    Recommendation.generated_at >= start_date
                )
                .group_by(Product.category)
                .order_by(desc('avg_score'))
            )

            category_performance = [
                {
                    "category": row.category,
                    "recommendations": row.rec_count,
                    "avg_score": float(row.avg_score or 0),
                    "viewed": row.viewed_count,
                    "view_rate": (row.viewed_count / row.rec_count * 100) if row.rec_count > 0 else 0
                }
                for row in category_stats
            ]

            total_recs = stats.total if stats else 0
            viewed_recs = stats.viewed if stats else 0

            return {
                "total_recommendations": total_recs,
                "viewed_recommendations": viewed_recs,
                "view_rate": (viewed_recs / total_recs * 100) if total_recs > 0 else 0,
                "avg_recommendation_score": float(stats.avg_score or 0) if stats else 0,
                "action_breakdown": action_breakdown,
                "category_performance": category_performance,
                "effectiveness_score": self._calculate_rec_effectiveness_score(
                    total_recs, viewed_recs, action_breakdown
                )
            }

        except Exception as e:
            logger.error(f"Failed to get recommendation effectiveness: {e}")
            return {}

    async def generate_personal_insights(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Generate personalized insights and recommendations for the user."""
        try:
            # Get user engagement data
            engagement_data = await self.get_user_engagement_summary(db, user_id, 30)

            # Get recommendation effectiveness
            rec_effectiveness = await self.get_recommendation_effectiveness(db, user_id, 30)

            # Generate insights based on patterns
            insights = []
            recommendations = []

            # Analyze engagement patterns
            total_interactions = engagement_data.get("total_interactions", 0)
            engagement_score = engagement_data.get("engagement_score", 0)

            if engagement_score < 30:
                insights.append({
                    "type": "engagement",
                    "title": "Low Engagement Detected",
                    "message": "You haven't been very active lately. Check out your personalized recommendations!",
                    "action_suggestion": "view_recommendations",
                    "priority": "medium"
                })
                recommendations.append("Try exploring more product categories to get better recommendations")

            elif engagement_score > 70:
                insights.append({
                    "type": "engagement",
                    "title": "Highly Engaged User",
                    "message": "You're making great use of the platform! Keep tracking products for the best deals.",
                    "action_suggestion": "explore_alerts",
                    "priority": "low"
                })

            # Analyze recommendation performance
            rec_view_rate = rec_effectiveness.get("view_rate", 0)
            if rec_view_rate < 40:
                insights.append({
                    "type": "recommendations",
                    "title": "Missing Great Recommendations",
                    "message": f"You've only viewed {rec_view_rate:.1f}% of your recommendations. You might be missing great deals!",
                    "action_suggestion": "check_recommendations",
                    "priority": "high"
                })
                recommendations.append("Review your AI recommendations regularly for personalized deals")

            # Analyze product tracking patterns
            product_interactions = engagement_data.get("interaction_breakdown", {}).get("track", 0)
            if product_interactions == 0:
                insights.append({
                    "type": "tracking",
                    "title": "Start Tracking Products",
                    "message": "Track products you're interested in to get price drop alerts!",
                    "action_suggestion": "track_products",
                    "priority": "high"
                })
                recommendations.append("Track at least 5 products to maximize your savings potential")

            # Analyze search behavior
            search_interactions = engagement_data.get("interaction_breakdown", {}).get("search", 0)
            if search_interactions > 20:
                insights.append({
                    "type": "efficiency",
                    "title": "Frequent Searcher",
                    "message": "You search a lot! Consider using price alerts to get notified automatically.",
                    "action_suggestion": "create_alerts",
                    "priority": "medium"
                })

            # Calculate potential savings (mock calculation for now)
            potential_savings = self._estimate_potential_savings(engagement_data, rec_effectiveness)

            # Determine engagement level
            if engagement_score >= 70:
                engagement_level = "high"
            elif engagement_score >= 40:
                engagement_level = "medium"
            else:
                engagement_level = "low"

            return {
                "insights": insights,
                "recommendations_for_improvement": recommendations,
                "usage_patterns": {
                    "most_common_action": max(engagement_data.get("interaction_breakdown", {}),
                                             key=engagement_data.get("interaction_breakdown", {}).get, default="view"),
                    "daily_avg_interactions": total_interactions / 30,
                    "engagement_trend": "stable"  # Could be calculated from daily trend
                },
                "savings_potential": potential_savings,
                "engagement_level": engagement_level,
                "generated_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to generate personal insights: {e}")
            return {
                "insights": [],
                "recommendations_for_improvement": [],
                "usage_patterns": {},
                "savings_potential": 0,
                "engagement_level": "unknown",
                "generated_at": datetime.utcnow()
            }

    async def aggregate_daily_analytics(self, db: AsyncSession, target_date: date = None) -> bool:
        """Aggregate daily analytics for all users."""
        if target_date is None:
            target_date = date.today() - timedelta(days=1)  # Previous day

        try:
            logger.info(f"Starting daily analytics aggregation for {target_date}")

            # Get all active users
            users_result = await db.execute(
                db.query(User.id).filter(User.is_active == True)
            )
            user_ids = [row.id for row in users_result]

            success_count = 0
            for user_id in user_ids:
                try:
                    await self._aggregate_user_daily_analytics(db, user_id, target_date)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to aggregate analytics for user {user_id}: {e}")

            logger.info(f"Completed daily analytics aggregation: {success_count}/{len(user_ids)} users")
            return True

        except Exception as e:
            logger.error(f"Failed to run daily analytics aggregation: {e}")
            return False

    # Private helper methods

    async def _get_recommendation_metrics(
        self, db: AsyncSession, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get recommendation-specific metrics."""
        rec_stats = await db.execute(
            db.query(
                func.count(Recommendation.id).label('total'),
                func.count(func.nullif(Recommendation.shown_to_user, False)).label('viewed'),
                func.avg(Recommendation.score).label('avg_score')
            )
            .filter(
                Recommendation.user_id == user_id,
                Recommendation.generated_at >= start_date,
                Recommendation.generated_at <= end_date
            )
        )
        stats = rec_stats.first()

        total = stats.total if stats else 0
        viewed = stats.viewed if stats else 0

        return {
            "total_received": total,
            "viewed": viewed,
            "view_rate": (viewed / total * 100) if total > 0 else 0,
            "avg_score": float(stats.avg_score or 0) if stats else 0
        }

    async def _get_product_engagement_metrics(
        self, db: AsyncSession, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get product interaction metrics."""
        product_interactions = await db.execute(
            db.query(
                func.count(func.distinct(
                    func.case([(UserInteraction.action_type == 'view', UserInteraction.resource_id)], else_=None)
                )).label('products_viewed'),
                func.count(func.distinct(
                    func.case([(UserInteraction.action_type == 'track', UserInteraction.resource_id)], else_=None)
                )).label('products_tracked'),
                func.count(func.distinct(
                    func.case([(UserInteraction.action_type == 'search', UserInteraction.id)], else_=None)
                )).label('searches_performed')
            )
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= start_date,
                UserInteraction.timestamp <= end_date,
                UserInteraction.resource_type == 'product'
            )
        )
        stats = product_interactions.first()

        return {
            "products_viewed": stats.products_viewed if stats else 0,
            "products_tracked": stats.products_tracked if stats else 0,
            "searches_performed": stats.searches_performed if stats else 0
        }

    async def _get_session_metrics(
        self, db: AsyncSession, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get session-based metrics."""
        # For now, return basic metrics (can be enhanced with actual session tracking)
        session_stats = await db.execute(
            db.query(
                func.count(func.distinct(UserInteraction.session_id)).label('unique_sessions'),
                func.count(UserInteraction.id).label('total_interactions')
            )
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= start_date,
                UserInteraction.timestamp <= end_date,
                UserInteraction.session_id.isnot(None)
            )
        )
        stats = session_stats.first()

        unique_sessions = stats.unique_sessions if stats else 1
        total_interactions = stats.total_interactions if stats else 0

        return {
            "unique_sessions": unique_sessions,
            "avg_interactions_per_session": total_interactions / unique_sessions if unique_sessions > 0 else 0,
            "estimated_session_duration": 5  # Mock value - would need actual session tracking
        }

    async def _get_daily_activity_trend(
        self, db: AsyncSession, user_id: UUID, days: int
    ) -> List[Dict[str, Any]]:
        """Get daily activity trend for the user."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        daily_activity = await db.execute(
            db.query(
                func.date(UserInteraction.timestamp).label('activity_date'),
                func.count(UserInteraction.id).label('interaction_count')
            )
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.timestamp >= start_date
            )
            .group_by(func.date(UserInteraction.timestamp))
            .order_by('activity_date')
        )

        return [
            {
                "date": row.activity_date.isoformat(),
                "interactions": row.interaction_count
            }
            for row in daily_activity
        ]

    def _calculate_engagement_score(
        self,
        interaction_breakdown: Dict[str, int],
        rec_metrics: Dict[str, Any],
        product_metrics: Dict[str, Any],
        session_metrics: Dict[str, Any]
    ) -> int:
        """Calculate overall engagement score (0-100)."""
        try:
            score = 0

            # Interaction diversity and volume (40% weight)
            total_interactions = sum(interaction_breakdown.values())
            interaction_types = len(interaction_breakdown)

            # More interactions = higher score (up to 25 points)
            score += min(25, total_interactions / 2)

            # More diverse actions = higher score (up to 15 points)
            score += min(15, interaction_types * 3)

            # Recommendation engagement (30% weight)
            rec_view_rate = rec_metrics.get("view_rate", 0)
            score += rec_view_rate * 0.3

            # Product engagement (30% weight)
            products_tracked = product_metrics.get("products_tracked", 0)
            products_viewed = product_metrics.get("products_viewed", 0)

            # Tracking shows deeper engagement
            score += min(15, products_tracked * 3)
            score += min(15, products_viewed * 0.5)

            return min(100, int(score))

        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0

    def _calculate_rec_effectiveness_score(
        self, total_recs: int, viewed_recs: int, action_breakdown: Dict[str, int]
    ) -> int:
        """Calculate recommendation effectiveness score."""
        if total_recs == 0:
            return 0

        view_rate = (viewed_recs / total_recs) * 100
        action_rate = (sum(action_breakdown.values()) / viewed_recs * 100) if viewed_recs > 0 else 0

        # Weight view rate (60%) and action rate (40%)
        effectiveness = (view_rate * 0.6) + (action_rate * 0.4)
        return min(100, int(effectiveness))

    def _estimate_potential_savings(
        self, engagement_data: Dict[str, Any], rec_effectiveness: Dict[str, Any]
    ) -> float:
        """Estimate potential savings from recommendations (mock calculation)."""
        # This is a simplified calculation - in reality would use actual price data
        total_recs = rec_effectiveness.get("total_recommendations", 0)
        avg_score = rec_effectiveness.get("avg_recommendation_score", 0)

        # Estimate based on recommendation quality and quantity
        estimated_savings = total_recs * avg_score * 100  # Mock formula
        return round(estimated_savings, 2)

    def _get_empty_engagement_summary(self, user_id: UUID, days: int) -> Dict[str, Any]:
        """Return empty engagement summary on error."""
        return {
            "user_id": str(user_id),
            "period_days": days,
            "total_interactions": 0,
            "interaction_breakdown": {},
            "recommendation_metrics": {},
            "product_metrics": {},
            "session_metrics": {},
            "engagement_score": 0,
            "daily_activity_trend": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _aggregate_user_daily_analytics(
        self, db: AsyncSession, user_id: UUID, target_date: date
    ) -> bool:
        """Aggregate daily analytics for a specific user."""
        # Implementation for daily aggregation would go here
        # This is a placeholder for the actual implementation
        return True