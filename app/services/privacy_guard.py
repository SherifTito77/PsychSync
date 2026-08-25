"""
Privacy Guard — k-Anonymity enforcement at the aggregation layer.

Enforces minimum group sizes before returning team-level metrics.
This is NOT presentation-layer masking — it suppresses data at the
query/service boundary so downstream consumers never see unsafe metrics.

Thresholds:
  - k=5 for basic metrics (team health, collaboration, change readiness)
  - k=10 for sensitive metrics (burnout risk, psych safety, manager health, friction)

Cross-filter protection: tracks active filters to prevent reconstruction
attacks where intersecting small-group queries reveal individuals.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class Sensitivity(Enum):
    BASIC = "basic"
    SENSITIVE = "sensitive"


# Maps score keys to their sensitivity level
SCORE_SENSITIVITY: Dict[str, Sensitivity] = {
    "team_health": Sensitivity.BASIC,
    "collaboration": Sensitivity.BASIC,
    "change_readiness": Sensitivity.BASIC,
    "manager_health": Sensitivity.SENSITIVE,
    "psychological_safety": Sensitivity.SENSITIVE,
    "friction_index": Sensitivity.SENSITIVE,
    "burnout_risk": Sensitivity.SENSITIVE,
}

K_THRESHOLDS: Dict[Sensitivity, int] = {
    Sensitivity.BASIC: 5,
    Sensitivity.SENSITIVE: 10,
}

SUPPRESSED_PLACEHOLDER = {
    "score": None,
    "label": "Suppressed",
    "suppressed": True,
    "reason": "Insufficient group size for privacy-safe reporting",
}


@dataclass
class SuppressionLog:
    """Audit record of a suppression event."""

    organization_id: str
    team_id: str
    metric: str
    sensitivity: str
    group_size: int
    required_k: int
    action: str  # "suppressed" | "generalized" | "passed"


@dataclass
class PrivacyContext:
    """Tracks active filters for cross-filter reconstruction protection."""

    organization_id: str
    active_filters: Dict[str, Any] = field(default_factory=dict)
    suppression_log: List[SuppressionLog] = field(default_factory=list)
    _seen_groups: Set[str] = field(default_factory=set)

    def add_filter(self, key: str, value: Any) -> None:
        self.active_filters[key] = value

    @property
    def filter_count(self) -> int:
        return len(self.active_filters)


class PrivacyGuard:
    """Enforces k-anonymity on team-level metric aggregations."""

    def __init__(self, k_overrides: Optional[Dict[Sensitivity, int]] = None):
        self.thresholds = {**K_THRESHOLDS, **(k_overrides or {})}

    def get_required_k(self, metric: str) -> int:
        sensitivity = SCORE_SENSITIVITY.get(metric, Sensitivity.SENSITIVE)
        return self.thresholds[sensitivity]

    def apply_suppression(
        self,
        metric: str,
        value: Dict[str, Any],
        group_size: int,
        ctx: PrivacyContext,
    ) -> Dict[str, Any]:
        """Decide whether to pass, generalize, or suppress a metric.

        Three-tier strategy:
          - group_size < k          → hard suppress (return placeholder)
          - k <= group_size < k+3   → generalize (bucket label, no exact score)
          - group_size >= k+3       → pass through

        Cross-filter safety is checked when filters are active — multiple
        simultaneous filters raise the effective k requirement.
        """
        sensitivity = SCORE_SENSITIVITY.get(metric, Sensitivity.SENSITIVE)
        required_k = self.thresholds[sensitivity]

        # Cross-filter escalation: more filters → stricter requirement
        if ctx.filter_count > 1 and not self.check_cross_filter_safety(ctx, group_size):
            action = "suppressed"
            result = {
                **SUPPRESSED_PLACEHOLDER,
                "reason": "Cross-filter reconstruction risk",
            }
        elif group_size < required_k:
            action = "suppressed"
            result = dict(SUPPRESSED_PLACEHOLDER)
        elif group_size < required_k + 3:
            # Borderline zone: strip exact score, return bucketed label
            action = "generalized"
            score = value.get("score")
            if score is not None:
                bucket = self._bucket_score(score, metric)
            else:
                bucket = "Unknown"
            result = {
                "score": None,
                "label": bucket,
                "generalized": True,
                "reason": f"Group size ({group_size}) near threshold — exact score withheld",
            }
        else:
            action = "passed"
            result = value

        ctx.suppression_log.append(
            SuppressionLog(
                organization_id=ctx.organization_id,
                team_id="",  # filled by caller context
                metric=metric,
                sensitivity=sensitivity.value,
                group_size=group_size,
                required_k=required_k,
                action=action,
            )
        )

        if action != "passed":
            logger.info(
                "PrivacyGuard %s metric=%s group_size=%d required_k=%d",
                action,
                metric,
                group_size,
                required_k,
            )

        return result

    @staticmethod
    def _bucket_score(score: float, metric: str) -> str:
        """Convert exact score to a privacy-safe bucket label."""
        # Inverse metrics: lower is better (friction, burnout)
        inverse = metric in ("friction_index", "burnout_risk")
        if inverse:
            if score <= 30:
                return "Low Risk"
            elif score <= 60:
                return "Moderate Risk"
            else:
                return "High Risk"
        else:
            if score >= 70:
                return "Healthy"
            elif score >= 40:
                return "Moderate"
            else:
                return "Needs Attention"

    def guard_team_scores(
        self,
        team_id: str,
        team_name: str,
        member_count: int,
        scores: Dict[str, Dict[str, Any]],
        ctx: PrivacyContext,
    ) -> Dict[str, Dict[str, Any]]:
        """Apply privacy suppression to all scores for a single team.

        Returns a new dict with unsafe scores replaced by suppression placeholders.
        """
        guarded: Dict[str, Dict[str, Any]] = {}
        for metric, value in scores.items():
            guarded[metric] = self.apply_suppression(metric, value, member_count, ctx)
        return guarded

    def guard_dashboard(
        self,
        dashboard: Dict[str, Any],
        ctx: PrivacyContext,
    ) -> Dict[str, Any]:
        """Apply privacy guard to an entire organization dashboard response.

        Walks the team_results list and suppresses per-team scores that
        don't meet k-anonymity thresholds. Org-level aggregates are
        recomputed from non-suppressed teams only.
        """
        teams = dashboard.get("teams", [])
        if not teams:
            return dashboard

        guarded_teams = []
        safe_scores: Dict[str, List[float]] = {k: [] for k in SCORE_SENSITIVITY}

        for team in teams:
            mc = team.get("member_count", 0)
            raw_scores = team.get("scores", {})

            guarded = {}
            for metric, raw_val in raw_scores.items():
                result = self.apply_suppression(
                    metric,
                    (
                        {"score": raw_val}
                        if isinstance(raw_val, (int, float))
                        else raw_val
                    ),
                    mc,
                    ctx,
                )
                guarded[metric] = result
                if not result.get("suppressed") and result.get("score") is not None:
                    safe_scores.setdefault(metric, []).append(result["score"])

            guarded_teams.append({**team, "scores": guarded})

        # Recompute org-level aggregates from non-suppressed teams only
        org_scores = {}
        for metric, values in safe_scores.items():
            if values:
                org_scores[metric] = round(sum(values) / len(values), 1)
            else:
                org_scores[metric] = None

        result = {**dashboard, "teams": guarded_teams}
        if "scores" in result:
            result["scores"] = org_scores
        result["privacy"] = {
            "k_thresholds": {s.value: k for s, k in self.thresholds.items()},
            "teams_suppressed": sum(
                1
                for t in guarded_teams
                if any(
                    v.get("suppressed")
                    for v in t.get("scores", {}).values()
                    if isinstance(v, dict)
                )
            ),
            "total_teams": len(teams),
            "suppression_log_count": len(ctx.suppression_log),
        }
        return result

    def check_cross_filter_safety(self, ctx: PrivacyContext, group_size: int) -> bool:
        """Detect cross-filter reconstruction risk.

        When multiple filters are applied simultaneously (e.g., department +
        tenure band + gender), the intersection can produce groups small
        enough to identify individuals even if each filter alone is safe.
        Each additional filter raises the effective k requirement.
        """
        effective_k = self.thresholds[Sensitivity.SENSITIVE]
        # Each additional filter beyond the first doubles the risk
        if ctx.filter_count > 1:
            effective_k = effective_k + (ctx.filter_count - 1) * 3
        return group_size >= effective_k

    def get_suppression_summary(self, ctx: PrivacyContext) -> Dict[str, Any]:
        """Summary of all suppressions for audit logging."""
        by_action = {"suppressed": 0, "generalized": 0, "passed": 0}
        for log in ctx.suppression_log:
            by_action[log.action] = by_action.get(log.action, 0) + 1
        return {
            "organization_id": ctx.organization_id,
            "total_checks": len(ctx.suppression_log),
            "by_action": by_action,
            "active_filters": ctx.active_filters,
        }
