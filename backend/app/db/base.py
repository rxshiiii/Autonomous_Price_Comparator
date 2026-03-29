"""
Base database model with common fields.
"""
from datetime import datetime
import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class IDMixin:
    """Mixin for UUID primary key."""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
