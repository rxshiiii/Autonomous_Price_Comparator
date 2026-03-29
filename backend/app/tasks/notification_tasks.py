"""
Celery tasks for notification sending.
"""
from app.tasks.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task
def send_pending_notifications():
    """
    Send pending notifications to users.

    This task will be fully implemented in Phase 5 when we add the Notification Agent.
    """
    logger.info("sending_pending_notifications")
    return {"status": "ok", "message": "Notification sending task (Phase 5)"}
