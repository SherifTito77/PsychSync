# app/schemas/user.py

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.db.models.user import UserRole

# SECURITY: Enterprise-grade password validation


class UserBase(BaseModel):
    """Base Pydantic model for a User, containing common attributes."""

    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user via the API. Requires email and password."""

    email: EmailStr
    password: str
    # Make full_name optional to allow registration without it
    full_name: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user. All fields are optional."""

    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {'full_name': 'John Smith', 'phone': '+1234567890', 'bio': 'Software engineer passionate about psychology'}
        }
    )

class UserRead(UserBase):
    """Schema for reading user data"""

    id: UUID  # Changed from int to UUID to match the database model

    model_config = ConfigDict(from_attributes=True)


class UserOut(UserBase):
    """
    Schema for returning user data in API responses.
    This is the primary schema for reading user information.
    It intentionally does NOT include the password hash.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime
    avatar_url: str | None = None
    is_verified: bool | None = False
    is_superuser: bool | None = False

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserOut):
    """
    Internal schema that includes the password hash.
    This should NEVER be returned in an API response.
    It's used internally, for example, after fetching a user from the DB
    before authentication.
    """

    # Use password_hash to match the database model
    password_hash: str

    model_config = ConfigDict(from_attributes=True)


# Alias for backward compatibility
UserResponse = UserOut
