"""
Message Queue Monitoring and Alerting System

Comprehensive monitoring for dropped messages, queue health, and system reliability.
Tracks metrics, detects anomalies, and generates alerts for operational issues.

Features:
- Real-time message loss tracking
- Queue depth monitoring
- DLQ growth alerts
- Publish/consume rate monitoring
- Lag detection
- Health dashboards
- Prometheus metrics integration

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

# Kafka Producer Metrics
kafka_messages_published_total = Counter(
    "kafka_messages_published_total",
    "Total number of messages published to Kafka",
    ["topic", "status"],  # status: success, failed, buffered
)

kafka_publish_duration_seconds = Histogram(
    "kafka_publish_duration_seconds",
    "Kafka publish duration in seconds",
    ["topic"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

kafka_buffer_size = Gauge(
    "kafka_persistent_buffer_size",
    "Number of events currently in persistent buffer awaiting retry",
    ["topic"],
)

# Kafka Consumer Metrics
kafka_messages_consumed_total = Counter(
    "kafka_messages_consumed_total",
    "Total number of messages consumed from Kafka",
    ["topic", "consumer_group", "status"],  # status: success, failed, retried
)

kafka_consumer_lag = Gauge(
    "kafka_consumer_lag",
    "Consumer lag by topic and partition",
    ["topic", "consumer_group", "partition"],
)

kafka_consumer_processing_duration_seconds = Histogram(
    "kafka_consumer_processing_duration_seconds",
    "Time to process messages",
    ["topic", "handler"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

# DLQ Metrics
kafka_dlq_size = Gauge(
    "kafka_dlq_size",
    "Number of events in Dead Letter Queue",
    ["topic", "reason", "status"],
)

celery_dlq_size = Gauge(
    "celery_dlq_size",
    "Number of failed tasks in Celery Dead Letter Queue",
    ["task_name", "reason", "status"],
)

# System Health Metrics
message_loss_rate = Gauge(
    "message_loss_rate",
    "Rate of message loss (messages/minute)",
    ["queue_type"],  # queue_type: kafka, celery
)

queue_health_score = Gauge(
    "queue_health_score",
    "Overall queue health score (0-100)",
    ["queue_type"],
)


# =============================================================================
# MONITORING MANAGER
# =============================================================================


class MessageQueueMonitor:
    """
    Monitors message queue health and detects dropped messages.

    Tracks:
    - Publish/consume rates
    - Queue depths
    - DLQ growth
    - Consumer lag
    - Error rates
    """

    def __init__(self):
        """Initialize the monitoring manager."""
        self.alert_thresholds = {
            "dlq_size_warning": 100,  # Alert if DLQ has > 100 entries
            "dlq_size_critical": 500,  # Critical alert if > 500 entries
            "consumer_lag_warning": 1000,  # Warn if consumer lag > 1000
            "consumer_lag_critical": 10000,  # Critical if lag > 10000
            "buffer_size_warning": 50,  # Warn if buffer > 50 events
            "message_loss_rate_warning": 10,  # Warn if loss rate > 10/min
            "health_score_critical": 50,  # Critical if health score < 50
        }

        self.alert_handlers = []

    async def check_kafka_health(self, producer, consumer) -> Dict[str, Any]:
        """
        Check overall Kafka queue health.

        Args:
            producer: KafkaEventProducer instance
            consumer: KafkaEventConsumer instance

        Returns:
            Health report with scores and alerts
        """
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": 0,
            "components": {},
            "alerts": [],
        }

        # Check buffer size
        buffer_health = await self._check_buffer_health(producer)
        health_report["components"]["buffer"] = buffer_health

        # Check consumer lag
        lag_health = await self._check_consumer_lag(consumer)
        health_report["components"]["consumer_lag"] = lag_health

        # Check DLQ size
        dlq_health = await self._check_dlq_size()
        health_report["components"]["dlq"] = dlq_health

        # Calculate overall score
        scores = [
            buffer_health.get("score", 0),
            lag_health.get("score", 0),
            dlq_health.get("score", 0),
        ]
        health_report["overall_score"] = sum(scores) / len(scores) if scores else 0

        # Update Prometheus metric
        queue_health_score.labels(queue_type="kafka").set(health_report["overall_score"])

        # Collect alerts
        for component in health_report["components"].values():
            if component.get("alerts"):
                health_report["alerts"].extend(component["alerts"])

        return health_report

    async def _check_buffer_health(self, producer) -> Dict[str, Any]:
        """
        Check persistent buffer health.

        Returns:
            Buffer health report
        """
        try:
            stats = await producer.retry_from_buffer()

            buffer_size = stats.get("remaining", 0)
            score = 100

            alerts = []

            if buffer_size > self.alert_thresholds["buffer_size_warning"]:
                score -= 20
                alerts.append({
                    "severity": "warning",
                    "message": f"Kafka buffer size elevated: {buffer_size} events",
                    "metric": "buffer_size",
                    "value": buffer_size,
                })

            if buffer_size > self.alert_thresholds["buffer_size_warning"] * 5:
                score -= 30
                alerts.append({
                    "severity": "critical",
                    "message": f"Kafka buffer size critical: {buffer_size} events",
                    "metric": "buffer_size",
                    "value": buffer_size,
                })

            return {
                "score": max(0, score),
                "buffer_size": buffer_size,
                "stats": stats,
                "alerts": alerts,
            }

        except Exception as e:
            logger.error(f"Failed to check buffer health: {e}", exc_info=True)
            return {
                "score": 0,
                "error": str(e),
                "alerts": [{
                    "severity": "critical",
                    "message": f"Buffer health check failed: {e}",
                }],
            }

    async def _check_consumer_lag(self, consumer) -> Dict[str, Any]:
        """
        Check consumer lag.

        Returns:
            Consumer lag health report
        """
        try:
            # Get consumer lag (if consumer provides this)
            # This is a placeholder - actual implementation depends on Kafka client
            lag = 0  # Placeholder

            score = 100
            alerts = []

            if lag > self.alert_thresholds["consumer_lag_warning"]:
                score -= 20
                alerts.append({
                    "severity": "warning",
                    "message": f"Consumer lag elevated: {lag}",
                    "metric": "consumer_lag",
                    "value": lag,
                })

            if lag > self.alert_thresholds["consumer_lag_critical"]:
                score -= 40
                alerts.append({
                    "severity": "critical",
                    "message": f"Consumer lag critical: {lag}",
                    "metric": "consumer_lag",
                    "value": lag,
                })

            return {
                "score": max(0, score),
                "lag": lag,
                "alerts": alerts,
            }

        except Exception as e:
            logger.error(f"Failed to check consumer lag: {e}", exc_info=True)
            return {
                "score": 0,
                "error": str(e),
                "alerts": [],
            }

    async def _check_dlq_size(self) -> Dict[str, Any]:
        """
        Check Dead Letter Queue sizes.

        Returns:
            DLQ health report
        """
        try:
            from sqlalchemy import select, func
            from app.core.database import AsyncSessionLocal
            from app.db.models.dead_letter import DeadLetterTask
            from app.db.models.kafka_dead_letter import KafkaDeadLetterTask

            async with AsyncSessionLocal() as db:
                # Check Celery DLQ
                celery_stmt = select(func.count(DeadLetterTask.id)).where(
                    DeadLetterTask.status.in_(["pending", "retryable", "retrying"])
                )
                celery_result = await db.execute(celery_stmt)
                celery_dlq_size = celery_result.scalar() or 0

                # Check Kafka DLQ
                kafka_stmt = select(func.count(KafkaDeadLetterTask.id)).where(
                    KafkaDeadLetterTask.status.in_(["pending", "retryable", "retrying"])
                )
                kafka_result = await db.execute(kafka_stmt)
                kafka_dlq_size = kafka_result.scalar() or 0

            total_dlq = celery_dlq_size + kafka_dlq_size
            score = 100
            alerts = []

            if total_dlq > self.alert_thresholds["dlq_size_warning"]:
                score -= 20
                alerts.append({
                    "severity": "warning",
                    "message": f"DLQ size elevated: {total_dlq} entries "
                              f"(Celery: {celery_dlq_size}, Kafka: {kafka_dlq_size})",
                    "metric": "dlq_size",
                    "value": total_dlq,
                })

            if total_dlq > self.alert_thresholds["dlq_size_critical"]:
                score -= 40
                alerts.append({
                    "severity": "critical",
                    "message": f"DLQ size critical: {total_dlq} entries",
                    "metric": "dlq_size",
                    "value": total_dlq,
                })

            return {
                "score": max(0, score),
                "celery_dlq_size": celery_dlq_size,
                "kafka_dlq_size": kafka_dlq_size,
                "total_dlq_size": total_dlq,
                "alerts": alerts,
            }

        except Exception as e:
            logger.error(f"Failed to check DLQ size: {e}", exc_info=True)
            return {
                "score": 0,
                "error": str(e),
                "alerts": [],
            }

    def register_alert_handler(self, handler):
        """
        Register an alert handler callback.

        Args:
            handler: Async function that takes alert dict as parameter
        """
        self.alert_handlers.append(handler)

    async def send_alerts(self, alerts: List[Dict[str, Any]]):
        """
        Send alerts to registered handlers.

        Args:
            alerts: List of alert dictionaries
        """
        for alert in alerts:
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}", exc_info=True)


# =============================================================================
# ALERT NOTIFICATION HANDLERS
# =============================================================================


class SlackAlertHandler:
    """
    Send monitoring alerts to Slack.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack alert handler.

        Args:
            webhook_url: Slack webhook URL (default: from settings)
        """
        self.webhook_url = webhook_url or getattr(settings, 'SLACK_WEBHOOK_URL', None)

    async def send_alert(self, alert: Dict[str, Any]):
        """
        Send alert to Slack.

        Args:
            alert: Alert dictionary
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured, skipping alert")
            return

        import aiohttp

        severity_emoji = {
            "warning": "⚠️",
            "critical": "🔴",
            "info": "ℹ️",
        }

        emoji = severity_emoji.get(alert.get("severity", "info"), "ℹ️")

        message = {
            "text": f"{emoji} Queue Monitoring Alert",
            "attachments": [{
                "color": "danger" if alert.get("severity") == "critical" else "warning",
                "fields": [
                    {"title": "Severity", "value": alert.get("severity", "unknown"), "short": True},
                    {"title": "Metric", "value": alert.get("metric", "unknown"), "short": True},
                    {"title": "Value", "value": str(alert.get("value", "N/A")), "short": True},
                    {"title": "Message", "value": alert.get("message", ""), "short": False},
                ],
                "footer": "PsychSync Queue Monitor",
                "ts": int(datetime.utcnow().timestamp()),
            }],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=message) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send Slack alert: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=True)


