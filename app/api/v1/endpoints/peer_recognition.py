"""
Peer Recognition API

Endpoints for giving and viewing peer-to-peer recognitions.
Recognition data feeds into the BI engine's engagement scoring
and the Digital Twin's engagement dimension.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.peer_recognition import PeerRecognition, RecognitionType
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/recognition", tags=["Peer Recognition"])


class GiveRecognitionRequest(BaseModel):
    recipient_id: UUID
    recognition_type: str = Field(
        ...,
        pattern="^(thank_you|great_work|innovation|teamwork|leadership|mentorship|above_and_beyond)$",
    )
    message: Optional[str] = Field(None, max_length=500)
    team_id: Optional[UUID] = None
    is_public: bool = True


@router.post("")
async def give_recognition(
    req: GiveRecognitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Give a peer recognition."""
    if str(req.recipient_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot recognize yourself")

    recognition = PeerRecognition(
        organization_id=current_user.organization_id,
        team_id=req.team_id,
        recognizer_id=current_user.id,
        recipient_id=req.recipient_id,
        recognition_type=RecognitionType(req.recognition_type),
        message=req.message,
        is_public=req.is_public,
    )
    db.add(recognition)
    await db.commit()
    await db.refresh(recognition)

    return {
        "id": str(recognition.id),
        "recognition_type": recognition.recognition_type.value,
        "created_at": recognition.created_at.isoformat(),
    }


@router.get("/received")
async def get_received_recognitions(
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get recognitions received by the current user."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(PeerRecognition)
        .where(
            PeerRecognition.recipient_id == current_user.id,
            PeerRecognition.created_at >= since,
        )
        .order_by(PeerRecognition.created_at.desc())
        .limit(100)
    )
    recs = result.scalars().all()
    return {
        "count": len(recs),
        "recognitions": [
            {
                "id": str(r.id),
                "type": r.recognition_type.value,
                "message": r.message if r.is_public else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ],
    }


@router.get("/team/{team_id}/feed")
async def get_team_recognition_feed(
    team_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Public recognition feed for a team."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(PeerRecognition)
        .where(
            PeerRecognition.team_id == team_id,
            PeerRecognition.is_public.is_(True),
            PeerRecognition.created_at >= since,
        )
        .order_by(PeerRecognition.created_at.desc())
        .limit(50)
    )
    recs = result.scalars().all()
    return {
        "team_id": str(team_id),
        "count": len(recs),
        "feed": [
            {
                "id": str(r.id),
                "type": r.recognition_type.value,
                "message": r.message,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ],
    }


@router.get("/stats/{organization_id}")
async def get_recognition_stats(
    organization_id: UUID,
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Organization-wide recognition metrics for dashboards."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(),
            func.count(func.distinct(PeerRecognition.recognizer_id)),
            func.count(func.distinct(PeerRecognition.recipient_id)),
        ).where(
            PeerRecognition.organization_id == organization_id,
            PeerRecognition.created_at >= since,
        )
    )
    row = result.one()

    # Type breakdown
    type_result = await db.execute(
        select(PeerRecognition.recognition_type, func.count())
        .where(
            PeerRecognition.organization_id == organization_id,
            PeerRecognition.created_at >= since,
        )
        .group_by(PeerRecognition.recognition_type)
    )
    type_breakdown = {r[0].value: r[1] for r in type_result.all()}

    return {
        "total_recognitions": row[0] or 0,
        "unique_givers": row[1] or 0,
        "unique_receivers": row[2] or 0,
        "type_breakdown": type_breakdown,
        "period_days": days,
    }
