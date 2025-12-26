"""
AI Security Monitoring and SOC Integration

Provides comprehensive security monitoring, alerting, and SOC (Security
Operations Center) workflow integration for AI/ML systems.

Features:
- Real-time security event tracking
- Anomaly detection in AI behavior
- Automated alerting for suspicious activities
- SOC integration workflow
- Audit trail generation

Author: Security Team
Version: 1.0
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger("app.ai.security.monitoring")


class SecurityEventSeverity(Enum):
    """Security event severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(Enum):
    """Types of security events"""
    # Input validation events
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    MALICIOUS_INPUT_DETECTED = "malicious_input_detected"
    PII_DETECTED = "pii_detected"
    INPUT_VALIDATION_FAILED = "input_validation_failed"

    # Output validation events
    DANGEROUS_OUTPUT_DETECTED = "dangerous_output_detected"
    SECRET_LEAK_DETECTED = "secret_leak_detected"
    OUTPUT_BLOCKED = "output_blocked"

    # Behavioral events
    UNUSUAL_REQUEST_PATTERN = "unusual_request_pattern"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Model events
    MODEL_ANOMALY_DETECTED = "model_anomaly_detected"
    PREDICTION_CONFIDENCE_LOW = "prediction_confidence_low"
    MODEL_ERROR = "model_error"


@dataclass
class SecurityEvent:
    """AI Security Event"""
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "details": self.details,
            "metadata": self.metadata,
            "resolved": self.resolved
        }


