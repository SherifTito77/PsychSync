"""
Standardized HTTP Error Response Utility

Provides consistent error response handling across all API endpoints.
Ensures correct HTTP status code usage per REST conventions.

Usage:
    from app.core.http_errors import (
        raise_not_found,
        raise_forbidden,
        raise_unauthorized,
        raise_validation_error,
        raise_conflict,
        raise_server_error,
    )

    # Resource not found
    raise_not_found("User", user_id)

    # Permission denied (user is authenticated but not authorized)
    raise_forbidden("You don't have permission to access this resource")

    # Validation error (user is authenticated but provided invalid data)
    raise_validation_error("password", "Password must be at least 8 characters")

    # Resource conflict (duplicate, state mismatch)
    raise_conflict("Email", "already exists")

Author: API Team
Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================================================
# ERROR RESPONSE MODELS
# ============================================================================


class ErrorDetail(BaseModel):
    """Standardized error response structure"""

    detail: str
    error_code: str
    status_code: int
    timestamp: str
    request_id: str | None = None
    field: str | None = None  # For validation errors
    resource: str | None = None  # For resource-related errors


# ============================================================================
# ERROR CODE CONSTANTS
# ============================================================================

# 2xx Success (not errors, but documented for completeness)
HTTP_200_OK = status.HTTP_200_OK
HTTP_201_CREATED = status.HTTP_201_CREATED
HTTP_204_NO_CONTENT = status.HTTP_204_NO_CONTENT

# 4xx Client Errors
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_409_CONFLICT = status.HTTP_409_CONFLICT
HTTP_422_UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
HTTP_429_TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS

# 5xx Server Errors
HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
HTTP_501_NOT_IMPLEMENTED = status.HTTP_501_NOT_IMPLEMENTED
HTTP_503_SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE


# ============================================================================
# CLIENT ERROR FUNCTIONS (4xx)
# ============================================================================


def raise_validation_error(
    field: str,
    message: str,
    request_id: str | None = None,
) -> None:
    """
    Raise a 400 BAD_REQUEST error for input validation failures.

    Use Cases:
    - Invalid input format (email, phone number, etc.)
    - Missing required fields
    - Invalid enum values
    - Business logic validation (authenticated user providing wrong data)

    IMPORTANT: User IS authenticated - this is not an auth error

    Examples:
        - Password doesn't meet requirements (while changing password)
        - Invalid email format
        - Missing required field

    Args:
        field: Field name that failed validation
        message: Human-readable error message
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 400 BAD_REQUEST
    """
    error_code = f"VALIDATION_ERROR_{field.upper()}"

    logger.warning(
        f"Validation error for field '{field}': {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_400_BAD_REQUEST,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 400,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "field": field,
        },
    )


def raise_unauthorized(
    message: str = "Authentication required",
    request_id: str | None = None,
) -> None:
    """
    Raise a 401 UNAUTHORIZED error for missing or invalid authentication.

    Use Cases:
    - Missing or invalid authentication token
    - Expired token
    - Failed authentication (wrong username/password)

    IMPORTANT: Use ONLY when authentication fails, not for authorization

    Examples:
        - No token provided
        - Token expired
        - Invalid credentials (during login, not during authenticated operations)

    Args:
        message: Human-readable error message
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 401 UNAUTHORIZED
    """
    error_code = "AUTHENTICATION_REQUIRED"

    logger.warning(
        f"Unauthorized access attempt: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 401,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
    )


def raise_forbidden(
    message: str = "You don't have permission to access this resource",
    request_id: str | None = None,
) -> None:
    """
    Raise a 403 FORBIDDEN error for authorization failures.

    Use Cases:
    - User is authenticated but lacks permission
    - Resource ownership check failed
    - Role-based access control denied
    - Tenant isolation check failed

    IMPORTANT: User IS authenticated but not authorized

    Examples:
        - User trying to access another user's resource
        - Regular user trying to access admin endpoint
        - User accessing resource from different organization

    Args:
        message: Human-readable error message
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 403 FORBIDDEN
    """
    error_code = "AUTHORIZATION_DENIED"

    logger.warning(
        f"Forbidden access attempt: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 403,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
    )


def raise_not_found(
    resource: str,
    resource_id: str | int | None = None,
    request_id: str | None = None,
) -> None:
    """
    Raise a 404 NOT_FOUND error for missing resources.

    Use Cases:
    - Resource doesn't exist in database
    - Resource was deleted
    - Invalid ID provided

    Examples:
        - User not found
        - Assessment not found
        - Email connection not found

    Args:
        resource: Resource type (e.g., "User", "Assessment", "EmailConnection")
        resource_id: Optional resource ID for context
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 404 NOT_FOUND
    """
    error_code = f"{resource.upper()}_NOT_FOUND"

    if resource_id:
        message = f"{resource} with ID '{resource_id}' not found"
    else:
        message = f"{resource} not found"

    logger.info(
        f"Resource not found: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_404_NOT_FOUND,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 404,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "resource": resource,
        },
    )


def raise_conflict(
    resource: str,
    message: str,
    request_id: str | None = None,
) -> None:
    """
    Raise a 409 CONFLICT error for resource state conflicts.

    Use Cases:
    - Duplicate resource (unique constraint violation)
    - Resource state incompatible with operation
    - Concurrent modification conflict

    Examples:
        - Email already exists
        - Username already taken
        - Assessment already completed

    Args:
        resource: Resource type (e.g., "Email", "Username", "Assessment")
        message: Human-readable error message
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 409 CONFLICT
    """
    error_code = f"{resource.upper()}_CONFLICT"

    logger.warning(
        f"Resource conflict for {resource}: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_409_CONFLICT,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 409,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
            "resource": resource,
        },
    )


def raise_unprocessable_entity(
    message: str,
    error_code: str = "UNPROCESSABLE_ENTITY",
    request_id: str | None = None,
) -> None:
    """
    Raise a 422 UNPROCESSABLE_ENTITY error for semantic errors.

    Use Cases:
    - Request is well-formed but contains semantic errors
    - Business logic violations
    - Complex validation failures

    Examples:
        - Assessment deadline passed
        - Invalid state transition
        - Referential integrity issues

    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 422 UNPROCESSABLE_ENTITY
    """
    logger.warning(
        f"Unprocessable entity: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 422,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
    )


def raise_rate_limit_exceeded(
    retry_after: int | None = None,
    request_id: str | None = None,
) -> None:
    """
    Raise a 429 TOO_MANY_REQUESTS error for rate limiting.

    Use Cases:
    - Rate limit exceeded
    - IP banned
    - Account temporarily locked

    Args:
        retry_after: Seconds until client can retry
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 429 TOO_MANY_REQUESTS
    """
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please slow down."

    if retry_after:
        message += f" Try again in {retry_after} seconds."

    logger.warning(
        f"Rate limit exceeded: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    raise HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 429,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
        headers=headers,
    )


# ============================================================================
# SERVER ERROR FUNCTIONS (5xx)
# ============================================================================


def raise_server_error(
    message: str = "An internal error occurred",
    error_code: str = "INTERNAL_SERVER_ERROR",
    request_id: str | None = None,
    log_level: str = "error",
) -> None:
    """
    Raise a 500 INTERNAL_SERVER_ERROR for unexpected server errors.

    Use Cases:
    - Unexpected database errors
    - External service failures
    - Configuration errors
    - Unhandled exceptions

    IMPORTANT: Only use for genuine server errors, not client errors

    Examples:
        - Database connection failed
        - External API timeout
        - File system error
        - Unhandled exception

    Args:
        message: Human-readable error message (don't expose internals)
        error_code: Machine-readable error code
        request_id: Optional request ID for tracing
        log_level: Log level ("error", "critical")

    Raises:
        HTTPException: 500 INTERNAL_SERVER_ERROR
    """
    log_func = getattr(logger, log_level, logger.error)

    log_func(
        f"Internal server error: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 500,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
    )


def raise_not_implemented(
    feature: str,
    request_id: str | None = None,
) -> None:
    """
    Raise a 501 NOT_IMPLEMENTED error for unimplemented features.

    Args:
        feature: Feature name
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 501 NOT_IMPLEMENTED
    """
    error_code = "NOT_IMPLEMENTED"
    message = f"The '{feature}' feature is not implemented"

    logger.warning(
        f"Not implemented: {feature}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    raise HTTPException(
        status_code=HTTP_501_NOT_IMPLEMENTED,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 501,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
    )


def raise_service_unavailable(
    message: str = "Service temporarily unavailable",
    retry_after: int | None = None,
    request_id: str | None = None,
) -> None:
    """
    Raise a 503 SERVICE_UNAVAILABLE for temporary service unavailability.

    Use Cases:
    - Service maintenance
    - Service overloaded
    - Dependent service down

    Args:
        message: Human-readable error message
        retry_after: Seconds until service should be available
        request_id: Optional request ID for tracing

    Raises:
        HTTPException: 503 SERVICE_UNAVAILABLE
    """
    error_code = "SERVICE_UNAVAILABLE"

    logger.warning(
        f"Service unavailable: {message}",
        extra={"error_code": error_code, "request_id": request_id},
    )

    headers = {}
    if retry_after:
        headers["Retry-After"] = str(retry_after)

    raise HTTPException(
        status_code=HTTP_503_SERVICE_UNAVAILABLE,
        detail={
            "detail": message,
            "error_code": error_code,
            "status_code": 503,
            "timestamp": datetime.now(UTC).isoformat(),
            "request_id": request_id,
        },
        headers=headers,
    )


# ============================================================================
# DECORATOR FOR AUTOMATIC REQUEST ID EXTRACTION
# ============================================================================


def get_request_id() -> str | None:
    """
    Extract request ID from current request context.

    Returns:
        Request ID if available, None otherwise
    """
    try:
        # Try to get from context var if set
        import contextvars

        request_id_ctx = contextvars.ContextVar("request_id", default=None)
        return request_id_ctx.get()
    except Exception:
        return None
