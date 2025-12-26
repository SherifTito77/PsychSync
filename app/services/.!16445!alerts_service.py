"""
Unified Alerts Service
Provides comprehensive alerting system that aggregates alerts from all monitoring sources
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
import json
import uuid
import asyncio
from collections import defaultdict, deque
from dataclasses import asdict

from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

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
    condition: Dict[str, Any]  # Condition to trigger alert
    severity: AlertSeverity
    enabled: bool = True
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    throttle_window: int = 300  # seconds - throttle similar alerts
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UnifiedAlert:
    """Unified alert from any monitoring source"""
    id: str
    rule_id: Optional[str]
    source: AlertSource
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notifications_sent: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # For grouping related alerts


@dataclass
class AlertNotification:
    """Alert notification configuration and status"""
    id: str
    alert_id: str
    channel: NotificationChannel
    status: str  # pending, sent, failed
    recipient: str  # email, webhook URL, Slack channel, etc.
    sent_at: Optional[datetime] = None
    response: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertEscalation:
    """Alert escalation configuration"""
    id: str
    rule_id: str
    level: int
    delay_minutes: int
    severity: AlertSeverity
    notification_channels: List[NotificationChannel]
    escalation_message: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class AlertSummary:
    """Alert summary for dashboard"""
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    by_source: Dict[str, int]
    by_severity: Dict[str, int]
    recent_trend: List[Dict[str, Any]]
    top_alerts: List[Dict[str, Any]]
    resolution_rate: float
    average_resolution_time: float


class AlertsService:
    """Comprehensive unified alerts service"""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, UnifiedAlert] = {}
        self.alert_history: List[UnifiedAlert] = []
        self.notifications: Dict[str, AlertNotification] = {}
        self.escalations: Dict[str, List[AlertEscalation]] = defaultdict(list)
        self.throttled_alerts: Dict[str, datetime] = {}
        self.alert_correlations: Dict[str, List[str]] = defaultdict(list)

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
                    "duration": 300  # 5 minutes
                },
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                throttle_window=900  # 15 minutes
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
                    "duration": 600  # 10 minutes
                },
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                throttle_window=1800  # 30 minutes
            ),
            AlertRule(
                id="sentry_critical_error",
                name="Critical Error in Application",
                description="Alert on critical Sentry errors",
                source=AlertSource.SENTRY,
                condition={
                    "level": "error",
                    "tags": {"critical": "true"},
                    "count": 1
                },
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.PAGERDUTY],
                throttle_window=600  # 10 minutes
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
                    "duration": 300  # 5 minutes
                },
                severity=AlertSeverity.WARNING,
                notification_channels=[NotificationChannel.EMAIL],
                throttle_window=1800  # 30 minutes
            ),
            AlertRule(
                id="health_check_failure",
                name="Health Check Failure",
                description="Alert when health checks fail",
                source=AlertSource.HEALTH_CHECKS,
                condition={
                    "status": "unhealthy",
                    "consecutive_failures": 3
                },
                severity=AlertSeverity.CRITICAL,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.PAGERDUTY],
                throttle_window=300  # 5 minutes
            )
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
        condition: Dict[str, Any],
        severity: AlertSeverity,
        notification_channels: Optional[List[NotificationChannel]] = None,
        **kwargs
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
            **kwargs
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
        details: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        rule_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[UnifiedAlert]:
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
                    if severity not in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
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
                correlation_id=correlation_id
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
            logger.error(f"Error processing alert: {str(e)}")
            return None

    def _get_throttle_key(self, source: AlertSource, title: str, details: Optional[Dict[str, Any]]) -> str:
        """Generate throttle key for alert"""
        key_parts = [source.value, title]
        if details:
            # Add relevant details for better throttling
            for detail_key in ['metric', 'endpoint', 'service', 'host']:
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
        details: Optional[Dict[str, Any]]
    ) -> Optional[str]:
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

    async def _evaluate_rule_condition(self, rule: AlertRule, details: Optional[Dict[str, Any]]) -> bool:
        """Evaluate rule condition against alert details"""
        if not details:
            return False

        condition = rule.condition

        # Simple metric comparison
        if "metric" in condition and "operator" in condition and "threshold" in condition:
            metric_name = condition["metric"]
            if metric_name in details:
                metric_value = details[metric_name]
                threshold = condition["threshold"]
                operator = condition["operator"]

                if operator == "greater_than":
                    return metric_value > threshold
                elif operator == "less_than":
                    return metric_value < threshold
                elif operator == "equals":
                    return metric_value == threshold
                elif operator == "not_equals":
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
        else:
            # Default channels based on severity
            if alert.severity == AlertSeverity.CRITICAL:
                channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]
            elif alert.severity == AlertSeverity.EMERGENCY:
                channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.PAGERDUTY]
            else:
                channels = [NotificationChannel.EMAIL]

        # Send notifications
        for channel in channels:
            notification = AlertNotification(
                id=str(uuid.uuid4()),
                alert_id=alert.id,
                channel=channel,
                status="pending",
                recipient=self._get_recipient_for_channel(channel, alert)
            )

            self.notifications[notification.id] = notification

            # Send notification asynchronously
            asyncio.create_task(self._send_notification(notification, alert))

        alert.notifications_sent = channels

    def _get_recipient_for_channel(self, channel: NotificationChannel, alert: UnifiedAlert) -> str:
        """Get recipient for notification channel"""
        channel_configs = {
            NotificationChannel.EMAIL: getattr(settings, 'ALERT_EMAIL_RECIPIENTS', 'alerts@psychsync.com'),
            NotificationChannel.SLACK: getattr(settings, 'SLACK_WEBHOOK_URL', ''),
            NotificationChannel.PAGERDUTY: getattr(settings, 'PAGERDUTY_SERVICE_KEY', ''),
            NotificationChannel.WEBHOOK: getattr(settings, 'ALERT_WEBHOOK_URL', ''),
        }

        return channel_configs.get(channel, '')

    async def _send_notification(self, notification: AlertNotification, alert: UnifiedAlert):
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

            logger.error(f"Failed to send {notification.channel.value} notification: {str(e)}")

    async def _send_email_notification(self, notification: AlertNotification, alert: UnifiedAlert):
        """Send email notification"""
        # Implementation would integrate with email service
        message = f"""
        Alert: {alert.title}

        Severity: {alert.severity.value.upper()}
        Status: {alert.status.value}
        Source: {alert.source.value}
        Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

        Description:
        {alert.description}

        Details:
        {json.dumps(alert.details, indent=2)}

        Tags: {json.dumps(alert.tags, indent=2)}
        """

        logger.info(f"Email alert sent: {notification.recipient}")

    async def _send_slack_notification(self, notification: AlertNotification, alert: UnifiedAlert):
        """Send Slack notification"""
        if not notification.recipient:
            logger.warning("No Slack webhook URL configured")
            return

        # Implementation would send to Slack webhook
        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.EMERGENCY: "danger"
        }.get(alert.severity, "warning")

        payload = {
            "attachments": [{
                "color": color,