class EmailAlertHandler:
    """
    Send critical monitoring alerts via email.
    """

    def __init__(self, recipients: List[str]):
        """
        Initialize email alert handler.

        Args:
            recipients: List of email addresses to notify
        """
        self.recipients = recipients

    async def send_alert(self, alert: Dict[str, Any]):
        """
        Send alert via email.

        Args:
            alert: Alert dictionary
        """
        # Only send critical alerts via email
        if alert.get("severity") != "critical":
            return

        # TODO: Implement email sending
        logger.warning(f"Email alert not implemented for: {alert}")


# =============================================================================
# PERIODIC HEALTH CHECKS
# =============================================================================


async def run_periodic_health_checks(
    monitor: MessageQueueMonitor,
    interval_seconds: int = 60,
):
    """
    Run periodic health checks and send alerts.

    Args:
        monitor: MessageQueueMonitor instance
        interval_seconds: Check interval in seconds
    """
    logger.info(f"Starting periodic health checks (interval: {interval_seconds}s)")

    while True:
        try:
            # Check Kafka health
            # Note: This would need producer/consumer instances
            # health_report = await monitor.check_kafka_health(producer, consumer)

            # For now, just check DLQ size
            dlq_health = await monitor._check_dlq_size()

            if dlq_health.get("alerts"):
                logger.warning(f"DLQ health alerts: {dlq_health['alerts']}")
                await monitor.send_alerts(dlq_health["alerts"])

            # Log health status
            score = dlq_health.get("score", 0)
            logger.info(f"Queue health check completed: score={score}/100")

        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)

        await asyncio.sleep(interval_seconds)


