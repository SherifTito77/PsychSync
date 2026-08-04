"""
Security Audit Logging Service

Comprehensive audit logging for:
- Authentication events (login, logout, MFA)
- Authorization decisions (access grants/denials)
- Data access (encrypted fields, cross-tenant)
- Configuration changes
- Security incidents

COMPLIANCE:
- GDPR Article 30: Records of processing activities
- HIPAA: Access logs for ePHI
- SOC 2: Monitoring and logging of system events
- NIST SP 800-53: Audit and accountability

Author: Security Team
Version: 1.0
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.db.models.user import User

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""

    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_MFA_VERIFIED = "auth.mfa.verified"
    AUTH_PASSWORD_CHANGED = "auth.password.changed"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_SESSION_CREATED = "auth.session.created"
    AUTH_SESSION_ROTATED = "auth.session.rotated"
    AUTH_SESSION_REVOKED = "auth.session.revoked"

    # Authorization events
    AUTHZ_ACCESS_GRANTED = "authz.access.granted"
    AUTHZ_ACCESS_DENIED = "authz.access.denied"
    AUTHZ_PERMISSION_CHECK = "authz.permission.check"
    AUTHZ_ROLE_ASSIGNED = "authz.role.assigned"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"

    # Data access events
    DATA_ACCESSED = "data.accessed"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_EXPORTED = "data.exported"
    DATA_ENCRYPTED = "data.encrypted"
    DATA_DECRYPTED = "data.decrypted"

    # Multi-tenancy events
    TENANT_CROSS_ACCESS = "tenant.cross_access"
    TENANT_ISOLATION_BREACH = "tenant.isolation_breach"

    # Configuration events
    CONFIG_CHANGED = "config.changed"
    CONFIG_DEPLOYED = "config.deployed"
    CONFIG_ROLLED_BACK = "config.rolled_back"

    # Security events
    SECURITY_INCIDENT = "security.incident"
    SECURITY_INVESTIGATION = "security.investigation"
    SECURITY_RESPONSE = "security.response"
    SECURITY_ALERT_TRIGGERED = "security.alert.triggered"


class AuditSeverity(Enum):
    """Severity levels for audit events"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record"""

    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: str | None
    organization_id: str | None
    ip_address: str | None
    user_agent: str | None
    resource_type: str | None
    resource_id: str | None
    action: str
    details: dict[str, Any]
    success: bool
    session_id: str | None = None
    location: str | None = None


