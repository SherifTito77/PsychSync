"""
Advanced Audit Logging Service

Comprehensive audit logging for security, compliance, and monitoring.
Tracks all sensitive operations, data access, and system events.

Features:
- Automatic action logging
- Request/response tracking
- Data change history
- User activity monitoring
- Compliance reporting (HIPAA, GDPR, SOC 2)
- Real-time alerting on suspicious patterns

Audit Events:
- Authentication (login, logout, MFA)
- Data access (read, write, delete)
- Configuration changes
- Permission modifications
- Export operations
- Failed authentication attempts
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from fastapi import Request

from app.db.models.user import User

logger = logging.getLogger(__name__)


# =============================================================================
# Audit Event Types
# =============================================================================

class AuditEventType(str):
    """Enumeration of audit event types"""

    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"

    # Data Access Events
    DATA_READ = "data_read"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    BULK_DATA_ACCESS = "bulk_data_access"

    # User Management Events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"
    USER_PERMISSION_GRANTED = "user_permission_granted"
    USER_PERMISSION_REVOKED = "user_permission_revoked"

    # Clinical Events (HIPAA)
    PATIENT_DATA_ACCESS = "patient_data_access"
    CLINICAL_ASSESSMENT_CREATED = "clinical_assessment_created"
    CLINICAL_ASSESSMENT_UPDATED = "clinical_assessment_updated"
    CLINICAL_NOTES_ACCESS = "clinical_notes_access"
    DIAGNOSIS_CREATED = "diagnosis_created"
    DIAGNOSIS_UPDATED = "diagnosis_updated"

    # Security Events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    UNUSUAL_DATA_ACCESS = "unusual_data_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"

    # Configuration Events
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"

    # Compliance Events
    GDPR_DATA_REQUEST = "gdpr_data_request"
    GDPR_DATA_EXPORT = "gdpr_data_export"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    AUDIT_LOG_EXPORT = "audit_log_export"


class AuditSeverity(str):
    """Severity levels for audit events"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Audit Service
# =============================================================================

