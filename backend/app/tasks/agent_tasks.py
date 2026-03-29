"""
Celery tasks for executing AI agents.
"""
import asyncio
from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.agents.recommendation_agent import RecommendationAgentOrchestrator
from app.agents.price_tracking_agent import PriceTrackingAgent
from app.agents.notification_agent import NotificationAgent
from app.agents.scraping_coordinator_agent import ScrapingCoordinatorAgent
from app.models.agent_execution import AgentExecution
from app.models.notification import Notification
from app.models.user import User
from app.services.email_service import email_service
from datetime import datetime
import structlog
from decimal import Decimal
from sqlalchemy import select


logger = structlog.get_logger()


def _async_task_wrapper(coro):
    """Wrapper to run async code in Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def run_recommendation_agent(self):
    """Execute recommendation agent for all active users."""
    try:
        async def execute():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select, distinct

                # Get all active users
                from app.models.user import User
                result = await db.execute(
                    select(User).where(User.is_active == True)
                )
                users = result.scalars().all()

                logger.info("recommendation_agent_task_started", user_count=len(users))

                orchestrator = RecommendationAgentOrchestrator(db)
                successful = 0
                failed = 0

                for user in users:
                    try:
                        result = await orchestrator.generate_recommendations_for_user(user.id)
                        if "error" not in result or not result.get("error"):
                            successful += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error("recommendation_generation_failed", user_id=user.id, error=str(e))
                        failed += 1

                logger.info("recommendation_agent_task_completed", successful=successful, failed=failed)
                return {"status": "completed", "successful": successful, "failed": failed}

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error("recommendation_agent_task_error", error=str(exc))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def run_price_tracking_agent(self):
    """Execute price tracking agent."""
    try:
        async def execute():
            start_time = datetime.utcnow()
            async with AsyncSessionLocal() as db:
                agent = PriceTrackingAgent(db)
                result = await agent.run()

                # Log execution
                execution = AgentExecution(
                    agent_type="price_tracking",
                    status="completed" if result.get("status") == "completed" else "failed",
                    input_data=None,
                    output_data={
                        "alerts_checked": result.get("alerts_checked", 0),
                        "alerts_triggered": result.get("alerts_triggered", 0),
                    },
                    error_message=result.get("error"),
                    started_at=start_time,
                    completed_at=datetime.utcnow(),
                    duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )
                db.add(execution)
                await db.commit()

                logger.info("price_tracking_agent_task_completed", result=result)
                return result

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error("price_tracking_agent_task_error", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def run_notification_agent(self):
    """Execute notification agent."""
    try:
        async def execute():
            start_time = datetime.utcnow()
            async with AsyncSessionLocal() as db:
                agent = NotificationAgent(db)
                result = await agent.run()

                # Log execution
                execution = AgentExecution(
                    agent_type="notification",
                    status="completed" if result.get("status") == "completed" else "failed",
                    input_data=None,
                    output_data={
                        "pending_count": result.get("pending_count", 0),
                        "processed_count": result.get("processed_count", 0),
                    },
                    error_message=result.get("error"),
                    started_at=start_time,
                    completed_at=datetime.utcnow(),
                    duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )
                db.add(execution)
                await db.commit()

                logger.info("notification_agent_task_completed", result=result)
                return result

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error("notification_agent_task_error", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def run_scraping_coordinator(self):
    """Execute scraping coordinator agent."""
    try:
        async def execute():
            start_time = datetime.utcnow()
            async with AsyncSessionLocal() as db:
                agent = ScrapingCoordinatorAgent(db)
                result = await agent.run()

                # Log execution
                execution = AgentExecution(
                    agent_type="scraping_coordinator",
                    status="completed" if result.get("status") == "completed" else "failed",
                    input_data=None,
                    output_data=result.get("products_by_platform", {}),
                    error_message=result.get("error"),
                    started_at=start_time,
                    completed_at=datetime.utcnow(),
                    duration_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )
                db.add(execution)
                await db.commit()

                logger.info("scraping_coordinator_task_completed", result=result)
                return result

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error("scraping_coordinator_task_error", error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# Phase 5: Email Notification Tasks

@celery_app.task(bind=True, max_retries=3)
def send_notification_email_task(self, user_id: str, notification_id: str):
    """
    Send notification email asynchronously.

    Args:
        user_id: User UUID string
        notification_id: Notification UUID string
    """
    try:
        async def execute():
            async with AsyncSessionLocal() as db:
                # Get user
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    logger.error("email_task_user_not_found", user_id=user_id)
                    return {"success": False, "error": "User not found"}

                # Get notification
                notification_result = await db.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = notification_result.scalar_one_or_none()

                if not notification:
                    logger.error("email_task_notification_not_found", notification_id=notification_id)
                    return {"success": False, "error": "Notification not found"}

                # Send email
                success = await email_service.send_notification_email(user, notification)

                logger.info(
                    "email_notification_task_completed",
                    user_id=user_id,
                    notification_id=notification_id,
                    success=success
                )

                return {
                    "success": success,
                    "user_id": user_id,
                    "notification_id": notification_id
                }

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error(
            "email_notification_task_error",
            error=str(exc),
            user_id=user_id,
            notification_id=notification_id
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=3)
def send_price_drop_email_task(self, user_id: str, product_data: dict, price_change: dict):
    """
    Send price drop alert email asynchronously.

    Args:
        user_id: User UUID string
        product_data: Product information dictionary
        price_change: Price change information dictionary
    """
    try:
        async def execute():
            async with AsyncSessionLocal() as db:
                # Get user
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    logger.error("price_drop_email_user_not_found", user_id=user_id)
                    return {"success": False, "error": "User not found"}

                # Send price drop email
                success = await email_service.send_price_drop_alert(user, product_data, price_change)

                logger.info(
                    "price_drop_email_task_completed",
                    user_id=user_id,
                    product_name=product_data.get("name"),
                    success=success
                )

                return {
                    "success": success,
                    "user_id": user_id,
                    "product_name": product_data.get("name")
                }

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error(
            "price_drop_email_task_error",
            error=str(exc),
            user_id=user_id
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(bind=True, max_retries=2)
def send_weekly_summary_email_task(self, user_id: str, summary_data: dict):
    """
    Send weekly summary email asynchronously.

    Args:
        user_id: User UUID string
        summary_data: Weekly summary data dictionary
    """
    try:
        async def execute():
            async with AsyncSessionLocal() as db:
                # Get user
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    logger.error("weekly_summary_email_user_not_found", user_id=user_id)
                    return {"success": False, "error": "User not found"}

                # Send weekly summary email
                success = await email_service.send_weekly_summary(user, summary_data)

                logger.info(
                    "weekly_summary_email_task_completed",
                    user_id=user_id,
                    success=success
                )

                return {
                    "success": success,
                    "user_id": user_id
                }

        return _async_task_wrapper(execute())

    except Exception as exc:
        logger.error(
            "weekly_summary_email_task_error",
            error=str(exc),
            user_id=user_id
        )
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
