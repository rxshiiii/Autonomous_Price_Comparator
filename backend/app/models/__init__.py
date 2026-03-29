"""
Database models package.
Import all models here so Alembic can detect them.
"""
from app.db.session import Base
from app.models.user import User, UserPreference, UserTrackedProduct
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.models.price_alert import PriceAlert
from app.models.notification import Notification
from app.models.recommendation import Recommendation
from app.models.scraping_job import ScrapingJob

__all__ = [
    "Base",
    "User",
    "UserPreference",
    "UserTrackedProduct",
    "Product",
    "PriceHistory",
    "PriceAlert",
    "Notification",
    "Recommendation",
    "ScrapingJob",
]
