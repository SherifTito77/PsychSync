# app/db/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, CITEXT, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # Primary columns
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    email = Column(CITEXT, nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default='true')

    # Additional fields for comprehensive user management
    timezone = Column(String(50), nullable=True, default='UTC')
    locale = Column(String(10), nullable=True, default='en-US')
    preferences = Column(JSONB, nullable=True)  # User preferences as JSON

    # Authentication fields
    is_verified = Column(Boolean, nullable=False, server_default='false')
    is_superuser = Column(Boolean, nullable=False, server_default='false')
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Email verification
    email_verification_token = Column(Text, nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Password reset
    password_reset_token = Column(Text, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys - temporarily removed constraint
    organization_id = Column(
        UUID(as_uuid=True),
        nullable=True,  # Make nullable if not all users have orgs
        index=True  # Add index for performance
    )

    # Relationships with proper string references to avoid circular imports
    # templates_created = relationship(
    #     "Template",
    #     back_populates="created_by_user",
    #     foreign_keys="Template.created_by_id",
    #     lazy="dynamic"
    # )

    # Organization relationship - temporarily commented out to avoid circular import
    # organization = relationship("Organization", back_populates="users", lazy="joined")

    # Define table indexes for performance
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_org_active', 'organization_id', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_last_login', 'last_login'),
    )

    # Other relationships (add as needed)
    # assessments_created = relationship("Assessment", back_populates="created_by")
    # team_memberships = relationship("TeamMember", back_populates="user")

    # Email Analysis Relationships - Temporarily disabled due to missing tables
    # email_connections = relationship("EmailConnection", back_populates="user", cascade="all, delete-orphan")
    # email_metadata = relationship("EmailMetadata", back_populates="user", cascade="all, delete-orphan")
    # communication_analyses = relationship("CommunicationAnalysis", back_populates="user", cascade="all, delete-orphan")
    # communication_patterns = relationship("CommunicationPatterns", back_populates="user", cascade="all, delete-orphan")
    # coaching_recommendations = relationship("CoachingRecommendation", back_populates="user", cascade="all, delete-orphan")
    # user_alerts = relationship("CommunicationAlert", foreign_keys="CommunicationAlert.user_id", back_populates="user", cascade="all, delete-orphan")
    # acknowledged_alerts = relationship("CommunicationAlert", foreign_keys="CommunicationAlert.acknowledged_by", back_populates="acknowledged_user")
    # assigned_alerts = relationship("CommunicationAlert", foreign_keys="CommunicationAlert.assigned_to", back_populates="assigned_user")
    # managed_recommendations = relationship("CoachingRecommendation", foreign_keys="CoachingRecommendation.manager_id", back_populates="manager")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"