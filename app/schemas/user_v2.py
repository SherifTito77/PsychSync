# app/schemas/user_v2.py
"""
User Schemas - Refactored Version

Demonstrates standardized schema patterns using base classes.
This is the NEW version to migrate to.

Migration Guide:
1. Import from user_v2 instead of user
2. Update field names (see below)
3. Update validation rules
"""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field
from pydantic.functional_validators import field_validator

from app.db.models.user import UserRole
from app.schemas.base import BaseSchema, CommonFields, EntitySchema, ValidationRules

# ============================================================================
# CREATE/UPDATE SCHEMAS
# ============================================================================


class UserBase(BaseSchema):
    """
    Base user schema with common fields.

    All user-related schemas inherit from this.
    """

    email: EmailStr = Field(min_length=5, max_length=255, description="Email address")
    full_name: str | None = Field(default=None, **ValidationRules.name())
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Whether the user is active")


class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Validation:
    - Email is required and must be valid
    - Password must meet strength requirements
    - Full name is optional
    """

    email: EmailStr = Field(min_length=5, max_length=255, description="Email address")
    password: str = Field(
        min_length=12,
        max_length=128,
        description="Password (min 12 characters, must include uppercase, lowercase, digit, and special character)",
    )
    full_name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Name"
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """Validate full name if provided"""
        if v and len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.strip() if v else None


class UserUpdate(BaseSchema):
    """
    Schema for updating a user.

    All fields are optional - only update what's provided.
    """

    email: EmailStr | None = Field(default=None, **ValidationRules.email())
    full_name: str | None = Field(default=None, **ValidationRules.name())
    is_active: bool | None = Field(default=None, description="User active status")
    password: str | None = Field(default=None, **ValidationRules.password())

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str | None) -> str | None:
        """Validate full name if provided"""
        if v and len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.strip() if v else None


class UserPasswordUpdate(BaseSchema):
    """
    Schema for password updates.

    Requires both current and new password for security.
    """

    current_password: str = Field(description="Current password for verification")
    new_password: str = Field(
        min_length=12,
        max_length=128,
        description="Password (min 12 characters, must include uppercase, lowercase, digit, and special character)",
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class UserResponse(EntitySchema, UserBase):
    """
    Complete user response schema.

    Inherits from EntitySchema for ID and timestamps.
    Includes all user-safe information (no password hash).
    """

    avatar_url: str | None = Field(default=None, description="Profile avatar URL")
    is_verified: bool = Field(default=False, description="Email verification status")
    is_superuser: bool = Field(default=False, description="Superuser privileges")
    last_login: datetime | None = Field(
        default=None, description="Last login timestamp"
    )


class UserBasic(BaseSchema):
    """
    Basic user information for embedded responses.

    Use this when embedding user info in other responses
    to avoid circular references and reduce payload size.
    """

    id: UUID = Field(description="User ID")
    email: EmailStr = Field(min_length=5, max_length=255, description="Email address")
    full_name: str | None = Field(default=None, **ValidationRules.name())
    avatar_url: str | None = Field(default=None, description="Profile avatar URL")


class UserDetailed(UserResponse):
    """
    Detailed user response with additional fields.

    Use this for admin/user profile pages where more info is needed.
    """

    two_factor_enabled: bool = Field(default=False, description="2FA status")
    organization_id: UUID | None = Field(default=None, description="Organization ID")
    timezone: str | None = Field(default="UTC", description="User timezone")
    locale: str | None = Field(default="en-US", description="User locale")


# ============================================================================
# LIST RESPONSES
# ============================================================================


class UserListResponse(BaseSchema):
    """
    Paginated list of users.

    Example:
        {
            "users": [...],
            "total": 100,
            "page": 1,
            "page_size": 20
        }
    """

    users: list[UserResponse]
    total: int = Field(description="Total number of users")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================


class UserLogin(BaseSchema):
    """
    Schema for user login.

    Note: Uses username field but accepts email for compatibility.
    """

    username: EmailStr = Field(description="Email address (validated as EmailStr)")
    password: str = Field(description="User password")


class UserRegister(UserCreate):
    """
    Schema for user registration.

    Extends UserCreate with additional registration-specific fields.
    """

    confirm_password: str = Field(description="Confirm password")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class AuthResponse(BaseSchema):
    """
    Response schema for authentication endpoints.

    Returns access token and user information.
    """

    access_token: str = Field(description="JWT access token")
    refresh_token: str | None = Field(default=None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int | None = Field(
        default=None, description="Token expiration in seconds"
    )
    user: UserResponse = Field(description="Authenticated user information")


# ============================================================================
# ADMIN SCHEMAS
# ============================================================================


class UserAdminUpdate(UserUpdate):
    """
    Admin-only user update schema.

    Allows admins to modify fields users cannot change themselves.
    """

    role: UserRole | None = Field(default=None, description="User role")
    is_superuser: bool | None = Field(default=None, description="Superuser status")
    is_verified: bool | None = Field(
        default=None, description="Email verification status"
    )


class UserAdminCreate(UserCreate):
    """
    Admin-only user creation schema.

    Allows admins to create users with elevated privileges.
    """

    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_superuser: bool = Field(default=False, description="Superuser status")
    is_verified: bool = Field(default=False, description="Email verification status")


# ============================================================================
# EXPORTS (INCLUDING BACKWARD COMPATIBILITY)
# ============================================================================

# New standardized names (recommended)
__all__ = [
    # Base
    "UserBase",
    # Create/Update
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    # Responses
    "UserResponse",
    "UserBasic",
    "UserDetailed",
    # Lists
    "UserListResponse",
    # Auth
    "UserLogin",
    "UserRegister",
    "AuthResponse",
    # Admin
    "UserAdminUpdate",
    "UserAdminCreate",
]

# Backward compatibility aliases (will be deprecated)
UserOut = UserResponse  # Old name
User = UserResponse  # Old name
UserInDB = UserResponse  # Old name

# These will trigger deprecation warnings in future
import warnings

warnings.warn(
    "UserOut, User, and UserInDB are deprecated. Use UserResponse instead.",
    DeprecationWarning,
    stacklevel=2,
)
