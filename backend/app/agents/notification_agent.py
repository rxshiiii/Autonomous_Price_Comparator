"""
Notification Agent for intelligent notification prioritization and delivery.
Enhanced with real-time WebSocket and email delivery (Phase 5).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.models.notification import Notification
from app.models.notification_preferences import UserNotificationPreferences
from app.models.user import User
from app.websockets.connection_manager import websocket_manager
from app.services.email_service import email_service
from app.tasks.celery_app import celery_app
import structlog


logger = structlog.get_logger()


class NotificationAgent(BaseAgent):
    """Agent for managing notification delivery and prioritization with real-time delivery."""

    def __init__(self, db: AsyncSession):
        """Initialize notification agent."""
        super().__init__()
        self.db = db
        self.logger = logger.bind(agent="notification")

    async def run(self) -> Dict[str, Any]:
        """Execute notification workflow with real-time delivery."""
        self.logger.info("notification_agent_started")

        try:
            # Fetch all pending notifications (sent_at is None)
            result = await self.db.execute(
                select(Notification).where(Notification.sent_at == None)
            )
            pending = result.scalars().all()

            self.logger.info("pending_notifications", count=len(pending))

            processed_count = 0
            websocket_delivered = 0
            email_queued = 0

            # Group by user
            by_user: Dict[str, List[Notification]] = {}
            for notif in pending:
                user_id = str(notif.user_id)
                if user_id not in by_user:
                    by_user[user_id] = []
                by_user[user_id].append(notif)

            # Process each user
            for user_id_str, user_notifications in by_user.items():
                # Get user and preferences
                user_result = await self.db.execute(
                    select(User).where(User.id == user_id_str)
                )
                user = user_result.scalar_one_or_none()

                if not user or not user.is_active:
                    continue

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

                # PHASE 5: Send notifications with real-time delivery
                for notif in ranked[:max_daily - sent_today]:
                    delivery_results = await self._deliver_notification(notif, user, prefs)

                    # Update statistics
                    if delivery_results["websocket_sent"]:
                        websocket_delivered += 1
                    if delivery_results["email_queued"]:
                        email_queued += 1

                    # Mark as sent (regardless of delivery method)
                    notif.sent_at = datetime.utcnow()
                    self.db.add(notif)
                    processed_count += 1

            await self.db.commit()

            self.logger.info(
                "notification_processing_completed",
                processed=processed_count,
                websocket_delivered=websocket_delivered,
                email_queued=email_queued
            )

            return {
                "status": "completed",
                "pending_count": len(pending),
                "processed_count": processed_count,
                "websocket_delivered": websocket_delivered,
                "email_queued": email_queued
            }

        except Exception as e:
            self.logger.error("notification_agent_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    async def _deliver_notification(
        self,
        notification: Notification,
        user: User,
        prefs: Optional[UserNotificationPreferences]
    ) -> Dict[str, bool]:
        """
        Deliver notification via multiple channels.

        Args:
            notification: Notification to deliver
            user: User to deliver to
            prefs: User notification preferences

        Returns:
            Dictionary with delivery results
        """
        websocket_sent = False
        email_queued = False

        try:
            # 1. WebSocket delivery (real-time)
            if not prefs or prefs.websocket_enabled:
                websocket_sent = await self._send_websocket_notification(notification, user)

            # 2. Email delivery (async via Celery)
            if not prefs or prefs.email_enabled:
                email_queued = await self._queue_email_notification(notification, user)

            self.logger.info(
                "notification_delivered",
                notification_id=str(notification.id),
                user_id=str(user.id),
                websocket_sent=websocket_sent,
                email_queued=email_queued,
                notification_type=notification.notification_type
            )

        except Exception as e:
            self.logger.error(
                "notification_delivery_error",
                error=str(e),
                notification_id=str(notification.id),
                user_id=str(user.id)
            )

        return {
            "websocket_sent": websocket_sent,
            "email_queued": email_queued
        }

    async def _send_websocket_notification(self, notification: Notification, user: User) -> bool:
        """Send notification via WebSocket if user is connected."""
        try:
            # Format notification data for WebSocket
            notification_data = {
                "id": str(notification.id),
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "data": notification.data or {},
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat(),
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None
            }

            # Send via WebSocket manager
            sent = await websocket_manager.send_notification(notification_data, user.id)

            if sent:
                self.logger.debug(
                    "websocket_notification_sent",
                    user_id=str(user.id),
                    notification_id=str(notification.id)
                )
            else:
                self.logger.debug(
                    "websocket_user_not_connected",
                    user_id=str(user.id),
                    notification_id=str(notification.id)
                )

            return sent

        except Exception as e:
            self.logger.error("websocket_notification_error", error=str(e))
            return False

    async def _queue_email_notification(self, notification: Notification, user: User) -> bool:
        """Queue email notification for async delivery."""
        try:
            # Queue email task via Celery
            from app.tasks.agent_tasks import send_notification_email_task

            send_notification_email_task.delay(
                user_id=str(user.id),
                notification_id=str(notification.id)
            )

            self.logger.debug(
                "email_notification_queued",
                user_id=str(user.id),
                notification_id=str(notification.id)
            )

            return True

        except Exception as e:
            self.logger.error("email_notification_queue_error", error=str(e))
            return False

    async def _rank_notifications(self, notifications: List[Notification]) -> List[Notification]:
        """Rank notifications by importance using enhanced priority logic."""
        if not notifications:
            return notifications

        if len(notifications) <= 1:
            return notifications

        # Enhanced priority system for Phase 5
        priority_map = {
            "price_drop": 3,        # Highest priority - immediate action needed
            "back_in_stock": 3,     # High priority - limited availability
            "new_recommendation": 2, # Medium priority - discovery
            "system_message": 1,    # Low priority - informational
        }

        # Secondary sort by creation time (newer first)
        ranked = sorted(
            notifications,
            key=lambda n: (
                priority_map.get(n.notification_type, 0),
                n.created_at.timestamp()
            ),
            reverse=True
        )

        # FUTURE: Use GROQ for intelligent ranking based on user behavior
        # This could analyze user preferences, time of day, past interactions
        # to optimize notification timing and relevance

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

    # PHASE 5: New utility methods for enhanced functionality

    async def send_immediate_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send immediate notification (bypasses agent scheduling).
        Useful for urgent notifications or manual triggers.
        """
        try:
            # Get user
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                return {"success": False, "error": "User not found"}

            # Create notification
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data,
                is_read=False,
                sent_at=datetime.utcnow()
            )

            self.db.add(notification)
            await self.db.commit()

            # Get user preferences
            prefs_result = await self.db.execute(
                select(UserNotificationPreferences).where(
                    UserNotificationPreferences.user_id == user_id
                )
            )
            prefs = prefs_result.scalar_one_or_none()

            # Deliver immediately
            delivery_results = await self._deliver_notification(notification, user, prefs)

            return {
                "success": True,
                "notification_id": str(notification.id),
                "delivery_results": delivery_results
            }

        except Exception as e:
            self.logger.error("immediate_notification_error", error=str(e))
            return {"success": False, "error": str(e)}
