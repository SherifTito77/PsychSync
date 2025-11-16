# app/core/security.py

"""
Security utilities for password hashing, JWT token creation, and validation
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_async_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")

# JWT Configuration
ALGORITHM = settings.JWT_ALGORITHM


# =============================================================================
# PASSWORD FUNCTIONS
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback to passlib if bcrypt direct method fails
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    try:
        # Use bcrypt directly with explicit truncation
        import bcrypt
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except Exception as e:
        # Fallback to passlib if direct bcrypt fails
        try:
            # bcrypt has a 72 byte limit, truncate if necessary
            if isinstance(password, str):
                password_bytes = password.encode('utf-8')
                if len(password_bytes) > 72:
                    password_bytes = password_bytes[:72]
                    password = password_bytes.decode('utf-8', errors='ignore')
            return pwd_context.hash(password)
        except Exception as e2:
            raise Exception(f"Both bcrypt and passlib failed: {e}, {e2}")


def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password against security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of str)
    """
    errors = []
    
    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    
    # Check for uppercase letter
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# =============================================================================
# JWT TOKEN FUNCTIONS
# =============================================================================

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject of the token (usually user email or ID)
        expires_delta: Optional custom expiration time
        additional_claims: Optional additional claims to include in token
        
    Returns:
        Encoded JWT token as string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    
    # Add any additional claims
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The subject of the token (usually user email or ID)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token as string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        The subject (email) from the token, or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        email: str = payload.get("sub")
        if email is None:
            return None
            
        return email
        
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (for debugging).
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# =============================================================================
# USER AUTHENTICATION FUNCTIONS
# =============================================================================

async def get_current_user_from_token(token: str, db: AsyncSession):
    """
    Get the current user from a JWT token.

    Args:
        token: JWT token string
        db: Async database session

    Returns:
        User object if valid, None otherwise
    """
    from app.db.models.user import User
    from sqlalchemy import select

    email = verify_token(token, token_type="access")
    if not email:
        return None

    # Fixed: Use async query and get the user by email
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_current_user_async(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Async dependency to get current authenticated user.

    Args:
        token: JWT token from OAuth2 scheme
        db: Async database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.db.models.user import User
    from sqlalchemy import select

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = verify_token(token, token_type="access")
    if email is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


# Keep the sync version for backwards compatibility
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """Alias for get_current_user_async"""
    return await get_current_user_async(token, db)


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# =============================================================================
# PASSWORD RESET TOKEN FUNCTIONS
# =============================================================================

def create_password_reset_token(email: str) -> str:
    """
    Create a password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        Password reset token
    """
    expires_delta = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        subject=email,
        expires_delta=expires_delta,
        additional_claims={"type": "password_reset"}
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM]
        )
        
        if payload.get("type") != "password_reset":
            return None
            
        email: str = payload.get("sub")
        return email
        
    except JWTError:
        return None


# =============================================================================
# EMAIL VERIFICATION TOKEN FUNCTIONS
# =============================================================================

def create_email_verification_token(email: str) -> str:
    """
    Create an email verification token.
    
    Args:
        email: User's email address
        
    Returns:
        Email verification token
    """
    expires_delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    return create_access_token(
        subject=email,
        expires_delta=expires_delta,
        additional_claims={"type": "email_verification"}
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify an email verification token.
    
    Args:
        token: Email verification token
        
    Returns:
        Email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM]
        )
        
        if payload.get("type") != "email_verification":
            return None
            
        email: str = payload.get("sub")
        return email
        
    except JWTError:
        return None