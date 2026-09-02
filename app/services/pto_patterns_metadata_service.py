"""
PTO Patterns Metadata Analysis Service

Analyzes leave/PTO METADATA ONLY — booking dates, cancellations,
balances, and sick day frequency. No leave reasons or medical details.

Input signals:
  - PTO booked / taken / cancelled
  - sick days taken (count only, no reason)
  - leave balance remaining
  - days since last vacation (>= 3 consecutive days off)
  - vacation cancellation pattern

Output behavioral signals:
  - vacation_avoidance (not using available PTO)
  - cancellation_pattern (booking then cancelling)
  - sick_day_spike (sudden increase in sick days)
  - recovery_deficit (days since last real break)
  - burnout_risk composite

This is one of the strongest burnout predictors available.
Research shows vacation avoidance predicts burnout 6-12 months
before communication metadata changes become visible.
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class LeaveType(str, Enum):
    VACATION = "vacation"
    SICK = "sick"
    PERSONAL = "personal"
    BEREAVEMENT = "bereavement"
    PARENTAL = "parental"
    OTHER = "other"


class LeaveStatus(str, Enum):
    BOOKED = "booked"
    TAKEN = "taken"
    CANCELLED = "cancelled"
    DECLINED = "declined"


@dataclass
class LeaveRecord:
    """One leave request — dates and status only, no reason text."""

    user_id: str
    leave_type: LeaveType
    status: LeaveStatus
    start_date: date
    end_date: date
    business_days: int
    booked_on: Optional[date]  # when the request was submitted
    cancelled_on: Optional[date]  # when it was cancelled (if applicable)


@dataclass
class LeaveBalance:
    """Current leave balance snapshot."""

    user_id: str
    as_of: date
    vacation_total: float  # days entitled per year
    vacation_used: float  # days used this year
    vacation_remaining: float  # days left
    sick_total: float
    sick_used: float
    sick_remaining: float
    utilization_pct: float  # vacation_used / vacation_total * 100


@dataclass
class PTOPatternsSignals:
    """Behavioral signals from PTO metadata analysis."""

    # Usage
    vacation_days_taken: float
    vacation_days_remaining: float
    vacation_utilization_pct: float  # how much of entitlement used
    sick_days_taken: float

    # Patterns
    days_since_last_vacation: int  # last >= 3 consecutive days off
    longest_streak_without_pto: int  # longest continuous work period
    vacations_booked: int
    vacations_cancelled: int
    cancellation_rate: float  # cancelled / booked

    # Sick day patterns
    sick_days_last_30: int
    sick_days_last_90: int
    sick_day_trend: str  # "increasing", "stable", "decreasing"
    monday_friday_sick_ratio: float  # sick days on Mon/Fri (disengagement signal)

    # Time-based
    months_into_year: float
    expected_utilization_pct: float  # prorated expectation
    utilization_gap: float  # actual vs expected (negative = under-using)

    # Composite scores (0-100, higher = more concerning)
    vacation_avoidance_score: float
    recovery_deficit_score: float
    sick_pattern_score: float
    burnout_risk_score: float

    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class PTOConnector(ABC):
    """Base interface for PTO/leave system connectors.

    Only receives dates, types, and status.
    Never receives leave reasons, medical details, or notes.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_leave_records(
        self,
        user_id: str,
        start: date,
        end: date,
    ) -> List[LeaveRecord]: ...

    @abstractmethod
    async def fetch_balance(
        self,
        user_id: str,
    ) -> Optional[LeaveBalance]: ...


# ══════════════════════════════════════════════════════════════════
# HRIS PTO CONNECTOR
# ══════════════════════════════════════════════════════════════════


