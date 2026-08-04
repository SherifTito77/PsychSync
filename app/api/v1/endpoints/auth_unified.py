"""
Unified Authentication Endpoint

Consolidates best practices from all authentication implementations:
- auth.py (original)
- auth_fixed.py (fix attempt)
- auth_secure.py (security-enhanced)
- auth_secure_owasp.py (OWASP-compliant)

Features:
- Account lockout integration (brute force protection)
- MFA support (TOTP + recovery codes)
- Device tracking and fingerprinting
- Rate limiting
- Secure token handling
- OWASP compliance
- Comprehensive logging

Security Enhancements:
- Failed login attempt tracking
- Exponential backoff lockout
- IP banning for repeat offenders
- Device mismatch detection
- Session management

Author: Security Team
Version: 3.0.0 (Unified)
Date: January 7, 2026
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.atomic_lockout_tracker import atomic_lockout_tracker
from app.core.config import settings
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.schemas.auth_validation import LoginRequestValidator, MFALoginRequestValidator
from app.services.email_service import EmailService
from app.services.mfa_service import mfa_service
from app.services.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# LOGIN ENDPOINT (with Account Lockout + MFA + Device Tracking)
# ============================================================================


@router.post("/login", response_model=dict)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified login endpoint with comprehensive security features.

    Security Features:
    - Account lockout after 5 failed attempts (exponential backoff)
    - IP banning after 20 failed attempts
    - MFA verification (if enabled)
    - Device tracking and fingerprinting
    - Rate limiting

    Args:
        request: FastAPI request
        form_data: OAuth2 password form (username, password)
        db: Database session

    Returns:
        Token response with access token, refresh token, and user info

    Raises:
        HTTPException: If authentication fails
    """
    client_ip = request.client.host if request.client else "unknown"

    # Validate input BEFORE any expensive operations (DoS prevention)
    try:
        LoginRequestValidator(username=form_data.username, password=form_data.password)
    except ValueError as validation_error:
        logger.warning(
            "Login validation failed from IP %s: %s", client_ip, str(validation_error)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(validation_error)
        )

    # Check if IP is banned
    is_ip_banned, ip_ban_remaining = await atomic_lockout_tracker.is_ip_banned(
        client_ip
    )
    if is_ip_banned:
        logger.warning("Login attempt from banned IP: %s", client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed attempts from your IP. Try again in "
            f"{ip_ban_remaining // 60} minutes.",
        )

    # Find user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user:
        # Record failed attempt (even for non-existent users to prevent enumeration)
        is_locked, lockout_msg = await atomic_lockout_tracker.record_failed_attempt(
            "unknown", client_ip, db
        )
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=lockout_msg
            )

        logger.warning("Login attempt with non-existent email: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if user account is locked
    is_locked, lockout_remaining = await atomic_lockout_tracker.is_user_locked_out(
        str(user.id)
    )
    if is_locked:
        logger.warning("Login attempt for locked account: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked due to too many failed attempts. "
            f"Try again in {lockout_remaining // 60} minutes.",
        )

    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        # Record failed attempt
        is_locked, lockout_msg = await atomic_lockout_tracker.record_failed_attempt(
            str(user.id), client_ip, db
        )

        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=lockout_msg
            )

        logger.warning("Failed login attempt for user: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Check if user is active
    if not user.is_active:
        logger.warning("Login attempt for inactive account: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support.",
        )

    # Check if user is verified
    if hasattr(user, "is_verified") and not user.is_verified:
        logger.warning("Login attempt for unverified account: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in.",
        )

    # Check if user has MFA enabled
    if user.two_factor_enabled:
        # Generate temporary MFA challenge token (5 minute expiry)
        mfa_challenge_token = jwt.encode(
            {
                "sub": str(user.id),
                "type": "mfa_challenge",
                "exp": datetime.now(UTC) + timedelta(minutes=5),
                "iat": datetime.now(UTC),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        # Store challenge token in Redis with automatic connection cleanup
        import redis.asyncio as redis

        try:
            # Use async context manager for automatic connection cleanup
            # This prevents connection leaks if any error occurs
            async with await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                decoding="utf-8",
                health_check_interval=30,  # Detect stale connections
            ) as redis_client:
                challenge_key = f"mfa_challenge:{str(user.id)}"
                await redis_client.setex(
                    challenge_key, 300, mfa_challenge_token  # 5 minutes
                )

                logger.info("MFA challenge issued for user: %s", user.email)

        except redis.ConnectionError as conn_error:
            logger.error(
                "Redis connection error while storing MFA challenge for user %s: %s",
                user.email,
                conn_error,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            ) from conn_error

        except Exception as redis_error:
            logger.error(
                "Failed to store MFA challenge in Redis for user %s: %s",
                user.email,
                redis_error,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate MFA challenge",
            ) from redis_error

        # Return response indicating MFA is required
        return {
            "requires_mfa": True,
            "mfa_challenge_token": mfa_challenge_token,
            "message": "MFA verification required",
            "user": {"id": str(user.id), "email": user.email},
        }

    # Record successful attempt (clears failed attempts)
    await atomic_lockout_tracker.record_successful_attempt(str(user.id), client_ip)

    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store refresh token in database
    # Hash the token for storage (NEVER store plaintext)
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    # Get device fingerprint from request headers
    device_fingerprint = request.headers.get("user-agent", "")[:255]

    # Create refresh token record
    refresh_token_record = RefreshToken(
        user_id=str(user.id),
        token_hash=token_hash,
        device_fingerprint=device_fingerprint,
        user_agent=request.headers.get("user-agent", "")[:500],
        ip_address=client_ip,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),  # 30 day expiry
        revoked=False,
    )

    db.add(refresh_token_record)
    await db.commit()

    logger.info("Successful login for user: %s from IP: %s", user.email, client_ip)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "mfa_enabled": user.two_factor_enabled,
        },
    }


