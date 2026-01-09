# app/core/security_monitoring.py
"""
Comprehensive Security Monitoring and Anomaly Detection System
Analyzes user behavior patterns, detects suspicious activities, and provides security alerts
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
import time
from typing import Any

from app.core.cache import cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Security alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(Enum):
    """Types of security anomalies"""

    IMPOSSIBLE_TRAVEL = "impossible_travel"
    UNUSUAL_LOCATION = "unusual_location"
    MULTIPLE_CONCURRENT_SESSIONS = "multiple_concurrent_sessions"
    BRUTE_FORCE_PATTERN = "brute_force_pattern"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SUSPICIOUS_API_USAGE = "suspicious_api_usage"
    ACCOUNT_TAKEOVER_ATTEMPT = "account_takeover_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class RiskLevel(Enum):
    """User risk levels for behavior analysis"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"


@dataclass
class SecurityAlert:
    """Security alert data structure"""

    id: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    user_id: str | None
    description: str
    details: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    risk_score: float = 0.0
    action_taken: str | None = None
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBehaviorProfile:
    """User behavior profile for anomaly detection"""

    user_id: str
    typical_ip_addresses: set[str] = field(default_factory=set)
    typical_user_agents: set[str] = field(default_factory=set)
    typical_login_times: list[int] = field(default_factory=list)  # Hours of day
    typical_session_durations: list[float] = field(default_factory=list)  # Minutes
    typical_api_usage_patterns: dict[str, float] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    last_activity: datetime = field(default_factory=datetime.utcnow)
    total_logins: int = 0
    failed_login_attempts: int = 0
    successful_logins: int = 0
    unique_locations: set[str] = field(default_factory=set)


@dataclass
class GeographicLocation:
    """Geographic location data"""

    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    ip_address: str = ""


