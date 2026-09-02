# app/services/employee_lifecycle_service.py
"""
Employee Lifecycle Analytics — organizational patterns from HRIS lifecycle events.

Derives behavioral signals from structural data:
  - Turnover rates (total / voluntary / involuntary / regrettable)
  - Promotion equity across departments
  - Internal mobility and transfer patterns
  - Flight risk from lifecycle indicators
  - Departure clustering and tenure cliff detection

Design principle: "Instead of reading 'John is frustrated with his manager',
PsychSync sees: Team A — Manager changes: 2, Turnover: up, Promotion rate: down."
"""

import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

EVENT_TYPES = {
    "hire",
    "promotion",
    "transfer",
    "role_change",
    "manager_change",
    "leave_start",
    "leave_return",
    "pip",
    "termination",
    "resignation",
}


@dataclass
class LifecycleEvent:
    employee_id: str
    event_type: str  # one of EVENT_TYPES
    event_date: datetime
    department: Optional[str] = None
    team_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LifecycleAnalysis:
    org_id: str
    analysis_period_days: int
    # Organization-level signals
    turnover_rate: float  # annualized
    voluntary_turnover_rate: float
    involuntary_turnover_rate: float
    promotion_rate: float  # promotions / headcount
    internal_mobility_rate: float  # transfers / headcount
    avg_tenure_months: float
    tenure_distribution: Dict[str, int]  # "0-6m", "6-12m", "1-2y", "2-5y", "5y+"
    # Risk signals
    flight_risk_indicators: Dict[str, float]  # by department/team
    manager_change_frequency: float
    new_hire_90day_retention: float
    regrettable_turnover_rate: float
    # Patterns
    departure_clustering: List[Dict[str, Any]]
    promotion_equity: Dict[str, float]  # promotion rates by department
    tenure_cliff: Optional[int]  # month where most departures happen


