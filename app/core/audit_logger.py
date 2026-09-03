# app/core/audit_logger.py
"""
Comprehensive audit logging system for security monitoring
Tracks all critical security events with structured logging
"""

import hashlib
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """Security event types for categorization"""

    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    PASSWORD_RESET = "password_reset"
    USER_REGISTRATION = "user_registration"
    USER_REGISTRATION_FAILED = "user_registration_failed"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_INPUT = "invalid_input"
    INJECTION_ATTEMPT = "injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SESSION_MANAGEMENT = "session_management"
    API_ABUSE = "api_abuse"
    MALICIOUS_REQUEST = "malicious_request"
    SYSTEM_ERROR = "system_error"


class AuditLogger:
    """Enterprise-grade audit logging system"""

    def __init__(self):
        self.security_logger = self._setup_security_logger()
        self.sensitive_fields = {
            "password",
            "password_hash",
            "token",
            "secret",
            "key",
            "credit_card",
            "ssn",
            "social_security",
            "bank_account",
            "api_key",
            "auth_token",
        }

    def _setup_security_logger(self) -> logging.Logger:
        """Setup dedicated security logger with appropriate formatting"""
        security_logger = logging.getLogger("security_audit")

        # Prevent duplicate handlers
        if not security_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            security_logger.addHandler(handler)
            security_logger.setLevel(logging.INFO)

        return security_logger

    @classmethod
    def log_security_event(
        cls,
        user_id: str | UUID | None = None,
        event_type: str | SecurityEventType | None = None,
        details: str | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
        session_id: str | None = None,
        organization_id: str | UUID | None = None,
        additional_data: dict[str, Any] | None = None,
        risk_score: int | None = None,
        severity: str | None = "medium",
    ) -> None:
        """
        Log a security event with comprehensive context

        Args:
            user_id: ID of the user involved (if applicable)
            event_type: Type of security event
            details: Human-readable description of the event
            client_ip: Client IP address
            user_agent: User agent string
            endpoint: API endpoint or URL
            method: HTTP method
            status_code: HTTP status code
            request_id: Unique request identifier
            session_id: Session identifier
            organization_id: Organization ID
            additional_data: Additional context data
            risk_score: Risk score (0-100)
            severity: Event severity (low, medium, high, critical)
        """
        try:
            # Create audit logger instance
            audit_logger = cls()

            # Sanitize and structure the event data
            event_data = audit_logger._sanitize_event_data(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_id": audit_logger._generate_event_id(),
                    "user_id": str(user_id) if user_id else None,
                    "event_type": (
                        event_type.value
                        if isinstance(event_type, SecurityEventType)
                        else event_type
                    ),
                    "details": details or "Security event occurred",
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "request_id": request_id,
                    "session_id": session_id,
                    "organization_id": (
                        str(organization_id) if organization_id else None
                    ),
                    "additional_data": audit_logger._sanitize_additional_data(
                        additional_data or {}
                    ),
                    "risk_score": risk_score,
                    "severity": severity,
                    "server_time": time.time(),
                }
            )

            # Calculate risk score if not provided
            if risk_score is None:
                event_data["risk_score"] = audit_logger._calculate_risk_score(
                    event_data
                )

            # Determine log level based on severity and risk score
            log_level = audit_logger._determine_log_level(
                event_data["risk_score"], severity
            )

            # Log the event
            audit_logger._log_event(event_data, log_level)

            # Check if immediate action is needed
            if event_data["risk_score"] >= 80:
                audit_logger._trigger_security_alert(event_data)

        except Exception as e:
            # Don't let audit logging failures break the application
            logger.error(f"Audit logging failed: {e!s}")
            # Try to log the failure itself
            try:
                logger.error(
                    f"Security audit failure: {event_type if event_type else 'unknown'} - {details if details else 'no details'}"
                )
            except Exception:
                import sys

                print(  # last-resort stderr output when all loggers fail
                    f"CRITICAL: audit logging completely failed for event={event_type}",
                    file=sys.stderr,
                )

    def _sanitize_event_data(self, event_data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize event data to remove sensitive information"""
        sanitized = {}

        for key, value in event_data.items():
            if key in self.sensitive_fields:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_additional_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_string(str(item)) for item in value]
            else:
                sanitized[key] = (
                    self._sanitize_string(str(value)) if value is not None else None
                )

        return sanitized

    def _sanitize_additional_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize additional data dictionary"""
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_additional_data(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [
                    str(item)[:100] + "..." if len(str(item)) > 100 else str(item)
                    for item in value
                ]
            else:
                sanitized[key] = (
                    str(value)[:500] + "..."
                    if value and len(str(value)) > 500
                    else value
                )
        return sanitized

    def _sanitize_string(self, text: str) -> str:
        """Sanitize string to prevent log injection"""
        if not text:
            return text

        # Remove potential log injection characters
        dangerous_chars = ["\n", "\r", "\t", "\\x00"]
        sanitized = text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."

        return sanitized

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{time.time()}".encode()
        ).hexdigest()[:16]

    def _calculate_risk_score(self, event_data: dict[str, Any]) -> int:
        """Calculate risk score based on event characteristics"""
        base_score = 0

        # Event type risk scoring
        high_risk_events = {
            "injection_attempt",
            "xss_attempt",
            "privilege_escalation",
            "unauthorized_access",
            "malicious_request",
            "suspicious_activity",
        }
        medium_risk_events = {
            "authentication_failure",
            "authorization_failure",
            "rate_limit_exceeded",
            "api_abuse",
            "data_export",
        }

        event_type = event_data.get("event_type", "").lower()
        if any(risk_event in event_type for risk_event in high_risk_events):
            base_score += 60
        elif any(risk_event in event_type for risk_event in medium_risk_events):
            base_score += 30
        else:
            base_score += 10

        # Status code scoring
        status_code = event_data.get("status_code")
        if status_code:
            if status_code >= 500:
                base_score += 20
            elif status_code >= 400:
                base_score += 15

        # Failed authentication scoring
        if "authentication_failure" in event_type:
            base_score += 25

        # Suspicious patterns
        details = event_data.get("details", "").lower()
        suspicious_patterns = [
            "sql",
            "injection",
            "xss",
            "script",
            "alert",
            "malicious",
            "attack",
        ]
        if any(pattern in details for pattern in suspicious_patterns):
            base_score += 40

        # Client IP reputation (placeholder - would integrate with threat intelligence)
        client_ip = event_data.get("client_ip", "")
        if client_ip and self._is_suspicious_ip(client_ip):
            base_score += 30

        return min(100, base_score)

    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious (placeholder implementation)"""
        # This would integrate with threat intelligence feeds
        suspicious_ranges = ["10.0.0.", "192.168.", "172.16."]  # Example only
        return any(ip.startswith(range_) for range_ in suspicious_ranges)

    def _determine_log_level(self, risk_score: int, severity: str) -> int:
        """Determine appropriate log level based on risk and severity"""
        if risk_score >= 80 or severity == "critical":
            return logging.CRITICAL
        if risk_score >= 60 or severity == "high":
            return logging.ERROR
        if risk_score >= 40 or severity == "medium":
            return logging.WARNING
        return logging.INFO

    def _log_event(self, event_data: dict[str, Any], log_level: int) -> None:
        """Log the security event with appropriate level"""
        log_message = self._format_log_message(event_data)

        if log_level >= logging.CRITICAL:
            self.security_logger.critical(log_message)
        elif log_level >= logging.ERROR:
            self.security_logger.error(log_message)
        elif log_level >= logging.WARNING:
            self.security_logger.warning(log_message)
        else:
            self.security_logger.info(log_message)

    def _format_log_message(self, event_data: dict[str, Any]) -> str:
        """Format log message for readability"""
        parts = [
            f"EVENT: {event_data.get('event_type', 'unknown')}",
            f"USER: {event_data.get('user_id', 'anonymous')}",
            f"IP: {event_data.get('client_ip', 'unknown')}",
            f"RISK: {event_data.get('risk_score', 0)}/100",
            f"SEVERITY: {event_data.get('severity', 'unknown')}",
        ]

        if event_data.get("details"):
            parts.append(f"DETAILS: {event_data['details']}")

        if event_data.get("endpoint"):
            parts.append(
                f"ENDPOINT: {event_data['endpoint']} {event_data.get('method', '')}"
            )

        return " | ".join(parts)

    def _trigger_security_alert(self, event_data: dict[str, Any]) -> None:
        """Trigger immediate security alert for high-risk events"""
        try:
            # This would integrate with alerting systems (PagerDuty, Slack, etc.)
            alert_message = f"🚨 HIGH RISK SECURITY EVENT: {event_data.get('event_type')} (Risk: {event_data.get('risk_score')})"

            # Log critical alert
            self.security_logger.critical(alert_message)

            # Placeholder for external alert integration
            # await send_security_alert(event_data)

        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e!s}")


# Convenience functions for common events
def log_auth_success(user_id: str | UUID, client_ip: str, **kwargs):
    """Log successful authentication"""
    AuditLogger.log_security_event(
        user_id=user_id,
        event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
        client_ip=client_ip,
        risk_score=0,
        severity="low",
        **kwargs,
    )


def log_auth_failure(user_id: str | UUID | None, reason: str, client_ip: str, **kwargs):
    """Log failed authentication"""
    AuditLogger.log_security_event(
        user_id=user_id,
        event_type=SecurityEventType.AUTHENTICATION_FAILURE,
        details=f"Authentication failed: {reason}",
        client_ip=client_ip,
        risk_score=40,
        severity="medium",
        **kwargs,
    )


def log_data_access(user_id: str | UUID, resource: str, action: str, **kwargs):
    """Log data access event"""
    AuditLogger.log_security_event(
        user_id=user_id,
        event_type=SecurityEventType.DATA_ACCESS,
        details=f"User accessed {resource} with action {action}",
        risk_score=10,
        severity="low",
        **kwargs,
    )


def log_suspicious_activity(
    details: str, client_ip: str, risk_score: int = 70, **kwargs
):
    """Log suspicious activity"""
    AuditLogger.log_security_event(
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        details=details,
        client_ip=client_ip,
        risk_score=risk_score,
        severity="high",
        **kwargs,
    )


def log_injection_attempt(
    user_id: str | UUID | None, injection_type: str, client_ip: str, **kwargs
):
    """Log injection attempt"""
    AuditLogger.log_security_event(
        user_id=user_id,
        event_type=SecurityEventType.INJECTION_ATTEMPT,
        details=f"{injection_type} injection attempt detected",
        client_ip=client_ip,
        risk_score=90,
        severity="critical",
        **kwargs,
    )


# Global instance for easy access
audit_logger = AuditLogger()
