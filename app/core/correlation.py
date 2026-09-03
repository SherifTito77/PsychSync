"""
Correlation ID Context Manager

Propagates correlation IDs across service boundaries for distributed tracing.
Enables request tracking across HTTP, database operations, and background tasks.

Usage:
    from app.core.correlation import get_correlation_id, set_correlation_id, log_with_context

    # In middleware or request handler
    set_correlation_id(request.state.correlation_id)

    # In any service or business logic
    correlation_id = get_correlation_id()

    # Structured logging with automatic correlation ID injection
    log_with_context(logger, logging.INFO, "Operation completed", user_id="123")
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Any, Optional

# =============================================================================
# Correlation ID Context (Thread-safe, Async-safe)
# =============================================================================

CORRELATION_ID_CONTEXT: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID in context for the current request/task.

    Args:
        correlation_id: Unique identifier for this request
    """
    CORRELATION_ID_CONTEXT.set(correlation_id)


def get_correlation_id() -> str:
    """
    Get correlation ID from context or generate new one.

    Returns:
        Correlation ID string (always returns a valid UUID)
    """
    correlation_id = CORRELATION_ID_CONTEXT.get()
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        CORRELATION_ID_CONTEXT.set(correlation_id)
    return correlation_id


def clear_correlation_id() -> None:
    """Clear correlation ID from context (typically at end of request)"""
    CORRELATION_ID_CONTEXT.set(None)


# =============================================================================
# Structured Logging Helper
# =============================================================================


def log_with_context(
    logger_instance: logging.Logger, level: int, message: str, **extra
) -> None:
    """
    Log a message with automatic correlation ID injection.

    This helper ensures every log message includes the correlation ID
    for distributed tracing, without requiring developers to manually
    include it in every call.

    Args:
        logger_instance: Logger instance (e.g., logging.getLogger(__name__))
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Human-readable log message
        **extra: Additional structured fields (e.g., user_id, event, operation)

    Example:
        from app.core.correlation import log_with_context

        log_with_context(
            logger,
            logging.INFO,
            "User logged in successfully",
            event="auth_success",
            user_id=str(user.id),
            client_ip=request.client.host,
        )
    """
    # Automatically inject correlation ID
    extra["correlation_id"] = get_correlation_id()

    # Log with extra context
    logger_instance.log(level, message, extra=extra)


# =============================================================================
# Performance Logging Helper
# =============================================================================

import time
from functools import wraps
from typing import Callable


def log_performance(
    operation_name: str,
    warning_threshold_ms: float = 5000,
    logger_instance: Optional[logging.Logger] = None,
):
    """
    Decorator to automatically log operation performance metrics.

    Tracks execution time and automatically logs warnings for slow operations.

    Args:
        operation_name: Name of the operation for logging
        warning_threshold_ms: Threshold in ms for performance warning (default: 5000ms)
        logger_instance: Logger instance (creates new one if not provided)

    Example:
        @log_performance("database_query", warning_threshold_ms=1000)
        async def get_user_data(user_id: str):
            # Database query logic
            pass

    Output:
        INFO: Database query completed - duration_ms: 234.5, success: true
    """
    if logger_instance is None:
        logger_instance = logging.getLogger(__name__)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger_instance,
                    logging.INFO,
                    f"{operation_name} completed",
                    event="performance_metric",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )

                # Warning if slow
                if duration_ms > warning_threshold_ms:
                    log_with_context(
                        logger_instance,
                        logging.WARNING,
                        f"Slow {operation_name} detected",
                        event="performance_slow",
                        operation=operation_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=warning_threshold_ms,
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger_instance,
                    logging.ERROR,
                    f"{operation_name} failed",
                    event="performance_error",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                )

                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger_instance,
                    logging.INFO,
                    f"{operation_name} completed",
                    event="performance_metric",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    success=True,
                )

                if duration_ms > warning_threshold_ms:
                    log_with_context(
                        logger_instance,
                        logging.WARNING,
                        f"Slow {operation_name} detected",
                        event="performance_slow",
                        operation=operation_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=warning_threshold_ms,
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logger_instance,
                    logging.ERROR,
                    f"{operation_name} failed",
                    event="performance_error",
                    operation=operation_name,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    exc_info=True,
                )

                raise

        # Return appropriate wrapper based on whether function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =============================================================================
# Database Operation Logging Helper
# =============================================================================


def log_db_operation(
    operation: str, table: str, record_id: Optional[str] = None, **extra_fields
) -> Callable:
    """
    Decorator to log database CRUD operations with performance metrics.

    Args:
        operation: Database operation type (create, read, update, delete)
        table: Database table name
        record_id: Optional record identifier (will be logged if provided)
        **extra_fields: Additional fields to log (e.g., user_id, organization_id)

    Example:
        @log_db_operation("create", "responses", user_id=lambda r: str(r.user_id))
        async def create_response(db, response_in):
            # Creation logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                # Call the function
                result = await func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Extract record ID if result is an object with id attribute
                result_id = record_id
                if result_id is None and hasattr(result, "id"):
                    result_id = str(result.id)

                # Prepare extra fields
                log_fields = {
                    "event": f"db_{operation}_success",
                    "operation": operation,
                    "table": table,
                    "duration_ms": round(duration_ms, 2),
                    "success": True,
                }

                if result_id:
                    log_fields[f"{table}_id"] = result_id

                # Add dynamic fields (e.g., callable fields that need result)
                for key, value in extra_fields.items():
                    if callable(value):
                        log_fields[key] = value(result)
                    else:
                        log_fields[key] = value

                log_with_context(
                    logging.getLogger(func.__module__),
                    logging.INFO,
                    f"Database {operation} operation completed",
                    **log_fields,
                )

                # Slow query warning
                if duration_ms > 500:  # >500ms
                    log_with_context(
                        logging.getLogger(func.__module__),
                        logging.WARNING,
                        f"Slow database {operation} detected",
                        event="db_slow_query",
                        operation=operation,
                        table=table,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=500,
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                log_with_context(
                    logging.getLogger(func.__module__),
                    logging.ERROR,
                    f"Database {operation} operation failed",
                    event="db_{operation}_error",
                    operation=operation,
                    table=table,
                    duration_ms=round(duration_ms, 2),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    exc_info=True,
                    **extra_fields,
                )

                raise

        return async_wrapper

    return decorator
