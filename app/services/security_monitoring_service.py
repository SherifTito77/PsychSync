"""
Security Monitoring and Alerting System
Real-time threat detection, monitoring, and alerting for PsychSync
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ThreatType(str, Enum):
    """Types of security threats."""

    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ABNORMAL_TRAFFIC = "abnormal_traffic"
    BLOCKED_IP = "blocked_ip"
    MALICIOUS_USER_AGENT = "malicious_user_agent"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class SecurityAlert:
    """Security alert data structure."""

    alert_id: str
    threat_type: ThreatType
    severity: AlertSeverity
    timestamp: datetime
    source_ip: str
    user_id: str | None
    endpoint: str | None
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str | None = None


@dataclass
class SecurityMetrics:
    """Real-time security metrics."""

    total_requests: int = 0
    failed_auth_attempts: int = 0
    blocked_requests: int = 0
    suspicious_ips: set = field(default_factory=set)
    rate_limit_violations: int = 0
    sql_injection_attempts: int = 0
    xss_attempts: int = 0
    alerts_triggered: int = 0


class SecurityMonitoringService:
    """
    Real-time security monitoring and alerting service.

    Features:
    - Real-time threat detection
    - Baseline establishment for normal behavior
    - Anomaly detection
    - Rate limiting monitoring
    - IP reputation tracking
    - Multi-channel alerting (Slack, email, PagerDuty)
    - Dashboard metrics
    - Alert deduplication and aggregation
    """

    def __init__(
        self,
        alert_cooldown_seconds: int = 300,  # 5 minutes
        max_alerts_per_hour: int = 100,
        enable_slack_alerts: bool = False,
        slack_webhook_url: str | None = None,
        enable_email_alerts: bool = False,
        enable_dashboard: bool = True,
    ):
        self.alert_cooldown = timedelta(seconds=alert_cooldown_seconds)
        self.max_alerts_per_hour = max_alerts_per_hour
        self.enable_slack = enable_slack_alerts and slack_webhook_url
        self.slack_webhook_url = slack_webhook_url
        self.enable_email = enable_email_alerts
        self.enable_dashboard = enable_dashboard

        # Alert tracking
        self.recent_alerts: deque = deque(maxlen=1000)
        self.alert_cooldowns: dict[str, datetime] = {}
        self.alert_history: list[SecurityAlert] = []

        # Metrics
        self.metrics = SecurityMetrics()

        # Baseline tracking (for anomaly detection)
        self.request_history: deque = deque(maxlen=1000)  # Last 1000 requests
        self.baseline_requests_per_minute = 60
        self.baseline_failed_auth_rate = 0.05  # 5%

        # Threat detection rules
        self._setup_detection_rules()

    def _setup_detection_rules(self):
        """Setup threat detection rules."""
        self.detection_rules = {
            ThreatType.BRUTE_FORCE: self._detect_brute_force,
            ThreatType.SQL_INJECTION: self._detect_sql_injection,
            ThreatType.XSS_ATTEMPT: self._detect_xss,
            ThreatType.RATE_LIMIT_EXCEEDED: self._detect_rate_limit_exceeded,
            ThreatType.ABNORMAL_TRAFFIC: self._detect_abnormal_traffic,
            ThreatType.BLOCKED_IP: self._detect_blocked_ip,
            ThreatType.MALICIOUS_USER_AGENT: self._detect_malicious_user_agent,
            ThreatType.PRIVILEGE_ESCALATION: self._detect_privilege_escalation,
            ThreatType.DATA_EXFILTRATION: self._detect_data_exfiltration,
        }

    async def monitor_request(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """
        Monitor a request for security threats.

        Args:
            request_data: Request information (ip, endpoint, user_id, etc.)
            response_status: HTTP response status code
            response_time_ms: Response time in milliseconds

        Returns:
            SecurityAlert if threat detected, None otherwise
        """
        # Update metrics
        self.metrics.total_requests += 1
        self.request_history.append(
            {
                "timestamp": datetime.utcnow(),
                "status": response_status,
                "response_time_ms": response_time_ms,
                **request_data,
            }
        )

        # Run detection rules
        for threat_type, detector in self.detection_rules.items():
            try:
                alert = await detector(request_data, response_status, response_time_ms)
                if alert:
                    await self._handle_alert(alert)
                    return alert
            except Exception as e:
                logger.error(f"Error in threat detector {threat_type}: {e}")

        return None

    async def _detect_brute_force(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect brute force login attempts."""
        endpoint = request_data.get("endpoint", "")
        user_id = request_data.get("user_id")
        source_ip = request_data.get("source_ip")

        # Only check auth endpoints
        if not any(
            x in endpoint
            for x in ["/auth/login", "/auth/register", "/auth/reset-password"]
        ):
            return None

        # Check for multiple failed attempts from same IP
        recent_failures = [
            r
            for r in self.request_history
            if r.get("source_ip") == source_ip
            and r.get("status") in [401, 403]
            and r.get("timestamp", datetime.utcnow())
            > datetime.utcnow() - timedelta(minutes=5)
        ]

        if len(recent_failures) >= 5:
            return SecurityAlert(
                alert_id=f"bf_{source_ip}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.BRUTE_FORCE,
                severity=AlertSeverity.CRITICAL,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                user_id=user_id,
                endpoint=endpoint,
                description=f"Brute force attack detected from {source_ip}: {len(recent_failures)} failed attempts",
                metadata={
                    "failed_attempts": len(recent_failures),
                    "time_window": "5 minutes",
                },
            )

        return None

    async def _detect_sql_injection(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect SQL injection attempts."""
        # Check if SQL injection was flagged by input validation middleware
        if request_data.get("sql_injection_detected"):
            return SecurityAlert(
                alert_id=f"sqli_{request_data.get('source_ip')}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.SQL_INJECTION,
                severity=AlertSeverity.CRITICAL,
                timestamp=datetime.utcnow(),
                source_ip=request_data.get("source_ip"),
                user_id=request_data.get("user_id"),
                endpoint=request_data.get("endpoint"),
                description=f"SQL injection attempt blocked from {request_data.get('source_ip')}",
                metadata={"payload_preview": request_data.get("sql_payload", "")[:100]},
            )

        return None

    async def _detect_xss(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect XSS attempts."""
        if request_data.get("xss_detected"):
            return SecurityAlert(
                alert_id=f"xss_{request_data.get('source_ip')}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.XSS_ATTEMPT,
                severity=AlertSeverity.CRITICAL,
                timestamp=datetime.utcnow(),
                source_ip=request_data.get("source_ip"),
                user_id=request_data.get("user_id"),
                endpoint=request_data.get("endpoint"),
                description=f"XSS attempt blocked from {request_data.get('source_ip')}",
                metadata={"payload_preview": request_data.get("xss_payload", "")[:100]},
            )

        return None

    async def _detect_rate_limit_exceeded(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect rate limit violations."""
        if response_status == 429:  # Too Many Requests
            return SecurityAlert(
                alert_id=f"rl_{request_data.get('source_ip')}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.RATE_LIMIT_EXCEEDED,
                severity=AlertSeverity.WARNING,
                timestamp=datetime.utcnow(),
                source_ip=request_data.get("source_ip"),
                user_id=request_data.get("user_id"),
                endpoint=request_data.get("endpoint"),
                description=f"Rate limit exceeded by {request_data.get('source_ip')}",
                metadata={"endpoint": request_data.get("endpoint")},
            )

        return None

    async def _detect_abnormal_traffic(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect abnormal traffic patterns (DDoS, scraping, etc.)."""
        # Calculate requests per minute in last minute
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)

        recent_requests = [
            r for r in self.request_history if r.get("timestamp", now) > one_minute_ago
        ]

        requests_per_minute = len(recent_requests)

        # Alert if significantly above baseline (3x normal)
        if requests_per_minute > self.baseline_requests_per_minute * 3:
            return SecurityAlert(
                alert_id=f"traffic_{int(now.timestamp())}",
                threat_type=ThreatType.ABNORMAL_TRAFFIC,
                severity=AlertSeverity.WARNING,
                timestamp=now,
                source_ip=request_data.get("source_ip"),
                endpoint=request_data.get("endpoint"),
                user_id=request_data.get("user_id"),
                description=f"Abnormal traffic detected: {requests_per_minute} requests/min (baseline: {self.baseline_requests_per_minute})",
                metadata={
                    "requests_per_minute": requests_per_minute,
                    "baseline": self.baseline_requests_per_minute,
                },
            )

        return None

    async def _detect_blocked_ip(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Check if IP is in blocklist."""
        source_ip = request_data.get("source_ip")
        if source_ip in self.metrics.suspicious_ips:
            return SecurityAlert(
                alert_id=f"blocked_{source_ip}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.BLOCKED_IP,
                severity=AlertSeverity.ERROR,
                timestamp=datetime.utcnow(),
                source_ip=source_ip,
                endpoint=request_data.get("endpoint"),
                description=f"Request from blocked IP: {source_ip}",
                metadata={"reason": "IP in blocklist"},
            )

        return None

    async def _detect_malicious_user_agent(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect malicious user agents (bots, scanners, etc.)."""
        user_agent = request_data.get("user_agent", "")

        # Common malicious user agent patterns
        malicious_patterns = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "zmap",
            "wget",
            "curl",
            "python-requests",
            "go-http-client",
            "metasploit",
            "burpcollaborator",
            "scanner",
        ]

        user_agent_lower = user_agent.lower()
        if any(pattern in user_agent_lower for pattern in malicious_patterns):
            return SecurityAlert(
                alert_id=f"ua_{request_data.get('source_ip')}_{int(datetime.utcnow().timestamp())}",
                threat_type=ThreatType.MALICIOUS_USER_AGENT,
                severity=AlertSeverity.WARNING,
                timestamp=datetime.utcnow(),
                source_ip=request_data.get("source_ip"),
                endpoint=request_data.get("endpoint"),
                description=f"Malicious user agent detected: {user_agent[:100]}",
                metadata={"user_agent": user_agent[:200]},
            )

        return None

    async def _detect_privilege_escalation(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect privilege escalation attempts."""
        endpoint = request_data.get("endpoint", "")
        user_id = request_data.get("user_id")

        # Check for admin access attempts by non-admin users
        if "/admin/" in endpoint or "/api/v1/admin/" in endpoint:
            # Check response status - if 403, it was blocked
            if response_status == 403:
                return SecurityAlert(
                    alert_id=f"pe_{user_id}_{int(datetime.utcnow().timestamp())}",
                    threat_type=ThreatType.PRIVILEGE_ESCALATION,
                    severity=AlertSeverity.WARNING,
                    timestamp=datetime.utcnow(),
                    source_ip=request_data.get("source_ip"),
                    user_id=user_id,
                    endpoint=endpoint,
                    description=f"Privilege escalation attempt by user {user_id} to {endpoint}",
                    metadata={"blocked": True},
                )

        return None

    async def _detect_data_exfiltration(
        self,
        request_data: dict[str, Any],
        response_status: int,
        response_time_ms: float,
    ) -> SecurityAlert | None:
        """Detect potential data exfiltration."""
        endpoint = request_data.get("endpoint", "")
        user_id = request_data.get("user_id")

        # Check for large data exports
        if "/export/" in endpoint or "/api/v1/analytics/export" in endpoint:
            # Check response size or number of records
            record_count = request_data.get("record_count", 0)

            # Alert if exporting more than 1000 records at once
            if record_count > 1000:
                return SecurityAlert(
                    alert_id=f"exfil_{user_id}_{int(datetime.utcnow().timestamp())}",
                    threat_type=ThreatType.DATA_EXFILTRATION,
                    severity=AlertSeverity.WARNING,
                    timestamp=datetime.utcnow(),
                    source_ip=request_data.get("source_ip"),
                    user_id=user_id,
                    endpoint=endpoint,
                    description=f"Potential data exfiltration: {record_count} records exported by {user_id}",
                    metadata={"record_count": record_count},
                )

        return None

    async def _handle_alert(self, alert: SecurityAlert):
        """Handle a security alert."""
        # Check cooldowns
        cooldown_key = f"{alert.threat_type}_{alert.source_ip}"
        last_alert_time = self.alert_cooldowns.get(cooldown_key)

        if (
            last_alert_time
            and datetime.utcnow() - last_alert_time < self.alert_cooldown
        ):
            # In cooldown, skip but log
            logger.debug(f"Alert in cooldown: {cooldown_key}")
            return

        # Update cooldown
        self.alert_cooldowns[cooldown_key] = datetime.utcnow()

        # Add to history
        self.alert_history.append(alert)
        self.recent_alerts.append(alert)
        self.metrics.alerts_triggered += 1

        # Log alert
        log_method = (
            logger.critical
            if alert.severity == AlertSeverity.CRITICAL
            else logger.warning
        )
        log_method(f"Security Alert: {alert.description}")

        # Send notifications
        if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            await self._send_alert_notifications(alert)

        # Update metrics
        if alert.threat_type == ThreatType.SQL_INJECTION:
            self.metrics.sql_injection_attempts += 1
        elif alert.threat_type == ThreatType.XSS_ATTEMPT:
            self.metrics.xss_attempts += 1

    async def _send_alert_notifications(self, alert: SecurityAlert):
        """Send alert notifications through configured channels."""
        # Slack notification
        if self.enable_slack and self.slack_webhook_url:
            await self._send_slack_alert(alert)

        # Email notification
        if self.enable_email:
            await self._send_email_alert(alert)

        # PagerDuty (for critical alerts)
        if alert.severity == AlertSeverity.CRITICAL:
            await self._send_pagerduty_alert(alert)

    async def _send_slack_alert(self, alert: SecurityAlert):
        """Send alert to Slack."""
        import aiohttp

        color_map = {
            AlertSeverity.INFO: "#36a64f",  # green
            AlertSeverity.WARNING: "#ff9900",  # orange
            AlertSeverity.ERROR: "#ff0000",  # red
            AlertSeverity.CRITICAL: "#8b0000",  # dark red
        }

        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#36a64f"),
                    "title": f"🚨 Security Alert: {alert.threat_type.value.upper()}",
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value,
                            "short": True,
                        },
                        {"title": "Source IP", "value": alert.source_ip, "short": True},
                        {
                            "title": "Endpoint",
                            "value": alert.endpoint or "N/A",
                            "short": True,
                        },
                        {
                            "title": "User ID",
                            "value": alert.user_id or "N/A",
                            "short": True,
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.isoformat(),
                            "short": True,
                        },
                    ],
                    "footer": "PsychSync Security Monitor",
                    "ts": int(alert.timestamp.timestamp()),
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url, json=payload
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    async def _send_email_alert(self, alert: SecurityAlert):
        """Send alert via email."""
        # Implementation depends on email service
        logger.info(f"Email alert would be sent for: {alert.alert_id}")

    async def _send_pagerduty_alert(self, alert: SecurityAlert):
        """Send alert to PagerDuty."""
        # Implementation depends on PagerDuty integration
        logger.info(f"PagerDuty alert would be sent for: {alert.alert_id}")

    def get_dashboard_metrics(self) -> dict[str, Any]:
        """Get metrics for security dashboard."""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)

        recent_alerts = [a for a in self.alert_history if a.timestamp > last_24h]

        return {
            "total_requests": self.metrics.total_requests,
            "failed_auth_attempts": self.metrics.failed_auth_attempts,
            "blocked_requests": self.metrics.blocked_requests,
            "suspicious_ips": len(self.metrics.suspicious_ips),
            "rate_limit_violations": self.metrics.rate_limit_violations,
            "sql_injection_attempts": self.metrics.sql_injection_attempts,
            "xss_attempts": self.metrics.xss_attempts,
            "alerts_triggered_24h": len(recent_alerts),
            "alerts_by_severity": self._get_alerts_by_severity(recent_alerts),
            "alerts_by_threat_type": self._get_alerts_by_threat_type(recent_alerts),
            "active_threats": len(
                [
                    a
                    for a in recent_alerts
                    if a.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]
                ]
            ),
        }

    def _get_alerts_by_severity(self, alerts: list[SecurityAlert]) -> dict[str, int]:
        """Count alerts by severity."""
        counts = defaultdict(int)
        for alert in alerts:
            counts[alert.severity.value] += 1
        return dict(counts)

    def _get_alerts_by_threat_type(self, alerts: list[SecurityAlert]) -> dict[str, int]:
        """Count alerts by threat type."""
        counts = defaultdict(int)
        for alert in alerts:
            counts[alert.threat_type.value] += 1
        return dict(counts)


# Global monitoring service instance
security_monitor = SecurityMonitoringService()


def get_security_monitor() -> SecurityMonitoringService:
    """Get the global security monitoring service instance."""
    return security_monitor
