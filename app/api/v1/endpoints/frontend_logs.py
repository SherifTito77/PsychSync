# app/api/v1/endpoints/frontend_logs.py
"""
Frontend Logging Endpoint

Receives structured logs from the frontend application,
logs them with proper context for debugging and monitoring.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class FrontendLogEntry(BaseModel):
    """Frontend log entry model"""
    timestamp: str = Field(..., description="ISO timestamp of when the log occurred")
    level: str = Field(..., description="Log level: info, warn, error, debug")
    message: str = Field(..., description="Log message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing")
    stack: Optional[str] = Field(None, description="Stack trace for errors")


class BulkFrontendLogs(BaseModel):
    """Multiple frontend log entries"""
    logs: list[FrontendLogEntry] = Field(..., description="List of log entries")


@router.post(
    "/logs/frontend",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Receive frontend logs",
    description="Receives structured logs from the frontend application for centralized logging",
    responses={
        201: {"description": "Logs received successfully"},
        400: {"description": "Invalid log data"},
    },
)
async def receive_frontend_logs(
    log_entry: FrontendLogEntry,
) -> Dict[str, str]:
    """
    Receive a single frontend log entry and log it to the application logger.

    Args:
        log_entry: Frontend log entry with timestamp, level, message, and context

    Returns:
        Confirmation message
    """
    try:
        # Map frontend log levels to Python logging levels
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR,
        }

        log_level = log_level_map.get(log_entry.level.lower(), logging.INFO)

        # Prepare log context
        log_context = {
            "source": "frontend",
            "user_id": log_entry.user_id,
            "session_id": log_entry.session_id,
            "correlation_id": log_entry.correlation_id,
            **(log_entry.context or {}),
        }

        # Log with appropriate level and context
        logger.log(
            log_level,
            f"Frontend: {log_entry.message}",
            extra=log_context,
        )

        # Include stack trace for errors
        if log_entry.level.lower() == "error" and log_entry.stack:
            logger.error(
                f"Frontend error stack trace:\n{log_entry.stack}",
                extra={
                    "source": "frontend",
                    "user_id": log_entry.user_id,
                    "session_id": log_entry.session_id,
                    "correlation_id": log_entry.correlation_id,
                },
            )

        return {"status": "logged", "message": "Log entry received and logged"}

    except Exception as e:
        logger.error(
            f"Failed to process frontend log: {e}",
            extra={
                "log_entry": log_entry.dict() if hasattr(log_entry, 'dict') else str(log_entry),
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process log entry: {e}",
        )


@router.post(
    "/logs/frontend/bulk",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Receive multiple frontend logs",
    description="Receives multiple frontend log entries for batch processing",
    responses={
        201: {"description": "Logs received successfully"},
        400: {"description": "Invalid log data"},
    },
)
async def receive_bulk_frontend_logs(
    bulk_logs: BulkFrontendLogs,
) -> Dict[str, str]:
    """
    Receive multiple frontend log entries and log them to the application logger.

    Args:
        bulk_logs: Multiple frontend log entries

    Returns:
        Confirmation message with count of logs received
    """
    try:
        log_count = len(bulk_logs.logs)

        # Map frontend log levels to Python logging levels
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warn": logging.WARNING,
            "error": logging.ERROR,
        }

        for log_entry in bulk_logs.logs:
            log_level = log_level_map.get(log_entry.level.lower(), logging.INFO)

            # Prepare log context
            log_context = {
                "source": "frontend",
                "user_id": log_entry.user_id,
                "session_id": log_entry.session_id,
                "correlation_id": log_entry.correlation_id,
                **(log_entry.context or {}),
            }

            # Log with appropriate level and context
            logger.log(
                log_level,
                f"Frontend: {log_entry.message}",
                extra=log_context,
            )

            # Include stack trace for errors
            if log_entry.level.lower() == "error" and log_entry.stack:
                logger.error(
                    f"Frontend error stack trace:\n{log_entry.stack}",
                    extra={
                        "source": "frontend",
                        "user_id": log_entry.user_id,
                        "session_id": log_entry.session_id,
                        "correlation_id": log_entry.correlation_id,
                    },
                )

        logger.info(
            f"Received {log_count} frontend log entries",
            extra={
                "source": "frontend",
                "log_count": log_count,
            },
        )

        return {
            "status": "logged",
            "message": f"Received and logged {log_count} log entries",
            "count": str(log_count),
        }

    except Exception as e:
        logger.error(
            f"Failed to process bulk frontend logs: {e}",
            extra={
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process log entries: {e}",
        )


@router.get(
    "/logs/frontend/health",
    response_model=Dict[str, str],
    summary="Frontend logging endpoint health check",
    description="Health check for the frontend logging endpoint",
)
async def frontend_logs_health() -> Dict[str, str]:
    """
    Health check endpoint for frontend logging system.

    Returns:
        Status message indicating the logging system is operational
    """
    return {
        "status": "healthy",
        "service": "frontend-logs",
        "timestamp": datetime.utcnow().isoformat(),
    }