class AISecurityMonitor:
    """
    AI Security Monitoring and SOC Integration

    Tracks security events, detects anomalies, and integrates with SOC workflows.
    """

    def __init__(self):
        """Initialize the security monitor"""
        self.events: List[SecurityEvent] = []
        self.alert_thresholds = {
            SecurityEventSeverity.CRITICAL: 1,  # Immediate alert
            SecurityEventSeverity.HIGH: 3,     # Alert after 3 in 1 hour
            SecurityEventSeverity.MEDIUM: 10,  # Alert after 10 in 1 hour
        }

    def log_event(
        self,
        event_type: SecurityEventType,
        severity: SecurityEventSeverity,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """
        Log a security event

        Args:
            event_type: Type of security event
            severity: Severity level
            details: Event details
            user_id: User ID (if available)
            session_id: Session ID (if available)
            ip_address: IP address (if available)
            metadata: Additional metadata

        Returns:
            SecurityEvent object
        """
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
            metadata=metadata or {}
        )

        # Store event
        self.events.append(event)

        # Log the event
        self._log_security_event(event)

        # Check if we need to trigger an alert
        self._check_alert_thresholds(event)

        return event

    def _log_security_event(self, event: SecurityEvent) -> None:
        """Log security event to appropriate logger"""
        log_level = {
            SecurityEventSeverity.CRITICAL: logger.critical,
            SecurityEventSeverity.HIGH: logger.error,
            SecurityEventSeverity.MEDIUM: logger.warning,
            SecurityEventSeverity.LOW: logger.info,
            SecurityEventSeverity.INFO: logger.info,
        }.get(event.severity, logger.info)

        log_level(
            f"AI Security Event: {event.event_type.value}",
            extra={
                "event_type": event.event_type.value,
                "severity": event.severity.value,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "ip_address": event.ip_address,
                "details": event.details,
                "event_data": event.to_dict(),
                "security_event": True
            }
        )

    def _check_alert_thresholds(self, new_event: SecurityEvent) -> None:
        """
        Check if alert thresholds are exceeded

        Triggers SOC alert if threshold exceeded for given severity
        """
        # Get events from the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_events = [
            e for e in self.events
            if e.timestamp > one_hour_ago
            and e.severity == new_event.severity
            and not e.resolved
        ]

        threshold = self.alert_thresholds.get(new_event.severity, 100)

        if len(recent_events) >= threshold:
            # Trigger SOC alert
            self._trigger_soc_alert(new_event.severity, recent_events)

    def _trigger_soc_alert(
        self,
        severity: SecurityEventSeverity,
        events: List[SecurityEvent]
    ) -> None:
        """
        Trigger SOC alert for security events

        Args:
            severity: Severity level that triggered the alert
            events: List of events that caused the alert
        """
        alert_data = {
            "alert_type": "AI_SECURITY_THRESHOLD_EXCEEDED",
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "event_count": len(events),
            "events": [e.to_dict() for e in events[-10:]],  # Last 10 events
            "recommended_actions": self._get_recommendations(severity, events)
        }

        # Log the alert
        logger.critical(
            f"SOC ALERT: {severity.value.upper()} - AI security threshold exceeded",
            extra={
                "soc_alert": True,
                "alert_data": alert_data,
                "event_type": "soc_alert_triggered"
            }
        )

        # In production, this would integrate with your SOC system
        # Examples: Splunk, SIEM, PagerDuty, Slack, etc.

    def _get_recommendations(
        self,
        severity: SecurityEventSeverity,
        events: List[SecurityEvent]
    ) -> List[str]:
        """Get recommended actions for SOC team"""
        recommendations = []

        event_types = set(e.event_type for e in events)

        if SecurityEventType.PROMPT_INJECTION_DETECTED in event_types:
            recommendations.extend([
                "Review recent AI prompts for injection patterns",
                "Consider implementing additional prompt validation",
                "Monitor affected user accounts",
                "Review AI model outputs for potential compromise"
            ])

        if SecurityEventType.PII_DETECTED in event_types:
            recommendations.extend([
                "Review data handling procedures",
                "Ensure PII redaction is working correctly",
                "Audit recent AI processing for data leakage",
                "Review user consent and data retention policies"
            ])

        if SecurityEventType.RATE_LIMIT_EXCEEDED in event_types:
            recommendations.extend([
                "Consider temporarily blocking offending IPs/users",
                "Review rate limiting thresholds",
                "Check for automated attack patterns",
                "Consider implementing CAPTCHA"
            ])

        if SecurityEventType.MODEL_ANOMALY_DETECTED in event_types:
            recommendations.extend([
                "Review AI model performance metrics",
                "Check for model drift or data poisoning",
                "Review recent training data",
                "Consider rolling back model if necessary"
            ])

        # Add general recommendations based on severity
        if severity == SecurityEventSeverity.CRITICAL:
            recommendations.insert(0, "IMMEDIATE ACTION REQUIRED")
            recommendations.insert(1, "Escalate to security team lead")

        return recommendations

    def get_security_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get security event summary for specified time period

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with security summary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        relevant_events = [e for e in self.events if e.timestamp > cutoff]

        # Count by severity
        severity_counts = {}
        for event in relevant_events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by type
        type_counts = {}
        for event in relevant_events:
            event_type = event.event_type.value
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

        # Calculate risk score
        risk_score = self._calculate_risk_score(relevant_events)

        return {
            "time_period_hours": hours,
            "total_events": len(relevant_events),
            "events_by_severity": severity_counts,
            "events_by_type": type_counts,
            "risk_score": risk_score,
            "unresolved_events": sum(1 for e in relevant_events if not e.resolved),
            "top_users": self._get_top_users(relevant_events),
            "top_ips": self._get_top_ips(relevant_events)
        }

    def _calculate_risk_score(self, events: List[SecurityEvent]) -> float:
        """Calculate overall risk score from events"""
        if not events:
            return 0.0

        # Weight events by severity
        weights = {
            SecurityEventSeverity.CRITICAL: 10.0,
            SecurityEventSeverity.HIGH: 5.0,
            SecurityEventSeverity.MEDIUM: 2.0,
            SecurityEventSeverity.LOW: 0.5,
            SecurityEventSeverity.INFO: 0.1,
        }

        total_score = sum(
            weights.get(e.severity, 1.0)
            for e in events
        )

        # Normalize to 0-100 range
        normalized = min(total_score / len(events) * 10, 100.0)

        return round(normalized, 2)

    def _get_top_users(self, events: List[SecurityEvent], limit: int = 5) -> List[Dict]:
        """Get users with most security events"""
        user_counts = {}
        for event in events:
            if event.user_id:
                user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1

        sorted_users = sorted(
            user_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"user_id": user, "event_count": count}
            for user, count in sorted_users
        ]

    def _get_top_ips(self, events: List[SecurityEvent], limit: int = 5) -> List[Dict]:
        """Get IPs with most security events"""
        ip_counts = {}
        for event in events:
            if event.ip_address:
                ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1

        sorted_ips = sorted(
            ip_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        return [
            {"ip_address": ip, "event_count": count}
            for ip, count in sorted_ips
        ]

    def export_audit_trail(
        self,
        hours: int = 24,
        format: str = "json"
    ) -> str:
        """
        Export audit trail for specified time period

        Args:
            hours: Number of hours to look back
            format: Export format ('json' or 'csv')

        Returns:
            Serialized audit trail
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        relevant_events = [e for e in self.events if e.timestamp > cutoff]

        if format == "json":
            return json.dumps(
                [e.to_dict() for e in relevant_events],
                indent=2
            )
        elif format == "csv":
            # Simple CSV format
            lines = [
                "timestamp,event_type,severity,user_id,session_id,ip_address"
            ]
            for event in relevant_events:
                lines.append(
                    f"{event.timestamp.isoformat()},"
                    f"{event.event_type.value},"
                    f"{event.severity.value},"
                    f"{event.user_id or ''},"
                    f"{event.session_id or ''},"
                    f"{event.ip_address or ''}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_old_events(self, hours: int = 168) -> int:
        """
        Clear events older than specified hours

        Args:
            hours: Number of hours after which to clear events (default 7 days)

        Returns:
            Number of events cleared
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        old_count = len(self.events)

        self.events = [e for e in self.events if e.timestamp > cutoff]

        cleared_count = old_count - len(self.events)

        if cleared_count > 0:
            logger.info(
                f"Cleared {cleared_count} old security events",
                extra={"event_type": "old_events_cleared"}
            )

        return cleared_count


# Global monitor instance
ai_security_monitor = AISecurityMonitor()


def log_ai_security_event(
    event_type: SecurityEventType,
    severity: SecurityEventSeverity,
    details: Dict[str, Any],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> SecurityEvent:
    """
    Convenience function to log AI security event

    Usage:
        from ai.security.ai_security_monitor import (
            log_ai_security_event,
            SecurityEventType,
            SecurityEventSeverity
        )

        log_ai_security_event(
            event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
            severity=SecurityEventSeverity.HIGH,
            details={"pattern": "ignore previous instructions"},
            user_id=user.id,
            ip_address=request.client.host
        )
    """
    return ai_security_monitor.log_event(
        event_type=event_type,
        severity=severity,
        details=details,
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        metadata=metadata
    )


def get_security_summary(hours: int = 24) -> Dict[str, Any]:
    """
    Get security event summary

    Usage:
        summary = get_security_summary(hours=24)
        print(f"Risk Score: {summary['risk_score']}")
        print(f"Total Events: {summary['total_events']}")
    """
    return ai_security_monitor.get_security_summary(hours)
