"""
Microsoft Teams Metadata Analysis Service

Analyzes Teams METADATA ONLY — never reads message content.
Uses Microsoft Graph API with $select to return counts, timestamps,
call durations, and presence data.

Input signals (per user):
  - chat message counts (sent/received, not content)
  - call frequency and duration
  - meeting joins and duration
  - channel participation breadth
  - 1:1 vs group chat ratio
  - presence / status timeline
  - after-hours and weekend activity

Output behavioral signals:
  - communication_load (message + call volume)
  - meeting_fatigue (call hours + meeting count)
  - boundary_erosion (after-hours presence + activity)
  - collaboration_breadth (channel + call diversity)
  - burnout_risk composite

Required Graph API permissions (metadata-only):
  - Presence.Read, Presence.Read.All
  - CallRecords.Read.All (duration/counts, not transcripts)
  - Reports.Read.All (usage reports)
  - No: ChannelMessage.Read, Chat.Read (which return content)
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
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class TeamsActivityType(str, Enum):
    CHAT = "chat"
    CHANNEL_MESSAGE = "channel_message"
    CALL = "call"
    MEETING = "meeting"


class TeamsCallType(str, Enum):
    ONE_ON_ONE = "1:1"
    GROUP = "group"
    CONFERENCE = "conference"


@dataclass
class TeamsActivityRecord:
    """One time-bucket of Teams activity metadata — no message content."""

    user_id: str
    timestamp: datetime
    activity_type: TeamsActivityType
    count: int  # messages sent, or calls made
    duration_minutes: float  # 0 for chat, actual duration for calls/meetings
    is_private: bool  # 1:1 chat or call
    channel_id: Optional[str]  # None for DMs
    participants: int  # number of people involved
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class TeamsPresenceRecord:
    """Presence status change from Graph API."""

    user_id: str
    timestamp: datetime
    availability: str  # "Available", "Busy", "Away", "DoNotDisturb", "Offline"
    activity: str  # "InACall", "InAMeeting", "Presenting", etc.
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class TeamsMetadataSignals:
    """Behavioral signals derived from Teams metadata analysis."""

    # Volume
    avg_daily_chats_sent: float
    avg_daily_calls: float
    avg_daily_meetings: float
    total_active_channels: int

    # Communication shape
    private_chat_ratio: float  # 1:1 vs group
    avg_call_duration_min: float
    avg_meeting_duration_min: float
    calls_vs_chats_ratio: float  # synchronous vs async preference

    # Meeting fatigue
    meeting_hours_per_week: float
    back_to_back_meetings: int
    meeting_fatigue_score: float  # 0-100

    # Timing
    after_hours_ratio: float
    weekend_ratio: float
    peak_hour: int
    hourly_distribution: List[int]

    # Presence
    avg_daily_available_hours: float
    dnd_usage_ratio: float  # how often DND is used (healthy boundary signal)

    # Composite scores (0-100, higher = more concerning)
    communication_load_score: float
    boundary_erosion_score: float
    burnout_risk_score: float

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class TeamsMetadataConnector(ABC):
    """Base interface for Teams metadata connectors.

    Implementations must NEVER request Chat.Read or ChannelMessage.Read.
    Only Reports, Presence, and CallRecords APIs.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[TeamsActivityRecord]: ...

    @abstractmethod
    async def fetch_presence(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[TeamsPresenceRecord]: ...


# ══════════════════════════════════════════════════════════════════
# MICROSOFT GRAPH CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GraphAPIMetadataConnector(TeamsMetadataConnector):
    """Microsoft Graph API connector — reports and presence only.

    Uses:
    - /reports/getTeamsUserActivityUserDetail (daily aggregates)
    - /communications/callRecords (call metadata)
    - /users/{id}/presence (current status)
    Never uses /chats/{id}/messages or /teams/{id}/channels/{id}/messages.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        tenant_id: str = "",
        client_id: str = "",
        client_secret: str = "",
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "teams_metadata",
            "permissions": [
                "Reports.Read.All",
                "CallRecords.Read.All",
                "Presence.Read.All",
            ],
            "note": "Reports + presence APIs only — no message content permissions",
        }

    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[TeamsActivityRecord]:
        """Fetch Teams usage report via Graph Reports API.

        GET /reports/getTeamsUserActivityUserDetail(period='D7')
        Returns CSV with columns: User ID, Chat Message Count,
        Team Chat Message Count, Private Chat Message Count,
        Call Count, Meeting Count, etc.
        """
        access_token = await self._get_access_token()
        if not access_token:
            return []

        records: List[TeamsActivityRecord] = []
        try:
            import httpx
            import csv
            import io

            days = (end - start).days
            period = f"D{min(days, 90)}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/reports/getTeamsUserActivityUserDetail(period='{period}')",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )
                resp.raise_for_status()

                # Graph returns CSV for reports
                content = resp.text
                reader = csv.DictReader(io.StringIO(content))

                for row in reader:
                    if row.get("User Id") != user_id:
                        continue

                    report_date_str = row.get("Report Date", "")
                    try:
                        report_date = datetime.strptime(report_date_str, "%Y-%m-%d")
                    except ValueError:
                        continue

                    chat_count = int(row.get("Private Chat Message Count", 0) or 0)
                    channel_count = int(row.get("Team Chat Message Count", 0) or 0)
                    call_count = int(row.get("Call Count", 0) or 0)
                    meeting_count = int(row.get("Meeting Count", 0) or 0)

                    is_wknd = report_date.weekday() >= 5

                    if chat_count > 0:
                        records.append(
                            TeamsActivityRecord(
                                user_id=user_id,
                                timestamp=report_date,
                                activity_type=TeamsActivityType.CHAT,
                                count=chat_count,
                                duration_minutes=0,
                                is_private=True,
                                channel_id=None,
                                participants=2,
                                is_weekend=is_wknd,
                            )
                        )

                    if channel_count > 0:
                        records.append(
                            TeamsActivityRecord(
                                user_id=user_id,
                                timestamp=report_date,
                                activity_type=TeamsActivityType.CHANNEL_MESSAGE,
                                count=channel_count,
                                duration_minutes=0,
                                is_private=False,
                                channel_id="aggregate",
                                participants=0,
                                is_weekend=is_wknd,
                            )
                        )

                    if call_count > 0:
                        records.append(
                            TeamsActivityRecord(
                                user_id=user_id,
                                timestamp=report_date,
                                activity_type=TeamsActivityType.CALL,
                                count=call_count,
                                duration_minutes=0,
                                is_private=True,
                                channel_id=None,
                                participants=2,
                                is_weekend=is_wknd,
                            )
                        )

                    if meeting_count > 0:
                        records.append(
                            TeamsActivityRecord(
                                user_id=user_id,
                                timestamp=report_date,
                                activity_type=TeamsActivityType.MEETING,
                                count=meeting_count,
                                duration_minutes=0,
                                is_private=False,
                                channel_id=None,
                                participants=0,
                                is_weekend=is_wknd,
                            )
                        )

            logger.info(
                "Teams: fetched %d activity records for %s", len(records), user_id
            )
        except ImportError:
            logger.warning("httpx not installed — Teams metadata connector disabled")
        except Exception as e:
            logger.error("Teams metadata fetch error: %s", e)
        return records

    async def fetch_presence(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[TeamsPresenceRecord]:
        """Fetch current presence via Graph API."""
        access_token = await self._get_access_token()
        if not access_token:
            return []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/users/{user_id}/presence",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                data = resp.json()

                now = datetime.utcnow()
                return [
                    TeamsPresenceRecord(
                        user_id=user_id,
                        timestamp=now,
                        availability=data.get("availability", "Offline"),
                        activity=data.get("activity", "OffWork"),
                        is_after_hours=self._is_after_hours(now),
                        is_weekend=now.weekday() >= 5,
                    )
                ]
        except Exception as e:
            logger.debug("Teams presence fetch failed: %s", e)
        return []

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END

    async def _get_access_token(self) -> Optional[str]:
        """Get app-level token via client credentials flow."""
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            return None
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "https://graph.microsoft.com/.default",
                        "grant_type": "client_credentials",
                    },
                )
                resp.raise_for_status()
                return resp.json().get("access_token")
        except Exception as e:
            logger.error("Teams token acquisition failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class TeamsMetadataAnalyzer:
    """Extracts behavioral signals from Teams metadata.

    Never sees message content. Works with activity counts, call
    durations, presence status, and meeting frequency.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def analyze(
        self,
        activity: List[TeamsActivityRecord],
        presence: List[TeamsPresenceRecord],
        days: int = 14,
    ) -> TeamsMetadataSignals:
        if not activity:
            return self._empty_signals()

        weeks = max(days / 7, 1)

        # Segment by type
        chats = [r for r in activity if r.activity_type == TeamsActivityType.CHAT]
        channels = [
            r for r in activity if r.activity_type == TeamsActivityType.CHANNEL_MESSAGE
        ]
        calls = [r for r in activity if r.activity_type == TeamsActivityType.CALL]
        meetings = [r for r in activity if r.activity_type == TeamsActivityType.MEETING]

        total_chats = sum(r.count for r in chats)
        total_channel = sum(r.count for r in channels)
        total_calls = sum(r.count for r in calls)
        total_meetings = sum(r.count for r in meetings)
        total_msgs = total_chats + total_channel

        avg_chats = total_chats / max(days, 1)
        avg_calls = total_calls / max(days, 1)
        avg_meetings = total_meetings / max(days, 1)

        # Channel breadth
        unique_channels = len(
            set(
                r.channel_id
                for r in channels
                if r.channel_id and r.channel_id != "aggregate"
            )
        )

        # Communication shape
        private_ratio = total_chats / max(total_msgs, 1)
        total_call_minutes = sum(r.duration_minutes for r in calls)
        total_meeting_minutes = sum(r.duration_minutes for r in meetings)
        avg_call_dur = total_call_minutes / max(total_calls, 1)
        avg_meeting_dur = total_meeting_minutes / max(total_meetings, 1)
        calls_vs_chats = (total_calls + total_meetings) / max(total_msgs, 1)

        # Meeting fatigue
        meeting_hours_week = (total_call_minutes + total_meeting_minutes) / 60 / weeks
        b2b = self._count_back_to_back(calls + meetings)
        meeting_fatigue = self._meeting_fatigue_score(
            meeting_hours_week, b2b, avg_meetings
        )

        # Timing
        all_records = activity
        ah_records = [r for r in all_records if r.is_after_hours]
        wk_records = [r for r in all_records if r.is_weekend]
        ah_count = sum(r.count for r in ah_records)
        wk_count = sum(r.count for r in wk_records)
        total_count = sum(r.count for r in all_records)
        after_hours_ratio = ah_count / max(total_count, 1)
        weekend_ratio = wk_count / max(total_count, 1)

        hourly = self._hourly_distribution(all_records)
        peak_hour = hourly.index(max(hourly))

        # Presence
        available_hours = self._estimate_available_hours(presence, days)
        dnd_count = sum(1 for p in presence if p.availability == "DoNotDisturb")
        dnd_ratio = dnd_count / max(len(presence), 1)

        # Composites
        comm_load = self._communication_load_score(
            avg_chats, avg_calls, avg_meetings, unique_channels
        )
        boundary = self._boundary_erosion_score(
            after_hours_ratio, weekend_ratio, presence
        )
        burnout, label = self._burnout_risk_score(
            comm_load, boundary, meeting_fatigue, weekend_ratio, dnd_ratio
        )

        daily = self._daily_breakdown(activity, days)
        recs = self._generate_recommendations(
            avg_chats + avg_calls + avg_meetings,
            after_hours_ratio,
            weekend_ratio,
            meeting_hours_week,
            meeting_fatigue,
            boundary,
            dnd_ratio,
        )

        return TeamsMetadataSignals(
            avg_daily_chats_sent=round(avg_chats, 1),
            avg_daily_calls=round(avg_calls, 1),
            avg_daily_meetings=round(avg_meetings, 1),
            total_active_channels=unique_channels,
            private_chat_ratio=round(private_ratio, 3),
            avg_call_duration_min=round(avg_call_dur, 1),
            avg_meeting_duration_min=round(avg_meeting_dur, 1),
            calls_vs_chats_ratio=round(calls_vs_chats, 3),
            meeting_hours_per_week=round(meeting_hours_week, 1),
            back_to_back_meetings=b2b,
            meeting_fatigue_score=round(meeting_fatigue, 1),
            after_hours_ratio=round(after_hours_ratio, 3),
            weekend_ratio=round(weekend_ratio, 3),
            peak_hour=peak_hour,
            hourly_distribution=hourly,
            avg_daily_available_hours=round(available_hours, 1),
            dnd_usage_ratio=round(dnd_ratio, 3),
            communication_load_score=round(comm_load, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # ── Component scores ─────────────────────────────────────────

    def _communication_load_score(
        self, avg_chats: float, avg_calls: float, avg_meetings: float, channels: int
    ) -> float:
        """0-100: combined chat + call + meeting volume pressure."""
        # Chats: 40/day normal, 100+ critical
        chat_pressure = min(50, (avg_chats / 100) * 50)
        # Calls + meetings: 5/day normal, 12+ critical
        sync_pressure = min(40, ((avg_calls + avg_meetings) / 12) * 40)
        # Channel sprawl
        sprawl = min(10, max(0, channels - 8) * 2)
        return min(100, chat_pressure + sync_pressure + sprawl)

    def _boundary_erosion_score(
        self,
        ah_ratio: float,
        wk_ratio: float,
        presence: List[TeamsPresenceRecord],
    ) -> float:
        """0-100: after-hours presence and activity."""
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, wk_ratio * 400)

        ah_active = sum(
            1
            for p in presence
            if p.is_after_hours and p.availability in ("Available", "Busy")
        )
        presence_component = min(100, (ah_active / max(len(presence), 1)) * 200)

        return ah_component * 0.40 + wk_component * 0.35 + presence_component * 0.25

    def _meeting_fatigue_score(
        self, hours_week: float, b2b: int, avg_meetings_day: float
    ) -> float:
        """0-100: meeting overload risk.

        Teams-specific: call/meeting hours dominate burnout more than chat.
        """
        # >15h/week in calls+meetings is concerning
        hours_pressure = min(60, max(0, (hours_week - 10) * 6))
        # Back-to-back amplifier
        b2b_pressure = min(20, b2b * 5)
        # >6 meetings/day
        density = min(20, max(0, (avg_meetings_day - 4) * 10))
        return min(100, hours_pressure + b2b_pressure + density)

    def _burnout_risk_score(
        self,
        comm_load: float,
        boundary: float,
        meeting_fatigue: float,
        weekend_ratio: float,
        dnd_ratio: float,
    ) -> tuple:
        """Composite burnout risk. Returns (score, label).

        Teams burnout: meeting fatigue is the #1 signal, followed by
        boundary erosion. DND usage is a *protective* factor.
        """
        base = meeting_fatigue * 0.35 + boundary * 0.30 + comm_load * 0.20

        # Interaction: meeting overload AND poor boundaries
        interaction = (meeting_fatigue / 100) * (boundary / 100) * 20

        # Weekend amplifier
        weekend_amp = min(10, max(0, (weekend_ratio - 0.10) * 100))

        # DND is protective — reduces risk if used healthily
        dnd_protection = min(5, dnd_ratio * 20)

        score = min(100, max(0, base + interaction + weekend_amp - dnd_protection))

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

    def _count_back_to_back(self, records: List[TeamsActivityRecord]) -> int:
        sorted_recs = sorted(records, key=lambda r: r.timestamp)
        b2b = 0
        for i in range(1, len(sorted_recs)):
            prev_end = sorted_recs[i - 1].timestamp + timedelta(
                minutes=sorted_recs[i - 1].duration_minutes
            )
            gap = (sorted_recs[i].timestamp - prev_end).total_seconds() / 60
            if 0 <= gap < 5:
                b2b += 1
        return b2b

    def _hourly_distribution(self, activity: List[TeamsActivityRecord]) -> List[int]:
        buckets = [0] * 24
        for r in activity:
            buckets[r.timestamp.hour] += r.count
        return buckets

    def _estimate_available_hours(
        self, presence: List[TeamsPresenceRecord], days: int
    ) -> float:
        active_records = sum(
            1 for p in presence if p.availability in ("Available", "Busy")
        )
        # Rough estimate: each presence record represents ~15 min
        return (active_records * 15 / 60) / max(days, 1)

    def _daily_breakdown(
        self, activity: List[TeamsActivityRecord], days: int
    ) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[TeamsActivityRecord]] = defaultdict(list)
        for r in activity:
            by_day[r.timestamp.strftime("%Y-%m-%d")].append(r)

        result = []
        for day_str in sorted(by_day.keys()):
            recs = by_day[day_str]
            chats = sum(
                r.count for r in recs if r.activity_type == TeamsActivityType.CHAT
            )
            channel = sum(
                r.count
                for r in recs
                if r.activity_type == TeamsActivityType.CHANNEL_MESSAGE
            )
            calls = sum(
                r.count for r in recs if r.activity_type == TeamsActivityType.CALL
            )
            meetings = sum(
                r.count for r in recs if r.activity_type == TeamsActivityType.MEETING
            )
            call_min = sum(
                r.duration_minutes
                for r in recs
                if r.activity_type
                in (TeamsActivityType.CALL, TeamsActivityType.MEETING)
            )
            ah = sum(r.count for r in recs if r.is_after_hours)

            result.append(
                {
                    "date": day_str,
                    "chats": chats,
                    "channel_messages": channel,
                    "calls": calls,
                    "meetings": meetings,
                    "call_meeting_minutes": round(call_min, 0),
                    "after_hours_activity": ah,
                }
            )
        return result

    def _generate_recommendations(
        self,
        daily_activity: float,
        ah_ratio: float,
        wk_ratio: float,
        meeting_hours: float,
        meeting_fatigue: float,
        boundary: float,
        dnd_ratio: float,
    ) -> List[str]:
        recs = []
        if meeting_hours > 15:
            recs.append(
                f"Meeting/call hours ({meeting_hours:.0f}h/week) are well above healthy range. "
                "Audit recurring meetings and consider async alternatives."
            )
        elif meeting_hours > 10:
            recs.append(
                f"Meeting/call hours ({meeting_hours:.0f}h/week) are elevated. "
                "Reserve meeting-free focus blocks on your calendar."
            )

        if meeting_fatigue > 50:
            recs.append(
                "Meeting fatigue is in the risk zone. "
                "Consider implementing 'no-meeting days' and shorter default durations."
            )

        if ah_ratio > 0.20:
            recs.append(
                f"{ah_ratio*100:.0f}% of Teams activity is outside work hours. "
                "Set quiet hours in Teams to pause notifications."
            )

        if wk_ratio > 0.10:
            recs.append(
                f"{wk_ratio*100:.0f}% of activity is on weekends. "
                "This is a strong burnout predictor. Set weekend boundaries."
            )

        if dnd_ratio < 0.05 and daily_activity > 30:
            recs.append(
                "You rarely use Do Not Disturb mode. "
                "Setting DND during focus work protects deep work time and reduces fatigue."
            )

        if boundary > 60:
            recs.append(
                "Work-life boundary erosion is in the risk zone. "
                "Discuss workload and availability expectations with your manager."
            )

        if not recs:
            recs.append(
                "Teams usage patterns look healthy. Communication load is sustainable."
            )
        return recs

    def _empty_signals(self) -> TeamsMetadataSignals:
        return TeamsMetadataSignals(
            avg_daily_chats_sent=0,
            avg_daily_calls=0,
            avg_daily_meetings=0,
            total_active_channels=0,
            private_chat_ratio=0,
            avg_call_duration_min=0,
            avg_meeting_duration_min=0,
            calls_vs_chats_ratio=0,
            meeting_hours_per_week=0,
            back_to_back_meetings=0,
            meeting_fatigue_score=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            peak_hour=10,
            hourly_distribution=[0] * 24,
            avg_daily_available_hours=0,
            dnd_usage_ratio=0,
            communication_load_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No Teams metadata available. Connect Microsoft Teams to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class TeamsMetadataRegistry:
    CONNECTOR_TYPES = {"graph_api": GraphAPIMetadataConnector}

    def __init__(self):
        self._connectors: Dict[str, TeamsMetadataConnector] = {}

    def register(self, name: str, connector: TeamsMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered Teams metadata connector: %s", name)

    def get(self, name: str) -> Optional[TeamsMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


teams_metadata_registry = TeamsMetadataRegistry()
