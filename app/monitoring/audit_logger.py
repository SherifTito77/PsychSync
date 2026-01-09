#!/usr/bin/env python3
"""
Comprehensive Audit Logging System

Tracks all security-relevant events for:
- Compliance (SOC 2, HIPAA, GDPR)
- Incident response
- Forensic investigation
- Threat hunting

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

from datetime import datetime
from enum import Enum
from functools import wraps
import json
import logging
from pathlib import Path
from typing import Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""

    # Authentication Events
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED_LOGIN = "auth.failed_login"
    AUTH_PASSWORD_CHANGE = "auth.password_change"
    AUTH_PASSWORD_RESET = "auth.password_reset"
    AUTH_MFA_ENABLED = "auth.mfa_enabled"
    AUTH_MFA_DISABLED = "auth.mfa_disabled"
    AUTH_TOKEN_ISSUED = "auth.token_issued"
    AUTH_TOKEN_REFRESHED = "auth.token_refreshed"
    AUTH_TOKEN_REVOKED = "auth.token_revoked"

    # Authorization Events
    AUTHZ_ACCESS_GRANTED = "authz.access_granted"
    AUTHZ_ACCESS_DENIED = "authz.access_denied"
    AUTHZ_PRIVILEGE_ESCALATION = "authz.privilege_escalation"
    AUTHZ_ROLE_CHANGE = "authz.role_change"

    # Data Access Events
    DATA_READ = "data.read"
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    DATA_MODIFY = "data.modify"
    DATA_BULK_ACCESS = "data.bulk_access"

    # Configuration Events
    CONFIG_CHANGE = "config.change"
    CONFIG_SECURITY_SETTING = "config.security_setting"
    CONFIG_PERMISSION_CHANGE = "config.permission_change"

    # Security Events
    SECURITY_THREAT_DETECTED = "security.threat_detected"
    SECURITY_ALERT_TRIGGERED = "security.alert_triggered"
    SECURITY_INCIDENT_CREATED = "security.incident_created"
    SECURITY_INCIDENT_UPDATED = "security.incident_updated"
    SECURITY_INCIDENT_RESOLVED = "security.incident_resolved"

    # File Operations
    FILE_UPLOAD = "file.upload"
    FILE_DOWNLOAD = "file.download"
    FILE_DELETE = "file.delete"
    FILE_SHARE = "file.share"

    # System Events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_PERFORMANCE = "system.performance"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent:
    """
    Immutable audit event record.

    Captures all relevant information for security auditing.
    """

    def __init__(
        self,
        event_type: AuditEventType | str,
        severity: AuditSeverity | str,
        user_id: int | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        action: str | None = None,
        status: str = "success",
        details: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        # Convert enum to string if needed
        if isinstance(event_type, AuditEventType):
            event_type = event_type.value
        if isinstance(severity, AuditSeverity):
            severity = severity.value

        self.event_type = event_type
        self.severity = severity
        self.user_id = user_id
        self.session_id = session_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.status = status
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.request_id = request_id
        self.metadata = metadata or {}

        # Validate event
        self._validate()

    def _validate(self):
        """Validate audit event"""
        if not self.event_type:
            raise ValueError("event_type is required")

        if not self.severity:
            raise ValueError("severity is required")

        # Validate severity is valid
        valid_severities = [s.value for s in AuditSeverity]
        if self.severity not in valid_severities:
            raise ValueError(f"Invalid severity: {self.severity}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)

    def __repr__(self) -> str:
        return f"AuditEvent({self.event_type}, {self.severity}, user={self.user_id})"


class AuditLogger:
    """
    Centralized audit logging system.

    Provides multiple backends for log storage and real-time alerting.
    """

    def __init__(self):
        self.backends: list = []
        self._setup_backends()

    def _setup_backends(self):
        """Setup logging backends"""
        # Console backend (structured logging)
        self.backends.append(ConsoleAuditBackend())

        # File backend (rotation) - use local logs directory
        import os
        from pathlib import Path

        # Use local logs directory instead of /var/log
        log_dir = Path(os.environ.get("PSYCHSYNC_LOG_DIR", "logs/audit"))
        self.backends.append(
            FileAuditBackend(
                log_dir=str(log_dir),
                max_bytes=100 * 1024 * 1024,  # 100 MB
                backup_count=10,
            )
        )

        # Database backend (async)
        self.backends.append(DatabaseAuditBackend())

    async def log(self, event: AuditEvent):
        """
        Log audit event to all backends.

        Args:
            event: Audit event to log
        """
        try:
            # Log to console (immediate)
            logger.info(
                "AUDIT_EVENT",
                extra={
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "resource": f"{event.resource_type}:{event.resource_id}"
                    if event.resource_type
                    else None,
                    "status": event.status,
                    "details": event.details,
                },
            )

            # Log to all backends
            for backend in self.backends:
                try:
                    await backend.write(event)
                except Exception as e:
                    logger.error(f"Backend {backend.__class__.__name__} failed: {e}")

            # Trigger real-time alerts for critical events
            if event.severity in [AuditSeverity.HIGH.value, AuditSeverity.CRITICAL.value]:
                await self._trigger_alert(event)

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    async def _trigger_alert(self, event: AuditEvent):
        """Trigger real-time alert for critical events"""
        from app.monitoring.alert_notification_system import send_security_alert

        alert_message = f"[{event.severity.upper()}] {event.event_type}"

        if event.user_id:
            alert_message += f" - User ID: {event.user_id}"

        if event.ip_address:
            alert_message += f" - IP: {event.ip_address}"

        await send_security_alert(
            severity=event.severity,
            title=alert_message,
            description=event.details.get("description", str(event.details)),
            metadata=event.to_dict(),
        )

    # ==================== Convenience Methods ====================

    async def log_authentication(
        self,
        action: str,  # "login", "logout", "failed_login"
        user_id: int | None,
        ip_address: str,
        user_agent: str,
        success: bool,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Log authentication event"""
        event_type = f"auth.{action}"

        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.INFO,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failure",
            details=details or {},
            action=action,
        )

        await self.log(event)

    async def log_authorization(
        self,
        resource_type: str,
        resource_id: int,
        user_id: int,
        action: str,  # "read", "write", "delete"
        permitted: bool,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ):
        """Log authorization check"""
        event_type = "authz.access_granted" if permitted else "authz.access_denied"

        event = AuditEvent(
            event_type=event_type,
            severity=AuditSeverity.HIGH if not permitted else AuditSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status="permitted" if permitted else "denied",
            details=details or {},
        )

        await self.log(event)

    async def log_data_access(
        self,
        action: str,  # "read", "export", "delete"
        user_id: int,
        resource_type: str,
        resource_id: int,
        record_count: int | None = None,
        ip_address: str = None,
        details: dict[str, Any] | None = None,
    ):
        """Log data access event"""
        severity = AuditSeverity.INFO

        # Higher severity for bulk operations
        if record_count and record_count > 100:
            severity = AuditSeverity.MEDIUM
        if record_count and record_count > 1000:
            severity = AuditSeverity.HIGH

        event = AuditEvent(
            event_type=f"data.{action}",
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details={**(details or {}), "record_count": record_count},
        )

        await self.log(event)

    async def log_security_event(
        self,
        event_type: str,
        severity: AuditSeverity,
        description: str,
        user_id: int | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        """Log security event"""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            details={**(details or {}), "description": description},
        )

        await self.log(event)


