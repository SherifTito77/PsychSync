"""
Slack Service Stub for Local Development

This stub allows local development without requiring actual Slack credentials.
For production, this connects to real Slack API via webhooks/OAuth.

Why we need this:
- Develop Slack features without live workspace
- Test notification logic without spam
- Mock Slack responses for unit tests
- Demonstrate integration flow
"""

import logging
from datetime import datetime
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class SlackServiceStub:
    """
    Stub implementation of Slack service for local development

    In production, replace with real slack_sdk.WebClient
    """

    def __init__(self, test_mode: bool = True):
        """
        Initialize Slack service

        Args:
            test_mode: If True, logs messages instead of sending
        """
        self.test_mode = test_mode or not settings.SLACK_BOT_TOKEN
        self.sent_messages = []  # For testing

        if self.test_mode:
            logger.info(
                "🧪 Slack Service running in TEST MODE - messages will be logged, not sent"
            )
        else:
            logger.info("✅ Slack Service connected to workspace")

    async def send_message_to_channel(
        self,
        channel: str,
        message: str,
        blocks: list[dict] | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """
        Send message to Slack channel

        Args:
            channel: Channel ID or name (e.g., #general, C1234567890)
            message: Plain text message (fallback)
            blocks: Rich message blocks (Slack Block Kit)
            thread_ts: Thread timestamp for replies

        Returns:
            Response with message timestamp

        Example:
            await slack.send_message_to_channel(
                channel="#team-wellness",
                message="Assessment completed!",
                blocks=[{
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "✅ Assessment completed!"}
                }]
            )
        """
        if self.test_mode:
            log_data = {
                "channel": channel,
                "message": message,
                "blocks": blocks,
                "thread_ts": thread_ts,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.sent_messages.append(log_data)
            logger.info(f"📤 [SLACK STUB] Message to {channel}: {message}")

            return {
                "ok": True,
                "channel": channel,
                "ts": f"stub_{datetime.utcnow().timestamp()}",
                "message": {"text": message},
            }

        # Production: Use real Slack SDK
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        try:
            client = WebClient(token=settings.SLACK_BOT_TOKEN)
            response = client.chat_postMessage(
                channel=channel, text=message, blocks=blocks, thread_ts=thread_ts
            )
            return response.data
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise

    async def send_notification(
        self, team_id: int, notification_type: str, data: dict[str, Any]
    ) -> bool:
        """
        Send formatted notification to team channel

        Args:
            team_id: Team ID
            notification_type: Type of notification
            data: Notification data

        Returns:
            Success boolean

        Notification Types:
            - assessment_complete: User completed assessment
            - wellbeing_alert: Team member needs support
            - report_ready: Team report is ready
            - team_member_joined: New member joined team
        """
        # Get team channel (from database in production)
        channel = f"#team-{team_id}"

        # Format message based on type
        if notification_type == "assessment_complete":
            message = self._format_assessment_complete(data)
        elif notification_type == "wellbeing_alert":
            message = self._format_wellbeing_alert(data)
        elif notification_type == "report_ready":
            message = self._format_report_ready(data)
        elif notification_type == "team_member_joined":
            message = self._format_member_joined(data)
        else:
            message = {"text": f"Notification: {notification_type}"}

        response = await self.send_message_to_channel(
            channel=channel, message=message["text"], blocks=message.get("blocks")
        )

        return response.get("ok", False)

    async def send_direct_message(
        self, user_id: str, message: str, blocks: list[dict] | None = None
    ) -> dict[str, Any]:
        """
        Send DM to specific user

        Args:
            user_id: Slack user ID (U1234567890)
            message: Message text
            blocks: Rich blocks
        """
        if self.test_mode:
            logger.info(f"📧 [SLACK STUB] DM to user {user_id}: {message}")
            return {"ok": True, "channel": f"D_{user_id}"}

        # Production: Open DM channel and send
        from slack_sdk import WebClient

        client = WebClient(token=settings.SLACK_BOT_TOKEN)

        # Open DM channel
        dm_response = client.conversations_open(users=[user_id])
        channel_id = dm_response["channel"]["id"]

        # Send message
        return await self.send_message_to_channel(
            channel=channel_id, message=message, blocks=blocks
        )

    async def handle_slash_command(
        self, command: str, user_id: str, channel_id: str, text: str
    ) -> dict[str, Any]:
        """
        Handle slash command from Slack

        Commands:
            /psychsync help - Show help
            /psychsync status - Show user status
            /psychsync team - Show team status
            /checkin - Quick wellness check-in
            /wellness - View wellness stats
            /assess - Start assessment

        Args:
            command: Command name (/psychsync)
            user_id: Slack user ID
            channel_id: Channel ID where command was sent
            text: Command arguments

        Returns:
            Response to send back to Slack
        """
        if self.test_mode:
            logger.info(f"⚡ [SLACK STUB] Command: {command} {text} from {user_id}")

        # Route to appropriate handler
        if command == "/psychsync":
            return await self._handle_psychsync_command(user_id, text)
        if command == "/checkin":
            return await self._handle_checkin_command(user_id)
        if command == "/wellness":
            return await self._handle_wellness_command(user_id, text)
        if command == "/assess":
            return await self._handle_assess_command(user_id)
        return {"response_type": "ephemeral", "text": f"Unknown command: {command}"}

    # ============================================
    # PRIVATE HELPER METHODS
    # ============================================

    def _format_assessment_complete(self, data: dict) -> dict:
        """Format assessment completion notification"""
        user_name = data.get("user_name", "Team member")
        assessment_type = data.get("assessment_type", "Assessment")
        score = data.get("score")

        emoji = (
            "🟢" if score and score >= 80 else "🟡" if score and score >= 60 else "🔴"
        )

        return {
            "text": f"{emoji} {user_name} completed {assessment_type}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Assessment Completed",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Team Member:*\n{user_name}"},
                        {"type": "mrkdwn", "text": f"*Assessment:*\n{assessment_type}"},
                        {
                            "type": "mrkdwn",
                            "text": (
                                f"*Score:*\n{score}/100"
                                if score
                                else "*Status:*\nCompleted"
                            ),
                        },
                    ],
                },
            ],
        }

    def _format_wellbeing_alert(self, data: dict) -> dict:
        """Format wellbeing alert notification"""
        return {
            "text": f"⚠️ Wellbeing alert: {data.get('message')}",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "⚠️ Wellbeing Alert"},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": data.get("message", "A team member needs support"),
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Details"},
                            "style": "primary",
                            "url": data.get("url", "https://app.psychsync.com"),
                        }
                    ],
                },
            ],
        }

    def _format_report_ready(self, data: dict) -> dict:
        """Format report ready notification"""
        return {
            "text": f"📊 {data.get('report_type', 'Report')} is ready",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📊 Your *{data.get('report_type', 'Team Report')}* is ready!",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Download Report"},
                            "url": data.get("download_url", "#"),
                        }
                    ],
                },
            ],
        }

    def _format_member_joined(self, data: dict) -> dict:
        """Format new member notification"""
        return {
            "text": f"👋 {data.get('member_name')} joined the team",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"👋 Welcome *{data.get('member_name')}* to the team!",
                    },
                }
            ],
        }

    async def _handle_psychsync_command(self, user_id: str, text: str) -> dict:
        """Handle /psychsync command"""
        if not text or text == "help":
            return {
                "response_type": "ephemeral",
                "text": "PsychSync Commands:\n"
                "• `/psychsync status` - Your wellness status\n"
                "• `/psychsync team` - Team overview\n"
                "• `/checkin` - Quick wellness check-in\n"
                "• `/wellness` - View your stats\n"
                "• `/assess` - Start assessment",
            }
        if text == "status":
            return {
                "response_type": "ephemeral",
                "text": "📊 Your Wellness Status:\n"
                "Overall Score: 78/100 🟢\n"
                "Trend: +5 from last week 📈\n"
                "Last Assessment: 2 days ago",
            }
        if text == "team":
            return {
                "response_type": "in_channel",
                "text": "👥 Team Wellness Overview:\n"
                "Average Score: 72/100 🟡\n"
                "Participation: 85% (11/13)\n"
                "Alerts: ⚠️ 2 requiring attention",
            }
        return {
            "response_type": "ephemeral",
            "text": f"Unknown command: {text}\nType `/psychsync help` for available commands",
        }

    async def _handle_checkin_command(self, user_id: str) -> dict:
        """Handle /checkin command"""
        # In production, this would open a modal
        return {
            "response_type": "ephemeral",
            "text": "✅ Opening check-in modal...\n"
            "(In production, this opens an interactive modal)",
        }

    async def _handle_wellness_command(self, user_id: str, text: str) -> dict:
        """Handle /wellness command"""
        if text == "team":
            return {
                "response_type": "in_channel",
                "text": "👥 Team Wellness Stats:\n"
                "• Team Average: 72/100\n"
                "• Participation: 85%\n"
                "• Trend: Stable ➡️",
            }
        return {
            "response_type": "ephemeral",
            "text": "📊 Your Wellness Stats:\n"
            "• Score: 78/100\n"
            "• Completed: 12/15 this month\n"
            "• Trend: +5 📈",
        }

    async def _handle_assess_command(self, user_id: str) -> dict:
        """Handle /assess command"""
        return {
            "response_type": "ephemeral",
            "text": "🎯 Choose an assessment:\n"
            "• Burnout Assessment\n"
            "• Stress Level Check\n"
            "• Wellbeing Survey\n"
            "\n(In production, this opens selection modal)",
        }

    # ============================================
    # UTILITY METHODS
    # ============================================

    def get_sent_messages(self) -> list[dict]:
        """Get list of sent messages (for testing)"""
        return self.sent_messages

    def clear_sent_messages(self):
        """Clear sent messages (for testing)"""
        self.sent_messages = []

    def is_test_mode(self) -> bool:
        """Check if running in test mode"""
        return self.test_mode


