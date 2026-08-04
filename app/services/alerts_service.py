"""
Unified Alerts Service
Provides comprehensive alerting system that aggregates alerts from all monitoring sources
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertSource(Enum):
    """Sources of alerts"""

    SENTRY = "sentry"
    APM = "apm"
    SYSTEM_METRICS = "system_metrics"
    HEALTH_CHECKS = "health_checks"
    USER_REPORTED = "user_reported"
    EXTERNAL_SYSTEM = "external_system"


class NotificationChannel(Enum):
    """Alert notification channels"""

    EMAIL = "email"
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft_teams"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    SMS = "sms"


@dataclass
class AlertRule:
    """Alert rule definition"""

    id: str
    name: str
    description: str
    source: AlertSource
    condition: dict[str, Any]  # Condition to trigger alert
    severity: AlertSeverity
    enabled: bool = True
    notification_channels: list[NotificationChannel] = field(default_factory=list)
    throttle_window: int = 300  # seconds - throttle similar alerts
    escalation_rules: list[dict[str, Any]] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UnifiedAlert:
    """Unified alert from any monitoring source"""

    id: str
    rule_id: str | None
    source: AlertSource
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    details: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    notifications_sent: list[NotificationChannel] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None  # For grouping related alerts


@dataclass
class AlertNotification:
    """Alert notification configuration and status"""

    id: str
    alert_id: str
    channel: NotificationChannel
    status: str  # pending, sent, failed
    recipient: str  # email, webhook URL, Slack channel, etc.
    sent_at: datetime | None = None
    response: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertEscalation:
    """Alert escalation configuration"""

    id: str
    rule_id: str
    level: int
    delay_minutes: int
    severity: AlertSeverity
    notification_channels: list[NotificationChannel]
    escalation_message: str
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AlertSummary:
    """Alert summary for dashboard"""

    total_alerts: int
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    by_source: dict[str, int]
    by_severity: dict[str, int]
    recent_trend: list[dict[str, Any]]
    top_alerts: list[dict[str, Any]]
    resolution_rate: float
    average_resolution_time: float


class AlertsService:
    """Comprehensive unified alerts service"""

    def __init__(self):
        self.alert_rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, UnifiedAlert] = {}
        self.alert_history: list[UnifiedAlert] = []
        self.notifications: dict[str, AlertNotification] = {}
        self.escalations: dict[str, list[AlertEscalation]] = defaultdict(list)
        self.throttled_alerts: dict[str, datetime] = {}
        self.alert_correlations: dict[str, list[str]] = defaultdict(list)

        # Initialize default alert rules
        self._initialize_default_rules()

        # Start background tasks
        self.background_tasks = []
        self._start_background_tasks()

    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                id="system_critical_cpu",
                name="Critical CPU Usage",
                description="Alert when CPU usage exceeds 90%",
                source=AlertSource.SYSTEM_METRICS,
                condition={
                    "metric": "cpu_usage",
                    "operator": "greater_than",
                    "threshold": 90,
                    "duration": 300,  # 5 minutes
                },
                severity=AlertSeverity.CRITICAL,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
                throttle_window=900,  # 15 minutes
            ),
            AlertRule(
                id="system_high_memory",
                name="High Memory Usage",
                description="Alert when memory usage exceeds 80%",
                source=AlertSource.SYSTEM_METRICS,
                condition={
                    "metric": "memory_usage",
                    "operator": "greater_than",
                    "threshold": 80,
                    "duration": 600,  # 10 minutes
                },
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                throttle_window=1800,  # 30 minutes
            ),
            AlertRule(
                id="sentry_critical_error",
                name="Critical Error in Application",
                description="Alert on critical Sentry errors",
                source=AlertSource.SENTRY,
                condition={"level": "error", "tags": {"critical": "true"}, "count": 1},
                severity=AlertSeverity.CRITICAL,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.PAGERDUTY,
                ],
                throttle_window=600,  # 10 minutes
            ),
            AlertRule(
                id="apm_slow_requests",
                name="Slow Application Requests",
                description="Alert on slow request patterns",
                source=AlertSource.APM,
                condition={
                    "metric": "response_time",
                    "operator": "greater_than",
                    "threshold": 5000,  # 5 seconds
                    "percentile": 95,
                    "duration": 300,  # 5 minutes
                },
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                throttle_window=1800,  # 30 minutes
            ),
            AlertRule(
                id="health_check_failure",
                name="Health Check Failure",
                description="Alert when health checks fail",
                source=AlertSource.HEALTH_CHECKS,
                condition={"status": "unhealthy", "consecutive_failures": 3},
                severity=AlertSeverity.CRITICAL,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.PAGERDUTY,
                ],
                throttle_window=300,  # 5 minutes
            ),
        ]

        for rule in default_rules:
            self.alert_rules[rule.id] = rule

    def _start_background_tasks(self):
        """Start background alert processing tasks"""
        # Alert escalation task
        escalation_task = asyncio.create_task(self._process_escalations_loop())

        # Alert cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_old_alerts_loop())

        # Alert correlation task
        correlation_task = asyncio.create_task(self._correlate_alerts_loop())

        self.background_tasks = [escalation_task, cleanup_task, correlation_task]

    async def create_alert_rule(
        self,
        name: str,
        description: str,
        source: AlertSource,
        condition: dict[str, Any],
        severity: AlertSeverity,
        notification_channels: list[NotificationChannel] | None = None,
        **kwargs,
    ) -> AlertRule:
        """Create a new alert rule"""
        rule = AlertRule(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            source=source,
            condition=condition,
            severity=severity,
            notification_channels=notification_channels or [],
            **kwargs,
        )

        self.alert_rules[rule.id] = rule
        logger.info(f"Created alert rule: {rule.id} - {name}")

        return rule

    async def process_alert(
        self,
        source: AlertSource,
        title: str,
        description: str,
        severity: AlertSeverity,
        details: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        rule_id: str | None = None,
        correlation_id: str | None = None,
    ) -> UnifiedAlert | None:
        """Process incoming alert and create unified alert"""
        try:
            # Check for throttling
            throttle_key = self._get_throttle_key(source, title, details)
            if self._is_throttled(throttle_key):
                logger.info(f"Alert throttled: {throttle_key}")
                return None

            # Check for matching rules
            if not rule_id:
                rule_id = await self._find_matching_rule(source, severity, details)
                if not rule_id:
                    # No matching rule, create alert if severity is critical
                    if severity not in [
                        AlertSeverity.CRITICAL,
                        AlertSeverity.EMERGENCY,
                    ]:
                        return None

            # Create unified alert
            alert = UnifiedAlert(
                id=str(uuid.uuid4()),
                rule_id=rule_id,
                source=source,
                severity=severity,
                status=AlertStatus.ACTIVE,
                title=title,
                description=description,
                details=details or {},
                tags=tags or {},
                correlation_id=correlation_id,
            )

            # Store alert
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # Correlate with existing alerts
            if correlation_id:
                self.alert_correlations[correlation_id].append(alert.id)

            # Send notifications
            await self._send_alert_notifications(alert)

            # Log alert
            logger.warning(f"ALERT [{severity.value.upper()}] {title}: {description}")

            return alert

        except Exception as e:
            logger.error(f"Error processing alert: {e!s}")
            return None

    def _get_throttle_key(
        self, source: AlertSource, title: str, details: dict[str, Any] | None
    ) -> str:
        """Generate throttle key for alert"""
        key_parts = [source.value, title]
        if details:
            # Add relevant details for better throttling
            for detail_key in ["metric", "endpoint", "service", "host"]:
                if detail_key in details:
                    key_parts.append(f"{detail_key}:{details[detail_key]}")
        return "|".join(key_parts)

    def _is_throttled(self, throttle_key: str) -> bool:
        """Check if alert is throttled"""
        if throttle_key not in self.throttled_alerts:
            return False

        last_alert_time = self.throttled_alerts[throttle_key]
        # Default throttle window is 5 minutes
        throttle_window = timedelta(minutes=5)
        return (datetime.utcnow() - last_alert_time) < throttle_window

    async def _find_matching_rule(
        self,
        source: AlertSource,
        severity: AlertSeverity,
        details: dict[str, Any] | None,
    ) -> str | None:
        """Find matching alert rule"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled or rule.source != source:
                continue

            # Check severity match
            if rule.severity != severity:
                continue

            # Check condition match
            if await self._evaluate_rule_condition(rule, details):
                return rule_id

        return None

    async def _evaluate_rule_condition(
        self, rule: AlertRule, details: dict[str, Any] | None
    ) -> bool:
        """Evaluate rule condition against alert details"""
        if not details:
            return False

        condition = rule.condition

        # Simple metric comparison
        if (
            "metric" in condition
            and "operator" in condition
            and "threshold" in condition
        ):
            metric_name = condition["metric"]
            if metric_name in details:
                metric_value = details[metric_name]
                threshold = condition["threshold"]
                operator = condition["operator"]

                if operator == "greater_than":
                    return metric_value > threshold
                if operator == "less_than":
                    return metric_value < threshold
                if operator == "equals":
                    return metric_value == threshold
                if operator == "not_equals":
                    return metric_value != threshold

        # Tag matching
        if "tags" in condition:
            for tag_key, tag_value in condition["tags"].items():
                if tag_key not in details.get("tags", {}):
                    return False
                if details["tags"][tag_key] != tag_value:
                    return False

        # Level matching
        if "level" in condition:
            if details.get("level") != condition["level"]:
                return False

        return False

    async def _send_alert_notifications(self, alert: UnifiedAlert):
        """Send notifications for alert"""
        # Get notification channels from rule or default channels
        channels = []
        if alert.rule_id and alert.rule_id in self.alert_rules:
            channels = self.alert_rules[alert.rule_id].notification_channels
        # Default channels based on severity
        elif alert.severity == AlertSeverity.CRITICAL:
            channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]
        elif alert.severity == AlertSeverity.EMERGENCY:
            channels = [
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
                NotificationChannel.PAGERDUTY,
            ]
        else:
            channels = [NotificationChannel.EMAIL]

        # Send notifications
        for channel in channels:
            notification = AlertNotification(
                id=str(uuid.uuid4()),
                alert_id=alert.id,
                channel=channel,
                status="pending",
                recipient=self._get_recipient_for_channel(channel, alert),
            )

            self.notifications[notification.id] = notification

            # Send notification asynchronously
            asyncio.create_task(self._send_notification(notification, alert))

        alert.notifications_sent = channels

    def _get_recipient_for_channel(
        self, channel: NotificationChannel, alert: UnifiedAlert
    ) -> str:
        """Get recipient for notification channel"""
        channel_configs = {
            NotificationChannel.EMAIL: getattr(
                settings, "ALERT_EMAIL_RECIPIENTS", "alerts@psychsync.com"
            ),
            NotificationChannel.SLACK: getattr(settings, "SLACK_WEBHOOK_URL", ""),
            NotificationChannel.PAGERDUTY: getattr(
                settings, "PAGERDUTY_SERVICE_KEY", ""
            ),
            NotificationChannel.WEBHOOK: getattr(settings, "ALERT_WEBHOOK_URL", ""),
        }

        return channel_configs.get(channel, "")

    async def _send_notification(
        self, notification: AlertNotification, alert: UnifiedAlert
    ):
        """Send individual notification"""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                await self._send_email_notification(notification, alert)
            elif notification.channel == NotificationChannel.SLACK:
                await self._send_slack_notification(notification, alert)
            elif notification.channel == NotificationChannel.PAGERDUTY:
                await self._send_pagerduty_notification(notification, alert)
            elif notification.channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(notification, alert)

            notification.status = "sent"
            notification.sent_at = datetime.utcnow()

        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)
            notification.retry_count += 1

            # Retry if retries available
            if notification.retry_count < notification.max_retries:
                await asyncio.sleep(60)  # Wait before retry
                await self._send_notification(notification, alert)

            logger.error(
                f"Failed to send {notification.channel.value} notification: {e!s}"
            )

    async def _send_email_notification(
        self, notification: AlertNotification, alert: UnifiedAlert
    ):
        """Send email notification"""
        # Implementation would integrate with email service
        message = f"""
        Alert: {alert.title}

        Severity: {alert.severity.value.upper()}
        Status: {alert.status.value}
        Source: {alert.source.value}
        Time: {alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}

        Description:
        {alert.description}

        Details:
        {json.dumps(alert.details, indent=2)}

        Tags: {json.dumps(alert.tags, indent=2)}
        """

        logger.info(f"Email alert sent: {notification.recipient}")

    async def _send_slack_notification(
        self, notification: AlertNotification, alert: UnifiedAlert
    ):
        """Send Slack notification"""
        if not notification.recipient:
            logger.warning("No Slack webhook URL configured")
            return

        # Implementation would send to Slack webhook
        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.EMERGENCY: "danger",
        }.get(alert.severity, "warning")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"=¨ {alert.severity.value.upper()} Alert: {alert.title}",
                    "text": alert.description,
                    "fields": [
                        {"title": "Source", "value": alert.source.value, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {
                            "title": "Time",
                            "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True,
                        },
                    ],
                    "footer": "PsychSync Monitoring",
                    "ts": int(alert.created_at.timestamp()),
                }
            ]
        }

        logger.info(f"Slack alert sent to {notification.recipient}")

    async def _send_pagerDuty_notification(
        self, notification: AlertNotification, alert: UnifiedAlert
    ):
        """Send PagerDuty notification"""
        if not notification.recipient:
            logger.warning("No PagerDuty service key configured")
            return

        # Implementation would integrate with PagerDuty API
        logger.info(f"PagerDuty alert sent with severity: {alert.severity.value}")

    async def _send_webhook_notification(
        self, notification: AlertNotification, alert: UnifiedAlert
    ):
        """Send webhook notification"""
        if not notification.recipient:
            logger.warning("No webhook URL configured")
            return

        payload = {
            "alert_id": alert.id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "source": alert.source.value,
            "details": alert.details,
            "tags": alert.tags,
            "created_at": alert.created_at.isoformat(),
            "correlation_id": alert.correlation_id,
        }

        logger.info(f"Webhook alert sent to {notification.recipient}")

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str, notes: str | None = None
    ) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        if notes:
            alert.metadata["acknowledgment_notes"] = notes

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    async def resolve_alert(
        self, alert_id: str, resolved_by: str, resolution_notes: str | None = None
    ) -> bool:
        """Resolve an alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by

        if resolution_notes:
            alert.metadata["resolution_notes"] = resolution_notes

        # Move from active to history
        del self.active_alerts[alert_id]

        logger.info(f"Alert {alert_id} resolved by {resolved_by}")
        return True

    async def escalate_alert(self, alert_id: str, escalation_level: int = 1) -> bool:
        """Escalate alert to next level"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]

        # Find escalation configuration
        if alert.rule_id and alert.rule_id in self.escalations:
            escalations = self.escalations[alert.rule_id]
            escalation_config = None

            for esc in escalations:
                if esc.level == escalation_level and esc.enabled:
                    escalation_config = esc
                    break

            if escalation_config:
                # Wait for escalation delay
                await asyncio.sleep(escalation_config.delay_minutes * 60)

                # Create escalated alert
                escalated_alert = UnifiedAlert(
                    id=str(uuid.uuid4()),
                    rule_id=alert.rule_id,
                    source=alert.source,
                    severity=escalation_config.severity,
                    status=AlertStatus.ACTIVE,
                    title=f"[ESCALATED] {alert.title}",
                    description=f"{alert.description}\n\n{escalation_config.escalation_message}",
                    details=alert.details,
                    tags={
                        **alert.tags,
                        "escalated_from": alert.id,
                        "escalation_level": str(escalation_level),
                    },
                    correlation_id=alert.correlation_id,
                )

                self.active_alerts[escalated_alert.id] = escalated_alert
                self.alert_history.append(escalated_alert)

                await self._send_alert_notifications(escalated_alert)

                logger.info(f"Alert escalated: {alert.id} -> {escalated_alert.id}")
                return True

        return False

    async def get_alert_summary(self, hours: int = 24) -> AlertSummary:
        """Get alert summary for dashboard"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Count alerts
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)
        critical_alerts = len(
            [
                a
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.CRITICAL
            ]
        )
        warning_alerts = len(
            [
                a
                for a in self.active_alerts.values()
                if a.severity == AlertSeverity.WARNING
            ]
        )

        # By source
        by_source = defaultdict(int)
        for alert in self.alert_history:
            if alert.created_at >= cutoff_time:
                by_source[alert.source.value] += 1

        # By severity
        by_severity = defaultdict(int)
        for alert in self.alert_history:
            if alert.created_at >= cutoff_time:
                by_severity[alert.severity.value] += 1

        # Recent trend (last 24 hours in hourly buckets)
        recent_trend = []
        for i in range(24):
            hour_time = datetime.utcnow() - timedelta(hours=i)
            hour_start = hour_time.replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            hour_alerts = [
                a for a in self.alert_history if hour_start <= a.created_at < hour_end
            ]
            recent_trend.append(
                {
                    "hour": hour_start.strftime("%Y-%m-%d %H:00"),
                    "count": len(hour_alerts),
                }
            )

        # Top alerts
        top_alerts = []
        alert_counts = defaultdict(int)
        for alert in self.alert_history:
            if alert.created_at >= cutoff_time:
                alert_counts[alert.title] += 1

        for title, count in sorted(
            alert_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            top_alerts.append({"title": title, "count": count})

        # Resolution metrics
        resolved_alerts = [
            a
            for a in self.alert_history
            if a.resolved_at and a.created_at >= cutoff_time
        ]
        resolution_rate = (
            len(resolved_alerts)
            / len([a for a in self.alert_history if a.created_at >= cutoff_time])
            if len([a for a in self.alert_history if a.created_at >= cutoff_time]) > 0
            else 0
        )

        resolution_times = []
        for alert in resolved_alerts:
            if alert.resolved_at and alert.created_at:
                resolution_times.append(
                    (alert.resolved_at - alert.created_at).total_seconds()
                )

        avg_resolution_time = mean(resolution_times) if resolution_times else 0

        return AlertSummary(
            total_alerts=total_alerts,
            active_alerts=active_alerts,
            critical_alerts=critical_alerts,
            warning_alerts=warning_alerts,
            by_source=dict(by_source),
            by_severity=dict(by_severity),
            recent_trend=list(reversed(recent_trend)),
            top_alerts=top_alerts,
            resolution_rate=resolution_rate,
            average_resolution_time=avg_resolution_time,
        )

    async def get_active_alerts(
        self, severity: AlertSeverity | None = None
    ) -> list[UnifiedAlert]:
        """Get active alerts, optionally filtered by severity"""
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda x: x.created_at, reverse=True)

    async def get_alert_history(
        self, hours: int = 24, limit: int = 100
    ) -> list[UnifiedAlert]:
        """Get alert history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = [a for a in self.alert_history if a.created_at >= cutoff_time]
        return sorted(history, key=lambda x: x.created_at, reverse=True)[:limit]

    async def _process_escalations_loop(self):
        """Background loop for processing alert escalations"""
        while True:
            try:
                # Check for alerts that need escalation
                for alert in list(self.active_alerts.values()):
                    if alert.status == AlertStatus.ACTIVE and alert.rule_id:
                        # Check if alert needs escalation
                        time_active = (
                            datetime.utcnow() - alert.created_at
                        ).total_seconds()

                        # Escalate after 1 hour for critical alerts
                        if (
                            alert.severity == AlertSeverity.CRITICAL
                            and time_active > 3600
                        ) or (
                            alert.severity == AlertSeverity.WARNING
                            and time_active > 14400
                        ):
                            await self.escalate_alert(alert.id)

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error processing escalations: {e!s}")
                await asyncio.sleep(60)

    async def _cleanup_old_alerts_loop(self):
        """Background loop for cleaning up old alerts"""
        while True:
            try:
                # Keep 30 days of alert history
                cutoff_time = datetime.utcnow() - timedelta(days=30)
                self.alert_history = [
                    a for a in self.alert_history if a.created_at >= cutoff_time
                ]

                # Clean up old notifications
                notification_cutoff = datetime.utcnow() - timedelta(days=7)
                old_notifications = [
                    nid
                    for nid, notif in self.notifications.items()
                    if notif.created_at < notification_cutoff
                ]
                for nid in old_notifications:
                    del self.notifications[nid]

                await asyncio.sleep(3600)  # Clean every hour

            except Exception as e:
                logger.error(f"Error cleaning up old alerts: {e!s}")
                await asyncio.sleep(3600)

    async def _correlate_alerts_loop(self):
        """Background loop for correlating related alerts"""
        while True:
            try:
                # Correlate alerts based on timing, source, and content
                recent_alerts = [
                    a
                    for a in self.active_alerts.values()
                    if (datetime.utcnow() - a.created_at).total_seconds() < 300
                ]  # Last 5 minutes

                for alert in recent_alerts:
                    if not alert.correlation_id:
                        # Look for correlation candidates
                        for other_alert in recent_alerts:
                            if (
                                alert.id != other_alert.id
                                and not other_alert.correlation_id
                            ):
                                if self._should_correlate(alert, other_alert):
                                    correlation_id = str(uuid.uuid4())
                                    alert.correlation_id = correlation_id
                                    other_alert.correlation_id = correlation_id
                                    self.alert_correlations[correlation_id] = [
                                        alert.id,
                                        other_alert.id,
                                    ]

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error correlating alerts: {e!s}")
                await asyncio.sleep(60)

    def _should_correlate(self, alert1: UnifiedAlert, alert2: UnifiedAlert) -> bool:
        """Determine if two alerts should be correlated"""
        # Same source and similar time
        if alert1.source != alert2.source:
            return False

        time_diff = abs((alert1.created_at - alert2.created_at).total_seconds())
        if time_diff > 300:  # 5 minutes
            return False

        # Same severity
        if alert1.severity != alert2.severity:
            return False

        # Similar title or tags
        title_similarity = self._calculate_similarity(
            alert1.title.lower(), alert2.title.lower()
        )
        if title_similarity > 0.7:  # 70% similarity
            return True

        # Check for overlapping tags
        common_tags = set(alert1.tags.items()) & set(alert2.tags.items())
        if len(common_tags) > 2:
            return True

        return False

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        words1 = set(str1.split())
        words2 = set(str2.split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0

    async def shutdown(self):
        """Shutdown alerts service"""
        logger.info("Shutting down alerts service")

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info("Alerts service shutdown complete")


# Initialize alerts service
alerts_service = AlertsService()
