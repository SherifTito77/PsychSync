# app/core/handlers.py
"""
FastAPI exception handlers for consistent error responses
"""
from typing import Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import logging

from app.core.exceptions import (
    PsychSyncException,
    handle_database_error,
    create_error_response
)
from app.core.response import ErrorResponse

logger = logging.getLogger(__name__)


async def psychsync_exception_handler(request: Request, exc: PsychSyncException) -> JSONResponse:
    """Handler for PsychSync custom exceptions"""
    # Log the exception with context
    exc.log()

    # Add request context to details
    exc.details.update({
        "path": str(request.url),
        "method": request.method
    })

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc)
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """Handler for FastAPI HTTP exceptions"""
    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )

    # Create standardized error response
    error_response = ErrorResponse(
        message=str(exc.detail),
        error_code=f"HTTP_{exc.status_code}",
        data={"path": str(request.url), "method": request.method}
    )

    # Convert to dict with datetime serialization
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json", exclude_unset=True)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for request validation errors"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "errors": exc.errors(),
            "path": str(request.url),
            "method": request.method
        }
    )

    # Format validation errors for better client understanding
    formatted_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })

    error_response = ErrorResponse(
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        data={
            "errors": formatted_errors,
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json", exclude_unset=True)
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handler for SQLAlchemy database errors"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method
        },
        exc_info=True
    )

    # Convert to structured exception
    operation = f"{request.method} {request.url.path}"
    structured_exc = handle_database_error(exc, operation)

    return JSONResponse(
        status_code=structured_exc.status_code,
        content=create_error_response(structured_exc)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for any unhandled exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method,
            "exception_message": str(exc)
        },
        exc_info=True
    )

    # Create a generic internal server error response
    from app.core.exceptions import PsychSyncException, ErrorCode

    generic_exc = PsychSyncException(
        message="An unexpected error occurred",
        error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        details={
            "path": str(request.url),
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(generic_exc)
    )