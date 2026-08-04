# app/db/models/organization.py
"""
Organization Model - Matches actual database schema
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    # Match EXACTLY what's in your database
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name = Column(String(255), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )

    # Relationships
    # TEMPORARILY DISABLED: Requires User.organization_id which doesn't exist in database
    # users = relationship("User", back_populates="organization", foreign_keys="[User.organization_id]")  # TEMPORARILY DISABLED
    # Team relationship - teams table has organization_id column
    # teams = relationship("Team", back_populates="organization")  # TEMPORARILY DISABLED

    # Intervention relationships
    # interventions = relationship("Intervention", back_populates="organization")  # TEMPORARILY DISABLED

    # Employee Safety relationships - Temporarily disabled due to circular import
    # safety_incidents = relationship("SafetyIncident", back_populates="organization")  # TEMPORARILY DISABLED
    # safety_resources = relationship("SafetyResource", back_populates="organization")  # TEMPORARILY DISABLED
    # safety_training = relationship("SafetyTraining", back_populates="organization")  # TEMPORARILY DISABLED
    # wellness_assessments = relationship("WellnessAssessment", back_populates="organization")  # TEMPORARILY DISABLED

    # Growth trajectory relationships
    # growth_trajectories = relationship("GrowthTrajectory", back_populates="organization")  # TEMPORARILY DISABLED

    # Email Analysis Relationships - Temporarily disabled
    # communication_patterns = relationship("CommunicationPatterns", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # culture_metrics = relationship("CultureMetrics", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # coaching_recommendations = relationship("CoachingRecommendation", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # communication_alerts = relationship("CommunicationAlert", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED

    # Anonymous Feedback Relationships
    # anonymous_feedback = relationship("AnonymousFeedback", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # feedback_patterns = relationship("AnonymousFeedbackPattern", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # feedback_templates = relationship("AnonymousFeedbackTemplate", back_populates="organization", cascade="all, delete-orphan")  # TEMPORARILY DISABLED

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
