#app/shemas/user.py

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base Pydantic model for a User, containing common attributes."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user via the API. Requires email and password."""
    email: EmailStr
    password: str
    # Make full_name optional to allow registration without it
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user. All fields are optional."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


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
    avatar_url: Optional[str] = None
    is_verified: Optional[bool] = False
    is_superuser: Optional[bool] = False
    
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