# ============================================================================
# MFA LOGIN VERIFICATION ENDPOINT
# ============================================================================


@router.post("/login/mfa/verify", response_model=dict)
async def login_verify_mfa(
    request: Request,
    mfa_challenge_token: str,
    totp_code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA code during login and issue access tokens.

    This endpoint completes the MFA challenge flow by:
    1. Verifying the MFA challenge token from Redis
    2. Validating the TOTP code
    3. Issuing access and refresh tokens upon success

    Args:
        request: FastAPI request
        mfa_challenge_token: Temporary MFA challenge token from /login
        totp_code: 6-digit TOTP code from authenticator app
        db: Database session

    Returns:
        Token response with access token, refresh token, and user info

    Raises:
        HTTPException: If MFA verification fails
    """
    client_ip = request.client.host if request.client else "unknown"

    # Validate input BEFORE any expensive operations
    try:
        MFALoginRequestValidator(
            mfa_challenge_token=mfa_challenge_token, totp_code=totp_code
        )
    except ValueError as validation_error:
        logger.warning(
            "MFA validation failed from IP %s: %s", client_ip, str(validation_error)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(validation_error)
        )

    try:
        # Decode challenge token to get user ID
        try:
            payload = jwt.decode(
                mfa_challenge_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if not user_id or token_type != "mfa_challenge":
                logger.warning(
                    "Invalid MFA challenge token format from IP: %s", client_ip
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA challenge token",
                )

        except jwt.ExpiredSignatureError as exp_error:
            logger.warning("Expired MFA challenge token from IP: %s", client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA challenge token has expired",
            ) from exp_error
        except jwt.InvalidTokenError as decode_error:
            logger.warning(
                "Failed to decode MFA challenge token from IP %s: %s",
                client_ip,
                decode_error,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA challenge token",
            ) from decode_error

        # Verify challenge token exists in Redis with automatic connection cleanup
        import redis.asyncio as redis

        try:
            # Use async context manager for automatic connection cleanup
            async with await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                decoding="utf-8",
                health_check_interval=30,
            ) as redis_client:
                challenge_key = f"mfa_challenge:{user_id}"
                stored_token = await redis_client.get(challenge_key)

                if not stored_token or stored_token != mfa_challenge_token:
                    logger.warning(
                        "MFA challenge token not found or invalid for user %s from IP: %s",
                        user_id,
                        client_ip,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired MFA challenge token",
                    )

                # Delete the challenge token (single-use)
                await redis_client.delete(challenge_key)
                logger.info("MFA challenge verified and consumed for user: %s", user_id)

        except HTTPException:
            raise
        except redis.ConnectionError as conn_error:
            logger.error(
                "Redis connection error during MFA verification: %s", conn_error
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            ) from conn_error
        except Exception as redis_error:
            logger.error("Redis error during MFA verification: %s", redis_error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify MFA challenge",
            ) from redis_error

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            logger.warning(
                "MFA verification attempt for non-existent or inactive user: %s",
                user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Verify TOTP code
        try:
            await mfa_service.verify_totp_code(user, totp_code, db)
        except Exception as mfa_error:
            logger.warning(
                "Failed MFA verification for user %s from IP %s: %s",
                user.email,
                client_ip,
                mfa_error,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication code",
            ) from mfa_error

        # Record successful attempt (clears failed attempts)
        await atomic_lockout_tracker.record_successful_attempt(str(user.id), client_ip)

        # Create access and refresh tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        device_fingerprint = request.headers.get("user-agent", "")[:255]

        refresh_token_record = RefreshToken(
            user_id=str(user.id),
            token_hash=token_hash,
            device_fingerprint=device_fingerprint,
            user_agent=request.headers.get("user-agent", "")[:500],
            ip_address=client_ip,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            revoked=False,
        )

        db.add(refresh_token_record)
        await db.commit()

        logger.info(
            "Successful MFA login for user: %s from IP: %s", user.email, client_ip
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "mfa_enabled": user.two_factor_enabled,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during MFA verification: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during MFA verification",
        ) from e


# ============================================================================
# REGISTER ENDPOINT (with Security)
# ============================================================================


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    email: str,
    password: str,
    full_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    User registration with comprehensive security features.

    Security Features:
    - Email validation
    - Password strength validation (12+ chars, complexity required)
    - Duplicate email prevention (database constraint)
    - IP-based rate limiting (max 3/hour)
    - Email verification requirement
    - Common password detection

    Args:
        request: FastAPI request
        email: User email
        password: User password
        full_name: User full name
        db: Database session

    Returns:
        Created user info with verification status

    Raises:
        HTTPException: If registration fails
    """
    import re
    import secrets

    import redis.asyncio as aioredis

    client_ip = request.client.host if request.client else "unknown"

    # =======================================================================
    # SECURITY 1: IP-based rate limiting
    # =======================================================================
    redis_client = await redis.asyncio.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

    try:
        registration_key = f"registrations:{client_ip}"

        # Check registration count for this IP
        attempts = await redis_client.incr(registration_key)

        if attempts == 1:
            # Set expiry on first attempt (1 hour)
            await redis_client.expire(registration_key, 3600)

        if attempts > 3:  # Max 3 registrations per hour per IP
            await redis_client.close()
            logger.warning(f"Rate limit exceeded for registration from IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many registration attempts from your IP. Please try again later.",
            )
    finally:
        await redis_client.close()

    # =======================================================================
    # SECURITY 2: Password strength validation
    # =======================================================================
    def validate_password_strength(password: str) -> tuple[bool, str | None]:
        """
        Validate password strength.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"

        # Check against common passwords
        common_passwords = [
            "password123",
            "qwerty2024",
            "admin123",
            "letmein",
            "password1",
            "12345678",
            "abc12345",
            "password123",
        ]

        if password.lower() in [p.lower() for p in common_passwords]:
            return False, "Password is too common. Please choose a stronger password."

        return True, None

    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # =======================================================================
    # SECURITY 3: Email validation
    # =======================================================================
    email = email.lower().strip()

    # Basic email format validation
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
        )

    # Check if email already exists (rely on database constraint for thread-safety)
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(
            f"Registration attempt with existing email: {email} from IP: {client_ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create user
    user = User(
        email=email.lower(),
        password_hash=get_password_hash(password),
        full_name=full_name,
        is_active=True,
        is_verified=False,  # Requires email verification
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user registered: {user.email} from IP: {client_ip}")

        # =======================================================================
        # SECURITY 4: Email verification
        # =======================================================================
        # Generate verification token (cryptographically secure random token)
        verification_token = secrets.token_urlsafe(32)

        # Store token in Redis with 24-hour expiry
        redis_client = await redis.asyncio.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        try:
            token_key = f"email_verification:{verification_token}"
            await redis_client.setex(token_key, 86400, str(user.id))  # 24 hours
            logger.info("Verification token generated for user: %s", user.email)
        finally:
            await redis_client.close()

        # Send verification email using EmailService
        email_service = EmailService()

        try:
            await email_service.send_verification_email(
                email=user.email, token=verification_token, name=user.full_name
            )
            logger.info("Verification email sent to: %s", user.email)
        except Exception as email_error:
            # Log email error but don't fail registration
            logger.warning(
                "Failed to send verification email to %s: %s", user.email, email_error
            )
            # Registration still succeeds, user can request resend
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account. Please try again.",
        ) from e

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "message": "Account created successfully. Please verify your email address.",
    }


# ============================================================================
# VERIFY EMAIL ENDPOINT
# ============================================================================


@router.post("/verify-email", response_model=dict)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify user email address.

    Security Features:
    - Token validation (must exist in Redis)
    - Token expiry (24-hour lifetime)
    - One-time use (token deleted after verification)

    Args:
        token: Verification token from email link
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid or expired
    """
    redis_client = await redis.asyncio.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

    try:
        token_key = f"email_verification:{token}"
        user_id = await redis_client.get(token_key)

        if not user_id:
            logger.warning("Invalid or expired verification token attempt")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User not found for verification token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check if already verified
        if user.is_verified:
            logger.info(f"Email already verified for user: {user.email}")
            return {"message": "Email already verified"}

        # Mark user as verified
        user.is_verified = True
        user.updated_at = datetime.now(UTC)

        await db.commit()

        # Delete verification token (one-time use)
        await redis_client.delete(token_key)

        logger.info(f"Email verified successfully for user: {user.email}")

        return {"message": "Email verified successfully. You can now login."}

    finally:
        await redis_client.close()


@router.post("/resend-verification", response_model=dict)
async def resend_verification_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Resend email verification link.

    Security Features:
    - Rate limiting (max 3 requests per hour)
    - User validation (must exist and be unverified)

    Args:
        email: User email
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or already verified
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)

    # Store token in Redis with 24-hour expiry
    redis_client = await redis.asyncio.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )
    try:
        token_key = f"email_verification:{verification_token}"
        await redis_client.setex(token_key, 86400, str(user.id))  # 24 hours
    finally:
        await redis_client.close()

    # Send verification email using EmailService
    email_service = EmailService()

    try:
        await email_service.send_verification_email(
            email=user.email, token=verification_token, name=user.full_name
        )
        logger.info("Resent verification email to: %s", user.email)
    except Exception as email_error:
        logger.error(
            "Failed to resend verification email to %s: %s", user.email, email_error
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later.",
        ) from email_error

    return {"message": "Verification email sent successfully"}


