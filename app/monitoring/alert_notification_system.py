#!/usr/bin/env python3
"""
Alert Notification System

Handles sending notifications from threat detection system to various channels:
- Slack (webhooks)
- PagerDuty (events API)
- Email (SMTP)
- SMS (Twilio)
- Custom Webhooks

Integrates with AutomatedThreatResponder notification hooks.

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import asyncio
import json
import logging
import smtplib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels"""

    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class NotificationConfig:
    """Configuration for a notification channel"""

    channel: NotificationChannel
    enabled: bool = True
    min_severity: AlertSeverity = AlertSeverity.LOW
    config: dict[str, Any] = field(default_factory=dict)

    def should_send(self, severity: AlertSeverity) -> bool:
        """Check if notification should be sent for this severity"""
        if not self.enabled:
            return False

        severity_order = {
            AlertSeverity.CRITICAL: 5,
            AlertSeverity.HIGH: 4,
            AlertSeverity.MEDIUM: 3,
            AlertSeverity.LOW: 2,
            AlertSeverity.INFO: 1,
        }

        return severity_order.get(severity, 0) >= severity_order.get(
            self.min_severity, 0
        )


@dataclass
class AlertNotification:
    """Alert notification data"""

    severity: AlertSeverity
    title: str
    description: str
    threat_type: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    runbook_url: str | None = None
    response_action: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "threat_type": self.threat_type,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata,
            "runbook_url": self.runbook_url,
            "response_action": self.response_action,
        }


class NotificationSender:
    """Base class for notification senders"""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self.failed_notifications: list[dict[str, Any]] = []

    async def send(self, notification: AlertNotification) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError

    async def send_with_retry(
        self,
        notification: AlertNotification,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        """Send notification with retry logic"""
        for attempt in range(max_retries):
            try:
                success = await self.send(notification)
                if success:
                    return True

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))

            except Exception as e:
                logger.error(f"Notification attempt {attempt + 1} failed: {e}")
                self.failed_notifications.append(
                    {
                        "notification": notification.to_dict(),
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2**attempt))

        return False


