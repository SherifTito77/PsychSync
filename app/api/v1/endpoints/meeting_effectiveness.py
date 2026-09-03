# app/api/v1/endpoints/meeting_effectiveness.py
"""Meeting Effectiveness API — Post-meeting micro-survey."""

from datetime import date
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.meeting_effectiveness_service import meeting_effectiveness_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/meeting-effectiveness",
    tags=["Meeting Effectiveness"],
)


@router.post("/{organization_id}/rate")
async def rate_meeting(
    organization_id: str,
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Submit a post-meeting effectiveness rating (1-5)."""
    rating = await meeting_effectiveness_service.submit_rating(
        db,
        organization_id=UUID(organization_id),
        rater_id=current_user.id,
        effectiveness_score=payload["score"],
        meeting_date=date.fromisoformat(payload.get("meeting_date", str(date.today()))),
        team_id=UUID(payload["team_id"]) if payload.get("team_id") else None,
        meeting_subject=payload.get("subject"),
        organizer_id=(
            UUID(payload["organizer_id"]) if payload.get("organizer_id") else None
        ),
        tags=payload.get("tags"),
        comment=payload.get("comment"),
    )
    await db.commit()
    return {
        "id": str(rating.id),
        "score": rating.effectiveness_score,
        "meeting_date": rating.meeting_date.isoformat(),
    }


@router.get("/{organization_id}/summary")
async def org_summary(
    organization_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Org-wide meeting effectiveness: avg score, effectiveness rate, top issues."""
    return await meeting_effectiveness_service.get_org_summary(
        db, organization_id, lookback_days
    )


@router.get("/{organization_id}/team/{team_id}")
async def team_summary(
    organization_id: str,
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Team-level meeting effectiveness."""
    return await meeting_effectiveness_service.get_team_summary(
        db, team_id, lookback_days
    )
