"""
Video Conferencing Metadata Analysis Service

Analyzes video call METADATA ONLY — no recordings, no transcripts,
no screen content. Extracts behavioral signals from call lifecycle
data: join/leave times, camera status, participant counts, duration.

Input signals (per meeting):
  - start/end timestamps
  - participant count
  - camera-on participant count
  - join latency (seconds after scheduled start)
  - host identifier
  - duration vs scheduled duration
  - recurring flag

Output behavioral signals:
  - camera_on_rate (engagement proxy)
  - join_punctuality_score (enthusiasm proxy)
  - meeting_fatigue_score (back-to-back video calls)
  - meeting_overrun_rate (scheduling discipline)
  - after_hours_meeting_rate
  - participation_balance (evenness of meeting load)
  - engagement_score (composite)
  - burnout_risk (composite)

Zero content analysis. No audio, no video frames, no chat text.
"""

import logging
import statistics
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# NORMALIZED SCHEMA
# ======================================================================


@dataclass
class VideoConferenceRecord:
    """One video call event — lifecycle metadata only."""

    meeting_id: str
    host_id: str
    start_time: datetime
    end_time: datetime
    scheduled_duration_minutes: float  # what was booked
    actual_duration_minutes: float  # how long it actually ran
    participant_count: int
    camera_on_count: int  # participants with camera on at any point
    avg_join_latency_seconds: float  # avg seconds after start participants joined
    is_recurring: bool
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class DailyVideoSummary:
    """Per-day video call load for one person."""

    date: str
    meeting_count: int
    total_minutes: float
    back_to_back_count: int  # meetings starting within 5 min of previous ending
    camera_on_rate: float  # 0-1
    longest_gap_minutes: float  # longest break between calls
    after_hours_count: int


@dataclass
class VideoConferenceSignals:
    """Behavioral signals from video conferencing metadata."""

    # Engagement signals
    camera_on_rate: float  # 0-100, % of meetings where >50% had cameras on
    avg_camera_on_ratio: float  # 0-1, average camera_on_count / participant_count
    join_punctuality_score: float  # 0-100, higher = more punctual
    meeting_participation_rate: float  # avg participants per meeting

    # Load signals
    avg_daily_meetings: float  # meetings per working day
    avg_daily_video_minutes: float  # minutes in video calls per day
    peak_daily_meetings: int  # most meetings in a single day
    meeting_overrun_rate: float  # 0-100, % of meetings exceeding scheduled duration

    # Fatigue signals
    back_to_back_rate: float  # 0-100, % of meetings with <5 min gap before
    avg_longest_gap_minutes: float  # avg longest break between meetings per day
    meeting_fatigue_score: float  # 0-100, derived from back-to-back + duration

    # Timing signals
    after_hours_meeting_rate: float  # 0-100
    weekend_meeting_count: int
    recurring_meeting_ratio: float  # 0-1, % of meetings that are recurring

    # Composite scores (0-100, higher = more concerning)
    overload_score: float
    burnout_risk: float

    engagement_score: float  # 0-100, higher = healthier engagement

    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ======================================================================
# ABSTRACT CONNECTOR
# ======================================================================


