"""
Agent Execution model for tracking AI agent runs and results.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.session import Base
from app.db.base import IDMixin


class AgentExecution(Base, IDMixin):
    """Model for tracking agent executions."""

    __tablename__ = "agent_executions"

    agent_type = Column(String(50), nullable=False)  # recommendation, price_tracking, notification, scraping_coordinator
    user_id = Column(UUID(as_uuid=True), nullable=True)  # For user-specific agents
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    input_data = Column(JSONB, nullable=True)  # Agent input parameters
    output_data = Column(JSONB, nullable=True)  # Agent output results
    error_message = Column(Text, nullable=True)  # Error details if failed
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Execution duration in milliseconds

    __table_args__ = (
        Index("idx_agent_executions_type_created", "agent_type", "started_at", postgresql_using="btree"),
        Index("idx_agent_executions_user_status", "user_id", "status", postgresql_using="btree"),
    )

    def __repr__(self):
        return f"<AgentExecution(agent_type={self.agent_type}, status={self.status})>"
