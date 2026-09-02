"""
Data Normalization Layer — Architectural centerpiece between raw connectors
and intelligence engines.

Problem: PsychSync has 15+ data connectors (HRIS, calendar, Slack, Teams,
email, git, badge, PTO, video conference, knowledge base, SSO, VPN,
endpoint, code review, tickets) each producing their own output formats.
Intelligence engines (BI, Pulse, ONA, Digital Twin) each receive different
raw shapes and do ad-hoc normalization internally.

Solution: This layer standardizes ALL connector outputs into a unified
NormalizedSignal format (0-100 scale, confidence-weighted, timestamped,
scoped) and detects cross-source BehavioralPatterns.

Architecture:
    Raw Connectors
         |
    [Normalizer per category]
         |
    List[NormalizedSignal]  (uniform shape, 0-100 scale)
         |
    [PatternDetector]       (rule-based cross-signal analysis)
         |
    List[BehavioralPattern] (actionable insights)
         |
    Intelligence Engines    (BI, Pulse, ONA, Digital Twin)

Categories:
    workload     — calendar, project mgmt, tickets
    collaboration — Slack, Teams, email, ONA edges
    wellbeing    — PTO, badge access, computer usage, burnout signals
    lifecycle    — HRIS events (tenure, promotions, team changes)
    knowledge    — git, knowledge base, code review
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# CORE DATA STRUCTURES
# ======================================================================


@dataclass
class NormalizedSignal:
    """A single behavioral signal, standardized across all data sources.

    Every signal regardless of origin shares this shape, making them
    directly comparable and composable by intelligence engines.
    """

    source: str  # e.g., "calendar", "slack", "hris", "git"
    category: str  # e.g., "workload", "collaboration", "wellbeing"
    signal_type: str  # e.g., "meeting_load", "after_hours_ratio"
    value: float  # normalized 0-100
    confidence: float  # 0-1 (sparse data = low confidence)
    timestamp: datetime
    scope: str  # "individual", "team", "department", "organization"
    scope_id: str  # UUID of the scoped entity
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralPattern:
    """A detected organizational pattern derived from multiple signals.

    Patterns are higher-order insights that require combining signals
    from different sources — things no single connector can see alone.
    """

    pattern_type: str  # e.g., "overwork", "isolation", "knowledge_hoarding"
    severity: float  # 0-100
    confidence: float  # 0-1
    signals: List[NormalizedSignal] = field(default_factory=list)
    description: str = ""
    recommendation: str = ""
    scope: str = "organization"
    scope_id: str = ""


@dataclass
class DataSourceHealth:
    """Health status of a single data source."""

    source: str
    available: bool
    signal_count: int = 0
    avg_confidence: float = 0.0
    last_data_at: Optional[datetime] = None
    staleness_hours: float = 0.0
    status: str = "unknown"  # "active", "stale", "missing"


@dataclass
class NormalizationResult:
    """Complete output of a normalization run."""

    signals: List[NormalizedSignal] = field(default_factory=list)
    patterns: List[BehavioralPattern] = field(default_factory=list)
    source_health: Dict[str, DataSourceHealth] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    signal_count: int = 0
    pattern_count: int = 0
    source_count: int = 0


# ======================================================================
# NORMALIZER HELPERS
# ======================================================================


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


def _safe_ratio(numerator: float, denominator: float, scale: float = 100.0) -> float:
    """Safe division returning 0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return _clamp(numerator / denominator * scale)


def _confidence_from_count(count: int, min_for_full: int = 20) -> float:
    """Higher sample count = higher confidence, saturating at 1.0."""
    if count <= 0:
        return 0.0
    return _clamp(count / min_for_full, 0.0, 1.0)


