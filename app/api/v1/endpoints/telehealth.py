"""
Telehealth API Endpoints

Queries TelehealthSession table for real session data.
Supports scheduling, joining, and managing telehealth sessions.

HIPAA: All endpoints handle PHI (session notes, consultation reasons).
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.hipaa import audit_phi_access, require_clinical_access
from app.core.database import get_db
from app.db.models.user import User


async def _audit_telehealth(
    request: Request,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Audit all telehealth PHI access."""
    action = "write" if request.method in ("POST", "PUT", "PATCH", "DELETE") else "read"
    await audit_phi_access(
        db,
        current_user,
        "telehealth_sessions",
        action,
        details={"endpoint": request.url.path},
        request=request,
    )


router = APIRouter(
    prefix="/telehealth",
    tags=["telehealth"],
    dependencies=[Depends(_audit_telehealth)],
)


def _get_session_model():
    from app.db.models.clinical_extended import TelehealthSession

    return TelehealthSession


def _serialize_session(s) -> dict[str, Any]:
    return {
        "id": str(s.id),
        "user_id": str(s.user_id),
        "clinician_id": str(s.clinician_id) if s.clinician_id else None,
        "session_type": s.session_type,
        "consultation_reason": s.consultation_reason,
        "scheduled_time": s.scheduled_time.isoformat() if s.scheduled_time else None,
        "duration_minutes": s.duration_minutes,
        "status": s.status,
        "room_name": s.room_name,
        "connection_quality": s.connection_quality,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("/upcoming")
async def get_upcoming_sessions(
    role: Optional[str] = Query(default="patient"),
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get upcoming scheduled telehealth sessions."""
    TelehealthSession = _get_session_model()
    now = datetime.utcnow()

    if role == "clinician":
        filter_cond = and_(
            TelehealthSession.clinician_id == current_user.id,
            TelehealthSession.scheduled_time >= now,
            TelehealthSession.status == "scheduled",
        )
    else:
        filter_cond = and_(
            TelehealthSession.user_id == current_user.id,
            TelehealthSession.scheduled_time >= now,
            TelehealthSession.status == "scheduled",
        )

    result = await db.execute(
        select(TelehealthSession)
        .where(filter_cond)
        .order_by(TelehealthSession.scheduled_time.asc())
        .limit(20)
    )
    sessions = [_serialize_session(s) for s in result.scalars().all()]

    return {"data": sessions, "count": len(sessions)}


@router.get("/sessions/active")
async def get_active_sessions(
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get currently active sessions for the user."""
    TelehealthSession = _get_session_model()

    result = await db.execute(
        select(TelehealthSession)
        .where(
            and_(
                or_(
                    TelehealthSession.user_id == current_user.id,
                    TelehealthSession.clinician_id == current_user.id,
                ),
                TelehealthSession.status == "in_progress",
            )
        )
        .order_by(TelehealthSession.started_at.desc())
    )
    sessions = [_serialize_session(s) for s in result.scalars().all()]

    return {"data": sessions, "count": len(sessions)}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific session by ID."""
    TelehealthSession = _get_session_model()
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return {"session_id": session_id, "status": "not_found"}

    result = await db.execute(
        select(TelehealthSession).where(TelehealthSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"session_id": session_id, "status": "not_found"}

    data = _serialize_session(session)
    data["session_notes"] = session.session_notes
    data["started_at"] = session.started_at.isoformat() if session.started_at else None
    data["ended_at"] = session.ended_at.isoformat() if session.ended_at else None
    data["actual_duration_minutes"] = session.actual_duration_minutes
    return data


class ScheduleRequest(BaseModel):
    session_type: str = "routine"
    consultation_reason: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration_minutes: int = 50
    clinician_id: Optional[str] = None


@router.post("/schedule")
async def schedule_session(
    body: Optional[ScheduleRequest] = None,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Schedule a new telehealth session."""
    TelehealthSession = _get_session_model()

    scheduled_time = datetime.utcnow() + timedelta(days=1)
    if body and body.scheduled_time:
        try:
            scheduled_time = datetime.fromisoformat(body.scheduled_time)
        except ValueError:
            pass

    room_name = f"psychsync-{uuid.uuid4().hex[:12]}"

    session = TelehealthSession(
        user_id=current_user.id,
        clinician_id=(
            uuid.UUID(body.clinician_id) if body and body.clinician_id else None
        ),
        session_type=body.session_type if body else "routine",
        consultation_reason=body.consultation_reason if body else None,
        scheduled_time=scheduled_time,
        duration_minutes=body.duration_minutes if body else 50,
        room_name=room_name,
        status="scheduled",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return {
        "id": str(session.id),
        "status": "scheduled",
        "room_name": room_name,
        "scheduled_time": scheduled_time.isoformat(),
        "created_at": (
            session.created_at.isoformat()
            if session.created_at
            else datetime.utcnow().isoformat()
        ),
    }


@router.post("/join")
async def join_session(
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Join the next upcoming session."""
    TelehealthSession = _get_session_model()
    now = datetime.utcnow()

    # Find nearest scheduled session
    result = await db.execute(
        select(TelehealthSession)
        .where(
            and_(
                or_(
                    TelehealthSession.user_id == current_user.id,
                    TelehealthSession.clinician_id == current_user.id,
                ),
                TelehealthSession.status.in_(["scheduled", "in_progress"]),
            )
        )
        .order_by(TelehealthSession.scheduled_time.asc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session:
        return {"token": "", "room_name": "", "status": "no_session_available"}

    # Mark as in progress
    if session.status == "scheduled":
        session.status = "in_progress"
        session.started_at = now
        if session.user_id == current_user.id:
            session.user_joined_at = now
        else:
            session.clinician_joined_at = now
        await db.commit()

    return {
        "token": session.user_token or "",
        "room_name": session.room_name or "",
        "session_id": str(session.id),
        "status": "joined",
    }


@router.post("/end/{session_id}")
async def end_session(
    session_id: str,
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """End a telehealth session."""
    TelehealthSession = _get_session_model()
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    result = await db.execute(
        select(TelehealthSession).where(TelehealthSession.id == sid)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.utcnow()
    session.status = "completed"
    session.ended_at = now
    if session.started_at:
        session.actual_duration_minutes = int(
            (now - session.started_at).total_seconds() / 60
        )
    await db.commit()

    return {"session_id": session_id, "status": "ended", "ended_at": now.isoformat()}


@router.post("/cancel")
async def cancel_session(
    current_user: User = Depends(require_clinical_access),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cancel the next upcoming scheduled session."""
    TelehealthSession = _get_session_model()

    result = await db.execute(
        select(TelehealthSession)
        .where(
            and_(
                TelehealthSession.user_id == current_user.id,
                TelehealthSession.status == "scheduled",
            )
        )
        .order_by(TelehealthSession.scheduled_time.asc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if not session:
        return {"status": "no_session_to_cancel"}

    session.status = "cancelled"
    session.cancelled_by = "patient"
    session.cancelled_at = datetime.utcnow()
    await db.commit()

    return {"status": "cancelled", "session_id": str(session.id)}