class AuditService:
    """
    Service for logging and managing audit events.

    Features:
    - Structured event logging
    - Request context tracking
    - Data change tracking
    - User activity monitoring
    - Compliance reporting
    - Real-time alerting
    """

    def __init__(self):
        self.logger = logging.getLogger("audit")

    # -------------------------------------------------------------------------
    # Core Logging Methods
    # -------------------------------------------------------------------------

    async def log_event(
        self,
        db: AsyncSession,
        event_type: str,
        user_id: Optional[UUID],
        details: Dict[str, Any],
        severity: str = AuditSeverity.INFO,
        request: Optional[Request] = None,
    ) -> None:
        """
        Log an audit event.

        Args:
            db: Database session
            event_type: Type of event (from AuditEventType)
            user_id: User UUID (None for system events)
            details: Event details (will be JSON-serialized)
            severity: Event severity
            request: Optional FastAPI request for context
        """
        try:
            # Extract request context
            request_context = self._extract_request_context(request) if request else {}

            # Create audit log entry
            from app.db.models.audit import AuditLog

            audit_entry = AuditLog(
                id=uuid4(),
                event_type=event_type,
                user_id=user_id,
                severity=severity,
                details=details,
                ip_address=request_context.get("ip_address"),
                user_agent=request_context.get("user_agent"),
                request_path=request_context.get("request_path"),
                request_method=request_context.get("request_method"),
                timestamp=datetime.now(timezone.utc),
            )

            db.add(audit_entry)
            await db.commit()

            # Log to application logger for real-time monitoring
            self._log_to_logger(audit_entry)

            # Check for suspicious patterns
            await self._check_suspicious_patterns(db, audit_entry)

        except Exception as e:
            # Don't fail application if audit logging fails
            logger.error(f"Failed to log audit event: {str(e)}")

    async def log_data_access(
        self,
        db: AsyncSession,
        user_id: UUID,
        table_name: str,
        record_id: Union[str, UUID],
        action: str,  # read, created, updated, deleted
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> None:
        """
        Log data access/modification event.

        Args:
            db: Database session
            user_id: User who performed the action
            table_name: Database table affected
            record_id: ID of the record
            action: Action performed (read, created, updated, deleted)
            details: Additional details
            request: Optional FastAPI request
        """
        event_details = {
            "table": table_name,
            "record_id": str(record_id),
            "action": action,
        }

        if details:
            event_details.update(details)

        # Map action to event type
        event_type_map = {
            "read": AuditEventType.DATA_READ,
            "created": AuditEventType.DATA_CREATED,
            "updated": AuditEventType.DATA_UPDATED,
            "deleted": AuditEventType.DATA_DELETED,
        }

        await self.log_event(
            db=db,
            event_type=event_type_map.get(action, "data_access"),
            user_id=user_id,
            details=event_details,
            request=request,
        )

    async def log_authentication_event(
        self,
        db: AsyncSession,
        event_type: str,
        user_id: Optional[UUID],
        success: bool,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> None:
        """
        Log authentication-related event.

        Args:
            db: Database session
            event_type: Type of auth event
            user_id: User UUID (None for failed login)
            success: Whether authentication succeeded
            details: Additional details
            request: FastAPI request
        """
        event_details = details or {}
        event_details["success"] = success

        severity = AuditSeverity.INFO if success else AuditSeverity.HIGH

        await self.log_event(
            db=db,
            event_type=event_type,
            user_id=user_id,
            details=event_details,
            severity=severity,
            request=request,
        )

    async def log_permission_change(
        self,
        db: AsyncSession,
        admin_user_id: UUID,
        target_user_id: UUID,
        permission: str,
        granted: bool,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> None:
        """
        Log permission modification.

        Args:
            db: Database session
            admin_user_id: Admin who made the change
            target_user_id: User whose permissions changed
            permission: Permission that was modified
            granted: True if permission was granted, False if revoked
            details: Additional details
            request: FastAPI request
        """
        event_details = {
            "admin_user_id": str(admin_user_id),
            "target_user_id": str(target_user_id),
            "permission": permission,
            "granted": granted,
        }

        if details:
            event_details.update(details)

        event_type = (
            AuditEventType.USER_PERMISSION_GRANTED
            if granted
            else AuditEventType.USER_PERMISSION_REVOKED
        )

        await self.log_event(
            db=db,
            event_type=event_type,
            user_id=admin_user_id,
            details=event_details,
            severity=AuditSeverity.MEDIUM,
            request=request,
        )

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    async def get_user_activity(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """
        Get audit log for specific user.

        Args:
            db: Database session
            user_id: User UUID
            limit: Max records to return
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        try:
            from app.db.models.audit import AuditLog

            query = (
                select(AuditLog)
                .where(AuditLog.user_id == user_id)
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get user activity: {str(e)}")
            return []

    async def get_events_by_type(
        self,
        db: AsyncSession,
        event_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """
        Get audit logs by event type.

        Args:
            db: Database session
            event_type: Type of event
            limit: Max records
            offset: Pagination offset

        Returns:
            List of audit log entries
        """
        try:
            from app.db.models.audit import AuditLog

            query = (
                select(AuditLog)
                .where(AuditLog.event_type == event_type)
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .offset(offset)
            )

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get events by type: {str(e)}")
            return []

    async def get_failed_login_attempts(
        self,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Any]:
        """
        Get recent failed login attempts.

        Args:
            db: Database session
            hours: Lookback period in hours
            limit: Max records

        Returns:
            List of failed login attempts
        """
        try:
            from app.db.models.audit import AuditLog
            from datetime import timedelta

            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == AuditEventType.LOGIN_FAILED,
                        AuditLog.timestamp >= cutoff_time,
                    )
                )
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
            )

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get failed login attempts: {str(e)}")
            return []

    async def get_suspicious_activity(
        self,
        db: AsyncSession,
        hours: int = 24,
    ) -> Dict[str, List[Any]]:
        """
        Get suspicious activity patterns.

        Args:
            db: Database session
            hours: Lookback period

        Returns:
            Dict with suspicious activity categories
        """
        try:
            from app.db.models.audit import AuditLog
            from datetime import timedelta
            from sqlalchemy import func

            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            # Multiple failed logins per user
            failed_logins_query = (
                select(
                    AuditLog.user_id,
                    func.count().label("failed_count")
                )
                .where(
                    and_(
                        AuditLog.event_type == AuditEventType.LOGIN_FAILED,
                        AuditLog.timestamp >= cutoff_time,
                    )
                )
                .group_by(AuditLog.user_id)
                .having(func.count() > 5)  # More than 5 failed attempts
            )

            failed_logins_result = await db.execute(failed_logins_query)

            # Bulk data access
            bulk_access_query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == AuditEventType.BULK_DATA_ACCESS,
                        AuditLog.timestamp >= cutoff_time,
                    )
                )
                .order_by(desc(AuditLog.timestamp))
            )

            bulk_access_result = await db.execute(bulk_access_query)

            # Unauthorized access attempts
            unauthorized_query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                        AuditLog.timestamp >= cutoff_time,
                    )
                )
                .order_by(desc(AuditLog.timestamp))
            )

            unauthorized_result = await db.execute(unauthorized_query)

            return {
                "multiple_failed_logins": failed_logins_result.all(),
                "bulk_data_access": bulk_access_result.scalars().all(),
                "unauthorized_attempts": unauthorized_result.scalars().all(),
            }

        except Exception as e:
            logger.error(f"Failed to get suspicious activity: {str(e)}")
            return {}

    # -------------------------------------------------------------------------
    # Compliance Reports
    # -------------------------------------------------------------------------

    async def generate_compliance_report(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "hipaa",
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit logs.

        Args:
            db: Database session
            start_date: Report start date
            end_date: Report end date
            report_type: Type of report (hipaa, gdpr, soc2)

        Returns:
            Compliance report data
        """
        try:
            from app.db.models.audit import AuditLog
            from sqlalchemy import func

            query = (
                select(
                    AuditLog.event_type,
                    func.count().label("count")
                )
                .where(
                    and_(
                        AuditLog.timestamp >= start_date,
                        AuditLog.timestamp <= end_date,
                    )
                )
                .group_by(AuditLog.event_type)
            )

            result = await db.execute(query)
            event_counts = {row.event_type: row.count for row in result}

            return {
                "report_type": report_type,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "event_summary": event_counts,
                "total_events": sum(event_counts.values()),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            return {}

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract context from FastAPI request"""
        context = {
            "request_path": request.url.path,
            "request_method": request.method,
            "user_agent": request.headers.get("user-agent"),
        }

        # Get IP address (handle proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            context["ip_address"] = forwarded_for.split(",")[0].strip()
        else:
            context["ip_address"] = request.client.host if request.client else None

        return context

    def _log_to_logger(self, audit_entry) -> None:
        """Log audit entry to application logger"""
        log_message = f"Audit: {audit_entry.event_type}"

        if audit_entry.user_id:
            log_message += f" | User: {audit_entry.user_id}"

        if audit_entry.ip_address:
            log_message += f" | IP: {audit_entry.ip_address}"

        # Map severity to log level
        severity_levels = {
            AuditSeverity.CRITICAL: logging.CRITICAL,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.INFO: logging.INFO,
        }

        log_level = severity_levels.get(audit_entry.severity, logging.INFO)

        self.logger.log(log_level, log_message, extra={"audit_entry": audit_entry})

    async def _check_suspicious_patterns(
        self,
        db: AsyncSession,
        audit_entry,
    ) -> None:
        """Check for suspicious activity patterns"""
        try:
            # Check for multiple failed logins from same IP
            if audit_entry.event_type == AuditEventType.LOGIN_FAILED:
                from app.db.models.audit import AuditLog
                from datetime import timedelta
                from sqlalchemy import func

                # Count failed logins from same IP in last hour
                one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

                query = (
                    select(func.count())
                    .select_from(AuditLog)
                    .where(
                        and_(
                            AuditLog.ip_address == audit_entry.ip_address,
                            AuditLog.event_type == AuditEventType.LOGIN_FAILED,
                            AuditLog.timestamp >= one_hour_ago,
                        )
                    )
                )

                result = await db.execute(query)
                failed_count = result.scalar() or 0

                if failed_count >= 5:
                    # Log suspicious activity
                    await self.log_event(
                        db=db,
                        event_type=AuditEventType.MULTIPLE_FAILED_LOGINS,
                        user_id=None,
                        details={
                            "ip_address": audit_entry.ip_address,
                            "failed_attempts": failed_count,
                            "timeframe": "1 hour",
                        },
                        severity=AuditSeverity.HIGH,
                    )

        except Exception as e:
            logger.error(f"Failed to check suspicious patterns: {str(e)}")


# =============================================================================
# Global Service Instance
# =============================================================================

audit_service = AuditService()


# =============================================================================
# Convenience Functions
# =============================================================================

async def log_event(
    db: AsyncSession,
    event_type: str,
    user_id: Optional[UUID],
    details: Dict[str, Any],
    severity: str = AuditSeverity.INFO,
    request: Optional[Request] = None,
) -> None:
    """Convenience function to log audit event"""
    await audit_service.log_event(db, event_type, user_id, details, severity, request)


async def log_data_access(
    db: AsyncSession,
    user_id: UUID,
    table_name: str,
    record_id: Union[str, UUID],
    action: str,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """Convenience function to log data access"""
    await audit_service.log_data_access(db, user_id, table_name, record_id, action, details, request)
