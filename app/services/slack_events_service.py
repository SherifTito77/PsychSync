# app/services/slack_events_service.py
"""
Slack Events API Webhook Handler

Receives real-time events from Slack (message metadata, reactions,
channel membership) and stores behavioral signals. No message content
is stored — metadata only.

Setup: Configure Slack app with Events API subscriptions:
  - message.channels (public channel messages)
  - message.groups (private channel messages)
  - reaction_added / reaction_removed
  - member_joined_channel / member_left_channel
"""

import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Work hours: 9-18, Mon-Fri
WORK_HOURS = (9, 18)
WORK_DAYS = {0, 1, 2, 3, 4}


class SlackEventsService:
    """Processes Slack Events API webhooks into behavioral signals."""

    def __init__(self, signing_secret: Optional[str] = None):
        self.signing_secret = signing_secret

    def verify_request(self, body: bytes, timestamp: str, signature: str) -> bool:
        """
        Verify Slack request signature.
        See: https://api.slack.com/authentication/verifying-requests-from-slack
        """
        if not self.signing_secret:
            logger.warning("No Slack signing secret configured — skipping verification")
            return True

        # Reject requests older than 5 minutes
        if abs(time.time() - float(timestamp)) > 300:
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        computed = (
            "v0="
            + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        return hmac.compare_digest(computed, signature)

    async def process_event(
        self, db: AsyncSession, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a Slack event payload.

        Returns action taken (for logging/monitoring).
        """
        event_type = payload.get("type")

        # URL verification challenge (initial setup)
        if event_type == "url_verification":
            return {"challenge": payload.get("challenge")}

        if event_type != "event_callback":
            return {"status": "ignored", "type": event_type}

        event = payload.get("event", {})
        inner_type = event.get("type")

        if inner_type in ("message", "message.channels", "message.groups"):
            return await self._handle_message(db, event, payload)
        elif inner_type == "reaction_added":
            return await self._handle_reaction(db, event, payload)
        elif inner_type == "member_joined_channel":
            return await self._handle_member_change(db, event, payload, joined=True)
        elif inner_type == "member_left_channel":
            return await self._handle_member_change(db, event, payload, joined=False)

        return {"status": "unhandled", "type": inner_type}

    async def _handle_message(
        self, db: AsyncSession, event: Dict, payload: Dict
    ) -> Dict[str, Any]:
        """Extract metadata from a message event. No content stored."""
        # Skip bot messages, message_changed, etc.
        subtype = event.get("subtype")
        if subtype in (
            "bot_message",
            "message_changed",
            "message_deleted",
            "channel_join",
            "channel_leave",
        ):
            return {"status": "skipped", "reason": subtype}

        user_id = event.get("user")
        if not user_id:
            return {"status": "skipped", "reason": "no_user"}

        ts = event.get("ts", "")
        try:
            event_time = datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (ValueError, TypeError):
            event_time = datetime.now(timezone.utc)

        text = event.get("text", "")
        channel = event.get("channel", "")

        metadata = {
            "slack_user_id": user_id,
            "channel_id": channel,
            "timestamp": event_time.isoformat(),
            "word_count": len(text.split()) if text else 0,
            "has_mentions": "<@" in text,
            "has_links": "http" in text,
            "has_attachments": bool(event.get("files")),
            "is_thread_reply": "thread_ts" in event and event.get("thread_ts") != ts,
            "is_thread_starter": "thread_ts" not in event
            or event.get("thread_ts") == ts,
            "is_after_hours": event_time.hour < WORK_HOURS[0]
            or event_time.hour >= WORK_HOURS[1],
            "is_weekend": event_time.weekday() not in WORK_DAYS,
            "hour_of_day": event_time.hour,
            "day_of_week": event_time.weekday(),
            "team_id": payload.get("team_id"),
        }

        # Store as SlackMessage in DB
        await self._store_message_metadata(db, metadata)

        return {"status": "processed", "type": "message", "channel": channel}

    async def _handle_reaction(
        self, db: AsyncSession, event: Dict, payload: Dict
    ) -> Dict[str, Any]:
        """Track reaction patterns (emoji sentiment, not content)."""
        reaction = event.get("reaction", "")
        user = event.get("user", "")
        item_user = event.get("item_user", "")

        # Classify reaction sentiment
        positive_emojis = {
            "thumbsup",
            "+1",
            "heart",
            "star",
            "tada",
            "clap",
            "raised_hands",
            "100",
            "fire",
            "rocket",
            "trophy",
        }
        negative_emojis = {
            "thumbsdown",
            "-1",
            "cry",
            "disappointed",
            "angry",
            "rage",
            "face_palm",
            "skull",
        }

        sentiment = "neutral"
        if reaction in positive_emojis:
            sentiment = "positive"
        elif reaction in negative_emojis:
            sentiment = "negative"

        metadata = {
            "reactor_slack_id": user,
            "author_slack_id": item_user,
            "reaction": reaction,
            "sentiment": sentiment,
            "team_id": payload.get("team_id"),
        }

        await self._store_reaction_metadata(db, metadata)
        return {"status": "processed", "type": "reaction", "sentiment": sentiment}

    async def _handle_member_change(
        self, db: AsyncSession, event: Dict, payload: Dict, joined: bool
    ) -> Dict[str, Any]:
        """Track channel membership changes for network edge generation."""
        user = event.get("user", "")
        channel = event.get("channel", "")

        logger.info(
            "Slack member %s channel %s: user=%s",
            "joined" if joined else "left",
            channel,
            user,
        )
        return {
            "status": "processed",
            "type": "member_joined" if joined else "member_left",
            "channel": channel,
        }

    async def _store_message_metadata(self, db: AsyncSession, metadata: Dict) -> None:
        """Persist message metadata to the slack_messages table."""
        try:
            from app.db.models.integrations import SlackMessage as SlackMessageModel

            msg = SlackMessageModel(
                user_id=metadata.get("slack_user_id"),
                channel_id=metadata.get("channel_id"),
                timestamp=metadata.get("timestamp"),
                word_count=metadata.get("word_count", 0),
                has_mentions=metadata.get("has_mentions", False),
                is_after_hours=metadata.get("is_after_hours", False),
                is_weekend=metadata.get("is_weekend", False),
                message_type=(
                    "thread_reply" if metadata.get("is_thread_reply") else "message"
                ),
            )
            db.add(msg)
            await db.flush()
        except Exception as e:
            logger.debug("Could not store Slack message metadata: %s", e)

    async def _store_reaction_metadata(self, db: AsyncSession, metadata: Dict) -> None:
        """Store reaction metadata for sentiment tracking."""
        # Reactions are lightweight — store in the existing SlackMessage table
        # with a special message_type or use a separate reactions column
        logger.debug("Reaction tracked: %s", metadata.get("reaction"))


# Singleton
slack_events_service = SlackEventsService()
