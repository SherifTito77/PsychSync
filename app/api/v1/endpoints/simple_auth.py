"""
Simple authentication endpoint for testing purposes
Minimal implementation without complex security dependencies

Enhanced with structured logging and security audit trail
"""

import logging
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Form, HTTPException, Request, status
from sqlalchemy import text

from app.core.audit_logger import AuditLogger, SecurityEventType
from app.core.config.settings import settings
from app.core.correlation import get_correlation_id, log_with_context
from app.services.security import verify_password

router = APIRouter()
logger = logging.getLogger(__name__)


# Create a simple async engine for auth endpoints
async def get_auth_db_session():
    """Get a simple database session for authentication without complex dependencies"""
    from app.api.v1.deps import get_db

    # Get first session from the generator
    db_gen = get_db()
    db = await db_gen.__anext__()
    return db


@router.post("/simple-login")
async def simple_login(
    username: str = Form(...), password: str = Form(...), request: Request = None
):
    """
    Simple login endpoint that works without complex dependencies.
    For development/testing: Accepts any user that exists in the database with any password.

    Enhanced with structured logging and security audit trail.
    """
    client_ip = request.client.host if request and request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    correlation_id = get_correlation_id()

    try:
        # Get database session
        db = await get_auth_db_session()

        try:
            # ❌ BEFORE: print(f"❌ Login failed: User '{username}' not found in database")
            # ✅ AFTER: Structured logging with security context
            log_with_context(
                logger,
                logging.INFO,
                "Authentication attempt initiated",
                event="auth_attempt_start",
                username=username,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            # Query user from database (include password_hash for verification)
            result = await db.execute(
                text(
                    "SELECT id, email, full_name, password_hash FROM users WHERE email = :email"
                ),
                {"email": username},
            )
            user = result.fetchone()

            if not user:
                # ❌ BEFORE: print(f"❌ Login failed: User '{username}' not found in database")
                # ✅ AFTER: Structured logging with security audit
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Authentication failed - user not found",
                    event="auth_failure",
                    username=username,
                    reason="user_not_found",
                    client_ip=client_ip,
                    user_agent=user_agent,
                )

                # Security audit log for threat detection
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                    details=f"Login attempt with non-existent email: {username}",
                    client_ip=client_ip,
                    user_agent=user_agent,
                    endpoint="/api/v1/auth/simple-login",
                    method="POST",
                    request_id=correlation_id,
                    additional_data={
                        "username": username,
                        "reason": "user_not_found",
                    },
                )

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
                )

            # ❌ BEFORE: print(f"✅ User found: {user.email}, attempting login...")
            # ✅ AFTER: Structured logging
            log_with_context(
                logger,
                logging.INFO,
                "User found, attempting authentication",
                event="auth_user_found",
                user_id=str(user.id),
                email=user.email,
                client_ip=client_ip,
            )

            # SECURITY FIX: Verify password before issuing token
            if not verify_password(password, user.password_hash):
                # Password verification failed
                log_with_context(
                    logger,
                    logging.WARNING,
                    "Authentication failed - invalid password",
                    event="auth_failure",
                    user_id=str(user.id),
                    email=user.email,
                    reason="invalid_password",
                    client_ip=client_ip,
                    user_agent=user_agent,
                )

                # Security audit log for failed authentication
                AuditLogger.log_security_event(
                    event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                    details=f"Login attempt with invalid password for: {user.email}",
                    client_ip=client_ip,
                    user_agent=user_agent,
                    endpoint="/api/v1/auth/simple-login",
                    method="POST",
                    request_id=correlation_id,
                    additional_data={
                        "email": user.email,
                        "user_id": str(user.id),
                        "reason": "invalid_password",
                    },
                )

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
                )

            # Password verified successfully - create JWT token
            token_data = {
                "sub": user.email,
                "user_id": str(user.id),
                "name": user.full_name,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
            }

            token = jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

            # ❌ BEFORE: print(f"✅ Login successful for: {user.email}")
            # ✅ AFTER: Structured logging with security audit
            log_with_context(
                logger,
                logging.INFO,
                "Authentication successful",
                event="auth_success",
                user_id=str(user.id),
                email=user.email,
                client_ip=client_ip,
            )

            # Security audit log for compliance
            AuditLogger.log_security_event(
                user_id=str(user.id),
                event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
                details=f"Successful login for: {user.email}",
                client_ip=client_ip,
                user_agent=user_agent,
                endpoint="/api/v1/auth/simple-login",
                method="POST",
                request_id=correlation_id,
                additional_data={
                    "email": user.email,
                    "full_name": user.full_name,
                },
            )

            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.full_name,
                },
            }

        finally:
            try:
                await db.close()
            except Exception:
                pass

    except HTTPException:
        raise
    except Exception as e:
        # ❌ BEFORE: print(f"Simple login error: {e}"); import traceback; traceback.print_exc()
        # ✅ AFTER: Structured error logging with full context
        log_with_context(
            logger,
            logging.ERROR,
            "Authentication system error",
            event="auth_error",
            exc_info=True,
            username=username,
            error_type=type(e).__name__,
            error_message=str(e),
            client_ip=client_ip,
        )

        # Security audit log for system errors
        AuditLogger.log_security_event(
            event_type=SecurityEventType.SYSTEM_ERROR,
            details=f"Authentication system error: {str(e)}",
            client_ip=client_ip,
            user_agent=user_agent,
            endpoint="/api/v1/auth/simple-login",
            method="POST",
            request_id=correlation_id,
            severity="high",
            additional_data={
                "username": username,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/verify-token/{token}")
async def verify_token(token: str):
    """
    Simple token verification endpoint

    Enhanced with structured logging
    """
    correlation_id = get_correlation_id()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        log_with_context(
            logger,
            logging.INFO,
            "Token verification successful",
            event="token_verify_success",
            token_valid=True,
        )

        return {"valid": True, "payload": payload}

    except jwt.ExpiredSignatureError:
        log_with_context(
            logger,
            logging.WARNING,
            "Token verification failed - expired",
            event="token_verify_failed",
            reason="token_expired",
        )

        return {"valid": False, "error": "Token expired"}

    except jwt.InvalidTokenError as e:
        log_with_context(
            logger,
            logging.WARNING,
            "Token verification failed - invalid",
            event="token_verify_failed",
            reason="invalid_token",
            error_type=type(e).__name__,
        )

        return {"valid": False, "error": "Invalid token"}


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get current user information from token

    Enhanced with structured logging
    """
    correlation_id = get_correlation_id()
    client_ip = request.client.host if request and request.client else "unknown"

    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            log_with_context(
                logger,
                logging.WARNING,
                "Unauthorized access attempt - no token",
                event="auth_unauthorized",
                reason="no_token",
                client_ip=client_ip,
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided",
            )

        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        log_with_context(
            logger,
            logging.INFO,
            "User profile retrieved",
            event="user_profile_retrieved",
            user_id=payload.get("user_id"),
            email=payload.get("sub"),
        )

        return {
            "id": payload.get("user_id"),
            "email": payload.get("sub"),
            "name": payload.get("name"),
        }

    except jwt.ExpiredSignatureError:
        log_with_context(
            logger,
            logging.WARNING,
            "Token expired",
            event="auth_token_expired",
            client_ip=client_ip,
        )

        # ❌ BEFORE: print(f"Me endpoint error: {e}"); raise HTTPException(...)
        # ✅ AFTER: Structured error logging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )

    except jwt.InvalidTokenError as e:
        log_with_context(
            logger,
            logging.WARNING,
            "Invalid token",
            event="auth_invalid_token",
            client_ip=client_ip,
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from e
