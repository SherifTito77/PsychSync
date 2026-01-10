# app/core/session_security.py
"""
Session Security Manager for PsychSync
Handles secure session management with fixation prevention and hijacking detection
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import secrets

from app.core.cache import cache_delete, cache_get, cache_set

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Session metadata for security tracking"""

    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    fixation_prevented: bool = True


class SessionSecurityManager:
    """
    Enhanced session security manager with fixation prevention and hijacking detection
    """

    def __init__(self):
        self.max_concurrent_sessions = 3
        self.session_timeout_minutes = 60
        self.suspicious_activity_threshold = 5

        # Cache prefixes
        self.SESSION_PREFIX = "session:"
        self.USER_SESSIONS_PREFIX = "user_sessions:"
        self.SUSPICIOUS_ACTIVITY_PREFIX = "suspicious_activity:"

        # Track active sessions in memory for quick access
        self.active_sessions: dict[str, SessionMetadata] = {}
        self._lock = asyncio.Lock()

    async def create_secure_session(
        self, user_id: str, ip_address: str, user_agent: str, prevent_fixation: bool = True
    ) -> str:
        """
        Create secure session with fixation prevention

        Args:
            user_id: User identifier
            ip_address: Request IP address
            user_agent: User agent string
            prevent_fixation: Whether to enforce session fixation prevention

        Returns:
            New session ID
        """
        async with self._lock:
            try:
                # Generate cryptographically secure session ID
                session_id = secrets.token_urlsafe(32)

                # Create session metadata
                now = datetime.utcnow()
                expires_at = now + timedelta(minutes=self.session_timeout_minutes)

                metadata = SessionMetadata(
                    session_id=session_id,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent[:200] if user_agent else "",
                    created_at=now,
                    last_activity=now,
                    expires_at=expires_at,
                    fixation_prevented=prevent_fixation,
                )

                # Store session metadata
                session_data = {
                    "session_id": session_id,
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "user_agent": user_agent[:200] if user_agent else "",
                    "created_at": now.isoformat(),
                    "last_activity": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "is_active": True,
                    "fixation_prevented": prevent_fixation,
                }

                # Store in cache
                await cache_set(
                    f"{self.SESSION_PREFIX}{session_id}",
                    session_data,
                    expire_seconds=self.session_timeout_minutes * 60,
                )

                # Add to user's active sessions
                await self._add_user_session(user_id, session_id)

                # Enforce concurrent session limit
                await self._enforce_session_limit(user_id)

                # Track in memory
                self.active_sessions[session_id] = metadata

                logger.info(f"Secure session created: {session_id[:8]}... for user: {user_id}")

                return session_id

            except Exception as e:
                logger.error(f"Failed to create secure session: {e}")
                raise RuntimeError("Session creation failed") from e

    async def validate_session(
        self, session_id: str, user_id: str, ip_address: str, user_agent: str
    ) -> dict[str, Any]:
        """
        Validate session security and detect potential hijacking

        Args:
            session_id: Session identifier
            user_id: User identifier
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            Dict with validation result and security status
        """
        try:
            # Get session metadata
            session_data = await cache_get(f"{self.SESSION_PREFIX}{session_id}")

            if not session_data:
                return {
                    "valid": False,
                    "reason": "session_not_found",
                    "security_score": 0,
                    "action_required": "reauthenticate",
                }

            # Check if session belongs to user
            if session_data["user_id"] != user_id:
                await self._record_suspicious_activity(
                    user_id,
                    "session_user_mismatch",
                    f"Session {session_id[:8]}... accessed by wrong user",
                    ip_address,
                )
                return {
                    "valid": False,
                    "reason": "user_mismatch",
                    "security_score": 0,
                    "action_required": "reauthenticate",
                }

            # Check if session has expired
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                await self._cleanup_session(session_id, user_id)
                return {
                    "valid": False,
                    "reason": "session_expired",
                    "security_score": 0,
                    "action_required": "reauthenticate",
                }

            # Check for potential hijacking indicators
            security_score = 100
            warnings = []

            # IP address change detection
            original_ip = session_data["ip_address"]
            if original_ip and original_ip != ip_address:
                # Significant IP change - potential hijacking
                await self._record_suspicious_activity(
                    user_id,
                    "ip_address_change",
                    f"Session IP changed from {original_ip} to {ip_address}",
                    ip_address,
                )
                security_score -= 30
                warnings.append("ip_address_changed")

            # User agent change detection
            original_user_agent = session_data["user_agent"]
            if original_user_agent and original_user_agent != user_agent[:200]:
                # User agent change - potential hijacking
                await self._record_suspicious_activity(
                    user_id, "user_agent_change", "Session user agent changed", ip_address
                )
                security_score -= 20
                warnings.append("user_agent_changed")

            # Check for excessive session age
            created_at = datetime.fromisoformat(session_data["created_at"])
            session_age = datetime.utcnow() - created_at
            if session_age > timedelta(hours=24):
                security_score -= 10
                warnings.append("long_session_age")

            # Update last activity
            session_data["last_activity"] = datetime.utcnow().isoformat()
            await cache_set(
                f"{self.SESSION_PREFIX}{session_id}",
                session_data,
                expire_seconds=self.session_timeout_minutes * 60,
            )

            # Determine action based on security score
            action_required = None
            if security_score < 50:
                action_required = "reauthenticate"
            elif security_score < 70:
                action_required = "verify_identity"

            return {
                "valid": True,
                "security_score": security_score,
                "warnings": warnings,
                "action_required": action_required,
                "session_age_minutes": int(session_age.total_seconds() / 60),
            }

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return {
                "valid": False,
                "reason": "validation_error",
                "security_score": 0,
                "action_required": "reauthenticate",
            }

    async def invalidate_session(
        self, session_id: str, user_id: str, reason: str = "logout"
    ) -> bool:
        """
        Securely invalidate a session

        Args:
            session_id: Session to invalidate
            user_id: User who owns the session
            reason: Reason for invalidation

        Returns:
            True if successfully invalidated
        """
        try:
            # Remove from cache
            await cache_delete(f"{self.SESSION_PREFIX}{session_id}")

            # Remove from user's active sessions
            await self._remove_user_session(user_id, session_id)

            # Remove from memory tracking
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]

            logger.info(f"Session invalidated: {session_id[:8]}... Reason: {reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")
            return False

    async def invalidate_all_user_sessions(
        self, user_id: str, reason: str = "security_action"
    ) -> int:
        """
        Invalidate all sessions for a user

        Args:
            user_id: User whose sessions to invalidate
            reason: Reason for invalidation

        Returns:
            Number of sessions invalidated
        """
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            session_ids = await cache_get(user_sessions_key) or []

            invalidated_count = 0
            for session_id in session_ids:
                if await self.invalidate_session(session_id, user_id, reason):
                    invalidated_count += 1

            # Clear user sessions list
            await cache_delete(user_sessions_key)

            logger.info(
                f"Invalidated {invalidated_count} sessions for user: {user_id}. Reason: {reason}"
            )

            return invalidated_count

        except Exception as e:
            logger.error(f"Failed to invalidate user sessions: {e}")
            return 0

    async def get_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """
        Get all active sessions for a user

        Args:
            user_id: User identifier

        Returns:
            List of session information
        """
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            session_ids = await cache_get(user_sessions_key) or []

            sessions = []
            for session_id in session_ids:
                session_data = await cache_get(f"{self.SESSION_PREFIX}{session_id}")
                if session_data:
                    # Calculate session age
                    created_at = datetime.fromisoformat(session_data["created_at"])
                    last_activity = datetime.fromisoformat(session_data["last_activity"])

                    sessions.append(
                        {
                            "session_id": session_id,
                            "created_at": session_data["created_at"],
                            "last_activity": session_data["last_activity"],
                            "ip_address": session_data["ip_address"],
                            "user_agent": session_data["user_agent"][:50] + "..."
                            if len(session_data["user_agent"]) > 50
                            else session_data["user_agent"],
                            "age_minutes": int(
                                (datetime.utcnow() - created_at).total_seconds() / 60
                            ),
                            "inactive_minutes": int(
                                (datetime.utcnow() - last_activity).total_seconds() / 60
                            ),
                        }
                    )

            return sorted(sessions, key=lambda x: x["last_activity"], reverse=True)

        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []

    async def _add_user_session(self, user_id: str, session_id: str):
        """Add session to user's active sessions list"""
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            sessions = await cache_get(user_sessions_key) or []

            if session_id not in sessions:
                sessions.append(session_id)
                await cache_set(
                    user_sessions_key,
                    sessions,
                    expire_seconds=86400 * 7,  # 7 days
                )

        except Exception as e:
            logger.error(f"Failed to add user session: {e}")

    async def _remove_user_session(self, user_id: str, session_id: str):
        """Remove session from user's active sessions list"""
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            sessions = await cache_get(user_sessions_key) or []

            if session_id in sessions:
                sessions.remove(session_id)
                await cache_set(user_sessions_key, sessions, expire_seconds=86400 * 7)

        except Exception as e:
            logger.error(f"Failed to remove user session: {e}")

    async def _enforce_session_limit(self, user_id: str):
        """Enforce maximum concurrent sessions limit"""
        try:
            user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
            sessions = await cache_get(user_sessions_key) or []

            if len(sessions) > self.max_concurrent_sessions:
                # Remove oldest sessions
                sessions_to_remove = len(sessions) - self.max_concurrent_sessions

                for session_id in sessions[:sessions_to_remove]:
                    await self.invalidate_session(session_id, user_id, "session_limit_exceeded")

                logger.info(
                    f"Removed {sessions_to_remove} old sessions for user: {user_id} due to limit"
                )

        except Exception as e:
            logger.error(f"Failed to enforce session limit: {e}")

    async def _record_suspicious_activity(
        self, user_id: str, activity_type: str, description: str, ip_address: str
    ):
        """Record suspicious activity for monitoring"""
        try:
            suspicious_key = f"{self.SUSPICIOUS_ACTIVITY_PREFIX}{user_id}"
            activities = await cache_get(suspicious_key) or []

            activity = {
                "type": activity_type,
                "description": description,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat(),
            }

            activities.append(activity)

            # Keep only recent activities
            if len(activities) > 100:
                activities = activities[-100:]

            await cache_set(
                suspicious_key,
                activities,
                expire_seconds=86400 * 30,  # 30 days
            )

            # Check if activity threshold is exceeded
            recent_activities = [
                a
                for a in activities
                if datetime.utcnow() - datetime.fromisoformat(a["timestamp"]) < timedelta(hours=24)
            ]

            if len(recent_activities) >= self.suspicious_activity_threshold:
                logger.warning(
                    f"Suspicious activity threshold exceeded for user {user_id}: "
                    f"{len(recent_activities)} activities in 24 hours"
                )
                # Could trigger additional security measures here

        except Exception as e:
            logger.error(f"Failed to record suspicious activity: {e}")

    async def _cleanup_session(self, session_id: str, user_id: str):
        """Clean up expired session"""
        await self.invalidate_session(session_id, user_id, "expired")


# Global instance
session_security_manager = SessionSecurityManager()
