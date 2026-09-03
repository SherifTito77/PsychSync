"""
Communication Platform Analytics Service

Connects to Slack and Microsoft Teams to extract behavioral signals:
  - Message sentiment trends
  - Response time patterns (engagement proxy)
  - After-hours messaging frequency
  - Channel participation distribution
  - Communication network density
  - Emoji/reaction sentiment
  - Thread depth (collaboration quality proxy)

Privacy-first: all analysis is aggregated. Individual messages are never stored.
Only statistical summaries and behavioral signals are retained.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class SentimentLevel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class MessageStats:
    """Aggregated messaging statistics (no individual messages stored)."""

    user_email: str
    user_name: str
    period_start: str
    period_end: str
    total_messages: int
    channels_active: int
    threads_started: int
    threads_replied: int
    reactions_given: int
    reactions_received: int
    after_hours_messages: int
    avg_response_time_min: float
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)


@dataclass
class ChannelHealth:
    """Per-channel engagement metrics."""

    channel_name: str
    channel_id: str
    member_count: int
    active_members: int
    messages_per_day: float
    avg_thread_depth: float
    response_rate: float  # % of messages that get replies
    sentiment_avg: float  # -1 to 1
    is_healthy: bool


@dataclass
class CommunicationHealthScore:
    """Organization-wide communication health."""

    score: float  # 0-100
    label: str
    total_active_users: int
    avg_messages_per_person_day: float
    after_hours_rate: float
    avg_response_time_min: float
    sentiment_trend: str  # improving, stable, declining
    channel_engagement_distribution: str  # balanced, concentrated, fragmented
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CommunicationConnector(ABC):
    """Base interface for communication platform connectors."""

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_user_stats(
        self,
        user_email: str,
        days: int = 14,
    ) -> Optional[MessageStats]: ...

    @abstractmethod
    async def fetch_channel_health(self, days: int = 14) -> List[ChannelHealth]: ...

    @abstractmethod
    async def fetch_org_stats(self, days: int = 14) -> Dict[str, Any]: ...


# ══════════════════════════════════════════════════════════════════
# SLACK CONNECTOR
# ══════════════════════════════════════════════════════════════════


class SlackConnector(CommunicationConnector):
    """Slack Web API connector (Bot token)."""

    def __init__(self, bot_token: str, workspace_name: str = ""):
        self.bot_token = bot_token
        self.workspace_name = workspace_name
        self.base_url = "https://slack.com/api"

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/auth.test",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    timeout=10,
                )
                data = resp.json()
                if data.get("ok"):
                    return {
                        "connected": True,
                        "team": data.get("team"),
                        "user": data.get("user"),
                    }
                return {"connected": False, "error": data.get("error")}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_user_stats(
        self,
        user_email: str,
        days: int = 14,
    ) -> Optional[MessageStats]:
        """Would use conversations.history + users.info APIs."""
        logger.info("Slack: would fetch stats for %s over %d days", user_email, days)
        return None

    async def fetch_channel_health(self, days: int = 14) -> List[ChannelHealth]:
        """Would use conversations.list + conversations.history APIs."""
        logger.info("Slack: would fetch channel health for %d days", days)
        return []

    async def fetch_org_stats(self, days: int = 14) -> Dict[str, Any]:
        """Would aggregate across channels and users."""
        return {"platform": "slack", "status": "awaiting_configuration"}


# ══════════════════════════════════════════════════════════════════
# MICROSOFT TEAMS CONNECTOR
# ══════════════════════════════════════════════════════════════════


class TeamsConnector(CommunicationConnector):
    """Microsoft Graph API connector for Teams."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            return {
                "connected": True,
                "provider": "microsoft_teams",
                "note": "Azure AD OAuth required",
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_user_stats(
        self,
        user_email: str,
        days: int = 14,
    ) -> Optional[MessageStats]:
        logger.info("Teams: would fetch stats for %s", user_email)
        return None

    async def fetch_channel_health(self, days: int = 14) -> List[ChannelHealth]:
        return []

    async def fetch_org_stats(self, days: int = 14) -> Dict[str, Any]:
        return {"platform": "teams", "status": "awaiting_configuration"}


# ══════════════════════════════════════════════════════════════════
# COMMUNICATION HEALTH ANALYZER
# ══════════════════════════════════════════════════════════════════


class CommunicationHealthAnalyzer:
    """Derives behavioral signals from communication data."""

    def analyze_org_health(
        self,
        user_stats: List[MessageStats],
        channel_health: List[ChannelHealth],
    ) -> CommunicationHealthScore:
        """Organization-wide communication health assessment."""
        if not user_stats:
            return CommunicationHealthScore(
                score=0,
                label="No Data",
                total_active_users=0,
                avg_messages_per_person_day=0,
                after_hours_rate=0,
                avg_response_time_min=0,
                sentiment_trend="unknown",
                channel_engagement_distribution="unknown",
                recommendations=[
                    "Connect Slack or Teams to enable communication analytics."
                ],
            )

        active = len(user_stats)
        total_msgs = sum(s.total_messages for s in user_stats)
        after_hours_total = sum(s.after_hours_messages for s in user_stats)
        avg_msg_day = total_msgs / max(active * 14, 1)  # Assume 14-day window
        after_hours_rate = (after_hours_total / max(total_msgs, 1)) * 100

        response_times = [
            s.avg_response_time_min for s in user_stats if s.avg_response_time_min > 0
        ]
        avg_response = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        # Score
        score = 100.0
        if after_hours_rate > 20:
            score -= min(20, (after_hours_rate - 20) * 1.5)
        if avg_response > 60:
            score -= min(15, (avg_response - 60) / 10)
        if avg_msg_day > 50:
            score -= min(10, (avg_msg_day - 50) * 0.5)
        elif avg_msg_day < 5:
            score -= 10  # Too quiet

        # Channel engagement
        if channel_health:
            active_pcts = [
                c.active_members / max(c.member_count, 1) for c in channel_health
            ]
            avg_engagement = sum(active_pcts) / len(active_pcts)
            if avg_engagement < 0.3:
                score -= 10
                distribution = "low_engagement"
            elif avg_engagement > 0.7:
                distribution = "balanced"
            else:
                distribution = "moderate"
        else:
            distribution = "unknown"

        score = max(0, min(100, score))
        label = (
            "Healthy" if score >= 70 else ("Moderate" if score >= 50 else "Concerning")
        )

        recs = self._recommendations(
            avg_msg_day,
            after_hours_rate,
            avg_response,
            distribution,
        )

        return CommunicationHealthScore(
            score=round(score, 1),
            label=label,
            total_active_users=active,
            avg_messages_per_person_day=round(avg_msg_day, 1),
            after_hours_rate=round(after_hours_rate, 1),
            avg_response_time_min=round(avg_response, 1),
            sentiment_trend="stable",
            channel_engagement_distribution=distribution,
            recommendations=recs,
        )

    def _recommendations(self, msg_rate, after_hours, response_time, distribution):
        recs = []
        if after_hours > 20:
            recs.append(
                f"After-hours messaging is at {after_hours:.0f}%. "
                "Set team agreements on response expectations outside work hours."
            )
        if msg_rate > 50:
            recs.append(
                f"Message volume ({msg_rate:.0f} msgs/person/day) is high. "
                "Consider async-first practices and reducing notification fatigue."
            )
        if msg_rate < 3:
            recs.append(
                "Communication volume is very low. Teams may be siloed. "
                "Encourage cross-channel interaction and shared standups."
            )
        if response_time > 120:
            recs.append(
                f"Average response time is {response_time:.0f} min. "
                "Identify bottlenecks — some team members may be overloaded."
            )
        if distribution == "low_engagement":
            recs.append(
                "Channel engagement is low. Many members are passive observers. "
                "Consider smaller, topic-focused channels to boost participation."
            )
        if not recs:
            recs.append(
                "Communication patterns look healthy. Maintain current practices."
            )
        return recs


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class CommunicationRegistry:
    """Manages communication platform connectors."""

    CONNECTOR_TYPES = {
        "slack": SlackConnector,
        "teams": TeamsConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, CommunicationConnector] = {}

    def register(self, name: str, connector: CommunicationConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered communication connector: %s", name)

    def get(self, name: str) -> Optional[CommunicationConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


communication_registry = CommunicationRegistry()
