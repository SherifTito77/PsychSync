"""
Computer Usage Metadata Analysis Service

Analyzes workstation ACTIVITY METADATA ONLY — no screen recording,
no keystroke logging, no application content capture.

Input signals (per time bucket):
  - keyboard activity level (events/min, NOT keystrokes)
  - mouse activity level (events/min, NOT coordinates)
  - application switch count (how often, NOT which apps)
  - idle periods (duration of inactivity)
  - continuous work session duration
  - active hours (first activity → last activity)

Output behavioral signals:
  - work_intensity (sustained high activity)
  - context_switching_rate (app switches per hour)
  - break_frequency (how often breaks are taken)
  - continuous_session_risk (long unbroken sessions)
  - boundary_erosion (after-hours computer activity)
  - burnout_risk composite

Privacy guarantees:
  - No screen content, screenshots, or recordings
  - No keystroke content (only events-per-minute rate)
  - No mouse coordinates or click targets
  - No application names or window titles
  - Only aggregate activity levels per time bucket
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


class ActivityLevel(str, Enum):
    IDLE = "idle"  # 0 events/min
    LOW = "low"  # 1-10 events/min
    MODERATE = "moderate"  # 11-40 events/min
    HIGH = "high"  # 41-80 events/min
    INTENSE = "intense"  # 80+ events/min


@dataclass
class UsageBucket:
    """5-minute activity bucket — no content, only intensity levels."""

    user_id: str
    timestamp: datetime
    keyboard_events_per_min: float  # aggregate rate, NOT keystrokes
    mouse_events_per_min: float  # aggregate rate, NOT coordinates
    app_switches: int  # count of focus changes
    is_idle: bool  # no activity for this bucket
    activity_level: ActivityLevel
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class WorkSession:
    """Continuous work session (activity without idle gap > 15 min)."""

    start: datetime
    end: datetime
    duration_minutes: float
    avg_activity_level: str
    app_switches: int
    break_count: int  # short pauses (5-15 min) within session


@dataclass
class ComputerUsageSignals:
    """Behavioral signals from computer usage metadata."""

    # Volume
    avg_daily_active_hours: float
    avg_daily_idle_hours: float
    total_active_days: int

    # Work sessions
    avg_session_duration_min: float
    max_session_duration_min: float
    sessions_over_3h: int  # long unbroken sessions
    avg_breaks_per_session: float

    # Activity patterns
    avg_keyboard_rate: float
    avg_mouse_rate: float
    app_switches_per_hour: float
    context_switching_score: float  # 0-100

    # Timing
    after_hours_ratio: float
    weekend_ratio: float
    avg_first_activity_hour: float  # e.g., 8.5 = 8:30 AM
    avg_last_activity_hour: float  # e.g., 18.5 = 6:30 PM
    avg_workday_span_hours: float  # last - first
    hourly_distribution: List[int]  # 24 buckets
    peak_hour: int

    # Composite scores (0-100, higher = more concerning)
    work_intensity_score: float
    break_deficit_score: float
    boundary_erosion_score: float
    burnout_risk_score: float

    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class ComputerUsageConnector(ABC):
    """Base interface for workstation activity connectors.

    MUST NOT capture: screen content, keystroke content, application
    names, window titles, URLs, mouse coordinates, or click targets.
    Only aggregate activity rates per time bucket.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_buckets(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[UsageBucket]: ...


# ══════════════════════════════════════════════════════════════════
# GENERIC AGENT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class AgentMetadataConnector(ComputerUsageConnector):
    """Lightweight desktop agent that reports only activity levels.

    The agent runs locally and reports:
    - Aggregate keyboard events/min (NOT individual keystrokes)
    - Aggregate mouse events/min (NOT coordinates)
    - Application focus-change count (NOT app names)
    - Idle detection

    Reports are sent as 5-minute bucketed summaries to the server.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(self, api_endpoint: str = "", api_key: str = ""):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "desktop_agent",
            "bucket_size": "5min",
            "note": "Activity levels only — no content, no screen capture",
        }

    async def fetch_buckets(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[UsageBucket]:
        """Fetch activity buckets from agent reporting endpoint."""
        if not self.api_endpoint:
            return []

        buckets: List[UsageBucket] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_endpoint}/activity-buckets",
                    headers={"X-API-Key": self.api_key},
                    params={
                        "user_id": user_id,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for row in data.get("buckets", []):
                    ts = datetime.fromisoformat(row["timestamp"])
                    kb_rate = row.get("keyboard_events_per_min", 0)
                    mouse_rate = row.get("mouse_events_per_min", 0)
                    is_idle = kb_rate == 0 and mouse_rate == 0

                    buckets.append(
                        UsageBucket(
                            user_id=user_id,
                            timestamp=ts,
                            keyboard_events_per_min=kb_rate,
                            mouse_events_per_min=mouse_rate,
                            app_switches=row.get("app_switches", 0),
                            is_idle=is_idle,
                            activity_level=self._classify(kb_rate + mouse_rate),
                            is_after_hours=self._is_after_hours(ts),
                            is_weekend=ts.weekday() >= 5,
                        )
                    )

            logger.info("Agent: fetched %d buckets for %s", len(buckets), user_id)
        except ImportError:
            logger.warning("httpx not installed — agent connector disabled")
        except Exception as e:
            logger.error("Agent fetch error: %s", e)
        return buckets

    def _classify(self, total_rate: float) -> ActivityLevel:
        if total_rate == 0:
            return ActivityLevel.IDLE
        if total_rate <= 10:
            return ActivityLevel.LOW
        if total_rate <= 40:
            return ActivityLevel.MODERATE
        if total_rate <= 80:
            return ActivityLevel.HIGH
        return ActivityLevel.INTENSE

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class ComputerUsageAnalyzer:
    """Extracts behavioral signals from workstation activity metadata."""

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)
    BUCKET_MINUTES = 5
    IDLE_GAP_MINUTES = 15  # gap > 15 min breaks a session

    def analyze(
        self,
        buckets: List[UsageBucket],
        days: int = 14,
    ) -> ComputerUsageSignals:
        if not buckets:
            return self._empty_signals()

        active = [b for b in buckets if not b.is_idle]
        idle = [b for b in buckets if b.is_idle]

        active_minutes = len(active) * self.BUCKET_MINUTES
        idle_minutes = len(idle) * self.BUCKET_MINUTES
        avg_active_hours = (active_minutes / 60) / max(days, 1)
        avg_idle_hours = (idle_minutes / 60) / max(days, 1)
        active_days = len(set(b.timestamp.strftime("%Y-%m-%d") for b in active))

        # Work sessions
        sessions = self._build_sessions(buckets)
        avg_session = sum(s.duration_minutes for s in sessions) / max(len(sessions), 1)
        max_session = max((s.duration_minutes for s in sessions), default=0)
        long_sessions = sum(1 for s in sessions if s.duration_minutes > 180)
        avg_breaks = sum(s.break_count for s in sessions) / max(len(sessions), 1)

        # Activity rates
        avg_kb = sum(b.keyboard_events_per_min for b in active) / max(len(active), 1)
        avg_mouse = sum(b.mouse_events_per_min for b in active) / max(len(active), 1)
        total_switches = sum(b.app_switches for b in active)
        active_hours_total = active_minutes / 60
        switches_per_hour = total_switches / max(active_hours_total, 1)
        ctx_switching = min(100, switches_per_hour * 2.5)

        # Timing
        ah_active = [b for b in active if b.is_after_hours]
        wk_active = [b for b in active if b.is_weekend]
        ah_ratio = len(ah_active) / max(len(active), 1)
        wk_ratio = len(wk_active) / max(len(active), 1)

        first_hours, last_hours = self._avg_first_last(active)
        span_hours = last_hours - first_hours if last_hours > first_hours else 0

        hourly = self._hourly_distribution(active)
        peak = hourly.index(max(hourly))

        # Composites
        work_intensity = self._work_intensity_score(
            avg_active_hours, avg_kb + avg_mouse, max_session
        )
        break_deficit = self._break_deficit_score(
            avg_breaks, avg_session, long_sessions
        )
        boundary = self._boundary_erosion_score(ah_ratio, wk_ratio, span_hours)
        burnout, label = self._burnout_risk_score(
            work_intensity, break_deficit, boundary, ctx_switching, wk_ratio
        )

        daily = self._daily_breakdown(buckets, days)
        recs = self._generate_recommendations(
            avg_active_hours,
            avg_session,
            long_sessions,
            avg_breaks,
            ah_ratio,
            wk_ratio,
            switches_per_hour,
            span_hours,
        )

        return ComputerUsageSignals(
            avg_daily_active_hours=round(avg_active_hours, 1),
            avg_daily_idle_hours=round(avg_idle_hours, 1),
            total_active_days=active_days,
            avg_session_duration_min=round(avg_session, 0),
            max_session_duration_min=round(max_session, 0),
            sessions_over_3h=long_sessions,
            avg_breaks_per_session=round(avg_breaks, 1),
            avg_keyboard_rate=round(avg_kb, 1),
            avg_mouse_rate=round(avg_mouse, 1),
            app_switches_per_hour=round(switches_per_hour, 1),
            context_switching_score=round(ctx_switching, 1),
            after_hours_ratio=round(ah_ratio, 3),
            weekend_ratio=round(wk_ratio, 3),
            avg_first_activity_hour=round(first_hours, 1),
            avg_last_activity_hour=round(last_hours, 1),
            avg_workday_span_hours=round(span_hours, 1),
            hourly_distribution=hourly,
            peak_hour=peak,
            work_intensity_score=round(work_intensity, 1),
            break_deficit_score=round(break_deficit, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # ── Component scores ─────────────────────────────────────────

    def _work_intensity_score(
        self, avg_hours: float, avg_rate: float, max_session: float
    ) -> float:
        """0-100: sustained high-intensity work without rest."""
        hours_pressure = min(40, max(0, (avg_hours - 8) * 10))
        rate_pressure = min(30, max(0, (avg_rate - 50) * 0.6))
        session_pressure = min(30, max(0, (max_session - 120) * 0.25))
        return min(100, hours_pressure + rate_pressure + session_pressure)

    def _break_deficit_score(
        self, avg_breaks: float, avg_session: float, long_sessions: int
    ) -> float:
        """0-100: insufficient breaks during work sessions."""
        # Healthy: break every 50 min (Pomodoro-ish)
        expected_breaks = avg_session / 50
        deficit = max(0, expected_breaks - avg_breaks)
        break_component = min(50, deficit * 15)
        long_component = min(50, long_sessions * 10)
        return min(100, break_component + long_component)

    def _boundary_erosion_score(
        self, ah_ratio: float, wk_ratio: float, span_hours: float
    ) -> float:
        """0-100: computer use outside normal boundaries."""
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, wk_ratio * 400)
        # Workday span > 10h is concerning
        span_component = min(100, max(0, (span_hours - 10) * 20))
        return ah_component * 0.35 + wk_component * 0.30 + span_component * 0.35

    def _burnout_risk_score(
        self,
        intensity: float,
        break_deficit: float,
        boundary: float,
        ctx_switching: float,
        weekend_ratio: float,
    ) -> tuple:
        """Composite burnout risk from computer usage metadata."""
        base = (
            break_deficit * 0.30
            + boundary * 0.30
            + intensity * 0.25
            + ctx_switching * 0.15
        )
        interaction = (intensity / 100) * (break_deficit / 100) * 20
        weekend_amp = min(10, max(0, (weekend_ratio - 0.05) * 150))
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

    def _build_sessions(self, buckets: List[UsageBucket]) -> List[WorkSession]:
        sorted_b = sorted(buckets, key=lambda b: b.timestamp)
        sessions: List[WorkSession] = []
        if not sorted_b:
            return sessions

        session_start = sorted_b[0].timestamp
        last_active = sorted_b[0].timestamp
        switches = 0
        breaks = 0
        levels: List[str] = []

        for b in sorted_b:
            gap = (b.timestamp - last_active).total_seconds() / 60

            if gap > self.IDLE_GAP_MINUTES and not b.is_idle:
                # End current session
                dur = (
                    last_active - session_start
                ).total_seconds() / 60 + self.BUCKET_MINUTES
                if dur >= 10:
                    sessions.append(
                        WorkSession(
                            start=session_start,
                            end=last_active,
                            duration_minutes=dur,
                            avg_activity_level=self._avg_level(levels),
                            app_switches=switches,
                            break_count=breaks,
                        )
                    )
                session_start = b.timestamp
                switches = 0
                breaks = 0
                levels = []
            elif self.BUCKET_MINUTES < gap <= self.IDLE_GAP_MINUTES:
                breaks += 1

            if not b.is_idle:
                last_active = b.timestamp
                switches += b.app_switches
                levels.append(b.activity_level.value)

        # Close last session
        dur = (last_active - session_start).total_seconds() / 60 + self.BUCKET_MINUTES
        if dur >= 10:
            sessions.append(
                WorkSession(
                    start=session_start,
                    end=last_active,
                    duration_minutes=dur,
                    avg_activity_level=self._avg_level(levels),
                    app_switches=switches,
                    break_count=breaks,
                )
            )
        return sessions

    def _avg_level(self, levels: List[str]) -> str:
        if not levels:
            return "idle"
        order = ["idle", "low", "moderate", "high", "intense"]
        avg_idx = sum(order.index(l) for l in levels if l in order) / len(levels)
        return order[min(int(round(avg_idx)), len(order) - 1)]

    def _avg_first_last(self, active: List[UsageBucket]) -> tuple:
        by_day: Dict[str, List[UsageBucket]] = defaultdict(list)
        for b in active:
            by_day[b.timestamp.strftime("%Y-%m-%d")].append(b)

        firsts, lasts = [], []
        for recs in by_day.values():
            sorted_r = sorted(recs, key=lambda b: b.timestamp)
            firsts.append(
                sorted_r[0].timestamp.hour + sorted_r[0].timestamp.minute / 60
            )
            lasts.append(
                sorted_r[-1].timestamp.hour + sorted_r[-1].timestamp.minute / 60
            )

        avg_first = sum(firsts) / len(firsts) if firsts else 9.0
        avg_last = sum(lasts) / len(lasts) if lasts else 18.0
        return avg_first, avg_last

    def _hourly_distribution(self, active: List[UsageBucket]) -> List[int]:
        buckets = [0] * 24
        for b in active:
            buckets[b.timestamp.hour] += 1
        return buckets

    def _daily_breakdown(
        self, buckets: List[UsageBucket], days: int
    ) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[UsageBucket]] = defaultdict(list)
        for b in buckets:
            by_day[b.timestamp.strftime("%Y-%m-%d")].append(b)

        result = []
        for day in sorted(by_day.keys()):
            recs = by_day[day]
            active = [b for b in recs if not b.is_idle]
            active_hrs = len(active) * self.BUCKET_MINUTES / 60
            ah = sum(1 for b in active if b.is_after_hours)
            switches = sum(b.app_switches for b in active)
            first = min((b.timestamp for b in active), default=None)
            last = max((b.timestamp for b in active), default=None)

            result.append(
                {
                    "date": day,
                    "active_hours": round(active_hrs, 1),
                    "idle_hours": round(
                        len([b for b in recs if b.is_idle]) * self.BUCKET_MINUTES / 60,
                        1,
                    ),
                    "after_hours_buckets": ah,
                    "app_switches": switches,
                    "first_activity": first.strftime("%H:%M") if first else None,
                    "last_activity": last.strftime("%H:%M") if last else None,
                }
            )
        return result

    def _generate_recommendations(
        self,
        avg_hours,
        avg_session,
        long_sessions,
        avg_breaks,
        ah_ratio,
        wk_ratio,
        switches_hr,
        span_hours,
    ) -> List[str]:
        recs = []
        if long_sessions > 3:
            recs.append(
                f"{long_sessions} work sessions exceeded 3 hours without a break. "
                "Use the 52/17 rule: 52 min focused work, 17 min break."
            )
        if avg_breaks < 1 and avg_session > 60:
            recs.append(
                "Very few breaks during work sessions. "
                "Set a timer for regular microbreaks — even 2 minutes helps."
            )
        if span_hours > 12:
            recs.append(
                f"Average workday span is {span_hours:.0f} hours (first to last activity). "
                "Consider setting a hard stop time for computer use."
            )
        if ah_ratio > 0.20:
            recs.append(
                f"{ah_ratio*100:.0f}% of computer activity is outside work hours. "
                "This sustained pattern is a strong burnout indicator."
            )
        if wk_ratio > 0.05:
            recs.append(
                f"{wk_ratio*100:.0f}% of computer activity is on weekends. "
                "Protect at least one full screen-free day."
            )
        if switches_hr > 30:
            recs.append(
                f"App switching rate ({switches_hr:.0f}/hour) is very high. "
                "Try single-tasking blocks with notifications disabled."
            )
        if avg_hours > 10:
            recs.append(
                f"Averaging {avg_hours:.0f}h/day of active computer use — "
                "well above sustainable levels. Discuss workload with your manager."
            )
        if not recs:
            recs.append(
                "Computer usage patterns look healthy. Activity levels are sustainable."
            )
        return recs

    def _empty_signals(self) -> ComputerUsageSignals:
        return ComputerUsageSignals(
            avg_daily_active_hours=0,
            avg_daily_idle_hours=0,
            total_active_days=0,
            avg_session_duration_min=0,
            max_session_duration_min=0,
            sessions_over_3h=0,
            avg_breaks_per_session=0,
            avg_keyboard_rate=0,
            avg_mouse_rate=0,
            app_switches_per_hour=0,
            context_switching_score=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            avg_first_activity_hour=9,
            avg_last_activity_hour=18,
            avg_workday_span_hours=0,
            hourly_distribution=[0] * 24,
            peak_hour=10,
            work_intensity_score=0,
            break_deficit_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No computer usage data available. Deploy the desktop agent to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class ComputerUsageRegistry:
    CONNECTOR_TYPES = {"agent": AgentMetadataConnector}

    def __init__(self):
        self._connectors: Dict[str, ComputerUsageConnector] = {}

    def register(self, name: str, connector: ComputerUsageConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered computer usage connector: %s", name)

    def get(self, name: str) -> Optional[ComputerUsageConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


computer_usage_registry = ComputerUsageRegistry()
