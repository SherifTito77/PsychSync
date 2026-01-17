"""
Telehealth API Endpoints

REST endpoints for video consultation sessions:
- Schedule telehealth sessions
- Generate video room tokens
- Manage session lifecycle
- Webhook handlers for Twilio events
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from app.api.v1.dependencies.auth import get_current_active_user
from app.core.config import settings
from app.db.session import get_async_db
from app.db.models.user import User
from app.db.models.clinical_extended import TelehealthSession
from app.services.telehealth.video_service import get_telehealth_service
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telehealth", tags=["telehealth"])


# =====================================================================
# Pydantic Schemas
# =====================================================================

class ScheduleSessionRequest(BaseModel):
    """Request to schedule telehealth session"""
    session_type: str = Field(..., description="Type: initial, follow_up, crisis, routine")
    consultation_reason: str = Field(..., description="Reason for consultation")
    scheduled_time: datetime = Field(..., description="When session should occur")
    duration_minutes: int = Field(50, description="Session duration in minutes")
    related_assessment_id: Optional[str] = Field(None, description="Related assessment if applicable")
    timezone: str = Field("UTC", description="User's timezone")


class SessionResponse(BaseModel):
    """Telehealth session response"""
    session_id: str
    session_type: str
    scheduled_time: datetime
    duration_minutes: int
    status: str
    room_name: Optional[str] = None
    access_token: Optional[str] = None
    consultation_link: Optional[str] = None


class JoinSessionRequest(BaseModel):
    """Request to join session"""
    session_id: str


class ClinicianJoinRequest(BaseModel):
    """Request for clinician to join session"""
    session_id: str


class CancelSessionRequest(BaseModel):
    """Request to cancel session"""
    session_id: str
    reason: str = Field(..., description="Reason for cancellation")


# =====================================================================
# Session Scheduling Endpoints
# =====================================================================

@router.post("/schedule", response_model=SessionResponse)
async def schedule_telehealth_session(
    request: ScheduleSessionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Schedule a new telehealth video consultation session

    Creates:
    1. Telehealth session record in database
    2. Twilio Video room
    3. Access token for patient
    4. Calendar invitation (sent in background)

    Session types:
    - initial: First consultation
    - follow_up: Subsequent appointment
    - crisis: Urgent crisis intervention
    - routine: Regular check-in
    """

    try:
        # Validate scheduled_time is in the future
        if request.scheduled_time < datetime.utcnow() + timedelta(minutes=15):
            raise HTTPException(
                status_code=400,
                detail="Sessions must be scheduled at least 15 minutes in advance"
            )

        # Assign clinician (in production, this would use availability matching)
        # For now, assign first available clinician
        clinician_query = select(User).where(
            and_(
                User.role == 'clinician',
                User.is_active == True
            )
        ).limit(1)

        clinician_result = await db.execute(clinician_query)
        clinician = clinician_result.scalar_one_or_none()

        if not clinician:
            raise HTTPException(
                status_code=503,
                detail="No clinicians available at this time"
            )

        # Create session record
        session = TelehealthSession(
            user_id=current_user.id,
            clinician_id=clinician.id,
            session_type=request.session_type,
            consultation_reason=request.consultation_reason,
            related_assessment_id=request.related_assessment_id,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes,
            timezone=request.timezone,
            status='scheduled'
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Create Twilio Video room
        telehealth_service = get_telehealth_service()
        room_result = await telehealth_service.create_video_room(
            session_id=str(session.id),
            user_name=current_user.full_name or current_user.email,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes
        )

        if room_result.get('error'):
            # Rollback session creation if video room fails
            await db.delete(session)
            await db.commit()

            raise HTTPException(
                status_code=503,
                detail=f"Failed to create video room: {room_result['error']}"
            )

        # Update session with room details
        session.room_sid = room_result['room_sid']
        session.room_name = room_result['room_name']
        session.user_token = room_result['user_token']
        await db.commit()

        # Send calendar invitation in background
        background_tasks.add_task(
            telehealth_service.send_calendar_invite,
            session_id=str(session.id),
            participant_email=current_user.email,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes
        )

        logger.info(f"Scheduled telehealth session {session.id} for user {current_user.id}")

        return SessionResponse(
            session_id=str(session.id),
            session_type=session.session_type,
            scheduled_time=session.scheduled_time,
            duration_minutes=session.duration_minutes,
            status=session.status,
            room_name=session.room_name,
            access_token=room_result['user_token'],
            consultation_link=f"{settings.API_BASE_URL}/telehealth/join/{session.id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule session")


@router.get("/sessions/active")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all active/scheduled sessions for current user

    Returns sessions that are:
    - Scheduled for future
    - Currently in progress
    - Within 1 hour of now
    """

    try:
        telehealth_service = get_telehealth_service()

        # Determine if user is patient or clinician
        role = 'clinician' if current_user.role == 'clinician' else 'patient'

        sessions = await telehealth_service.get_active_sessions_for_user(
            user_id=str(current_user.id),
            role=role
        )

        return {
            "active_sessions": sessions,
            "count": len(sessions)
        }

    except Exception as e:
        logger.error(f"Failed to get active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get details of a specific telehealth session"""

    try:
        query = select(TelehealthSession).where(
            TelehealthSession.id == session_id
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if current_user.role != 'admin' and str(session.user_id) != str(current_user.id) and str(session.clinician_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to view this session")

        return {
            "id": str(session.id),
            "session_type": session.session_type,
            "consultation_reason": session.consultation_reason,
            "scheduled_time": session.scheduled_time.isoformat(),
            "duration_minutes": session.duration_minutes,
            "status": session.status,
            "room_name": session.room_name,
            "timezone": session.timezone,
            "created_at": session.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


# =====================================================================
# Video Room Endpoints
# =====================================================================

@router.post("/join")
async def join_video_session(
    request: JoinSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Join a telehealth video session (patient)

    Returns:
    - Room access token
    - Room name
    - Connection instructions
    """

    try:
        # Get session
        query = select(TelehealthSession).where(
            and_(
                TelehealthSession.id == request.session_id,
                TelehealthSession.user_id == current_user.id
            )
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if session is scheduled/in-progress
        if session.status not in ['scheduled', 'in_progress']:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot join session with status: {session.status}"
            )

        # Check if session time has arrived (allow 5 min early)
        if session.scheduled_time > datetime.utcnow() + timedelta(minutes=5):
            raise HTTPException(
                status_code=400,
                detail=f"Session is scheduled for {session.scheduled_time.strftime('%Y-%m-%d %H:%M')} UTC"
            )

        # Generate fresh access token
        telehealth_service = get_telehealth_service()

        # Generate token for patient
        user_token = telehealth_service._generate_access_token(
            room_name=session.room_name,
            participant_identity=f"patient-{session.id}",
            ttl=session.duration_minutes * 60 + 300
        )

        # Update session status
        if session.status == 'scheduled':
            session.status = 'in_progress'
            await db.commit()

        logger.info(f"User {current_user.id} joined session {session.id}")

        return {
            "room_name": session.room_name,
            "access_token": user_token,
            "session_id": str(session.id),
            "session_type": session.session_type,
            "duration_minutes": session.duration_minutes,
            "status": session.status,
            "connection_info": {
                "domain": "psychsync.video",  # Would configure in production
                "region": "us1",  # Twilio region
                "turn_enabled": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join session")


@router.post("/clinician/join")
async def clinician_join_session(
    request: ClinicianJoinRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Join a telehealth video session (clinician)

    Returns clinician-specific access token with extended privileges
    """

    # Verify clinician role
    if current_user.role != 'clinician' and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Only clinicians can join via this endpoint")

    try:
        # Get session
        query = select(TelehealthSession).where(
            TelehealthSession.id == request.session_id
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify this clinician is assigned
        if str(session.clinician_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not assigned to this session")

        # Generate clinician token
        telehealth_service = get_telehealth_service()

        clinician_token = telehealth_service.generate_clinician_token(
            room_name=session.room_name,
            session_id=str(session.id),
            ttl=3600  # 1 hour
        )

        logger.info(f"Clinician {current_user.id} joined session {session.id}")

        return {
            "room_name": session.room_name,
            "access_token": clinician_token,
            "session_id": str(session.id),
            "patient_name": "Confidential",  # Would fetch from user table
            "session_type": session.session_type,
            "consultation_reason": session.consultation_reason,
            "related_assessment_id": session.related_assessment_id,
            "recording_enabled": session.recording_enabled
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clinician failed to join session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join session")


@router.post("/end/{session_id}")
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    End an active telehealth session

    Can be called by either patient or clinician
    """

    try:
        # Get session
        query = select(TelehealthSession).where(
            TelehealthSession.id == session_id
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if (str(session.user_id) != str(current_user.id) and
            str(session.clinician_id) != str(current_user.id) and
            current_user.role != 'admin'):
            raise HTTPException(status_code=403, detail="Not authorized to end this session")

        # End the video room
        telehealth_service = get_telehealth_service()
        end_result = await telehealth_service.complete_room(
            room_sid=session.room_sid,
            session_id=session_id
        )

        if end_result.get('error'):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to end session: {end_result['error']}"
            )

        logger.info(f"Session {session_id} ended by user {current_user.id}")

        return {
            "status": "ended",
            "session_id": session_id,
            "ended_at": end_result.get('ended_at'),
            "duration_minutes": end_result.get('duration_minutes')
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.post("/cancel")
async def cancel_session(
    request: CancelSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Cancel a scheduled telehealth session

    Can only cancel sessions that haven't started yet
    """

    try:
        # Get session
        query = select(TelehealthSession).where(
            TelehealthSession.id == request.session_id
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if (str(session.user_id) != str(current_user.id) and
            str(session.clinician_id) != str(current_user.id) and
            current_user.role != 'admin'):
            raise HTTPException(status_code=403, detail="Not authorized to cancel this session")

        # Can only cancel scheduled sessions
        if session.status != 'scheduled':
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel session with status: {session.status}"
            )

        # Cancel the room
        telehealth_service = get_telehealth_service()
        cancel_result = await telehealth_service.cancel_room(
            room_sid=session.room_sid,
            session_id=request.session_id,
            cancellation_reason=request.reason
        )

        if cancel_result.get('error'):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel session: {cancel_result['error']}"
            )

        logger.info(f"Session {request.session_id} cancelled by user {current_user.id}")

        return {
            "status": "cancelled",
            "session_id": request.session_id,
            "cancelled_at": cancel_result.get('cancelled_at'),
            "reason": request.reason
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel session")


# =====================================================================
# Webhook Endpoints
# =====================================================================

@router.post("/webhooks/room")
async def twilio_room_webhook(
    webhook_data: Dict,
    background_tasks: BackgroundTasks
):
    """
    Handle Twilio Video room webhooks

    Events:
    - room-created: Room successfully created
    - room-participant-connected: Participant joined
    - room-participant-disconnected: Participant left
    - room-ended: Room completed
    - room-recording-callback: Recording available

    Returns 200 OK to acknowledge receipt
    """

    try:
        # Process webhook in background
        telehealth_service = get_telehealth_service()

        background_tasks.add_task(
            telehealth_service.handle_room_webhook,
            webhook_data=webhook_data
        )

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Failed to process webhook: {str(e)}")
        # Still return 200 to avoid Twilio retries
        return {"status": "error", "message": str(e)}


# =====================================================================
# Admin Endpoints
# =====================================================================

@router.post("/admin/cleanup")
async def cleanup_expired_sessions(
    hours_old: int = Query(26, description="Delete sessions older than this many hours"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clean up expired video sessions (admin only)

    Should be run periodically via cron job
    """

    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        telehealth_service = get_telehealth_service()

        cleanup_result = await telehealth_service.cleanup_expired_rooms(
            hours_old=hours_old
        )

        return cleanup_result

    except Exception as e:
        logger.error(f"Failed to cleanup sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")
