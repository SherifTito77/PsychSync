"""
Secure Session Management with Rotation

This module provides enterprise-grade session management with automatic
rotation, secure cookie handling, and device binding.

Compliance: OWASP ASVS v3.2.1, NIST SP 800-63B, HIPAA §164.312(e)(1)

Security Features:
- Session ID rotation (every 15 minutes or on privilege change)
- Secure cookie flags (HttpOnly, Secure, SameSite=Strict)
- Device binding (fingerprinting)
- Session fixation prevention
- Concurrent session limits
- Idle and absolute timeout enforcement

Usage:
    from app.services.session_service import SessionService

    service = SessionService()

    # Create session
    session_id = service.create_session(user_id, request)

    # Validate and rotate session
    is_valid, new_session_id = service.validate_and_rotate(session_id, request)

    # Invalidate session
    service.invalidate_session(session_id)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
import secrets
from typing import Any

# import uvicorn
from fastapi import Request

# ============================================================================
# Session Configuration
# ============================================================================

class SessionConfig:
    """Session configuration"""
    # Rotation
    ROTATION_INTERVAL_MINUTES = 15
    ROTATION_ON_PRIVILEGE_CHANGE = True

    # Timeouts
    IDLE_TIMEOUT_MINUTES = 30
    ABSOLUTE_TIMEOUT_HOURS = 8

    # Limits
    MAX_CONCURRENT_SESSIONS = 5
    MAX_SESSIONS_PER_USER = 10

    # Cookie security
    COOKIE_HTTPONLY = True
    COOKIE_SECURE = True
    COOKIE_SAMESITE = "Strict"
    COOKIE_PATH = "/"

    # Device fingerprinting
    DEVICE_FINGERPRINT_HEADERS = [
        "User-Agent",
        "Accept",
        "Accept-Language",
        "Accept-Encoding",
    ]


# ============================================================================
# Session Status
# ============================================================================

class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    IDLE_EXPIRED = "idle_expired"
    ABSOLUTE_EXPIRED = "absolute_expired"
    INVALIDATED = "invalidated"
    ROTATED = "rotated"
    SUPERSEDED = "superseded"  # New session created, old one invalid


# ============================================================================
# Session Data Classes
# ============================================================================

@dataclass
class SessionData:
    """Session data"""
    session_id: str
    user_id: str
    user_role: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    device_fingerprint: str
    ip_address: str
    user_agent: str
    csrf_token: str
    privileges: list[str] = field(default_factory=list)
    is_elevated: bool = False
    status: SessionStatus = SessionStatus.ACTIVE

    def is_valid(self) -> bool:
        """Check if session is still valid"""
        now = datetime.utcnow()

        # Check status
        if self.status != SessionStatus.ACTIVE:
            return False

        # Check absolute timeout
        if now > self.expires_at:
            self.status = SessionStatus.ABSOLUTE_EXPIRED
            return False

        # Check idle timeout
        idle_time = (now - self.last_activity).total_seconds()
        if idle_time > (SessionConfig.IDLE_TIMEOUT_MINUTES * 60):
            self.status = SessionStatus.IDLE_EXPIRED
            return False

        return True

    def should_rotate(self) -> bool:
        """Check if session should be rotated"""
        now = datetime.utcnow()
        time_since_rotation = (now - self.created_at).total_seconds() / 60

        # Rotate based on time
        if time_since_rotation >= SessionConfig.ROTATION_INTERVAL_MINUTES:
            return True

        # Rotate on privilege change (if elevated)
        if self.is_elevated and SessionConfig.ROTATION_ON_PRIVILEGE_CHANGE:
            return True

        return False


# ============================================================================
# Main Session Service
# ============================================================================

class SessionService:
    """
    Secure session management service

    Handles session creation, validation, rotation, and invalidation
    with security best practices
    """

    def __init__(self):
        """Initialize session service"""
        self.logger = logging.getLogger("app.security.session")

        # In production, use Redis/Database for:
        # - Session storage
        # - Device tracking
        # - CSRF tokens
        self._sessions: dict[str, SessionData] = {}
        self._user_sessions: dict[str, list[str]] = defaultdict(list)
        self._csrf_tokens: dict[str, str] = {}  # session_id -> token

    def create_session(
        self,
        user_id: str,
        user_role: str,
        request: Request,
        privileges: list[str] | None = None,
        remember_me: bool = False
    ) -> tuple[str, str]:
        """
        Create new session

        Args:
            user_id: User ID
            user_role: User role
            request: FastAPI request object
            privileges: List of user privileges
            remember_me: Whether to extend session lifetime

        Returns:
            Tuple of (session_id, csrf_token)
        """

        # Generate session ID (cryptographically secure)
        session_id = secrets.token_urlsafe(32)

        # Generate CSRF token
        csrf_token = secrets.token_urlsafe(32)
        self._csrf_tokens[session_id] = csrf_token

        # Calculate expiry
        now = datetime.utcnow()
        if remember_me:
            expires_at = now + timedelta(days=30)  # 30 days for "remember me"
        else:
            expires_at = now + timedelta(hours=SessionConfig.ABSOLUTE_TIMEOUT_HOURS)

        # Get device fingerprint
        device_fingerprint = self._generate_device_fingerprint(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Create session data
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            user_role=user_role,
            created_at=now,
            last_activity=now,
            expires_at=expires_at,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            csrf_token=csrf_token,
            privileges=privileges or [],
            is_elevated=False,
            status=SessionStatus.ACTIVE
        )

        # Enforce concurrent session limit
        self._enforce_concurrent_session_limit(user_id)

        # Store session
        self._sessions[session_id] = session
        self._user_sessions[user_id].append(session_id)

        self.logger.info(
            f"Created session {session_id[:8]}... for user {user_id} "
            f"(expires {expires_at.isoformat()})"
        )

        return session_id, csrf_token

    def validate_and_rotate(
        self,
        session_id: str,
        request: Request,
        csrf_token: str | None = None
    ) -> tuple[bool, str | None, SessionStatus | None]:
        """
        Validate session and rotate if needed

        Args:
            session_id: Session ID
            request: FastAPI request object
            csrf_token: CSRF token for validation

        Returns:
            Tuple of (is_valid, new_session_id, status)
        """

        # Get session
        session = self._sessions.get(session_id)

        if not session:
            return False, None, None

        # Check CSRF token
        if csrf_token and session.csrf_token != csrf_token:
            self.logger.warning(
                f"CSRF token mismatch for session {session_id[:8]}..."
            )
            session.status = SessionStatus.INVALIDATED
            return False, None, SessionStatus.INVALIDATED

        # Check device fingerprint
        current_fingerprint = self._generate_device_fingerprint(request)
        if current_fingerprint != session.device_fingerprint:
            self.logger.warning(
                f"Device fingerprint mismatch for session {session_id[:8]}..."
            )
            # Don't invalidate immediately (could be legit network change)
            # But log for security monitoring

        # Check if session is valid
        if not session.is_valid():
            status = session.status
            return False, None, status

        # Update last activity
        session.last_activity = datetime.utcnow()

        # Check if rotation needed
        if session.should_rotate():
            new_session_id = self._rotate_session(session_id, request)
            return True, new_session_id, SessionStatus.ROTATED

        return True, session_id, SessionStatus.ACTIVE

    def _rotate_session(
        self,
        old_session_id: str,
        request: Request
    ) -> str:
        """
        Rotate session ID (session fixation prevention)

        Args:
            old_session_id: Old session ID
            request: FastAPI request object

        Returns:
            New session ID
        """

        old_session = self._sessions[old_session_id]

        # Generate new session ID
        new_session_id = secrets.token_urlsafe(32)

        # Update session data
        old_session.session_id = new_session_id
        old_session.created_at = datetime.utcnow()  # Reset creation time

        # Move to new session ID
        self._sessions[new_session_id] = old_session
        self._sessions.pop(old_session_id)

        # Update user session mapping
        user_id = old_session.user_id
        if old_session_id in self._user_sessions[user_id]:
            idx = self._user_sessions[user_id].index(old_session_id)
            self._user_sessions[user_id][idx] = new_session_id

        # Move CSRF token
        self._csrf_tokens[new_session_id] = self._csrf_tokens.pop(old_session_id)

        self.logger.info(
            f"Rotated session {old_session_id[:8]}... -> {new_session_id[:8]}..."
        )

        return new_session_id

    def invalidate_session(self, session_id: str, reason: str = "") -> bool:
        """
        Invalidate session

        Args:
            session_id: Session ID
            reason: Reason for invalidation (for logging)

        Returns:
            True if session was invalidated
        """

        session = self._sessions.get(session_id)

        if not session:
            return False

        # Mark as invalidated
        session.status = SessionStatus.INVALIDATED

        # Remove from storage
        self._sessions.pop(session_id)

        # Remove from user session mapping
        user_id = session.user_id
        if session_id in self._user_sessions.get(user_id, []):
            self._user_sessions[user_id].remove(session_id)

        # Remove CSRF token
        self._csrf_tokens.pop(session_id, None)

        self.logger.info(
            f"Invalidated session {session_id[:8]}... "
            f"for user {user_id}. Reason: {reason}"
        )

        return True

    def invalidate_all_user_sessions(
        self,
        user_id: str,
        reason: str = ""
    ) -> int:
        """
        Invalidate all sessions for a user

        Args:
            user_id: User ID
            reason: Reason for invalidation

        Returns:
            Number of sessions invalidated
        """

        session_ids = self._user_sessions.get(user_id, []).copy()
        count = 0

        for session_id in session_ids:
            if self.invalidate_session(session_id, reason or "User-wide invalidation"):
                count += 1

        self.logger.info(
            f"Invalidated {count} session(s) for user {user_id}. "
            f"Reason: {reason}"
        )

        return count

    def _enforce_concurrent_session_limit(self, user_id: str):
        """
        Enforce concurrent session limit

        Args:
            user_id: User ID
        """

        user_sessions = self._user_sessions.get(user_id, [])

        # Check limit
        if len(user_sessions) >= SessionConfig.MAX_CONCURRENT_SESSIONS:
            # Invalidate oldest session
            oldest_session_id = user_sessions[0]
            self.invalidate_session(
                oldest_session_id,
                "Concurrent session limit exceeded"
            )

    def _generate_device_fingerprint(self, request: Request) -> str:
        """
        Generate device fingerprint from request headers

        Args:
            request: FastAPI request object

        Returns:
            Device fingerprint hash
        """

        # Collect fingerprint data
        fingerprint_data = []

        for header in SessionConfig.DEVICE_FINGERPRINT_HEADERS:
            value = request.headers.get(header, "")
            fingerprint_data.append(f"{header}:{value}")

        # Add IP address
        ip_address = self._get_client_ip(request)
        fingerprint_data.append(f"ip:{ip_address}")

        # Create hash
        fingerprint_str = "|".join(fingerprint_data)
        fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()

        return fingerprint_hash

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """

        # Check X-Forwarded-For header (proxy/reverse proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (original client)
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct connection
        if request.client:
            return request.client.host

        return "unknown"

    def get_session_cookie_config(self) -> dict[str, Any]:
        """
        Get secure cookie configuration

        Returns:
            Dictionary of cookie options
        """

        return {
            "httponly": SessionConfig.COOKIE_HTTPONLY,
            "secure": SessionConfig.COOKIE_SECURE,
            "samesite": SessionConfig.COOKIE_SAMESITE,
            "path": SessionConfig.COOKIE_PATH,
            # Don't set 'max_age' here - let session expiration handle it
        }

    def elevate_session(
        self,
        session_id: str,
        request: Request,
        reason: str = "Privilege escalation"
    ) -> bool:
        """
        Elevate session privileges (triggers rotation)

        Args:
            session_id: Session ID
            request: FastAPI request object
            reason: Reason for elevation

        Returns:
            True if session was elevated
        """

        session = self._sessions.get(session_id)

        if not session or not session.is_valid():
            return False

        # Mark as elevated
        session.is_elevated = True

        # Rotate session (security best practice)
        new_session_id = self._rotate_session(session_id, request)

        self.logger.info(
            f"Elevated session {session_id[:8]}... -> {new_session_id[:8]}... "
            f"for user {session.user_id}. Reason: {reason}"
        )

        return True

    def get_session_info(self, session_id: str) -> dict[str, Any] | None:
        """
        Get session information

        Args:
            session_id: Session ID

        Returns:
            Session information dictionary or None
        """

        session = self._sessions.get(session_id)

        if not session:
            return None

        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "user_role": session.user_role,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "ip_address": session.ip_address,
            "is_elevated": session.is_elevated,
            "status": session.status.value,
            "is_valid": session.is_valid(),
        }

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (should be run periodically)

        Returns:
            Number of sessions cleaned up
        """

        now = datetime.utcnow()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if now > session.expires_at or session.status != SessionStatus.ACTIVE:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.invalidate_session(session_id, "Session expired")

        self.logger.info(f"Cleaned up {len(expired_sessions)} expired session(s)")

        return len(expired_sessions)


# ============================================================================
# Helper Functions
# ============================================================================

def create_secure_session(
    user_id: str,
    user_role: str,
    request: Request,
    privileges: list[str] | None = None
) -> tuple[str, str]:
    """
    Convenience function to create secure session

    Args:
        user_id: User ID
        user_role: User role
        request: FastAPI request object
        privileges: User privileges

    Returns:
        Tuple of (session_id, csrf_token)
    """

    service = SessionService()
    return service.create_session(user_id, user_role, request, privileges)


def validate_session(
    session_id: str,
    request: Request,
    csrf_token: str | None = None
) -> tuple[bool, str | None]:
    """
    Convenience function to validate session

    Args:
        session_id: Session ID
        request: FastAPI request object
        csrf_token: CSRF token

    Returns:
        Tuple of (is_valid, new_session_id) - new_session_id only if rotated
    """

    service = SessionService()
    is_valid, new_session_id, _ = service.validate_and_rotate(
        session_id, request, csrf_token
    )

    return is_valid, new_session_id


def invalidate_session(session_id: str, reason: str = "") -> bool:
    """
    Convenience function to invalidate session

    Args:
        session_id: Session ID
        reason: Reason for invalidation

    Returns:
        True if session was invalidated
    """

    service = SessionService()
    return service.invalidate_session(session_id, reason)