# ==================== Logging Backends ====================


class ConsoleAuditBackend:
    """Console logging backend"""

    async def write(self, event: AuditEvent):
        """Write to console (already done in logger)"""


class FileAuditBackend:
    """File logging backend with rotation"""

    def __init__(
        self, log_dir: str = None, max_bytes: int = 100 * 1024 * 1024, backup_count: int = 10
    ):
        import os

        # Use local logs directory by default
        if log_dir is None:
            log_dir = os.environ.get("PSYCHSYNC_LOG_DIR", "logs/audit")

        self.log_dir = Path(log_dir)
        self.max_bytes = max_bytes
        self.backup_count = backup_count

        # Create log directory with error handling
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to current directory if can't create log dir
            self.log_dir = Path("logs/audit")
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup file handler
        import logging.handlers

        self.handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "audit.log", maxBytes=max_bytes, backupCount=backup_count
        )

        # JSON formatter
        formatter = logging.Formatter("%(message)s")
        self.handler.setFormatter(formatter)

    async def write(self, event: AuditEvent):
        """Write to file"""
        try:
            self.handler.emit(
                logging.LogRecord(
                    name="audit",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=event.to_json(),
                    args=(),
                    exc_info=None,
                )
            )
        except Exception as e:
            logger.error(f"Failed to write audit log to file: {e}")


class DatabaseAuditBackend:
    """Database logging backend for long-term retention"""

    async def write(self, event: AuditEvent):
        """Write to database"""
        from app.core.database import async_session_maker
        from app.db.models import AuditLog

        async with async_session_maker() as session:
            try:
                # Create audit log record
                log_entry = AuditLog(
                    event_type=event.event_type,
                    severity=event.severity,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    action=event.action,
                    status=event.status,
                    details=event.details,
                    timestamp=event.timestamp,
                    request_id=event.request_id,
                )

                session.add(log_entry)
                await session.commit()

            except Exception as e:
                logger.error(f"Failed to write audit log to database: {e}")
                await session.rollback()


