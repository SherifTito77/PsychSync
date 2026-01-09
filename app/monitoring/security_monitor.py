"""
Security Monitoring Service
Real-time security event monitoring and alerting

Author: Security Team
Version: 1.0.0
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger("app.security.monitoring")


class SeverityLevel(Enum):
    """Security event severity levels"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""

    timestamp: datetime
    event_type: str
    severity: SeverityLevel
    source_ip: str
    user_agent: str
    path: str
    method: str
    details: dict[str, Any]
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["severity"] = self.severity.value
        return data


class SecurityMonitor:
    """
    Real-time security monitoring system

    Features:
    - Event collection and storage
    - Pattern detection
    - Rate limiting enforcement
    - Alert generation
    - Metrics reporting
    """

    def __init__(self, retention_hours: int = 24, alert_thresholds: dict[str, int] = None):
        self.retention_hours = retention_hours
        self.events: deque = deque(maxlen=10000)  # Circular buffer
        self.event_counts: dict[str, int] = defaultdict(int)
        self.ip_event_counts: dict[str, int] = defaultdict(int)
        self.alert_thresholds = alert_thresholds or {
            "critical": 1,
            "high": 5,
            "medium": 20,
            "low": 50,
        }
        self.alert_cooldown: dict[str, datetime] = {}
        self.cooldown_period = timedelta(minutes=5)

        # Alert callbacks
        self.alert_callbacks: list[callable] = []

        logger.info(
            "Security monitor initialized",
            extra={"retention_hours": retention_hours, "alert_thresholds": self.alert_thresholds},
        )

    def add_alert_callback(self, callback: callable) -> None:
        """Register an alert callback function"""
        self.alert_callbacks.append(callback)

    def record_event(self, event: SecurityEvent) -> None:
        """
        Record a security event

        Args:
            event: SecurityEvent to record
        """
        # Add to events
        self.events.append(event)

        # Update counts
        event_key = f"{event.event_type}:{event.severity.value}"
        self.event_counts[event_key] += 1
        self.ip_event_counts[event.source_ip] += 1

        # Check for patterns and generate alerts
        asyncio.create_task(self._check_patterns(event))

        # Log significant events
        if event.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            logger.critical(
                f"Security event: {event.event_type}",
                extra={
                    "event_type": event.event_type,
                    "severity": event.severity.value,
                    "source_ip": event.source_ip,
                    "path": event.path,
                    "details": event.details,
                },
            )

    async def _check_patterns(self, event: SecurityEvent) -> None:
        """Check event for attack patterns"""
        await self._check_rate_thresholds(event)
        await self._check_repeated_patterns(event)
        await self._check_distributed_patterns(event)

    async def _check_rate_thresholds(self, event: SecurityEvent) -> None:
        """Check if event rate exceeds thresholds"""
        severity = event.severity.value
        threshold = self.alert_thresholds.get(severity, 100)
        event_key = f"{event.event_type}:{severity}"

        if self.event_counts[event_key] >= threshold:
            await self._generate_alert(
                "rate_threshold_exceeded",
                event,
                {
                    "threshold": threshold,
                    "actual_count": self.event_counts[event_key],
                    "event_type": event.event_type,
                    "severity": severity,
                },
            )

    async def _check_repeated_patterns(self, event: SecurityEvent) -> None:
        """Check for repeated events from same source"""
        ip_count = self.ip_event_counts[event.source_ip]

        # More than 100 events from same IP
        if ip_count > 100:
            await self._generate_alert(
                "repeated_violations",
                event,
                {"source_ip": event.source_ip, "event_count": ip_count, "time_window": "last hour"},
            )

    async def _check_distributed_patterns(self, event: SecurityEvent) -> None:
        """Check for distributed attack patterns"""
        # Count unique IPs with similar events in last hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_events = [
            e for e in self.events if e.timestamp > cutoff and e.event_type == event.event_type
        ]
        unique_ips = set(e.source_ip for e in recent_events)

        # More than 50 unique IPs with same event type
        if len(unique_ips) > 50 and len(recent_events) > 200:
            await self._generate_alert(
                "distributed_attack",
                event,
                {
                    "event_type": event.event_type,
                    "unique_ips": len(unique_ips),
                    "total_events": len(recent_events),
                },
            )

    async def _generate_alert(
        self, alert_type: str, event: SecurityEvent, metadata: dict[str, Any]
    ) -> None:
        """Generate security alert"""
        # Check cooldown
        alert_key = f"{alert_type}:{event.source_ip}"
        last_alert = self.alert_cooldown.get(alert_key)

        if last_alert and (datetime.utcnow() - last_alert) < self.cooldown_period:
            return  # In cooldown period

        # Record alert time
        self.alert_cooldown[alert_key] = datetime.utcnow()

        # Create alert
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_type": alert_type,
            "severity": event.severity.value,
            "source_event": event.to_dict(),
            "metadata": metadata,
        }

        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"Security alert generated: {alert_type}", extra=alert)

    def get_events(
        self,
        event_type: str | None = None,
        severity: SeverityLevel | None = None,
        source_ip: str | None = None,
        hours_back: int = 1,
    ) -> list[SecurityEvent]:
        """
        Query events with filters

        Args:
            event_type: Filter by event type
            severity: Filter by severity level
            source_ip: Filter by source IP
            hours_back: Number of hours to look back

        Returns:
            List of matching SecurityEvents
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)

        filtered = [
            e
            for e in self.events
            if e.timestamp > cutoff
            and (event_type is None or e.event_type == event_type)
            and (severity is None or e.severity == severity)
            and (source_ip is None or e.source_ip == source_ip)
        ]

        return filtered

    def get_summary(self, hours_back: int = 24) -> dict[str, Any]:
        """
        Get security event summary

        Args:
            hours_back: Number of hours to summarize

        Returns:
            Summary statistics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        recent_events = [e for e in self.events if e.timestamp > cutoff]

        # Count by severity
        severity_counts = defaultdict(int)
        for event in recent_events:
            severity_counts[event.severity.value] += 1

        # Count by type
        type_counts = defaultdict(int)
        for event in recent_events:
            type_counts[event.event_type] += 1

        # Top offender IPs
        ip_counts = defaultdict(int)
        for event in recent_events:
            if event.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                ip_counts[event.source_ip] += 1

        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "period_hours": hours_back,
            "total_events": len(recent_events),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "top_offender_ips": top_ips,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def cleanup_old_events(self) -> None:
        """Remove events older than retention period"""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)

        while self.events and self.events[0].timestamp < cutoff:
            old_event = self.events.popleft()

            # Decrement counts
            event_key = f"{old_event.event_type}:{old_event.severity.value}"
            if event_key in self.event_counts:
                self.event_counts[event_key] -= 1

        logger.debug(f"Cleaned up old events, remaining: {len(self.events)}")