def _make_signal(
    source: str,
    category: str,
    signal_type: str,
    value: float,
    confidence: float,
    scope: str,
    scope_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> NormalizedSignal:
    """Convenience factory with clamping."""
    return NormalizedSignal(
        source=source,
        category=category,
        signal_type=signal_type,
        value=_clamp(value),
        confidence=_clamp(confidence, 0.0, 1.0),
        timestamp=datetime.utcnow(),
        scope=scope,
        scope_id=scope_id,
        metadata=metadata or {},
    )


# ======================================================================
# NORMALIZERS — one per data-source category
# ======================================================================


class WorkloadNormalizer:
    """Normalizes calendar, project management, and ticket data into workload signals."""

    def normalize(
        self, raw_data: Dict[str, Any], scope: str = "organization", scope_id: str = ""
    ) -> List[NormalizedSignal]:
        signals: List[NormalizedSignal] = []

        # -- Meeting load: hours in meetings / total work hours --
        calendar = raw_data.get("calendar", {})
        if calendar:
            meeting_hours = calendar.get("meeting_hours_per_week", 0)
            # 40h work week baseline; 100 = entirely in meetings
            meeting_load = _safe_ratio(meeting_hours, 40)
            data_points = calendar.get("total_events", 0)
            signals.append(
                _make_signal(
                    "calendar",
                    "workload",
                    "meeting_load",
                    meeting_load,
                    _confidence_from_count(data_points),
                    scope,
                    scope_id,
                    {"meeting_hours_per_week": meeting_hours},
                )
            )

            # -- Fragmentation: context switches --
            focus_hours = calendar.get("focus_hours_per_week", 0)
            total_hours = calendar.get("total_work_hours", 40)
            # Low focus time relative to total = high fragmentation
            frag = (
                _safe_ratio(total_hours - focus_hours, total_hours)
                if total_hours > 0
                else 0
            )
            signals.append(
                _make_signal(
                    "calendar",
                    "workload",
                    "fragmentation",
                    frag,
                    _confidence_from_count(data_points),
                    scope,
                    scope_id,
                    {"focus_hours_per_week": focus_hours},
                )
            )

            # -- After hours --
            after_hours_ratio = calendar.get("after_hours_ratio", 0)
            # Raw ratio 0-1 → 0-100
            signals.append(
                _make_signal(
                    "calendar",
                    "workload",
                    "after_hours",
                    (
                        after_hours_ratio * 100
                        if after_hours_ratio <= 1
                        else after_hours_ratio
                    ),
                    _confidence_from_count(data_points),
                    scope,
                    scope_id,
                )
            )

            # -- Back-to-back density --
            b2b = calendar.get("back_to_back_rate", 0)
            signals.append(
                _make_signal(
                    "calendar",
                    "workload",
                    "back_to_back_density",
                    b2b * 100 if b2b <= 1 else b2b,
                    _confidence_from_count(data_points),
                    scope,
                    scope_id,
                )
            )

        # -- Deadline pressure from work systems --
        work_systems = raw_data.get("work_systems", {})
        if work_systems:
            overdue = work_systems.get("overdue_items", 0)
            total_items = work_systems.get("total_items", 0)
            deadline_pressure = _safe_ratio(overdue, total_items) if total_items else 0
            signals.append(
                _make_signal(
                    "work_systems",
                    "workload",
                    "deadline_pressure",
                    deadline_pressure,
                    _confidence_from_count(total_items, 10),
                    scope,
                    scope_id,
                    {"overdue": overdue, "total": total_items},
                )
            )

            # -- Workload volume --
            items_per_person = work_systems.get("items_per_person", 0)
            # 15 items/person is heavy; 30+ is critical
            workload_vol = _clamp(items_per_person / 30 * 100)
            signals.append(
                _make_signal(
                    "work_systems",
                    "workload",
                    "workload_volume",
                    workload_vol,
                    _confidence_from_count(total_items, 10),
                    scope,
                    scope_id,
                )
            )

        # -- Cycle time from work systems --
        cycle_times = raw_data.get("cycle_times", {})
        if cycle_times and cycle_times.get("count", 0) > 0:
            avg_days = cycle_times.get("avg_cycle_days", 0)
            # 14 day cycle = 50 (moderate), 30+ = 100
            cycle_score = _clamp(avg_days / 30 * 100)
            signals.append(
                _make_signal(
                    "work_systems",
                    "workload",
                    "cycle_time_pressure",
                    cycle_score,
                    _confidence_from_count(cycle_times["count"], 10),
                    scope,
                    scope_id,
                    {"avg_cycle_days": avg_days},
                )
            )

        return signals


class CollaborationNormalizer:
    """Normalizes Slack, Teams, email, and ONA data into collaboration signals."""

    def normalize(
        self, raw_data: Dict[str, Any], scope: str = "organization", scope_id: str = ""
    ) -> List[NormalizedSignal]:
        signals: List[NormalizedSignal] = []

        # -- Slack collaboration --
        slack = raw_data.get("slack", {})
        if slack:
            channel_breadth = slack.get("channel_breadth", 0)
            total_channels = slack.get("total_channels", 1)
            # Breadth: unique channels active / total available
            breadth_score = _safe_ratio(channel_breadth, total_channels)
            data_points = slack.get("total_messages", 0)
            signals.append(
                _make_signal(
                    "slack",
                    "collaboration",
                    "collaboration_breadth",
                    breadth_score,
                    _confidence_from_count(data_points, 50),
                    scope,
                    scope_id,
                )
            )

            # DM ratio (high DM = potential silos)
            dm_ratio = slack.get("dm_ratio", 0)
            signals.append(
                _make_signal(
                    "slack",
                    "collaboration",
                    "dm_silo_risk",
                    dm_ratio * 100 if dm_ratio <= 1 else dm_ratio,
                    _confidence_from_count(data_points, 50),
                    scope,
                    scope_id,
                )
            )

            # Context switching
            switches = slack.get("context_switching_rate", 0)
            # 20 switches/hour = 100 (excessive)
            switch_score = _clamp(switches / 20 * 100)
            signals.append(
                _make_signal(
                    "slack",
                    "collaboration",
                    "context_switching",
                    switch_score,
                    _confidence_from_count(data_points, 50),
                    scope,
                    scope_id,
                )
            )

        # -- Teams collaboration --
        teams = raw_data.get("teams", {})
        if teams:
            chat_count = teams.get("chat_count", 0)
            call_duration = teams.get("avg_call_duration_min", 0)
            # High call duration relative to work hours
            call_load = _clamp(call_duration / 480 * 100)  # 480 min = 8h
            signals.append(
                _make_signal(
                    "teams",
                    "collaboration",
                    "call_load",
                    call_load,
                    _confidence_from_count(chat_count, 30),
                    scope,
                    scope_id,
                )
            )

        # -- Email collaboration --
        email = raw_data.get("email", {})
        if email:
            response_time_min = email.get("avg_response_time_minutes", 0)
            total_emails = email.get("total_emails", 0)
            # Response latency: <30min=low(10), 30-120=moderate(30-60), 120+=high
            latency_score = _clamp(response_time_min / 240 * 100)
            signals.append(
                _make_signal(
                    "email",
                    "collaboration",
                    "response_latency",
                    latency_score,
                    _confidence_from_count(total_emails, 30),
                    scope,
                    scope_id,
                )
            )

            # Network breadth: internal vs external split
            internal_ratio = email.get("internal_ratio", 0.5)
            # Pure internal = low cross-boundary collaboration
            cross_boundary = (1 - internal_ratio) * 100
            signals.append(
                _make_signal(
                    "email",
                    "collaboration",
                    "cross_boundary",
                    cross_boundary,
                    _confidence_from_count(total_emails, 30),
                    scope,
                    scope_id,
                )
            )

            # Communication volume
            daily_volume = email.get("daily_volume", 0)
            # 100+ emails/day = overload
            volume_score = _clamp(daily_volume / 100 * 100)
            signals.append(
                _make_signal(
                    "email",
                    "collaboration",
                    "communication_volume",
                    volume_score,
                    _confidence_from_count(total_emails, 30),
                    scope,
                    scope_id,
                )
            )

        # -- ONA / cross-team ratio --
        ona = raw_data.get("ona", {})
        if ona:
            cross_team = ona.get("cross_team_ratio", 0)
            total_edges = ona.get("total_edges", 0)
            signals.append(
                _make_signal(
                    "ona",
                    "collaboration",
                    "cross_team_ratio",
                    cross_team * 100 if cross_team <= 1 else cross_team,
                    _confidence_from_count(total_edges, 30),
                    scope,
                    scope_id,
                )
            )

            # Isolation risk: inverse of collaboration breadth
            unique_collaborators = ona.get("unique_collaborators", 0)
            team_size = ona.get("team_size", 1)
            isolation = _clamp(100 - _safe_ratio(unique_collaborators, team_size))
            signals.append(
                _make_signal(
                    "ona",
                    "collaboration",
                    "isolation_risk",
                    isolation,
                    _confidence_from_count(total_edges, 15),
                    scope,
                    scope_id,
                )
            )

        return signals


class WellbeingNormalizer:
    """Normalizes PTO, badge access, computer usage, and burnout signals."""

    def normalize(
        self, raw_data: Dict[str, Any], scope: str = "organization", scope_id: str = ""
    ) -> List[NormalizedSignal]:
        signals: List[NormalizedSignal] = []

        # -- PTO / vacation deficit --
        pto = raw_data.get("pto", {})
        if pto:
            days_available = pto.get("days_available", 0)
            days_taken = pto.get("days_taken", 0)
            utilization = (
                _safe_ratio(days_taken, days_available) if days_available else 0
            )
            # Invert: low utilization = high deficit
            vacation_deficit = _clamp(100 - utilization)
            data_points = max(1, days_available)
            signals.append(
                _make_signal(
                    "pto",
                    "wellbeing",
                    "vacation_deficit",
                    vacation_deficit,
                    _confidence_from_count(data_points, 5),
                    scope,
                    scope_id,
                    {"days_available": days_available, "days_taken": days_taken},
                )
            )

            # Cancellation pattern
            cancellation_rate = pto.get("cancellation_rate", 0)
            signals.append(
                _make_signal(
                    "pto",
                    "wellbeing",
                    "vacation_cancellation",
                    (
                        cancellation_rate * 100
                        if cancellation_rate <= 1
                        else cancellation_rate
                    ),
                    _confidence_from_count(data_points, 3),
                    scope,
                    scope_id,
                )
            )

            # Recovery deficit: days since last real break
            days_since_break = pto.get("days_since_last_vacation", 0)
            # 90 days without a break = 50, 180+ = 100
            recovery_deficit = _clamp(days_since_break / 180 * 100)
            signals.append(
                _make_signal(
                    "pto",
                    "wellbeing",
                    "recovery_deficit",
                    recovery_deficit,
                    _confidence_from_count(data_points, 3),
                    scope,
                    scope_id,
                    {"days_since_last_vacation": days_since_break},
                )
            )

        # -- Badge access (work hour excess) --
        badge = raw_data.get("badge", {})
        if badge:
            avg_hours = badge.get("avg_office_hours", 8)
            data_points = badge.get("total_days", 0)
            # Hours over 8 = excess; 12h avg = 50, 16h+ = 100
            excess = _clamp((avg_hours - 8) / 8 * 100) if avg_hours > 8 else 0
            signals.append(
                _make_signal(
                    "badge",
                    "wellbeing",
                    "work_hour_excess",
                    excess,
                    _confidence_from_count(data_points, 10),
                    scope,
                    scope_id,
                    {"avg_office_hours": avg_hours},
                )
            )

            # Weekend presence
            weekend_ratio = badge.get("weekend_presence_ratio", 0)
            signals.append(
                _make_signal(
                    "badge",
                    "wellbeing",
                    "weekend_presence",
                    weekend_ratio * 100 if weekend_ratio <= 1 else weekend_ratio,
                    _confidence_from_count(data_points, 10),
                    scope,
                    scope_id,
                )
            )

        # -- Computer usage (break deficit) --
        computer = raw_data.get("computer_usage", {})
        if computer:
            break_freq = computer.get("break_frequency", 0)
            data_points = computer.get("total_buckets", 0)
            # Expected: 1 break per 90 min; below = deficit
            expected_breaks = computer.get("expected_breaks", 4)
            deficit = _clamp(100 - _safe_ratio(break_freq, expected_breaks))
            signals.append(
                _make_signal(
                    "computer",
                    "wellbeing",
                    "break_deficit",
                    deficit,
                    _confidence_from_count(data_points, 20),
                    scope,
                    scope_id,
                )
            )

            # Continuous session risk
            max_session_hours = computer.get("max_continuous_session_hours", 0)
            # 4h continuous = 50, 8h+ = 100
            session_risk = _clamp(max_session_hours / 8 * 100)
            signals.append(
                _make_signal(
                    "computer",
                    "wellbeing",
                    "continuous_session_risk",
                    session_risk,
                    _confidence_from_count(data_points, 20),
                    scope,
                    scope_id,
                )
            )

        # -- Burnout composite from metadata signals --
        metadata = raw_data.get("metadata_burnout", {})
        if metadata and metadata.get("metadata_burnout_risk") is not None:
            signals.append(
                _make_signal(
                    "metadata",
                    "wellbeing",
                    "burnout_composite",
                    metadata["metadata_burnout_risk"],
                    _confidence_from_count(
                        metadata.get("_metadata_source_count", 0), 3
                    ),
                    scope,
                    scope_id,
                    {"sources": metadata.get("_metadata_sources", [])},
                )
            )

        return signals


class LifecycleNormalizer:
    """Normalizes HRIS events into lifecycle signals."""

    def normalize(
        self, raw_data: Dict[str, Any], scope: str = "organization", scope_id: str = ""
    ) -> List[NormalizedSignal]:
        signals: List[NormalizedSignal] = []

        hris = raw_data.get("hris", {})
        if not hris:
            return signals

        total_employees = hris.get("total_employees", 0)
        conf = _confidence_from_count(total_employees, 10)

        # -- Tenure --
        avg_tenure_days = hris.get("avg_tenure_days", 0)
        # Normalize: 0-365 days = 0-50 (new org), 365-1825 = 50-100 (mature)
        tenure_score = _clamp(avg_tenure_days / 1825 * 100)
        signals.append(
            _make_signal(
                "hris",
                "lifecycle",
                "tenure_months",
                tenure_score,
                conf,
                scope,
                scope_id,
                {"avg_tenure_days": avg_tenure_days},
            )
        )

        # -- Turnover rate --
        turnover_pct = hris.get("turnover_rate_pct", 0)
        # 20% annual = moderate (50), 40%+ = critical (100)
        turnover_score = _clamp(turnover_pct / 40 * 100)
        signals.append(
            _make_signal(
                "hris",
                "lifecycle",
                "turnover_rate",
                turnover_score,
                conf,
                scope,
                scope_id,
                {"turnover_rate_pct": turnover_pct},
            )
        )

        # -- Leave utilization --
        leave_util = hris.get("avg_leave_utilization_pct", 0)
        # Low utilization = risk; invert so high score = concerning
        leave_concern = _clamp(100 - leave_util)
        signals.append(
            _make_signal(
                "hris",
                "lifecycle",
                "leave_underutilization",
                leave_concern,
                conf,
                scope,
                scope_id,
            )
        )

        # -- Performance score --
        perf = hris.get("avg_performance_score", 0)
        if perf > 0:
            # 0-5 scale → 0-100
            perf_normalized = _clamp(perf / 5 * 100)
            signals.append(
                _make_signal(
                    "hris",
                    "lifecycle",
                    "performance_score",
                    perf_normalized,
                    conf,
                    scope,
                    scope_id,
                )
            )

        # -- Team stability --
        team_changes = hris.get("team_changes_90d", 0)
        team_size = hris.get("avg_team_size", 1)
        # High churn relative to size = instability
        instability = _safe_ratio(team_changes, team_size)
        signals.append(
            _make_signal(
                "hris",
                "lifecycle",
                "team_instability",
                instability,
                conf,
                scope,
                scope_id,
            )
        )

        # -- Flight risk lifecycle composite --
        # Combines low tenure + low performance + high turnover
        flight_components = []
        if avg_tenure_days > 0 and avg_tenure_days < 365:
            flight_components.append(60)  # new hires at risk
        if turnover_pct > 15:
            flight_components.append(min(100, turnover_pct * 2.5))
        if leave_util < 50:
            flight_components.append(70)

        if flight_components:
            flight_risk = sum(flight_components) / len(flight_components)
            signals.append(
                _make_signal(
                    "hris",
                    "lifecycle",
                    "flight_risk_lifecycle",
                    flight_risk,
                    conf * 0.8,  # composite = slightly lower confidence
                    scope,
                    scope_id,
                )
            )

        return signals


class KnowledgeNormalizer:
    """Normalizes git, knowledge base, and code review data into knowledge signals."""

    def normalize(
        self, raw_data: Dict[str, Any], scope: str = "organization", scope_id: str = ""
    ) -> List[NormalizedSignal]:
        signals: List[NormalizedSignal] = []

        # -- Git signals --
        git = raw_data.get("git", {})
        if git:
            total_commits = git.get("total_commits", 0)
            conf = _confidence_from_count(total_commits, 30)

            # Code churn: deletions / additions (high churn = rework)
            additions = git.get("total_additions", 0)
            deletions = git.get("total_deletions", 0)
            churn = _safe_ratio(deletions, additions) if additions > 0 else 0
            signals.append(
                _make_signal(
                    "git",
                    "knowledge",
                    "code_churn",
                    churn,
                    conf,
                    scope,
                    scope_id,
                    {"additions": additions, "deletions": deletions},
                )
            )

            # Work intensity: commits per day
            commits_per_day = git.get("commits_per_day", 0)
            # 10 commits/day = moderate (50), 25+ = intense (100)
            intensity = _clamp(commits_per_day / 25 * 100)
            signals.append(
                _make_signal(
                    "git",
                    "knowledge",
                    "work_intensity",
                    intensity,
                    conf,
                    scope,
                    scope_id,
                )
            )

            # Review bottleneck: avg review wait hours
            review_wait = git.get("avg_review_wait_hours", 0)
            # 4h = moderate (33), 24h = high (100)
            bottleneck = _clamp(review_wait / 24 * 100)
            signals.append(
                _make_signal(
                    "git",
                    "knowledge",
                    "review_bottleneck",
                    bottleneck,
                    conf,
                    scope,
                    scope_id,
                    {"avg_review_wait_hours": review_wait},
                )
            )

            # After-hours commit ratio
            after_hours = git.get("after_hours_commit_ratio", 0)
            signals.append(
                _make_signal(
                    "git",
                    "knowledge",
                    "after_hours_coding",
                    after_hours * 100 if after_hours <= 1 else after_hours,
                    conf,
                    scope,
                    scope_id,
                )
            )

        # -- Knowledge base signals --
        kb = raw_data.get("knowledge_base", {})
        if kb:
            total_activity = kb.get("total_activity", 0)
            conf = _confidence_from_count(total_activity, 20)

            # Knowledge sharing rate: docs created per month
            creation_rate = kb.get("doc_creation_rate", 0)
            # 20 docs/month = healthy team (50), 50+ = very active (100)
            sharing_score = _clamp(creation_rate / 50 * 100)
            signals.append(
                _make_signal(
                    "knowledge_base",
                    "knowledge",
                    "knowledge_sharing_rate",
                    sharing_score,
                    conf,
                    scope,
                    scope_id,
                )
            )

            # Contributor concentration (Gini-like)
            concentration = kb.get("contributor_concentration", 0)
            # High concentration = knowledge hoarding risk (0-1 → 0-100)
            signals.append(
                _make_signal(
                    "knowledge_base",
                    "knowledge",
                    "contributor_concentration",
                    concentration * 100 if concentration <= 1 else concentration,
                    conf,
                    scope,
                    scope_id,
                )
            )

            # Stale content ratio
            stale_ratio = kb.get("stale_content_ratio", 0)
            signals.append(
                _make_signal(
                    "knowledge_base",
                    "knowledge",
                    "stale_content",
                    stale_ratio * 100 if stale_ratio <= 1 else stale_ratio,
                    conf,
                    scope,
                    scope_id,
                )
            )

            # Documentation health: inverse of stale
            doc_health = _clamp(
                100 - (stale_ratio * 100 if stale_ratio <= 1 else stale_ratio)
            )
            signals.append(
                _make_signal(
                    "knowledge_base",
                    "knowledge",
                    "documentation_health",
                    doc_health,
                    conf,
                    scope,
                    scope_id,
                )
            )

        # -- Video conference engagement as knowledge-sharing proxy --
        video = raw_data.get("video_conference", {})
        if video:
            camera_rate = video.get("camera_on_rate", 0)
            meetings_count = video.get("total_meetings", 0)
            engagement = camera_rate * 100 if camera_rate <= 1 else camera_rate
            signals.append(
                _make_signal(
                    "video_conference",
                    "knowledge",
                    "meeting_engagement",
                    engagement,
                    _confidence_from_count(meetings_count, 10),
                    scope,
                    scope_id,
                )
            )

        return signals


# ======================================================================
# PATTERN DETECTION — rule-based cross-signal analysis
# ======================================================================


@dataclass
class PatternRule:
    """A declarative rule that triggers when signal conditions are met.

    conditions: list of (signal_type, operator, threshold) tuples
    operator: ">" or "<"
    All conditions must match for the pattern to fire.
    """

    pattern_type: str
    conditions: List[tuple]  # [(signal_type, ">"|"<", threshold), ...]
    min_confidence: float  # minimum avg confidence across matched signals
    severity_formula: str  # "avg", "max", or "weighted"
    description: str
    recommendation: str


# Default pattern rules — new rules can be added without code changes
_DEFAULT_RULES: List[PatternRule] = [
    PatternRule(
        pattern_type="calendar_overload",
        conditions=[("meeting_load", ">", 70), ("fragmentation", ">", 60)],
        min_confidence=0.3,
        severity_formula="avg",
        description="Excessive meeting load combined with high calendar fragmentation. "
        "Team members lack focused work time.",
        recommendation="Audit recurring meetings for necessity. Institute 'no meeting' blocks "
        "of at least 2 hours daily. Cancel meetings with no clear agenda.",
    ),
    PatternRule(
        pattern_type="team_silos",
        conditions=[("isolation_risk", ">", 70), ("cross_team_ratio", "<", 20)],
        min_confidence=0.3,
        severity_formula="avg",
        description="Low cross-team collaboration with high isolation risk. "
        "Knowledge and relationships are siloed within teams.",
        recommendation="Create cross-functional project groups. Schedule inter-team demos. "
        "Rotate people across teams for short-term projects.",
    ),
    PatternRule(
        pattern_type="burnout_risk",
        conditions=[("after_hours", ">", 50), ("vacation_deficit", ">", 40)],
        min_confidence=0.3,
        severity_formula="max",
        description="Significant after-hours work combined with unused vacation time. "
        "Classic burnout precursor pattern.",
        recommendation="Encourage mandatory time off. Review workload distribution. "
        "Address cultural norms around always-on availability.",
    ),
    PatternRule(
        pattern_type="career_stagnation",
        conditions=[("tenure_months", ">", 66), ("performance_score", "<", 40)],
        min_confidence=0.4,
        severity_formula="avg",
        description="Long-tenured employees with declining performance. "
        "May indicate career stagnation or disengagement.",
        recommendation="Conduct career development conversations. Offer skill-building "
        "opportunities. Consider role rotation or stretch assignments.",
    ),
    PatternRule(
        pattern_type="knowledge_hoarding",
        conditions=[
            ("contributor_concentration", ">", 70),
            ("review_bottleneck", ">", 60),
        ],
        min_confidence=0.3,
        severity_formula="avg",
        description="Knowledge concentrated in few individuals with slow review cycles. "
        "High bus factor risk.",
        recommendation="Implement pair programming rotations. Document tribal knowledge. "
        "Spread code ownership across more contributors.",
    ),
    PatternRule(
        pattern_type="communication_overload",
        conditions=[("communication_volume", ">", 70), ("context_switching", ">", 60)],
        min_confidence=0.3,
        severity_formula="avg",
        description="High message volume combined with frequent context switching. "
        "Information overload reducing deep work capacity.",
        recommendation="Consolidate communication channels. Establish async-first norms. "
        "Batch notifications to reduce interruptions.",
    ),
    PatternRule(
        pattern_type="workload_spike",
        conditions=[("deadline_pressure", ">", 60), ("work_hour_excess", ">", 40)],
        min_confidence=0.3,
        severity_formula="max",
        description="Rising deadline pressure with extended work hours. "
        "Team may be under-resourced for current commitments.",
        recommendation="Reassess sprint/project scope. Consider temporary resource "
        "reallocation. Prioritize ruthlessly — cut scope, not quality.",
    ),
    PatternRule(
        pattern_type="disengagement_drift",
        conditions=[("vacation_cancellation", ">", 50), ("recovery_deficit", ">", 60)],
        min_confidence=0.3,
        severity_formula="avg",
        description="Employees booking then cancelling time off while going long stretches "
        "without breaks. Signals guilt-driven overwork.",
        recommendation="Normalize time off from leadership down. Make PTO non-negotiable "
        "during critical recovery windows.",
    ),
    PatternRule(
        pattern_type="collaboration_bottleneck",
        conditions=[("review_bottleneck", ">", 70), ("response_latency", ">", 60)],
        min_confidence=0.3,
        severity_formula="avg",
        description="Slow code reviews and slow message responses across the organization. "
        "Collaboration is bottlenecked.",
        recommendation="Set SLAs for code review turnaround. Reduce WIP limits. "
        "Audit whether key people are spread too thin.",
    ),
    PatternRule(
        pattern_type="weekend_creep",
        conditions=[("weekend_presence", ">", 30), ("after_hours_coding", ">", 40)],
        min_confidence=0.3,
        severity_formula="max",
        description="Regular weekend office presence combined with after-hours code commits. "
        "Work-life boundaries are eroding.",
        recommendation="Audit on-call schedules. Ensure weekend work is truly necessary. "
        "Model healthy boundaries from management.",
    ),
]


class PatternDetector:
    """Detects organizational patterns from normalized signals using configurable rules."""

    def __init__(self, rules: Optional[List[PatternRule]] = None):
        self.rules = rules if rules is not None else _DEFAULT_RULES

    def detect_patterns(
        self,
        signals: List[NormalizedSignal],
        scope: str = "organization",
        scope_id: str = "",
    ) -> List[BehavioralPattern]:
        if not signals:
            return []

        # Index signals by type for O(1) lookup
        signal_index: Dict[str, NormalizedSignal] = {}
        for s in signals:
            signal_index[s.signal_type] = s

        patterns: List[BehavioralPattern] = []

        for rule in self.rules:
            matched_signals: List[NormalizedSignal] = []
            all_conditions_met = True

            for signal_type, operator, threshold in rule.conditions:
                sig = signal_index.get(signal_type)
                if sig is None:
                    all_conditions_met = False
                    break

                if operator == ">" and sig.value <= threshold:
                    all_conditions_met = False
                    break
                elif operator == "<" and sig.value >= threshold:
                    all_conditions_met = False
                    break

                matched_signals.append(sig)

            if not all_conditions_met or not matched_signals:
                continue

            # Check minimum confidence
            avg_conf = sum(s.confidence for s in matched_signals) / len(matched_signals)
            if avg_conf < rule.min_confidence:
                continue

            # Compute severity
            values = [s.value for s in matched_signals]
            if rule.severity_formula == "max":
                severity = max(values)
            elif rule.severity_formula == "weighted":
                # Weight by confidence
                severity = sum(s.value * s.confidence for s in matched_signals) / sum(
                    s.confidence for s in matched_signals
                )
            else:  # "avg"
                severity = sum(values) / len(values)

            patterns.append(
                BehavioralPattern(
                    pattern_type=rule.pattern_type,
                    severity=round(_clamp(severity), 1),
                    confidence=round(avg_conf, 3),
                    signals=matched_signals,
                    description=rule.description,
                    recommendation=rule.recommendation,
                    scope=scope,
                    scope_id=scope_id,
                )
            )

        # Sort by severity descending
        patterns.sort(key=lambda p: p.severity, reverse=True)
        return patterns


# ======================================================================
# MAIN ORCHESTRATOR
# ======================================================================


class DataNormalizationService:
    """Orchestrates normalization across all data sources.

    Takes raw connector outputs (as gathered by DataSourceAggregator),
    standardizes them into NormalizedSignals, detects cross-source
    patterns, and reports data source health.
    """

    def __init__(self):
        self.normalizers: Dict[str, Any] = {
            "workload": WorkloadNormalizer(),
            "collaboration": CollaborationNormalizer(),
            "wellbeing": WellbeingNormalizer(),
            "lifecycle": LifecycleNormalizer(),
            "knowledge": KnowledgeNormalizer(),
        }
        self.pattern_detector = PatternDetector()

    async def normalize_all(
        self,
        org_id: str,
        raw_data: Dict[str, Any],
        scope: str = "organization",
    ) -> NormalizationResult:
        """Takes raw data from all sources, returns normalized signals + detected patterns.

        Args:
            org_id: Organization UUID string.
            raw_data: Dict keyed by source category with raw connector outputs.
                Expected top-level keys (all optional):
                    calendar, work_systems, cycle_times,
                    slack, teams, email, ona,
                    pto, badge, computer_usage, metadata_burnout,
                    hris,
                    git, knowledge_base, video_conference
            scope: Scope level for generated signals.

        Returns:
            NormalizationResult with signals, patterns, and source health.
        """
        all_signals: List[NormalizedSignal] = []

        for category, normalizer in self.normalizers.items():
            try:
                category_signals = normalizer.normalize(
                    raw_data, scope=scope, scope_id=org_id
                )
                all_signals.extend(category_signals)
            except Exception as exc:
                logger.warning(
                    "Normalizer %s failed for org %s: %s",
                    category,
                    org_id,
                    exc,
                )

        # Detect cross-source patterns
        patterns = self.pattern_detector.detect_patterns(
            all_signals, scope=scope, scope_id=org_id
        )

        # Report source health
        source_health = self.get_data_source_health(raw_data)

        active_sources = sum(1 for h in source_health.values() if h.available)

        result = NormalizationResult(
            signals=all_signals,
            patterns=patterns,
            source_health=source_health,
            timestamp=datetime.utcnow(),
            signal_count=len(all_signals),
            pattern_count=len(patterns),
            source_count=active_sources,
        )

        logger.info(
            "DataNormalizationService: org=%s signals=%d patterns=%d sources=%d",
            org_id,
            len(all_signals),
            len(patterns),
            active_sources,
        )

        return result

    async def get_signal_summary(
        self, org_id: str, signals: List[NormalizedSignal]
    ) -> Dict[str, Any]:
        """Aggregates signals into category-level scores.

        Returns a dict like:
            {
                "workload": {"score": 62.3, "signal_count": 5, "avg_confidence": 0.78},
                "collaboration": {"score": 45.1, ...},
                ...
                "overall": {"score": 53.7, ...}
            }
        """
        if not signals:
            return {"overall": {"score": 0, "signal_count": 0, "avg_confidence": 0}}

        by_category: Dict[str, List[NormalizedSignal]] = {}
        for sig in signals:
            by_category.setdefault(sig.category, []).append(sig)

        summary: Dict[str, Any] = {}
        all_weighted_scores: List[float] = []
        all_weights: List[float] = []

        for category, cat_signals in by_category.items():
            if not cat_signals:
                continue

            # Confidence-weighted average of signal values
            total_weight = sum(s.confidence for s in cat_signals)
            if total_weight == 0:
                avg_score = sum(s.value for s in cat_signals) / len(cat_signals)
            else:
                avg_score = (
                    sum(s.value * s.confidence for s in cat_signals) / total_weight
                )

            avg_conf = sum(s.confidence for s in cat_signals) / len(cat_signals)

            summary[category] = {
                "score": round(avg_score, 1),
                "signal_count": len(cat_signals),
                "avg_confidence": round(avg_conf, 3),
                "signals": [s.signal_type for s in cat_signals],
            }

            all_weighted_scores.append(avg_score * avg_conf)
            all_weights.append(avg_conf)

        # Overall: confidence-weighted average across categories
        if all_weights and sum(all_weights) > 0:
            overall = sum(all_weighted_scores) / sum(all_weights)
        else:
            overall = 0

        summary["overall"] = {
            "score": round(overall, 1),
            "signal_count": len(signals),
            "avg_confidence": round(
                sum(s.confidence for s in signals) / len(signals), 3
            ),
            "category_count": len(by_category),
        }

        return summary

    def get_data_source_health(
        self, raw_data: Dict[str, Any]
    ) -> Dict[str, DataSourceHealth]:
        """Reports which data sources are active, stale, or missing."""
        now = datetime.utcnow()

        # Map raw_data keys to human-readable source names
        source_mapping = {
            "calendar": "Calendar",
            "work_systems": "Work Systems",
            "cycle_times": "Cycle Times",
            "slack": "Slack",
            "teams": "Microsoft Teams",
            "email": "Email",
            "ona": "ONA",
            "pto": "PTO",
            "badge": "Badge Access",
            "computer_usage": "Computer Usage",
            "metadata_burnout": "Metadata Burnout",
            "hris": "HRIS",
            "git": "Git/GitHub",
            "knowledge_base": "Knowledge Base",
            "video_conference": "Video Conference",
        }

        health: Dict[str, DataSourceHealth] = {}

        for key, display_name in source_mapping.items():
            data = raw_data.get(key)

            if data is None or data == {}:
                health[key] = DataSourceHealth(
                    source=display_name,
                    available=False,
                    status="missing",
                )
                continue

            # Try to extract signal count and last timestamp
            signal_count = 0
            last_data_at = None

            if isinstance(data, dict):
                # Look for common count fields
                for count_key in (
                    "total_events",
                    "total_emails",
                    "total_messages",
                    "total_commits",
                    "total_activity",
                    "total_employees",
                    "total_days",
                    "total_buckets",
                    "total_meetings",
                    "count",
                    "total_edges",
                    "total_items",
                ):
                    if count_key in data:
                        signal_count = data[count_key]
                        break

                # Look for timestamp fields
                for ts_key in ("last_event_at", "last_updated", "latest_timestamp"):
                    ts_val = data.get(ts_key)
                    if isinstance(ts_val, datetime):
                        last_data_at = ts_val
                        break

            staleness = 0.0
            if last_data_at:
                staleness = (now - last_data_at).total_seconds() / 3600

            # Determine status
            if signal_count == 0:
                status = "missing"
                available = False
            elif staleness > 72:
                status = "stale"
                available = True
            else:
                status = "active"
                available = True

            avg_conf = _confidence_from_count(signal_count, 20)

            health[key] = DataSourceHealth(
                source=display_name,
                available=available,
                signal_count=signal_count,
                avg_confidence=round(avg_conf, 3),
                last_data_at=last_data_at,
                staleness_hours=round(staleness, 1),
                status=status,
            )

        return health


# Module-level singleton
data_normalization_service = DataNormalizationService()
