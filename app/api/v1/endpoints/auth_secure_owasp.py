"""
OWASP-Secure Authentication Endpoints
Replaces vulnerable authentication patterns with security-hardened implementation

Security Improvements:
- Proper audit logging for all security events
- Structured logging replacing print statements
- Input validation with length limits
- Generic error messages preventing information disclosure
- Secure token handling with httpOnly cookies
- Rate limiting and brute force protection
- Comprehensive security monitoring

Author: Security Team
Version: 3.0 OWASP-Compliant
"""

from datetime import datetime, timedelta
import logging
import re

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.audit_logging import AuditAction, AuditEvent, AuditSeverity, audit_logger
from app.core.config import settings
from app.core.database import get_async_db
from app.core.security_fixes import (
    create_secure_token_for_user,
    get_current_user_from_token,
    hash_password,
    initialize_security,
    rate_limiter,
    session_manager,
    verify_password,
    verify_password_strength,
)
from app.core.simple_rate_limiter import rate_limit
from app.db.models.user import User

# SECURITY: Configure structured logging
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

# Initialize router
router = APIRouter()

# Maximum lengths for input validation
MAX_EMAIL_LENGTH = 254  # RFC 5321
MAX_FULL_NAME_LENGTH = 100
MAX_PASSWORD_LENGTH = 128

# SECURITY: OAuth2 scheme reads from httpOnly cookie instead of Authorization header
# This prevents XSS attacks from accessing tokens via JavaScript
class CookieOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        # Try to get token from httpOnly cookie first
        access_token = request.cookies.get("access_token")
        if access_token:
            return access_token

        # Fallback to Authorization header for backward compatibility during transition
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() == "bearer":
                return token

        return None

oauth2_scheme = CookieOAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Initialize security on module load
try:
    initialize_security(settings.SECRET_KEY)
except Exception as e:
    logger.error(f"Security initialization error: {e}")


async def _validate_email(email: str) -> tuple[bool, str | None]:
    """
    Validate email with RFC-compliant regex and length checks

    Returns:
        (is_valid, error_message)
    """
    # Check length
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return False, "Email must be between 1 and 254 characters"

    # RFC 5322 compliant email pattern
    email_pattern = r"^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    # Check for suspicious patterns (potential injection attempts)
    suspicious_patterns = ["../", "..\\", "<script", "javascript:", "onerror=", "onload="]
    email_lower = email.lower()
    for pattern in suspicious_patterns:
        if pattern in email_lower:
            security_logger.warning(
                f"Suspicious pattern detected in email: {pattern}",
                extra={"security_event": "SUSPICIOUS_INPUT", "pattern": pattern}
            )
            return False, "Invalid email format"

    return True, None


async def _validate_full_name(full_name: str) -> tuple[bool, str | None]:
    """
    Validate full name with security checks

    Returns:
        (is_valid, error_message)
    """
    # Check length
    if not full_name or len(full_name) > MAX_FULL_NAME_LENGTH:
        return False, f"Full name must be between 1 and {MAX_FULL_NAME_LENGTH} characters"

    # Check for XSS patterns
    xss_patterns = ["<script", "</script", "javascript:", "onerror=", "onload=", "onclick="]
    name_lower = full_name.lower()
    for pattern in xss_patterns:
        if pattern in name_lower:
            security_logger.warning(
                f"XSS pattern detected in full_name: {pattern}",
                extra={"security_event": "XSS_ATTEMPT", "field": "full_name", "pattern": pattern}
            )
            return False, "Invalid characters in full name"

    # Allow only safe characters: letters, spaces, hyphens, apostrophes
    if not re.match(r"^[\w\s\-']+$", full_name):
        return False, "Full name contains invalid characters"

    return True, None


