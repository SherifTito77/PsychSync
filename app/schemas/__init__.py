# app/schemas/__init__.py

from .user import UserCreate, UserOut, UserRead, UserResponse, UserUpdate

# Import auth schemas
try:
    from .auth import Token, UserLogin, UserRegister
except ImportError:
    Token = None
    UserLogin = None
    UserRegister = None

# Import team schemas
try:
    from .team import (
        TeamCreate,
        TeamList,
        TeamMember,
        TeamMemberCreate,
        TeamMemberUpdate,
        TeamOut,
        TeamResponse,
        TeamUpdate,
        TeamWithMembers,
    )
except ImportError:
    TeamCreate = None
    TeamUpdate = None
    TeamOut = None
    TeamResponse = None

# Import assessment schemas
try:
    from .assessment import AssessmentCreate, AssessmentOut, AssessmentUpdate
except ImportError:
    AssessmentCreate = None
    AssessmentUpdate = None
    AssessmentOut = None

# Import response schemas
try:
    from .response import ResponseCreate, ResponseOut, ResponseUpdate
except ImportError:
    ResponseCreate = None
    ResponseUpdate = None
    ResponseOut = None

# Import organization schemas
try:
    from .organization import OrganizationCreate, OrganizationOut, OrganizationUpdate
except ImportError:
    OrganizationCreate = None
    OrganizationUpdate = None
    OrganizationOut = None

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserRead",
    "UserResponse",
    # Auth schemas
    "Token",
    "UserLogin",
    "UserRegister",
    # Team schemas
    "TeamCreate",
    "TeamUpdate",
    "TeamOut",
    "TeamResponse",
    "TeamMember",
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamWithMembers",
    "TeamList",
    # Assessment schemas
    "AssessmentCreate",
    "AssessmentUpdate",
    "AssessmentOut",
    # Response schemas
    "ResponseCreate",
    "ResponseUpdate",
    "ResponseOut",
    # Organization schemas
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationOut",
]
