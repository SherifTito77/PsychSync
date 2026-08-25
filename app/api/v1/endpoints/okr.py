"""
OKR (Objectives & Key Results) API

Endpoints for creating objectives, tracking key results,
updating progress, and retrieving OKR summaries.
"""

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.okr_service import OKRService
from app.services.security import get_current_user

router = APIRouter(prefix="/okr", tags=["OKR"])


# ── Request schemas ──────────────────────────────────────────────


class CreateObjectiveRequest(BaseModel):
    title: str
    objective_type: str = Field(
        ..., pattern="^(growth|excellence|innovation|enterprise)$"
    )
    period: str = Field(..., pattern="^(q1|q2|q3|q4|h1|h2|annual)$")
    year: int
    start_date: datetime
    end_date: datetime
    organization_id: Optional[UUID] = None
    team: Optional[str] = None
    description: Optional[str] = None
    strategic_priority: Optional[str] = None
    parent_objective_id: Optional[UUID] = None
    tags: Optional[List[str]] = None


class CreateKeyResultRequest(BaseModel):
    objective_id: UUID
    title: str
    target_value: float
    unit_of_measure: str
    start_date: datetime
    end_date: datetime
    baseline_value: Optional[float] = None
    description: Optional[str] = None
    weight: float = 1.0


class UpdateKRProgressRequest(BaseModel):
    current_value: float
    notes: Optional[str] = None
    blockers: Optional[str] = None
    next_steps: Optional[str] = None
    confidence_level: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    sentiment: Optional[str] = Field(None, pattern="^(positive|neutral|negative)$")


# ── Endpoints ────────────────────────────────────────────────────


@router.post("/objectives")
async def create_objective(
    req: CreateObjectiveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new objective."""
    from app.db.models.okr import OKRPeriod

    svc = OKRService(db)
    obj = await svc.create_objective(
        title=req.title,
        owner_id=current_user.id,
        period=OKRPeriod(req.period),
        year=req.year,
        start_date=req.start_date,
        end_date=req.end_date,
        objective_type=req.objective_type,
        organization_id=req.organization_id,
        team=req.team,
        description=req.description,
        strategic_priority=req.strategic_priority,
        parent_objective_id=req.parent_objective_id,
        tags=req.tags,
    )
    return {"id": str(obj.id), "title": obj.title, "status": obj.status.value}


@router.post("/key-results")
async def create_key_result(
    req: CreateKeyResultRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a key result for an objective."""
    svc = OKRService(db)
    try:
        kr = await svc.create_key_result(
            objective_id=req.objective_id,
            title=req.title,
            owner_id=current_user.id,
            target_value=req.target_value,
            unit_of_measure=req.unit_of_measure,
            start_date=req.start_date,
            end_date=req.end_date,
            baseline_value=req.baseline_value,
            description=req.description,
            weight=req.weight,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": str(kr.id),
        "title": kr.title,
        "status": kr.status.value,
        "progress": kr.progress_percentage,
    }


@router.patch("/key-results/{key_result_id}/progress")
async def update_kr_progress(
    key_result_id: UUID,
    req: UpdateKRProgressRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a key result's progress."""
    svc = OKRService(db)
    try:
        kr = await svc.update_key_result_progress(
            key_result_id=key_result_id,
            current_value=req.current_value,
            updated_by=current_user.id,
            notes=req.notes,
            blockers=req.blockers,
            next_steps=req.next_steps,
            confidence_level=req.confidence_level,
            sentiment=req.sentiment,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "id": str(kr.id),
        "status": kr.status.value,
        "progress": kr.progress_percentage,
        "current_value": kr.current_value,
        "target_value": kr.target_value,
    }


@router.get("/summary")
async def get_okr_summary(
    period: str = Query(..., pattern="^(q1|q2|q3|q4|h1|h2|annual)$"),
    year: int = Query(...),
    organization_id: Optional[UUID] = None,
    team: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get OKR summary for a period with health indicators."""
    from app.db.models.okr import OKRPeriod

    svc = OKRService(db)
    return await svc.get_okr_summary(
        period=OKRPeriod(period),
        year=year,
        organization_id=organization_id,
        team=team,
    )
