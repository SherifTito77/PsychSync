"""
ScheduledReport model — stores user-configured automated report schedules.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    frequency = Column(String(20), nullable=False, default="weekly")  # weekly | monthly
    recipients = Column(JSON, nullable=False, default=list)
    format = Column(String(10), nullable=False, default="pdf")  # pdf | html
    status = Column(String(20), nullable=False, default="active")  # active | paused
    include_charts = Column(Boolean, nullable=False, default=True)
    next_run = Column(DateTime(timezone=True), nullable=True)
    last_run = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
