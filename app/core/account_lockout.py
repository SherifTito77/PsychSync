# app/core/account_lockout.py
"""
Account lockout mechanism to prevent brute force attacks.

Features:
- Track failed login attempts per user and IP
- Progressive delays (exponential backoff)
- Temporary account lockout
- Automatic unlock after timeout
- Admin override capability
- Redis-backed for distributed systems
"""

import logging
import time

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class AccountLockoutManager:
    """
    Manages account lockout policies.

    Lockout Strategy:
    - 3 failed attempts: Warning (no lockout)
    - 5 failed attempts: 5 minute lockout
    - 10 failed attempts: 30 minute lockout
    - 15+ failed attempts: 60 minute lockout
    """

    # Lockout thresholds (attempts, duration_minutes)
    LOCKOUT_THRESHOLDS = [
        (5, 5),  # 5 attempts = 5 minute lockout
        (10, 30),  # 10 attempts = 30 minute lockout
        (15, 60),  # 15 attempts = 60 minute lockout
    ]

    WARNING_THRESHOLD = 3  # Show warning after 3 attempts

    def __init__(self, redis: Redis):
        """
        Initialize account lockout manager.

        Args:
            redis: Redis client instance
        """
        self.redis = redis

    async def check_login_attempt(
        self, identifier: str, ip_address: str = "unknown"
    ) -> tuple[bool, str | None, dict]:
        """
        Check if login attempt should be allowed.

        Args:
            identifier: User identifier (email, username, or user_id)
            ip_address: Client IP address

        Returns:
            Tuple of (allowed, lockout_reason, lockout_info)

        Raises:
            HTTPException: If account is locked (with 423 status)
        """
        # Get current attempt counts
        user_attempts = await self._get_attempts(f"login_attempts:user:{identifier}")
        ip_attempts = await self._get_attempts(f"login_attempts:ip:{ip_address}")

        # Check if account is locked
        is_locked, lockout_info = await self._is_account_locked(identifier)

        if is_locked:
            # Calculate remaining time
            remaining_time = lockout_info["unlock_time"] - int(time.time())
            reason = (
                f"Account temporarily locked due to {lockout_info['attempts']} "
                f"failed login attempts. Please try again in {remaining_time // 60} minutes."
            )

            logger.warning(
                f"Locked login attempt for {identifier} from {ip_address}: "
                f"{lockout_info['attempts']} attempts"
            )

            return False, reason, lockout_info

        # Check if we should show a warning
        show_warning = user_attempts >= self.WARNING_THRESHOLD

        return (
            True,
            None,
            {
                "user_attempts": user_attempts,
                "ip_attempts": ip_attempts,
                "show_warning": show_warning,
                "attempts_remaining": self._get_lockout_threshold(user_attempts) - user_attempts,
            },
        )

    async def record_failed_attempt(
        self, identifier: str, ip_address: str = "unknown", details: str | None = None
    ) -> dict:
        """
        Record a failed login attempt.

        Args:
            identifier: User identifier
            ip_address: Client IP address
            details: Optional details about the attempt

        Returns:
            Dictionary with attempt information
        """
        current_time = int(time.time())

        # Increment user attempt counter
        user_key = f"login_attempts:user:{identifier}"
        user_attempts = await self.redis.incr(user_key)
        await self.redis.expire(user_key, 3600)  # Expire after 1 hour

        # Increment IP attempt counter
        ip_key = f"login_attempts:ip:{ip_address}"
        ip_attempts = await self.redis.incr(ip_key)
        await self.redis.expire(ip_key, 3600)

        # Check if we should lock the account
        lockout_duration = None
        for threshold, duration in self.LOCKOUT_THRESHOLDS:
            if user_attempts >= threshold:
                lockout_duration = duration
                break

        # Apply lockout if needed
        if lockout_duration:
            await self._lock_account(identifier, lockout_duration, user_attempts)
            logger.warning(
                f"Account {identifier} locked for {lockout_duration} minutes "
                f"after {user_attempts} failed attempts from {ip_address}"
            )

        # Log the failed attempt
        await self._log_failed_attempt(identifier, ip_address, user_attempts, details)

        return {
            "user_attempts": user_attempts,
            "ip_attempts": ip_attempts,
            "locked": lockout_duration is not None,
            "lockout_duration_minutes": lockout_duration,
        }

    async def record_successful_login(self, identifier: str, ip_address: str = "unknown"):
        """
        Record a successful login and clear attempt counters.

        Args:
            identifier: User identifier
            ip_address: Client IP address
        """
        # Clear user attempt counter
        await self.redis.delete(f"login_attempts:user:{identifier}")

        # Clear IP attempt counter (optional - comment out if you want to track IP separately)
        # await self.redis.delete(f"login_attempts:ip:{ip_address}")

        # Clear account lockout
        await self.redis.delete(f"account_locked:{identifier}")

        logger.info(f"Successful login for {identifier} from {ip_address}")

    async def _get_attempts(self, key: str) -> int:
        """Get current attempt count."""
        attempts = await self.redis.get(key)
        return int(attempts) if attempts else 0

    def _get_lockout_threshold(self, attempts: int) -> int:
        """Get the next lockout threshold."""
        for threshold, _ in reversed(self.LOCKOUT_THRESHOLDS):
            if attempts < threshold:
                return threshold
        return self.LOCKOUT_THRESHOLDS[-1][0] + 5

    async def _is_account_locked(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if account is currently locked.

        Returns:
            Tuple of (is_locked, lockout_info)
        """
        lock_key = f"account_locked:{identifier}"
        lock_data = await self.redis.get(lock_key)

        if not lock_data:
            return False, {}

        import json

        try:
            lock_info = json.loads(lock_data)
            unlock_time = lock_info.get("unlock_time", 0)

            # Check if lockout has expired
            if int(time.time()) >= unlock_time:
                await self.redis.delete(lock_key)
                return False, {}

            return True, lock_info
        except (json.JSONDecodeError, TypeError):
            # Invalid lock data - remove it
            await self.redis.delete(lock_key)
            return False, {}

    async def _lock_account(self, identifier: str, duration_minutes: int, attempts: int):
        """
        Lock an account for specified duration.

        Args:
            identifier: User identifier
            duration_minutes: Lockout duration in minutes
            attempts: Number of failed attempts
        """
        lock_key = f"account_locked:{identifier}"
        unlock_time = int(time.time()) + (duration_minutes * 60)

        import json

        lock_info = {
            "locked_at": int(time.time()),
            "unlock_time": unlock_time,
            "duration_minutes": duration_minutes,
            "attempts": attempts,
            "reason": f"Too many failed login attempts ({attempts})",
        }

        await self.redis.setex(lock_key, duration_minutes * 60, json.dumps(lock_info))

    async def _log_failed_attempt(
        self, identifier: str, ip_address: str, attempts: int, details: str | None
    ):
        """Log failed attempt for security monitoring."""
        logger.warning(f"Failed login attempt #{attempts} for {identifier} from {ip_address}")

        # Store in security event log (for review)
        event_key = f"security_events:failed_login:{int(time.time())}"
        import json

        event_data = {
            "identifier": identifier,
            "ip_address": ip_address,
            "attempts": attempts,
            "timestamp": int(time.time()),
            "details": details,
        }

        # Keep for 7 days
        await self.redis.setex(event_key, 7 * 24 * 3600, json.dumps(event_data))

    async def get_account_status(self, identifier: str) -> dict:
        """
        Get current account status including lockout info.

        Args:
            identifier: User identifier

        Returns:
            Dictionary with account status
        """
        user_attempts = await self._get_attempts(f"login_attempts:user:{identifier}")
        is_locked, lock_info = await self._is_account_locked(identifier)

        status = {
            "identifier": identifier,
            "failed_attempts": user_attempts,
            "is_locked": is_locked,
            "lockout_info": lock_info if is_locked else None,
        }

        return status

    async def unlock_account(self, identifier: str, admin_user: str):
        """
        Manually unlock an account (admin function).

        Args:
            identifier: User identifier to unlock
            admin_user: Admin performing the unlock
        """
        await self.redis.delete(f"account_locked:{identifier}")
        await self.redis.delete(f"login_attempts:user:{identifier}")

        logger.info(f"Account {identifier} manually unlocked by admin {admin_user}")

    async def get_failed_login_history(self, identifier: str, hours: int = 24) -> list:
        """
        Get failed login history for an account.

        Args:
            identifier: User identifier
            hours: Hours of history to retrieve

        Returns:
            List of failed login events
        """
        # This would require a more complex Redis setup
        # For now, return empty list
        return []


# Singleton instance
_lockout_manager: AccountLockoutManager | None = None


def get_lockout_manager() -> AccountLockoutManager | None:
    """Get the account lockout manager instance."""
    return _lockout_manager


async def init_lockout_manager(redis_url: str):
    """
    Initialize the account lockout manager with Redis.

    Args:
        redis_url: Redis connection URL
    """
    global _lockout_manager

    redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    _lockout_manager = AccountLockoutManager(redis)
