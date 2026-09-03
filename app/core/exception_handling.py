# app/core/exception_handling.py
"""
Standardized Exception Handling for API Endpoints

This module provides a consistent way to handle exceptions across all API endpoints.
It ensures:
1. Consistent error response format
2. No sensitive information leakage
3. Proper logging
4. Appropriate HTTP status codes
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.exceptions import ErrorCode, PsychSyncException

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# SECURITY: Safe Error Messages
# ============================================================================

SAFE_ERROR_MESSAGES = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: "An internal server error occurred. Please try again later.",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Service temporarily unavailable. Please try again later.",
    status.HTTP_504_GATEWAY_TIMEOUT: "Request timed out. Please try again.",
}


def get_safe_error_message(exception: Exception, status_code: int) -> str:
    """
    Get a safe error message that doesn't leak sensitive information.

    NEVER expose:
    - Database error details
    - Internal file paths
    - Stack traces
    - System information
    - User data

    Args:
        exception: The exception that occurred
        status_code: HTTP status code

    Returns:
        Safe, user-friendly error message
    """
    # Use predefined safe messages for server errors
    if status_code >= 500:
        return SAFE_ERROR_MESSAGES.get(
            status_code, "An unexpected error occurred. Please try again later."
        )

    # For client errors (4xx), use the exception message if it's a PsychSyncException
    if isinstance(exception, PsychSyncException):
        return exception.message

    # For validation errors, return a generic message
    if isinstance(exception, ValidationError):
        return "Request validation failed"

    # For HTTPException, use the detail if it's safe
    if isinstance(exception, HTTPException):
        return str(exception.detail) if exception.detail else "An error occurred"

    # Default fallback
    return str(exception)


def sanitize_error_detail(detail: str) -> str:
    """
    Sanitize error detail to prevent information leakage.

    Removes potentially sensitive information like:
    - File paths
    - Database queries
    - Stack traces
    - System configuration
    """
    # List of patterns that might indicate sensitive information
    sensitive_patterns = [
        "/app/",
        "/var/",
        "/home/",
        "/usr/",
        "SELECT ",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "DROP ",
        "TRACEBACK",
        "Error:",
        "Exception:",
        "at line",
        "in file",
    ]

    detail_lower = detail.lower()
    for pattern in sensitive_patterns:
        if pattern.lower() in detail_lower:
            # If sensitive pattern found, return generic message
            return "An error occurred while processing your request"

    return detail


# ============================================================================
# DECORATORS FOR CONSISTENT EXCEPTION HANDLING
# ============================================================================


def handle_exceptions(
    default_message: str = "An error occurred",
    error_code: str = None,
    reraise: bool = False,
):
    """
    Decorator to consistently handle exceptions in endpoint functions.

    Args:
        default_message: Default message if exception cannot be determined
        error_code: Default error code
        reraise: If True, re-raise the exception after logging

    Example:
        @handle_exceptions(default_message="Failed to create team")
        async def create_team(...):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is (already properly formatted)
                if reraise:
                    raise
                raise
            except PsychSyncException as e:
                # Log our custom exceptions
                e.log()
                if reraise:
                    raise
                # Convert to HTTP exception with proper format
                raise HTTPException(
                    status_code=e.status_code,
                    detail={
                        "message": e.message,
                        "error_code": e.error_code.value,
                        "details": e.details,
                    },
                )
            except ValidationError as e:
                # Handle Pydantic validation errors
                logger.warning(f"Validation error in {func.__name__}: {e.errors()}")
                if reraise:
                    raise
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": "Request validation failed",
                        "error_code": ErrorCode.VALIDATION_ERROR.value,
                        "errors": e.errors(),
                    },
                )
            except Exception as e:
                # Handle unexpected exceptions
                logger.error(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {e!s}",
                    exc_info=True,
                )
                if reraise:
                    raise

                # Return safe error message
                safe_message = get_safe_error_message(
                    e, status.HTTP_500_INTERNAL_SERVER_ERROR
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": safe_message,
                        "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    },
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except HTTPException:
                if reraise:
                    raise
                raise
            except PsychSyncException as e:
                e.log()
                if reraise:
                    raise
                raise HTTPException(
                    status_code=e.status_code,
                    detail={
                        "message": e.message,
                        "error_code": e.error_code.value,
                        "details": e.details,
                    },
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error in {func.__name__}: {type(e).__name__}: {e!s}",
                    exc_info=True,
                )
                if reraise:
                    raise

                safe_message = get_safe_error_message(
                    e, status.HTTP_500_INTERNAL_SERVER_ERROR
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": safe_message,
                        "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                    },
                )

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# CONTEXT MANAGER FOR EXCEPTION HANDLING
# ============================================================================


class ExceptionHandler:
    """
    Context manager for consistent exception handling in code blocks.

    Example:
        async with ExceptionHandler(operation="create_team"):
            # Code that might raise exceptions
            ...
    """

    def __init__(
        self,
        operation: str,
        reraise: bool = False,
        default_message: str = "Operation failed",
    ):
        self.operation = operation
        self.reraise = reraise
        self.default_message = default_message

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        # Handle the exception
        if exc_type == HTTPException:
            # Let HTTP exceptions propagate
            if not self.reraise:
                logger.warning(f"HTTPException in {self.operation}: {exc_val.detail}")
            return not self.reraise

        if issubclass(exc_type, PsychSyncException):
            # Log our custom exceptions
            logger.error(f"{exc_type.__name__} in {self.operation}: {exc_val}")
            return not self.reraise

        # Handle unexpected exceptions
        logger.error(
            f"Unexpected error in {self.operation}: {exc_type.__name__}: {exc_val}",
            exc_info=(exc_type, exc_val, exc_tb),
        )

        if not self.reraise:
            # Convert to HTTP exception
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": get_safe_error_message(
                        exc_val, status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                },
            )

        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return True

        if exc_type == HTTPException:
            if not self.reraise:
                logger.warning(f"HTTPException in {self.operation}: {exc_val.detail}")
            return not self.reraise

        if issubclass(exc_type, PsychSyncException):
            logger.error(f"{exc_type.__name__} in {self.operation}: {exc_val}")
            return not self.reraise

        logger.error(
            f"Unexpected error in {self.operation}: {exc_type.__name__}: {exc_val}",
            exc_info=(exc_type, exc_val, exc_tb),
        )

        if not self.reraise:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": get_safe_error_message(
                        exc_val, status.HTTP_500_INTERNAL_SERVER_ERROR
                    ),
                    "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
                },
            )

        return False