class SlackNotificationSender(NotificationSender):
    """Send notifications to Slack via webhook"""

    WEBHOOK_URL_TEMPLATE = "https://hooks.slack.com/services/{webhook}"

    async def send(self, notification: AlertNotification) -> bool:
        """Send notification to Slack"""
        try:
            webhook_url = self.config.config.get("webhook_url")
            if not webhook_url:
                logger.error("Slack webhook URL not configured")
                return False

            # Build Slack message
            color_map = {
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.HIGH: "danger",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.LOW: "good",
                AlertSeverity.INFO: "good",
            }

            emoji_map = {
                AlertSeverity.CRITICAL: "🚨",
                AlertSeverity.HIGH: "⚠️",
                AlertSeverity.MEDIUM: "⚡",
                AlertSeverity.LOW: "ℹ️",
                AlertSeverity.INFO: "📝",
            }

            emoji = emoji_map.get(notification.severity, "🔔")
            color = color_map.get(notification.severity, "good")

            fields = []

            if notification.threat_type:
                fields.append(
                    {
                        "title": "Threat Type",
                        "value": notification.threat_type,
                        "short": True,
                    }
                )

            if notification.user_id:
                fields.append(
                    {"title": "User ID", "value": notification.user_id, "short": True}
                )

            if notification.ip_address:
                fields.append(
                    {
                        "title": "IP Address",
                        "value": notification.ip_address,
                        "short": True,
                    }
                )

            if notification.session_id:
                fields.append(
                    {
                        "title": "Session ID",
                        "value": notification.session_id,
                        "short": True,
                    }
                )

            if notification.response_action:
                fields.append(
                    {
                        "title": "Response Action",
                        "value": notification.response_action,
                        "short": False,
                    }
                )

            if notification.runbook_url:
                fields.append(
                    {
                        "title": "Runbook",
                        "value": f"<{notification.runbook_url}|View Runbook>",
                        "short": False,
                    }
                )

            message = {
                "username": "PsychSync Security",
                "icon_emoji": ":shield:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} {notification.title}",
                        "text": notification.description,
                        "fields": fields,
                        "footer": "PsychSync Threat Detection",
                        "ts": int(notification.timestamp.timestamp()),
                    }
                ],
            }

            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, json=message, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent: {notification.title}")
                        return True
                    error_text = await response.text()
                    logger.error(
                        f"Slack notification failed: {response.status} - {error_text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class PagerDutyNotificationSender(NotificationSender):
    """Send notifications to PagerDuty via Events API"""

    EVENTS_API_URL = "https://events.pagerduty.com/v2/enqueue"

    async def send(self, notification: AlertNotification) -> bool:
        """Send notification to PagerDuty"""
        try:
            routing_key = self.config.config.get(
                "routing_key"
            ) or self.config.config.get("integration_key")
            if not routing_key:
                logger.error("PagerDuty routing key not configured")
                return False

            # Build PagerDuty event
            severity_map = {
                AlertSeverity.CRITICAL: "critical",
                AlertSeverity.HIGH: "error",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.LOW: "info",
                AlertSeverity.INFO: "info",
            }

            event = {
                "routing_key": routing_key,
                "event_action": "trigger",
                "payload": {
                    "summary": notification.title,
                    "severity": severity_map.get(notification.severity, "error"),
                    "source": "psychsync-threat-detection",
                    "timestamp": notification.timestamp.isoformat(),
                    "custom_details": {
                        "description": notification.description,
                        "threat_type": notification.threat_type,
                        "user_id": notification.user_id,
                        "session_id": notification.session_id,
                        "ip_address": notification.ip_address,
                        "response_action": notification.response_action,
                        **notification.metadata,
                    },
                },
                "dedup_key": (
                    f"{notification.session_id or notification.user_id}_{notification.threat_type}"
                    if (notification.session_id or notification.user_id)
                    else None
                ),
            }

            if notification.runbook_url:
                event["payload"]["custom_details"][
                    "runbook_url"
                ] = notification.runbook_url

            # Send to PagerDuty
            async with aiohttp.ClientSession() as session, session.post(
                self.EVENTS_API_URL,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in [200, 202]:
                    logger.info(f"PagerDuty notification sent: {notification.title}")
                    return True
                error_text = await response.text()
                logger.error(
                    f"PagerDuty notification failed: {response.status} - {error_text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send PagerDuty notification: {e}")
            return False


class EmailNotificationSender(NotificationSender):
    """Send notifications via email (SMTP)"""

    async def send(self, notification: AlertNotification) -> bool:
        """Send notification via email"""
        try:
            smtp_host = self.config.config.get("smtp_host")
            smtp_port = self.config.config.get("smtp_port", 587)
            smtp_user = self.config.config.get("smtp_user")
            smtp_password = self.config.config.get("smtp_password")
            recipients = self.config.config.get("recipients", [])

            if not all([smtp_host, smtp_user, smtp_password, recipients]):
                logger.error("Email configuration incomplete")
                return False

            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"[{notification.severity.value.upper()}] {notification.title}"
            )
            msg["From"] = smtp_user
            msg["To"] = ", ".join(recipients)

            # Plain text version
            text_parts = [
                f"Severity: {notification.severity.value.upper()}",
                f"Title: {notification.title}",
                f"Description: {notification.description}",
                f"Timestamp: {notification.timestamp.isoformat()}",
            ]

            if notification.threat_type:
                text_parts.append(f"Threat Type: {notification.threat_type}")
            if notification.user_id:
                text_parts.append(f"User ID: {notification.user_id}")
            if notification.session_id:
                text_parts.append(f"Session ID: {notification.session_id}")
            if notification.ip_address:
                text_parts.append(f"IP Address: {notification.ip_address}")
            if notification.response_action:
                text_parts.append(f"Response Action: {notification.response_action}")
            if notification.runbook_url:
                text_parts.append(f"Runbook: {notification.runbook_url}")

            text_content = "\n".join(text_parts)

            # HTML version
            severity_colors = {
                AlertSeverity.CRITICAL: "#dc3545",
                AlertSeverity.HIGH: "#fd7e14",
                AlertSeverity.MEDIUM: "#ffc107",
                AlertSeverity.LOW: "#28a745",
                AlertSeverity.INFO: "#17a2b8",
            }

            color = severity_colors.get(notification.severity, "#6c757d")

            html_parts = [
                f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: {color}; color: white; padding: 15px; }}
                    .content {{ padding: 20px; }}
                    .field {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>{notification.title}</h2>
                    <p>Severity: {notification.severity.value.upper()}</p>
                </div>
                <div class="content">
                    <p>{notification.description}</p>
            """
            ]

            if notification.threat_type:
                html_parts.append(
                    f'<div class="field"><span class="label">Threat Type:</span> {notification.threat_type}</div>'
                )
            if notification.user_id:
                html_parts.append(
                    f'<div class="field"><span class="label">User ID:</span> {notification.user_id}</div>'
                )
            if notification.ip_address:
                html_parts.append(
                    f'<div class="field"><span class="label">IP Address:</span> {notification.ip_address}</div>'
                )
            if notification.response_action:
                html_parts.append(
                    f'<div class="field"><span class="label">Response Action:</span> {notification.response_action}</div>'
                )
            if notification.runbook_url:
                html_parts.append(
                    f'<div class="field"><span class="label">Runbook:</span> <a href="{notification.runbook_url}">View Runbook</a></div>'
                )

            html_parts.append(
                f"""
                    <div class="field"><span class="label">Timestamp:</span> {notification.timestamp.isoformat()}</div>
                </div>
            </body>
            </html>
            """
            )

            html_content = "".join(html_parts)

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"Email notification sent: {notification.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class SMSNotificationSender(NotificationSender):
    """Send SMS notifications via Twilio"""

    API_URL = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    async def send(self, notification: AlertNotification) -> bool:
        """Send SMS notification via Twilio"""
        try:
            account_sid = self.config.config.get("account_sid")
            auth_token = self.config.config.get("auth_token")
            from_number = self.config.config.get("from_number")
            to_numbers = self.config.config.get("to_numbers", [])

            if not all([account_sid, auth_token, from_number, to_numbers]):
                logger.error("Twilio configuration incomplete")
                return False

            # Build SMS message
            message = f"[{notification.severity.value.upper()}] {notification.title}\n\n{notification.description}"

            if notification.response_action:
                message += f"\n\nAction: {notification.response_action}"

            if notification.runbook_url:
                message += f"\n\nRunbook: {notification.runbook_url}"

            # Send to all recipients
            success_count = 0
            for to_number in to_numbers:
                try:
                    url = self.API_URL.format(account_sid=account_sid)

                    data = {"From": from_number, "To": to_number, "Body": message}

                    auth = aiohttp.BasicAuth(account_sid, auth_token)

                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            url,
                            data=data,
                            auth=auth,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as response:
                            if response.status in [200, 201]:
                                success_count += 1
                            else:
                                error_text = await response.text()
                                logger.error(
                                    f"Twilio SMS failed to {to_number}: {response.status} - {error_text}"
                                )

                except Exception as e:
                    logger.error(f"Failed to send SMS to {to_number}: {e}")

            if success_count > 0:
                logger.info(
                    f"SMS notification sent to {success_count}/{len(to_numbers)} recipients"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return False


class WebhookNotificationSender(NotificationSender):
    """Send notifications to custom webhooks"""

    async def send(self, notification: AlertNotification) -> bool:
        """Send notification to custom webhook"""
        try:
            webhook_url = self.config.config.get("webhook_url")
            if not webhook_url:
                logger.error("Webhook URL not configured")
                return False

            # Build webhook payload
            payload = {
                "notification": notification.to_dict(),
                "channel": "psychsync-threat-detection",
            }

            headers = self.config.config.get("headers", {})

            # Send to webhook
            async with aiohttp.ClientSession() as session, session.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in [200, 201, 202, 204]:
                    logger.info(f"Webhook notification sent: {notification.title}")
                    return True
                error_text = await response.text()
                logger.error(
                    f"Webhook notification failed: {response.status} - {error_text}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class AlertNotificationSystem:
    """
    Main alert notification system.

    Manages multiple notification channels and routes alerts based on severity.
    """

    def __init__(self, configs: list[NotificationConfig]):
        """
        Initialize notification system.

        Args:
            configs: List of notification channel configurations
        """
        self.senders: dict[NotificationChannel, NotificationSender] = {}
        self.configs = configs

        # Initialize senders
        for config in configs:
            sender = self._create_sender(config)
            if sender:
                self.senders[config.channel] = sender

        logger.info(
            f"Alert notification system initialized with {len(self.senders)} channels"
        )

    def _create_sender(self, config: NotificationConfig) -> NotificationSender | None:
        """Create appropriate sender for channel"""
        sender_classes = {
            NotificationChannel.SLACK: SlackNotificationSender,
            NotificationChannel.PAGERDUTY: PagerDutyNotificationSender,
            NotificationChannel.EMAIL: EmailNotificationSender,
            NotificationChannel.SMS: SMSNotificationSender,
            NotificationChannel.WEBHOOK: WebhookNotificationSender,
        }

        sender_class = sender_classes.get(config.channel)
        if sender_class:
            return sender_class(config)

        logger.warning(f"Unknown notification channel: {config.channel}")
        return None

    async def send_alert(self, notification: AlertNotification) -> dict[str, bool]:
        """
        Send alert to all appropriate channels.

        Args:
            notification: Alert notification to send

        Returns:
            Dict mapping channel names to success status
        """
        results = {}

        # Send to each enabled channel that meets severity threshold
        for channel, sender in self.senders.items():
            config = next((c for c in self.configs if c.channel == channel), None)
            if config and config.should_send(notification.severity):
                success = await sender.send_with_retry(notification)
                results[channel.value] = success
            else:
                results[channel.value] = False  # Skipped

        # Log summary
        successful = sum(1 for s in results.values() if s)
        logger.info(
            f"Alert sent to {successful}/{len(results)} channels: {notification.title}"
        )

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get notification system statistics"""
        stats = {
            "total_channels": len(self.senders),
            "enabled_channels": sum(1 for c in self.configs if c.enabled),
            "channels": [],
        }

        for channel, sender in self.senders.items():
            stats["channels"].append(
                {
                    "channel": channel.value,
                    "enabled": next(
                        (c.enabled for c in self.configs if c.channel == channel), False
                    ),
                    "failed_notifications": len(sender.failed_notifications),
                }
            )

        return stats


# Integration with AutomatedThreatResponder
def create_notification_hook(notification_system: AlertNotificationSystem) -> Callable:
    """
    Create a notification hook for AutomatedThreatResponder.

    Usage:
        from app.ai.security.auto_response import AutomatedThreatResponder
        from app.monitoring.alert_notification_system import create_notification_hook, AlertNotificationSystem

        notification_system = AlertNotificationSystem(configs)
        responder = AutomatedThreatResponder(
            notification_hooks=[create_notification_hook(notification_system)]
        )
    """

    async def notification_hook(
        threat_report: dict[str, Any], response_report: dict[str, Any]
    ) -> None:
        """Send notification based on threat report"""
        try:
            # Map threat levels to alert severities
            severity_map = {
                "critical": AlertSeverity.CRITICAL,
                "high": AlertSeverity.HIGH,
                "medium": AlertSeverity.MEDIUM,
                "low": AlertSeverity.LOW,
                "safe": AlertSeverity.INFO,
            }

            threat_level = threat_report.get("overall_threat_level", "low")
            alert_severity = severity_map.get(threat_level, AlertSeverity.LOW)

            # Build notification
            notification = AlertNotification(
                severity=alert_severity,
                title=f"Threat Detected: {threat_level.upper()}",
                description=threat_report.get(
                    "summary", f"Threat level: {threat_level}"
                ),
                threat_type=threat_report.get("dominant_threat_type"),
                user_id=threat_report.get("user_id"),
                session_id=threat_report.get("session_id"),
                ip_address=response_report.get("context", {}).get("ip_address"),
                metadata={
                    "risk_score": threat_report.get("risk_score"),
                    "recommended_action": threat_report.get("recommended_action"),
                    "threat_signals_count": len(
                        threat_report.get("threat_signals", [])
                    ),
                },
            )

            # Send notification
            await notification_system.send_alert(notification)

        except Exception as e:
            logger.error(f"Notification hook failed: {e}")

    return notification_hook


# Convenience functions
async def send_security_alert(
    severity: str, title: str, description: str, **kwargs
) -> dict[str, bool]:
    """
    Convenience function to send security alert.

    Usage:
        from app.monitoring.alert_notification_system import send_security_alert

        await send_security_alert(
            severity='critical',
            title='Account Takeover Detected',
            description='Anomalous behavior detected for user user_123',
            user_id='user_123',
            ip_address='192.168.1.1',
            threat_type='account_takeover'
        )
    """
    # Get global notification system
    from app.monitoring.alert_notification_system import get_notification_system

    notification_system = get_notification_system()
    if not notification_system:
        logger.warning("No notification system configured")
        return {}

    alert_severity = AlertSeverity(severity.lower())

    notification = AlertNotification(
        severity=alert_severity, title=title, description=description, **kwargs
    )

    return await notification_system.send_alert(notification)


# Global notification system instance
_notification_system: AlertNotificationSystem | None = None


def initialize_notification_system(
    configs: list[NotificationConfig],
) -> AlertNotificationSystem:
    """Initialize global notification system"""
    global _notification_system
    _notification_system = AlertNotificationSystem(configs)
    return _notification_system


def get_notification_system() -> AlertNotificationSystem | None:
    """Get global notification system instance"""
    return _notification_system


# CLI interface
def main():
    """CLI interface for notification system"""
    import argparse

    parser = argparse.ArgumentParser(description="Alert Notification System")
    parser.add_argument("--test", action="store_true", help="Send test notification")
    parser.add_argument(
        "--severity",
        type=str,
        default="critical",
        choices=["critical", "high", "medium", "low", "info"],
        help="Test notification severity",
    )

    args = parser.parse_args()

    if args.test:
        logger.info("Sending test notification...")

        async def send_test():
            # Example configuration (load from environment/config in production)
            configs = [
                NotificationConfig(
                    channel=NotificationChannel.SLACK,
                    enabled=True,
                    config={"webhook_url": "YOUR_SLACK_WEBHOOK_URL"},
                )
            ]

            system = AlertNotificationSystem(configs)

            notification = AlertNotification(
                severity=AlertSeverity(args.severity),
                title="Test Security Alert",
                description="This is a test notification from PsychSync Threat Detection System",
                threat_type="test",
                metadata={"test": True},
            )

            results = await system.send_alert(notification)

            logger.info(f"\nTest notification sent with severity: {args.severity}")
            logger.info("Results:")
            for channel, success in results.items():
                status = "✓" if success else "✗"
                logger.info(f"  {status} {channel}: {success}")

            # Print stats
            stats = system.get_stats()
            logger.info(f"\nSystem stats: {json.dumps(stats, indent=2)}")

        asyncio.run(send_test())
    else:
        logger.info("Use --test to send a test notification")


if __name__ == "__main__":
    main()
