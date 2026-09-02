# app/api/v1/endpoints/feedback_360.py
"""360-Degree Feedback API — Campaign management, response collection, and reports."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.feedback_360_service import feedback_360_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/feedback-360",
    tags=["360-Degree Feedback"],
)


@router.post("/{organization_id}/rounds")
async def create_round(
    organization_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new 360-feedback campaign."""
    round_ = await feedback_360_service.create_round(
        db,
        organization_id=UUID(organization_id),
        name=payload["name"],
        created_by=current_user.id,
        competency_set=payload.get("competencies"),
        min_raters=payload.get("min_raters", 3),
    )
    await db.commit()
    return {
        "id": str(round_.id),
        "name": round_.name,
        "status": round_.status,
        "competency_set": round_.competency_set,
        "min_raters_per_category": round_.min_raters_per_category,
    }


@router.post("/{organization_id}/rounds/{round_id}/requests")
async def add_requests(
    organization_id: str,
    round_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add rater assignments: {subject_id, raters: [{rater_id, category}]}."""
    reqs = await feedback_360_service.add_feedback_requests(
        db,
        round_id=UUID(round_id),
        subject_id=UUID(payload["subject_id"]),
        raters=payload["raters"],
    )
    await db.commit()
    return {"created": len(reqs)}


@router.post("/{organization_id}/rounds/{round_id}/activate")
async def activate_round(
    organization_id: str,
    round_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Activate a round to start collecting responses."""
    round_ = await feedback_360_service.activate_round(db, UUID(round_id))
    if not round_:
        raise HTTPException(status_code=404, detail="Round not found")
    await db.commit()
    return {"id": str(round_.id), "status": round_.status}


@router.post("/respond/{request_id}")
async def submit_response(
    request_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Submit feedback: {competency_scores: {name: score}, open_ended: str}."""
    response = await feedback_360_service.submit_response(
        db,
        request_id=UUID(request_id),
        competency_scores=payload["competency_scores"],
        open_ended=payload.get("open_ended"),
    )
    if not response:
        raise HTTPException(
            status_code=400, detail="Request not found or already completed"
        )
    await db.commit()
    return {"id": str(response.id), "submitted_at": response.submitted_at.isoformat()}


@router.get("/{organization_id}/rounds/{round_id}/report/{subject_id}")
async def subject_report(
    organization_id: str,
    round_id: str,
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Privacy-safe aggregated report for a subject."""
    return await feedback_360_service.get_subject_report(
        db, UUID(round_id), UUID(subject_id)
    )


@router.get("/{organization_id}/rounds/{round_id}/summary")
async def round_summary(
    organization_id: str,
    round_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Campaign-level completion summary."""
    return await feedback_360_service.get_round_summary(db, UUID(round_id))