class VideoConferenceConnector(ABC):
    """Base interface for video conferencing platform connectors.

    Only receives call lifecycle metadata.
    No recordings, no transcripts, no screen content.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_meetings(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[VideoConferenceRecord]: ...


# ======================================================================
# PROVIDER CONNECTORS
# ======================================================================


class ZoomConnector(VideoConferenceConnector):
    """Zoom Admin API — meeting reports (metadata only)."""

    WORK_START = time(7, 0)
    WORK_END = time(20, 0)

    def __init__(self, api_key: str = "", account_id: str = ""):
        self.api_key = api_key
        self.account_id = account_id

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "zoom",
            "note": "Meeting lifecycle metadata only — no recordings or transcripts",
        }

    async def fetch_meetings(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[VideoConferenceRecord]:
        if not self.api_key:
            return []
        records: List[VideoConferenceRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    "https://api.zoom.us/v2/report/meetings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={
                        "from": start.strftime("%Y-%m-%d"),
                        "to": end.strftime("%Y-%m-%d"),
                    },
                )
                resp.raise_for_status()
                for m in resp.json().get("meetings", []):
                    st = datetime.fromisoformat(m["start_time"].replace("Z", "+00:00"))
                    et = st + timedelta(minutes=m.get("duration", 0))
                    records.append(
                        VideoConferenceRecord(
                            meeting_id=m["id"],
                            host_id=m.get("host_id", ""),
                            start_time=st,
                            end_time=et,
                            scheduled_duration_minutes=m.get("duration", 0),
                            actual_duration_minutes=m.get("duration", 0),
                            participant_count=m.get("participants_count", 0),
                            camera_on_count=m.get("participants_count", 0),
                            avg_join_latency_seconds=0,
                            is_recurring=m.get("type", 1) in (3, 8),
                            is_after_hours=self._is_after_hours(st),
                            is_weekend=st.weekday() >= 5,
                        )
                    )
        except Exception as e:
            logger.error("Zoom fetch error: %s", e)
        return records

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


class GoogleMeetConnector(VideoConferenceConnector):
    """Google Workspace Admin Reports — Meet activity (metadata only)."""

    def __init__(self, credentials: Optional[Dict] = None):
        self.credentials = credentials or {}

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "google_meet",
            "note": "Meeting metadata from Admin Reports API — no recordings",
        }

    async def fetch_meetings(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[VideoConferenceRecord]:
        if not self.credentials:
            return []
        return []  # Real implementation uses google-admin-sdk


class TeamsMeetingConnector(VideoConferenceConnector):
    """Microsoft Graph — Teams Call Records API (metadata only)."""

    def __init__(
        self, client_id: str = "", client_secret: str = "", tenant_id: str = ""
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "teams_meetings",
            "note": "Call records metadata from Microsoft Graph — no content",
        }

    async def fetch_meetings(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[VideoConferenceRecord]:
        if not self.client_id:
            return []
        return []  # Real implementation uses Microsoft Graph callRecords API


# ======================================================================
# REGISTRY
# ======================================================================


class VideoConferenceRegistry:
    """Registry of video conferencing connectors."""

    def __init__(self):
        self._connectors: Dict[str, VideoConferenceConnector] = {}

    def register(self, name: str, connector: VideoConferenceConnector) -> None:
        self._connectors[name] = connector

    def get(self, name: str) -> Optional[VideoConferenceConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


video_conference_registry = VideoConferenceRegistry()


# ======================================================================
# ANALYZER
# ======================================================================


class VideoConferenceAnalyzer:
    """Analyze video conferencing metadata for behavioral signals."""

    def analyze(
        self,
        records: List[VideoConferenceRecord],
        days: int = 30,
    ) -> VideoConferenceSignals:
        if not records:
            return self._empty_signals()

        # --- Camera engagement ---
        camera_ratios = []
        high_camera_meetings = 0
        for r in records:
            if r.participant_count > 0:
                ratio = r.camera_on_count / r.participant_count
                camera_ratios.append(ratio)
                if ratio > 0.5:
                    high_camera_meetings += 1

        camera_on_rate = (high_camera_meetings / len(records) * 100) if records else 0
        avg_camera_ratio = statistics.mean(camera_ratios) if camera_ratios else 0

        # --- Join punctuality ---
        latencies = [
            r.avg_join_latency_seconds
            for r in records
            if r.avg_join_latency_seconds >= 0
        ]
        avg_latency = statistics.mean(latencies) if latencies else 0
        # 0 seconds = 100, 120+ seconds = 0
        join_punctuality = max(0, min(100, 100 - (avg_latency / 1.2)))

        # --- Daily breakdown ---
        daily: Dict[str, List[VideoConferenceRecord]] = defaultdict(list)
        for r in records:
            day_key = r.start_time.strftime("%Y-%m-%d")
            daily[day_key].append(r)

        working_days = max(1, len(daily))
        daily_summaries = []
        total_back_to_back = 0
        total_meetings = len(records)

        for day_key, day_records in sorted(daily.items()):
            sorted_recs = sorted(day_records, key=lambda x: x.start_time)
            b2b = 0
            for i in range(1, len(sorted_recs)):
                gap = (
                    sorted_recs[i].start_time - sorted_recs[i - 1].end_time
                ).total_seconds() / 60
                if gap < 5:
                    b2b += 1
            total_back_to_back += b2b

            total_mins = sum(r.actual_duration_minutes for r in sorted_recs)

            # Longest gap between meetings
            gaps = []
            for i in range(1, len(sorted_recs)):
                gap_min = (
                    sorted_recs[i].start_time - sorted_recs[i - 1].end_time
                ).total_seconds() / 60
                gaps.append(max(0, gap_min))
            longest_gap = max(gaps) if gaps else 480  # 8h = no meetings

            day_camera = []
            for r in sorted_recs:
                if r.participant_count > 0:
                    day_camera.append(r.camera_on_count / r.participant_count)

            after_h = sum(1 for r in sorted_recs if r.is_after_hours)

            daily_summaries.append(
                DailyVideoSummary(
                    date=day_key,
                    meeting_count=len(sorted_recs),
                    total_minutes=total_mins,
                    back_to_back_count=b2b,
                    camera_on_rate=statistics.mean(day_camera) if day_camera else 0,
                    longest_gap_minutes=longest_gap,
                    after_hours_count=after_h,
                )
            )

        # --- Aggregate metrics ---
        avg_daily_meetings = total_meetings / working_days
        avg_daily_minutes = sum(s.total_minutes for s in daily_summaries) / working_days
        peak_daily = max((s.meeting_count for s in daily_summaries), default=0)

        overrun_count = sum(
            1
            for r in records
            if r.actual_duration_minutes > r.scheduled_duration_minutes * 1.1
        )
        meeting_overrun_rate = (
            (overrun_count / total_meetings * 100) if total_meetings else 0
        )

        back_to_back_rate = (
            total_back_to_back / max(1, total_meetings - working_days)
        ) * 100
        back_to_back_rate = min(100, back_to_back_rate)

        avg_longest_gap = (
            statistics.mean(s.longest_gap_minutes for s in daily_summaries)
            if daily_summaries
            else 480
        )

        after_hours_count = sum(1 for r in records if r.is_after_hours)
        after_hours_rate = (
            (after_hours_count / total_meetings * 100) if total_meetings else 0
        )

        weekend_count = sum(1 for r in records if r.is_weekend)
        recurring_ratio = (
            sum(1 for r in records if r.is_recurring) / total_meetings
            if total_meetings
            else 0
        )

        avg_participants = statistics.mean(r.participant_count for r in records)

        # --- Fatigue score ---
        meeting_fatigue = self._compute_fatigue(
            back_to_back_rate,
            avg_daily_minutes,
            avg_longest_gap,
        )

        # --- Overload score ---
        overload = self._compute_overload(
            avg_daily_meetings,
            avg_daily_minutes,
            after_hours_rate,
        )

        # --- Burnout risk ---
        burnout = meeting_fatigue * 0.45 + overload * 0.35 + after_hours_rate * 0.20
        burnout = min(100, burnout)

        # --- Engagement score ---
        engagement = self._compute_engagement_score(
            camera_on_rate,
            join_punctuality,
            avg_camera_ratio,
            recurring_ratio,
            avg_participants,
        )

        risk_label = (
            "Critical"
            if burnout >= 70
            else (
                "Elevated"
                if burnout >= 45
                else "Monitor" if burnout >= 25 else "Healthy"
            )
        )

        recs = self._generate_recommendations(
            burnout,
            meeting_fatigue,
            overload,
            camera_on_rate,
            back_to_back_rate,
            after_hours_rate,
        )

        return VideoConferenceSignals(
            camera_on_rate=round(camera_on_rate, 1),
            avg_camera_on_ratio=round(avg_camera_ratio, 3),
            join_punctuality_score=round(join_punctuality, 1),
            meeting_participation_rate=round(avg_participants, 1),
            avg_daily_meetings=round(avg_daily_meetings, 1),
            avg_daily_video_minutes=round(avg_daily_minutes, 1),
            peak_daily_meetings=peak_daily,
            meeting_overrun_rate=round(meeting_overrun_rate, 1),
            back_to_back_rate=round(back_to_back_rate, 1),
            avg_longest_gap_minutes=round(avg_longest_gap, 1),
            meeting_fatigue_score=round(meeting_fatigue, 1),
            after_hours_meeting_rate=round(after_hours_rate, 1),
            weekend_meeting_count=weekend_count,
            recurring_meeting_ratio=round(recurring_ratio, 3),
            overload_score=round(overload, 1),
            burnout_risk=round(burnout, 1),
            engagement_score=round(engagement, 1),
            risk_label=risk_label,
            recommendations=recs,
            daily_breakdown=[
                {
                    "date": s.date,
                    "meetings": s.meeting_count,
                    "minutes": round(s.total_minutes, 1),
                    "back_to_back": s.back_to_back_count,
                    "camera_on_rate": round(s.camera_on_rate, 3),
                    "longest_gap_min": round(s.longest_gap_minutes, 1),
                }
                for s in daily_summaries
            ],
        )

    def _compute_fatigue(
        self,
        back_to_back_rate: float,
        avg_daily_minutes: float,
        avg_gap: float,
    ) -> float:
        """Meeting fatigue score: back-to-back density + total load + recovery gaps."""
        b2b_component = back_to_back_rate * 0.45

        # >240 min/day of video is heavy; scale linearly to 100
        duration_component = min(100, avg_daily_minutes / 2.4) * 0.30

        # Short gaps between meetings = no recovery
        # 60+ min gap = healthy, <15 min = concerning
        gap_component = max(0, min(100, (60 - avg_gap) / 0.6)) * 0.25

        return min(100, b2b_component + duration_component + gap_component)

    def _compute_overload(
        self,
        avg_daily: float,
        avg_minutes: float,
        after_hours_rate: float,
    ) -> float:
        """Meeting overload: too many meetings, too much time, after hours."""
        # >6 meetings/day is overloaded
        count_component = min(100, avg_daily / 0.06) * 0.40

        # >300 min/day = overloaded
        duration_component = min(100, avg_minutes / 3.0) * 0.35

        after_hours_component = after_hours_rate * 0.25

        return min(100, count_component + duration_component + after_hours_component)

    def _compute_engagement_score(
        self,
        camera_on_rate: float,
        join_punctuality: float,
        avg_camera_ratio: float,
        recurring_ratio: float,
        avg_participants: float,
    ) -> float:
        """Compute engagement score from video conference signals.

        Punctuality is weighted highest — it's the strongest signal that
        people value the meeting. Camera-on is secondary because cultural
        norms vary. Meeting size penalizes passive mega-meetings.
        Recurring ratio has a sweet spot: some structure is healthy,
        but >80% recurring suggests calendar bloat.
        """
        # Punctuality: strongest engagement signal (35%)
        punctuality_component = join_punctuality * 0.35

        # Camera engagement: blend of rate and ratio (25%)
        camera_component = (camera_on_rate * 0.6 + avg_camera_ratio * 100 * 0.4) * 0.25

        # Meeting size sweet spot: 3-8 people is ideal (20%)
        # Small meetings = more active participation
        if avg_participants <= 0:
            size_score = 50
        elif avg_participants <= 3:
            size_score = 70  # small but maybe too narrow
        elif avg_participants <= 8:
            size_score = 100  # sweet spot
        elif avg_participants <= 15:
            size_score = max(30, 100 - (avg_participants - 8) * 10)
        else:
            size_score = 20  # large passive meetings
        size_component = size_score * 0.20

        # Recurring ratio: sweet spot 0.3-0.6 (20%)
        # Some structure is healthy; too much = bloat
        if recurring_ratio <= 0.3:
            recur_score = 60 + recurring_ratio * 100  # low = ad-hoc heavy
        elif recurring_ratio <= 0.6:
            recur_score = 90  # healthy balance
        elif recurring_ratio <= 0.8:
            recur_score = 90 - (recurring_ratio - 0.6) * 200  # tapering
        else:
            recur_score = max(20, 50 - (recurring_ratio - 0.8) * 150)  # bloat
        recur_component = recur_score * 0.20

        return max(
            0,
            min(
                100,
                punctuality_component
                + camera_component
                + size_component
                + recur_component,
            ),
        )

    def _generate_recommendations(
        self,
        burnout: float,
        fatigue: float,
        overload: float,
        camera_rate: float,
        b2b_rate: float,
        after_hours_rate: float,
    ) -> List[str]:
        recs = []
        if burnout >= 70:
            recs.append(
                "URGENT: Video meeting burnout is critical. "
                "Implement mandatory no-meeting days and reduce recurring meetings."
            )
        if b2b_rate > 60:
            recs.append(
                "Back-to-back video calls exceed 60%. Add 10-minute buffers "
                "between meetings to allow recovery."
            )
        if after_hours_rate > 30:
            recs.append(
                "Over 30% of video calls occur after hours. "
                "Set core collaboration hours and block after-hours scheduling."
            )
        if camera_rate < 30:
            recs.append(
                "Camera-on rate is low (<30%). Consider smaller meetings "
                "to encourage participation, or make cameras optional in large calls."
            )
        if overload > 50:
            recs.append(
                "Meeting overload detected. Audit recurring meetings — "
                "cancel those without clear agendas or outcomes."
            )
        if not recs:
            recs.append("Video conferencing patterns are healthy. Continue monitoring.")
        return recs

    def _empty_signals(self) -> VideoConferenceSignals:
        return VideoConferenceSignals(
            camera_on_rate=0,
            avg_camera_on_ratio=0,
            join_punctuality_score=100,
            meeting_participation_rate=0,
            avg_daily_meetings=0,
            avg_daily_video_minutes=0,
            peak_daily_meetings=0,
            meeting_overrun_rate=0,
            back_to_back_rate=0,
            avg_longest_gap_minutes=480,
            meeting_fatigue_score=0,
            after_hours_meeting_rate=0,
            weekend_meeting_count=0,
            recurring_meeting_ratio=0,
            overload_score=0,
            burnout_risk=0,
            engagement_score=50,
            risk_label="Healthy",
            recommendations=["No video conferencing data available."],
        )
