# app/api/v1/endpoints/client_errors.py
"""
Client Error Reporting Endpoint

Receives error reports from the frontend ErrorBoundary component,
logs them with full context for debugging and monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ClientErrorReport(BaseModel):
    """Client error report model from ErrorBoundary"""

    errorId: str = Field(..., description="Unique error identifier")
    message: str = Field(..., description="Error message")
    stack: Optional[str] = Field(None, description="Stack trace")
    componentStack: Optional[str] = Field(None, description="React component stack")
    timestamp: str = Field(..., description="ISO timestamp of when the error occurred")
    userAgent: Optional[str] = Field(None, description="Browser user agent")
    url: Optional[str] = Field(None, description="Page URL where error occurred")
    userId: Optional[str] = Field(None, description="User ID if authenticated")
    retryCount: Optional[int] = Field(0, description="Number of retry attempts")
    buildVersion: Optional[str] = Field(
        "unknown", description="Application build version"
    )


@router.post(
    "/errors/client",
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="Receive client error report",
    description="Receives error reports from the frontend ErrorBoundary component",
    responses={
        201: {"description": "Error report received successfully"},
        400: {"description": "Invalid error report data"},
    },
)
async def receive_client_error_report(
    error_report: ClientErrorReport,
) -> Dict[str, str]:
    """
    Receive an error report from the frontend ErrorBoundary and log it.

    Args:
        error_report: Client error report with full context

    Returns:
        Confirmation message
    """
    try:
        # Log the error with full context
        logger.error(
            f"Client Error [{error_report.errorId}]: {error_report.message}",
            extra={
                "source": "frontend_error_boundary",
                "error_id": error_report.errorId,
                "error_message": error_report.message,
                "error_stack": error_report.stack,
                "component_stack": error_report.componentStack,
                "user_id": error_report.userId,
                "url": error_report.url,
                "user_agent": error_report.userAgent,
                "build_version": error_report.buildVersion,
                "retry_count": error_report.retryCount,
                "timestamp": error_report.timestamp,
            },
        )

        # Log stack trace if available
        if error_report.stack:
            logger.error(
                f"Client Error Stack Trace [{error_report.errorId}]:\n{error_report.stack}",
                extra={
                    "source": "frontend_error_boundary",
                    "error_id": error_report.errorId,
                },
            )

        # Log component stack if available
        if error_report.componentStack:
            logger.error(
                f"Component Stack Trace [{error_report.errorId}]:\n{error_report.componentStack}",
                extra={
                    "source": "frontend_error_boundary",
                    "error_id": error_report.errorId,
                },
            )

        return {
            "status": "logged",
            "message": "Error report received and logged",
            "error_id": error_report.errorId,
        }

    except Exception as e:
        logger.error(
            f"Failed to process client error report: {e}",
            extra={
                "error_report": (
                    error_report.dict()
                    if hasattr(error_report, "dict")
                    else str(error_report)
                ),
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process error report: {e}",
        )


@router.get(
    "/errors/client/health",
    response_model=Dict[str, str],
    summary="Client error reporting endpoint health check",
    description="Health check for the client error reporting endpoint",
)
async def client_errors_health() -> Dict[str, str]:
    """
    Health check endpoint for client error reporting system.

    Returns:
        Status message indicating the error reporting system is operational
    """
    return {
        "status": "healthy",
        "service": "client-error-reporting",
        "timestamp": datetime.utcnow().isoformat(),
    }
