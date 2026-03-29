"""
Notification Agent for intelligent notification prioritization and delivery.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.models.notification import Notification
from app.models.user_notification_preferences import UserNotificationPreferences
import structlog


logger = structlog.get_logger()


class NotificationAgent(BaseAgent):
    """Agent for managing notification delivery and prioritization."""

    def __init__(self, db: AsyncSession):
        """Initialize notification agent."""
        super().__init__()
        self.db = db
        self.logger = logger.bind(agent="notification")

    async def run(self) -> Dict[str, Any]:
        """Execute notification workflow."""
        self.logger.info("notification_agent_started")

        try:
            # Fetch all pending notifications (sent_at is None)
            result = await self.db.execute(
                select(Notification).where(Notification.sent_at == None)
            )
            pending = result.scalars().all()

            self.logger.info("pending_notifications", count=len(pending))

            processed_count = 0

            # Group by user
            by_user: Dict[str, List[Notification]] = {}
            for notif in pending:
                user_id = str(notif.user_id)
                if user_id not in by_user:
                    by_user[user_id] = []
                by_user[user_id].append(notif)

            # Process each user
            for user_id_str, user_notifications in by_user.items():
                # Get user preferences
                prefs_result = await self.db.execute(
                    select(UserNotificationPreferences).where(
                        UserNotificationPreferences.user_id == user_id_str
                    )
                )
                prefs = prefs_result.scalar_one_or_none()

                # Check quiet hours
                if prefs and self._is_quiet_hours(prefs.notification_quiet_hours_start, prefs.notification_quiet_hours_end):
                    self.logger.info("skipping_quiet_hours", user_id=user_id_str)
                    continue

                # Check daily limit
                max_daily = prefs.max_notifications_per_day if prefs else 5
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

                result = await self.db.execute(
                    select(func.count(Notification.id)).where(
                        and_(
                            Notification.user_id == user_id_str,
                            Notification.sent_at >= today_start,
                            Notification.sent_at != None
                        )
                    )
                )
                sent_today = result.scalar() or 0

                notifications_to_send = user_notifications[:max(1, max_daily - sent_today)]

                # Rank notifications by importance
                ranked = await self._rank_notifications(notifications_to_send)

                # Send notifications (mark as sent)
                for notif in ranked[:max_daily - sent_today]:
                    notif.sent_at = datetime.utcnow()
                    self.db.add(notif)
                    processed_count += 1

            await self.db.commit()

            self.logger.info("notification_processing_completed", processed=processed_count)

            return {
                "status": "completed",
                "pending_count": len(pending),
                "processed_count": processed_count,
            }

        except Exception as e:
            self.logger.error("notification_agent_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def _rank_notifications(self, notifications: List[Notification]) -> List[Notification]:
        """Rank notifications by importance using GROQ."""
        if not notifications:
            return notifications

        if len(notifications) <= 1:
            return notifications

        # For now, use simple priority: price_drop > recommendation > other
        priority_map = {
            "price_drop": 2,
            "new_recommendation": 1,
            "back_in_stock": 2,
        }

        ranked = sorted(
            notifications,
            key=lambda n: priority_map.get(n.notification_type, 0),
            reverse=True
        )

        self.logger.info("notifications_ranked", count=len(ranked))
        return ranked

    def _is_quiet_hours(self, start_time: time, end_time: time) -> bool:
        """Check if current time is within quiet hours."""
        current = datetime.utcnow().time()

        # Handle wrap-around (e.g., 22:00 to 09:00)
        if start_time <= end_time:
            return start_time <= current <= end_time
        else:
            return current >= start_time or current <= end_time
