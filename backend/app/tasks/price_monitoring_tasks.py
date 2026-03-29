"""
Celery tasks for price monitoring and tracking.
"""
from app.tasks.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task
def check_price_changes():
    """
    Check for price changes in tracked products.

    This task will be implemented in Phase 4 when we add the Price Tracking Agent.
    """
    logger.info("checking_price_changes")
    return {"status": "ok", "message": "Price check task (Phase 4)"}
