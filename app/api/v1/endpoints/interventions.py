# app/api/v1/endpoints/interventions.py
"""
Intervention Plan Endpoints

Closed-loop intervention tracking: create from Pulse, track progress,
measure outcomes against source BI metrics.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.intervention_plans import InterventionPlan, InterventionStatus
from app.services.intervention_service import intervention_service
from app.services.security import get_current_user

router = APIRouter(prefix="/interventions", tags=["interventions"])


class CheckInRequest(BaseModel):
    progress_notes: Optional[str] = None
    blockers: Optional[str] = None
    metric_value: Optional[float] = None


class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


@router.get("/{organization_id}", response_model=dict[str, Any])
async def get_interventions(
    organization_id: UUID,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all interventions for an organization with summary stats."""
    return await intervention_service.get_organization_interventions(
        db, organization_id, status=status, limit=limit
    )


@router.post("/{organization_id}/measure", response_model=dict[str, Any])
async def measure_intervention_outcomes(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Measure outcomes for active interventions.
    Re-queries source BI metrics to determine if interventions improved scores.
    """
    results = await intervention_service.measure_outcomes(db, organization_id)
    return {
        "organization_id": str(organization_id),
        "measured": len(results),
        "results": results,
    }


@router.post("/{intervention_id}/check-in", response_model=dict[str, Any])
async def add_intervention_check_in(
    intervention_id: UUID,
    body: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a progress check-in to an intervention."""
    check_in = await intervention_service.add_check_in(
        db,
        intervention_id,
        checked_by=current_user.id,
        progress_notes=body.progress_notes,
        blockers=body.blockers,
        metric_value=body.metric_value,
    )
    return {
        "id": str(check_in.id),
        "intervention_id": str(intervention_id),
        "status": "recorded",
    }


@router.patch("/{intervention_id}/status", response_model=dict[str, Any])
async def update_intervention_status(
    intervention_id: UUID,
    body: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update intervention status (assigned, in_progress, measuring, resolved, cancelled)."""
    result = await db.execute(
        select(InterventionPlan).where(InterventionPlan.id == intervention_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Intervention not found")

    valid_statuses = {s.value for s in InterventionStatus}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    from datetime import datetime, timezone

    plan.status = body.status
    plan.updated_at = datetime.now(timezone.utc)

    if body.status == InterventionStatus.IN_PROGRESS.value and not plan.started_at:
        plan.started_at = datetime.now(timezone.utc)
    elif body.status == InterventionStatus.RESOLVED.value:
        plan.completed_at = datetime.now(timezone.utc)

    if body.notes:
        plan.notes = body.notes

    await db.commit()
    return {"id": str(intervention_id), "status": plan.status}


@router.patch("/{intervention_id}/assign", response_model=dict[str, Any])
async def assign_intervention(
    intervention_id: UUID,
    assignee_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Assign an intervention to a user."""
    result = await db.execute(
        select(InterventionPlan).where(InterventionPlan.id == intervention_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Intervention not found")

    from datetime import datetime, timezone

    plan.assigned_to = assignee_id
    plan.status = InterventionStatus.ASSIGNED.value
    plan.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": str(intervention_id),
        "assigned_to": str(assignee_id),
        "status": "assigned",
    }
