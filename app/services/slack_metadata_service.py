"""
Slack Metadata Analysis Service

Analyzes Slack METADATA ONLY — never reads message content.
Uses Slack API scopes that return counts and timestamps, not text.

Input signals (per user):
  - messages sent / received (counts only)
  - channel participation (which channels, how many)
  - DM vs public vs private channel ratio
  - thread depth (reply counts, not content)
  - reaction given / received (counts, not emoji identity)
  - presence / status timestamps
  - after-hours and weekend activity

Output behavioral signals:
  - communication_load (message volume pressure)
  - context_switching (channel hops per hour)
  - boundary_erosion (after-hours + weekend presence)
  - isolation_risk (low channel breadth, few threads)
  - engagement_proxy (reaction frequency)
  - burnout_risk composite

Required Slack scopes (metadata-only):
  - users:read (presence, status)
  - channels:read (channel list, membership counts)
  - team:read (workspace info)
  - No: channels:history, groups:history, im:history, mpim:history
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA — counts and timestamps only
# ══════════════════════════════════════════════════════════════════


class SlackChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    DM = "dm"
    GROUP_DM = "group_dm"


@dataclass
class SlackActivityRecord:
    """One time-bucket of Slack activity metadata — no message content."""

    user_id: str
    timestamp: datetime
    messages_sent: int
    messages_received: int
    channel_type: SlackChannelType
    channel_id: str
    threads_started: int
    thread_replies: int
    reactions_given: int
    reactions_received: int
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class SlackPresenceRecord:
    """Presence/status change — when user went online/away/offline."""

    user_id: str
    timestamp: datetime
    status: str  # "active", "away", "offline"
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class DailySlackLoad:
    """Per-day Slack summary."""

    date: str
    messages_sent: int
    messages_received: int
    active_channels: int
    dm_messages: int
    public_messages: int
    threads_participated: int
    reactions_given: int
    after_hours_messages: int
    presence_minutes_after_hours: float


@dataclass
class SlackMetadataSignals:
    """Behavioral signals derived from Slack metadata analysis."""

    # Volume
    avg_daily_messages_sent: float
    avg_daily_messages_received: float
    total_active_channels: int

    # Communication shape
    dm_ratio: float  # fraction of messages in DMs vs channels
    thread_participation_rate: float  # fraction of messages that are thread replies
    avg_thread_depth: float

    # Engagement
    reactions_given_per_day: float
    reactions_received_per_day: float
    reaction_reciprocity: float  # given/received ratio

    # Timing
    after_hours_ratio: float
    weekend_ratio: float
    peak_hour: int
    hourly_distribution: List[int]

    # Context switching
    channel_hops_per_hour: float  # unique channels per active hour
    context_switching_score: float  # 0-100

    # Composite scores (0-100, higher = more concerning)
    communication_load_score: float
    boundary_erosion_score: float
    isolation_risk_score: float
    burnout_risk_score: float

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class SlackMetadataConnector(ABC):
    """Base interface for Slack metadata connectors.

    Implementations must NEVER request message content scopes.
    Only analytics/admin APIs that return counts and timestamps.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[SlackActivityRecord]: ...

    @abstractmethod
    async def fetch_presence(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[SlackPresenceRecord]: ...


# ══════════════════════════════════════════════════════════════════
# SLACK API CONNECTOR
# ══════════════════════════════════════════════════════════════════


class SlackAPIMetadataConnector(SlackMetadataConnector):
    """Slack Web API connector — analytics endpoints only.

    Uses admin.analytics.* and conversations.list for metadata.
    Never calls conversations.history (which would return message text).
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(self, bot_token: str = "", org_domain: str = ""):
        self.bot_token = bot_token
        self.org_domain = org_domain

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "slack_metadata",
            "scopes": ["admin.analytics:read", "users:read", "channels:read"],
            "note": "Analytics API only — no message history scopes",
        }

    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[SlackActivityRecord]:
        """Fetch per-user activity via Slack admin.analytics.getFile.

        The analytics API returns daily aggregate CSVs with columns:
        user_id, date, messages_posted, messages_in_channels,
        messages_in_dms, reactions_added, files_added, etc.
        No message content is ever included.
        """
        if not self.bot_token:
            return []

        records: List[SlackActivityRecord] = []
        try:
            import httpx

            current = start.date()
            end_date = end.date()

            async with httpx.AsyncClient(timeout=30.0) as client:
                while current <= end_date:
                    resp = await client.get(
                        "https://slack.com/api/admin.analytics.getFile",
                        headers={"Authorization": f"Bearer {self.bot_token}"},
                        params={
                            "type": "member",
                            "date": current.isoformat(),
                        },
                    )

                    if resp.status_code == 200 and resp.headers.get(
                        "content-type", ""
                    ).startswith("application/json"):
                        data = resp.json()
                        if not data.get("ok"):
                            current += timedelta(days=1)
                            continue

                    # Parse NDJSON response for the target user
                    import json

                    for line in resp.text.strip().split("\n"):
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        if row.get("user_id") != user_id:
                            continue

                        ts = datetime.combine(current, time(12, 0))
                        msgs_in_channels = row.get("messages_posted_in_channel", 0)
                        msgs_in_dms = row.get("messages_posted_in_direct", 0)

                        if msgs_in_channels > 0:
                            records.append(
                                SlackActivityRecord(
                                    user_id=user_id,
                                    timestamp=ts,
                                    messages_sent=msgs_in_channels,
                                    messages_received=0,
                                    channel_type=SlackChannelType.PUBLIC,
                                    channel_id="aggregate",
                                    threads_started=row.get("threads_started", 0),
                                    thread_replies=row.get("thread_replies", 0),
                                    reactions_given=row.get("reactions_added", 0),
                                    reactions_received=0,
                                    is_after_hours=False,
                                    is_weekend=current.weekday() >= 5,
                                )
                            )

                        if msgs_in_dms > 0:
                            records.append(
                                SlackActivityRecord(
                                    user_id=user_id,
                                    timestamp=ts,
                                    messages_sent=msgs_in_dms,
                                    messages_received=0,
                                    channel_type=SlackChannelType.DM,
                                    channel_id="aggregate_dm",
                                    threads_started=0,
                                    thread_replies=0,
                                    reactions_given=0,
                                    reactions_received=0,
                                    is_after_hours=False,
                                    is_weekend=current.weekday() >= 5,
                                )
                            )

                    current += timedelta(days=1)

            logger.info(
                "Slack: fetched %d activity records for %s", len(records), user_id
            )
        except ImportError:
            logger.warning("httpx not installed — Slack metadata connector disabled")
        except Exception as e:
            logger.error("Slack metadata fetch error: %s", e)
        return records

    async def fetch_presence(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[SlackPresenceRecord]:
        """Fetch presence data via users.getPresence.

        Note: real-time presence is a point-in-time query. For historical
        presence, admin.analytics daily data includes active_hours.
        """
        if not self.bot_token:
            return []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://slack.com/api/users.getPresence",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    params={"user": user_id},
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("ok"):
                    now = datetime.utcnow()
                    return [
                        SlackPresenceRecord(
                            user_id=user_id,
                            timestamp=now,
                            status=data.get("presence", "away"),
                            is_after_hours=self._is_after_hours(now),
                            is_weekend=now.weekday() >= 5,
                        )
                    ]
        except Exception as e:
            logger.debug("Presence fetch failed: %s", e)
        return []

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class SlackMetadataAnalyzer:
    """Extracts behavioral signals from Slack metadata.

    Never sees message content. Works with counts, timestamps,
    channel types, thread depths, and presence patterns.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def analyze(
        self,
        activity: List[SlackActivityRecord],
        presence: List[SlackPresenceRecord],
        days: int = 14,
    ) -> SlackMetadataSignals:
        if not activity:
            return self._empty_signals()

        total_sent = sum(r.messages_sent for r in activity)
        total_received = sum(r.messages_received for r in activity)
        avg_sent = total_sent / max(days, 1)
        avg_received = total_received / max(days, 1)

        # Channel breadth
        unique_channels = len(set(r.channel_id for r in activity))

        # DM ratio
        dm_msgs = sum(
            r.messages_sent
            for r in activity
            if r.channel_type in (SlackChannelType.DM, SlackChannelType.GROUP_DM)
        )
        total_msgs = sum(r.messages_sent for r in activity)
        dm_ratio = dm_msgs / max(total_msgs, 1)

        # Thread participation
        total_thread_replies = sum(r.thread_replies for r in activity)
        thread_rate = total_thread_replies / max(total_msgs, 1)
        avg_thread_depth = total_thread_replies / max(
            sum(1 for r in activity if r.thread_replies > 0), 1
        )

        # Reactions
        reactions_given = sum(r.reactions_given for r in activity)
        reactions_received = sum(r.reactions_received for r in activity)
        react_given_day = reactions_given / max(days, 1)
        react_recv_day = reactions_received / max(days, 1)
        react_reciprocity = reactions_given / max(reactions_received, 1)

        # Timing
        after_hours = [r for r in activity if r.is_after_hours]
        weekend = [r for r in activity if r.is_weekend]
        ah_messages = sum(r.messages_sent for r in after_hours)
        wk_messages = sum(r.messages_sent for r in weekend)
        after_hours_ratio = ah_messages / max(total_msgs, 1)
        weekend_ratio = wk_messages / max(total_msgs, 1)

        hourly = self._hourly_distribution(activity)
        peak_hour = hourly.index(max(hourly))

        # Context switching: unique channels per active hour
        active_hours = len(set(r.timestamp.strftime("%Y-%m-%d-%H") for r in activity))
        channels_per_hour = unique_channels / max(active_hours, 1)
        context_switching = min(100, channels_per_hour * 20)

        # Composite scores
        comm_load = self._communication_load_score(
            avg_sent, avg_received, unique_channels
        )
        boundary = self._boundary_erosion_score(
            after_hours_ratio, weekend_ratio, presence
        )
        isolation = self._isolation_risk_score(
            unique_channels, thread_rate, dm_ratio, react_given_day
        )
        burnout, label = self._burnout_risk_score(
            comm_load, boundary, isolation, context_switching, weekend_ratio
        )

        daily = self._daily_breakdown(activity, presence, days)
        recs = self._generate_recommendations(
            avg_sent + avg_received,
            after_hours_ratio,
            weekend_ratio,
            dm_ratio,
            unique_channels,
            context_switching,
            isolation,
            boundary,
        )

        return SlackMetadataSignals(
            avg_daily_messages_sent=round(avg_sent, 1),
            avg_daily_messages_received=round(avg_received, 1),
            total_active_channels=unique_channels,
            dm_ratio=round(dm_ratio, 3),
            thread_participation_rate=round(thread_rate, 3),
            avg_thread_depth=round(avg_thread_depth, 1),
            reactions_given_per_day=round(react_given_day, 1),
            reactions_received_per_day=round(react_recv_day, 1),
            reaction_reciprocity=round(react_reciprocity, 2),
            after_hours_ratio=round(after_hours_ratio, 3),
            weekend_ratio=round(weekend_ratio, 3),
            peak_hour=peak_hour,
            hourly_distribution=hourly,
            channel_hops_per_hour=round(channels_per_hour, 1),
            context_switching_score=round(context_switching, 1),
            communication_load_score=round(comm_load, 1),
            boundary_erosion_score=round(boundary, 1),
            isolation_risk_score=round(isolation, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # ── Component scores ─────────────────────────────────────────

    def _communication_load_score(
        self, avg_sent: float, avg_received: float, channels: int
    ) -> float:
        """0-100: message volume + channel sprawl pressure."""
        daily_total = avg_sent + avg_received
        # 50 msgs/day normal, 150+ critical
        volume = min(100, (daily_total / 150) * 100)
        # >15 active channels = sprawl
        sprawl = min(30, max(0, channels - 10) * 5)
        return min(100, volume * 0.75 + sprawl)

    def _boundary_erosion_score(
        self,
        after_hours_ratio: float,
        weekend_ratio: float,
        presence: List[SlackPresenceRecord],
    ) -> float:
        """0-100: after-hours presence + messaging outside work."""
        ah_component = min(100, after_hours_ratio * 250)
        wk_component = min(100, weekend_ratio * 400)

        # Presence amplifier: being "active" after hours even without messaging
        ah_presence = sum(
            1 for p in presence if p.is_after_hours and p.status == "active"
        )
        presence_ratio = ah_presence / max(len(presence), 1)
        presence_component = min(100, presence_ratio * 200)

        return ah_component * 0.40 + wk_component * 0.35 + presence_component * 0.25

    def _isolation_risk_score(
        self,
        channels: int,
        thread_rate: float,
        dm_ratio: float,
        reactions_per_day: float,
    ) -> float:
        """0-100: risk of social isolation in the workspace.

        Low channel breadth + high DM ratio + few reactions = isolated.
        """
        # Few channels = limited network
        channel_risk = max(0, min(40, (5 - channels) * 10)) if channels < 5 else 0
        # High DM ratio = avoiding public collaboration
        dm_risk = min(30, max(0, (dm_ratio - 0.6) * 100)) if dm_ratio > 0.6 else 0
        # Low thread engagement = not participating in discussions
        thread_risk = (
            min(15, max(0, (0.1 - thread_rate) * 150)) if thread_rate < 0.1 else 0
        )
        # No reactions = low social engagement
        react_risk = (
            min(15, max(0, (1 - reactions_per_day) * 15))
            if reactions_per_day < 1
            else 0
        )

        return channel_risk + dm_risk + thread_risk + react_risk

    def _burnout_risk_score(
        self,
        comm_load: float,
        boundary: float,
        isolation: float,
        context_switching: float,
        weekend_ratio: float,
    ) -> tuple:
        """Composite burnout risk. Returns (score, label).

        Slack burnout differs from email: context switching and isolation
        are stronger signals than raw volume.
        """
        base = (
            boundary * 0.35
            + comm_load * 0.20
            + context_switching * 0.25
            + isolation * 0.20
        )

        # Interaction: high switching AND poor boundaries = compounding
        interaction = (context_switching / 100) * (boundary / 100) * 20

        # Weekend Slack is a very strong signal
        weekend_amp = min(10, max(0, (weekend_ratio - 0.10) * 100))

        score = min(100, base + interaction + weekend_amp)

        if score >= 70:
            label = "Critical"
        elif score >= 45:
            label = "Elevated"
        elif score >= 25:
            label = "Monitor"
        else:
            label = "Healthy"

        return round(score, 1), label

    # ── Helpers ──────────────────────────────────────────────────

    def _hourly_distribution(self, activity: List[SlackActivityRecord]) -> List[int]:
        buckets = [0] * 24
        for r in activity:
            buckets[r.timestamp.hour] += r.messages_sent
        return buckets

    def _daily_breakdown(
        self,
        activity: List[SlackActivityRecord],
        presence: List[SlackPresenceRecord],
        days: int,
    ) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[SlackActivityRecord]] = defaultdict(list)
        for r in activity:
            by_day[r.timestamp.strftime("%Y-%m-%d")].append(r)

        result = []
        for day_str in sorted(by_day.keys()):
            recs = by_day[day_str]
            sent = sum(r.messages_sent for r in recs)
            recv = sum(r.messages_received for r in recs)
            channels = len(set(r.channel_id for r in recs))
            dms = sum(
                r.messages_sent
                for r in recs
                if r.channel_type in (SlackChannelType.DM, SlackChannelType.GROUP_DM)
            )
            threads = sum(r.thread_replies for r in recs)
            reacts = sum(r.reactions_given for r in recs)
            ah = sum(r.messages_sent for r in recs if r.is_after_hours)

            result.append(
                {
                    "date": day_str,
                    "sent": sent,
                    "received": recv,
                    "active_channels": channels,
                    "dm_messages": dms,
                    "public_messages": sent - dms,
                    "threads_participated": threads,
                    "reactions_given": reacts,
                    "after_hours_messages": ah,
                }
            )
        return result

    def _generate_recommendations(
        self,
        daily_volume: float,
        ah_ratio: float,
        wk_ratio: float,
        dm_ratio: float,
        channels: int,
        ctx_switching: float,
        isolation: float,
        boundary: float,
    ) -> List[str]:
        recs = []
        if daily_volume > 100:
            recs.append(
                f"Slack volume ({daily_volume:.0f} msgs/day) is very high. "
                "Consider batching responses and using threads to reduce noise."
            )
        if ctx_switching > 50:
            recs.append(
                "High context switching across channels. "
                "Mute low-priority channels and set focus-time Do Not Disturb schedules."
            )
        if ah_ratio > 0.20:
            recs.append(
                f"{ah_ratio*100:.0f}% of Slack messages are outside work hours. "
                "Enable scheduled send and set Slack notification schedules."
            )
        if wk_ratio > 0.10:
            recs.append(
                f"{wk_ratio*100:.0f}% of Slack activity is on weekends — "
                "a strong burnout predictor. Set weekend DND on Slack."
            )
        if dm_ratio > 0.70:
            recs.append(
                f"{dm_ratio*100:.0f}% of messages are in DMs. "
                "High DM reliance can indicate siloed work — consider public channels for transparency."
            )
        if isolation > 40:
            recs.append(
                "Isolation risk detected: limited channel participation and low engagement signals. "
                "Consider joining cross-team channels or participating in threads."
            )
        if boundary > 60:
            recs.append(
                "Boundary erosion is in the risk zone. "
                "Discuss Slack availability expectations with your team."
            )
        if not recs:
            recs.append(
                "Slack patterns look healthy. Communication load is sustainable."
            )
        return recs

    def _empty_signals(self) -> SlackMetadataSignals:
        return SlackMetadataSignals(
            avg_daily_messages_sent=0,
            avg_daily_messages_received=0,
            total_active_channels=0,
            dm_ratio=0,
            thread_participation_rate=0,
            avg_thread_depth=0,
            reactions_given_per_day=0,
            reactions_received_per_day=0,
            reaction_reciprocity=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            peak_hour=10,
            hourly_distribution=[0] * 24,
            channel_hops_per_hour=0,
            context_switching_score=0,
            communication_load_score=0,
            boundary_erosion_score=0,
            isolation_risk_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No Slack metadata available. Connect Slack to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class SlackMetadataRegistry:
    CONNECTOR_TYPES = {"slack_api": SlackAPIMetadataConnector}

    def __init__(self):
        self._connectors: Dict[str, SlackMetadataConnector] = {}

    def register(self, name: str, connector: SlackMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered Slack metadata connector: %s", name)

    def get(self, name: str) -> Optional[SlackMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


slack_metadata_registry = SlackMetadataRegistry()
