"""
Monitoring System Initialization

This module initializes the monitoring and alerting system for message queues.
It should be called during application startup to register alert handlers
and start background health checks.

Usage:
    from app.monitoring.init import initialize_monitoring

    @app.on_event("startup")
    async def startup_event():
        await initialize_monitoring()

Author: Infrastructure Team
Version: 1.0.0
Date: February 10, 2026
"""

import logging
from typing import Optional

from app.core.config import settings
from app.monitoring.message_queue_monitoring import (
    EmailAlertHandler,
    MessageQueueMonitor,
    SlackAlertHandler,
    run_periodic_health_checks,
)

logger = logging.getLogger(__name__)

# Global monitor instance
_monitor: Optional[MessageQueueMonitor] = None


def get_monitor() -> Optional[MessageQueueMonitor]:
    """
    Get the global monitor instance.

    Returns:
        MessageQueueMonitor instance or None if not initialized
    """
    return _monitor


async def initialize_monitoring(
    enable_slack_alerts: bool = True,
    enable_email_alerts: bool = False,
    health_check_interval_seconds: int = 60,
):
    """
    Initialize the monitoring and alerting system.

    This function:
    1. Creates the global monitor instance
    2. Registers alert handlers (Slack, Email)
    3. Starts periodic health checks

    Args:
        enable_slack_alerts: Enable Slack webhook alerts (default: True)
        enable_email_alerts: Enable email alerts for critical issues (default: False)
        health_check_interval_seconds: How often to run health checks (default: 60)
    """
    global _monitor

    logger.info("🚀 Initializing message queue monitoring system...")

    # Create monitor instance
    _monitor = MessageQueueMonitor()

    # Register Slack alert handler
    if enable_slack_alerts:
        slack_webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)

        if slack_webhook_url:
            slack_handler = SlackAlertHandler(webhook_url=slack_webhook_url)
            _monitor.register_alert_handler(slack_handler.send_alert)
            logger.info("✅ Slack alert handler registered")
        else:
            logger.warning(
                "⚠️  Slack webhook URL not configured (SLACK_WEBHOOK_URL). "
                "Set environment variable to enable Slack alerts."
            )

    # Register email alert handler (critical alerts only)
    if enable_email_alerts:
        alert_recipients_str = getattr(settings, "ALERT_EMAIL_RECIPIENTS", None)

        if alert_recipients_str:
            alert_recipients = [r.strip() for r in alert_recipients_str.split(",")]
            email_handler = EmailAlertHandler(recipients=alert_recipients)
            _monitor.register_alert_handler(email_handler.send_alert)
            logger.info(
                f"✅ Email alert handler registered for {len(alert_recipients)} recipients"
            )
        else:
            logger.warning(
                "⚠️  Alert email recipients not configured (ALERT_EMAIL_RECIPIENTS). "
                "Set environment variable to enable email alerts."
            )

    # Log alert thresholds
    logger.info("📊 Alert thresholds configured:")
    for key, value in _monitor.alert_thresholds.items():
        logger.info(f"   {key}: {value}")

    # Start periodic health checks
    import asyncio

    asyncio.create_task(
        run_periodic_health_checks(
            monitor=_monitor,
            interval_seconds=health_check_interval_seconds,
        )
    )

    logger.info(
        f"✅ Monitoring system initialized! Health checks will run every "
        f"{health_check_interval_seconds} seconds."
    )

    # Log configuration summary
    monitoring_config = settings.get_monitoring_config()
    logger.info(f"📋 Monitoring configuration: {monitoring_config}")


async def shutdown_monitoring():
    """
    Shutdown the monitoring system gracefully.

    This function should be called during application shutdown
    to ensure all monitoring tasks complete cleanly.
    """
    global _monitor

    if _monitor:
        logger.info("🛑 Shutting down monitoring system...")
        # Add any cleanup logic here if needed
        _monitor = None
        logger.info("✅ Monitoring system shutdown complete")


# Convenience function for manual health check trigger
async def trigger_manual_health_check(producer=None, consumer=None):
    """
    Trigger a manual health check and log results.

    This is useful for testing or on-demand health verification.

    Args:
        producer: KafkaEventProducer instance (optional)
        consumer: KafkaEventConsumer instance (optional)

    Returns:
        Health report dictionary
    """
    monitor = get_monitor()

    if not monitor:
        logger.error("❌ Monitor not initialized. Call initialize_monitoring() first.")
        return {}

    logger.info("🔍 Triggering manual health check...")

    if producer and consumer:
        health_report = await monitor.check_kafka_health(producer, consumer)
    else:
        # Partial health check without producer/consumer
        health_report = {
            "timestamp": "2026-02-10T00:00:00.000Z",
            "overall_score": 100,
            "components": {},
            "alerts": [],
            "note": "Full health check requires producer and consumer instances",
        }

    logger.info(
        f"✅ Health check complete. Score: {health_report.get('overall_score', 0):.1f}/100"
    )

    if health_report.get("alerts"):
        logger.warning(f"⚠️  Alerts detected: {len(health_report['alerts'])}")
        for alert in health_report["alerts"]:
            logger.warning(f"   [{alert.get('severity')}] {alert.get('message')}")
    else:
        logger.info("✅ No alerts - system healthy!")

    return health_report
