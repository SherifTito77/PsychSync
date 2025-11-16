
# # app/schemas/auth.py - Authentication Request/Response Schemas

# app/schemas/auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr #,validator
from app.core.security import validate_password
from pydantic import field_validator

from pydantic import validator



class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr
    full_name: str
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        is_valid, error = validate_password(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    @field_validator('full_name')
    def validate_full_name(cls, v):
        if len(v) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload schema"""
    sub: Optional[str] = None
    exp: Optional[int] = None


class PasswordChange(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    def validate_new_password(cls, v):
        is_valid, error = validate_password(v)
        if not is_valid:
            raise ValueError(error)
        return v




# ... existing schemas ...

class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""
    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, error = validate_password(v)
        if not is_valid:
            raise ValueError(error)
        return v


class AdminUserUpdate(BaseModel):
    """Admin user update schema"""
    is_active: Optional[bool] = None
    role: Optional[str] = None