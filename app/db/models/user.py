# app/db/models/user.py
from enum import Enum as PyEnum

from sqlalchemy import ARRAY, Boolean, Column, DateTime, Index, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CitextString(TypeDecorator):
    """Platform-independent CITEXT type.

    Uses CITEXT on PostgreSQL, falls back to String for other databases.
    This allows tests to use SQLite while production uses PostgreSQL.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Use PostgreSQL CITEXT when available"""
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import CITEXT

            return dialect.type_descriptor(CITEXT())
        return dialect.type_descriptor(String(255))


class UserRole(PyEnum):
    """User role enumeration"""

    ADMIN = "ADMIN"
    USER = "USER"
    TEAM_LEAD = "TEAM_LEAD"


class User(Base):
    __tablename__ = "users"

    # Primary columns
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    email = Column(CitextString, nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=True)  # Exists in database
    password_hash = Column(Text, nullable=False)
    full_name = Column(Text, nullable=True)

    # TEMPORARILY DISABLED: These columns don't exist in database
    # avatar_url = Column(Text, nullable=True)
    # role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    # is_active = Column(Boolean, nullable=False, server_default='true')

    # Additional fields for comprehensive user management
    # timezone = Column(String(50), nullable=True, default='UTC')
    # locale = Column(String(10), nullable=True, default='en-US')
    # preferences = Column(JSONB, nullable=True)  # User preferences as JSON

    # Authentication fields
    # is_verified = Column(Boolean, nullable=False, server_default='false')
    is_superuser = Column(Boolean, nullable=False, server_default="false")
    # last_login = Column(DateTime(timezone=True), nullable=True)

    # Email verification
    # email_verification_token = Column(Text, nullable=True)
    # email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Password reset
    # password_reset_token = Column(Text, nullable=True)
    # password_reset_expires = Column(DateTime(timezone=True), nullable=True)

    # Two-Factor Authentication (2FA)
    two_factor_enabled = Column(Boolean, nullable=False, server_default="false")
    two_factor_secret = Column(String(255), nullable=True)  # TOTP secret
    two_factor_recovery_codes = Column(ARRAY(String), nullable=True)  # Backup recovery codes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # deleted_at = Column(DateTime(timezone=True), nullable=True)

    # TEMPORARILY DISABLED: Add is_active if needed
    is_active = Column(Boolean, nullable=False, server_default="true")

    # Foreign keys
    # TEMPORARILY DISABLED: organization_id column doesn't exist in database
    # organization_id = Column(
    #     UUID(as_uuid=True),
    #     ForeignKey('organizations.id'),  # Add foreign key constraint
    #     nullable=True,  # Make nullable if not all users have orgs
    #     index=True  # Add index for performance
    # )

    # Relationships with proper string references to avoid circular imports
    # templates_created = relationship(
    #     "Template",
    #     back_populates="created_by_user",
    #     foreign_keys="Template.created_by_id",
    #     lazy="dynamic"
    # )

    # Organization relationship - properly configured
    # TEMPORARILY DISABLED: Organization relationship requires organization_id column
    # organization = relationship("Organization", back_populates="users", lazy="joined")

    # Define table indexes for performance
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        # Index('idx_user_org_active', 'organization_id', 'is_active'),  # Disabled with organization_id
        Index("idx_user_created_at", "created_at"),
        # Index('idx_user_last_login', 'last_login'),  # Disabled - column doesn't exist
    )

    # Other relationships (add as needed)
    assessments_created = relationship("Assessment", back_populates="created_by")
    teams_created = relationship("Team", back_populates="created_by")
    team_memberships = relationship("TeamMember", back_populates="user")
    responses = relationship("Response", back_populates="user")

    # Intervention relationships
    created_interventions = relationship("Intervention", back_populates="created_by_user")
    intervention_participations = relationship("InterventionParticipant", back_populates="user")
    pre_intervention_measurements = relationship(
        "PreInterventionMeasurement", back_populates="user"
    )
    post_intervention_measurements = relationship(
        "PostInterventionMeasurement", back_populates="user"
    )

    # Growth trajectory relationships
    growth_trajectories = relationship("GrowthTrajectory", back_populates="user")
    growth_potential_analyses = relationship("GrowthPotentialAnalysis", back_populates="user")

    # Employee Safety relationships
    reported_incidents = relationship(
        "SafetyIncident", foreign_keys="SafetyIncident.reporter_id", back_populates="reporter"
    )
    involved_incidents = relationship(
        "SafetyIncident",
        foreign_keys="SafetyIncident.affected_user_id",
        back_populates="affected_user",
    )
    investigated_incidents = relationship(
        "SafetyIncident",
        foreign_keys="SafetyIncident.investigator_id",
        back_populates="investigator",
    )
    wellness_assessments = relationship("WellnessAssessment", back_populates="user")
    wellness_alerts = relationship(
        "WellnessAlert", foreign_keys="WellnessAlert.user_id", back_populates="user"
    )
    safety_training_completions = relationship("SafetyTrainingCompletion", back_populates="user")

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
