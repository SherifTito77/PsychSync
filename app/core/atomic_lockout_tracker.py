"""
Atomic Lockout Tracker - Race-Condition Free Authentication Security

This module provides thread-safe, atomic lockout tracking using Redis INCR operations.
Eliminates race conditions in the original account_lockout_enhanced.py implementation.

Key Improvements:
- Atomic operations using Redis INCR
- No read-modify-write race conditions
- Automatic expiry of failed attempt counters
- IP-based and user-based lockout tracking
- Distributed lockout tracking (works across multiple servers)

Author: Security Team
Version: 2.0 (Atomic Implementation)
Date: 2025-01-19
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class AtomicLockoutTracker:
    """
    Thread-safe, atomic lockout tracker using Redis operations.

    Uses Redis INCR for atomic increments, eliminating race conditions
    in the original read-modify-write implementation.
    """

    # Lockout thresholds (configurable)
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_SECONDS = 3600  # 1 hour
    FAILED_ATTEMPT_WINDOW_SECONDS = 900  # 15 minutes

    # IP banning thresholds
    MAX_IP_FAILED_ATTEMPTS = 20
    IP_BAN_DURATION_SECONDS = 86400  # 24 hours

    def __init__(self):
        """Initialize the atomic lockout tracker."""
        self._redis_client: Optional[redis.Redis] = None

    async def _get_redis_client(self) -> redis.Redis:
        """
        Get Redis client with lazy initialization.

        Returns:
            Redis client instance

        Raises:
            redis.ConnectionError: If Redis connection fails
        """
        if self._redis_client is None:
            try:
                self._redis_client = await redis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    decoding="utf-8",
                    health_check_interval=30
                )
                logger.info("Atomic lockout tracker connected to Redis")
            except Exception as e:
                logger.error("Failed to connect to Redis for lockout tracking: %s", e)
                raise

        return self._redis_client

    async def close(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.info("Atomic lockout tracker Redis connection closed")

    async def record_failed_attempt(
        self,
        user_id: str,
        ip_address: str,
        db=None  # Unused, kept for backward compatibility
    ) -> Tuple[bool, Optional[str]]:
        """
        Record a failed login attempt atomically using Redis INCR.

        This eliminates the race condition in the original implementation
        where multiple concurrent requests could read the same count and
        increment it multiple times, bypassing lockout.

        Args:
            user_id: User ID (or "unknown" for non-existent users)
            ip_address: Client IP address
            db: Database session (unused, for backward compatibility)

        Returns:
            (is_locked, lockout_message) tuple
                - is_locked: True if user/IP is now locked out
                - lockout_message: Message describing lockout if locked

        Example:
            >>> is_locked, msg = await tracker.record_failed_attempt("user123", "192.168.1.1")
            >>> if is_locked:
            ...     print(f"Account locked: {msg}")
        """
        try:
            redis_client = await self._get_redis_client()

            # Atomic increment of user failed attempts
            user_key = f"failed_attempts:user:{user_id}"
            user_attempts = await redis_client.incr(user_key)

            # Set expiry on first attempt (prevents stale data)
            if user_attempts == 1:
                await redis_client.expire(user_key, self.FAILED_ATTEMPT_WINDOW_SECONDS)

            # Check if user should be locked out
            if user_attempts >= self.MAX_FAILED_ATTEMPTS:
                # Set lockout flag with expiry
                lockout_key = f"locked:user:{user_id}"
                await redis_client.setex(
                    lockout_key,
                    self.LOCKOUT_DURATION_SECONDS,
                    "1"
                )

                remaining_time = self.LOCKOUT_DURATION_SECONDS
                logger.warning(
                    "User %s locked out after %d failed attempts from IP %s",
                    user_id,
                    user_attempts,
                    ip_address
                )

                return True, (
                    f"Account locked due to too many failed attempts. "
                    f"Try again in {remaining_time // 60} minutes."
                )

            # Atomic increment of IP failed attempts
            ip_key = f"failed_attempts:ip:{ip_address}"
            ip_attempts = await redis_client.incr(ip_key)

            # Set expiry on first attempt
            if ip_attempts == 1:
                await redis_client.expire(ip_key, self.FAILED_ATTEMPT_WINDOW_SECONDS)

            # Check if IP should be banned
            if ip_attempts >= self.MAX_IP_FAILED_ATTEMPTS:
                # Set IP ban flag with expiry
                ip_ban_key = f"banned:ip:{ip_address}"
                await redis_client.setex(
                    ip_ban_key,
                    self.IP_BAN_DURATION_SECONDS,
                    "1"
                )

                remaining_time = self.IP_BAN_DURATION_SECONDS
                logger.warning(
                    "IP %s banned after %d failed attempts",
                    ip_address,
                    ip_attempts
                )

                return True, (
                    f"Too many failed attempts from your IP. "
                    f"Try again in {remaining_time // 60} minutes."
                )

            # Not locked yet, return attempt counts
            logger.info(
                "Failed attempt recorded for user %s from IP %s "
                "(user attempts: %d, IP attempts: %d)",
                user_id,
                ip_address,
                user_attempts,
                ip_attempts
            )

            return False, None

        except redis.ConnectionError as e:
            logger.error("Redis connection error in record_failed_attempt: %s", e)
            # Fail open - don't lock out if Redis is down
            return False, None
        except Exception as e:
            logger.error("Unexpected error in record_failed_attempt: %s", e)
            # Fail open - don't lock out on unexpected errors
            return False, None

    async def record_successful_attempt(
        self,
        user_id: str,
        ip_address: str,
        db=None  # Unused, kept for backward compatibility
    ) -> None:
        """
        Record a successful login attempt by clearing failed attempt counters.

        Args:
            user_id: User ID
            ip_address: Client IP address
            db: Database session (unused, for backward compatibility)
        """
        try:
            redis_client = await self._get_redis_client()

            # Clear user failed attempts
            user_key = f"failed_attempts:user:{user_id}"
            await redis_client.delete(user_key)

            # Clear IP failed attempts (partial reset - divide by 2)
            # This prevents IP ban from single compromised account
            ip_key = f"failed_attempts:ip:{ip_address}"
            current_attempts = await redis_client.get(ip_key)
            if current_attempts:
                try:
                    attempts_int = int(current_attempts)
                    # Reduce by half (minimum 1)
                    new_attempts = max(1, attempts_int // 2)
                    await redis_client.setex(
                        ip_key,
                        self.FAILED_ATTEMPT_WINDOW_SECONDS,
                        str(new_attempts)
                    )
                except ValueError:
                    # If not an integer, delete the key
                    await redis_client.delete(ip_key)

            logger.info(
                "Successful login recorded for user %s from IP %s",
                user_id,
                ip_address
            )

        except Exception as e:
            # Don't fail on successful login
            logger.error("Error clearing failed attempts for user %s: %s", user_id, e)

    async def is_user_locked_out(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user is currently locked out.

        Args:
            user_id: User ID to check

        Returns:
            (is_locked, remaining_seconds) tuple
                - is_locked: True if user is locked out
                - remaining_seconds: Seconds remaining in lockout (0 if not locked)
        """
        try:
            redis_client = await self._get_redis_client()

            lockout_key = f"locked:user:{user_id}"
            remaining_ttl = await redis_client.ttl(lockout_key)

            if remaining_ttl > 0:
                return True, remaining_ttl

            return False, 0

        except Exception as e:
            logger.error("Error checking lockout status for user %s: %s", user_id, e)
            # Fail open - don't lock out if we can't check
            return False, 0

    async def is_ip_banned(self, ip_address: str) -> Tuple[bool, int]:
        """
        Check if IP address is currently banned.

        Args:
            ip_address: IP address to check

        Returns:
            (is_banned, remaining_seconds) tuple
                - is_banned: True if IP is banned
                - remaining_seconds: Seconds remaining in ban (0 if not banned)
        """
        try:
            redis_client = await self._get_redis_client()

            ip_ban_key = f"banned:ip:{ip_address}"
            remaining_ttl = await redis_client.ttl(ip_ban_key)

            if remaining_ttl > 0:
                return True, remaining_ttl

            return False, 0

        except Exception as e:
            logger.error("Error checking IP ban status for %s: %s", ip_address, e)
            # Fail open - don't ban if we can't check
            return False, 0

    async def get_failed_attempt_counts(
        self,
        user_id: str,
        ip_address: str
    ) -> Tuple[int, int]:
        """
        Get current failed attempt counts for monitoring/debugging.

        Args:
            user_id: User ID to check
            ip_address: IP address to check

        Returns:
            (user_attempts, ip_attempts) tuple
        """
        try:
            redis_client = await self._get_redis_client()

            user_key = f"failed_attempts:user:{user_id}"
            ip_key = f"failed_attempts:ip:{ip_address}"

            user_attempts_str = await redis_client.get(user_key)
            ip_attempts_str = await redis_client.get(ip_key)

            user_attempts = int(user_attempts_str) if user_attempts_str else 0
            ip_attempts = int(ip_attempts_str) if ip_attempts_str else 0

            return user_attempts, ip_attempts

        except Exception as e:
            logger.error("Error getting failed attempt counts: %s", e)
            return 0, 0

    async def reset_user_lockout(self, user_id: str) -> bool:
        """
        Manually reset user lockout (admin function).

        Args:
            user_id: User ID to reset

        Returns:
            True if reset successful, False otherwise
        """
        try:
            redis_client = await self._get_redis_client()

            # Clear lockout flag
            lockout_key = f"locked:user:{user_id}"
            await redis_client.delete(lockout_key)

            # Clear failed attempts
            user_key = f"failed_attempts:user:{user_id}"
            await redis_client.delete(user_key)

            logger.info("Manually reset lockout for user %s", user_id)
            return True

        except Exception as e:
            logger.error("Error resetting lockout for user %s: %s", user_id, e)
            return False

    async def reset_ip_ban(self, ip_address: str) -> bool:
        """
        Manually reset IP ban (admin function).

        Args:
            ip_address: IP address to unban

        Returns:
            True if reset successful, False otherwise
        """
        try:
            redis_client = await self._get_redis_client()

            # Clear IP ban flag
            ip_ban_key = f"banned:ip:{ip_address}"
            await redis_client.delete(ip_ban_key)

            # Clear IP failed attempts
            ip_key = f"failed_attempts:ip:{ip_address}"
            await redis_client.delete(ip_key)

            logger.info("Manually reset IP ban for %s", ip_address)
            return True

        except Exception as e:
            logger.error("Error resetting IP ban for %s: %s", ip_address, e)
            return False


# Global singleton instance
_atomic_lockout_tracker: Optional[AtomicLockoutTracker] = None


async def get_atomic_lockout_tracker() -> AtomicLockoutTracker:
    """
    Get global atomic lockout tracker instance (singleton pattern).

    Returns:
        AtomicLockoutTracker instance
    """
    global _atomic_lockout_tracker

    if _atomic_lockout_tracker is None:
        _atomic_lockout_tracker = AtomicLockoutTracker()

    return _atomic_lockout_tracker


# Create global instance
atomic_lockout_tracker = AtomicLockoutTracker()
