"""
Telehealth API Endpoints

REST endpoints for video consultation sessions:
- Schedule telehealth sessions
- Generate video room tokens
- Manage session lifecycle
- Webhook handlers for Twilio events
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.db.models.clinical_extended import TelehealthSession
from app.db.models.user import User
from app.db.session import get_db
from app.services.telehealth.video_service import get_telehealth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telehealth", tags=["telehealth"])


# =====================================================================
# Pydantic Schemas
# =====================================================================


class ScheduleSessionRequest(BaseModel):
    """Request to schedule telehealth session"""

    session_type: str = Field(
        ..., description="Type: initial, follow_up, crisis, group"
    )
    consultation_reason: Optional[str] = Field(
        None, description="Reason for consultation (optional)"
    )
    scheduled_time: datetime = Field(..., description="When session should occur")
    duration_minutes: int = Field(60, description="Session duration in minutes")
    related_assessment_id: Optional[str] = Field(
        None, description="Related assessment if applicable"
    )
    timezone: str = Field("UTC", description="User's timezone")
    clinician_id: Optional[str] = Field(
        None,
        description="Specific clinician ID (optional, auto-assigned if not provided)",
    )
    recording_enabled: bool = Field(False, description="Whether to record the session")


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


class CancelSessionByPathRequest(BaseModel):
    """Request body for cancel endpoint with session_id in path"""

    cancellation_reason: str = Field(..., description="Reason for cancellation")


# =====================================================================
# Session Scheduling Endpoints
# =====================================================================


@router.post("/schedule", response_model=SessionResponse)
async def schedule_telehealth_session(
    request: ScheduleSessionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule a new telehealth video consultation session

    Creates:
    1. Telehealth session record in database
    2. Video room (if video service available)
    3. Access token for patient
    4. Calendar invitation (sent in background)

    Session types:
    - initial: First consultation
    - follow_up: Subsequent appointment
    - crisis: Urgent crisis intervention
    - group: Group therapy session
    """

    try:
        # Validate scheduled_time is in the future
        # request.scheduled_time is aware (from Pydantic ISO string), so we MUST use aware comparison
        if request.scheduled_time < datetime.now(timezone.utc) + timedelta(minutes=15):
            raise HTTPException(
                status_code=400,
                detail="Sessions must be scheduled at least 15 minutes in advance",
            )

        # Assign clinician
        clinician = None
        if request.clinician_id:
            # Use specified clinician
            clinician_query = select(User).where(
                and_(User.id == request.clinician_id, User.is_active == True)
            )
            clinician_result = await db.execute(clinician_query)
            clinician = clinician_result.scalar_one_or_none()

        if not clinician:
            # Auto-assign first available clinician (Fallback for demo/unspecified)
            clinician_query = (
                select(User)
                .where(and_(User.role == "clinician", User.is_active == True))
                .limit(1)
            )

            clinician_result = await db.execute(clinician_query)
            clinician = clinician_result.scalar_one_or_none()

            if not clinician:
                raise HTTPException(
                    status_code=503, detail="No clinicians available at this time"
                )

        # Create session record
        session = TelehealthSession(
            user_id=current_user.id,
            clinician_id=clinician.id,
            session_type=request.session_type,
            consultation_reason=request.consultation_reason
            or f"{request.session_type.replace('_', ' ').title()} Consultation",
            related_assessment_id=request.related_assessment_id,
            scheduled_time=request.scheduled_time,
            duration_minutes=request.duration_minutes,
            timezone=request.timezone,
            status="scheduled",
        )

        # Set recording_enabled if the field exists in the model
        if hasattr(session, "recording_enabled"):
            session.recording_enabled = request.recording_enabled

        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Try to create video room (may fail if service not configured)
        try:
            telehealth_service = get_telehealth_service()
            room_result = await telehealth_service.create_video_room(
                session_id=str(session.id),
                user_name=current_user.full_name or current_user.email,
                scheduled_time=request.scheduled_time,
                duration_minutes=request.duration_minutes,
            )

            if room_result.get("error"):
                # Log warning but don't fail - session can still be created
                logger.warning(f"Video room creation failed: {room_result['error']}")
                room_result = None
            else:
                # Update session with room details
                session.room_sid = room_result["room_sid"]
                session.room_name = room_result["room_name"]
                session.user_token = room_result["user_token"]
                await db.commit()

                # Send calendar invitation in background
                background_tasks.add_task(
                    telehealth_service.send_calendar_invite,
                    session_id=str(session.id),
                    participant_email=current_user.email,
                    scheduled_time=request.scheduled_time,
                    duration_minutes=request.duration_minutes,
                )
        except Exception as e:
            # Video service not available, but session is still valid
            logger.warning(f"Video service unavailable: {str(e)}")
            room_result = None

        logger.info(
            f"Scheduled telehealth session {session.id} for user {current_user.id}"
        )

        return SessionResponse(
            session_id=str(session.id),
            session_type=session.session_type,
            scheduled_time=session.scheduled_time,
            duration_minutes=session.duration_minutes,
            status=session.status,
            room_name=getattr(session, "room_name", None),
            access_token=room_result["user_token"] if room_result else None,
            consultation_link=(
                f"{settings.API_BASE_URL}/telehealth/join/{session.id}"
                if hasattr(settings, "API_BASE_URL")
                else None
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to schedule session")


@router.get("/sessions/active")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
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
        role = "clinician" if current_user.role == "clinician" else "patient"

        sessions = await telehealth_service.get_active_sessions_for_user(
            user_id=str(current_user.id), role=role
        )

        return {"active_sessions": sessions, "count": len(sessions)}

    except Exception as e:
        logger.error(f"Failed to get active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/upcoming")
async def get_upcoming_sessions(
    role: str = Query("patient", description="Role: patient or clinician"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get upcoming sessions for the current user

    Matches frontend expectation: GET /telehealth/upcoming?role=patient
    Returns all future scheduled sessions for the user
    """

    try:
        # Import timezone-aware datetime
        from datetime import timezone

        # Query upcoming sessions from database
        user_field = (
            TelehealthSession.clinician_id
            if role == "clinician" or current_user.role == "clinician"
            else TelehealthSession.user_id
        )

        # Use timezone-aware datetime for comparison
        now = datetime.now(timezone.utc)

        query = (
            select(TelehealthSession)
            .where(
                and_(
                    user_field == current_user.id,
                    TelehealthSession.status.in_(["scheduled", "in_progress"]),
                    TelehealthSession.scheduled_time
                    >= now,  # Only future or current sessions
                )
            )
            .order_by(TelehealthSession.scheduled_time.asc())
        )

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Format response to match frontend expectations
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append(
                {
                    "id": str(session.id),
                    "session_type": session.session_type,
                    "scheduled_time": session.scheduled_time.isoformat(),
                    "duration_minutes": session.duration_minutes,
                    "status": session.status,
                    "recording_enabled": getattr(session, "recording_enabled", False),
                    "clinician_id": (
                        str(session.clinician_id) if session.clinician_id else None
                    ),
                    "user_id": str(session.user_id),
                }
            )

        logger.info(
            f"Retrieved {len(formatted_sessions)} upcoming sessions for user {current_user.id} (role: {role})"
        )

        return {"data": formatted_sessions, "count": len(formatted_sessions)}

    except Exception as e:
        logger.error(f"Failed to get upcoming sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve upcoming sessions"
        )


@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific telehealth session"""

    try:
        query = select(TelehealthSession).where(TelehealthSession.id == session_id)

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if (
            current_user.role != "admin"
            and str(session.user_id) != str(current_user.id)
            and str(session.clinician_id) != str(current_user.id)
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to view this session"
            )

        return {
            "id": str(session.id),
            "session_type": session.session_type,
            "consultation_reason": session.consultation_reason,
            "scheduled_time": session.scheduled_time.isoformat(),
            "duration_minutes": session.duration_minutes,
            "status": session.status,
            "room_name": session.room_name,
            "timezone": session.timezone,
            "created_at": session.created_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")


# =====================================================================
# Video Room Endpoints
# =====================================================================


@router.get("/join/{session_id}")
async def join_session_get(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Join a telehealth video session (GET version for frontend compatibility)
    """
    try:
        # Get session
        query = select(TelehealthSession).where(
            and_(
                TelehealthSession.id == session_id,
                TelehealthSession.user_id == current_user.id,
            )
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            # Check if user is clinician for this session
            query = select(TelehealthSession).where(
                and_(
                    TelehealthSession.id == session_id,
                    TelehealthSession.clinician_id == current_user.id,
                )
            )
            result = await db.execute(query)
            session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=404, detail="Session not found or not authorized"
            )

        # Update session status
        if session.status == "scheduled":
            session.status = "in_progress"
            await db.commit()

        telehealth_service = get_telehealth_service()

        # Jitsi doesn't need tokens, but we return the room info
        room_info = await telehealth_service.create_video_room(
            session_id=str(session.id),
            user_name=current_user.full_name or current_user.email,
            scheduled_time=session.scheduled_time,
        )

        return {
            "access_token": "jitsi-free-tier",
            "room_name": room_info["room_name"],
            "domain": "meet.jit.si",
            "session_type": session.session_type,
            "recording_enabled": session.recording_enabled,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join session")


@router.post("/join")
async def join_video_session(
    request: JoinSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
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
                TelehealthSession.user_id == current_user.id,
            )
        )

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if session is scheduled/in-progress
        if session.status not in ["scheduled", "in_progress"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot join session with status: {session.status}",
            )

        # Check if session time has arrived (allow 5 min early)
        if session.scheduled_time > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise HTTPException(
                status_code=400,
                detail=f"Session is scheduled for {session.scheduled_time.strftime('%Y-%m-%d %H:%M')} UTC",
            )

        # Generate fresh access token
        telehealth_service = get_telehealth_service()

        # Generate token for patient
        user_token = telehealth_service._generate_access_token(
            room_name=session.room_name,
            participant_identity=f"patient-{session.id}",
            ttl=session.duration_minutes * 60 + 300,
        )

        # Update session status
        if session.status == "scheduled":
            session.status = "in_progress"
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
                "turn_enabled": True,
            },
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
    db: AsyncSession = Depends(get_db),
):
    """
    Join a telehealth video session (clinician)

    Returns clinician-specific access token with extended privileges
    """

    # Verify clinician role
    if current_user.role != "clinician" and current_user.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only clinicians can join via this endpoint"
        )

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
            room_name=session.room_name, session_id=str(session.id), ttl=3600  # 1 hour
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
            "recording_enabled": session.recording_enabled,
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
    db: AsyncSession = Depends(get_db),
):
    """
    End an active telehealth session

    Can be called by either patient or clinician
    """

    try:
        # Get session
        query = select(TelehealthSession).where(TelehealthSession.id == session_id)

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if (
            str(session.user_id) != str(current_user.id)
            and str(session.clinician_id) != str(current_user.id)
            and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to end this session"
            )

        # End the video room
        telehealth_service = get_telehealth_service()
        end_result = await telehealth_service.complete_room(
            room_sid=session.room_sid, session_id=session_id
        )

        if end_result.get("error"):
            raise HTTPException(
                status_code=500, detail=f"Failed to end session: {end_result['error']}"
            )

        logger.info(f"Session {session_id} ended by user {current_user.id}")

        return {
            "status": "ended",
            "session_id": session_id,
            "ended_at": end_result.get("ended_at"),
            "duration_minutes": end_result.get("duration_minutes"),
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
    db: AsyncSession = Depends(get_db),
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
        if (
            str(session.user_id) != str(current_user.id)
            and str(session.clinician_id) != str(current_user.id)
            and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to cancel this session"
            )

        # Can only cancel scheduled sessions
        if session.status != "scheduled":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel session with status: {session.status}",
            )

        # Cancel the room
        telehealth_service = get_telehealth_service()
        cancel_result = await telehealth_service.cancel_room(
            room_sid=session.room_sid,
            session_id=request.session_id,
            cancellation_reason=request.reason,
        )

        if cancel_result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel session: {cancel_result['error']}",
            )

        logger.info(f"Session {request.session_id} cancelled by user {current_user.id}")

        return {
            "status": "cancelled",
            "session_id": request.session_id,
            "cancelled_at": cancel_result.get("cancelled_at"),
            "reason": request.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cancel session")


@router.post("/cancel/{session_id}")
async def cancel_session_by_id(
    session_id: str,
    request: CancelSessionByPathRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a scheduled telehealth session by ID in URL path

    Matches frontend expectation: POST /telehealth/cancel/{sessionId}
    with JSON body containing cancellation_reason
    """

    try:
        # Get session
        query = select(TelehealthSession).where(TelehealthSession.id == session_id)

        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check authorization
        if (
            str(session.user_id) != str(current_user.id)
            and str(session.clinician_id) != str(current_user.id)
            and current_user.role != "admin"
        ):
            raise HTTPException(
                status_code=403, detail="Not authorized to cancel this session"
            )

        # Can only cancel scheduled sessions
        if session.status != "scheduled":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel session with status: {session.status}",
            )

        # Update session status to cancelled
        session.status = "cancelled"
        session.cancellation_reason = request.cancellation_reason
        session.cancelled_at = datetime.now(timezone.utc)

        await db.commit()

        # Try to cancel the video room (non-critical if it fails)
        try:
            telehealth_service = get_telehealth_service()
            cancel_result = await telehealth_service.cancel_room(
                room_sid=session.room_sid,
                session_id=session_id,
                cancellation_reason=request.cancellation_reason,
            )
            logger.info(f"Video room cancelled for session {session_id}")
        except Exception as e:
            logger.warning(
                f"Failed to cancel video room for session {session_id}: {str(e)}"
            )
            # Don't fail the request if room cancellation fails

        logger.info(f"Session {session_id} cancelled by user {current_user.id}")

        return {
            "status": "cancelled",
            "session_id": session_id,
            "cancelled_at": session.cancelled_at.isoformat(),
            "reason": request.cancellation_reason,
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
async def twilio_room_webhook(webhook_data: Dict, background_tasks: BackgroundTasks):
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
            telehealth_service.handle_room_webhook, webhook_data=webhook_data
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
    hours_old: int = Query(
        26, description="Delete sessions older than this many hours"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """
    Clean up expired video sessions (admin only)

    Should be run periodically via cron job
    """

    if current_user.role != "admin":
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