# ==================== Decorators ====================


def audit_action(
    event_type: AuditEventType | str, severity: AuditSeverity | str = AuditSeverity.INFO
):
    """
    Decorator to audit function calls.

    Usage:
        @audit_action(AuditEventType.DATA_READ, AuditSeverity.INFO)
        async def get_user_data(user_id: int):
            return await fetch_data(user_id)
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)

            # Extract context from kwargs if available
            user_id = kwargs.get("user_id") or kwargs.get("current_user", {}).id
            ip_address = kwargs.get("ip_address")
            resource_id = kwargs.get("id") or kwargs.get("resource_id")

            # Log audit event
            audit_logger.log(
                AuditEvent(
                    event_type=event_type,
                    severity=severity,
                    user_id=user_id,
                    ip_address=ip_address,
                    resource_id=resource_id,
                    action=func.__name__,
                    status="success",
                )
            )

            return result

        return wrapper

    return decorator


# ==================== Query Interface ====================


class AuditQuery:
    """Query audit logs for reporting and analysis"""

    @staticmethod
    async def query_by_user(
        user_id: int, start_date: datetime, end_date: datetime, event_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Query audit logs by user"""
        from sqlalchemy import and_, select

        from app.core.database import async_session_maker
        from app.db.models import AuditLog

        async with async_session_maker() as session:
            query = select(AuditLog).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                )
            )

            if event_types:
                query = query.where(AuditLog.event_type.in_(event_types))

            query = query.order_by(AuditLog.timestamp.desc())

            result = await session.execute(query)
            return [row.to_dict() for row in result.scalars()]

    @staticmethod
    async def query_by_type(
        event_type: str, start_date: datetime, end_date: datetime, limit: int = 1000
    ) -> list[dict[str, Any]]:
        """Query audit logs by event type"""
        from sqlalchemy import and_, select

        from app.core.database import async_session_maker
        from app.db.models import AuditLog

        async with async_session_maker() as session:
            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.event_type == event_type,
                        AuditLog.timestamp >= start_date,
                        AuditLog.timestamp <= end_date,
                    )
                )
                .order_by(AuditLog.timestamp.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            return [row.to_dict() for row in result.scalars()]

    @staticmethod
    async def query_failed_authorizations(
        start_date: datetime, end_date: datetime, user_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Query failed authorization attempts"""
        from sqlalchemy import and_, or_, select

        from app.core.database import async_session_maker
        from app.db.models import AuditLog

        async with async_session_maker() as session:
            conditions = [
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                or_(AuditLog.event_type == "authz.access_denied", AuditLog.status == "denied"),
            ]

            if user_id:
                conditions.append(AuditLog.user_id == user_id)

            query = select(AuditLog).where(and_(*conditions)).order_by(AuditLog.timestamp.desc())

            result = await session.execute(query)
            return [row.to_dict() for row in result.scalars()]


# ==================== Global Instance ====================

audit_logger = AuditLogger()


# ==================== Convenience Functions ====================


async def log_auth_event(
    action: str, user_id: int | None, ip_address: str, user_agent: str, success: bool, **kwargs
):
    """Convenience function to log authentication event"""
    await audit_logger.log_authentication(
        action=action,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        **kwargs,
    )


async def log_authz_event(
    resource_type: str,
    resource_id: int,
    user_id: int,
    action: str,
    permitted: bool,
    ip_address: str,
    **kwargs,
):
    """Convenience function to log authorization event"""
    await audit_logger.log_authorization(
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        action=action,
        permitted=permitted,
        ip_address=ip_address,
        **kwargs,
    )


async def log_security_event(
    event_type: str, severity: AuditSeverity | str, description: str, **kwargs
):
    """Convenience function to log security event"""
    await audit_logger.log_security_event(
        event_type=event_type, severity=severity, description=description, **kwargs
    )


# ==================== Usage Examples ====================


def example_usage():
    """Example usage of audit logging"""

    async def login_example():
        """Example: Log login attempt"""
        await log_auth_event(
            action="login",
            user_id=123,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0...",
            success=True,
            details={"method": "password"},
        )

    async def authorization_example():
        """Example: Log authorization check"""
        await log_authz_event(
            resource_type="assessment",
            resource_id=456,
            user_id=123,
            action="read",
            permitted=True,
            ip_address="192.168.1.1",
        )

    async def security_event_example():
        """Example: Log security event"""
        await log_security_event(
            event_type="brute_force_attack",
            severity=AuditSeverity.HIGH,
            description="Multiple failed login attempts detected",
            user_id=123,
            ip_address="192.168.1.1",
            details={"attempts": 10},
        )


if __name__ == "__main__":
    print("Comprehensive Audit Logging System")
    print("Tracks all security-relevant events for compliance and incident response")
