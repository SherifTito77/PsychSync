"""
Badge Access Metadata Analysis Service

Analyzes physical access control METADATA ONLY.
Entry/exit timestamps from badge swipe systems.

Input signals (per swipe):
  - timestamp
  - direction (entry / exit)
  - location (building / floor, NOT specific room)
  - user identifier

Output behavioral signals:
  - avg_office_hours (time between first entry and last exit)
  - late_departure_ratio (exits after 8 PM)
  - early_arrival_ratio (entries before 7 AM)
  - long_day_count (>12h in office)
  - weekend_presence_ratio
  - consistency_score (regularity of schedule)
  - burnout_risk composite

No location tracking beyond building-level.
No movement tracking within the building.
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


class SwipeDirection(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"


@dataclass
class BadgeSwipe:
    """One badge swipe event — timestamp and direction only."""

    user_id: str
    timestamp: datetime
    direction: SwipeDirection
    building: str  # building/site name (not room-level)
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class OfficeDaySummary:
    """Per-day office presence derived from badge swipes."""

    date: str
    first_entry: str  # HH:MM
    last_exit: str  # HH:MM
    office_hours: float  # hours between first entry and last exit
    is_long_day: bool  # >12 hours
    is_weekend: bool
    entry_count: int  # total badge swipes in
    exit_count: int


@dataclass
class BadgeAccessSignals:
    """Behavioral signals from badge access metadata."""

    # Presence
    avg_office_hours: float  # avg hours in office per day
    median_office_hours: float
    max_office_hours: float
    total_office_days: int

    # Extremes
    long_day_count: int  # days > 12h
    very_long_day_count: int  # days > 14h
    late_departure_ratio: float  # exits after 8 PM
    early_arrival_ratio: float  # entries before 7 AM

    # Timing patterns
    avg_arrival_hour: float  # e.g., 8.5 = 8:30 AM
    avg_departure_hour: float  # e.g., 18.5 = 6:30 PM
    arrival_consistency: float  # std dev of arrival times (lower = more consistent)

    # Weekend / off-hours
    weekend_days_present: int
    weekend_ratio: float  # weekend days with badge / total days with badge

    # Trends
    hours_trend: str  # "increasing", "stable", "decreasing"
    recent_vs_baseline_hours: float  # ratio of last 7 days avg vs full period avg

    # Composite scores (0-100, higher = more concerning)
    overwork_score: float
    boundary_erosion_score: float
    burnout_risk_score: float

    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class BadgeAccessConnector(ABC):
    """Base interface for physical access control connectors.

    Only receives timestamp + direction + building.
    No room-level tracking, no movement patterns.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_swipes(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[BadgeSwipe]: ...


# ══════════════════════════════════════════════════════════════════
# GENERIC ACCESS CONTROL CONNECTOR
# ══════════════════════════════════════════════════════════════════


class AccessControlConnector(BadgeAccessConnector):
    """Generic connector for building access control systems (Lenel, HID, etc.)."""

    WORK_START = time(7, 0)
    WORK_END = time(20, 0)

    def __init__(self, api_endpoint: str = "", api_key: str = ""):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "access_control",
            "note": "Building-level entry/exit only — no room tracking",
        }

    async def fetch_swipes(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[BadgeSwipe]:
        if not self.api_endpoint:
            return []
        swipes: List[BadgeSwipe] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_endpoint}/swipes",
                    headers={"X-API-Key": self.api_key},
                    params={
                        "user_id": user_id,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    },
                )
                resp.raise_for_status()
                for row in resp.json().get("events", []):
                    ts = datetime.fromisoformat(row["timestamp"])
                    swipes.append(
                        BadgeSwipe(
                            user_id=user_id,
                            timestamp=ts,
                            direction=SwipeDirection(row.get("direction", "entry")),
                            building=row.get("building", "main"),
                            is_after_hours=self._is_after_hours(ts),
                            is_weekend=ts.weekday() >= 5,
                        )
                    )
        except Exception as e:
            logger.error("Badge access fetch error: %s", e)
        return swipes

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class BadgeAccessAnalyzer:
    """Extracts behavioral signals from badge swipe metadata."""

    def analyze(
        self,
        swipes: List[BadgeSwipe],
        days: int = 30,
    ) -> BadgeAccessSignals:
        if not swipes:
            return self._empty_signals()

        day_summaries = self._build_day_summaries(swipes)
        if not day_summaries:
            return self._empty_signals()

        office_hours = [d.office_hours for d in day_summaries]
        weekday_summaries = [d for d in day_summaries if not d.is_weekend]
        weekend_summaries = [d for d in day_summaries if d.is_weekend]

        avg_hours = sum(office_hours) / len(office_hours)
        sorted_hours = sorted(office_hours)
        median_hours = sorted_hours[len(sorted_hours) // 2]
        max_hours = max(office_hours)

        long_days = sum(1 for h in office_hours if h > 12)
        very_long = sum(1 for h in office_hours if h > 14)

        # Late departures / early arrivals
        late_exits = sum(1 for d in day_summaries if d.last_exit >= "20:00")
        late_ratio = late_exits / max(len(day_summaries), 1)
        early_entries = sum(1 for d in day_summaries if d.first_entry <= "07:00")
        early_ratio = early_entries / max(len(day_summaries), 1)

        # Arrival/departure times
        arrival_hours = []
        departure_hours = []
        for d in weekday_summaries:
            h, m = d.first_entry.split(":")
            arrival_hours.append(int(h) + int(m) / 60)
            h2, m2 = d.last_exit.split(":")
            departure_hours.append(int(h2) + int(m2) / 60)

        avg_arrival = sum(arrival_hours) / len(arrival_hours) if arrival_hours else 9.0
        avg_departure = (
            sum(departure_hours) / len(departure_hours) if departure_hours else 18.0
        )

        # Arrival consistency (std dev)
        if len(arrival_hours) > 1:
            mean_arr = sum(arrival_hours) / len(arrival_hours)
            variance = sum((h - mean_arr) ** 2 for h in arrival_hours) / len(
                arrival_hours
            )
            consistency = variance**0.5
        else:
            consistency = 0

        # Weekend
        wk_days = len(weekend_summaries)
        wk_ratio = wk_days / max(len(day_summaries), 1)

        # Trend
        hours_trend, recent_ratio = self._compute_trend(day_summaries)

        # Composites
        overwork = self._overwork_score(avg_hours, long_days, very_long, max_hours)
        boundary = self._boundary_erosion_score(
            late_ratio, early_ratio, wk_ratio, avg_hours
        )
        burnout, label = self._burnout_risk_score(
            overwork, boundary, wk_ratio, recent_ratio
        )

        daily = [
            {
                "date": d.date,
                "first_entry": d.first_entry,
                "last_exit": d.last_exit,
                "office_hours": d.office_hours,
                "is_long_day": d.is_long_day,
                "is_weekend": d.is_weekend,
            }
            for d in day_summaries
        ]

        recs = self._generate_recommendations(
            avg_hours,
            long_days,
            very_long,
            late_ratio,
            wk_ratio,
            recent_ratio,
        )

        return BadgeAccessSignals(
            avg_office_hours=round(avg_hours, 1),
            median_office_hours=round(median_hours, 1),
            max_office_hours=round(max_hours, 1),
            total_office_days=len(day_summaries),
            long_day_count=long_days,
            very_long_day_count=very_long,
            late_departure_ratio=round(late_ratio, 3),
            early_arrival_ratio=round(early_ratio, 3),
            avg_arrival_hour=round(avg_arrival, 1),
            avg_departure_hour=round(avg_departure, 1),
            arrival_consistency=round(consistency, 2),
            weekend_days_present=wk_days,
            weekend_ratio=round(wk_ratio, 3),
            hours_trend=hours_trend,
            recent_vs_baseline_hours=round(recent_ratio, 2),
            overwork_score=round(overwork, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # ── Component scores ─────────────────────────────────────────

    def _overwork_score(
        self, avg_hours: float, long_days: int, very_long: int, max_hours: float
    ) -> float:
        """0-100: physical overwork based on time in office."""
        hours_pressure = min(50, max(0, (avg_hours - 9) * 15))
        long_day_pressure = min(25, long_days * 5)
        extreme_pressure = min(25, very_long * 12)
        return min(100, hours_pressure + long_day_pressure + extreme_pressure)

    def _boundary_erosion_score(
        self, late_ratio: float, early_ratio: float, wk_ratio: float, avg_hours: float
    ) -> float:
        """0-100: working outside normal physical boundaries."""
        late_component = min(40, late_ratio * 120)
        early_component = min(20, early_ratio * 80)
        weekend_component = min(40, wk_ratio * 200)
        return late_component + early_component + weekend_component

    def _burnout_risk_score(
        self, overwork: float, boundary: float, wk_ratio: float, recent_ratio: float
    ) -> tuple:
        """Composite burnout risk from badge access metadata.

        Badge data is uniquely physical: you can't fake being in the
        office. Hours trend increasing is a particularly strong signal.
        """
        base = overwork * 0.45 + boundary * 0.35

        # Trend amplifier: hours increasing over baseline
        trend_amp = 0.0
        if recent_ratio > 1.15:
            trend_amp = min(15, (recent_ratio - 1.0) * 75)

        # Weekend presence is a strong physical signal
        weekend_amp = min(10, max(0, (wk_ratio - 0.05) * 150))

        score = min(100, base + trend_amp + weekend_amp)

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

    def _build_day_summaries(self, swipes: List[BadgeSwipe]) -> List[OfficeDaySummary]:
        by_day: Dict[str, List[BadgeSwipe]] = defaultdict(list)
        for s in swipes:
            by_day[s.timestamp.strftime("%Y-%m-%d")].append(s)

        summaries = []
        for day_str in sorted(by_day.keys()):
            day_swipes = sorted(by_day[day_str], key=lambda s: s.timestamp)
            entries = [s for s in day_swipes if s.direction == SwipeDirection.ENTRY]
            exits = [s for s in day_swipes if s.direction == SwipeDirection.EXIT]

            if not entries and not exits:
                continue

            first_ts = day_swipes[0].timestamp
            last_ts = day_swipes[-1].timestamp
            hours = (last_ts - first_ts).total_seconds() / 3600

            summaries.append(
                OfficeDaySummary(
                    date=day_str,
                    first_entry=first_ts.strftime("%H:%M"),
                    last_exit=last_ts.strftime("%H:%M"),
                    office_hours=round(hours, 1),
                    is_long_day=hours > 12,
                    is_weekend=first_ts.weekday() >= 5,
                    entry_count=len(entries),
                    exit_count=len(exits),
                )
            )
        return summaries

    def _compute_trend(self, summaries: List[OfficeDaySummary]) -> tuple:
        if len(summaries) < 7:
            return "insufficient_data", 1.0

        recent = summaries[-7:]
        baseline = summaries[:-7] if len(summaries) > 7 else summaries
        recent_avg = sum(d.office_hours for d in recent) / len(recent)
        baseline_avg = sum(d.office_hours for d in baseline) / max(len(baseline), 1)

        if baseline_avg == 0:
            return "stable", 1.0

        ratio = recent_avg / baseline_avg
        if ratio > 1.10:
            return "increasing", round(ratio, 2)
        elif ratio < 0.90:
            return "decreasing", round(ratio, 2)
        return "stable", round(ratio, 2)

    def _generate_recommendations(
        self,
        avg_hours,
        long_days,
        very_long,
        late_ratio,
        wk_ratio,
        recent_ratio,
    ) -> List[str]:
        recs = []
        if very_long > 2:
            recs.append(
                f"{very_long} days exceeded 14 hours in the office. "
                "This level of sustained physical presence is a critical burnout indicator."
            )
        if long_days > 5:
            recs.append(
                f"{long_days} days exceeded 12 hours. "
                "Set a hard departure time and communicate it to your team."
            )
        if avg_hours > 10:
            recs.append(
                f"Averaging {avg_hours:.0f}h/day in the office — well above sustainable. "
                "Discuss workload redistribution with management."
            )
        if late_ratio > 0.30:
            recs.append(
                f"{late_ratio*100:.0f}% of days have exits after 8 PM. "
                "Late departures compound fatigue over time."
            )
        if wk_ratio > 0.10:
            recs.append(
                f"Present in the office {wk_ratio*100:.0f}% of weekend days. "
                "Physical rest days are essential for recovery."
            )
        if recent_ratio > 1.15:
            recs.append(
                f"Office hours have increased {(recent_ratio-1)*100:.0f}% vs baseline. "
                "Escalating hours is an early burnout warning — investigate root cause."
            )
        if not recs:
            recs.append("Office presence patterns look healthy.")
        return recs

    def _empty_signals(self) -> BadgeAccessSignals:
        return BadgeAccessSignals(
            avg_office_hours=0,
            median_office_hours=0,
            max_office_hours=0,
            total_office_days=0,
            long_day_count=0,
            very_long_day_count=0,
            late_departure_ratio=0,
            early_arrival_ratio=0,
            avg_arrival_hour=9,
            avg_departure_hour=18,
            arrival_consistency=0,
            weekend_days_present=0,
            weekend_ratio=0,
            hours_trend="no_data",
            recent_vs_baseline_hours=1.0,
            overwork_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No badge access data available. Connect your access control system to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class BadgeAccessRegistry:
    CONNECTOR_TYPES = {"access_control": AccessControlConnector}

    def __init__(self):
        self._connectors: Dict[str, BadgeAccessConnector] = {}

    def register(self, name: str, connector: BadgeAccessConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered badge access connector: %s", name)

    def get(self, name: str) -> Optional[BadgeAccessConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


badge_access_registry = BadgeAccessRegistry()