class AuditLogger:
    """
    Comprehensive audit logging service

    Captures all security-relevant events for compliance and monitoring
    """

    def __init__(self):
        """Initialize audit logger"""
        self.audit_log: list[AuditEvent] = []
        selfRetention_days = 90  # Default retention period

        # Set up structured logging
        self._setup_audit_logger()

    def _setup_audit_logger(self):
        """Configure structured audit logger"""
        # Create audit logger handler
        # In production, would write to database or SIEM system

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        organization_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str = "",
        details: dict[str, Any] | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        session_id: str | None = None,
        location: str | None = None,
    ) -> None:
        """
        Log an audit event

        Args:
            event_type: Type of event
            user_id: User ID (if applicable)
            organization_id: Organization ID (if applicable)
            ip_address: IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            details: Additional details
            severity: Event severity
            success: Whether operation was successful
            session_id: Session ID (if applicable)
            location: Location (if available)
        """
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            organization_id=organization_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=details or {},
            success=success,
            session_id=session_id,
            location=location,
        )

        # Store in memory (in production, would write to database)
        self.audit_log.append(event)

        # Limit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]

        # Log to standard logger
        log_level = self._get_log_level(severity)
        logger.log(log_level, f"[{event_type.value}] {action}", extra=asdict(event))

    def log_authentication_event(
        self,
        event_type: AuditEventType,
        user: User | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log authentication event

        Args:
            event_type: Type of auth event
            user: User object (if authenticated)
            email: Email address (if not authenticated)
            ip_address: IP address
            user_agent: User agent
            success: Whether operation was successful
            details: Additional details
        """
        user_id = str(user.id) if user else None
        org_id = str(user.organization_id) if user and user.organization_id else None

        severity = AuditSeverity.HIGH if not success else AuditSeverity.INFO

        self.log_event(
            event_type=event_type,
            user_id=user_id,
            organization_id=org_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user",
            resource_id=user_id,
            action=f"Authentication: {event_type.value}",
            details=details or {"email": email},
            severity=severity,
            success=success,
        )

    def log_authorization_event(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str,
        permissions: list[str],
        granted: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
        denial_reason: str | None = None,
    ) -> None:
        """
        Log authorization decision

        Args:
            user: User object
            resource_type: Type of resource
            resource_id: ID of resource
            action: Action attempted
            permissions: Permissions checked
            granted: Whether access was granted
            ip_address: IP address
            user_agent: User agent
            denial_reason: Reason for denial (if denied)
        """
        event_type = (
            AuditEventType.AUTHZ_ACCESS_GRANTED
            if granted
            else AuditEventType.AUTHZ_ACCESS_DENIED
        )

        severity = AuditSeverity.MEDIUM if not granted else AuditSeverity.LOW

        details = {"permissions_checked": permissions, "action": action}

        if not granted and denial_reason:
            details["denial_reason"] = denial_reason

        self.log_event(
            event_type=event_type,
            user_id=str(user.id),
            organization_id=str(user.organization_id) if user.organization_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=f"Authorization: {action}",
            details=details,
            severity=severity,
            success=granted,
        )

    def log_data_access(
        self,
        user: User,
        resource_type: str,
        resource_id: str,
        action: str,
        fields_accessed: list[str],
        ip_address: str | None = None,
        user_agent: str | None = None,
        is_encrypted: bool = False,
    ) -> None:
        """
        Log data access event

        Args:
            user: User accessing data
            resource_type: Type of resource
            resource_id: ID of resource
            action: Action performed
            fields_accessed: Fields accessed
            ip_address: IP address
            user_agent: User agent
            is_encrypted: Whether data was encrypted
        """
        event_type = AuditEventType.DATA_ACCESSED

        details = {
            "fields_accessed": fields_accessed,
            "action": action,
            "encrypted": is_encrypted,
        }

        severity = AuditSeverity.LOW
        if is_encrypted:
            severity = AuditSeverity.MEDIUM

        self.log_event(
            event_type=event_type,
            user_id=str(user.id),
            organization_id=str(user.organization_id) if user.organization_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=f"Data access: {action}",
            details=details,
            severity=severity,
            success=True,
        )

    def log_cross_tenant_access(
        self,
        user: User,
        target_org_id: str,
        target_team_id: str | None,
        resource_type: str,
        resource_id: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log cross-tenant access attempt

        Args:
            user: User attempting access
            target_org_id: Target organization ID
            target_team_id: Target team ID (if applicable)
            resource_type: Type of resource
            resource_id: ID of resource
            ip_address: IP address
            user_agent: User agent
        """
        details = {
            "user_org_id": str(user.organization_id) if user.organization_id else None,
            "target_org_id": target_org_id,
            "target_team_id": target_team_id,
        }

        self.log_event(
            event_type=AuditEventType.TENANT_CROSS_ACCESS,
            user_id=str(user.id),
            organization_id=str(user.organization_id) if user.organization_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action="Cross-tenant access",
            details=details,
            severity=AuditSeverity.HIGH,
            success=False,
        )

    def log_security_incident(
        self,
        incident_type: str,
        severity: AuditSeverity,
        user_id: str | None,
        description: str,
        affected_resources: list[dict[str, str]],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        Log security incident

        Args:
            incident_type: Type of incident
            severity: Incident severity
            user_id: User involved (if applicable)
            description: Incident description
            affected_resources: List of affected resources
            ip_address: IP address
            user_agent: User agent
        """
        details = {
            "incident_type": incident_type,
            "description": description,
            "affected_resources": affected_resources,
        }

        self.log_event(
            event_type=AuditEventType.SECURITY_INCIDENT,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action=f"Security incident: {incident_type}",
            details=details,
            severity=severity,
            success=False,
        )

    def query_audit_log(
        self,
        user_id: str | None = None,
        organization_id: str | None = None,
        event_type: AuditEventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """
        Query audit log with filters

        Args:
            user_id: Filter by user ID
            organization_id: Filter by organization ID
            event_type: Filter by event type
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum results

        Returns:
            List of matching audit events
        """
        results = []

        for event in self.audit_log:
            # Apply filters
            if user_id and event.user_id != user_id:
                continue
            if organization_id and event.organization_id != organization_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue

            results.append(event)

            if len(results) >= limit:
                break

        return results

    def get_security_summary(
        self, start_time: datetime, end_time: datetime
    ) -> dict[str, Any]:
        """
        Generate security summary for a time period

        Args:
            start_time: Start of period
            end_time: End of period

        Returns:
            Dictionary with security metrics
        """
        events_in_period = [
            e for e in self.audit_log if start_time <= e.timestamp <= end_time
        ]

        # Count by event type
        event_counts = {}
        failed_logins = 0
        cross_tenant_attempts = 0
        access_denials = 0

        for event in events_in_period:
            et = event.event_type.value
            event_counts[et] = event_counts.get(et, 0) + 1

            if et == AuditEventType.AUTH_LOGIN_FAILED.value:
                failed_logins += 1
            elif et == AuditEventType.TENANT_CROSS_ACCESS.value:
                cross_tenant_attempts += 1
            elif et == AuditEventType.AUTHZ_ACCESS_DENIED.value:
                access_denials += 1

        return {
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "total_events": len(events_in_period),
            "failed_logins": failed_logins,
            "cross_tenant_attempts": cross_tenant_attempts,
            "access_denials": access_denials,
            "event_breakdown": event_counts,
        }

    def _get_log_level(self, severity: AuditSeverity) -> int:
        """Convert severity to logging level"""
        severity_map = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }
        return severity_map.get(severity, logging.INFO)

    def export_audit_log(
        self, start_time: datetime, end_time: datetime, format: str = "json"
    ) -> str:
        """
        Export audit log for compliance reporting

        Args:
            start_time: Start of period
            end_time: End of period
            format: Export format (json or csv)

        Returns:
            Exported data as string
        """
        events = self.query_audit_log(
            start_time=start_time,
            end_time=end_time,
            limit=100000,  # Large limit for export
        )

        if format == "json":
            return json.dumps([asdict(e) for e in events], indent=2)
        if format == "csv":
            # Simple CSV export
            lines = [
                "timestamp,event_type,severity,user_id,organization_id,"
                "resource_type,resource_id,action,success"
            ]
            for e in events:
                lines.append(
                    f"{e.timestamp.isoformat()},{e.event_type.value},"
                    f"{e.severity.value},{e.user_id},{e.organization_id},"
                    f"{e.resource_type},{e.resource_id},{e.action},{e.success}"
                )
            return "\n".join(lines)
        raise ValueError(f"Unsupported export format: {format}")


# Singleton instance
audit_logger = AuditLogger()
