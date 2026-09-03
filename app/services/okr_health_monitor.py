# app/services/okr_health_monitor.py
"""
OKR-BI Feedback Loop

Cross-references active OKR objectives with their owning team's
Behavioral Intelligence scores. Flags objectives whose teams show
concerning health signals — burnout, low collaboration, poor manager
health, or high friction — that could undermine OKR achievement.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.okr import Objective, OKRStatus
from app.db.models.team import Team

logger = logging.getLogger(__name__)

# Thresholds for each BI signal
RISK_THRESHOLDS = {
    "burnout_risk": {
        "caution": 50,
        "warning": 65,
        "critical": 80,
        "message": "Team burnout risk is {severity} ({score:.0f}/100). Achievement pace may not be sustainable.",
    },
    "collaboration": {
        # Inverted — low score is bad
        "caution": 50,
        "warning": 40,
        "critical": 25,
        "message": "Team collaboration is {severity} ({score:.0f}/100). Siloed work may slow progress.",
        "inverted": True,
    },
    "manager_health": {
        "caution": 50,
        "warning": 40,
        "critical": 25,
        "message": "Manager health is {severity} ({score:.0f}/100). Leadership gaps may block execution.",
        "inverted": True,
    },
    "friction_index": {
        "caution": 50,
        "warning": 60,
        "critical": 75,
        "message": "Organizational friction is {severity} ({score:.0f}/100). Execution drag expected.",
    },
    "team_health": {
        "caution": 50,
        "warning": 40,
        "critical": 25,
        "message": "Overall team health is {severity} ({score:.0f}/100). Multiple risk factors present.",
        "inverted": True,
    },
    "psychological_safety": {
        "caution": 45,
        "warning": 35,
        "critical": 20,
        "message": "Psychological safety is {severity} ({score:.0f}/100). Team may avoid raising blockers.",
        "inverted": True,
    },
}

SEVERITY_ORDER = {"critical": 3, "warning": 2, "caution": 1, "none": 0}


class OKRHealthMonitor:
    """Monitors active OKR objectives against team BI scores."""

    async def check_organization(
        self, db: AsyncSession, org_id: UUID
    ) -> Dict[str, Any]:
        """
        Check all active objectives in an org against their team's BI scores.
        Updates health_risk_flag on each objective.
        Returns summary of flagged objectives.
        """
        from app.services.behavioral_intelligence_service import (
            BehavioralIntelligenceService,
        )

        bi_service = BehavioralIntelligenceService()

        # Get all active objectives for this org
        objectives = await self._get_active_objectives(db, org_id)
        if not objectives:
            return {
                "organization_id": str(org_id),
                "checked": 0,
                "flagged": 0,
                "objectives": [],
            }

        # Get all teams in org and build name→id+scores map
        team_scores = await self._get_team_scores(db, org_id, bi_service)

        flagged = []
        now = datetime.now(timezone.utc)

        for obj in objectives:
            team_name = obj.team
            if not team_name or team_name not in team_scores:
                obj.health_risk_flag = "none"
                obj.health_risk_signals = []
                obj.health_risk_checked_at = now
                continue

            scores = team_scores[team_name]
            signals = self._evaluate_signals(scores)
            overall_flag = self._determine_overall_flag(signals)

            obj.health_risk_flag = overall_flag
            obj.health_risk_signals = signals
            obj.health_risk_checked_at = now

            if overall_flag != "none":
                flagged.append(
                    {
                        "objective_id": str(obj.id),
                        "title": obj.title,
                        "team": team_name,
                        "progress": round(obj.progress_percentage, 1),
                        "health_risk_flag": overall_flag,
                        "signals": signals,
                    }
                )

        await db.commit()

        # Auto-create action plans for critical OKR health flags
        critical_flagged = [f for f in flagged if f["health_risk_flag"] == "critical"]
        action_plans_created = 0
        if critical_flagged:
            try:
                from app.services.action_plan_service import action_plan_service

                for f in critical_flagged:
                    top_signal = f["signals"][0] if f["signals"] else {}
                    await action_plan_service.create(
                        db,
                        organization_id=org_id,
                        owner_id=org_id,  # Org-level until assigned
                        title=f"OKR at risk: {f['title']}",
                        source="bi_alert",
                        source_reference_id=f["objective_id"],
                        description=(
                            f"Objective '{f['title']}' (team: {f.get('team', 'N/A')}) "
                            f"has critical health risks. "
                            f"Top signal: {top_signal.get('message', 'Multiple risk factors')}"
                        ),
                        category=top_signal.get("signal", "general"),
                        priority="critical",
                        related_metric=top_signal.get("signal"),
                        metric_before=top_signal.get("score"),
                    )
                    action_plans_created += 1
                await db.commit()
            except Exception as e:
                logger.warning("Failed to create action plans for OKR flags: %s", e)

        return {
            "organization_id": str(org_id),
            "checked": len(objectives),
            "flagged": len(flagged),
            "action_plans_created": action_plans_created,
            "objectives": flagged,
        }

    def _evaluate_signals(self, scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """Evaluate BI scores against thresholds, return list of risk signals."""
        signals = []

        for metric, config in RISK_THRESHOLDS.items():
            score = scores.get(metric)
            if score is None or score == 0:
                continue

            inverted = config.get("inverted", False)
            severity = self._classify_severity(score, config, inverted)

            if severity != "none":
                signals.append(
                    {
                        "signal": metric,
                        "score": round(score, 1),
                        "severity": severity,
                        "message": config["message"].format(
                            severity=severity, score=score
                        ),
                    }
                )

        # Sort by severity (critical first)
        signals.sort(key=lambda s: SEVERITY_ORDER.get(s["severity"], 0), reverse=True)
        return signals

    def _classify_severity(self, score: float, config: Dict, inverted: bool) -> str:
        """
        Classify a score into severity level.

        For normal metrics (higher=worse, e.g. burnout): score >= threshold = flagged
        For inverted metrics (lower=worse, e.g. collaboration): score <= threshold = flagged
        """
        if inverted:
            if score <= config["critical"]:
                return "critical"
            elif score <= config["warning"]:
                return "warning"
            elif score <= config["caution"]:
                return "caution"
        else:
            if score >= config["critical"]:
                return "critical"
            elif score >= config["warning"]:
                return "warning"
            elif score >= config["caution"]:
                return "caution"
        return "none"

    def _determine_overall_flag(self, signals: List[Dict]) -> str:
        """Determine overall objective risk flag from individual signals."""
        if not signals:
            return "none"

        max_severity = max(SEVERITY_ORDER.get(s["severity"], 0) for s in signals)

        # Multiple warnings escalate to critical
        warning_count = sum(
            1 for s in signals if s["severity"] in ("warning", "critical")
        )
        if warning_count >= 3 and max_severity < 3:
            max_severity = 3

        for flag, level in SEVERITY_ORDER.items():
            if level == max_severity:
                return flag
        return "none"

    async def _get_active_objectives(
        self, db: AsyncSession, org_id: UUID
    ) -> List[Objective]:
        """Get all active objectives for an organization."""
        result = await db.execute(
            select(Objective).where(
                and_(
                    Objective.organization_id == org_id,
                    Objective.status == OKRStatus.ACTIVE,
                )
            )
        )
        return list(result.scalars().all())

    async def _get_team_scores(
        self, db: AsyncSession, org_id: UUID, bi_service
    ) -> Dict[str, Dict[str, float]]:
        """
        Build a map of team_name → BI scores for all teams in the org.
        Calls each BI metric individually per team.
        """
        result = await db.execute(select(Team).where(Team.organization_id == org_id))
        teams = result.scalars().all()

        score_methods = {
            "team_health": bi_service.calculate_team_health,
            "collaboration": bi_service.calculate_collaboration_score,
            "manager_health": bi_service.calculate_manager_health,
            "psychological_safety": bi_service.calculate_psychological_safety,
            "burnout_risk": bi_service.calculate_burnout_risk,
            "friction_index": bi_service.calculate_friction_index,
        }

        team_scores = {}
        for team in teams:
            scores = {}
            tid = str(team.id)
            for metric_name, method in score_methods.items():
                try:
                    result_data = await method(db, tid)
                    scores[metric_name] = result_data.get("score", 0)
                except Exception:
                    pass
            if scores:
                team_scores[team.name] = scores

        return team_scores


# Singleton
okr_health_monitor = OKRHealthMonitor()
