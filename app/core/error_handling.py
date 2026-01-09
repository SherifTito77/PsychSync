# app/core/error_handling.py
"""
Standardized Error Handling System for PsychSync
Provides consistent error handling patterns across all services
"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
import logging
import traceback
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import (
    DatabaseError,
    IntegrityError,
    OperationalError,
    PendingRollbackError,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseOperationException(Exception):
    """Custom exception for database operation failures"""

    def __init__(self, message: str, operation: str, original_error: Exception = None):
        self.message = message
        self.operation = operation
        self.original_error = original_error
        super().__init__(self.message)


class ValidationException(Exception):
    """Custom exception for validation failures"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def handle_database_errors(operation_name: str, reraise: bool = True):
    """
    Standardized database error handling decorator

    Args:
        operation_name: Name of the database operation for logging
        reraise: Whether to reraise exceptions after handling

    Returns:
        Decorated function with consistent error handling
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Extract database session from kwargs or args
            db: AsyncSession | None = kwargs.get("db")
            if not db and len(args) > 0:
                # First argument might be the database session
                db = args[0] if hasattr(args[0], "commit") else None

            start_time = datetime.utcnow()

            try:
                # Execute the function
                result = await func(*args, **kwargs)

                # Log successful operation
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(
                    f"Database operation '{operation_name}' completed successfully",
                    extra={
                        "operation": operation_name,
                        "duration_ms": duration_ms,
                        "success": True,
                    },
                )

                return result

            except IntegrityError as e:
                # Handle constraint violations
                if db:
                    await db.rollback()

                error_message = str(e.orig) if hasattr(e, "orig") else str(e)

                # Determine specific constraint type
                if "unique" in error_message.lower():
                    detail = f"Resource already exists: {operation_name}"
                    status_code = status.HTTP_409_CONFLICT
                elif "foreign key" in error_message.lower():
                    detail = f"Referenced resource not found: {operation_name}"
                    status_code = status.HTTP_400_BAD_REQUEST
                elif "not null" in error_message.lower():
                    detail = f"Required field missing: {operation_name}"
                    status_code = status.HTTP_400_BAD_REQUEST
                else:
                    detail = f"Data integrity error: {operation_name}"
                    status_code = status.HTTP_400_BAD_REQUEST

                logger.warning(
                    f"Integrity error in {operation_name}: {error_message}",
                    extra={
                        "operation": operation_name,
                        "error_type": "integrity_error",
                        "error_detail": error_message,
                        "status_code": status_code,
                    },
                )

                if reraise:
                    raise HTTPException(status_code=status_code, detail=detail)

            except OperationalError as e:
                # Handle database connection/operation issues
                if db:
                    await db.rollback()

                error_message = str(e.orig) if hasattr(e, "orig") else str(e)

                # Check for connection issues
                if "connection" in error_message.lower():
                    detail = "Database connection error. Please try again later."
                    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                else:
                    detail = f"Database operation failed: {operation_name}"
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

                logger.error(
                    f"Operational error in {operation_name}: {error_message}",
                    extra={
                        "operation": operation_name,
                        "error_type": "operational_error",
                        "error_detail": error_message,
                        "status_code": status_code,
                    },
                )

                if reraise:
                    raise HTTPException(status_code=status_code, detail=detail)

            except (DatabaseError, PendingRollbackError) as e:
                # Handle general database errors
                if db:
                    try:
                        await db.rollback()
                    except Exception as rollback_error:
                        logger.error(
                            f"Failed to rollback transaction in {operation_name}: {rollback_error}"
                        )

                error_message = str(e)

                logger.error(
                    f"Database error in {operation_name}: {error_message}",
                    extra={
                        "operation": operation_name,
                        "error_type": "database_error",
                        "error_detail": error_message,
                        "traceback": traceback.format_exc(),
                    },
                )

                if reraise:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Database operation failed: {operation_name}",
                    )

            except ValidationException as e:
                # Handle validation errors
                if db:
                    await db.rollback()

                logger.warning(
                    f"Validation error in {operation_name}: {e.message}",
                    extra={
                        "operation": operation_name,
                        "error_type": "validation_error",
                        "field": e.field,
                        "error_detail": e.message,
                    },
                )

                if reraise:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

            except ValueError as e:
                # Handle value errors (commonly raised for business logic validation)
                if db:
                    await db.rollback()

                logger.warning(
                    f"Value error in {operation_name}: {e!s}",
                    extra={
                        "operation": operation_name,
                        "error_type": "value_error",
                        "error_detail": str(e),
                    },
                )

                if reraise:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

            except HTTPException:
                # Re-raise HTTP exceptions as-is (already properly formatted)
                if db:
                    await db.rollback()
                raise

            except Exception as e:
                # Handle any other unexpected errors
                if db:
                    try:
                        await db.rollback()
                    except Exception as rollback_error:
                        logger.error(
                            f"Failed to rollback transaction in {operation_name}: {rollback_error}"
                        )

                logger.error(
                    f"Unexpected error in {operation_name}: {e!s}",
                    extra={
                        "operation": operation_name,
                        "error_type": "unexpected_error",
                        "error_detail": str(e),
                        "traceback": traceback.format_exc(),
                    },
                )

                if reraise:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"An unexpected error occurred during {operation_name}",
                    )

        return wrapper

    return decorator


def handle_service_errors(service_name: str):
    """
    Error handling decorator for non-database service operations

    Args:
        service_name: Name of the service for logging

    Returns:
        Decorated function with consistent error handling
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except ValidationException as e:
                logger.warning(
                    f"Validation error in {service_name}.{func.__name__}: {e.message}",
                    extra={
                        "service": service_name,
                        "function": func.__name__,
                        "error_type": "validation_error",
                        "field": e.field,
                        "error_detail": e.message,
                    },
                )

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)

            except ValueError as e:
                logger.warning(
                    f"Value error in {service_name}.{func.__name__}: {e!s}",
                    extra={
                        "service": service_name,
                        "function": func.__name__,
                        "error_type": "value_error",
                        "error_detail": str(e),
                    },
                )

                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise

            except Exception as e:
                logger.error(
                    f"Unexpected error in {service_name}.{func.__name__}: {e!s}",
                    extra={
                        "service": service_name,
                        "function": func.__name__,
                        "error_type": "unexpected_error",
                        "error_detail": str(e),
                        "traceback": traceback.format_exc(),
                    },
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred in {service_name}",
                )

        return wrapper

    return decorator


# TODO(human): Implement CircuitBreaker pattern for handling database connection issues
# This should track consecutive failures and temporarily stop trying operations
# after a threshold is reached, with gradual recovery attempts


class CircuitBreaker:
    """
    Circuit breaker pattern for handling database connection issues
    Prevents cascading failures when database is unavailable
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Service temporarily unavailable - circuit breaker is OPEN",
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset"""
        import time

        return (
            (time.time() - self.last_failure_time) >= self.timeout
            if self.last_failure_time
            else True
        )

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failed operation"""
        import time

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


# Global circuit breaker instance for database operations
database_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)


def with_circuit_breaker(circuit_breaker: CircuitBreaker = None):
    """
    Decorator to add circuit breaker protection to functions
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = circuit_breaker or database_circuit_breaker
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
