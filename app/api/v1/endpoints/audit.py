"""
Audit Logging API Endpoints

Provides endpoints for querying and managing audit logs.
Admin and auditor access only for security and compliance.

Access: Administrators and auditors
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import get_async_db, get_current_user
from app.db.models.user import User
from app.services.audit_service import AuditEventType, AuditSeverity, audit_service

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/audit", tags=["audit-logging"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_admin_or_auditor(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is admin or auditor"""
    if current_user.is_superuser:
        return current_user

    # TODO: Add auditor role check
    # if current_user.role in ["admin", "auditor"]:
    #     return current_user

    raise HTTPException(
        status_code=403, detail="Administrator or auditor access required"
    )


# =============================================================================
# Pydantic Schemas
# =============================================================================


class AuditLogResponse(BaseModel):
    """Response schema for audit log entry"""

    id: UUID
    event_type: str
    user_id: Optional[UUID]
    severity: str
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditLogsResponse(BaseModel):
    """Response schema for audit logs query"""

    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class ComplianceReportRequest(BaseModel):
    """Request schema for compliance report generation"""

    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    report_type: str = Field(
        default="hipaa", description="Type of report (hipaa, gdpr, soc2)"
    )


class SuspiciousActivityResponse(BaseModel):
    """Response schema for suspicious activity"""

    multiple_failed_logins: List[Dict[str, Any]]
    bulk_data_access: List[Dict[str, Any]]
    unauthorized_attempts: List[Dict[str, Any]]


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/logs/user/{user_id}", response_model=AuditLogsResponse)
async def get_user_audit_logs(
    user_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get audit logs for a specific user.

    **Admin/Auditor Only**

    Useful for investigating user activity or compliance review.

    **Path Parameters:**
    - user_id: User UUID

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)

    **Response:**
    ```json
    {
      "logs": [...],
      "total": 150,
      "page": 1,
      "page_size": 50
    }
    ```
    """

    try:
        offset = (page - 1) * page_size

        logs = await audit_service.get_user_activity(
            db=db,
            user_id=user_id,
            limit=page_size,
            offset=offset,
        )

        # Get total count
        from sqlalchemy import func, select

        from app.db.models.audit import AuditLog

        count_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.user_id == user_id)
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        return AuditLogsResponse(
            logs=[AuditLogResponse.model_validate(log) for log in logs],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to get user audit logs: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.get("/logs/event/{event_type}", response_model=AuditLogsResponse)
async def get_logs_by_event_type(
    event_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get audit logs by event type.

    **Admin/Auditor Only**

    Useful for tracking specific types of events.

    **Path Parameters:**
    - event_type: Type of event (e.g., login_success, data_read)

    **Query Parameters:**
    - page: Page number (default: 1)
    - page_size: Items per page (default: 50, max: 100)
    """

    try:
        offset = (page - 1) * page_size

        logs = await audit_service.get_events_by_type(
            db=db,
            event_type=event_type,
            limit=page_size,
            offset=offset,
        )

        return AuditLogsResponse(
            logs=[AuditLogResponse.model_validate(log) for log in logs],
            total=len(logs),
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to get logs by event type: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.get("/logs/failed-logins", response_model=List[AuditLogResponse])
async def get_failed_login_attempts(
    hours: int = Query(
        24, ge=1, le=168, description="Lookback period in hours (max 7 days)"
    ),
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get recent failed login attempts.

    **Admin/Auditor Only**

    Useful for security monitoring and detecting brute force attacks.

    **Query Parameters:**
    - hours: Lookback period in hours (default: 24, max: 168)
    - limit: Maximum results (default: 100, max: 500)

    **Response:**
    ```json
    [
      {
        "id": "uuid",
        "event_type": "login_failed",
        "user_id": null,
        "severity": "high",
        "timestamp": "2024-01-17T10:00:00Z",
        ...
      }
    ]
    ```
    """

    try:
        logs = await audit_service.get_failed_login_attempts(
            db=db,
            hours=hours,
            limit=limit,
        )

        return [AuditLogResponse.model_validate(log) for log in logs]

    except Exception as e:
        logger.error(f"Failed to get failed login attempts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve logs: {str(e)}"
        )


@router.get("/suspicious-activity", response_model=SuspiciousActivityResponse)
async def get_suspicious_activity(
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours"),
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get suspicious activity patterns.

    **Admin/Auditor Only**

    Analyzes audit logs to detect:
    - Multiple failed logins from same IP/user
    - Bulk data access (potential scraping)
    - Unauthorized access attempts

    **Query Parameters:**
    - hours: Lookback period in hours (default: 24, max: 168)

    **Response:**
    ```json
    {
      "multiple_failed_logins": [...],
      "bulk_data_access": [...],
      "unauthorized_attempts": [...]
    }
    ```
    """

    try:
        suspicious_activity = await audit_service.get_suspicious_activity(
            db=db,
            hours=hours,
        )

        return SuspiciousActivityResponse(**suspicious_activity)

    except Exception as e:
        logger.error(f"Failed to get suspicious activity: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze activity: {str(e)}"
        )


@router.post("/compliance-report")
async def generate_compliance_report(
    request: ComplianceReportRequest,
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Generate compliance report.

    **Admin/Auditor Only**

    Generates a compliance report for specified date range.
    Supports HIPAA, GDPR, and SOC 2 reporting.

    **Request Body:**
    ```json
    {
      "start_date": "2024-01-01T00:00:00Z",
      "end_date": "2024-01-31T23:59:59Z",
      "report_type": "hipaa"
    }
    ```

    **Response:**
    ```json
    {
      "report_type": "hipaa",
      "period": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-31T23:59:59Z"
      },
      "event_summary": {
        "login_success": 1500,
        "data_read": 5000,
        "patient_data_access": 250
      },
      "total_events": 6750,
      "generated_at": "2024-01-17T12:00:00Z"
    }
    ```
    """

    try:
        report = await audit_service.generate_compliance_report(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            report_type=request.report_type,
        )

        # Log the report generation
        await audit_service.log_event(
            db=db,
            event_type=AuditEventType.AUDIT_LOG_EXPORT,
            user_id=admin_user.id,
            details={
                "report_type": request.report_type,
                "period_start": request.start_date.isoformat(),
                "period_end": request.end_date.isoformat(),
            },
        )

        return report

    except Exception as e:
        logger.error(f"Failed to generate compliance report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/stats/summary")
async def get_audit_statistics(
    hours: int = Query(24, ge=1, le=168, description="Lookback period in hours"),
    admin_user: User = Depends(get_admin_or_auditor),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get audit log statistics summary.

    **Admin/Auditor Only**

    Provides high-level statistics about system activity.

    **Query Parameters:**
    - hours: Lookback period in hours (default: 24, max: 168)

    **Response:**
    ```json
    {
      "total_events": 5420,
      "unique_users": 125,
      "logins": 450,
      "failed_logins": 15,
      "data_access": 3200,
      "suspicious_events": 3,
      "period_hours": 24
    }
    ```
    """

    try:
        from datetime import timedelta

        from sqlalchemy import and_, func, select

        from app.db.models.audit import AuditLog

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Total events
        total_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.timestamp >= cutoff_time)
        )
        total_result = await db.execute(total_query)
        total_events = total_result.scalar() or 0

        # Unique users
        users_query = (
            select(func.count(func.distinct(AuditLog.user_id)))
            .select_from(AuditLog)
            .where(
                and_(AuditLog.timestamp >= cutoff_time, AuditLog.user_id.isnot(None))
            )
        )
        users_result = await db.execute(users_query)
        unique_users = users_result.scalar() or 0

        # Logins
        logins_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= cutoff_time,
                    AuditLog.event_type.in_(
                        [AuditEventType.LOGIN_SUCCESS, AuditEventType.LOGIN_FAILED]
                    ),
                )
            )
        )
        logins_result = await db.execute(logins_query)
        logins = logins_result.scalar() or 0

        # Failed logins
        failed_logins_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= cutoff_time,
                    AuditLog.event_type == AuditEventType.LOGIN_FAILED,
                )
            )
        )
        failed_result = await db.execute(failed_logins_query)
        failed_logins = failed_result.scalar() or 0

        # Data access events
        data_access_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= cutoff_time,
                    AuditLog.event_type.in_(
                        [
                            AuditEventType.DATA_READ,
                            AuditEventType.DATA_CREATED,
                            AuditEventType.DATA_UPDATED,
                            AuditEventType.DATA_DELETED,
                        ]
                    ),
                )
            )
        )
        data_access_result = await db.execute(data_access_query)
        data_access = data_access_result.scalar() or 0

        # Suspicious events (high or critical severity)
        suspicious_query = (
            select(func.count())
            .select_from(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= cutoff_time,
                    AuditLog.severity.in_([AuditSeverity.HIGH, AuditSeverity.CRITICAL]),
                )
            )
        )
        suspicious_result = await db.execute(suspicious_query)
        suspicious_events = suspicious_result.scalar() or 0

        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "logins": logins,
            "failed_logins": failed_logins,
            "data_access": data_access,
            "suspicious_events": suspicious_events,
            "period_hours": hours,
        }

    except Exception as e:
        logger.error(f"Failed to get audit statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/events/types")
