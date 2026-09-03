"""
Toxicity & Burnout Composite Engine

Fuses all signal collectors into unified toxicity and burnout scores.
The key insight: toxicity and burnout are NOT independent variables.
Toxic environments cause burnout, and burned-out managers generate
toxicity. The cross-contamination multiplier captures this feedback loop.

Signal sources:
  Burnout (6 signals):
    - PTO avoidance (25%)
    - Login span expansion / SSO (20%)
    - Break deficit / endpoint (15%)
    - Calendar fragmentation (15%)
    - After-hours VPN/email trend (15%)
    - Code quality degradation / CI (10%)

  Toxicity (7 signals):
    - Speaking imbalance in meetings (20%)
    - Reaction asymmetry in Slack (15%)
    - Code review hostility (15%)
    - 1:1 cancellation asymmetry (15%)
    - Invite exclusion from meetings (15%)
    - Response latency asymmetry (10%)
    - Attrition clustering (10%)

  Cross-contamination: when both scores are elevated on the same
  team, the combined risk is worse than additive.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BurnoutSignalInput:
    """Normalized burnout signals from all collectors."""

    pto_avoidance: Optional[float] = None  # 0-100
    login_span_expansion: Optional[float] = None  # from SSO
    break_deficit: Optional[float] = None  # from endpoint
    calendar_fragmentation: Optional[float] = None  # from calendar
    after_hours_trend: Optional[float] = None  # from VPN/email
    quality_degradation: Optional[float] = None  # from CI/git


@dataclass
class ToxicitySignalInput:
    """Normalized toxicity signals from all collectors."""

    speaking_imbalance: Optional[float] = None  # 0-100, from calendar toxicity
    reaction_asymmetry: Optional[float] = None  # from communication toxicity
    review_hostility: Optional[float] = None  # from code review toxicity
    one_on_one_cancellation: Optional[float] = None  # from calendar toxicity
    invite_exclusion: Optional[float] = None  # from calendar toxicity
    response_asymmetry: Optional[float] = None  # from communication toxicity
    attrition_clustering: Optional[float] = None  # from communication toxicity


@dataclass
class ToxicityBurnoutResult:
    """Combined toxicity + burnout analysis result."""

    # Individual scores
    burnout_score: float  # 0-100
    toxicity_score: float  # 0-100

    # The key differentiator
    combined_risk: float  # 0-100, includes cross-contamination
    cross_contamination_multiplier: float  # 1.0 = no interaction, >1 = amplified

    # Signal breakdown
    burnout_signals: Dict[str, float] = field(default_factory=dict)
    toxicity_signals: Dict[str, float] = field(default_factory=dict)
    active_burnout_sources: int = 0
    active_toxicity_sources: int = 0

    # Labels
    burnout_label: str = "No Data"
    toxicity_label: str = "No Data"
    combined_label: str = "No Data"

    # Overlap patterns (where both are elevated)
    overlap_patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# Burnout signal weights
BURNOUT_WEIGHTS = {
    "pto_avoidance": 0.25,
    "login_span_expansion": 0.20,
    "break_deficit": 0.15,
    "calendar_fragmentation": 0.15,
    "after_hours_trend": 0.15,
    "quality_degradation": 0.10,
}

# Toxicity signal weights
TOXICITY_WEIGHTS = {
    "speaking_imbalance": 0.20,
    "reaction_asymmetry": 0.15,
    "review_hostility": 0.15,
    "one_on_one_cancellation": 0.15,
    "invite_exclusion": 0.15,
    "response_asymmetry": 0.10,
    "attrition_clustering": 0.10,
}


def _label(score: float) -> str:
    if score >= 70:
        return "Critical"
    elif score >= 45:
        return "Elevated"
    elif score >= 25:
        return "Monitor"
    return "Healthy"


def _weighted_score(
    signals: Dict[str, Optional[float]],
    weights: Dict[str, float],
) -> tuple:
    """Compute weighted average, redistributing weight from missing signals."""
    active: Dict[str, float] = {}
    for key, value in signals.items():
        if value is not None and key in weights:
            active[key] = value

    if not active:
        return 0.0, {}, 0

    # Redistribute missing weights proportionally
    total_active_weight = sum(weights[k] for k in active)
    if total_active_weight == 0:
        return 0.0, {}, 0

    score = 0.0
    breakdown: Dict[str, float] = {}
    for key, value in active.items():
        normalized_weight = weights[key] / total_active_weight
        contribution = value * normalized_weight
        score += contribution
        breakdown[key] = round(value, 1)

    return round(score, 1), breakdown, len(active)


def compute_cross_contamination(burnout: float, toxicity: float) -> float:
    """Cross-contamination multiplier for toxicity-burnout feedback loop.

    Uses a sigmoid-product approach: the multiplier ramps smoothly
    from 1.0 (both low) to ~2.0 (both critical). The key insight is
    that the interaction depends on the MINIMUM of the two scores —
    one high + one low doesn't trigger the feedback loop, but both
    elevated creates a self-reinforcing spiral.

    Based on Maslach Burnout Inventory research showing toxic
    environments increase burnout onset rate by ~2.5x.

    Parameters:
        burnout: 0-100 burnout score
        toxicity: 0-100 toxicity score

    Returns:
        float: multiplier >= 1.0 that amplifies combined risk
    """
    import math

    # Use geometric mean — captures "both must be elevated" better
    # than arithmetic mean (one high + one zero = zero interaction)
    joint = math.sqrt(burnout * toxicity) / 100  # 0-1 normalized

    # Sigmoid ramp: slow start, steep middle, plateaus near 2.0
    # f(x) = 1 + (max_boost / (1 + e^(-steepness * (x - midpoint))))
    max_boost = 1.0  # caps multiplier at 2.0
    steepness = 10.0  # sharpness of the transition
    midpoint = 0.45  # inflection point (~both at 45)

    multiplier = 1.0 + max_boost / (1.0 + math.exp(-steepness * (joint - midpoint)))

    return round(multiplier, 3)


def compute_composite(
    burnout_input: BurnoutSignalInput,
    toxicity_input: ToxicitySignalInput,
) -> ToxicityBurnoutResult:
    """Compute combined toxicity + burnout score with cross-contamination."""

    burnout_signals = {
        "pto_avoidance": burnout_input.pto_avoidance,
        "login_span_expansion": burnout_input.login_span_expansion,
        "break_deficit": burnout_input.break_deficit,
        "calendar_fragmentation": burnout_input.calendar_fragmentation,
        "after_hours_trend": burnout_input.after_hours_trend,
        "quality_degradation": burnout_input.quality_degradation,
    }

    toxicity_signals = {
        "speaking_imbalance": toxicity_input.speaking_imbalance,
        "reaction_asymmetry": toxicity_input.reaction_asymmetry,
        "review_hostility": toxicity_input.review_hostility,
        "one_on_one_cancellation": toxicity_input.one_on_one_cancellation,
        "invite_exclusion": toxicity_input.invite_exclusion,
        "response_asymmetry": toxicity_input.response_asymmetry,
        "attrition_clustering": toxicity_input.attrition_clustering,
    }

    burnout_score, burnout_breakdown, burnout_sources = _weighted_score(
        burnout_signals, BURNOUT_WEIGHTS
    )
    toxicity_score, toxicity_breakdown, toxicity_sources = _weighted_score(
        toxicity_signals, TOXICITY_WEIGHTS
    )

    # Cross-contamination
    multiplier = compute_cross_contamination(burnout_score, toxicity_score)
    base_combined = (burnout_score + toxicity_score) / 2
    combined_risk = min(100, base_combined * multiplier)

    # Detect overlap patterns
    overlaps = _detect_overlaps(burnout_input, toxicity_input)

    # Generate recommendations
    recs = _generate_recommendations(
        burnout_score,
        toxicity_score,
        combined_risk,
        burnout_breakdown,
        toxicity_breakdown,
        overlaps,
    )

    return ToxicityBurnoutResult(
        burnout_score=burnout_score,
        toxicity_score=toxicity_score,
        combined_risk=round(combined_risk, 1),
        cross_contamination_multiplier=round(multiplier, 3),
        burnout_signals=burnout_breakdown,
        toxicity_signals=toxicity_breakdown,
        active_burnout_sources=burnout_sources,
        active_toxicity_sources=toxicity_sources,
        burnout_label=_label(burnout_score),
        toxicity_label=_label(toxicity_score),
        combined_label=_label(combined_risk),
        overlap_patterns=overlaps,
        recommendations=recs,
    )


def _detect_overlaps(
    burnout: BurnoutSignalInput,
    toxicity: ToxicitySignalInput,
) -> List[str]:
    """Detect dangerous overlap patterns where burnout meets toxicity."""
    overlaps = []

    # Overwork + Exclusion
    if (burnout.login_span_expansion or 0) > 40 and (
        toxicity.invite_exclusion or 0
    ) > 30:
        overlaps.append(
            "Overwork + Exclusion: person working long hours but being "
            "excluded from meetings. Likely doing invisible/thankless work."
        )

    # High output + No recognition
    if (burnout.after_hours_trend or 0) > 40 and (
        toxicity.reaction_asymmetry or 0
    ) > 40:
        overlaps.append(
            "High output + No recognition: after-hours work combined with "
            "messages being ignored. Flight risk within 90 days."
        )

    # Manager 1:1 drought + After-hours spike
    if (toxicity.one_on_one_cancellation or 0) > 40 and (
        burnout.after_hours_trend or 0
    ) > 40:
        overlaps.append(
            "Manager 1:1 drought + After-hours spike: unsupported employee "
            "compensating by working harder instead of getting help."
        )

    # Review hostility + PTO avoidance
    if (toxicity.review_hostility or 0) > 40 and (burnout.pto_avoidance or 0) > 40:
        overlaps.append(
            "Review hostility + PTO avoidance: person under attack who "
            "won't step away. Freeze response pattern."
        )

    # Meeting domination + team attrition
    if (toxicity.speaking_imbalance or 0) > 50 and (
        toxicity.attrition_clustering or 0
    ) > 30:
        overlaps.append(
            "Meeting domination + team attrition: toxic leader pattern. "
            "The data proves it without a single complaint filed."
        )

    return overlaps


def _generate_recommendations(
    burnout: float,
    toxicity: float,
    combined: float,
    burnout_signals: Dict[str, float],
    toxicity_signals: Dict[str, float],
    overlaps: List[str],
) -> List[str]:
    """Generate prioritized recommendations."""
    recs = []

    if combined >= 70:
        recs.append(
            "URGENT: Combined toxicity-burnout risk is critical. "
            "Immediate intervention recommended — skip-level meetings, "
            "workload audit, and culture assessment."
        )

    if overlaps:
        recs.append(
            f"{len(overlaps)} dangerous overlap pattern(s) detected where "
            "burnout and toxicity reinforce each other. Address the root cause "
            "(usually a management or workload issue) rather than symptoms."
        )

    # Top burnout signal
    if burnout_signals:
        top_burnout = max(burnout_signals, key=burnout_signals.get)
        if burnout_signals[top_burnout] > 50:
            signal_recs = {
                "pto_avoidance": "Mandate minimum PTO usage and track vacation avoidance.",
                "login_span_expansion": "Set session limits and enforce end-of-day disconnection.",
                "break_deficit": "Enable mandatory break reminders every 90 minutes.",
                "calendar_fragmentation": "Implement no-meeting days and protect focus blocks.",
                "after_hours_trend": "Set delayed-send policies and after-hours notification blocks.",
                "quality_degradation": "Reduce sprint commitments and increase code review support.",
            }
            recs.append(signal_recs.get(top_burnout, "Address top burnout signal."))

    # Top toxicity signal
    if toxicity_signals:
        top_toxicity = max(toxicity_signals, key=toxicity_signals.get)
        if toxicity_signals[top_toxicity] > 50:
            signal_recs = {
                "speaking_imbalance": "Implement meeting facilitation and round-robin speaking.",
                "reaction_asymmetry": "Address social exclusion norms in team channels.",
                "review_hostility": "Rotate reviewers and set SLA targets for review turnaround.",
                "one_on_one_cancellation": "Mandate consistent 1:1 cadence with all reports.",
                "invite_exclusion": "Audit recurring meeting invites for exclusion patterns.",
                "response_asymmetry": "Set response time expectations regardless of sender.",
                "attrition_clustering": "Conduct skip-level interviews under flagged managers.",
            }
            recs.append(signal_recs.get(top_toxicity, "Address top toxicity signal."))

    if not recs:
        recs.append(
            "Toxicity and burnout levels are healthy. "
            "Continue monitoring passive signals."
        )

    return recs