# ============================================================================
# HELPER FUNCTIONS FOR COMMON EXCEPTION PATTERNS
# ============================================================================


def raise_http_exception(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: str = None,
    details: dict[str, Any] = None,
) -> None:
    """
    Raise an HTTPException with consistent formatting.

    Args:
        message: Error message (will be sanitized)
        status_code: HTTP status code
        error_code: Application error code
        details: Additional error details (will be sanitized)
    """
    # Sanitize message to prevent information leakage
    safe_message = sanitize_error_detail(message)

    # Build detail dictionary
    detail = {"message": safe_message}

    if error_code:
        detail["error_code"] = error_code

    if details:
        # Sanitize details to remove sensitive information
        safe_details = {}
        for key, value in details.items():
            if isinstance(value, str):
                safe_details[key] = sanitize_error_detail(str(value))
            elif isinstance(value, (int, float, bool, list, dict)):
                # Only include safe types
                safe_details[key] = value
            # Skip other types (objects, etc.)
        detail["details"] = safe_details

    raise HTTPException(status_code=status_code, detail=detail)


def log_and_raise_exception(
    exception: Exception,
    operation: str,
    user_id: str = None,
    request_id: str = None,
    reraise_type: type[Exception] = HTTPException,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> None:
    """
    Log an exception and raise a standardized HTTP exception.

    Args:
        exception: The exception to log and convert
        operation: Description of the operation being performed
        user_id: User ID (optional)
        request_id: Request ID (optional)
        reraise_type: Type of exception to raise
        status_code: HTTP status code for the raised exception
    """
    log_data = {
        "operation": operation,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
    }

    if user_id:
        log_data["user_id"] = user_id
    if request_id:
        log_data["request_id"] = request_id

    logger.error(f"Exception in {operation}", extra=log_data, exc_info=True)

    # Raise standardized HTTP exception
    raise_http_exception(
        message=get_safe_error_message(exception, status_code),
        status_code=status_code,
        error_code=ErrorCode.INTERNAL_SERVER_ERROR.value,
    )
