"""
Celery application configuration and task setup.
"""
from celery import Celery
from app.config import settings
import structlog

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "price_comparator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Define task schedule for Celery Beat
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Scrape Flipkart every 2 hours
    "scrape-flipkart": {
        "task": "app.tasks.scraping_tasks.scrape_platform",
        "schedule": crontab(minute=0, hour="*/2"),
        "args": ("flipkart", "trending products"),
    },
    # Scrape Amazon every 3 hours
    "scrape-amazon": {
        "task": "app.tasks.scraping_tasks.scrape_platform",
        "schedule": crontab(minute=0, hour="*/3"),
        "args": ("amazon", "trending products"),
    },
    # Scrape Myntra every 2 hours
    "scrape-myntra": {
        "task": "app.tasks.scraping_tasks.scrape_platform",
        "schedule": crontab(minute=0, hour="*/2"),
        "args": ("myntra", "clothing"),
    },
    # Scrape Meesho every 2 hours
    "scrape-meesho": {
        "task": "app.tasks.scraping_tasks.scrape_platform",
        "schedule": crontab(minute=0, hour="*/2"),
        "args": ("meesho", "trending products"),
    },
    # Check price changes every hour
    "check-price-changes": {
        "task": "app.tasks.price_monitoring_tasks.check_price_changes",
        "schedule": crontab(minute=0),
    },
    # Send notifications every 30 minutes
    "send-notifications": {
        "task": "app.tasks.notification_tasks.send_pending_notifications",
        "schedule": crontab(minute="*/30"),
    },
}

logger.info("celery_app_initialized", broker=settings.CELERY_BROKER_URL)
