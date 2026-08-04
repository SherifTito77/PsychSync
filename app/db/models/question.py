# app/db/models/question.py
import sqlalchemy as sa
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Question(Base):
    __tablename__ = "framework_questions"

    id = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    text = sa.Column(sa.String, nullable=False)
    framework_id = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("frameworks.id"), nullable=False
    )
    created_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )
    updated_at = sa.Column(
        sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )
    type = Column(String, nullable=False)
    assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE")
    )

    # assessment relationship removed to avoid conflicts with Assessment.assessments_questions relationship