async def list_event_types(
    admin_user: User = Depends(get_admin_or_auditor),
):
    """
    List all available audit event types.

    **Admin/Auditor Only**

    Returns a comprehensive list of event types that can be queried.

    **Response:**
    ```json
    {
      "authentication_events": [
        {"type": "login_success", "description": "Successful user login"},
        {"type": "login_failed", "description": "Failed login attempt"},
        ...
      ],
      "data_access_events": [
        {"type": "data_read", "description": "Data read operation"},
        ...
      ],
      "total_types": 35
    }
    ```
    """

    from app.services.audit_service import AuditEventType

    event_categories = {
        "authentication_events": [
            {
                "type": AuditEventType.LOGIN_SUCCESS,
                "description": "Successful user login",
            },
            {
                "type": AuditEventType.LOGIN_FAILED,
                "description": "Failed login attempt",
            },
            {"type": AuditEventType.LOGOUT, "description": "User logout"},
            {"type": AuditEventType.MFA_ENABLED, "description": "MFA enabled for user"},
            {
                "type": AuditEventType.MFA_DISABLED,
                "description": "MFA disabled for user",
            },
            {
                "type": AuditEventType.MFA_VERIFIED,
                "description": "MFA verified during login",
            },
            {
                "type": AuditEventType.MFA_FAILED,
                "description": "MFA verification failed",
            },
            {"type": AuditEventType.PASSWORD_CHANGE, "description": "Password changed"},
            {
                "type": AuditEventType.PASSWORD_RESET,
                "description": "Password reset completed",
            },
            {
                "type": AuditEventType.PASSWORD_RESET_REQUESTED,
                "description": "Password reset requested",
            },
        ],
        "data_access_events": [
            {"type": AuditEventType.DATA_READ, "description": "Data read operation"},
            {"type": AuditEventType.DATA_CREATED, "description": "New data created"},
            {"type": AuditEventType.DATA_UPDATED, "description": "Data updated"},
            {"type": AuditEventType.DATA_DELETED, "description": "Data deleted"},
            {"type": AuditEventType.DATA_EXPORTED, "description": "Data exported"},
            {
                "type": AuditEventType.BULK_DATA_ACCESS,
                "description": "Bulk data access (multiple records)",
            },
        ],
        "user_management_events": [
            {"type": AuditEventType.USER_CREATED, "description": "New user created"},
            {
                "type": AuditEventType.USER_UPDATED,
                "description": "User details updated",
            },
            {"type": AuditEventType.USER_DELETED, "description": "User deleted"},
            {
                "type": AuditEventType.USER_ROLE_CHANGED,
                "description": "User role modified",
            },
            {
                "type": AuditEventType.USER_PERMISSION_GRANTED,
                "description": "Permission granted to user",
            },
            {
                "type": AuditEventType.USER_PERMISSION_REVOKED,
                "description": "Permission revoked from user",
            },
        ],
        "clinical_events": [
            {
                "type": AuditEventType.PATIENT_DATA_ACCESS,
                "description": "Patient data accessed (HIPAA)",
            },
            {
                "type": AuditEventType.CLINICAL_ASSESSMENT_CREATED,
                "description": "Clinical assessment created",
            },
            {
                "type": AuditEventType.CLINICAL_ASSESSMENT_UPDATED,
                "description": "Clinical assessment updated",
            },
            {
                "type": AuditEventType.CLINICAL_NOTES_ACCESS,
                "description": "Clinical notes accessed",
            },
            {
                "type": AuditEventType.DIAGNOSIS_CREATED,
                "description": "Diagnosis created",
            },
            {
                "type": AuditEventType.DIAGNOSIS_UPDATED,
                "description": "Diagnosis updated",
            },
        ],
        "security_events": [
            {
                "type": AuditEventType.SUSPICIOUS_ACTIVITY,
                "description": "Suspicious activity detected",
            },
            {
                "type": AuditEventType.MULTIPLE_FAILED_LOGINS,
                "description": "Multiple failed logins detected",
            },
            {
                "type": AuditEventType.UNUSUAL_DATA_ACCESS,
                "description": "Unusual data access pattern",
            },
            {
                "type": AuditEventType.PRIVILEGE_ESCALATION,
                "description": "Privilege escalation attempt",
            },
            {
                "type": AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                "description": "Unauthorized access attempt",
            },
        ],
    }

    total_types = sum(len(events) for events in event_categories.values())

    return {
        **event_categories,
        "total_types": total_types,
    }