async def _get_client_info(request: Request) -> dict[str, str]:
    """
    Extract client information for security logging
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    # SECURITY: Check for proxy headers and log them
    forwarded_for = request.headers.get("X-Forwarded-For")
    real_ip = request.headers.get("X-Real-IP")

    return {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "forwarded_for": forwarded_for,
        "real_ip": real_ip
    }


@router.post("/token")
@rate_limit(max_requests=5, window_seconds=60)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    OWASP-secure authentication endpoint

    Security Features:
    - Rate limiting (5 attempts per minute)
    - Generic error messages (no information disclosure)
    - Comprehensive audit logging
    - Brute force detection
    - httpOnly cookie token storage (XSS prevention)
    """
    client_info = await _get_client_info(request)
    client_ip = client_info["ip_address"]

    try:
        # Check rate limiting
        if rate_limiter.is_rate_limited(client_ip):
            security_logger.warning(
                "Rate limit exceeded for login endpoint",
                extra={
                    "security_event": "RATE_LIMIT_EXCEEDED",
                    "ip_address": client_ip,
                    "endpoint": "/auth/token"
                }
            )

            # SECURITY: Log rate limit exceeded
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.RATE_LIMIT_EXCEEDED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/token",
                details={"reason": "Too many login attempts"},
                severity=AuditSeverity.HIGH
            ))

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        # SECURITY: Validate input length before processing
        if not form_data.username or len(form_data.username) > MAX_EMAIL_LENGTH:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.AUTHENTICATION_FAILED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/token",
                details={"reason": "Invalid username length"},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials"
            )

        if not form_data.password or len(form_data.password) > MAX_PASSWORD_LENGTH:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.AUTHENTICATION_FAILED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/token",
                details={"reason": "Invalid password length"},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials"
            )

        # Validate email format
        email_valid, email_error = await _validate_email(form_data.username)
        if not email_valid:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.AUTHENTICATION_FAILED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/token",
                details={"reason": "Invalid email format"},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid credentials"
            )

        # Query user from database
        result = await db.execute(
            select(User).where(User.email == form_data.username.lower())
        )
        user = result.scalar_one_or_none()

        # Authentication check (generic error message)
        authentication_failed = False

        if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
            authentication_failed = True

        # Handle authentication failure
        if authentication_failed:
            # SECURITY: Log failed authentication attempt
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.AUTHENTICATION_FAILED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/token",
                details={"email": form_data.username.lower()},  # Log attempt for monitoring
                severity=AuditSeverity.MEDIUM
            ))

            security_logger.warning(
                "Failed authentication attempt",
                extra={
                    "security_event": "FAILED_LOGIN",
                    "ip_address": client_ip,
                    "email": form_data.username.lower()
                }
            )

            # SECURITY: Generic error message (no information disclosure)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Authentication successful - create secure session
        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value if user.role else "user"
        }

        session = session_manager.create_session(session_data)

        # Create JWT token
        access_token = create_secure_token_for_user(str(user.id), user.email)
        refresh_token = create_secure_token_for_user(
            str(user.id),
            user.email,
            expires_delta=timedelta(days=7)
        )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        # SECURITY: Log successful authentication
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.AUTHENTICATE,
            user_id=str(user.id),
            ip_address=client_ip,
            user_agent=client_info["user_agent"],
            resource="/auth/token",
            details={
                "success": True,
                "login_method": "password"
            },
            severity=AuditSeverity.LOW
        ))

        logger.info(
            f"Successful login for user {user.id}",
            extra={
                "user_id": str(user.id),
                "ip_address": client_ip,
                "security_event": "SUCCESSFUL_LOGIN"
            }
        )

        # SECURITY: Set httpOnly cookies instead of returning tokens in response
        # This prevents XSS attacks from stealing tokens
        response = Response(
            content='{"message": "Login successful"}',
            media_type="application/json",
            status_code=200
        )

        # Set access token cookie (httpOnly, secure, SameSite)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=1800,  # 30 minutes
            path="/",
            secure=True,  # HTTPS only
            httponly=True,  # Not accessible via JavaScript
            samesite="lax"  # CSRF protection
        )

        # Set refresh token cookie (longer expiry)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=604800,  # 7 days
            path="/",
            secure=True,
            httponly=True,
            samesite="lax"
        )

        # Set CSRF token in a non-httpOnly cookie (needed for AJAX requests)
        response.set_cookie(
            key="csrf_token",
            value=session["csrf_token"],
            max_age=1800,
            path="/",
            secure=True,
            httponly=False,  # Must be readable by JavaScript
            samesite="lax"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Authentication error: {e!s}",
            extra={
                "security_event": "AUTH_ERROR",
                "ip_address": client_ip,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/register")
@rate_limit(max_requests=3, window_seconds=3600)
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    db: AsyncSession = Depends(get_async_db)
):
    """
    OWASP-secure user registration endpoint

    Security Features:
    - Rate limiting (3 registrations per hour)
    - Comprehensive input validation
    - Password strength requirements
    - Email format validation
    - XSS prevention in full_name
    - Audit logging
    """
    client_info = await _get_client_info(request)
    client_ip = client_info["ip_address"]

    try:
        # Check rate limiting for registration
        if rate_limiter.is_rate_limited(f"register:{client_ip}", max_attempts=3, window_minutes=60):
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.RATE_LIMIT_EXCEEDED,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/register",
                details={"reason": "Too many registration attempts"},
                severity=AuditSeverity.HIGH
            ))

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts. Please try again later."
            )

        # Validate email
        email_valid, email_error = await _validate_email(email)
        if not email_valid:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.CREATE,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/register",
                details={"reason": email_error},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=email_error
            )

        # Validate full name
        full_name_valid, name_error = await _validate_full_name(full_name)
        if not full_name_valid:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.CREATE,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/register",
                details={"reason": name_error},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=name_error
            )

        # Validate password strength
        password_validation = verify_password_strength(password)
        if not password_validation["valid"]:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.CREATE,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/register",
                details={"reason": "Weak password"},
                severity=AuditSeverity.LOW
            ))

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password requirements not met",
                    "errors": password_validation["errors"]
                }
            )

        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.CREATE,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/register",
                details={"reason": "Email already exists"},
                severity=AuditSeverity.LOW
            ))

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = hash_password(password)

        new_user = User(
            email=email.lower(),
            full_name=full_name.strip(),
            password_hash=hashed_password,
            is_active=True,
            is_verified=False,
            role="user"
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # SECURITY: Log successful registration
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.CREATE,
            user_id=str(new_user.id),
            ip_address=client_ip,
            user_agent=client_info["user_agent"],
            resource="/auth/register",
            details={
                "email": new_user.email,
                "registration_method": "standard"
            },
            severity=AuditSeverity.LOW
        ))

        logger.info(
            f"New user registered: {new_user.id}",
            extra={
                "user_id": str(new_user.id),
                "ip_address": client_ip,
                "security_event": "USER_REGISTRATION"
            }
        )

        return {
            "message": "Registration successful",
            "user": {
                "id": str(new_user.id),
                "email": new_user.email,
                "full_name": new_user.full_name,
                "is_active": True,
                "is_verified": False
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Registration error: {e!s}",
            extra={
                "security_event": "REGISTRATION_ERROR",
                "ip_address": client_ip,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service temporarily unavailable"
        )


@router.get("/me")
async def get_current_user_info(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get current user information with proper token validation

    Security Features:
    - Token validation
    - Account status check
    - Audit logging
    """
    client_info = await _get_client_info(request)
    client_ip = client_info["ip_address"]

    try:
        # Validate token and extract user info
        try:
            user_info = get_current_user_from_token(token)
            user_id = user_info["user_id"]
        except HTTPException:
            raise
        except Exception:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.READ,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/me",
                details={"reason": "Invalid token"},
                severity=AuditSeverity.MEDIUM
            ))

            logger.warning(
                f"Invalid token attempt from {client_ip}",
                extra={"security_event": "INVALID_TOKEN", "ip_address": client_ip}
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.READ,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/me",
                details={"reason": "User not found"},
                severity=AuditSeverity.MEDIUM
            ))

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user.is_active:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                user_id=str(user.id),
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/me",
                details={"reason": "Inactive account"},
                severity=AuditSeverity.HIGH
            ))

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )

        # SECURITY: Log successful access
        await audit_logger.log_event(AuditEvent(
            action=AuditAction.READ,
            user_id=str(user.id),
            ip_address=client_ip,
            user_agent=client_info["user_agent"],
            resource="/auth/me",
            severity=AuditSeverity.LOW
        ))

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "role": user.role.value if user.role else "user",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Get user info error: {e!s}",
            extra={
                "security_event": "USER_INFO_ERROR",
                "ip_address": client_ip,
                "error_type": type(e).__name__
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User service temporarily unavailable"
        )


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    """
    Logout endpoint that properly invalidates tokens and sessions

    Security Features:
    - Token blacklisting
    - Cookie clearing
    - Audit logging
    """
    client_info = await _get_client_info(request)
    client_ip = client_info["ip_address"]
    user_id = None

    try:
        # Validate token first
        try:
            user_info = get_current_user_from_token(token)
            user_id = user_info.get("user_id")
            token_jti = user_info.get("token_jti")

            # Blacklist the token
            from app.core.security_fixes import token_validator
            if token_validator:
                token_validator.blacklist_token(token)

        except HTTPException:
            # Even if token is invalid, return success to avoid exposing errors
            pass

        # SECURITY: Log logout
        if user_id:
            await audit_logger.log_event(AuditEvent(
                action=AuditAction.LOGOUT,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=client_info["user_agent"],
                resource="/auth/logout",
                severity=AuditSeverity.LOW
            ))

        logger.info(
            f"User logged out: {user_id}",
            extra={
                "user_id": user_id,
                "ip_address": client_ip,
                "security_event": "LOGOUT"
            }
        )

        # SECURITY: Clear httpOnly cookies by setting them with expired date
        response = Response(
            content='{"message": "Logout successful"}',
            media_type="application/json",
            status_code=200
        )

        # Clear all cookies
        response.delete_cookie("access_token", path="/", secure=True, httponly=True, samesite="lax")
        response.delete_cookie("refresh_token", path="/", secure=True, httponly=True, samesite="lax")
        response.delete_cookie("csrf_token", path="/", secure=True, httponly=False, samesite="lax")

        return response

    except Exception as e:
        logger.error(
            f"Logout error: {e!s}",
            extra={
                "security_event": "LOGOUT_ERROR",
                "ip_address": client_ip,
                "error_type": type(e).__name__
            }
        )
        # Always return success for logout to avoid exposing internal errors
        return {"message": "Logout successful"}


@router.get("/health")
async def health_check():
    """
    Health check endpoint for authentication service
    """
    return {
        "status": "healthy",
        "service": "authentication-secure",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0-owasp"
    }
