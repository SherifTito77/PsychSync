# app/api/v1/endpoints/action_plans.py
"""
Action Plans API — CRUD, status transitions, and effectiveness tracking.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.action_plan_service import action_plan_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/action-plans",
    tags=["Action Plans"],
)


@router.post("/{organization_id}")
async def create_action_plan(
    organization_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a manual action plan."""
    plan = await action_plan_service.create(
        db,
        organization_id=UUID(organization_id),
        owner_id=UUID(payload["owner_id"]),
        title=payload["title"],
        description=payload.get("description"),
        category=payload.get("category"),
        priority=payload.get("priority", "medium"),
        team_id=UUID(payload["team_id"]) if payload.get("team_id") else None,
        due_date=payload.get("due_date"),
        related_metric=payload.get("related_metric"),
    )
    await db.commit()
    return _serialize(plan)


@router.get("/{organization_id}")
async def list_action_plans(
    organization_id: str,
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List action plans for an organization with optional filters."""
    plans = await action_plan_service.list_for_organization(
        db,
        UUID(organization_id),
        status=status,
        source=source,
        priority=priority,
    )
    return [_serialize(p) for p in plans]


@router.get("/{organization_id}/dashboard")
async def action_plan_dashboard(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Summary dashboard: counts by status, source, priority, overdue."""
    return await action_plan_service.get_dashboard(db, UUID(organization_id))


@router.get("/{organization_id}/effectiveness")
async def action_plan_effectiveness(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Effectiveness report: metric improvement from completed actions."""
    return await action_plan_service.get_effectiveness_summary(
        db, UUID(organization_id)
    )


@router.get("/{organization_id}/my-actions")
async def my_action_plans(
    organization_id: str,
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List action plans assigned to the current user."""
    plans = await action_plan_service.list_for_owner(db, current_user.id, status=status)
    return [_serialize(p) for p in plans]


@router.patch("/{organization_id}/{plan_id}/status")
async def update_status(
    organization_id: str,
    plan_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Transition action plan status (proposed→accepted→in_progress→completed)."""
    new_status = payload.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="'status' is required")

    try:
        plan = await action_plan_service.transition(
            db,
            UUID(plan_id),
            new_status,
            metric_after=payload.get("metric_after"),
            outcome_notes=payload.get("outcome_notes"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not plan:
        raise HTTPException(status_code=404, detail="Action plan not found")

    await db.commit()
    return _serialize(plan)


@router.get("/{organization_id}/team/{team_id}")
async def team_action_plans(
    organization_id: str,
    team_id: str,
    status: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List action plans for a specific team."""
    plans = await action_plan_service.list_for_team(db, UUID(team_id), status=status)
    return [_serialize(p) for p in plans]


def _serialize(plan) -> dict[str, Any]:
    return {
        "id": str(plan.id),
        "organization_id": str(plan.organization_id),
        "team_id": str(plan.team_id) if plan.team_id else None,
        "owner_id": str(plan.owner_id),
        "source": plan.source,
        "source_reference_id": plan.source_reference_id,
        "title": plan.title,
        "description": plan.description,
        "category": plan.category,
        "priority": plan.priority,
        "status": plan.status,
        "due_date": plan.due_date.isoformat() if plan.due_date else None,
        "accepted_at": plan.accepted_at.isoformat() if plan.accepted_at else None,
        "started_at": plan.started_at.isoformat() if plan.started_at else None,
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        "related_metric": plan.related_metric,
        "metric_before": float(plan.metric_before) if plan.metric_before else None,
        "metric_after": float(plan.metric_after) if plan.metric_after else None,
        "outcome_notes": plan.outcome_notes,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }
