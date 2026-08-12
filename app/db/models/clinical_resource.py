"""
ClinicalResource — admin-managed directory of therapists, support groups, and resources.
"""

import uuid

from sqlalchemy import Boolean, Column, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.core.database import Base


class ClinicalResource(Base):
    __tablename__ = "clinical_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(
        String(20), nullable=False, index=True
    )  # therapist|group|resource
    name = Column(String(255), nullable=False)
    credentials = Column(ARRAY(String), nullable=True)
    specializations = Column(ARRAY(String), nullable=True)
    languages = Column(ARRAY(String), nullable=True)
    telehealth = Column(Boolean, nullable=True, default=False)
    insurance = Column(ARRAY(String), nullable=True)
    rating = Column(Float, nullable=True)
    distance = Column(String(50), nullable=True)
    consultation_fee = Column(String(50), nullable=True)
    availability = Column(String(100), nullable=True)
    # For groups/resources
    meeting_schedule = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
