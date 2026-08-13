"""
PsychSync Enterprise Security - Authentication Utilities
Unified module for JWT token management, password hashing, and user authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db

# Initialize security logger
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("app.security.core")

# Password Hashing Context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    default="bcrypt",
    deprecated="auto",
    bcrypt__rounds=12,
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")

# JWT Configuration
ALGORITHM = settings.JWT_ALGORITHM

# =============================================================================
# Password Utilities
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure hash for a password."""
    return pwd_context.hash(password)


# =============================================================================
# JWT Utilities
# =============================================================================


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a new JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token, returning the subject (user ID)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user_async(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)
):
    """Dependency to retrieve the current authenticated user."""
    from sqlalchemy import select

    from app.db.models.user import User

    user_id_str = verify_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    from uuid import UUID

    from sqlalchemy import String, bindparam

    user = None

    # Try UUID lookup first (auth_unified tokens store UUID in sub).
    # Use a String-typed bind param to bypass postgresql.UUID's bind processor,
    # which converts uuid.UUID objects to hex — breaking SQLite string comparison.
    try:
        UUID(user_id_str)  # validate format only
        result = await db.execute(
            select(User).where(User.id == bindparam("uid", user_id_str, type_=String))
        )
        user = result.scalar_one_or_none()
    except ValueError:
        pass  # sub is not a UUID — fall through to email lookup

    # Fallback: email lookup (simple_auth tokens store email in sub)
    if user is None:
        result = await db.execute(select(User).where(User.email == user_id_str))
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


async def get_current_active_user(current_user=Depends(get_current_user_async)):
    """Dependency to get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user
