# app/db/models/organization.py
"""
Organization Model - Matches actual database schema
"""
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    # Match EXACTLY what's in your database
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('NOW()'), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="organization", foreign_keys="[User.organization_id]")
    # teams = relationship("Team", back_populates="organization", foreign_keys="[Team.organization_id]")

    # Email Analysis Relationships - Temporarily disabled
    # communication_patterns = relationship("CommunicationPatterns", back_populates="organization", cascade="all, delete-orphan")
    # culture_metrics = relationship("CultureMetrics", back_populates="organization", cascade="all, delete-orphan")
    # coaching_recommendations = relationship("CoachingRecommendation", back_populates="organization", cascade="all, delete-orphan")
    # communication_alerts = relationship("CommunicationAlert", back_populates="organization", cascade="all, delete-orphan")

    # Anonymous Feedback Relationships
    # anonymous_feedback = relationship("AnonymousFeedback", back_populates="organization", cascade="all, delete-orphan")
    # feedback_patterns = relationship("AnonymousFeedbackPattern", back_populates="organization", cascade="all, delete-orphan")
    # feedback_templates = relationship("AnonymousFeedbackTemplate", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"