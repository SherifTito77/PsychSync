# app/core/session_management.py
"""
Advanced Session Management and Device Tracking for PsychSync
Implements device fingerprinting, concurrent session limits, and session security
"""

import hashlib
import logging
import secrets
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.core.cache import cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Device classification types"""

    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class SessionStatus(Enum):
    """Session status states"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


@dataclass
class DeviceFingerprint:
    """Device fingerprint information"""

    user_agent: str = ""
    ip_address: str = ""
    accept_language: str = ""
    accept_encoding: str = ""
    platform: str = ""
    vendor: str = ""
    screen_resolution: str = ""
    timezone: str = ""
    canvas_fingerprint: str = ""
    webgl_fingerprint: str = ""
    fonts_fingerprint: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_trusted: bool = False
    device_type: DeviceType = DeviceType.UNKNOWN


@dataclass
class UserSession:
    """User session information"""

    session_id: str
    user_id: str
    device_fingerprint: DeviceFingerprint
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )
    status: SessionStatus = SessionStatus.ACTIVE
    is_current_session: bool = False
    login_location: str | None = None
    access_count: int = 0
    security_flags: list[str] = field(default_factory=list)


class SessionManager:
    """
    Advanced session management with device tracking and security monitoring
    """

    def __init__(self):
        # Session policies
        self.max_concurrent_sessions = getattr(settings, "MAX_CONCURRENT_SESSIONS", 5)
        self.session_duration_hours = getattr(settings, "SESSION_DURATION_HOURS", 24)
        self.device_trust_duration_days = getattr(
            settings, "DEVICE_TRUST_DURATION_DAYS", 30
        )
        self.suspicious_activity_threshold = getattr(
            settings, "SUSPICIOUS_ACTIVITY_THRESHOLD", 3
        )

        # Cache keys
        self.SESSION_PREFIX = "session:"
        self.USER_SESSIONS_PREFIX = "user_sessions:"
        self.DEVICE_PREFIX = "device:"
        self.SESSION_ACTIVITY_PREFIX = "session_activity:"

        # Trusted devices tracking
        self.trusted_devices: dict[str, dict[str, Any]] = defaultdict(dict)

    async def create_session(
        self,
        user_id: str,
        device_fingerprint: DeviceFingerprint,
        request_headers: dict[str, str],
    ) -> UserSession:
        """
        Create a new user session with device tracking
        """
        try:
            session_id = secrets.token_urlsafe(32)

            # Create session object
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                device_fingerprint=device_fingerprint,
                expires_at=datetime.utcnow()
                + timedelta(hours=self.session_duration_hours),
                login_location=self._extract_location(request_headers),
                access_count=1,
            )

            # Check device trust
            device_id = self._generate_device_id(device_fingerprint)
            device_info = await self._get_device_info(device_id)

            if device_info.get("is_trusted", False):
                session.security_flags.append("trusted_device")
                device_fingerprint.is_trusted = True

            # Enforce concurrent session limit
            await self._enforce_session_limit(user_id, session)

            # Store session
            await self._store_session(session)

            # Record session activity
            await self._record_session_activity(
                session_id, "session_created", request_headers
            )

            logger.info(
                f"New session created for user {user_id}",
                extra={
                    "session_id": session_id,
                    "device_id": device_id,
                    "device_type": device_fingerprint.device_type.value,
                    "is_trusted": device_fingerprint.is_trusted,
                    "concurrent_sessions": await self._get_active_session_count(
                        user_id
                    ),
                },
            )

            return session

        except Exception as e:
            logger.error(f"Error creating session for user {user_id}: {e}")
            raise

    async def validate_session(
        self, session_id: str, user_id: str, current_headers: dict[str, str]
    ) -> dict[str, Any]:
        """
        Validate a session and return session status
        """
        try:
            session = await self._get_session(session_id)

            if not session:
                return {
                    "valid": False,
                    "reason": "session_not_found",
                    "action": "reauthenticate",
                }

            if session.user_id != user_id:
                return {
                    "valid": False,
                    "reason": "user_mismatch",
                    "action": "reauthenticate",
                }

            # Check session expiration
            if datetime.utcnow() > session.expires_at:
                await self._revoke_session(session_id, "expired")
                return {
                    "valid": False,
                    "reason": "session_expired",
                    "action": "reauthenticate",
                }

            # Check session status
            if session.status != SessionStatus.ACTIVE:
                return {
                    "valid": False,
                    "reason": f"session_{session.status.value}",
                    "action": "reauthenticate",
                }

            # Verify device consistency
            current_fingerprint = self._create_device_fingerprint(current_headers)
            device_match = self._verify_device_match(
                session.device_fingerprint, current_fingerprint
            )

            if not device_match:
                session.security_flags.append("suspicious_device_change")
                await self._store_session(session)

                # Log suspicious activity
                logger.warning(
                    f"Suspicious device change detected for session {session_id}",
                    extra={
                        "user_id": user_id,
                        "session_id": session_id,
                        "original_device": session.device_fingerprint.user_agent[:50],
                        "current_device": current_fingerprint.user_agent[:50],
                    },
                )

                return {
                    "valid": False,
                    "reason": "device_mismatch",
                    "action": "verify_identity",
                    "requires_verification": True,
                }

            # Update session activity
            session.last_activity = datetime.utcnow()
            session.access_count += 1
            await self._store_session(session)

            # Record activity
            await self._record_session_activity(
                session_id, "session_validated", current_headers
            )

            return {
                "valid": True,
                "session": session,
                "device_trusted": session.device_fingerprint.is_trusted,
            }

        except Exception as e:
            logger.error(f"Error validating session {session_id}: {e}")
            return {
                "valid": False,
                "reason": "validation_error",
                "action": "reauthenticate",
            }

    async def revoke_session(self, session_id: str, reason: str = "user_logout"):
        """
        Revoke a specific session
        """
        try:
            session = await self._get_session(session_id)
            if session:
                session.status = SessionStatus.REVOKED
                session.security_flags.append(f"revoked_{reason}")
                await self._store_session(session)

                logger.info(
                    f"Session revoked: {session_id}",
                    extra={"user_id": session.user_id, "reason": reason},
                )

        except Exception as e:
            logger.error(f"Error revoking session {session_id}: {e}")

    async def revoke_all_user_sessions(
        self, user_id: str, reason: str = "security_action"
    ):
        """
        Revoke all sessions for a user
        """
        try:
            sessions = await self._get_user_sessions(user_id)
            revoked_count = 0

            for session in sessions:
                if session.status == SessionStatus.ACTIVE:
                    await self.revoke_session(session.session_id, reason)
                    revoked_count += 1

            logger.info(
                f"Revoked {revoked_count} sessions for user {user_id}",
                extra={"reason": reason},
            )

        except Exception as e:
            logger.error(f"Error revoking sessions for user {user_id}: {e}")

    async def get_user_sessions(
        self, user_id: str, include_expired: bool = False
    ) -> list[UserSession]:
        """
        Get all sessions for a user
        """
        try:
            sessions = await self._get_user_sessions(user_id)

            if not include_expired:
                sessions = [
                    s
                    for s in sessions
                    if s.status == SessionStatus.ACTIVE
                    and s.expires_at > datetime.utcnow()
                ]

            return sorted(sessions, key=lambda x: x.last_activity, reverse=True)

        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []

    async def get_active_sessions(self, user_id: str) -> list[UserSession]:
        """
        Get active sessions for a user
        """
        return await self.get_user_sessions(user_id, include_expired=False)

    async def trust_device(self, user_id: str, device_fingerprint: DeviceFingerprint):
        """
        Mark a device as trusted for a user
        """
        try:
            device_id = self._generate_device_id(device_fingerprint)

            device_info = {
                "user_id": user_id,
                "device_id": device_id,
                "fingerprint": device_fingerprint,
                "trusted_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "is_trusted": True,
            }

            # Store trusted device with long expiration
            await cache_set(
                f"{self.DEVICE_PREFIX}{user_id}:{device_id}",
                device_info,
                expire_seconds=self.device_trust_duration_days * 24 * 3600,
            )

            logger.info(
                f"Device trusted for user {user_id}",
                extra={
                    "device_id": device_id,
                    "device_type": device_fingerprint.device_type.value,
                },
            )

        except Exception as e:
            logger.error(f"Error trusting device for user {user_id}: {e}")

    async def get_device_fingerprint(
        self, headers: dict[str, str]
    ) -> DeviceFingerprint:
        """
        Create device fingerprint from request headers
        """
        return self._create_device_fingerprint(headers)

    def _create_device_fingerprint(self, headers: dict[str, str]) -> DeviceFingerprint:
        """
        Create device fingerprint from HTTP headers
        """
        user_agent = headers.get("User-Agent", "")
        ip_address = headers.get("X-Forwarded-For", headers.get("X-Real-IP", ""))
        accept_language = headers.get("Accept-Language", "")
        accept_encoding = headers.get("Accept-Encoding", "")

        # Parse user agent for device type
        device_type = DeviceType.UNKNOWN
        if user_agent:
            ua_lower = user_agent.lower()
            if any(
                mobile in ua_lower for mobile in ["mobile", "android", "iphone", "ipad"]
            ):
                if "ipad" in ua_lower:
                    device_type = DeviceType.TABLET
                else:
                    device_type = DeviceType.MOBILE
            elif any(
                desktop in ua_lower
                for desktop in ["windows", "macintosh", "linux", "x11"]
            ):
                device_type = DeviceType.DESKTOP

        # Extract platform and vendor from user agent
        platform = "unknown"
        vendor = "unknown"

        if "Windows" in user_agent:
            platform = "Windows"
        elif "Macintosh" in user_agent:
            platform = "macOS"
        elif "Linux" in user_agent:
            platform = "Linux"
        elif "Android" in user_agent:
            platform = "Android"
        elif "iOS" in user_agent:
            platform = "iOS"

        return DeviceFingerprint(
            user_agent=user_agent,
            ip_address=ip_address.split(",")[0].strip() if ip_address else "",
            accept_language=accept_language,
            accept_encoding=accept_encoding,
            platform=platform,
            vendor=vendor,
            device_type=device_type,
        )

    def _generate_device_id(self, fingerprint: DeviceFingerprint) -> str:
        """
        Generate a consistent device ID from fingerprint
        """
        fingerprint_data = (
            f"{fingerprint.user_agent}|{fingerprint.platform}|{fingerprint.vendor}"
        )
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

    def _verify_device_match(
        self, original: DeviceFingerprint, current: DeviceFingerprint
    ) -> bool:
        """
        Verify if current device matches original fingerprint
        """
        # Check critical identifiers
        if original.platform != current.platform:
            return False

        if original.user_agent != current.user_agent:
            # Allow minor user agent changes (version updates)
            return self._is_similar_user_agent(original.user_agent, current.user_agent)

        return True

    def _is_similar_user_agent(self, original: str, current: str) -> bool:
        """
        Check if user agents are similar (allowing version changes)
        """
        # Remove version numbers and minor variations
        import re

        def normalize_ua(ua):
            # Remove version numbers and Chrome version info
            return re.sub(r"\d+(\.\d+)*", "X", ua.lower())

        normalized_original = normalize_ua(original)
        normalized_current = normalize_ua(current)

        # Check if normalized versions are very similar
        similarity = sum(
            a == b for a, b in zip(normalized_original, normalized_current)
        )
        total_length = max(len(normalized_original), len(normalized_current))

        return similarity / total_length > 0.9 if total_length > 0 else False

    def _extract_location(self, headers: dict[str, str]) -> str | None:
        """
        Extract location information from headers
        """
        # This could be enhanced with GeoIP lookup in production
        cf_ip = headers.get("CF-IPCountry")
        if cf_ip:
            return f"CF-{cf_ip}"

        return None

    async def _store_session(self, session: UserSession):
        """Store session in cache"""
        session_key = f"{self.SESSION_PREFIX}{session.session_id}"
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "device_fingerprint": {
                "user_agent": session.device_fingerprint.user_agent,
                "ip_address": session.device_fingerprint.ip_address,
                "platform": session.device_fingerprint.platform,
                "device_type": session.device_fingerprint.device_type.value,
                "is_trusted": session.device_fingerprint.is_trusted,
            },
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "status": session.status.value,
            "is_current_session": session.is_current_session,
            "login_location": session.login_location,
            "access_count": session.access_count,
            "security_flags": session.security_flags,
        }

        # Store with expiration matching session duration
        expire_seconds = int((session.expires_at - datetime.utcnow()).total_seconds())
        await cache_set(session_key, session_data, expire_seconds=expire_seconds)

        # Add to user's session list
        await self._add_to_user_sessions(session)

    async def _get_session(self, session_id: str) -> UserSession | None:
        """Get session from cache"""
        session_key = f"{self.SESSION_PREFIX}{session_id}"
        session_data = await cache_get(session_key)

        if not session_data:
            return None

        device_fingerprint = DeviceFingerprint(
            user_agent=session_data["device_fingerprint"]["user_agent"],
            ip_address=session_data["device_fingerprint"]["ip_address"],
            platform=session_data["device_fingerprint"]["platform"],
            device_type=DeviceType(session_data["device_fingerprint"]["device_type"]),
            is_trusted=session_data["device_fingerprint"]["is_trusted"],
        )

        return UserSession(
            session_id=session_data["session_id"],
            user_id=session_data["user_id"],
            device_fingerprint=device_fingerprint,
            created_at=datetime.fromisoformat(session_data["created_at"]),
            last_activity=datetime.fromisoformat(session_data["last_activity"]),
            expires_at=datetime.fromisoformat(session_data["expires_at"]),
            status=SessionStatus(session_data["status"]),
            is_current_session=session_data["is_current_session"],
            login_location=session_data.get("login_location"),
            access_count=session_data["access_count"],
            security_flags=session_data["security_flags"],
        )

    async def _add_to_user_sessions(self, session: UserSession):
        """Add session to user's session list"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{session.user_id}"
        user_sessions = await cache_get(user_sessions_key) or []

        # Add new session
        user_sessions.append(session.session_id)

        # Maintain only recent sessions (max 50)
        if len(user_sessions) > 50:
            user_sessions = user_sessions[-50:]

        await cache_set(
            user_sessions_key, user_sessions, expire_seconds=86400 * 30
        )  # 30 days

    async def _get_user_sessions(self, user_id: str) -> list[UserSession]:
        """Get all sessions for a user"""
        user_sessions_key = f"{self.USER_SESSIONS_PREFIX}{user_id}"
        session_ids = await cache_get(user_sessions_key) or []

        sessions = []
        for session_id in session_ids:
            session = await self._get_session(session_id)
            if session:
                sessions.append(session)

        return sessions

    async def _get_active_session_count(self, user_id: str) -> int:
        """Get count of active sessions for user"""
        sessions = await self.get_active_sessions(user_id)
        return len(sessions)

    async def get_active_session_count(self, user_id: str) -> int:
        """Public method to get count of active sessions for user"""
        return await self._get_active_session_count(user_id)

    async def _enforce_session_limit(self, user_id: str, new_session: UserSession):
        """Enforce concurrent session limit"""
        active_sessions = await self.get_active_sessions(user_id)

        if len(active_sessions) >= self.max_concurrent_sessions:
            # Revoke oldest session(s)
            sessions_to_revoke = sorted(active_sessions, key=lambda x: x.last_activity)[
                : len(active_sessions) - self.max_concurrent_sessions + 1
            ]

            for session in sessions_to_revoke:
                await self.revoke_session(session.session_id, "concurrent_limit")

    async def _get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get device information"""
        # This would be enhanced to look up from user-specific device registry
        return {"is_trusted": False}

    async def _record_session_activity(
        self, session_id: str, activity_type: str, headers: dict[str, str]
    ):
        """Record session activity for security monitoring"""
        activity_data = {
            "activity_type": activity_type,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": headers.get("X-Forwarded-For", headers.get("X-Real-IP", "")),
            "user_agent": headers.get("User-Agent", ""),
        }

        activity_key = f"{self.SESSION_ACTIVITY_PREFIX}{session_id}"
        activities = await cache_get(activity_key) or []

        activities.append(activity_data)

        # Keep only recent activities (last 100)
        if len(activities) > 100:
            activities = activities[-100:]

        await cache_set(activity_key, activities, expire_seconds=86400)  # 24 hours

    async def revoke_all_except_current(
        self, user_id: str, current_session_id: str, reason: str = "password_change"
    ):
        """
        Revoke all sessions except the current one.
        Used after password change or security events.
        """
        try:
            sessions = await self._get_user_sessions(user_id)
            revoked_count = 0

            for session in sessions:
                if (
                    session.session_id != current_session_id
                    and session.status == SessionStatus.ACTIVE
                ):
                    await self.revoke_session(session.session_id, reason)
                    revoked_count += 1

            logger.info(
                "Revoked %d sessions for user %s (reason: %s, kept: %s)",
                revoked_count,
                user_id,
                reason,
                current_session_id[:8],
            )
            return revoked_count

        except Exception as e:
            logger.error(f"Error revoking sessions for user {user_id}: {e}")
            return 0

    @staticmethod
    def _mask_ip(ip: str) -> str:
        """Mask IP address for GDPR/HIPAA compliance. Shows only network prefix."""
        if not ip:
            return ""
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        # IPv6 or other format — show first segment only
        if ":" in ip:
            segments = ip.split(":")
            return f"{segments[0]}:{segments[1] if len(segments) > 1 else ''}::*"
        return ip[:4] + "***"

    async def get_sessions_summary(self, user_id: str) -> dict:
        """
        Get a summary of all sessions for the user management UI.
        Sanitizes sensitive data before returning.
        """
        sessions = await self.get_user_sessions(user_id, include_expired=False)
        return {
            "active_count": len(sessions),
            "max_allowed": self.max_concurrent_sessions,
            "sessions": [
                {
                    "session_id": s.session_id[:8] + "...",
                    "device_type": s.device_fingerprint.device_type.value,
                    "platform": s.device_fingerprint.platform,
                    "ip_address": self._mask_ip(s.device_fingerprint.ip_address),
                    "location": s.login_location,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity.isoformat(),
                    "is_trusted": s.device_fingerprint.is_trusted,
                    "is_current": s.is_current_session,
                }
                for s in sessions
            ],
        }


# Global session manager instance
session_manager = SessionManager()
