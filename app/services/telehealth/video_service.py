"""
Telehealth Video Service
Manages secure video consultations using Twilio Video API

HIPAA Compliance:
- All recordings encrypted at rest
- BAA required with Twilio
- Session recordings stored securely
- Access logged for audit trails
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

from app.core.config import settings
from app.db.models.clinical_advanced import TelehealthSession
from app.db.models.user import User

logger = logging.getLogger(__name__)


class TelehealthVideoService:
    """
    Manages telehealth video consultations
    Integrates with Twilio Video for HIPAA-compliant video sessions
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._init_twilio()

    def _init_twilio(self):
        """Initialize Twilio client"""
        try:
            self.twilio_client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            logger.info("Twilio Video client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            self.twilio_client = None

    async def create_consultation_room(
        self,
        user_id: UUID,
        clinician_id: UUID,
        scheduled_time: datetime,
        session_type: str = "initial",
        duration_minutes: int = 60,
        recording_enabled: bool = False
    ) -> Dict:
        """
        Create a secure video consultation room

        Args:
            user_id: Patient user ID
            clinician_id: Clinician user ID
            scheduled_time: When the consultation is scheduled
            session_type: Type of session (initial, follow_up, crisis, group)
            duration_minutes: Expected session duration
            recording_enabled: Whether to record the session (requires consent)

        Returns:
            Dict with session details and access tokens
        """

        if not self.twilio_client:
            raise ValueError("Twilio Video service not available")

        # Verify participants exist
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        clinician_result = await self.db.execute(select(User).where(User.id == clinician_id))
        clinician = clinician_result.scalar_one_or_none()
        if not clinician:
            raise ValueError(f"Clinician {clinician_id} not found")

        # Generate unique room name
        room_name = f"consult_{user_id}_{int(scheduled_time.timestamp())}"
        token_expires_at = scheduled_time + timedelta(hours=2)

        try:
            # Create Twilio Video room
            room = self.twilio_client.video.rooms.create(
                unique_name=room_name,
                type='peer-to-peer',  # For 1:1 sessions (use 'group' for >2 participants)
                max_participants=2,
                record_participants_on_connect=recording_enabled,
                status_callback=f"{settings.API_URL}/api/v1/telehealth/webhook/twilio",
                status_callback_method='POST'
            )

            logger.info(f"Created Twilio room: {room.sid} for user {user_id}")

            # Generate access tokens
            user_token = self._generate_access_token(
                room_sid=room.sid,
                user_id=str(user_id),
                role='patient',
                expires_at=token_expires_at
            )

            clinician_token = self._generate_access_token(
                room_sid=room.sid,
                user_id=str(clinician_id),
                role='clinician',
                expires_at=token_expires_at
            )

            # Create database record
            session = TelehealthSession(
                user_id=user_id,
                clinician_id=clinician_id,
                org_id=user.org_id,
                session_type=session_type,
                scheduled_time=scheduled_time,
                duration_minutes=duration_minutes,
                room_sid=room.sid,
                room_name=room.unique_name,
                user_token=user_token,
                clinician_token=clinician_token,
                token_expires_at=token_expires_at,
                recording_enabled=recording_enabled,
                recording_encrypted=True,
                status='scheduled'
            )

            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)

            logger.info(f"Telehealth session {session.id} created successfully")

            return {
                'session_id': str(session.id),
                'room_name': room.unique_name,
                'user_token': user_token,
                'clinician_token': clinician_token,
                'scheduled_time': scheduled_time.isoformat(),
                'duration_minutes': duration_minutes,
                'recording_enabled': recording_enabled,
                'expires_at': token_expires_at.isoformat(),
                'status': 'scheduled'
            }

        except Exception as e:
            logger.error(f"Failed to create consultation room: {e}")
            raise

    def _generate_access_token(
        self,
        room_sid: str,
        user_id: str,
        role: str,
        expires_at: datetime
    ) -> str:
        """
        Generate JWT token for Twilio Video access

        Args:
            room_sid: Twilio room SID
            user_id: User ID
            role: 'patient' or 'clinician'
            expires_at: Token expiration time

        Returns:
            JWT token as string
        """

        # Create access token
        token = AccessToken(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_API_KEY_SID,
            settings.TWILIO_API_KEY_SECRET,
            identity=f"{role}_{user_id}",
            ttl=7200  # 2 hours
        )

        # Add video grant
        video_grant = VideoGrant(room=room_sid)
        token.add_grant(video_grant)

        return token.to_jwt()

    async def join_session(
        self,
        session_id: UUID,
        user_id: UUID,
        user_role: str  # 'patient' or 'clinician'
    ) -> Dict:
        """
        Get access token to join an existing session

        Args:
            session_id: Telehealth session ID
            user_id: User ID joining the session
            user_role: Role of the user ('patient' or 'clinician')

        Returns:
            Dict with room details and access token
        """

        # Get session
        result = await self.db.execute(
            select(TelehealthSession).where(TelehealthSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Verify user is authorized
        if user_role == 'patient' and session.user_id != user_id:
            raise ValueError("User not authorized for this session")
        if user_role == 'clinician' and session.clinician_id != user_id:
            raise ValueError("Clinician not authorized for this session")

        # Check if session is scheduled and not expired
        if session.status == 'cancelled':
            raise ValueError("This session has been cancelled")

        if session.token_expires_at and session.token_expires_at < datetime.utcnow():
            raise ValueError("Session access tokens have expired")

        # Get appropriate token
        access_token = session.user_token if user_role == 'patient' else session.clinician_token

        # If tokens are expired, regenerate them
        if session.token_expires_at and session.token_expires_at < datetime.utcnow() + timedelta(minutes=15):
            new_expires_at = datetime.utcnow() + timedelta(hours=2)
            new_token = self._generate_access_token(
                room_sid=session.room_sid,
                user_id=str(user_id),
                role=user_role,
                expires_at=new_expires_at
            )

            if user_role == 'patient':
                session.user_token = new_token
            else:
                session.clinician_token = new_token

            session.token_expires_at = new_expires_at
            await self.db.commit()

            access_token = new_token

        return {
            'session_id': str(session.id),
            'room_name': session.room_name,
            'access_token': access_token,
            'session_type': session.session_type,
            'scheduled_time': session.scheduled_time.isoformat(),
            'duration_minutes': session.duration_minutes,
            'recording_enabled': session.recording_enabled,
            'status': session.status
        }

    async def start_session(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> Dict:
        """
        Mark session as started

        Args:
            session_id: Telehealth session ID
            user_id: User ID (clinician) starting the session

        Returns:
            Updated session details
        """

        result = await self.db.execute(
            select(TelehealthSession).where(TelehealthSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Only clinician can start session
        if session.clinician_id != user_id:
            raise ValueError("Only clinician can start the session")

        session.status = 'in_progress'
        session.started_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session_id} started by clinician {user_id}")

        return {
            'session_id': str(session.id),
            'status': session.status,
            'started_at': session.started_at.isoformat()
        }

    async def end_session(
        self,
        session_id: UUID,
        user_id: UUID,
        session_notes: Optional[str] = None,
        diagnosis_codes: Optional[list] = None,
        treatment_plan: Optional[str] = None,
        patient_satisfaction: Optional[int] = None
    ) -> Dict:
        """
        End a telehealth session and save clinical notes

        Args:
            session_id: Telehealth session ID
            user_id: User ID ending the session
            session_notes: Clinical notes from the session
            diagnosis_codes: ICD-10 diagnosis codes
            treatment_plan: Treatment plan
            patient_satisfaction: Patient satisfaction rating (1-5)

        Returns:
            Updated session details
        """

        result = await self.db.execute(
            select(TelehealthSession).where(TelehealthSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Verify user is participant
        if user_id not in [session.user_id, session.clinician_id]:
            raise ValueError("User not authorized to end this session")

        # Calculate actual duration
        if session.started_at:
            duration = (datetime.utcnow() - session.started_at).seconds / 60
            session.actual_duration_minutes = int(duration)

        session.status = 'completed'
        session.ended_at = datetime.utcnow()

        # Save clinical data
        if session_notes:
            session.session_notes = session_notes
        if diagnosis_codes:
            session.diagnosis_codes = diagnosis_codes
        if treatment_plan:
            session.treatment_plan = treatment_plan
        if patient_satisfaction:
            session.patient_satisfaction = patient_satisfaction

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session_id} ended by user {user_id}")

        return {
            'session_id': str(session.id),
            'status': session.status,
            'ended_at': session.ended_at.isoformat(),
            'actual_duration_minutes': session.actual_duration_minutes
        }

    async def cancel_session(
        self,
        session_id: UUID,
        user_id: UUID,
        cancellation_reason: Optional[str] = None
    ) -> Dict:
        """
        Cancel a scheduled telehealth session

        Args:
            session_id: Telehealth session ID
            user_id: User ID cancelling the session
            cancellation_reason: Reason for cancellation

        Returns:
            Updated session details
        """

        result = await self.db.execute(
            select(TelehealthSession).where(TelehealthSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Verify user is participant
        if user_id not in [session.user_id, session.clinician_id]:
            raise ValueError("User not authorized to cancel this session")

        # Cannot cancel completed or in-progress sessions
        if session.status in ['completed', 'in_progress']:
            raise ValueError(f"Cannot cancel session with status: {session.status}")

        session.status = 'cancelled'
        session.cancelled_by = user_id
        session.cancelled_reason = cancellation_reason
        session.cancelled_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session_id} cancelled by user {user_id}")

        return {
            'session_id': str(session.id),
            'status': session.status,
            'cancelled_at': session.cancelled_at.isoformat(),
            'cancelled_by': str(user_id)
        }

    async def get_upcoming_sessions(
        self,
        user_id: UUID,
        role: str = 'patient'
    ) -> list:
        """
        Get upcoming telehealth sessions for a user

        Args:
            user_id: User ID
            role: 'patient' or 'clinician'

        Returns:
            List of upcoming sessions
        """

        query = select(TelehealthSession).where(
            TelehealthSession.status == 'scheduled',
            TelehealthSession.scheduled_time > datetime.utcnow()
        )

        if role == 'patient':
            query = query.where(TelehealthSession.user_id == user_id)
        else:
            query = query.where(TelehealthSession.clinician_id == user_id)

        query = query.order_by(TelehealthSession.scheduled_time)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return [
            {
                'session_id': str(session.id),
                'session_type': session.session_type,
                'scheduled_time': session.scheduled_time.isoformat(),
                'duration_minutes': session.duration_minutes,
                'status': session.status,
                'recording_enabled': session.recording_enabled
            }
            for session in sessions
        ]

    async def check_clinician_availability(
        self,
        clinician_id: UUID,
        requested_time: datetime
    ) -> bool:
        """
        Check if clinician is available at requested time

        Args:
            clinician_id: Clinician user ID
            requested_time: Desired consultation time

        Returns:
            True if available, False otherwise
        """

        # Check for existing sessions within 1 hour of requested time
        time_window_start = requested_time - timedelta(hours=1)
        time_window_end = requested_time + timedelta(hours=1)

        result = await self.db.execute(
            select(TelehealthSession).where(
                TelehealthSession.clinician_id == clinician_id,
                TelehealthSession.status.in_(['scheduled', 'in_progress']),
                TelehealthSession.scheduled_time >= time_window_start,
                TelehealthSession.scheduled_time <= time_window_end
            )
        )

        existing_sessions = result.scalars().all()

        return len(existing_sessions) == 0