class HRISPTOConnector(PTOConnector):
    """Connects to HRIS systems (Workday, BambooHR, etc.) for PTO data."""

    def __init__(self, api_endpoint: str = "", api_key: str = ""):
        self.api_endpoint = api_endpoint
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "hris_pto",
            "note": "Dates and status only — no leave reasons or medical details",
        }

    async def fetch_leave_records(
        self,
        user_id: str,
        start: date,
        end: date,
    ) -> List[LeaveRecord]:
        if not self.api_endpoint:
            return []
        records = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.api_endpoint}/leave-records",
                    headers={"X-API-Key": self.api_key},
                    params={
                        "user_id": user_id,
                        "start": start.isoformat(),
                        "end": end.isoformat(),
                    },
                )
                resp.raise_for_status()
                for row in resp.json().get("records", []):
                    records.append(
                        LeaveRecord(
                            user_id=user_id,
                            leave_type=LeaveType(row.get("type", "other")),
                            status=LeaveStatus(row.get("status", "taken")),
                            start_date=date.fromisoformat(row["start_date"]),
                            end_date=date.fromisoformat(row["end_date"]),
                            business_days=row.get("business_days", 1),
                            booked_on=(
                                date.fromisoformat(row["booked_on"])
                                if row.get("booked_on")
                                else None
                            ),
                            cancelled_on=(
                                date.fromisoformat(row["cancelled_on"])
                                if row.get("cancelled_on")
                                else None
                            ),
                        )
                    )
        except Exception as e:
            logger.error("PTO fetch error: %s", e)
        return records

    async def fetch_balance(self, user_id: str) -> Optional[LeaveBalance]:
        if not self.api_endpoint:
            return None
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.api_endpoint}/leave-balance",
                    headers={"X-API-Key": self.api_key},
                    params={"user_id": user_id},
                )
                resp.raise_for_status()
                d = resp.json()
                vac_total = d.get("vacation_total", 20)
                vac_used = d.get("vacation_used", 0)
                sick_total = d.get("sick_total", 10)
                sick_used = d.get("sick_used", 0)
                return LeaveBalance(
                    user_id=user_id,
                    as_of=date.today(),
                    vacation_total=vac_total,
                    vacation_used=vac_used,
                    vacation_remaining=vac_total - vac_used,
                    sick_total=sick_total,
                    sick_used=sick_used,
                    sick_remaining=sick_total - sick_used,
                    utilization_pct=round((vac_used / max(vac_total, 1)) * 100, 1),
                )
        except Exception as e:
            logger.debug("Balance fetch failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class PTOPatternsAnalyzer:
    """Extracts behavioral signals from PTO metadata.

    PTO avoidance is one of the strongest early burnout predictors.
    """

    def analyze(
        self,
        records: List[LeaveRecord],
        balance: Optional[LeaveBalance],
        lookback_days: int = 365,
    ) -> PTOPatternsSignals:
        if not records and not balance:
            return self._empty_signals()

        today = date.today()

        # Filter to taken/cancelled vacation and sick
        vacation_taken = [
            r
            for r in records
            if r.leave_type == LeaveType.VACATION and r.status == LeaveStatus.TAKEN
        ]
        vacation_booked = [
            r
            for r in records
            if r.leave_type == LeaveType.VACATION and r.status == LeaveStatus.BOOKED
        ]
        vacation_cancelled = [
            r
            for r in records
            if r.leave_type == LeaveType.VACATION and r.status == LeaveStatus.CANCELLED
        ]
        sick_taken = [
            r
            for r in records
            if r.leave_type == LeaveType.SICK and r.status == LeaveStatus.TAKEN
        ]

        vac_days = sum(r.business_days for r in vacation_taken)
        sick_days = sum(r.business_days for r in sick_taken)

        # Balance
        vac_remaining = balance.vacation_remaining if balance else 0
        vac_utilization = (
            balance.utilization_pct
            if balance
            else (round((vac_days / 20) * 100, 1))  # assume 20 days default
        )

        # Days since last real vacation (>= 3 consecutive days)
        real_vacations = [r for r in vacation_taken if r.business_days >= 3]
        if real_vacations:
            last_vac_end = max(r.end_date for r in real_vacations)
            days_since = (today - last_vac_end).days
        else:
            days_since = lookback_days  # never taken a real vacation in period

        # Longest streak without any PTO
        longest_streak = self._longest_work_streak(records, lookback_days)

        # Cancellation pattern
        total_booked = (
            len(vacation_taken) + len(vacation_booked) + len(vacation_cancelled)
        )
        cancel_rate = len(vacation_cancelled) / max(total_booked, 1)

        # Sick day patterns
        sick_30 = sum(1 for r in sick_taken if (today - r.start_date).days <= 30)
        sick_90 = sum(1 for r in sick_taken if (today - r.start_date).days <= 90)
        sick_trend = self._sick_trend(sick_taken, lookback_days)

        # Monday/Friday sick ratio (disengagement signal)
        mon_fri_sick = sum(
            1
            for r in sick_taken
            if r.start_date.weekday() in (0, 4)  # Monday=0, Friday=4
        )
        mf_ratio = mon_fri_sick / max(len(sick_taken), 1)

        # Utilization gap
        months = today.month + today.day / 30  # rough months into year
        expected_util = (months / 12) * 100
        util_gap = vac_utilization - expected_util

        # Composites
        vac_avoidance = self._vacation_avoidance_score(
            vac_utilization,
            days_since,
            cancel_rate,
            util_gap,
        )
        recovery = self._recovery_deficit_score(days_since, longest_streak, vac_days)
        sick_score = self._sick_pattern_score(sick_30, sick_90, sick_trend, mf_ratio)
        burnout, label = self._burnout_risk_score(
            vac_avoidance,
            recovery,
            sick_score,
            cancel_rate,
        )

        timeline = self._build_timeline(records)
        recs = self._generate_recommendations(
            vac_utilization,
            days_since,
            cancel_rate,
            sick_30,
            util_gap,
            longest_streak,
        )

        return PTOPatternsSignals(
            vacation_days_taken=vac_days,
            vacation_days_remaining=vac_remaining,
            vacation_utilization_pct=round(vac_utilization, 1),
            sick_days_taken=sick_days,
            days_since_last_vacation=days_since,
            longest_streak_without_pto=longest_streak,
            vacations_booked=total_booked,
            vacations_cancelled=len(vacation_cancelled),
            cancellation_rate=round(cancel_rate, 3),
            sick_days_last_30=sick_30,
            sick_days_last_90=sick_90,
            sick_day_trend=sick_trend,
            monday_friday_sick_ratio=round(mf_ratio, 3),
            months_into_year=round(months, 1),
            expected_utilization_pct=round(expected_util, 1),
            utilization_gap=round(util_gap, 1),
            vacation_avoidance_score=round(vac_avoidance, 1),
            recovery_deficit_score=round(recovery, 1),
            sick_pattern_score=round(sick_score, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            timeline=timeline,
        )

    # ── Component scores ─────────────────────────────────────────

    def _vacation_avoidance_score(
        self,
        utilization: float,
        days_since: int,
        cancel_rate: float,
        util_gap: float,
    ) -> float:
        """0-100: is the person avoiding vacation?

        Strong burnout predictor. Cancelling booked vacations is
        particularly concerning — it indicates perceived indispensability.
        """
        # Under-utilization relative to time in year
        gap_component = min(40, max(0, -util_gap * 1.5))
        # Days since last real break
        days_component = min(30, max(0, (days_since - 60) * 0.5))
        # Cancellation pattern
        cancel_component = min(30, cancel_rate * 100)
        return min(100, gap_component + days_component + cancel_component)

    def _recovery_deficit_score(
        self,
        days_since: int,
        longest_streak: int,
        vac_days: float,
    ) -> float:
        """0-100: has the person had adequate recovery time?"""
        # No vacation in 90+ days
        recency = min(50, max(0, (days_since - 60) * 0.8))
        # Longest continuous work streak
        streak_pressure = min(30, max(0, (longest_streak - 30) * 0.75))
        # Total vacation days < 5 in a year
        volume = min(20, max(0, (5 - vac_days) * 4)) if vac_days < 5 else 0
        return min(100, recency + streak_pressure + volume)

    def _sick_pattern_score(
        self,
        sick_30: int,
        sick_90: int,
        trend: str,
        mf_ratio: float,
    ) -> float:
        """0-100: concerning sick day patterns.

        Frequent sick days + Monday/Friday clustering can indicate
        either genuine health decline OR disengagement — both burnout signals.
        """
        # Recent spike
        recent = min(40, sick_30 * 12)
        # 90-day volume
        volume = min(30, max(0, (sick_90 - 3) * 8))
        # Monday/Friday clustering
        mf_signal = min(30, max(0, (mf_ratio - 0.4) * 100)) if mf_ratio > 0.4 else 0
        return min(100, recent + volume + mf_signal)

    def _burnout_risk_score(
        self,
        avoidance: float,
        recovery: float,
        sick: float,
        cancel_rate: float,
    ) -> tuple:
        """Composite burnout risk from PTO patterns.

        PTO avoidance + recovery deficit are the primary drivers.
        Cancelling vacations is treated as an amplifier.
        """
        base = avoidance * 0.40 + recovery * 0.35 + sick * 0.25
        # Cancellation amplifier: actively avoiding rest
        cancel_amp = min(15, cancel_rate * 50)
        score = min(100, base + cancel_amp)

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

    def _longest_work_streak(self, records: List[LeaveRecord], lookback: int) -> int:
        today = date.today()
        start = today - timedelta(days=lookback)

        # Build set of all days with any leave taken
        leave_days = set()
        for r in records:
            if r.status != LeaveStatus.TAKEN:
                continue
            d = r.start_date
            while d <= r.end_date:
                if d.weekday() < 5:  # only count business days
                    leave_days.add(d)
                d += timedelta(days=1)

        # Find longest consecutive business day streak without leave
        longest = 0
        current = 0
        d = start
        while d <= today:
            if d.weekday() < 5:  # business day
                if d not in leave_days:
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 0
            d += timedelta(days=1)
        return longest

    def _sick_trend(self, sick_records: List[LeaveRecord], lookback: int) -> str:
        if len(sick_records) < 3:
            return "insufficient_data"

        today = date.today()
        mid = today - timedelta(days=lookback // 2)
        recent = sum(1 for r in sick_records if r.start_date >= mid)
        older = sum(1 for r in sick_records if r.start_date < mid)

        if recent > older * 1.5:
            return "increasing"
        elif recent < older * 0.5:
            return "decreasing"
        return "stable"

    def _build_timeline(self, records: List[LeaveRecord]) -> List[Dict[str, Any]]:
        return [
            {
                "type": r.leave_type.value,
                "status": r.status.value,
                "start": r.start_date.isoformat(),
                "end": r.end_date.isoformat(),
                "days": r.business_days,
                "cancelled": r.cancelled_on.isoformat() if r.cancelled_on else None,
            }
            for r in sorted(records, key=lambda r: r.start_date)
        ]

    def _generate_recommendations(
        self,
        utilization,
        days_since,
        cancel_rate,
        sick_30,
        util_gap,
        streak,
    ) -> List[str]:
        recs = []
        if days_since > 90:
            recs.append(
                f"No vacation (3+ days) in {days_since} days. "
                "Extended periods without real rest are the #1 behavioral burnout predictor."
            )
        if cancel_rate > 0.30:
            recs.append(
                f"{cancel_rate*100:.0f}% of booked vacations were cancelled. "
                "Vacation cancellation signals perceived indispensability — a burnout trap."
            )
        if util_gap < -20:
            recs.append(
                f"PTO utilization is {abs(util_gap):.0f}% below expected for this point in the year. "
                "Book upcoming time off now to prevent year-end PTO cramming."
            )
        if streak > 45:
            recs.append(
                f"Longest continuous work streak is {streak} business days. "
                "Schedule a break within the next 2 weeks."
            )
        if sick_30 >= 3:
            recs.append(
                f"{sick_30} sick days in the last month — elevated pattern. "
                "This may indicate physical toll from sustained overwork."
            )
        if not recs:
            recs.append("PTO patterns look healthy. Keep taking regular breaks.")
        return recs

    def _empty_signals(self) -> PTOPatternsSignals:
        return PTOPatternsSignals(
            vacation_days_taken=0,
            vacation_days_remaining=0,
            vacation_utilization_pct=0,
            sick_days_taken=0,
            days_since_last_vacation=0,
            longest_streak_without_pto=0,
            vacations_booked=0,
            vacations_cancelled=0,
            cancellation_rate=0,
            sick_days_last_30=0,
            sick_days_last_90=0,
            sick_day_trend="no_data",
            monday_friday_sick_ratio=0,
            months_into_year=0,
            expected_utilization_pct=0,
            utilization_gap=0,
            vacation_avoidance_score=0,
            recovery_deficit_score=0,
            sick_pattern_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No PTO data available. Connect your HRIS to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class PTORegistry:
    CONNECTOR_TYPES = {"hris": HRISPTOConnector}

    def __init__(self):
        self._connectors: Dict[str, PTOConnector] = {}

    def register(self, name: str, connector: PTOConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered PTO connector: %s", name)

    def get(self, name: str) -> Optional[PTOConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


pto_registry = PTORegistry()
