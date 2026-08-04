# app/db/models/team.py
import enum

from sqlalchemy import Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base


class TeamRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Team(Base):
    __tablename__ = "teams"

    # Match database after removing org_id
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name = Column(Text, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False
    )
    description = Column(Text, nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=True
    )
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )

    # Relationships
    # created_by = relationship(  # TEMPORARILY DISABLED
    #     "User", back_populates="teams_created", foreign_keys=[created_by_id], lazy="select"
    # )

    # organization = relationship(  # TEMPORARILY DISABLED
    #     "Organization", back_populates="teams", foreign_keys=[organization_id], lazy="select"
    # )

    # members = relationship(  # TEMPORARILY DISABLED
    #     "TeamMember",
    #     back_populates="team",
    #     cascade="all, delete-orphan",
    #     foreign_keys="[TeamMember.team_id]",
    # )

    # Employee Safety relationships - Temporarily disabled due to circular import
    # safety_incidents = relationship("SafetyIncident", back_populates="team")  # TEMPORARILY DISABLED
    # wellness_assessments = relationship("WellnessAssessment", back_populates="team")  # TEMPORARILY DISABLED

    # Growth trajectory relationships
    # growth_trajectories = relationship("GrowthTrajectory", back_populates="team")  # TEMPORARILY DISABLED

    # assessments = relationship(  # TEMPORARILY DISABLED
    #     "Assessment", back_populates="team", foreign_keys="[Assessment.team_id]"
    # )

    # Intervention relationships
    # interventions = relationship("Intervention", back_populates="team")  # TEMPORARILY DISABLED

    # Email Analysis Relationships - Temporarily disabled
    # communication_patterns = relationship("CommunicationPatterns", back_populates="team", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # culture_metrics = relationship("CultureMetrics", back_populates="team", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # coaching_recommendations = relationship("CoachingRecommendation", back_populates="team", cascade="all, delete-orphan")  # TEMPORARILY DISABLED
    # communication_alerts = relationship("CommunicationAlert", back_populates="team", cascade="all, delete-orphan")  # TEMPORARILY DISABLED

    # Define table indexes for performance
    __table_args__ = (
        Index("idx_teams_org_created", "organization_id", "created_at"),
        Index("idx_teams_creator", "created_by_id", "created_at"),
        Index("idx_teams_name_search", "name"),  # For text search
        Index("idx_teams_lookup", "organization_id", "id"),
    )

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"


class TeamMember(Base):
    __tablename__ = "team_members"

    # Only include columns that exist in your actual database
    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(TeamRole), default=TeamRole.MEMBER, nullable=False)
    # REMOVED joined_at - doesn't exist in database

    # Define table constraints and indexes for performance
    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member_user"),
        Index("idx_team_members_team_role", "team_id", "role"),
        Index("idx_team_members_user_active", "user_id"),
        Index("idx_team_members_lookup", "team_id", "user_id", "role"),
    )

    # Relationships
    # team = relationship("Team", back_populates="members", foreign_keys=[team_id])  # TEMPORARILY DISABLED

    # user = relationship("User", back_populates="team_memberships", foreign_keys=[user_id])  # TEMPORARILY DISABLED

    def __repr__(self):
        return f"<TeamMember(team_id={self.team_id}, user_id={self.user_id}, role={self.role})>"