class EmployeeLifecycleService:
    """Derives organizational behavioral signals from HRIS lifecycle events."""

    async def analyze_lifecycle(
        self,
        db: AsyncSession,
        org_id: str,
        period_days: int = 365,
    ) -> LifecycleAnalysis:
        """Full lifecycle analysis from HRIS events."""
        events = await self._load_events(db, org_id, period_days)
        employees = await self._load_employees(db, org_id)

        headcount = max(len(employees), 1)

        # --- Turnover ---
        departures = [
            e for e in events if e.event_type in ("termination", "resignation")
        ]
        voluntary = [e for e in departures if e.event_type == "resignation"]
        involuntary = [e for e in departures if e.event_type == "termination"]

        annualization = 365 / max(period_days, 1)
        turnover_rate = round((len(departures) / headcount) * annualization * 100, 2)
        voluntary_turnover_rate = round(
            (len(voluntary) / headcount) * annualization * 100, 2
        )
        involuntary_turnover_rate = round(
            (len(involuntary) / headcount) * annualization * 100, 2
        )

        # Regrettable: voluntary departures of employees with tenure > 12 months
        regrettable = [
            e
            for e in voluntary
            if self._get_employee_tenure_months(e.employee_id, employees) > 12
        ]
        regrettable_turnover_rate = round(
            (len(regrettable) / headcount) * annualization * 100, 2
        )

        # --- Promotions & Mobility ---
        promotions = [e for e in events if e.event_type == "promotion"]
        transfers = [e for e in events if e.event_type == "transfer"]
        promotion_rate = round(len(promotions) / headcount * 100, 2)
        internal_mobility_rate = round(len(transfers) / headcount * 100, 2)

        # --- Manager changes ---
        mgr_changes = [e for e in events if e.event_type == "manager_change"]
        manager_change_frequency = round(len(mgr_changes) / headcount, 2)

        # --- Tenure ---
        tenure_months_list = [
            emp.get("tenure_months", 0) for emp in employees if emp.get("tenure_months")
        ]
        avg_tenure_months = round(
            statistics.mean(tenure_months_list) if tenure_months_list else 0, 1
        )
        tenure_distribution = self._compute_tenure_distribution(tenure_months_list)

        # --- 90-day retention ---
        new_hire_90day_retention = self._compute_90day_retention(events)

        # --- Pattern detection ---
        departure_clustering = await self.detect_departure_clusters(events)
        promotion_equity = await self.compute_promotion_equity(events, employees)
        tenure_cliff = await self.compute_tenure_cliff(events)
        flight_risk_indicators = self._compute_flight_risk_by_group(events, employees)

        return LifecycleAnalysis(
            org_id=org_id,
            analysis_period_days=period_days,
            turnover_rate=turnover_rate,
            voluntary_turnover_rate=voluntary_turnover_rate,
            involuntary_turnover_rate=involuntary_turnover_rate,
            promotion_rate=promotion_rate,
            internal_mobility_rate=internal_mobility_rate,
            avg_tenure_months=avg_tenure_months,
            tenure_distribution=tenure_distribution,
            flight_risk_indicators=flight_risk_indicators,
            manager_change_frequency=manager_change_frequency,
            new_hire_90day_retention=new_hire_90day_retention,
            regrettable_turnover_rate=regrettable_turnover_rate,
            departure_clustering=departure_clustering,
            promotion_equity=promotion_equity,
            tenure_cliff=tenure_cliff,
        )

    async def get_team_stability(
        self,
        db: AsyncSession,
        org_id: str,
        team_id: str,
    ) -> Dict[str, Any]:
        """Team-level stability metrics."""
        events = await self._load_events(db, org_id, period_days=365)
        employees = await self._load_employees(db, org_id)

        team_events = [e for e in events if e.team_id == team_id]
        team_employees = [emp for emp in employees if emp.get("team_id") == team_id]
        team_headcount = max(len(team_employees), 1)

        departures = [
            e for e in team_events if e.event_type in ("termination", "resignation")
        ]
        mgr_changes = [e for e in team_events if e.event_type == "manager_change"]
        hires = [e for e in team_events if e.event_type == "hire"]

        tenure_months_list = [
            emp.get("tenure_months", 0)
            for emp in team_employees
            if emp.get("tenure_months")
        ]

        # Recent departures (last 90 days)
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(days=90)
        recent_departures = [e for e in departures if e.event_date >= recent_cutoff]

        return {
            "team_id": team_id,
            "headcount": team_headcount,
            "avg_tenure_months": round(
                statistics.mean(tenure_months_list) if tenure_months_list else 0, 1
            ),
            "tenure_distribution": self._compute_tenure_distribution(
                tenure_months_list
            ),
            "departures_period": len(departures),
            "departures_recent_90d": len(recent_departures),
            "hires_period": len(hires),
            "net_change": len(hires) - len(departures),
            "manager_changes": len(mgr_changes),
            "manager_stability": "unstable" if len(mgr_changes) >= 2 else "stable",
            "turnover_rate": round(len(departures) / team_headcount * 100, 2),
            "stability_score": self._compute_team_stability_score(
                departures=len(departures),
                mgr_changes=len(mgr_changes),
                headcount=team_headcount,
                avg_tenure=(
                    statistics.mean(tenure_months_list) if tenure_months_list else 0
                ),
            ),
        }

    async def detect_departure_clusters(
        self, events: List[LifecycleEvent]
    ) -> List[Dict[str, Any]]:
        """Finds teams/departments with statistically abnormal departure rates.

        Uses z-score: flag if team departure rate > org_mean + 1.5 * std_dev.
        """
        departures = [
            e for e in events if e.event_type in ("termination", "resignation")
        ]
        if not departures:
            return []

        # Count departures per group (prefer team_id, fall back to department)
        group_counts: Dict[str, int] = Counter()
        for dep in departures:
            group = dep.team_id or dep.department or "unknown"
            group_counts[group] += 1

        if len(group_counts) < 2:
            return []

        counts = list(group_counts.values())
        mean = statistics.mean(counts)
        stdev = statistics.stdev(counts) if len(counts) > 1 else 0

        if stdev == 0:
            return []

        clusters = []
        for group, count in group_counts.items():
            z = (count - mean) / stdev
            if z > 1.5:
                clusters.append(
                    {
                        "group": group,
                        "departures": count,
                        "z_score": round(z, 2),
                        "severity": (
                            "critical" if z > 3.0 else "high" if z > 2.0 else "elevated"
                        ),
                        "org_avg_departures": round(mean, 1),
                    }
                )

        clusters.sort(key=lambda c: c["z_score"], reverse=True)
        return clusters

    async def compute_tenure_cliff(self, events: List[LifecycleEvent]) -> Optional[int]:
        """Finds the month where most departures happen (e.g., month 13 = post-1yr cliff).

        Builds a histogram of departure month-since-hire and returns the mode.
        """
        departures = [
            e for e in events if e.event_type in ("termination", "resignation")
        ]
        if len(departures) < 5:
            return None

        # Pair departures with hire events to compute tenure at departure
        hire_dates: Dict[str, datetime] = {}
        for e in events:
            if e.event_type == "hire":
                hire_dates[e.employee_id] = e.event_date

        departure_months = []
        for dep in departures:
            hire_date = hire_dates.get(dep.employee_id)
            if hire_date:
                months = max(1, int((dep.event_date - hire_date).days / 30.44))
                departure_months.append(months)

        if not departure_months:
            return None

        # Find the mode (peak month)
        month_counts = Counter(departure_months)
        peak_month, peak_count = month_counts.most_common(1)[0]

        # Only report as a cliff if it stands out (at least 20% of departures)
        if peak_count / len(departure_months) >= 0.15:
            return peak_month

        return None

    async def compute_promotion_equity(
        self,
        events: List[LifecycleEvent],
        employees: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Promotion rates by department -- flags inequity if deviation > 2x.

        Returns dict of department -> promotion_rate (%).
        """
        promotions = [e for e in events if e.event_type == "promotion"]

        # Count employees per department
        dept_headcount: Dict[str, int] = Counter()
        for emp in employees:
            dept = emp.get("department", "Unknown")
            dept_headcount[dept] += 1

        # Count promotions per department
        dept_promotions: Dict[str, int] = Counter()
        for p in promotions:
            dept = p.department or "Unknown"
            dept_promotions[dept] += 1

        # Compute rates
        rates: Dict[str, float] = {}
        for dept, headcount in dept_headcount.items():
            promo_count = dept_promotions.get(dept, 0)
            rates[dept] = round(promo_count / max(headcount, 1) * 100, 2)

        return rates

    async def get_flight_risk_from_lifecycle(
        self,
        events: List[LifecycleEvent],
        employee_id: str,
    ) -> float:
        """Individual flight risk based on lifecycle patterns.

        Composite: tenure_past_cliff (30%) + no_promotion_18m (25%) +
        peer_departures (20%) + manager_instability (15%) + leave_frequency (10%).
        Returns 0-100.
        """
        now = datetime.now(timezone.utc)
        emp_events = [e for e in events if e.employee_id == employee_id]

        # --- Signal 1: Tenure past cliff (30%) ---
        hire_event = next((e for e in emp_events if e.event_type == "hire"), None)
        tenure_months = 0
        if hire_event:
            tenure_months = int((now - hire_event.event_date).days / 30.44)

        # Tenure cliff risk peaks at 12-18 months, again at 24-30 months
        if tenure_months == 0:
            tenure_risk = 0
        elif 12 <= tenure_months <= 18:
            tenure_risk = 70
        elif 24 <= tenure_months <= 30:
            tenure_risk = 55
        elif tenure_months > 60:
            tenure_risk = 20  # Long-tenured employees lower risk
        else:
            tenure_risk = 35

        # --- Signal 2: No promotion in 18+ months (25%) ---
        promotions = [e for e in emp_events if e.event_type == "promotion"]
        last_promotion = max((p.event_date for p in promotions), default=None)
        if last_promotion:
            months_since_promo = (now - last_promotion).days / 30.44
            no_promo_risk = min(100, max(0, (months_since_promo - 12) * 8))
        elif tenure_months > 18:
            no_promo_risk = 80  # Never promoted + long tenure
        else:
            no_promo_risk = 0

        # --- Signal 3: Peer departures (20%) ---
        # Use same team/department events
        team_id = next((e.team_id for e in emp_events if e.team_id), None)
        dept = next((e.department for e in emp_events if e.department), None)
        peer_departures = [
            e
            for e in events
            if e.event_type in ("termination", "resignation")
            and e.employee_id != employee_id
            and (e.team_id == team_id if team_id else e.department == dept)
            and (now - e.event_date).days <= 180
        ]
        peer_risk = min(100, len(peer_departures) * 25)

        # --- Signal 4: Manager instability (15%) ---
        mgr_changes = [e for e in emp_events if e.event_type == "manager_change"]
        recent_mgr = [e for e in mgr_changes if (now - e.event_date).days <= 365]
        mgr_risk = min(100, len(recent_mgr) * 40)

        # --- Signal 5: Leave frequency (10%) ---
        leaves = [e for e in emp_events if e.event_type == "leave_start"]
        recent_leaves = [e for e in leaves if (now - e.event_date).days <= 365]
        leave_risk = min(100, len(recent_leaves) * 20)

        # Weighted composite
        risk = (
            tenure_risk * 0.30
            + no_promo_risk * 0.25
            + peer_risk * 0.20
            + mgr_risk * 0.15
            + leave_risk * 0.10
        )
        return round(min(100, max(0, risk)), 1)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _load_events(
        self,
        db: AsyncSession,
        org_id: str,
        period_days: int,
    ) -> List[LifecycleEvent]:
        """Load lifecycle events from the database.

        Falls back to an empty list if the lifecycle_events table
        does not exist yet (the system can be deployed incrementally).
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

        try:
            from app.db.models.team import Team, TeamMember
            from app.db.models.user import User

            # Derive hire events from user creation dates
            query = (
                select(
                    User.id,
                    User.created_at,
                    User.full_name,
                    TeamMember.team_id,
                )
                .join(TeamMember, TeamMember.user_id == User.id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(Team.organization_id == org_id)
            )
            result = await db.execute(query)
            rows = result.all()

            events: List[LifecycleEvent] = []
            for row in rows:
                user_id = str(row[0])
                created = row[1]
                team_id = str(row[3]) if row[3] else None

                # Synthesize a hire event for each user
                if created:
                    events.append(
                        LifecycleEvent(
                            employee_id=user_id,
                            event_type="hire",
                            event_date=(
                                created.replace(tzinfo=timezone.utc)
                                if created.tzinfo is None
                                else created
                            ),
                            team_id=team_id,
                        )
                    )

            return events
        except Exception as exc:
            logger.warning("Failed to load lifecycle events: %s", exc)
            return []

    async def _load_employees(
        self,
        db: AsyncSession,
        org_id: str,
    ) -> List[Dict[str, Any]]:
        """Load current employee roster with tenure info."""
        try:
            from app.db.models.team import Team, TeamMember
            from app.db.models.user import User

            query = (
                select(
                    User.id,
                    User.full_name,
                    User.email,
                    User.created_at,
                    TeamMember.team_id,
                )
                .join(TeamMember, TeamMember.user_id == User.id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(Team.organization_id == org_id)
            )
            result = await db.execute(query)
            rows = result.all()

            now = datetime.now(timezone.utc)
            employees = []
            for row in rows:
                created = row[3]
                if created and created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                tenure_months = (now - created).days / 30.44 if created else 0
                employees.append(
                    {
                        "employee_id": str(row[0]),
                        "name": row[1] or row[2] or "Unknown",
                        "email": row[2],
                        "created_at": created,
                        "team_id": str(row[4]) if row[4] else None,
                        "tenure_months": round(tenure_months, 1),
                        "department": None,  # Populated from HRIS if available
                    }
                )

            return employees
        except Exception as exc:
            logger.warning("Failed to load employees: %s", exc)
            return []

    def _get_employee_tenure_months(
        self, employee_id: str, employees: List[Dict[str, Any]]
    ) -> float:
        for emp in employees:
            if emp.get("employee_id") == employee_id:
                return emp.get("tenure_months", 0)
        return 0

    def _compute_tenure_distribution(
        self, tenure_months_list: List[float]
    ) -> Dict[str, int]:
        buckets = {"0-6m": 0, "6-12m": 0, "1-2y": 0, "2-5y": 0, "5y+": 0}
        for m in tenure_months_list:
            if m < 6:
                buckets["0-6m"] += 1
            elif m < 12:
                buckets["6-12m"] += 1
            elif m < 24:
                buckets["1-2y"] += 1
            elif m < 60:
                buckets["2-5y"] += 1
            else:
                buckets["5y+"] += 1
        return buckets

    def _compute_90day_retention(self, events: List[LifecycleEvent]) -> float:
        """Fraction of new hires still present after 90 days."""
        hire_dates: Dict[str, datetime] = {}
        departed: set = set()

        for e in events:
            if e.event_type == "hire":
                hire_dates[e.employee_id] = e.event_date
            elif e.event_type in ("termination", "resignation"):
                departed.add(e.employee_id)

        now = datetime.now(timezone.utc)
        eligible = 0
        retained = 0

        for emp_id, hire_date in hire_dates.items():
            if (now - hire_date).days >= 90:
                eligible += 1
                # Check if they departed within 90 days of hire
                early_departure = any(
                    e.employee_id == emp_id
                    and e.event_type in ("termination", "resignation")
                    and (e.event_date - hire_date).days <= 90
                    for e in events
                )
                if not early_departure:
                    retained += 1

        return round(retained / max(eligible, 1) * 100, 1)

    def _compute_team_stability_score(
        self,
        departures: int,
        mgr_changes: int,
        headcount: int,
        avg_tenure: float,
    ) -> float:
        """0-100 stability score. Higher = more stable."""
        # Turnover penalty: -20 per departure relative to headcount
        turnover_penalty = min(60, (departures / max(headcount, 1)) * 200)
        # Manager instability penalty
        mgr_penalty = min(20, mgr_changes * 10)
        # Tenure bonus: longer avg tenure = more stable
        tenure_bonus = min(20, avg_tenure / 3)

        score = 100 - turnover_penalty - mgr_penalty + tenure_bonus
        return round(max(0, min(100, score)), 1)

    def _compute_flight_risk_by_group(
        self,
        events: List[LifecycleEvent],
        employees: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Aggregate flight risk indicators per team/department."""
        now = datetime.now(timezone.utc)
        groups: Dict[str, List[str]] = defaultdict(list)

        for emp in employees:
            group = emp.get("team_id") or emp.get("department") or "unknown"
            groups[group].append(emp["employee_id"])

        result: Dict[str, float] = {}
        for group, emp_ids in groups.items():
            if not emp_ids:
                continue

            # Simple heuristic: departures in last 6 months / headcount
            recent_departures = [
                e
                for e in events
                if e.event_type in ("termination", "resignation")
                and (e.team_id == group or e.department == group)
                and (now - e.event_date).days <= 180
            ]
            mgr_changes = [
                e
                for e in events
                if e.event_type == "manager_change"
                and (e.team_id == group or e.department == group)
                and (now - e.event_date).days <= 365
            ]

            headcount = len(emp_ids)
            departure_signal = min(50, (len(recent_departures) / headcount) * 100)
            mgr_signal = min(30, len(mgr_changes) * 15)
            risk = departure_signal + mgr_signal

            result[group] = round(min(100, risk), 1)

        return result


# Singleton
employee_lifecycle_service = EmployeeLifecycleService()
