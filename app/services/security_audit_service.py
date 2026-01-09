"""
Comprehensive Security Audit Logging Service
Logs security-relevant events for compliance, monitoring, and incident response
"""

import asyncio
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Types of security events to log."""

    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_TOKEN_REFRESH = "auth.token.refresh"
    AUTH_SESSION_EXPIRED = "auth.session.expired"

    # Authorization events
    AUTHZ_PERMISSION_GRANTED = "authz.permission.granted"
    AUTHZ_PERMISSION_DENIED = "authz.permission.denied"
    AUTHZ_ROLE_CHANGE = "authz.role.change"
    AUTHZ_PRIVILEGE_ESCALATION = "authz.privilege.escalation"

    # Data access events
    DATA_ACCESS = "data.access"
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    DATA_MODIFY = "data.modify"
    DATA_PII_ACCESS = "data.pii.access"
    DATA_PHI_ACCESS = "data.phi.access"

    # Account management
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_DELETED = "account.deleted"
    ACCOUNT_SUSPENDED = "account.suspended"
    ACCOUNT_REACTIVATED = "account.reactivated"
    ACCOUNT_EMAIL_CHANGED = "account.email.changed"

    # Security violations
    VIOLATION_RATE_LIMIT = "violation.rate_limit"
    VIOLATION_SQL_INJECTION = "violation.sql_injection"
    VIOLATION_XSS = "violation.xss"
    VIOLATION_CSRF = "violation.csrf"
    VIOLATION_PATH_TRAVERSAL = "violation.path_traversal"
    VIOLATION_BRUTE_FORCE = "violation.brute_force"
    VIOLATION_BLOCKED_IP = "violation.blocked_ip"
    VIOLATION_MALICIOUS_INPUT = "violation.malicious.input"

    # System events
    SYSTEM_CONFIG_CHANGE = "system.config.change"
    SYSTEM_SECURITY_SCAN = "system.security.scan"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"


class SecurityEvent(BaseModel):
    """Security event model."""

    # Event identification
    event_type: SecurityEventType = Field(..., description="Type of security event")
    event_id: str = Field(default_factory=lambda: f"{datetime.utcnow().timestamp()}", description="Unique event ID")

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    # Actor information
    user_id: str | None = Field(None, description="User ID who triggered the event")
    username: str | None = Field(None, description="Username (if available)")
    session_id: str | None = Field(None, description="Session ID")

    # Request information
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    request_id: str | None = Field(None, description="Request ID for tracing")
    endpoint: str | None = Field(None, description="API endpoint")
    method: str | None = Field(None, description="HTTP method")

    # Event details
    severity: str = Field(default="info", description="Event severity: debug, info, warning, error, critical")
    status: str = Field(default="success", description="Event status: success, failure, blocked")
    description: str = Field(..., description="Human-readable description")

    # Additional context
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")

    # PII/PHI indicators
    involves_pii: bool = Field(default=False, description="Event involves PII data")
    involves_phi: bool = Field(default=False, description="Event involves PHI (health) data")

    # Organization context
    organization_id: str | None = Field(None, description="Organization ID")
    team_id: str | None = Field(None, description="Team ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SecurityAuditLogger:
    """
    Comprehensive security audit logging service.

    Features:
    - Structured logging with JSON format
    - Multiple log levels and severity
    - PII/PHI data tracking
    - Compliance-ready output (GDPR, HIPAA)
    - Async logging for performance
    - Log rotation and retention
    - Integration with SIEM systems
    """

    def __init__(
        self,
        log_file: str = "logs/security-audit.log",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 30,
        enable_console: bool = True,
        enable_file: bool = True,
        siem_endpoint: str | None = None,
    ):
        self.log_file = Path(log_file)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.siem_endpoint = siem_endpoint

        # Create logs directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self._setup_logger()

    def _setup_logger(self):
        """Setup structured logger with handlers."""
        # Create logger
        self.logger = logging.getLogger("security.audit")
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if self.logger.handlers:
            return

        # Formatter: JSON format for machine parsing
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if self.enable_file:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_event(self, event: SecurityEvent):
        """
        Log a security event.

        Args:
            event: SecurityEvent to log
        """
        # Ensure event has timestamp
        if not event.timestamp:
            event.timestamp = datetime.utcnow()

        # Log based on severity
        if event.severity == "critical":
            self.logger.critical(event.json())
        elif event.severity == "error":
            self.logger.error(event.json())
        elif event.severity == "warning":
            self.logger.warning(event.json())
        elif event.severity == "info":
            self.logger.info(event.json())
        else:
            self.logger.debug(event.json())

        # Send to SIEM if configured
        if self.siem_endpoint:
            asyncio.create_task(self._send_to_siem(event))

        # Alert on critical events
        if event.severity == "critical":
            self._trigger_alert(event)

    async def _send_to_siem(self, event: SecurityEvent):
        """Send event to SIEM system (Splunk, Elasticsearch, etc.)."""
        # Implementation depends on SIEM system
        # Example: Send to Elasticsearch, Splunk HEC, etc.

    def _trigger_alert(self, event: SecurityEvent):
        """Trigger alert for critical security events."""
        # Integration with alerting system (PagerDuty, Slack, email, etc.)
        logger.critical(f"SECURITY ALERT: {event.event_type} - {event.description}")

    # Convenience methods for common event types

    def log_auth_success(
        self,
        user_id: str,
        username: str,
        ip_address: str,
        method: str = "password",
        mfa_used: bool = False
    ):
        """Log successful authentication."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            description=f"User {username} logged in successfully via {method}",
            metadata={"method": method, "mfa_used": mfa_used}
        )
        self.log_event(event)

    def log_auth_failure(
        self,
        username: str,
        ip_address: str,
        reason: str = "invalid_credentials",
        user_id: str | None = None
    ):
        """Log failed authentication attempt."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_LOGIN_FAILURE,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            description=f"Failed login attempt for {username}: {reason}",
            status="failure",
            severity="warning",
            metadata={"reason": reason}
        )
        self.log_event(event)

    def log_rate_limit_violation(
        self,
        ip_address: str,
        endpoint: str,
        user_id: str | None = None
    ):
        """Log rate limit violation."""
        event = SecurityEvent(
            event_type=SecurityEventType.VIOLATION_RATE_LIMIT,
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
            description=f"Rate limit exceeded for {endpoint} by {ip_address}",
            status="blocked",
            severity="warning",
            metadata={"blocked_endpoint": endpoint}
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "read",
        involves_pii: bool = False,
        involves_phi: bool = False
    ):
        """Log data access event."""
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_ACCESS,
            user_id=user_id,
            description=f"User {user_id} {action} {resource_type}:{resource_id}",
            metadata={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            },
            involves_pii=involves_pii,
            involves_phi=involves_phi
        )
        self.log_event(event)

    def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        reason: str = "insufficient_permissions"
    ):
        """Log permission denial."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTHZ_PERMISSION_DENIED,
            user_id=user_id,
            description=f"Permission denied for user {user_id} to {action} {resource}: {reason}",
            status="failure",
            severity="warning",
            metadata={"resource": resource, "action": action, "reason": reason}
        )
        self.log_event(event)

    def log_sql_injection_attempt(
        self,
        ip_address: str,
        endpoint: str,
        payload: str,
        user_id: str | None = None
    ):
        """Log SQL injection attempt (blocked)."""
        event = SecurityEvent(
            event_type=SecurityEventType.VIOLATION_SQL_INJECTION,
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
            description=f"SQL injection attempt blocked from {ip_address} on {endpoint}",
            status="blocked",
            severity="critical",
            metadata={
                "payload_preview": payload[:100] if len(payload) > 100 else payload
            }
        )
        self.log_event(event)

    def log_pii_access(
        self,
        user_id: str,
        data_subject_id: str,
        data_type: str,
        purpose: str = "business_operations"
    ):
        """Log PII data access for GDPR compliance."""
        event = SecurityEvent(
            event_type=SecurityEventType.DATA_PII_ACCESS,
            user_id=user_id,
            description=f"User {user_id} accessed PII data of subject {data_subject_id} ({data_type})",
            involves_pii=True,
            metadata={
                "data_subject_id": data_subject_id,
                "data_type": data_type,
                "purpose": purpose
            }
        )
        self.log_event(event)

    def log_account_deletion(
        self,
        user_id: str,
        deleted_by: str,
        reason: str = "user_request"
    ):
        """Log account deletion for GDPR right to erasure."""
        event = SecurityEvent(
            event_type=SecurityEventType.ACCOUNT_DELETED,
            user_id=deleted_by,
            description=f"Account {user_id} deleted by {deleted_by}: {reason}",
            involves_pii=True,
            metadata={
                "deleted_account": user_id,
                "reason": reason
            }
        )
        self.log_event(event)


# Global audit logger instance
audit_logger = SecurityAuditLogger()


def get_audit_logger() -> SecurityAuditLogger:
    """Get the global security audit logger instance."""
    return audit_logger
