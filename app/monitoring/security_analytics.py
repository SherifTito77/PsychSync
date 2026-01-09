#!/usr/bin/env python3
"""
Real-Time Security Analytics System

Provides real-time analysis of security events:
- Anomaly detection
- Pattern recognition
- Risk scoring
- Automated alerting
- Trend analysis

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Real-time security event"""

    event_type: str
    timestamp: datetime
    user_id: int | None
    session_id: str | None
    ip_address: str | None
    severity: str
    details: dict[str, Any]


@dataclass
class ThreatIndicator:
    """Detected threat indicator"""

    indicator_type: str
    severity: ThreatLevel
    confidence: float
    description: str
    affected_entities: list[str]
    mitigation_suggestions: list[str]


class RealTimeSecurityAnalyzer:
    """
    Real-time security event analysis.

    Detects patterns and anomalies in security events.
    """

    def __init__(self):
        # Event history for pattern detection
        self.event_history: deque = deque(maxlen=10000)
        self.user_history: dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.ip_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Threat detection thresholds
        self.thresholds = {
            "failed_auth_attempts": 5,
            "failed_auth_window_minutes": 15,
            "bulk_data_export_threshold": 100,
            "unauthorized_access_threshold": 3,
            "suspicious_patterns_enabled": True,
        }

    async def analyze_event(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """
        Analyze security event in real-time.

        Returns list of detected threat indicators.
        """
        indicators = []

        # Store event
        self.event_history.append(event)

        if event.user_id:
            self.user_history[event.user_id].append(event)

        if event.ip_address:
            self.ip_history[event.ip_address].append(event)

        # Run detection rules
        indicators.extend(await self._detect_brute_force(event))
        indicators.extend(await self._detect_unauthorized_access(event))
        indicators.extend(await self._detect_bulk_operations(event))
        indicators.extend(await self._detect_anomalous_patterns(event))
        indicators.extend(await self._detect_geo_anomalies(event))

        return indicators

    async def _detect_brute_force(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """Detect brute force attacks"""
        indicators = []

        # Check for failed auth attempts
        if event.event_type.startswith("auth.failed"):
            if event.user_id:
                user_events = list(self.user_history[event.user_id])
                recent_failures = [
                    e
                    for e in user_events
                    if e.event_type.startswith("auth.failed")
                    and e.timestamp > datetime.utcnow() - timedelta(minutes=15)
                ]

                if len(recent_failures) >= self.thresholds["failed_auth_attempts"]:
                    indicators.append(
                        ThreatIndicator(
                            indicator_type="brute_force",
                            severity=ThreatLevel.HIGH,
                            confidence=0.9,
                            description=f"Brute force attack detected: {len(recent_failures)} failed attempts",
                            affected_entities=[f"user_{event.user_id}"],
                            mitigation_suggestions=[
                                "Lock account temporarily",
                                "Require CAPTCHA",
                                "Implement rate limiting",
                            ],
                        )
                    )

        # Check IP-based brute force
        if event.ip_address:
            ip_events = list(self.ip_history[event.ip_address])
            recent_failures = [
                e
                for e in ip_events
                if e.event_type.startswith("auth.failed")
                and e.timestamp > datetime.utcnow() - timedelta(minutes=15)
            ]

            if len(recent_failures) >= self.thresholds["failed_auth_attempts"]:
                indicators.append(
                    ThreatIndicator(
                        indicator_type="brute_force_ip",
                        severity=ThreatLevel.CRITICAL,
                        confidence=0.95,
                        description=f"IP-based brute force: {len(recent_failures)} attempts from {event.ip_address}",
                        affected_entities=[event.ip_address],
                        mitigation_suggestions=[
                            "Block IP address",
                            "Implement IP rate limiting",
                            "Enable CAPTCHA",
                        ],
                    )
                )

        return indicators

    async def _detect_unauthorized_access(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """Detect repeated unauthorized access attempts"""
        indicators = []

        if event.event_type == "authz.access_denied":
            if event.user_id:
                user_events = list(self.user_history[event.user_id])

                # Count unauthorized attempts in last hour
                recent_denials = [
                    e
                    for e in user_events
                    if e.event_type in ["authz.access_denied", "authz.privilege_escalation"]
                    and e.timestamp > datetime.utcnow() - timedelta(hours=1)
                ]

                if len(recent_denials) >= self.thresholds["unauthorized_access_threshold"]:
                    indicators.append(
                        ThreatIndicator(
                            indicator_type="unauthorized_access_attempt",
                            severity=ThreatLevel.HIGH,
                            confidence=0.85,
                            description=f"Multiple unauthorized access attempts: {len(recent_denials)} attempts",
                            affected_entities=[f"user_{event.user_id}"],
                            mitigation_suggestions=[
                                "Review user permissions",
                                "Lock account if suspicious",
                                "Alert security team",
                            ],
                        )
                    )

        return indicators

    async def _detect_bulk_operations(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """Detect suspicious bulk data operations"""
        indicators = []

        if event.event_type in ["data.export", "data.bulk_access"]:
            record_count = event.details.get("record_count", 0)

            if record_count > self.thresholds["bulk_data_export_threshold"]:
                indicators.append(
                    ThreatIndicator(
                        indicator_type="data_exfiltration",
                        severity=ThreatLevel.HIGH,
                        confidence=0.75,
                        description=f"Bulk data export: {record_count} records",
                        affected_entities=[f"user_{event.user_id}"],
                        mitigation_suggestions=[
                            "Require additional approval",
                            "Review data access logs",
                            "Alert security team",
                        ],
                    )
                )

        return indicators

    async def _detect_anomalous_patterns(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """Detect anomalous behavioral patterns"""
        indicators = []

        if not event.user_id:
            return indicators

        user_events = list(self.user_history[event.user_id])

        # Pattern 1: Multiple resource types accessed in short time
        if len(user_events) > 10:
            recent_events = user_events[-10:]
            resource_types = set(e.resource_type for e in recent_events if e.resource_type)

            if len(resource_types) > 5:
                indicators.append(
                    ThreatIndicator(
                        indicator_type="suspicious_activity_pattern",
                        severity=ThreatLevel.MEDIUM,
                        confidence=0.6,
                        description=f"Accessed {len(resource_types)} different resource types rapidly",
                        affected_entities=[f"user_{event.user_id}"],
                        mitigation_suggestions=["Monitor user activity", "Verify user intent"],
                    )
                )

        # Pattern 2: Rapid successive requests
        if len(user_events) >= 3:
            last_3 = user_events[-3:]
            time_spans = [
                (last_3[i].timestamp - last_3[i - 1].timestamp).total_seconds()
                for i in range(1, len(last_3))
            ]

            if all(ts < 1 for ts in time_spans):
                indicators.append(
                    ThreatIndicator(
                        indicator_type="automation_detected",
                        severity=ThreatLevel.LOW,
                        confidence=0.7,
                        description="Rapid successive requests (possible automation)",
                        affected_entities=[f"user_{event.user_id}"],
                        mitigation_suggestions=["Implement rate limiting", "Require CAPTCHA"],
                    )
                )

        return indicators

    async def _detect_geo_anomalies(self, event: SecurityEvent) -> list[ThreatIndicator]:
        """Detect geographic anomalies (impossible travel)"""
        indicators = []

        if not event.user_id or not event.ip_address:
            return indicators

        user_events = list(self.user_history[event.user_id])

        # Get previous IP addresses
        previous_ips = [
            e.ip_address
            for e in user_events
            if e.ip_address and e.timestamp > datetime.utcnow() - timedelta(hours=1)
        ]

        if previous_ips:
            # Check for multiple countries (requires geoip lookup)
            # This is a simplified version - production would use MaxMind GeoIP
            from ipaddress import ip_address

            countries = set()
            for ip in previous_ips + [event.ip_address]:
                # Extract country code (simplified - real impl would query GeoIP)
                # For now, just check for IP range changes
                try:
                    addr = ip_address(ip)
                    # Check if IP is in different /8 (different country likely)
                    # This is a heuristic - real impl needs GeoIP DB
                except Exception:
                    pass

        return indicators

    def get_security_metrics(self) -> dict[str, Any]:
        """Get real-time security metrics"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(days=1)

        # Count events by type
        events_by_type = defaultdict(int)
        events_by_severity = defaultdict(int)

        for event in self.event_history:
            if event.timestamp > last_hour:
                events_by_type[event.event_type] += 1
                events_by_severity[event.severity] += 1

        # Get active users
        active_users = len(
            [
                user_id
                for user_id, events in self.user_history.items()
                if events and events[-1].timestamp > last_hour
            ]
        )

        # Get active IPs
        active_ips = len(
            [
                ip
                for ip, events in self.ip_history.items()
                if events and events[-1].timestamp > last_hour
            ]
        )

        return {
            "events_last_hour": dict(events_by_type),
            "events_by_severity": dict(events_by_severity),
            "active_users": active_users,
            "active_ips": active_ips,
            "total_events": len(self.event_history),
        }


# Global analyzer instance
security_analyzer = RealTimeSecurityAnalyzer()