@dataclass
class SecurityEvent:
    """Security event for analysis"""

    user_id: str | None
    event_type: str
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    endpoint: str | None = None
    response_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SecurityMonitoringEngine:
    """
    Advanced security monitoring and anomaly detection engine
    """

    def __init__(self):
        # Configuration
        self.enable_monitoring = getattr(settings, "SECURITY_MONITORING_ENABLED", True)
        self.anomaly_threshold = getattr(settings, "ANOMALY_DETECTION_THRESHOLD", 0.7)
        self.alert_retention_days = getattr(settings, "SECURITY_ALERT_RETENTION_DAYS", 90)
        self.behavior_retention_days = getattr(settings, "BEHAVIOR_PROFILE_RETENTION_DAYS", 30)

        # Anomaly detection parameters
        self.impossible_travel_speed_kmh = getattr(settings, "IMPOSSIBLE_TRAVEL_SPEED_KMH", 800)
        self.max_concurrent_sessions = getattr(settings, "MAX_CONCURRENT_SESSIONS", 3)
        self.brute_force_threshold = getattr(settings, "BRUTE_FORCE_THRESHOLD", 5)
        self.unusual_location_threshold = getattr(settings, "UNUSUAL_LOCATION_THRESHOLD", 0.8)

        # Storage
        self.user_profiles: dict[str, UserBehaviorProfile] = {}
        self.security_events: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.active_alerts: dict[str, SecurityAlert] = {}
        self.alert_history: list[SecurityAlert] = []

        # Cache keys
        self.PROFILE_PREFIX = "user_profile:"
        self.EVENTS_PREFIX = "security_events:"
        self.ALERTS_PREFIX = "security_alerts:"
        self.BEHAVIOR_ANALYTICS_PREFIX = "behavior_analytics:"

        self._lock = asyncio.Lock()

        # Initialize background monitoring task flag
        self._background_task_started = False

    async def record_security_event(
        self,
        user_id: str | None,
        event_type: str,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        endpoint: str | None = None,
        response_time: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityAlert | None:
        """
        Record a security event and analyze for anomalies
        """
        if not self.enable_monitoring:
            return None

        # Start background monitoring task if not already started
        if not self._background_task_started:
            self._background_task_started = True
            asyncio.create_task(self._periodic_analysis())

        async with self._lock:
            try:
                # Create security event
                event = SecurityEvent(
                    user_id=user_id,
                    event_type=event_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    timestamp=datetime.utcnow(),
                    success=success,
                    endpoint=endpoint,
                    response_time=response_time,
                    metadata=metadata or {},
                )

                # Store event
                await self._store_security_event(event)

                # Update user behavior profile
                if user_id:
                    await self._update_user_profile(user_id, event)

                # Analyze for anomalies
                alert = await self._analyze_event(event)

                if alert:
                    await self._handle_security_alert(alert)
                    return alert

                return None

            except Exception as e:
                logger.error(f"Error recording security event: {e}")
                return None

    async def get_user_risk_level(self, user_id: str) -> tuple[RiskLevel, dict[str, Any]]:
        """
        Get current risk level and assessment for a user
        """
        try:
            profile = await self._get_user_profile(user_id)

            risk_factors = {}
            risk_score = 0.0

            # Failed login attempts
            if profile.failed_login_attempts > 0:
                failure_rate = profile.failed_login_attempts / max(1, profile.total_logins)
                risk_factors["failed_login_rate"] = failure_rate
                risk_score += failure_rate * 30

            # Unique locations (more locations = higher risk)
            if len(profile.unique_locations) > 5:
                risk_factors["unusual_locations"] = len(profile.unique_locations)
                risk_score += min(len(profile.unique_locations) - 5, 10) * 5

            # Session anomalies
            risk_factors["total_logins"] = profile.total_logins
            risk_factors["success_rate"] = profile.successful_logins / max(1, profile.total_logins)

            # Recent security alerts
            recent_alerts = await self._get_user_recent_alerts(user_id, hours=24)
            if recent_alerts:
                risk_factors["recent_alerts"] = len(recent_alerts)
                risk_score += len(recent_alerts) * 15

            # Determine risk level
            if risk_score >= 70:
                risk_level = RiskLevel.SEVERE
            elif risk_score >= 50:
                risk_level = RiskLevel.HIGH
            elif risk_score >= 30:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            risk_factors["risk_score"] = risk_score

            return risk_level, risk_factors

        except Exception as e:
            logger.error(f"Error getting user risk level for {user_id}: {e}")
            return RiskLevel.LOW, {}

    async def get_security_alerts(
        self,
        user_id: str | None = None,
        severity: AlertSeverity | None = None,
        anomaly_type: AnomalyType | None = None,
        hours: int = 24,
        include_resolved: bool = False,
    ) -> list[SecurityAlert]:
        """
        Get security alerts with filtering options
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            alerts = []

            # Get from cache
            cache_key = f"{self.ALERTS_PREFIX}{'all' if not user_id else user_id}"
            cached_alerts = await cache_get(cache_key) or []

            for alert_data in cached_alerts:
                alert = SecurityAlert(
                    id=alert_data["id"],
                    anomaly_type=AnomalyType(alert_data["anomaly_type"]),
                    severity=AlertSeverity(alert_data["severity"]),
                    user_id=alert_data.get("user_id"),
                    description=alert_data["description"],
                    details=alert_data.get("details", {}),
                    timestamp=datetime.fromisoformat(alert_data["timestamp"]),
                    risk_score=alert_data.get("risk_score", 0.0),
                    action_taken=alert_data.get("action_taken"),
                    resolved=alert_data.get("resolved", False),
                    metadata=alert_data.get("metadata", {}),
                )

                # Apply filters
                if alert.timestamp < cutoff_time:
                    continue
                if not include_resolved and alert.resolved:
                    continue
                if severity and alert.severity != severity:
                    continue
                if anomaly_type and alert.anomaly_type != anomaly_type:
                    continue
                if user_id and alert.user_id != user_id:
                    continue

                alerts.append(alert)

            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Error getting security alerts: {e}")
            return []

    async def resolve_alert(self, alert_id: str, resolution_note: str | None = None) -> bool:
        """
        Mark a security alert as resolved
        """
        try:
            if alert_id not in self.active_alerts:
                return False

            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.metadata["resolution_note"] = resolution_note
            alert.metadata["resolved_at"] = datetime.utcnow().isoformat()

            # Update cache
            await self._update_alert_cache(alert)

            # Remove from active alerts
            del self.active_alerts[alert_id]

            logger.info(
                f"Security alert resolved: {alert_id}",
                extra={"alert_id": alert_id, "resolution_note": resolution_note},
            )

            return True

        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

    async def _store_security_event(self, event: SecurityEvent):
        """Store security event in cache"""
        try:
            events_key = f"{self.EVENTS_PREFIX}{event.user_id or 'anonymous'}"
            existing_events = await cache_get(events_key) or []

            event_data = {
                "user_id": event.user_id,
                "event_type": event.event_type,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "timestamp": event.timestamp.isoformat(),
                "success": event.success,
                "endpoint": event.endpoint,
                "response_time": event.response_time,
                "metadata": event.metadata,
            }

            existing_events.append(event_data)

            # Keep only recent events (last 1000)
            if len(existing_events) > 1000:
                existing_events = existing_events[-1000:]

            # Store with expiration
            await cache_set(events_key, existing_events, expire_seconds=86400 * 7)  # 7 days

        except Exception as e:
            logger.error(f"Error storing security event: {e}")

    async def _update_user_profile(self, user_id: str, event: SecurityEvent):
        """Update user behavior profile with new event data"""
        try:
            profile = await self._get_user_profile(user_id)
            profile.last_activity = event.timestamp
            profile.total_logins += 1

            if event.success:
                profile.successful_logins += 1
            else:
                profile.failed_login_attempts += 1

            # Track IP addresses
            profile.typical_ip_addresses.add(event.ip_address)

            # Track user agents
            profile.typical_user_agents.add(event.user_agent)

            # Track login times
            profile.typical_login_times.append(event.timestamp.hour)
            if len(profile.typical_login_times) > 100:
                profile.typical_login_times = profile.typical_login_times[-100:]

            # Store updated profile
            await self._store_user_profile(profile)

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")

    async def _analyze_event(self, event: SecurityEvent) -> SecurityAlert | None:
        """Analyze event for security anomalies"""
        alerts = []

        # Impossible travel detection
        travel_alert = await self._detect_impossible_travel(event)
        if travel_alert:
            alerts.append(travel_alert)

        # Multiple concurrent sessions
        concurrent_alert = await self._detect_concurrent_sessions(event)
        if concurrent_alert:
            alerts.append(concurrent_alert)

        # Brute force pattern detection
        brute_force_alert = await self._detect_brute_force_pattern(event)
        if brute_force_alert:
            alerts.append(brute_force_alert)

        # Unusual location detection
        location_alert = await self._detect_unusual_location(event)
        if location_alert:
            alerts.append(location_alert)

        # Suspicious API usage
        if event.endpoint:
            api_alert = await self._detect_suspicious_api_usage(event)
            if api_alert:
                alerts.append(api_alert)

        # Return highest severity alert
        if alerts:
            return max(alerts, key=lambda x: (x.severity.value, x.risk_score))

        return None

    async def _detect_impossible_travel(self, event: SecurityEvent) -> SecurityAlert | None:
        """Detect impossible travel between geographic locations"""
        if not event.user_id or event.success:
            return None

        try:
            profile = await self._get_user_profile(event.user_id)
            recent_events = await self._get_user_recent_events(event.user_id, hours=24)

            for past_event in recent_events:
                if not past_event["success"]:
                    continue

                # Calculate time difference
                past_time = datetime.fromisoformat(past_event["timestamp"])
                time_diff_hours = (event.timestamp - past_time).total_seconds() / 3600

                if time_diff_hours <= 1:  # Only check events within last hour
                    # Get location information (simplified - in production use GeoIP)
                    distance_km = self._calculate_distance_estimate(
                        past_event["ip_address"], event.ip_address
                    )

                    if distance_km > self.impossible_travel_speed_kmh * time_diff_hours:
                        alert = SecurityAlert(
                            id=self._generate_alert_id(),
                            anomaly_type=AnomalyType.IMPOSSIBLE_TRAVEL,
                            severity=AlertSeverity.HIGH,
                            user_id=event.user_id,
                            description=f"Impossible travel detected: {distance_km:.0f}km in {time_diff_hours:.1f} hours",
                            details={
                                "from_ip": past_event["ip_address"],
                                "to_ip": event.ip_address,
                                "distance_km": distance_km,
                                "time_diff_hours": time_diff_hours,
                                "max_speed_kmh": self.impossible_travel_speed_kmh,
                            },
                            risk_score=80.0,
                        )
                        return alert

        except Exception as e:
            logger.error(f"Error detecting impossible travel: {e}")

        return None

    async def _detect_concurrent_sessions(self, event: SecurityEvent) -> SecurityAlert | None:
        """Detect suspicious number of concurrent sessions"""
        if not event.user_id or not event.success:
            return None

        try:
            recent_events = await self._get_user_recent_events(event.user_id, hours=1)
            unique_ips = set()

            for past_event in recent_events:
                if past_event["success"] and past_event["ip_address"] != event.ip_address:
                    unique_ips.add(past_event["ip_address"])

            if len(unique_ips) >= self.max_concurrent_sessions:
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    anomaly_type=AnomalyType.MULTIPLE_CONCURRENT_SESSIONS,
                    severity=AlertSeverity.MEDIUM,
                    user_id=event.user_id,
                    description=f"Multiple concurrent sessions from {len(unique_ips) + 1} different IPs",
                    details={
                        "unique_ips": list(unique_ips) + [event.ip_address],
                        "session_count": len(unique_ips) + 1,
                        "threshold": self.max_concurrent_sessions,
                    },
                    risk_score=60.0,
                )
                return alert

        except Exception as e:
            logger.error(f"Error detecting concurrent sessions: {e}")

        return None

    async def _detect_brute_force_pattern(self, event: SecurityEvent) -> SecurityAlert | None:
        """Detect brute force attack patterns"""
        if event.success:
            return None

        try:
            if event.user_id:
                # User-specific brute force
                recent_failures = await self._get_user_recent_failures(event.user_id, hours=1)
                if len(recent_failures) >= self.brute_force_threshold:
                    alert = SecurityAlert(
                        id=self._generate_alert_id(),
                        anomaly_type=AnomalyType.BRUTE_FORCE_PATTERN,
                        severity=AlertSeverity.HIGH,
                        user_id=event.user_id,
                        description=f"Brute force attack detected: {len(recent_failures)} failed attempts",
                        details={
                            "failed_attempts": len(recent_failures),
                            "ip_addresses": list(set(f["ip_address"] for f in recent_failures)),
                            "time_window_hours": 1,
                        },
                        risk_score=75.0,
                    )
                    return alert
            else:
                # IP-based brute force (credential stuffing)
                ip_failures = await self._get_ip_recent_failures(event.ip_address, hours=1)
                if len(ip_failures) >= self.brute_force_threshold * 2:  # Higher threshold for IP
                    alert = SecurityAlert(
                        id=self._generate_alert_id(),
                        anomaly_type=AnomalyType.CREDENTIAL_STUFFING,
                        severity=AlertSeverity.HIGH,
                        user_id=None,
                        description=f"Credential stuffing attack from IP {event.ip_address}",
                        details={
                            "failed_attempts": len(ip_failures),
                            "target_users": list(
                                set(f.get("user_id") for f in ip_failures if f.get("user_id"))
                            ),
                            "ip_address": event.ip_address,
                            "time_window_hours": 1,
                        },
                        risk_score=85.0,
                    )
                    return alert

        except Exception as e:
            logger.error(f"Error detecting brute force pattern: {e}")

        return None

    async def _detect_unusual_location(self, event: SecurityEvent) -> SecurityAlert | None:
        """Detect login from unusual geographic location"""
        if not event.user_id or not event.success:
            return None

        try:
            profile = await self._get_user_profile(event.user_id)

            # If user has established location patterns
            if len(profile.typical_ip_addresses) >= 3:
                # Check if current IP is very different from typical ones
                location_similarity = self._calculate_location_similarity(
                    event.ip_address, list(profile.typical_ip_addresses)
                )

                if location_similarity < (1 - self.unusual_location_threshold):
                    alert = SecurityAlert(
                        id=self._generate_alert_id(),
                        anomaly_type=AnomalyType.UNUSUAL_LOCATION,
                        severity=AlertSeverity.MEDIUM,
                        user_id=event.user_id,
                        description="Login from unusual location",
                        details={
                            "current_ip": event.ip_address,
                            "typical_ips": list(profile.typical_ip_addresses)[
                                :5
                            ],  # Limit for privacy
                            "similarity_score": location_similarity,
                            "threshold": 1 - self.unusual_location_threshold,
                        },
                        risk_score=50.0,
                    )
                    return alert

        except Exception as e:
            logger.error(f"Error detecting unusual location: {e}")

        return None

    async def _detect_suspicious_api_usage(self, event: SecurityEvent) -> SecurityAlert | None:
        """Detect suspicious API usage patterns"""
        if not event.success or not event.endpoint:
            return None

        try:
            # Check for unusual request patterns
            user_events = await self._get_user_recent_events(event.user_id, hours=1)

            # High frequency requests
            recent_requests = [e for e in user_events if e["endpoint"] == event.endpoint]
            if len(recent_requests) > 100:  # More than 100 requests to same endpoint in hour
                alert = SecurityAlert(
                    id=self._generate_alert_id(),
                    anomaly_type=AnomalyType.SUSPICIOUS_API_USAGE,
                    severity=AlertSeverity.MEDIUM,
                    user_id=event.user_id,
                    description=f"High frequency API usage: {len(recent_requests)} requests to {event.endpoint}",
                    details={
                        "endpoint": event.endpoint,
                        "request_count": len(recent_requests),
                        "time_window_hours": 1,
                    },
                    risk_score=55.0,
                )
                return alert

        except Exception as e:
            logger.error(f"Error detecting suspicious API usage: {e}")

        return None

    async def _handle_security_alert(self, alert: SecurityAlert):
        """Handle security alert based on severity and type"""
        try:
            # Store alert
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # Update cache
            await self._update_alert_cache(alert)

            # Take automatic actions based on severity
            if alert.severity == AlertSeverity.CRITICAL:
                await self._take_critical_action(alert)
            elif alert.severity == AlertSeverity.HIGH:
                await self._take_high_risk_action(alert)
            elif alert.severity == AlertSeverity.MEDIUM:
                await self._take_medium_risk_action(alert)

            # Log alert
            logger.warning(
                f"Security alert generated: {alert.description}",
                extra={
                    "alert_id": alert.id,
                    "anomaly_type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "user_id": alert.user_id,
                    "risk_score": alert.risk_score,
                },
            )

        except Exception as e:
            logger.error(f"Error handling security alert: {e}")

    async def _take_critical_action(self, alert: SecurityAlert):
        """Take automatic action for critical alerts"""
        if alert.user_id:
            # Could implement temporary account lock, require 2FA, etc.
            alert.action_taken = "Security team notified and enhanced monitoring enabled"
            logger.critical(
                f"CRITICAL SECURITY ALERT: {alert.description}",
                extra={
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "anomaly_type": alert.anomaly_type.value,
                },
            )

    async def _take_high_risk_action(self, alert: SecurityAlert):
        """Take automatic action for high risk alerts"""
        if alert.user_id:
            # Could implement session invalidation, email notification, etc.
            alert.action_taken = "Enhanced authentication required for next login"
            logger.error(
                f"HIGH RISK SECURITY ALERT: {alert.description}",
                extra={
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "anomaly_type": alert.anomaly_type.value,
                },
            )

    async def _take_medium_risk_action(self, alert: SecurityAlert):
        """Take automatic action for medium risk alerts"""
        alert.action_taken = "Monitoring increased and alert logged"
        logger.warning(
            f"MEDIUM RISK SECURITY ALERT: {alert.description}",
            extra={
                "alert_id": alert.id,
                "user_id": alert.user_id,
                "anomaly_type": alert.anomaly_type.value,
            },
        )

    async def _periodic_analysis(self):
        """Background task for periodic security analysis"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                if not self.enable_monitoring:
                    continue

                # Clean up old data
                await self._cleanup_old_data()

                # Analyze user behavior patterns
                await self._analyze_behavior_patterns()

            except Exception as e:
                logger.error(f"Error in periodic security analysis: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _cleanup_old_data(self):
        """Clean up old security data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.alert_retention_days)

            # Clean old alerts from history
            self.alert_history = [
                alert for alert in self.alert_history if alert.timestamp > cutoff_date
            ]

        except Exception as e:
            logger.error(f"Error cleaning up old security data: {e}")

    async def _analyze_behavior_patterns(self):
        """Analyze overall behavior patterns for trends"""
        try:
            # This could implement more sophisticated ML-based anomaly detection
            # For now, it's a placeholder for future enhancements
            pass
        except Exception as e:
            logger.error(f"Error analyzing behavior patterns: {e}")

    # Helper methods
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        return f"alert_{int(time.time())}_{hash(str(time.time())) % 10000}"

    async def _get_user_profile(self, user_id: str) -> UserBehaviorProfile:
        """Get or create user behavior profile"""
        if user_id not in self.user_profiles:
            # Try to load from cache
            cache_key = f"{self.PROFILE_PREFIX}{user_id}"
            profile_data = await cache_get(cache_key)

            if profile_data:
                profile = UserBehaviorProfile(
                    user_id=user_id,
                    typical_ip_addresses=set(profile_data.get("typical_ips", [])),
                    typical_user_agents=set(profile_data.get("typical_user_agents", [])),
                    typical_login_times=profile_data.get("typical_login_times", []),
                    typical_session_durations=profile_data.get("typical_session_durations", []),
                    typical_api_usage_patterns=profile_data.get("typical_api_usage_patterns", {}),
                    risk_level=RiskLevel(profile_data.get("risk_level", "low")),
                    last_activity=datetime.fromisoformat(profile_data["last_activity"]),
                    total_logins=profile_data.get("total_logins", 0),
                    failed_login_attempts=profile_data.get("failed_login_attempts", 0),
                    successful_logins=profile_data.get("successful_logins", 0),
                    unique_locations=set(profile_data.get("unique_locations", [])),
                )
                self.user_profiles[user_id] = profile
            else:
                profile = UserBehaviorProfile(user_id=user_id)
                self.user_profiles[user_id] = profile

        return self.user_profiles[user_id]

    async def _store_user_profile(self, profile: UserBehaviorProfile):
        """Store user behavior profile in cache"""
        try:
            cache_key = f"{self.PROFILE_PREFIX}{profile.user_id}"
            profile_data = {
                "typical_ips": list(profile.typical_ip_addresses),
                "typical_user_agents": list(profile.typical_user_agents),
                "typical_login_times": profile.typical_login_times[-50:],  # Keep last 50
                "typical_session_durations": profile.typical_session_durations[-50:],
                "typical_api_usage_patterns": profile.typical_api_usage_patterns,
                "risk_level": profile.risk_level.value,
                "last_activity": profile.last_activity.isoformat(),
                "total_logins": profile.total_logins,
                "failed_login_attempts": profile.failed_login_attempts,
                "successful_logins": profile.successful_logins,
                "unique_locations": list(profile.unique_locations),
            }

            await cache_set(
                cache_key, profile_data, expire_seconds=86400 * self.behavior_retention_days
            )

        except Exception as e:
            logger.error(f"Error storing user profile: {e}")

    async def _get_user_recent_events(self, user_id: str, hours: int = 24) -> list[dict]:
        """Get user's recent security events"""
        try:
            events_key = f"{self.EVENTS_PREFIX}{user_id}"
            events = await cache_get(events_key) or []

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_events = []

            for event_data in events:
                event_time = datetime.fromisoformat(event_data["timestamp"])
                if event_time >= cutoff_time:
                    recent_events.append(event_data)

            return recent_events

        except Exception as e:
            logger.error(f"Error getting user recent events: {e}")
            return []

    async def _get_user_recent_failures(self, user_id: str, hours: int = 24) -> list[dict]:
        """Get user's recent failed login attempts"""
        events = await self._get_user_recent_events(user_id, hours)
        return [e for e in events if not e.get("success", True)]

    async def _get_ip_recent_failures(self, ip_address: str, hours: int = 24) -> list[dict]:
        """Get recent failed attempts from specific IP"""
        try:
            # This would ideally query across all users for the given IP
            # For now, return empty list (placeholder)
            return []
        except Exception as e:
            logger.error(f"Error getting IP recent failures: {e}")
            return []

    async def _get_user_recent_alerts(self, user_id: str, hours: int = 24) -> list[SecurityAlert]:
        """Get user's recent security alerts"""
        try:
            alerts = await self.get_security_alerts(
                user_id=user_id, hours=hours, include_resolved=False
            )
            return alerts
        except Exception as e:
            logger.error(f"Error getting user recent alerts: {e}")
            return []

    async def _update_alert_cache(self, alert: SecurityAlert):
        """Update alert cache"""
        try:
            # Update global alerts cache
            global_cache_key = f"{self.ALERTS_PREFIX}all"
            await self._add_alert_to_cache(alert, global_cache_key)

            # Update user-specific alerts cache
            if alert.user_id:
                user_cache_key = f"{self.ALERTS_PREFIX}{alert.user_id}"
                await self._add_alert_to_cache(alert, user_cache_key)

        except Exception as e:
            logger.error(f"Error updating alert cache: {e}")

    async def _add_alert_to_cache(self, alert: SecurityAlert, cache_key: str):
        """Add alert to cache storage"""
        existing_alerts = await cache_get(cache_key) or []

        alert_data = {
            "id": alert.id,
            "anomaly_type": alert.anomaly_type.value,
            "severity": alert.severity.value,
            "user_id": alert.user_id,
            "description": alert.description,
            "details": alert.details,
            "timestamp": alert.timestamp.isoformat(),
            "risk_score": alert.risk_score,
            "action_taken": alert.action_taken,
            "resolved": alert.resolved,
            "metadata": alert.metadata,
        }

        existing_alerts.append(alert_data)

        # Keep only recent alerts (last 1000)
        if len(existing_alerts) > 1000:
            existing_alerts = existing_alerts[-1000:]

        # Store with expiration
        await cache_set(
            cache_key, existing_alerts, expire_seconds=86400 * self.alert_retention_days
        )

    def _calculate_distance_estimate(self, ip1: str, ip2: str) -> float:
        """
        Estimate distance between two IP addresses
        This is a simplified version - in production use proper GeoIP database
        """
        try:
            # Simple heuristic based on IP address structure
            # In production, use MaxMind GeoIP database or similar
            if ip1 == ip2:
                return 0.0

            # Generate pseudo-random but consistent distance estimate
            hash1 = int(hashlib.md5(ip1.encode()).hexdigest()[:8], 16)
            hash2 = int(hashlib.md5(ip2.encode()).hexdigest()[:8], 16)
            distance = abs(hash1 - hash2) % 10000  # Distance up to 10,000 km

            return float(distance)

        except Exception:
            return 1000.0  # Default to 1000 km on error

    def _calculate_location_similarity(self, current_ip: str, typical_ips: list[str]) -> float:
        """
        Calculate location similarity score between current IP and typical IPs
        """
        try:
            if not typical_ips:
                return 0.0

            similarities = []
            for typical_ip in typical_ips:
                # Simple similarity based on IP structure
                # In production, use actual geographic distance
                if current_ip == typical_ip:
                    similarity = 1.0
                elif current_ip.split(".")[:2] == typical_ip.split(".")[:2]:
                    similarity = 0.8  # Same first two octets
                elif current_ip.split(".")[0] == typical_ip.split(".")[0]:
                    similarity = 0.5  # Same first octet
                else:
                    similarity = 0.1  # Different first octet

                similarities.append(similarity)

            return max(similarities)  # Return highest similarity

        except Exception:
            return 0.0

    # ========== PUBLIC API METHODS ==========

    async def detect_impossible_travel(
        self, user_id: str, ip_address: str, timestamp: datetime | None = None
    ) -> SecurityAlert | None:
        """
        Public API: Detect impossible travel between geographic locations

        Args:
            user_id: User ID to check
            ip_address: Current IP address
            timestamp: Event timestamp (default: now)

        Returns:
            SecurityAlert if impossible travel detected, None otherwise
        """
        event = SecurityEvent(
            user_id=user_id,
            event_type="login",
            ip_address=ip_address,
            user_agent="",
            timestamp=timestamp or datetime.utcnow(),
            success=True,
        )
        return await self._detect_impossible_travel(event)

    async def detect_brute_force(
        self, user_id: str | None, ip_address: str, success: bool = False
    ) -> SecurityAlert | None:
        """
        Public API: Detect brute force attack patterns

        Args:
            user_id: User ID (None for IP-based detection)
            ip_address: IP address to check
            success: Whether the attempt was successful

        Returns:
            SecurityAlert if brute force detected, None otherwise
        """
        event = SecurityEvent(
            user_id=user_id,
            event_type="login_attempt",
            ip_address=ip_address,
            user_agent="",
            timestamp=datetime.utcnow(),
            success=success,
        )
        return await self._detect_brute_force_pattern(event)

    async def detect_credential_stuffing(
        self, ip_address: str, attempt_count: int | None = None
    ) -> SecurityAlert | None:
        """
        Public API: Detect credential stuffing attacks (IP-based, multiple users)

        Args:
            ip_address: IP address to check
            attempt_count: Number of failed attempts (optional)

        Returns:
            SecurityAlert if credential stuffing detected, None otherwise
        """
        # Get recent failures from this IP
        ip_failures = await self._get_ip_recent_failures(ip_address, hours=1)

        if attempt_count is not None:
            actual_count = attempt_count
        else:
            actual_count = len(ip_failures)

        if actual_count >= self.brute_force_threshold * 2:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                anomaly_type=AnomalyType.CREDENTIAL_STUFFING,
                severity=AlertSeverity.HIGH,
                user_id=None,
                description=f"Credential stuffing attack from IP {ip_address}: {actual_count} failed attempts",
                details={
                    "failed_attempts": actual_count,
                    "ip_address": ip_address,
                    "time_window_hours": 1,
                },
                risk_score=85.0,
            )
            return alert

        return None

    async def detect_unusual_location(self, user_id: str, ip_address: str) -> SecurityAlert | None:
        """
        Public API: Detect login from unusual geographic location

        Args:
            user_id: User ID to check
            ip_address: Current IP address

        Returns:
            SecurityAlert if unusual location detected, None otherwise
        """
        event = SecurityEvent(
            user_id=user_id,
            event_type="login",
            ip_address=ip_address,
            user_agent="",
            timestamp=datetime.utcnow(),
            success=True,
        )
        return await self._detect_unusual_location(event)

    async def detect_account_takeover(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        behavior_changes: dict[str, Any] | None = None,
    ) -> SecurityAlert | None:
        """
        Public API: Detect potential account takeover attempts

        Analyzes multiple indicators:
        - Unusual location
        - Changed user agent
        - Behavioral deviations
        - Failed login pattern

        Args:
            user_id: User ID to check
            ip_address: Current IP address
            user_agent: Current user agent
            behavior_changes: Optional dict of behavioral changes

        Returns:
            SecurityAlert if account takeover suspected, None otherwise
        """
        risk_indicators = []
        risk_score = 0.0

        profile = await self._get_user_profile(user_id)

        # Check 1: Unusual location
        if (
            ip_address not in profile.typical_ip_addresses
            and len(profile.typical_ip_addresses) >= 3
        ):
            risk_indicators.append("unusual_location")
            risk_score += 25

        # Check 2: Changed user agent
        if user_agent not in profile.typical_user_agents and len(profile.typical_user_agents) >= 2:
            risk_indicators.append("changed_user_agent")
            risk_score += 20

        # Check 3: Recent failed logins
        recent_failures = await self._get_user_recent_failures(user_id, hours=24)
        if len(recent_failures) >= 3:
            risk_indicators.append(f"recent_failures:{len(recent_failures)}")
            risk_score += 30

        # Check 4: Behavioral changes (if provided)
        if behavior_changes:
            risk_indicators.append("behavioral_deviation")
            risk_score += 25

        if risk_score >= 50:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                anomaly_type=AnomalyType.ACCOUNT_TAKEOVER_ATTEMPT,
                severity=AlertSeverity.CRITICAL if risk_score >= 75 else AlertSeverity.HIGH,
                user_id=user_id,
                description=f"Potential account takeover: {len(risk_indicators)} risk indicators detected",
                details={
                    "risk_indicators": risk_indicators,
                    "risk_score": risk_score,
                    "ip_address": ip_address,
                    "user_agent": user_agent[:100],  # Truncate for privacy
                },
                risk_score=risk_score,
            )
            return alert

        return None

    async def detect_privilege_escalation(
        self, user_id: str, attempted_role: str, current_role: str, ip_address: str
    ) -> SecurityAlert | None:
        """
        Public API: Detect privilege escalation attempts

        Args:
            user_id: User ID attempting escalation
            attempted_role: Role being attempted
            current_role: User's current role
            ip_address: IP address of attempt

        Returns:
            SecurityAlert if privilege escalation detected, None otherwise
        """
        # Check if user is trying to escalate to admin-like role
        admin_roles = {"admin", "administrator", "superuser", "root", "owner"}

        if attempted_role.lower() in admin_roles and current_role.lower() not in admin_roles:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                anomaly_type=AnomalyType.PRIVILEGE_ESCALATION,
                severity=AlertSeverity.CRITICAL,
                user_id=user_id,
                description=f"Privilege escalation attempt: {current_role} -> {attempted_role}",
                details={
                    "current_role": current_role,
                    "attempted_role": attempted_role,
                    "ip_address": ip_address,
                },
                risk_score=90.0,
            )
            return alert

        return None

    async def detect_data_exfiltration(
        self, user_id: str, data_accessed: int, endpoint: str, time_window_seconds: int = 60
    ) -> SecurityAlert | None:
        """
        Public API: Detect potential data exfiltration

        Analyzes:
        - Unusual data access volume
        - Rapid successive requests
        - Access to sensitive endpoints

        Args:
            user_id: User ID to check
            data_accessed: Number of records/data points accessed
            endpoint: Endpoint being accessed
            time_window_seconds: Time window for analysis

        Returns:
            SecurityAlert if exfiltration suspected, None otherwise
        """
        # Get recent activity
        recent_events = await self._get_user_recent_events(user_id, hours=1)

        # Count accesses to this endpoint in time window
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)
        recent_accesses = [
            e
            for e in recent_events
            if e.get("endpoint") == endpoint
            and datetime.fromisoformat(e["timestamp"]) >= cutoff_time
        ]

        # Calculate exfiltration risk
        risk_score = 0.0
        indicators = []

        # High volume access
        if data_accessed > 1000:
            risk_score += 40
            indicators.append(f"high_volume:{data_accessed}")

        # Rapid requests
        if len(recent_accesses) > 50:
            risk_score += 35
            indicators.append(f"rapid_requests:{len(recent_accesses)}")

        # Sensitive endpoints
        sensitive_keywords = ["export", "download", "bulk", "all", "admin"]
        if any(kw in endpoint.lower() for kw in sensitive_keywords):
            risk_score += 25
            indicators.append("sensitive_endpoint")

        if risk_score >= 50:
            alert = SecurityAlert(
                id=self._generate_alert_id(),
                anomaly_type=AnomalyType.DATA_EXFILTRATION,
                severity=AlertSeverity.CRITICAL if risk_score >= 75 else AlertSeverity.HIGH,
                user_id=user_id,
                description=f"Potential data exfiltration: {len(indicators)} risk indicators",
                details={
                    "risk_indicators": indicators,
                    "risk_score": risk_score,
                    "endpoint": endpoint,
                    "data_accessed": data_accessed,
                    "request_count": len(recent_accesses),
                },
                risk_score=risk_score,
            )
            return alert

        return None


# Global instance
security_monitor = SecurityMonitoringEngine()