# Singleton instance
security_monitor = SecurityMonitor()


# Convenience functions
def record_security_event(
    event_type: str,
    severity: SeverityLevel,
    source_ip: str,
    user_agent: str,
    path: str,
    method: str,
    details: dict[str, Any],
) -> None:
    """Record a security event"""
    event = SecurityEvent(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        severity=severity,
        source_ip=source_ip,
        user_agent=user_agent,
        path=path,
        method=method,
        details=details,
    )
    security_monitor.record_event(event)


def get_security_summary(hours_back: int = 24) -> dict[str, Any]:
    """Get security event summary"""
    return security_monitor.get_summary(hours_back)


# Event types
class SecurityEventTypes:
    """Standard security event types"""

    # Authentication events
    AUTH_FAILURE = "auth_failure"
    AUTH_SUCCESS = "auth_success"
    SUSPICIOUS_LOGIN = "suspicious_login"
    BRUTE_FORCE_DETECTED = "brute_force_detected"

    # Network events
    HOST_HEADER_INVALID = "host_header_invalid"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_REQUEST = "suspicious_request"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"

    # Application events
    PERMISSION_DENIED = "permission_denied"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    DATA_ACCESS_ATTEMPT = "data_access_attempt"

    # DoS events
    DOS_ATTACK_DETECTED = "dos_attack_detected"
    FLOODING_DETECTED = "flooding_detected"
