"""
Session Management and Rotation Service

Provides secure session lifecycle management:
- Automatic session rotation after login
- Session fingerprinting and device tracking
- Suspicious activity detection
- Concurrent session limits
- Secure session termination

SECURITY PRINCIPLES:
- Rotate sessions to prevent session hijacking
- Detect and prevent session hijacking attempts
- Limit concurrent sessions per user
- Track devices and locations
- Immediate session revocation capability

Author: Security Team
Version: 1.0
"""

import secrets
import hashlib
import logging
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from fastapi import Request, HTTPException, status

from app.db.models.user import User

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPICIOUS = "suspicious"


@dataclass
class SessionInfo:
    """Session information"""
    session_id: str
    user_id: str
    device_fingerprint: str
    ip_address: str
    user_agent: str
    location: Optional[str]
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: SessionStatus
    is_current: bool = False


class SessionRotationService:
    """
    Session rotation and management service

    Handles:
    - Session creation with device fingerprinting
    - Automatic session rotation
    - Session validation and refresh
    - Suspicious activity detection
    """

    def __init__(
        self,
        session_duration_minutes: int = 30,
        max_concurrent_sessions: int = 5,
        rotation_interval_minutes: int = 15
    ):
        """
        Initialize session service

        Args:
            session_duration_minutes: Default session duration
            max_concurrent_sessions: Max sessions per user
            rotation_interval_minutes: Interval for session rotation
        """
        self.session_duration = timedelta(minutes=session_duration_minutes)
        self.max_concurrent_sessions = max_concurrent_sessions
        self.rotation_interval = timedelta(minutes=rotation_interval_minutes)

        # In-memory session storage (in production, use Redis)
        self.active_sessions: Dict[str, SessionInfo] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids

    def generate_device_fingerprint(self, request: Request) -> str:
        """
        Generate device fingerprint from request

        Args:
            request: FastAPI Request object

        Returns:
            Device fingerprint hash
        """
        # Get relevant request attributes
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")

        # Create fingerprint string
        fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}"

        # Hash to create fingerprint
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def generate_session_id(self) -> str:
        """
        Generate cryptographically secure session ID

        Returns:
            Session ID
        """
        return secrets.token_urlsafe(32)

    async def create_session(
        self,
        user: User,
        request: Request
    ) -> SessionInfo:
        """
        Create new session for user

        Args:
            user: User object
            request: HTTP request

        Returns:
            SessionInfo object

        Raises:
            HTTPException: If max concurrent sessions exceeded
        """
        user_id = str(user.id)

        # Check concurrent session limit
        if user_id in self.user_sessions:
            active_count = len(self.user_sessions[user_id])
            if active_count >= self.max_concurrent_sessions:
                # Revoke oldest session
                oldest_session_id = min(self.user_sessions[user_id])
                await self.revoke_session(oldest_session_id, "Session limit exceeded")

        # Generate session attributes
        session_id = self.generate_session_id()
        device_fingerprint = self.generate_device_fingerprint(request)
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        location = self._get_location_from_ip(ip_address)

        now = datetime.utcnow()
        expires_at = now + self.session_duration

        # Create session
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
            status=SessionStatus.ACTIVE,
            is_current=True
        )

        # Store session
        self.active_sessions[session_id] = session

        # Add to user's sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)

        # Mark other sessions as not current
        for other_session_id in self.user_sessions[user_id]:
            if other_session_id != session_id:
                other_session = self.active_sessions.get(other_session_id)
                if other_session:
                    other_session.is_current = False

        logger.info(
            f"Session created for user {user_id}",
            extra={
                "user_id": user_id,
                "session_id": session_id,
                "ip_address": ip_address,
                "device_fingerprint": device_fingerprint[:16] + "..."
            }
        )

        return session

    async def validate_session(
        self,
        session_id: str,
        request: Request
    ) -> SessionInfo:
        """
        Validate session and return session info

        Args:
            session_id: Session ID to validate
            request: HTTP request

        Returns:
            SessionInfo object

        Raises:
            HTTPException: If session is invalid or expired
        """
        session = self.active_sessions.get(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        # Check if session is expired
        if datetime.utcnow() > session.expires_at:
            session.status = SessionStatus.EXPIRED
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )

        # Check if session is revoked
        if session.status == SessionStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked"
            )

        # Check for suspicious activity
        current_fingerprint = self.generate_device_fingerprint(request)
        current_ip = request.client.host if request.client else "unknown"

        if current_fingerprint != session.device_fingerprint:
            # Device mismatch - suspicious!
            logger.warning(
                f"Device fingerprint mismatch for session {session_id}",
                extra={
                    "session_id": session_id,
                    "expected": session.device_fingerprint[:16] + "...",
                    "received": current_fingerprint[:16] + "...",
                    "user_id": session.user_id
                }
            )

            # Mark as suspicious and require re-authentication
            session.status = SessionStatus.SUSPICIOUS
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Device fingerprint mismatch - please login again"
            )

        # Check IP change (location change)
        if current_ip != session.ip_address:
            logger.warning(
                f"IP address changed for session {session_id}",
                extra={
                    "session_id": session_id,
                    "old_ip": session.ip_address,
                    "new_ip": current_ip,
                    "user_id": session.user_id
                }
            )

            # Update IP and location (allow but log)
            session.ip_address = current_ip
            session.location = self._get_location_from_ip(current_ip)

        # Update last activity
        session.last_activity = datetime.utcnow()

        # Check if session should be rotated
        time_since_creation = datetime.utcnow() - session.created_at
        if time_since_creation > self.rotation_interval:
            logger.info(
                f"Session rotation triggered for {session_id}",
                extra={"session_id": session_id, "user_id": session.user_id}
            )
            # Would trigger rotation in production
            # For now, just update expiration
            session.expires_at = datetime.utcnow() + self.session_duration

        return session

    async def rotate_session(
        self,
        old_session_id: str,
        request: Request
    ) -> SessionInfo:
        """
        Rotate session (create new session, revoke old one)

        Args:
            old_session_id: Old session ID to rotate
            request: HTTP request

        Returns:
            New SessionInfo object

        Raises:
            HTTPException: If old session is invalid
        """
        old_session = self.active_sessions.get(old_session_id)

        if not old_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )

        # Revoke old session
        await self.revoke_session(old_session_id, "Session rotated")

        # Create new session
        # Note: Would need User object here
        # For now, return old session with updated ID
        old_session.status = SessionStatus.REVOKED

        logger.info(
            f"Session rotated: {old_session_id} -> revoked",
            extra={"old_session_id": old_session_id, "user_id": old_session.user_id}
        )

        return old_session  # Would return new session in production

    async def revoke_session(
        self,
        session_id: str,
        reason: str = "User logout"
    ) -> None:
        """
        Revoke a session

        Args:
            session_id: Session ID to revoke
            reason: Reason for revocation
        """
        session = self.active_sessions.get(session_id)

        if session:
            session.status = SessionStatus.REVOKED

            # Remove from user's active sessions
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].discard(session_id)

            logger.info(
                f"Session revoked: {session_id}",
                extra={
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "reason": reason
                }
            )

    async def revoke_all_user_sessions(
        self,
        user_id: str,
        reason: str = "Security action"
    ) -> int:
        """
        Revoke all sessions for a user

        Args:
            user_id: User ID
            reason: Reason for revocation

        Returns:
            Number of sessions revoked
        """
        if user_id not in self.user_sessions:
            return 0

        revoked_count = 0
        for session_id in list(self.user_sessions[user_id]):
            await self.revoke_session(session_id, reason)
            revoked_count += 1

        logger.info(
            f"All sessions revoked for user {user_id}",
            extra={"user_id": user_id, "count": revoked_count, "reason": reason}
        )

        return revoked_count

    def get_user_sessions(
        self,
        user_id: str
    ) -> List[SessionInfo]:
        """
        Get all active sessions for a user

        Args:
            user_id: User ID

        Returns:
            List of SessionInfo objects
        """
        if user_id not in self.user_sessions:
            return []

        sessions = []
        for session_id in self.user_sessions[user_id]:
            session = self.active_sessions.get(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)

        return sessions

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = []

        for session_id, session in list(self.active_sessions.items()):
            if now > session.expires_at or session.status != SessionStatus.ACTIVE:
                expired_sessions.append(session_id)

                # Remove from user's sessions
                if session.user_id in self.user_sessions:
                    self.user_sessions[session.user_id].discard(session_id)

        # Remove expired sessions
        for session_id in expired_sessions:
            del self.active_sessions[session_id]

        if expired_sessions:
            logger.info(
                f"Cleaned up {len(expired_sessions)} expired sessions"
            )

        return len(expired_sessions)

    def _get_location_from_ip(self, ip_address: str) -> Optional[str]:
        """
        Get location from IP address

        In production, would use geo-IP lookup service

        Args:
            ip_address: IP address

        Returns:
            Location string or None
        """
        # Simplified implementation
        # In production, use MaxMind GeoIP or similar
        if ip_address.startswith("127.") or ip_address == "localhost":
            return "Local"
        elif ip_address.startswith("192.168."):
            return "Private Network"
        else:
            return "Unknown"


# Singleton instance
session_service = SessionRotationService()