# =============================================================================
# MESSAGE LOSS DETECTION
# =============================================================================


class MessageLossDetector:
    """
    Detects message loss by comparing publish and consume counts.

    Uses time windows to track expected vs. actual message delivery.
    """

    def __init__(self, window_seconds: int = 60):
        """
        Initialize message loss detector.

        Args:
            window_seconds: Time window for tracking (default: 60 seconds)
        """
        self.window_seconds = window_seconds
        self.publish_counts: Dict[str, List[datetime]] = {}
        self.consume_counts: Dict[str, List[datetime]] = {}

    def record_publish(self, topic: str, message_id: str):
        """
        Record a message publish event.

        Args:
            topic: Topic name
            message_id: Message ID
        """
        if topic not in self.publish_counts:
            self.publish_counts[topic] = []

        now = datetime.utcnow()
        self.publish_counts[topic].append(now)

        # Clean old entries outside window
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.publish_counts[topic] = [
            ts for ts in self.publish_counts[topic] if ts > cutoff
        ]

        # Update Prometheus metric
        kafka_messages_published_total.labels(topic=topic, status="success").inc()

    def record_consume(self, topic: str, message_id: str):
        """
        Record a message consume event.

        Args:
            topic: Topic name
            message_id: Message ID
        """
        if topic not in self.consume_counts:
            self.consume_counts[topic] = []

        now = datetime.utcnow()
        self.consume_counts[topic].append(now)

        # Clean old entries outside window
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.consume_counts[topic] = [
            ts for ts in self.consume_counts[topic] if ts > cutoff
        ]

        # Update Prometheus metric
        kafka_messages_consumed_total.labels(
            topic=topic,
            consumer_group="default",
            status="success"
        ).inc()

    def detect_loss(self) -> Dict[str, Any]:
        """
        Detect message loss by comparing publish and consume counts.

        Returns:
            Loss detection report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "topics": {},
        }

        for topic in self.publish_counts.keys():
            published = len(self.publish_counts.get(topic, []))
            consumed = len(self.consume_counts.get(topic, []))
            loss = published - consumed

            loss_rate = loss / self.window_seconds * 60 if self.window_seconds > 0 else 0

            report["topics"][topic] = {
                "published": published,
                "consumed": consumed,
                "loss": max(0, loss),
                "loss_rate_per_minute": loss_rate,
            }

            # Update Prometheus metric
            message_loss_rate.labels(queue_type="kafka").set(loss_rate)

        return report


# =============================================================================
# GLOBAL MONITOR INSTANCE
# =============================================================================

_monitor: Optional[MessageQueueMonitor] = None
_loss_detector: Optional[MessageLossDetector] = None


def get_monitor() -> MessageQueueMonitor:
    """Get global monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = MessageQueueMonitor()
    return _monitor


def get_loss_detector() -> MessageLossDetector:
    """Get global loss detector instance."""
    global _loss_detector
    if _loss_detector is None:
        _loss_detector = MessageLossDetector()
    return _loss_detector
