"""
CorporateIntegration model — persists per-org integration state.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class CorporateIntegration(Base):
    __tablename__ = "corporate_integrations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id = Column(String(36), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # who set it up
    source_type = Column(String(64), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    status = Column(
        String(20), nullable=False, default="pending"
    )  # active|disabled|error|pending
    last_sync = Column(DateTime(timezone=True), nullable=True)
    next_sync = Column(DateTime(timezone=True), nullable=True)
    records_processed = Column(Integer, nullable=False, default=0)
    health_score = Column(Float, nullable=False, default=1.0)
    api_credentials = Column(JSON, nullable=True)
    custom_settings = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
