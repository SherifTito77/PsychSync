"""
Security fixes for critical session vulnerabilities
This module provides secure, simplified versions of authentication functions
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import HTTPException, status


class SecureTokenValidator:
    """Fixed JWT token validation with proper security checks"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

        # Simple in-memory token blacklist for demo
        # In production, use Redis or database
        self.blacklisted_tokens = set()

    def create_access_token(self, subject: str, expires_delta: timedelta = None) -> str:
        """Create secure JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)

        to_encode = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # JWT ID for blacklist tracking
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify JWT token with comprehensive security checks"""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token format
        if not isinstance(token, str) or len(token) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token has been blacklisted
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self.blacklisted_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={
                    "require": ["exp", "sub", "iat"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )

            # Additional security checks
            self._validate_token_payload(payload)

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e!s}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _validate_token_payload(self, payload: dict[str, Any]):
        """Validate token payload for security"""
        # Check required claims
        required_claims = ["sub", "exp", "iat", "type"]
        for claim in required_claims:
            if claim not in payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token missing required claim: {claim}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Check token type
        if payload["type"] != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration (additional check)
        exp = payload["exp"]
        if isinstance(exp, (int, float)):
            exp_datetime = datetime.utcfromtimestamp(exp)
            if exp_datetime < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Check issued at time
        iat = payload["iat"]
        if isinstance(iat, (int, float)):
            iat_datetime = datetime.utcfromtimestamp(iat)
            # Don't allow tokens issued in the future
            if iat_datetime > datetime.utcnow() + timedelta(minutes=1):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token issued in the future",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    def blacklist_token(self, token: str):
        """Add token to blacklist"""
        if token:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            self.blacklisted_tokens.add(token_hash)


class SessionManager:
    """Secure session management with fixation protection"""

    def __init__(self):
        self.sessions = {}  # In-memory session store (use Redis in production)

    def create_session_id(self) -> str:
        """Generate secure session ID"""
        return secrets.token_urlsafe(32)

    def create_session(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Create new session with fixation protection"""
        session_id = self.create_session_id()

        session_data = {
            "session_id": session_id,
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "csrf_token": secrets.token_urlsafe(32),
            "is_active": True,
        }

        # Store session
        self.sessions[session_id] = session_data

        return {
            "session_id": session_id,
            "csrf_token": session_data["csrf_token"],
            "created_at": session_data["created_at"],
        }

    def validate_session(self, session_id: str) -> dict[str, Any] | None:
        """Validate session and return session data"""
        if not session_id:
            return None

        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check if session is active
        if not session.get("is_active", False):
            return None

        # Check session age (max 24 hours)
        created_at = datetime.fromisoformat(session["created_at"])
        if datetime.utcnow() - created_at > timedelta(hours=24):
            session["is_active"] = False
            return None

        # Update last activity
        session["last_activity"] = datetime.utcnow().isoformat()

        return session

    def regenerate_session(self, old_session_id: str) -> str | None:
        """Regenerate session ID to prevent fixation"""
        old_session = self.sessions.get(old_session_id)
        if not old_session:
            return None

        # Create new session ID
        new_session_id = self.create_session_id()

        # Move session data to new ID
        self.sessions[new_session_id] = old_session.copy()
        self.sessions[new_session_id]["session_id"] = new_session_id
        self.sessions[new_session_id]["csrf_token"] = secrets.token_urlsafe(32)

        # Delete old session
        del self.sessions[old_session_id]

        return new_session_id

    def destroy_session(self, session_id: str):
        """Destroy session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


class RateLimiter:
    """Simple rate limiter for authentication endpoints"""

    def __init__(self):
        # In-memory rate limit store (use Redis in production)
        self.attempts = {}

    def is_rate_limited(
        self, identifier: str, max_attempts: int = 5, window_minutes: int = 15
    ) -> bool:
        """Check if identifier is rate limited"""
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=window_minutes)

        # Get existing attempts for this identifier
        user_attempts = self.attempts.get(identifier, [])

        # Remove old attempts outside the window
        user_attempts = [
            attempt_time
            for attempt_time in user_attempts
            if attempt_time > window_start
        ]

        # Check if rate limit exceeded
        if len(user_attempts) >= max_attempts:
            return True

        # Add current attempt
        user_attempts.append(current_time)
        self.attempts[identifier] = user_attempts

        return False

    def reset_rate_limit(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self.attempts:
            del self.attempts[identifier]


# Global instances
token_validator = None
session_manager = SessionManager()
rate_limiter = RateLimiter()


def initialize_security(secret_key: str):
    """Initialize security components"""
    global token_validator
    token_validator = SecureTokenValidator(secret_key)
    return token_validator


def get_current_user_from_token(token: str) -> dict[str, Any]:
    """Get current user from token with validation"""
    if not token_validator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security not initialized",
        )

    payload = token_validator.verify_token(token)

    # Extract user information from token
    return {
        "user_id": payload.get("sub"),
        "token_jti": payload.get("jti"),
        "expires_at": datetime.utcfromtimestamp(payload["exp"]).isoformat(),
    }


def create_secure_token_for_user(
    user_id: str, email: str, expires_delta: timedelta = None
) -> str:
    """Create secure token for user"""
    if not token_validator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security not initialized",
        )

    # Create access token with custom or default expiration
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    token = token_validator.create_access_token(
        subject=user_id, expires_delta=expires_delta
    )

    return token


def verify_password_strength(password: str) -> dict[str, Any]:
    """Verify password strength"""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errors.append("Password must contain at least one special character")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "strength_score": max(0, 100 - len(errors) * 20),
    }


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError) as e:
        # Log specific errors for security auditing
        import logging

        logging.warning(f"Password verification error: {type(e).__name__}")
        return False