# ============================================
# INTEGRATION GUIDE
# ============================================

"""
Production Integration Guide
============================

1. Install Dependencies:
   pip install slack-sdk

2. Create Slack App:
   - Go to https://api.slack.com/apps
   - Create new app
   - Get Bot Token (xoxb-...)
   - Get Signing Secret

3. Add to .env:
   SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}  # Set via environment variable
   SLACK_SIGNING_SECRET=your-secret-here
   SLACK_WEBHOOK_URL=https://hooks.slack.com/... (optional)

4. Register Slash Commands:
   - /psychsync → https://your-api.com/api/v1/slack/commands
   - /checkin → https://your-api.com/api/v1/slack/commands
   - /wellness → https://your-api.com/api/v1/slack/commands
   - /assess → https://your-api.com/api/v1/slack/commands

5. Enable Event Subscriptions:
   - Request URL: https://your-api.com/api/v1/slack/events
   - Subscribe to: app_mention, message.im

6. Replace Stub with Real Implementation:

   from slack_sdk import WebClient
   from slack_sdk.errors import SlackApiError

   class SlackService:
       def __init__(self):
           self.client = WebClient(token=settings.SLACK_BOT_TOKEN)

       async def send_message_to_channel(self, channel, message, blocks=None):
           try:
               response = self.client.chat_postMessage(
                   channel=channel,
                   text=message,
                   blocks=blocks
               )
               return response.data
           except SlackApiError as e:
               logger.error(f"Slack error: {e.response['error']}")
               raise

7. Test Integration:
   - Send test message: await slack.send_message_to_channel("#general", "Test!")
   - Test slash command: /psychsync help in Slack
   - Verify notifications work

For detailed setup, see: SLACK_BOT_SETUP_GUIDE.md
"""

# Global instance
slack_service = SlackServiceStub()
