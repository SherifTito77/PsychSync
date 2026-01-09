# app/schemas/team.py
"""
Team Schemas - Fixed to use UUID instead of int
Includes all backward compatibility aliases
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# Base Team Schema
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


# Team Create Schema
class TeamCreate(TeamBase):
    pass


# Team Update Schema
class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


# Team Member Base
class TeamMemberBase(BaseModel):
    user_id: UUID
    role: TeamRole = TeamRole.MEMBER


# Team Member Create
class TeamMemberCreate(TeamMemberBase):
    pass


# Team Member Update
class TeamMemberUpdate(BaseModel):
    role: TeamRole


# Team Member Response
class TeamMemberResponse(TeamMemberBase):
    id: UUID
    team_id: UUID

    model_config = ConfigDict(from_attributes=True)


# User Info (for team member display)
class UserInfo(BaseModel):
    id: UUID
    email: str
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Team Member with User Info
class TeamMemberWithUser(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    role: TeamRole
    user: UserInfo | None = None

    model_config = ConfigDict(from_attributes=True)


# Team Response Schema
class TeamResponse(TeamBase):
    id: UUID
    created_by_id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# Team with Members
class TeamWithMembers(TeamResponse):
    members: list[TeamMemberWithUser] = []

    model_config = ConfigDict(from_attributes=True)


# Team List Response
class TeamListResponse(BaseModel):
    teams: list[TeamResponse]
    total: int


# ============================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================
Team = TeamResponse
TeamSchema = TeamResponse
TeamInDB = TeamResponse
TeamOut = TeamResponse

TeamMember = TeamMemberResponse
TeamMemberSchema = TeamMemberResponse
TeamMemberInDB = TeamMemberResponse
TeamMemberOut = TeamMemberResponse

TeamList = TeamListResponse
TeamListSchema = TeamListResponse

# Export all
__all__ = [
    # Enums
    "TeamRole",
    # Base classes
    "TeamBase",
    "TeamMemberBase",
    # Create/Update
    "TeamCreate",
    "TeamUpdate",
    "TeamMemberCreate",
    "TeamMemberUpdate",
    # Responses
    "TeamResponse",
    "TeamMemberResponse",
    "TeamWithMembers",
    "TeamMemberWithUser",
    "TeamListResponse",
    "UserInfo",
    # Aliases (for backward compatibility)
    "Team",
    "TeamSchema",
    "TeamInDB",
    "TeamOut",
    "TeamMember",
    "TeamMemberSchema",
    "TeamMemberInDB",
    "TeamMemberOut",
    "TeamList",
    "TeamListSchema",
]
