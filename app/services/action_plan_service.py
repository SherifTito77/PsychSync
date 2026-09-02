# app/services/action_plan_service.py
"""
Action Plan Service — Lifecycle management for intelligence-driven actions.

Bridges ephemeral interventions from Pulse Q7 and Manager Intelligence
into persistent, trackable action plans with effectiveness measurement.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.action_plan import (
    ActionPlan,
    ActionPlanPriority,
    ActionPlanSource,
    ActionPlanStatus,
)

logger = logging.getLogger(__name__)


# Priority mapping from source systems to ActionPlanPriority
_PULSE_PRIORITY_MAP = {
    1: ActionPlanPriority.CRITICAL.value,
    2: ActionPlanPriority.HIGH.value,
    3: ActionPlanPriority.MEDIUM.value,
}

_MANAGER_PRIORITY_MAP = {
    "urgent": ActionPlanPriority.CRITICAL.value,
    "high": ActionPlanPriority.HIGH.value,
    "medium": ActionPlanPriority.MEDIUM.value,
    "low": ActionPlanPriority.LOW.value,
}

# Urgency → due date offset
_URGENCY_DAYS = {
    "immediate": 3,
    "this_week": 7,
    "this_month": 30,
}

_TIMEFRAME_DAYS = {
    "This week": 7,
    "Next 2 weeks": 14,
    "Next sprint": 14,
    "This month": 30,
}


class ActionPlanService:
    """Manages the full lifecycle of action plans."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        db: AsyncSession,
        organization_id: UUID,
        owner_id: UUID,
        title: str,
        *,
        source: str = ActionPlanSource.MANUAL.value,
        source_reference_id: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        priority: str = ActionPlanPriority.MEDIUM.value,
        team_id: Optional[UUID] = None,
        due_date: Optional[date] = None,
        related_metric: Optional[str] = None,
        metric_before: Optional[float] = None,
    ) -> ActionPlan:
        plan = ActionPlan(
            organization_id=organization_id,
            owner_id=owner_id,
            title=title,
            source=source,
            source_reference_id=source_reference_id,
            description=description,
            category=category,
            priority=priority,
            team_id=team_id,
            due_date=due_date,
            related_metric=related_metric,
            metric_before=metric_before,
            status=ActionPlanStatus.PROPOSED.value,
        )
        db.add(plan)
        await db.flush()
        return plan

    async def get(self, db: AsyncSession, plan_id: UUID) -> Optional[ActionPlan]:
        result = await db.execute(select(ActionPlan).where(ActionPlan.id == plan_id))
        return result.scalar_one_or_none()

    async def list_for_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        status: Optional[str] = None,
    ) -> List[ActionPlan]:
        q = select(ActionPlan).where(ActionPlan.owner_id == owner_id)
        if status:
            q = q.where(ActionPlan.status == status)
        q = q.order_by(ActionPlan.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    async def list_for_organization(
        self,
        db: AsyncSession,
        organization_id: UUID,
        *,
        status: Optional[str] = None,
        source: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[ActionPlan]:
        q = select(ActionPlan).where(ActionPlan.organization_id == organization_id)
        if status:
            q = q.where(ActionPlan.status == status)
        if source:
            q = q.where(ActionPlan.source == source)
        if priority:
            q = q.where(ActionPlan.priority == priority)
        q = q.order_by(ActionPlan.created_at.desc()).limit(limit)
        result = await db.execute(q)
        return list(result.scalars().all())

    async def list_for_team(
        self,
        db: AsyncSession,
        team_id: UUID,
        status: Optional[str] = None,
    ) -> List[ActionPlan]:
        q = select(ActionPlan).where(ActionPlan.team_id == team_id)
        if status:
            q = q.where(ActionPlan.status == status)
        q = q.order_by(ActionPlan.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Status transitions
    # ------------------------------------------------------------------

    async def transition(
        self,
        db: AsyncSession,
        plan_id: UUID,
        new_status: str,
        *,
        metric_after: Optional[float] = None,
        outcome_notes: Optional[str] = None,
    ) -> Optional[ActionPlan]:
        plan = await self.get(db, plan_id)
        if not plan:
            return None

        now = datetime.now(timezone.utc)
        valid = _VALID_TRANSITIONS.get(plan.status, set())
        if new_status not in valid:
            raise ValueError(
                f"Cannot transition from '{plan.status}' to '{new_status}'. "
                f"Valid: {valid}"
            )

        plan.status = new_status
        plan.updated_at = now

        if new_status == ActionPlanStatus.ACCEPTED.value:
            plan.accepted_at = now
        elif new_status == ActionPlanStatus.IN_PROGRESS.value:
            plan.started_at = now
        elif new_status == ActionPlanStatus.COMPLETED.value:
            plan.completed_at = now
            if metric_after is not None:
                plan.metric_after = metric_after
            if outcome_notes:
                plan.outcome_notes = outcome_notes

        await db.flush()
        return plan

    # ------------------------------------------------------------------
    # Auto-creation from Pulse interventions
    # ------------------------------------------------------------------

    async def create_from_pulse_interventions(
        self,
        db: AsyncSession,
        organization_id: UUID,
        owner_id: UUID,
        interventions: List[Dict[str, Any]],
        bi_scores: Optional[Dict] = None,
    ) -> List[ActionPlan]:
        """Persist Pulse Q7 interventions as trackable action plans."""
        plans = []
        for intervention in interventions:
            team_id = intervention.get("team_id")
            category = intervention.get("category", "general")
            priority = _PULSE_PRIORITY_MAP.get(
                intervention.get("priority", 3),
                ActionPlanPriority.MEDIUM.value,
            )

            # Compute due date from urgency
            urgency = intervention.get("urgency", "this_month")
            days = _URGENCY_DAYS.get(urgency, 30)
            due = date.today() + timedelta(days=days)

            # Extract related metric and its current score from BI
            related_metric = _CATEGORY_TO_METRIC.get(category)
            metric_before = None
            if related_metric and bi_scores:
                score_data = bi_scores.get(related_metric, {})
                metric_before = score_data.get("score")

            plan = await self.create(
                db,
                organization_id=organization_id,
                owner_id=owner_id,
                title=intervention.get("action", "Untitled intervention"),
                source=ActionPlanSource.PULSE_INTERVENTION.value,
                description=intervention.get("details"),
                category=category,
                priority=priority,
                team_id=UUID(team_id) if team_id else None,
                due_date=due,
                related_metric=related_metric,
                metric_before=metric_before,
            )
            plans.append(plan)

        logger.info(
            "Created %d action plans from Pulse interventions for org %s",
            len(plans),
            organization_id,
        )
        return plans

    # ------------------------------------------------------------------
    # Auto-creation from Manager Intelligence
    # ------------------------------------------------------------------

    async def create_from_manager_actions(
        self,
        db: AsyncSession,
        organization_id: UUID,
        owner_id: UUID,
        team_id: UUID,
        action_items: List[Dict[str, Any]],
        bi_scores: Optional[Dict] = None,
    ) -> List[ActionPlan]:
        """Persist Manager Intelligence action items as trackable plans."""
        plans = []
        for item in action_items:
            category = item.get("category", "general")
            priority = _MANAGER_PRIORITY_MAP.get(
                item.get("priority", "medium"),
                ActionPlanPriority.MEDIUM.value,
            )

            timeframe = item.get("timeframe", "This month")
            days = _TIMEFRAME_DAYS.get(timeframe, 30)
            due = date.today() + timedelta(days=days)

            related_metric = _CATEGORY_TO_METRIC.get(category)
            metric_before = None
            if related_metric and bi_scores:
                score_data = bi_scores.get(related_metric, {})
                metric_before = score_data.get("score")

            plan = await self.create(
                db,
                organization_id=organization_id,
                owner_id=owner_id,
                title=item.get("action", "Untitled action"),
                source=ActionPlanSource.MANAGER_INTELLIGENCE.value,
                description=item.get("reason"),
                category=category,
                priority=priority,
                team_id=team_id,
                due_date=due,
                related_metric=related_metric,
                metric_before=metric_before,
            )
            plans.append(plan)

        logger.info(
            "Created %d action plans from Manager Intelligence for team %s",
            len(plans),
            team_id,
        )
        return plans

    # ------------------------------------------------------------------
    # Effectiveness measurement
    # ------------------------------------------------------------------

    async def get_effectiveness_summary(
        self,
        db: AsyncSession,
        organization_id: UUID,
    ) -> Dict[str, Any]:
        """Analyze completed action plans to measure which interventions work."""
        # Gather completed plans with both before/after metrics
        q = select(ActionPlan).where(
            and_(
                ActionPlan.organization_id == organization_id,
                ActionPlan.status == ActionPlanStatus.COMPLETED.value,
                ActionPlan.metric_before.isnot(None),
                ActionPlan.metric_after.isnot(None),
            )
        )
        result = await db.execute(q)
        completed = list(result.scalars().all())

        if not completed:
            return {
                "total_completed": 0,
                "measurable": 0,
                "effectiveness": None,
                "by_source": {},
                "by_category": {},
            }

        # For inverted metrics (lower = better), flip the delta sign
        def _improvement(plan: ActionPlan) -> float:
            delta = float(plan.metric_after) - float(plan.metric_before)
            if plan.related_metric in _INVERTED_METRICS:
                delta = -delta
            return delta

        improvements = [_improvement(p) for p in completed]
        successes = [d for d in improvements if d > 0]

        # Break down by source
        by_source: Dict[str, Dict[str, Any]] = {}
        for p in completed:
            bucket = by_source.setdefault(p.source, {"improvements": [], "count": 0})
            bucket["improvements"].append(_improvement(p))
            bucket["count"] += 1

        source_summary = {}
        for src, data in by_source.items():
            imps = data["improvements"]
            wins = [d for d in imps if d > 0]
            source_summary[src] = {
                "count": data["count"],
                "avg_improvement": round(sum(imps) / len(imps), 1),
                "success_rate": round(len(wins) / len(imps) * 100, 1),
            }

        # Break down by category
        by_category: Dict[str, Dict[str, Any]] = {}
        for p in completed:
            cat = p.category or "uncategorized"
            bucket = by_category.setdefault(cat, {"improvements": [], "count": 0})
            bucket["improvements"].append(_improvement(p))
            bucket["count"] += 1

        category_summary = {}
        for cat, data in by_category.items():
            imps = data["improvements"]
            wins = [d for d in imps if d > 0]
            category_summary[cat] = {
                "count": data["count"],
                "avg_improvement": round(sum(imps) / len(imps), 1),
                "success_rate": round(len(wins) / len(imps) * 100, 1),
            }

        return {
            "total_completed": len(completed),
            "measurable": len(completed),
            "effectiveness": {
                "avg_improvement": round(sum(improvements) / len(improvements), 1),
                "success_rate": round(len(successes) / len(improvements) * 100, 1),
                "best_improvement": round(max(improvements), 1),
                "worst_outcome": round(min(improvements), 1),
            },
            "by_source": source_summary,
            "by_category": category_summary,
        }

    # ------------------------------------------------------------------
    # Summary stats
    # ------------------------------------------------------------------

    async def get_dashboard(
        self,
        db: AsyncSession,
        organization_id: UUID,
    ) -> Dict[str, Any]:
        """Summary dashboard for action plans."""
        all_plans = await self.list_for_organization(db, organization_id, limit=500)

        by_status: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        overdue = 0
        today = date.today()

        for p in all_plans:
            by_status[p.status] = by_status.get(p.status, 0) + 1
            by_source[p.source] = by_source.get(p.source, 0) + 1
            by_priority[p.priority] = by_priority.get(p.priority, 0) + 1
            if (
                p.due_date
                and p.due_date < today
                and p.status
                not in (
                    ActionPlanStatus.COMPLETED.value,
                    ActionPlanStatus.SKIPPED.value,
                )
            ):
                overdue += 1

        return {
            "total": len(all_plans),
            "by_status": by_status,
            "by_source": by_source,
            "by_priority": by_priority,
            "overdue": overdue,
        }


# Singleton
action_plan_service = ActionPlanService()


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

_VALID_TRANSITIONS = {
    ActionPlanStatus.PROPOSED.value: {
        ActionPlanStatus.ACCEPTED.value,
        ActionPlanStatus.SKIPPED.value,
    },
    ActionPlanStatus.ACCEPTED.value: {
        ActionPlanStatus.IN_PROGRESS.value,
        ActionPlanStatus.SKIPPED.value,
    },
    ActionPlanStatus.IN_PROGRESS.value: {
        ActionPlanStatus.COMPLETED.value,
        ActionPlanStatus.SKIPPED.value,
    },
}

_CATEGORY_TO_METRIC = {
    "isolation": "collaboration",
    "manager_effectiveness": "manager_health",
    "retention": "burnout_risk",
    "friction_reduction": "friction_index",
    "change_readiness": "change_readiness",
    "people": "burnout_risk",
    "wellness": "burnout_risk",
    "culture": "psychological_safety",
    "collaboration": "collaboration",
}

# Metrics where lower score = better outcome
_INVERTED_METRICS = {"burnout_risk", "friction_index"}
