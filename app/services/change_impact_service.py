# app/services/change_impact_service.py
"""
Change Impact Predictor

Predicts how a proposed organizational change will affect each team
by cross-referencing current BI scores with the change type.

Change types and their primary impact dimensions:
  - reorg: collaboration, culture, teams
  - tool_migration: friction, team_health
  - policy_shift: psychological_safety, culture
  - leadership_change: manager_health, engagement, turnover_risk
  - layoff: turnover_risk, engagement, psychological_safety
  - expansion: collaboration, culture (dilution)

Each team's vulnerability is computed from their current BI scores —
teams with low change_readiness or low psych_safety absorb change worse.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.team import Team, TeamMember
from sqlalchemy import func

logger = logging.getLogger(__name__)

# Which BI dimensions each change type stresses (dimension -> base_impact)
CHANGE_STRESS_MAP: Dict[str, Dict[str, float]] = {
    "reorg": {
        "collaboration": -18,
        "culture": -15,
        "teams": -10,
        "engagement": -8,
    },
    "tool_migration": {
        "friction_index": -20,
        "team_health": -10,
        "collaboration": -5,
    },
    "policy_shift": {
        "psychological_safety": -15,
        "culture": -12,
        "change_readiness": -8,
    },
    "leadership_change": {
        "manager_health": -25,
        "engagement": -15,
        "turnover_risk": -12,
        "culture": -8,
    },
    "layoff": {
        "turnover_risk": -25,
        "engagement": -20,
        "psychological_safety": -18,
        "culture": -15,
        "manager_health": -10,
    },
    "expansion": {
        "collaboration": -12,
        "culture": -10,
        "managers": -8,
    },
}

# Dimensions where lower score = worse (inverted for vulnerability calc)
INVERTED_METRICS = {"friction_index", "burnout_risk", "turnover_risk"}


class ChangeImpactService:
    """Predicts per-team impact of proposed organizational changes."""

    async def predict_impact(
        self,
        db: AsyncSession,
        org_id: UUID,
        change_type: str,
        affected_team_ids: Optional[List[UUID]] = None,
        magnitude: float = 1.0,
    ) -> Dict[str, Any]:
        """Predict how a change will affect teams.

        Args:
            org_id: Organization UUID
            change_type: One of the CHANGE_STRESS_MAP keys
            affected_team_ids: Specific teams (None = all teams)
            magnitude: Scale factor (0.5 = minor, 1.0 = standard, 2.0 = major)

        Returns:
            Per-team impact predictions with risk levels and recommendations.
        """
        if change_type not in CHANGE_STRESS_MAP:
            return {
                "error": f"Unknown change type: {change_type}",
                "valid_types": list(CHANGE_STRESS_MAP.keys()),
            }

        stress = CHANGE_STRESS_MAP[change_type]

        # Get teams
        q = select(Team).where(Team.organization_id == str(org_id))
        if affected_team_ids:
            q = q.where(Team.id.in_([str(t) for t in affected_team_ids]))
        result = await db.execute(q)
        teams = result.scalars().all()

        if not teams:
            return {"error": "No teams found"}

        # Get BI scores for vulnerability assessment
        bi_scores = await self._get_bi_scores(db, str(org_id))

        team_impacts = []
        for team in teams:
            tid = str(team.id)

            # Get member count
            mc_result = await db.execute(
                select(func.count())
                .select_from(TeamMember)
                .where(TeamMember.team_id == tid)
            )
            member_count = mc_result.scalar() or 0

            # Get team's BI scores (fall back to org-level)
            team_bi = bi_scores.get(tid, bi_scores.get("org", {}))

            # Compute vulnerability multiplier from change_readiness and psych_safety
            vulnerability = self._compute_vulnerability(team_bi)

            # Apply stress with vulnerability and magnitude
            predicted_deltas = {}
            for dimension, base_impact in stress.items():
                adjusted = base_impact * magnitude * vulnerability
                predicted_deltas[dimension] = round(adjusted, 1)

            # Overall risk score (0-100, higher = more at risk)
            risk_score = self._compute_risk_score(predicted_deltas, vulnerability)

            # Risk level
            if risk_score >= 70:
                risk_level = "critical"
            elif risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 30:
                risk_level = "moderate"
            else:
                risk_level = "low"

            team_impacts.append(
                {
                    "team_id": tid,
                    "team_name": team.name,
                    "member_count": member_count,
                    "vulnerability": round(vulnerability, 2),
                    "risk_score": round(risk_score, 1),
                    "risk_level": risk_level,
                    "predicted_deltas": predicted_deltas,
                    "current_scores": {
                        "change_readiness": team_bi.get("change_readiness"),
                        "psychological_safety": team_bi.get("psychological_safety"),
                        "team_health": team_bi.get("team_health"),
                    },
                    "recommendations": self._generate_recommendations(
                        risk_level, predicted_deltas, team_bi
                    ),
                }
            )

        # Sort by risk
        team_impacts.sort(key=lambda t: t["risk_score"], reverse=True)

        return {
            "organization_id": str(org_id),
            "change_type": change_type,
            "magnitude": magnitude,
            "teams_assessed": len(team_impacts),
            "summary": {
                "critical_teams": sum(
                    1 for t in team_impacts if t["risk_level"] == "critical"
                ),
                "high_risk_teams": sum(
                    1 for t in team_impacts if t["risk_level"] == "high"
                ),
                "avg_risk_score": round(
                    sum(t["risk_score"] for t in team_impacts)
                    / max(len(team_impacts), 1),
                    1,
                ),
            },
            "team_impacts": team_impacts,
        }

    def _compute_vulnerability(self, bi_scores: Dict[str, Any]) -> float:
        """Compute vulnerability multiplier from current BI scores.

        Low change_readiness and low psych_safety = higher vulnerability.
        Returns multiplier: 0.5 (resilient) to 2.0 (highly vulnerable).
        """
        cr = bi_scores.get("change_readiness", 50)
        ps = bi_scores.get("psychological_safety", 50)
        th = bi_scores.get("team_health", 50)

        # Average resilience (0-100)
        resilience = cr * 0.45 + ps * 0.35 + th * 0.20

        # Map to multiplier: 100 resilience → 0.5x, 0 resilience → 2.0x
        return 2.0 - (resilience / 100) * 1.5

    def _compute_risk_score(
        self, deltas: Dict[str, float], vulnerability: float
    ) -> float:
        """Convert predicted deltas to a 0-100 risk score."""
        if not deltas:
            return 0.0
        # Sum of absolute impacts, scaled by vulnerability
        total_impact = sum(abs(d) for d in deltas.values())
        # Normalize: max realistic total impact ~120 points
        normalized = min(total_impact / 120 * 100, 100)
        return normalized

    def _generate_recommendations(
        self,
        risk_level: str,
        deltas: Dict[str, float],
        current_scores: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations based on risk profile."""
        recs = []

        if risk_level in ("critical", "high"):
            recs.append("Conduct pre-change readiness assessment with team leads")

        # Dimension-specific recommendations
        if deltas.get("collaboration", 0) < -10:
            recs.append("Schedule cross-team sync meetings during transition period")

        if deltas.get("psychological_safety", 0) < -10:
            recs.append("Hold transparent Q&A sessions to address team concerns")

        if deltas.get("manager_health", 0) < -15:
            recs.append("Provide manager coaching and transition support resources")

        if deltas.get("turnover_risk", 0) < -10:
            recs.append(
                "Proactively engage high-performers with retention conversations"
            )

        if deltas.get("culture", 0) < -10:
            recs.append("Reinforce cultural values through team rituals during change")

        if deltas.get("engagement", 0) < -15:
            recs.append("Increase 1-on-1 check-in frequency during transition")

        cr = current_scores.get("change_readiness", 50)
        if cr and cr < 40:
            recs.append("Team has low change readiness — consider phased rollout")

        if not recs:
            recs.append("Monitor team sentiment weekly during transition")

        return recs

    async def _get_bi_scores(
        self, db: AsyncSession, org_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get BI scores for all teams and org-level."""
        try:
            from app.services.behavioral_intelligence_service import (
                BehavioralIntelligenceService,
            )

            bi = BehavioralIntelligenceService()
            dashboard = await bi.get_organization_dashboard(db, org_id)

            scores = {}
            # Org-level
            scores["org"] = dashboard.get("scores", {})

            # Per-team
            for team in dashboard.get("teams", []):
                tid = team.get("team_id", "")
                scores[tid] = team.get("scores", {})

            return scores
        except Exception as e:
            logger.warning("BI scores unavailable for change impact: %s", e)
            return {"org": {}}


change_impact_service = ChangeImpactService()
