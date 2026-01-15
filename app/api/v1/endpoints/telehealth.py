"""
Telehealth API Endpoints
Video consultation management with Twilio integration

HIPAA Compliant:
- All sessions logged
- Encrypted recordings
- Access controlled
- Audit trail maintained
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.telehealth.video_service import TelehealthVideoService

router = APIRouter(prefix="/telehealth", tags=["telehealth"])
logger = logging.getLogger(__name__)


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a telehealth session"""
    clinician_id: UUID
    scheduled_time: datetime
    session_type: str = "initial"  # initial, follow_up, crisis, group
    duration_minutes: int = 60
    recording_enabled: bool = False


class SessionNotesRequest(BaseModel):
    """Clinical notes for completed session"""
    session_notes: Optional[str] = None
    diagnosis_codes: Optional[list] = None
    treatment_plan: Optional[str] = None
    patient_satisfaction: Optional[int] = None


class CancelSessionRequest(BaseModel):
    """Request to cancel a session"""
    cancellation_reason: Optional[str] = None


# ============================================================================
# TELEHEALTH ENDPOINTS
# ============================================================================

@router.post("/schedule")
async def schedule_consultation(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Schedule a video consultation with a clinician

    Creates a Twilio Video room and generates access tokens for both participants.
    Requires explicit consent for recording if enabled.
    """
    try:
        video_service = TelehealthVideoService(db)

        # Check clinician availability
        is_available = await video_service.check_clinician_availability(
            clinician_id=request.clinician_id,
            requested_time=request.scheduled_time
        )

        if not is_available:
            raise HTTPException(
                400,
                "Clinician is not available at the requested time. Please choose a different time."
            )

        # Create consultation room
        session_data = await video_service.create_consultation_room(
            user_id=current_user.id,
            clinician_id=request.clinician_id,
            scheduled_time=request.scheduled_time,
            session_type=request.session_type,
            duration_minutes=request.duration_minutes,
            recording_enabled=request.recording_enabled
        )

        # Log session creation (audit trail)
        logger.info(
            f"Telehealth session {session_data['session_id']} scheduled "
            f"for user {current_user.id} at {request.scheduled_time}"
        )

        return {
            "success": True,
            "message": "Video consultation scheduled successfully",
            "data": session_data
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to schedule consultation: {e}")
        raise HTTPException(500, "Failed to schedule consultation") from e


@router.get("/join/{session_id}")
async def join_consultation(
    session_id: UUID,
    user_role: str = Query(..., description="Role: 'patient' or 'clinician'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join a scheduled video consultation

    Returns room details and access token for the specified user role.
    Tokens are time-limited and expire after 2 hours.
    """
    try:
        video_service = TelehealthVideoService(db)

        session_data = await video_service.join_session(
            session_id=session_id,
            user_id=current_user.id,
            user_role=user_role
        )

        logger.info(f"User {current_user.id} joined telehealth session {session_id}")

        return {
            "success": True,
            "message": "Successfully joined consultation",
            "data": session_data
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to join consultation: {e}")
        raise HTTPException(500, "Failed to join consultation") from e


@router.post("/start/{session_id}")
async def start_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a telehealth session (clinician only)

    Marks the session as in-progress and records the start time.
    Only the assigned clinician can start the session.
    """
    try:
        video_service = TelehealthVideoService(db)

        session_data = await video_service.start_session(
            session_id=session_id,
            user_id=current_user.id
        )

        logger.info(f"Clinician {current_user.id} started session {session_id}")

        return {
            "success": True,
            "message": "Session started successfully",
            "data": session_data
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        raise HTTPException(500, "Failed to start session") from e


@router.post("/end/{session_id}")
async def end_session(
    session_id: UUID,
    notes: SessionNotesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End a telehealth session and save clinical notes

    Completes the session and optionally saves clinical documentation.
    Can be called by either participant but typically by clinician.
    """
    try:
        video_service = TelehealthVideoService(db)

        session_data = await video_service.end_session(
            session_id=session_id,
            user_id=current_user.id,
            session_notes=notes.session_notes,
            diagnosis_codes=notes.diagnosis_codes,
            treatment_plan=notes.treatment_plan,
            patient_satisfaction=notes.patient_satisfaction
        )

        logger.info(
            f"Session {session_id} ended by user {current_user.id}. "
            f"Duration: {session_data.get('actual_duration_minutes')} minutes"
        )

        return {
            "success": True,
            "message": "Session ended successfully",
            "data": session_data
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        raise HTTPException(500, "Failed to end session") from e


@router.post("/cancel/{session_id}")
async def cancel_session(
    session_id: UUID,
    request: CancelSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a scheduled telehealth session

    Cancels an upcoming session. Cannot cancel completed or in-progress sessions.
    Both patient and clinician can cancel.
    """
    try:
        video_service = TelehealthVideoService(db)

        session_data = await video_service.cancel_session(
            session_id=session_id,
            user_id=current_user.id,
            cancellation_reason=request.cancellation_reason
        )

        logger.info(
            f"Session {session_id} cancelled by user {current_user.id}. "
            f"Reason: {request.cancellation_reason or 'Not provided'}"
        )

        return {
            "success": True,
            "message": "Session cancelled successfully",
            "data": session_data
        }

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to cancel session: {e}")
        raise HTTPException(500, "Failed to cancel session") from e


@router.get("/upcoming")
async def get_upcoming_sessions(
    role: str = Query("patient", description="Filter by role: 'patient' or 'clinician'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get upcoming telehealth sessions

    Returns all scheduled future sessions for the current user.
    Can filter by role if user is both a patient and a clinician.
    """
    try:
        video_service = TelehealthVideoService(db)

        sessions = await video_service.get_upcoming_sessions(
            user_id=current_user.id,
            role=role
        )

        return {
            "success": True,
            "count": len(sessions),
            "data": sessions
        }

    except Exception as e:
        logger.error(f"Failed to get upcoming sessions: {e}")
        raise HTTPException(500, "Failed to retrieve upcoming sessions") from e


@router.get("/availability")
async def check_availability(
    clinician_id: UUID,
    requested_time: datetime,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a clinician is available at a specific time

    Returns True if the clinician has no conflicts within 1 hour of the requested time.
    Useful for scheduling UI to show available slots.
    """
    try:
        video_service = TelehealthVideoService(db)

        is_available = await video_service.check_clinician_availability(
            clinician_id=clinician_id,
            requested_time=requested_time
        )

        return {
            "success": True,
            "available": is_available,
            "clinician_id": str(clinician_id),
            "requested_time": requested_time.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        raise HTTPException(500, "Failed to check availability") from e
