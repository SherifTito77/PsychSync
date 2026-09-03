# app/services/intervention_service.py
"""
Intervention Service — Closed-Loop Action Management

Auto-creates InterventionPlans from Pulse Q7 interventions,
tracks progress, and measures outcomes against source BI metrics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.intervention_plans import (
    InterventionCheckIn,
    InterventionPlan,
    InterventionPriority,
    InterventionStatus,
)

logger = logging.getLogger(__name__)

# Maps Pulse intervention types to the BI metric they should improve
SIGNAL_TO_METRIC = {
    "team_isolation": "collaboration",
    "manager_burnout": "manager_health",
    "flight_risk": "burnout_risk",  # inverted: lower is better
    "friction": "friction_index",  # inverted: lower is better
    "change_readiness": "change_readiness",
    "burnout_risk": "burnout_risk",
    "collaboration": "collaboration",
    "psychological_safety": "psychological_safety",
}

# Whether lower metric value = improvement (for inverted metrics)
INVERTED_METRICS = {"burnout_risk", "friction_index"}


class InterventionService:
    """Manages the full lifecycle of organizational interventions."""

    async def create_from_pulse(
        self,
        db: AsyncSession,
        org_id: UUID,
        pulse_interventions: List[Dict[str, Any]],
        team_scores: Dict[str, Dict[str, float]],
    ) -> List[InterventionPlan]:
        """
        Auto-create InterventionPlans from Pulse Q7 output.

        Args:
            pulse_interventions: List of intervention dicts from Pulse Q7
            team_scores: Map of team_id → BI scores (for baseline values)
        """
        created = []

        for intervention in pulse_interventions:
            team_id = intervention.get("team_id")
            signal = intervention.get("signal", "")
            priority_str = intervention.get("priority", "this_week")

            # Check for existing active intervention on same signal+team
            existing = await self._find_active(db, org_id, team_id, signal)
            if existing:
                logger.debug(
                    "Skipping duplicate intervention: %s for team %s", signal, team_id
                )
                continue

            # Determine outcome metric and baseline
            outcome_metric = SIGNAL_TO_METRIC.get(signal, signal)
            baseline = None
            target = None
            if team_id and str(team_id) in team_scores:
                scores = team_scores[str(team_id)]
                baseline = scores.get(outcome_metric)
                if baseline is not None:
                    if outcome_metric in INVERTED_METRICS:
                        target = max(0, baseline - 15)  # Aim to reduce by 15 points
                    else:
                        target = min(100, baseline + 15)  # Aim to improve by 15 points

            # Map priority
            priority_map = {
                "immediate": InterventionPriority.IMMEDIATE,
                "this_week": InterventionPriority.THIS_WEEK,
                "this_month": InterventionPriority.THIS_MONTH,
            }
            priority = priority_map.get(priority_str, InterventionPriority.THIS_WEEK)

            # Calculate due date from priority
            due_offsets = {
                InterventionPriority.IMMEDIATE: timedelta(days=3),
                InterventionPriority.THIS_WEEK: timedelta(days=7),
                InterventionPriority.THIS_MONTH: timedelta(days=30),
            }

            plan = InterventionPlan(
                organization_id=org_id,
                team_id=team_id,
                source_signal=signal,
                source_question=intervention.get("source_question"),
                source_severity=intervention.get("severity"),
                title=intervention.get("title", f"Address {signal}"),
                description=intervention.get("description"),
                priority=priority.value,
                intervention_type=intervention.get("type"),
                action_items=intervention.get("actions", []),
                status=InterventionStatus.PENDING.value,
                due_date=datetime.now(timezone.utc)
                + due_offsets.get(priority, timedelta(days=7)),
                outcome_metric=outcome_metric,
                baseline_value=baseline,
                target_value=target,
            )

            db.add(plan)
            created.append(plan)

        if created:
            await db.commit()
            logger.info(
                "Created %d intervention plans for org %s", len(created), org_id
            )

        return created

    async def measure_outcomes(
        self, db: AsyncSession, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Measure outcomes for interventions that are due or past due.
        Re-queries the source BI metric to see if it improved.
        """
        from app.services.behavioral_intelligence_service import (
            BehavioralIntelligenceService,
        )

        bi_service = BehavioralIntelligenceService()

        # Get interventions in "measuring" or past-due "in_progress" status
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(InterventionPlan).where(
                and_(
                    InterventionPlan.organization_id == org_id,
                    InterventionPlan.status.in_(
                        [
                            InterventionStatus.MEASURING.value,
                            InterventionStatus.IN_PROGRESS.value,
                        ]
                    ),
                    InterventionPlan.outcome_metric.isnot(None),
                )
            )
        )
        plans = list(result.scalars().all())

        results = []
        score_methods = {
            "team_health": bi_service.calculate_team_health,
            "collaboration": bi_service.calculate_collaboration_score,
            "manager_health": bi_service.calculate_manager_health,
            "psychological_safety": bi_service.calculate_psychological_safety,
            "burnout_risk": bi_service.calculate_burnout_risk,
            "friction_index": bi_service.calculate_friction_index,
            "change_readiness": bi_service.calculate_change_readiness,
        }

        for plan in plans:
            if not plan.team_id or not plan.outcome_metric:
                continue

            method = score_methods.get(plan.outcome_metric)
            if not method:
                continue

            try:
                score_data = await method(db, str(plan.team_id))
                current = score_data.get("score", 0)

                plan.current_value = current
                plan.outcome_measured_at = now

                # Determine outcome
                if plan.baseline_value is not None:
                    if plan.outcome_metric in INVERTED_METRICS:
                        # Lower is better
                        if current < plan.baseline_value - 5:
                            plan.outcome_result = "improved"
                        elif current > plan.baseline_value + 5:
                            plan.outcome_result = "worsened"
                        else:
                            plan.outcome_result = "unchanged"
                    else:
                        # Higher is better
                        if current > plan.baseline_value + 5:
                            plan.outcome_result = "improved"
                        elif current < plan.baseline_value - 5:
                            plan.outcome_result = "worsened"
                        else:
                            plan.outcome_result = "unchanged"

                # Auto-resolve if improved past target
                if plan.target_value is not None:
                    if plan.outcome_metric in INVERTED_METRICS:
                        target_met = current <= plan.target_value
                    else:
                        target_met = current >= plan.target_value

                    if target_met:
                        plan.status = InterventionStatus.RESOLVED.value
                        plan.completed_at = now

                results.append(
                    {
                        "intervention_id": str(plan.id),
                        "title": plan.title,
                        "metric": plan.outcome_metric,
                        "baseline": plan.baseline_value,
                        "current": current,
                        "target": plan.target_value,
                        "result": plan.outcome_result,
                        "status": plan.status,
                    }
                )
            except Exception as e:
                logger.warning("Failed to measure outcome for %s: %s", plan.id, e)

        await db.commit()
        return results

    async def add_check_in(
        self,
        db: AsyncSession,
        intervention_id: UUID,
        checked_by: UUID,
        progress_notes: Optional[str] = None,
        blockers: Optional[str] = None,
        metric_value: Optional[float] = None,
    ) -> InterventionCheckIn:
        """Add a progress check-in to an intervention."""
        check_in = InterventionCheckIn(
            intervention_id=intervention_id,
            checked_by=checked_by,
            progress_notes=progress_notes,
            blockers=blockers,
            metric_value=metric_value,
        )
        db.add(check_in)

        # Update intervention's current_value if metric provided
        if metric_value is not None:
            result = await db.execute(
                select(InterventionPlan).where(InterventionPlan.id == intervention_id)
            )
            plan = result.scalar_one_or_none()
            if plan:
                plan.current_value = metric_value
                plan.updated_at = datetime.now(timezone.utc)

        await db.commit()
        return check_in

    async def get_organization_interventions(
        self,
        db: AsyncSession,
        org_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get all interventions for an org with summary stats."""
        conditions = [InterventionPlan.organization_id == org_id]
        if status:
            conditions.append(InterventionPlan.status == status)

        result = await db.execute(
            select(InterventionPlan)
            .where(and_(*conditions))
            .order_by(desc(InterventionPlan.created_at))
            .limit(limit)
        )
        plans = result.scalars().all()

        # Summary stats
        total = len(plans)
        by_status = {}
        improved = 0
        for p in plans:
            by_status[p.status] = by_status.get(p.status, 0) + 1
            if p.outcome_result == "improved":
                improved += 1

        return {
            "organization_id": str(org_id),
            "total": total,
            "by_status": by_status,
            "improvement_rate": round(improved / max(total, 1) * 100, 1),
            "interventions": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "team_id": str(p.team_id) if p.team_id else None,
                    "source_signal": p.source_signal,
                    "priority": p.priority,
                    "status": p.status,
                    "outcome_metric": p.outcome_metric,
                    "baseline_value": p.baseline_value,
                    "current_value": p.current_value,
                    "target_value": p.target_value,
                    "outcome_result": p.outcome_result,
                    "due_date": p.due_date.isoformat() if p.due_date else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in plans
            ],
        }

    async def _find_active(
        self, db: AsyncSession, org_id: UUID, team_id: Optional[UUID], signal: str
    ) -> Optional[InterventionPlan]:
        """Find an existing active intervention for the same signal+team."""
        conditions = [
            InterventionPlan.organization_id == org_id,
            InterventionPlan.source_signal == signal,
            InterventionPlan.status.in_(
                [
                    InterventionStatus.PENDING.value,
                    InterventionStatus.ASSIGNED.value,
                    InterventionStatus.IN_PROGRESS.value,
                ]
            ),
        ]
        if team_id:
            conditions.append(InterventionPlan.team_id == team_id)

        result = await db.execute(
            select(InterventionPlan).where(and_(*conditions)).limit(1)
        )
        return result.scalar_one_or_none()


# Singleton
intervention_service = InterventionService()