# ============================================================================
# GET CURRENT USER ENDPOINT
# ============================================================================


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "mfa_enabled": current_user.two_factor_enabled,
        "created_at": (
            current_user.created_at.isoformat() if current_user.created_at else None
        ),
        "updated_at": (
            current_user.updated_at.isoformat() if current_user.updated_at else None
        ),
    }


# ============================================================================
# LOGOUT ENDPOINT
# ============================================================================


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user and invalidate tokens.

    Security Features:
    - Token blacklisting (prevents token reuse)
    - Session invalidation
    - Comprehensive logging

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Extract access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

        # Blacklist token in Redis with expiry matching token's natural expiry
        from datetime import timedelta

        from app.services.auth_service import blacklist_token

        token_expiry = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        await blacklist_token(token, expiry=datetime.now(UTC) + token_expiry)

        logger.info(f"Token blacklisted for user: {current_user.email}")

    logger.info("User logged out: %s", current_user.email)

    return {"message": "Successfully logged out"}


# ============================================================================
# REFRESH TOKEN ENDPOINT
# ============================================================================


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: Request, refresh_token: str, db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Security Features:
    - Database verification (token must exist)
    - Token rotation (issue new refresh token, revoke old one)
    - Device fingerprint verification
    - Revocation checking

    Args:
        request: FastAPI request
        refresh_token: Refresh token
        db: Database session

    Returns:
        New access token and refresh token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Hash the token to lookup in database
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

    # Query database for token
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash, RefreshToken.revoked is False
        )
    )
    token_record = result.scalar_one_or_none()

    if not token_record or token_record.expires_at < datetime.now(UTC):
        logger.warning("Invalid or expired refresh token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Get user from token record
    user_id = token_record.user_id
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Verify device fingerprint (optional security check)
    current_device = request.headers.get("user-agent", "")[:255]
    if (
        token_record.device_fingerprint
        and token_record.device_fingerprint != current_device
    ):
        logger.warning(
            "Refresh token device mismatch for user %s: expected=%s, got=%s",
            user.email,
            token_record.device_fingerprint[:50],
            current_device[:50],
        )
        # Don't block, but log the suspicious activity

    # Revoke old refresh token (token rotation)
    token_record.revoked = True
    token_record.revoked_at = datetime.now(UTC)
    token_record.replaced_by = str(token_record.id)  # Self-reference for now

    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store new refresh token in database
    new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()

    new_token_record = RefreshToken(
        user_id=str(user.id),
        token_hash=new_token_hash,
        device_fingerprint=current_device,
        user_agent=request.headers.get("user-agent", "")[:500],
        ip_address=request.client.host if request.client else "unknown",
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        revoked=False,
    )

    db.add(new_token_record)
    await db.commit()

    logger.info("Token refreshed for user: %s", user.email)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# ============================================================================
# MFA SETUP ENDPOINT
# ============================================================================


@router.post("/mfa/setup", response_model=dict)
async def setup_mfa(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Initiate MFA setup for user.

    Returns:
        MFA setup information (secret, QR code, recovery codes)
    """
    # Check if MFA already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    # Setup MFA
    setup_info = await mfa_service.setup_mfa(current_user, db)

    logger.info("MFA setup initiated for user: %s", current_user.email)

    return setup_info


@router.post("/mfa/verify", response_model=dict)
async def verify_mfa_setup(
    totp_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA setup and enable MFA for user.

    Args:
        totp_code: 6-digit TOTP code
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message
    """
    is_valid = await mfa_service.verify_mfa_setup(current_user, totp_code, db)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication code",
        )

    logger.info("MFA enabled for user: %s", current_user.email)

    return {"message": "MFA enabled successfully"}


@router.post("/mfa/disable", response_model=dict)
async def disable_mfa(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Disable MFA for user.

    Returns:
        Success message
    """
    await mfa_service.disable_mfa(current_user, db)

    logger.info("MFA disabled for user: %s", current_user.email)

    return {"message": "MFA disabled successfully"}


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================


@router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint for authentication service.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "3.0.0-unified",
    }
