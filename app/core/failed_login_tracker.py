# app/core/failed_login_tracker.py
"""
Failed Login Attempt Tracker with Rate Limiting and Account Lockout
Tracks failed login attempts per user and IP, with automatic account lockout

Features:
- Per-user failed login counting
- Per-IP failed login counting
- Automatic account lockout after threshold
- Configurable lockout duration
- Integration with rate limiter
- Lockout notification

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import time
import asyncio
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from app.core.cache import cache_get, cache_set, cache_delete
import logging

logger = logging.getLogger(__name__)


class LockoutReason(Enum):
    """Reasons for account lockout"""
    TOO_MANY_ATTEMPTS = "too_many_attempts"
    BRUTE_FORCE_DETECTED = "brute_force_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ADMIN_LOCKED = "admin_locked"


@dataclass
class LoginAttempt:
    """Record of a login attempt"""
    timestamp: datetime
    success: bool
    ip_address: str
    user_agent: str
    username: Optional[str] = None


@dataclass
class LockoutInfo:
    """Account lockout information"""
    is_locked: bool
    reason: Optional[LockoutReason]
    locked_at: Optional[datetime]
    expires_at: Optional[datetime]
    attempts_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_locked": self.is_locked,
            "reason": self.reason.value if self.reason else None,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "attempts_count": self.attempts_count,
            "metadata": self.metadata
        }


class FailedLoginTracker:
    """
    Track failed login attempts and implement automatic account lockout
    """

    # Cache key prefixes
    USER_ATTEMPTS_PREFIX = "login_attempts:user:"
    IP_ATTEMPTS_PREFIX = "login_attempts:ip:"
    LOCKOUT_PREFIX = "account_lockout:"

    def __init__(
        self,
        max_attempts: int = 5,
        lockout_duration_minutes: int = 15,
        tracking_window_minutes: int = 15
    ):
        """
        Initialize failed login tracker

        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_duration_minutes: How long to lock account (default: 15 minutes)
            tracking_window_minutes: Time window to count attempts (default: 15 minutes)
        """
        self.max_attempts = max_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self.tracking_window = timedelta(minutes=tracking_window_minutes)

    async def record_login_attempt(
        self,
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str = ""
    ) -> Tuple[bool, Optional[LockoutInfo]]:
        """
        Record a login attempt and check if account should be locked

        Args:
            username: Username attempting login
            success: Whether login was successful
            ip_address: IP address of attempt
            user_agent: User agent string

        Returns:
            Tuple of (should_allow, lockout_info)
            - should_allow: True if login should be allowed, False if locked
            - lockout_info: LockoutInfo if locked or exceeded threshold, None otherwise
        """
        try:
            # Check if already locked first
            lockout_info = await self.get_lockout_status(username)
            if lockout_info.is_locked:
                logger.warning(f"Login attempt for locked account: {username}", extra={
                    "username": username,
                    "ip_address": ip_address,
                    "lockout_reason": lockout_info.reason.value if lockout_info.reason else None
                })
                return False, lockout_info

            # If successful login, clear failed attempts
            if success:
                await self.clear_failed_attempts(username)
                return True, None

            # Record failed attempt
            await self._record_failed_attempt(username, ip_address, user_agent)

            # Check if should lock
            attempts = await self.get_failed_attempt_count(username)
            if attempts >= self.max_attempts:
                lockout_info = await self._lock_account(
                    username=username,
                    reason=LockoutReason.TOO_MANY_ATTEMPTS,
                    ip_address=ip_address,
                    attempts_count=attempts
                )
                return False, lockout_info

            # Return warning info if approaching threshold
            if attempts >= self.max_attempts - 1:
                warning_info = LockoutInfo(
                    is_locked=False,
                    reason=None,
                    locked_at=None,
                    expires_at=None,
                    attempts_count=attempts,
                    metadata={"warning": "One more attempt will lock account"}
                )
                return True, warning_info

            return True, None

        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
            # Fail open - allow login on error
            return True, None

    async def _record_failed_attempt(
        self,
        username: str,
        ip_address: str,
        user_agent: str
    ):
        """Record a failed login attempt in cache"""
        try:
            # Record per-user attempt
            user_key = f"{self.USER_ATTEMPTS_PREFIX}{username}"
            user_attempts = await cache_get(user_key) or []

            attempt = {
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent[:200]  # Truncate for storage
            }

            user_attempts.append(attempt)

            # Clean old attempts outside tracking window
            cutoff_time = datetime.utcnow() - self.tracking_window
            user_attempts = [
                a for a in user_attempts
                if datetime.fromisoformat(a["timestamp"]) >= cutoff_time
            ]

            # Store with expiration
            await cache_set(user_key, user_attempts, expire_seconds=int(self.tracking_window.total_seconds()))

            # Also track per-IP (for detecting credential stuffing)
            ip_key = f"{self.IP_ATTEMPTS_PREFIX}{ip_address}"
            ip_attempts = await cache_get(ip_key) or []

            ip_attempt = {
                "timestamp": datetime.utcnow().isoformat(),
                "username": username
            }

            ip_attempts.append(ip_attempt)

            # Keep last 100 IP attempts
            if len(ip_attempts) > 100:
                ip_attempts = ip_attempts[-100:]

            # Store with longer expiration for IP tracking
            await cache_set(ip_key, ip_attempts, expire_seconds=3600)  # 1 hour

        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")

    async def get_failed_attempt_count(self, username: str) -> int:
        """Get count of recent failed login attempts for user"""
        try:
            user_key = f"{self.USER_ATTEMPTS_PREFIX}{username}"
            attempts = await cache_get(user_key) or []
            return len(attempts)
        except Exception as e:
            logger.error(f"Error getting failed attempt count: {e}")
            return 0

    async def get_failed_attempts(self, username: str) -> list:
        """Get list of recent failed login attempts for user"""
        try:
            user_key = f"{self.USER_ATTEMPTS_PREFIX}{username}"
            attempts = await cache_get(user_key) or []
            return attempts
        except Exception as e:
            logger.error(f"Error getting failed attempts: {e}")
            return []

    async def clear_failed_attempts(self, username: str):
        """Clear failed login attempts for user (called after successful login)"""
        try:
            user_key = f"{self.USER_ATTEMPTS_PREFIX}{username}"
            await cache_delete(user_key)
        except Exception as e:
            logger.error(f"Error clearing failed attempts: {e}")

    async def _lock_account(
        self,
        username: str,
        reason: LockoutReason,
        ip_address: str,
        attempts_count: int
    ) -> LockoutInfo:
        """Lock account after too many failed attempts"""
        try:
            lockout_info = LockoutInfo(
                is_locked=True,
                reason=reason,
                locked_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.lockout_duration,
                attempts_count=attempts_count,
                metadata={
                    "locking_ip": ip_address,
                    "lockout_duration_minutes": int(self.lockout_duration.total_seconds() / 60)
                }
            )

            # Store lockout info
            lockout_key = f"{self.LOCKOUT_PREFIX}{username}"
            await cache_set(
                lockout_key,
                lockout_info.to_dict(),
                expire_seconds=int(self.lockout_duration.total_seconds())
            )

            # Log the lockout
            logger.warning(f"Account locked: {username}", extra={
                "username": username,
                "reason": reason.value,
                "attempts": attempts_count,
                "ip_address": ip_address,
                "locked_until": lockout_info.expires_at.isoformat()
            })

            return lockout_info

        except Exception as e:
            logger.error(f"Error locking account: {e}")
            # Return minimal lockout info on error
            return LockoutInfo(
                is_locked=True,
                reason=reason,
                locked_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.lockout_duration,
                attempts_count=attempts_count
            )

    async def get_lockout_status(self, username: str) -> LockoutInfo:
        """Check if account is currently locked"""
        try:
            lockout_key = f"{self.LOCKOUT_PREFIX}{username}"
            lockout_data = await cache_get(lockout_key)

            if not lockout_data:
                return LockoutInfo(
                    is_locked=False,
                    reason=None,
                    locked_at=None,
                    expires_at=None,
                    attempts_count=0
                )

            # Check if lockout has expired
            if lockout_data.get("expires_at"):
                expires_at = datetime.fromisoformat(lockout_data["expires_at"])
                if datetime.utcnow() >= expires_at:
                    # Lockout expired, clear it
                    await cache_delete(lockout_key)
                    return LockoutInfo(
                        is_locked=False,
                        reason=None,
                        locked_at=None,
                        expires_at=None,
                        attempts_count=0
                    )

            # Account is locked
            return LockoutInfo(
                is_locked=True,
                reason=LockoutReason(lockout_data["reason"]) if lockout_data.get("reason") else None,
                locked_at=datetime.fromisoformat(lockout_data["locked_at"]) if lockout_data.get("locked_at") else None,
                expires_at=datetime.fromisoformat(lockout_data["expires_at"]) if lockout_data.get("expires_at") else None,
                attempts_count=lockout_data.get("attempts_count", 0),
                metadata=lockout_data.get("metadata", {})
            )

        except Exception as e:
            logger.error(f"Error getting lockout status: {e}")
            return LockoutInfo(
                is_locked=False,
                reason=None,
                locked_at=None,
                expires_at=None,
                attempts_count=0
            )

    async def unlock_account(self, username: str) -> bool:
        """
        Manually unlock an account

        Args:
            username: Username to unlock

        Returns:
            True if unlocked successfully
        """
        try:
            lockout_key = f"{self.LOCKOUT_PREFIX}{username}"
            await cache_delete(lockout_key)

            # Also clear failed attempts
            await self.clear_failed_attempts(username)

            logger.info(f"Account unlocked: {username}", extra={"username": username})

            return True

        except Exception as e:
            logger.error(f"Error unlocking account: {e}")
            return False

    async def get_ip_failed_attempts(self, ip_address: str) -> list:
        """Get recent failed login attempts from an IP address"""
        try:
            ip_key = f"{self.IP_ATTEMPTS_PREFIX}{ip_address}"
            attempts = await cache_get(ip_key) or []
            return attempts
        except Exception as e:
            logger.error(f"Error getting IP failed attempts: {e}")
            return []

    async def is_ip_blocked(self, ip_address: str, threshold: int = 20) -> bool:
        """
        Check if IP should be blocked due to excessive failed attempts

        Args:
            ip_address: IP address to check
            threshold: Number of attempts to consider as blocking threshold

        Returns:
            True if IP should be blocked
        """
        try:
            attempts = await self.get_ip_failed_attempts(ip_address)

            # Count unique usernames attempted (credential stuffing detection)
            unique_usernames = set(a.get("username") for a in attempts if a.get("username"))

            if len(unique_usernames) >= threshold:
                logger.warning(f"IP blocked due to credential stuffing: {ip_address}", extra={
                    "ip_address": ip_address,
                    "unique_usernames_attempted": len(unique_usernames),
                    "total_attempts": len(attempts)
                })
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False

    async def get_statistics(self, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Get failed login statistics

        Args:
            username: Optional username to get stats for specific user

        Returns:
            Dictionary with statistics
        """
        try:
            if username:
                user_attempts = await self.get_failed_attempts(username)
                user_lockout = await self.get_lockout_status(username)

                return {
                    "username": username,
                    "failed_attempts": len(user_attempts),
                    "is_locked": user_lockout.is_locked,
                    "lockout_reason": user_lockout.reason.value if user_lockout.reason else None,
                    "attempts": user_attempts[-10:] if user_attempts else []  # Last 10 attempts
                }
            else:
                # Global stats would require scanning all keys - expensive
                # Return placeholder for now
                return {
                    "message": "Per-user statistics available. Specify username parameter.",
                    "max_attempts": self.max_attempts,
                    "lockout_duration_minutes": int(self.lockout_duration.total_seconds() / 60),
                    "tracking_window_minutes": int(self.tracking_window.total_seconds() / 60)
                }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Global instance
failed_login_tracker = FailedLoginTracker(
    max_attempts=5,
    lockout_duration_minutes=15,
    tracking_window_minutes=15
)
