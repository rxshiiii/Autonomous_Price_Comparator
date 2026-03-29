"""
Scraping job model for tracking web scraping operations.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base
from app.db.base import IDMixin, TimestampMixin


class ScrapingJob(Base, IDMixin, TimestampMixin):
    """Scraping job model for monitoring web scraping operations."""

    __tablename__ = "scraping_jobs"

    job_type = Column(String(50), nullable=False)  # full_catalog, price_update, targeted
    platform = Column(String(50), nullable=False)  # flipkart, amazon, myntra, meesho
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed
    products_scraped = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    metadata = Column(JSONB)  # Additional job-specific data

    def __repr__(self):
        return f"<ScrapingJob(platform={self.platform}, status={self.status}, type={self.job_type})>"
