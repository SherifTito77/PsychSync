"""
Slack and Microsoft Teams Integration Service
Sends notifications to communication platforms
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx


class PlatformType(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationIntegrationService:
    """Service for sending notifications to Slack, Teams, and other platforms"""

    def __init__(self):
        # Webhook URLs (set in environment variables)
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL", "")

        # API clients
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def send_notification(
        self,
        platform: PlatformType,
        message: str,
        title: str = "",
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        fields: Optional[Dict[str, str]] = None,
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to specified platform

        Args:
            platform: Platform to send to (slack, teams)
            message: Notification message
            title: Notification title
            priority: Priority level
            fields: Additional fields to include
            channel: Specific channel (for Slack)

        Returns:
            Success status and response
        """
        if platform == PlatformType.SLACK:
            return await self._send_slack_notification(
                message=message,
                title=title,
                priority=priority,
                fields=fields,
                channel=channel,
            )
        elif platform == PlatformType.TEAMS:
            return await self._send_teams_notification(
                message=message, title=title, priority=priority, fields=fields
            )
        else:
            return {"success": False, "error": f"Platform {platform} not supported"}

    async def _send_slack_notification(
        self,
        message: str,
        title: str,
        priority: NotificationPriority,
        fields: Optional[Dict[str, str]],
        channel: Optional[str],
    ) -> Dict[str, Any]:
        """Send notification to Slack"""
        if not self.slack_webhook:
            return {"success": False, "error": "Slack webhook URL not configured"}

        # Build Slack message payload
        color = self._get_color_for_priority(priority)

        slack_payload = {
            "text": title or "PsychSync Alert",
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [],
                    "footer": "PsychSync Email Monitor",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        # Add channel if specified
        if channel:
            slack_payload["channel"] = channel

        # Add fields if provided
        if fields:
            for key, value in fields.items():
                slack_payload["attachments"][0]["fields"].append(
                    {"title": key, "value": value, "short": True}
                )

        try:
            response = await self.http_client.post(
                self.slack_webhook, json=slack_payload
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "platform": "slack",
                    "message": "Notification sent successfully",
                }
            else:
                return {
                    "success": False,
                    "error": f"Slack API error: {response.status_code}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send Slack notification: {str(e)}",
            }

    async def _send_teams_notification(
        self,
        message: str,
        title: str,
        priority: NotificationPriority,
        fields: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Send notification to Microsoft Teams"""
        if not self.teams_webhook:
            return {"success": False, "error": "Teams webhook URL not configured"}

        # Build Teams Adaptive Card payload
        color = self._get_color_for_priority(priority)

        teams_payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": color.replace("#", ""),
            "title": title,
            "text": message,
            "sections": [{"facts": []}],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Dashboard",
                    "targets": [
                        {
                            "os": "default",
                            "uri": "http://localhost:5173/email-monitoring",
                        }
                    ],
                }
            ],
        }

        # Add fields if provided
        if fields:
            for key, value in fields.items():
                teams_payload["sections"][0]["facts"].append(
                    {"name": key, "value": str(value)}
                )

        try:
            response = await self.http_client.post(
                self.teams_webhook, json=teams_payload
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "platform": "teams",
                    "message": "Notification sent successfully",
                }
            else:
                return {
                    "success": False,
                    "error": f"Teams API error: {response.status_code}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to send Teams notification: {str(e)}",
            }

    async def send_email_alert(
        self, platform: PlatformType, alert_type: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send formatted email alert notification

        Args:
            platform: Platform to send to
            alert_type: Type of alert (anomaly, stress, etc.)
            details: Alert details

        Returns:
            Success status
        """
        # Format message based on alert type
        if alert_type == "anomaly":
            title = "🚨 Email Anomaly Detected"
            message = self._format_anomaly_message(details)
            priority = NotificationPriority.HIGH
        elif alert_type == "stress":
            title = "😰 High Stress Alert"
            message = self._format_stress_message(details)
            priority = NotificationPriority.HIGH
        elif alert_type == "critical":
            title = "⚠️ CRITICAL Email Alert"
            message = self._format_critical_message(details)
            priority = NotificationPriority.CRITICAL
        else:
            title = "📧 Email Notification"
            message = str(details)
            priority = NotificationPriority.MEDIUM

        # Build fields
        fields = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Alert Type": alert_type,
        }

        # Add detail fields
        for key, value in details.items():
            if key not in ["message", "type"]:
                fields[key.replace("_", " ").title()] = str(value)

        return await self.send_notification(
            platform=platform,
            message=message,
            title=title,
            priority=priority,
            fields=fields,
        )

    async def send_daily_summary(
        self, platform: PlatformType, summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send daily email summary digest

        Args:
            platform: Platform to send to
            summary_data: Daily summary statistics

        Returns:
            Success status
        """
        title = "📊 Daily Email Summary"
        message = self._format_daily_summary(summary_data)

        fields = {
            "Total Emails": str(summary_data.get("total_emails", 0)),
            "Emails Today": str(summary_data.get("emails_today", 0)),
            "Top Category": summary_data.get("top_category", "N/A"),
            "Sentiment": summary_data.get("overall_sentiment", "neutral"),
        }

        return await self.send_notification(
            platform=platform,
            message=message,
            title=title,
            priority=NotificationPriority.LOW,
            fields=fields,
        )

    async def send_team_digest(
        self, platform: PlatformType, team_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send team performance digest

        Args:
            platform: Platform to send to
            team_data: Team analytics data

        Returns:
            Success status
        """
        title = f"👥 Team Digest: {team_data.get('team_name', 'Team')}"
        message = self._format_team_digest(team_data)

        fields = {
            "Productivity Score": str(team_data.get("productivity_score", 0)),
            "Avg Response Time": str(team_data.get("avg_response_time", 0)) + " min",
            "Team Size": str(team_data.get("team_size", 0)),
            "Period": str(team_data.get("period_days", 30)) + " days",
        }

        return await self.send_notification(
            platform=platform,
            message=message,
            title=title,
            priority=NotificationPriority.MEDIUM,
            fields=fields,
        )

    def _get_color_for_priority(self, priority: NotificationPriority) -> str:
        """Get color code for priority level"""
        colors = {
            NotificationPriority.LOW: "#36a64f",  # green
            NotificationPriority.MEDIUM: "#ff9900",  # orange
            NotificationPriority.HIGH: "#ff0000",  # red
            NotificationPriority.CRITICAL: "#8b0000",  # dark red
        }
        return colors.get(priority, "#36a64f")

    def _format_anomaly_message(self, details: Dict[str, Any]) -> str:
        """Format anomaly detection message"""
        return (
            f"Anomaly detected in email patterns:\n"
            f"• Type: {details.get('anomaly_type', 'Unknown')}\n"
            f"• Severity: {details.get('severity', 'Unknown')}\n"
            f"• Details: {details.get('message', 'No additional details')}"
        )

    def _format_stress_message(self, details: Dict[str, Any]) -> str:
        """Format stress alert message"""
        return (
            f"High stress indicators detected:\n"
            f"• Stress Level: {details.get('stress_level', 'Unknown')}\n"
            f"• Indicators: {details.get('indicator_count', 0)} found\n"
            f"• Recommendation: Consider reaching out to offer support"
        )

    def _format_critical_message(self, details: Dict[str, Any]) -> str:
        """Format critical alert message"""
        return (
            f"CRITICAL email alert requires immediate attention:\n"
            f"• Alert: {details.get('alert', 'Unknown')}\n"
            f"• Action: {details.get('action_required', 'Review immediately')}\n"
            f"• Impact: {details.get('impact', 'Unknown')}"
        )

    def _format_daily_summary(self, summary: Dict[str, Any]) -> str:
        """Format daily summary message"""
        return (
            f"📈 Here's your daily email summary:\n"
            f"• Total emails processed: {summary.get('total_emails', 0):,}\n"
            f"• Emails today: {summary.get('emails_today', 0)}\n"
            f"• Top category: {summary.get('top_category', 'N/A')}\n"
            f"• Overall sentiment: {summary.get('overall_sentiment', 'neutral')}"
        )

    def _format_team_digest(self, team: Dict[str, Any]) -> str:
        """Format team digest message"""
        return (
            f"Team performance summary:\n"
            f"• Productivity Score: {team.get('productivity_score', 0)}/100\n"
            f"• Average Response Time: {team.get('avg_response_time', 0)} min\n"
            f"• Team Size: {team.get('team_size', 0)} members\n"
            f"• Period: {team.get('period_days', 30)} days"
        )

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


# Singleton instance
notification_integration_service = NotificationIntegrationService()
