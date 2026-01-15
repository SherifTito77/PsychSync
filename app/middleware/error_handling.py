# app/middleware/error_handling.py
"""
Error handling middleware for FastAPI application
Catches and formats all exceptions consistently
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import PsychSyncException, ErrorCode

logger = logging.getLogger(__name__)


async def psychsync_exception_handler(
    request: Request, exc: PsychSyncException
) -> JSONResponse:
    """
    Handle PsychSync custom exceptions with structured error responses

    Args:
        request: FastAPI request object
        exc: PsychSync exception

    Returns:
        JSONResponse with standardized error format
    """
    # Get request ID from state or generate new one
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the error
    logger.error(
        f"PsychSyncException: {exc.error_code.value} - {exc.message}",
        extra={
            "error_code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Build error response
    error_response = {
        "error": True,
        "error_code": exc.error_code.value,
        "message": exc.message,
        "status_code": exc.status_code,
        "details": exc.details,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "path": request.url.path,
    }

    # Add retry_after if rate limit error
    if exc.error_code in [ErrorCode.RATE_LIMIT_EXCEEDED_AUTH, ErrorCode.RATE_LIMIT_EXCEEDED]:
        error_response["retry_after"] = exc.details.get("retry_after", 60)

    # Add documentation URL
    error_response["documentation_url"] = (
        f"https://docs.psychsync.com/api/errors/{exc.error_code.value}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI request validation errors

    Args:
        request: FastAPI request object
        exc: Request validation exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Validation error: {len(errors)} field(s)",
        extra={
            "error_code": ErrorCode.VALIDATION_ERROR.value,
            "errors": errors,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )

    error_response = {
        "error": True,
        "error_code": ErrorCode.VALIDATION_ERROR.value,
        "message": "Request validation failed",
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "details": {"errors": errors, "error_count": len(errors)},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "path": request.url.path,
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
    """
    """
    Handle all other unhandled exceptions

    Args:
        request: FastAPI request object
        exc: Generic exception

    Returns:
        JSONResponse with standardized error format
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log critical errors
    logger.critical(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        extra={
            "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True,
    )

    error_response = {
        "error": True,
        "error_code": ErrorCode.INTERNAL_SERVER_ERROR.value,
        "message": "An unexpected error occurred. Please try again later.",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "details": (
            {"exception_type": type(exc).__name__} if logger.level <= logging.DEBUG else {}
        ),
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "path": request.url.path,
    }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID and handle errors globally
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Perform operation.

Args:
    **kwargs: Input parameters

Returns:
    Operation result
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            # Handle exceptions
            if isinstance(exc, PsychSyncException):
                return await psychsync_exception_handler(request, exc)
            elif isinstance(exc, RequestValidationError):
                return await validation_exception_handler(request, exc)
            else:
                return await generic_exception_handler(request, exc)


def add_request_id(request: Request) -> str:
    """
    Get or generate request ID

    Args:
        request: FastAPI request object

    Returns:
        Request ID string
    """
    if not hasattr(request.state, "request_id"):
        request.state.request_id = str(uuid.uuid4())
    return request.state.request_id
