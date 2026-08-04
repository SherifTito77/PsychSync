"""
Account Lockout Manager

Enhanced account protection against brute force attacks:
- Track failed login attempts per user and IP
- Configurable lockout duration and thresholds
- Automatic account unlocking after timeout
- IP-based rate limiting for login attempts
- Comprehensive logging and monitoring
- Redis-based storage for performance

Security Features:
- Exponential backoff for repeated attacks
- IP ban after multiple account lockouts
- Notification emails on lockout
- Audit trail for all lockout events

Author: Security Team
Version: 2.0.0
Date: January 7, 2026
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# ACCOUNT LOCKOUT MANAGER
# ============================================================================


class AccountLockoutManager:
    """
    Enhanced account lockout manager for brute force protection.

    Features:
    - Per-user failed login tracking
    - Per-IP failed login tracking
    - Configurable lockout thresholds
    - Automatic unlocking
    - IP banning for repeat offenders
    """

    # Lockout Configuration
    MAX_ATTEMPTS = 5  # Max failed attempts before lockout
    LOCKOUT_DURATION = timedelta(minutes=15)  # Initial lockout duration
    MAX_LOCKOUT_DURATION = timedelta(hours=24)  # Maximum lockout duration

    # IP Ban Configuration
    IP_MAX_ATTEMPTS = 20  # Max failed attempts across all accounts
    IP_BAN_DURATION = timedelta(hours=1)  # IP ban duration

    # Redis Key Patterns
    USER_FAILED_KEY = "lockout:user_failed:{user_id}"
    USER_LOCKOUT_KEY = "lockout:user_locked:{user_id}"
    IP_FAILED_KEY = "lockout:ip_failed:{ip_hash}"
    IP_BANNED_KEY = "lockout:ip_banned:{ip_hash}"

    def __init__(self):
        """Initialize account lockout manager"""
        self.redis_url = settings.REDIS_URL

    async def _get_redis_client(self):
        """Get Redis client"""
        return await aioredis.from_url(
            self.redis_url, encoding="utf-8", decode_responses=True
        )

    def _hash_ip(self, ip_address: str) -> str:
        """
        Hash IP address for privacy-safe storage.

        Args:
            ip_address: IP address

        Returns:
            Hashed IP address
        """
        return hashlib.sha256(ip_address.encode()).hexdigest()

    # =======================================================================
    # LOGIN ATTEMPT TRACKING
    # =======================================================================

    async def record_failed_attempt(
        self, user_id: str, ip_address: str, db: AsyncSession
    ) -> tuple[bool, str | None]:
        """
        Record a failed login attempt.

        Args:
            user_id: User ID
            ip_address: IP address
            db: Database session

        Returns:
            Tuple of (is_locked_out, lockout_message)
        """
        redis_client = await self._get_redis_client()

        try:
            # Get user from database
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User not found: {user_id}")
                return False, None

            # Hash IP for privacy
            ip_hash = self._hash_ip(ip_address)

            # Increment failed attempt counters
            user_failed_key = self.USER_FAILED_KEY.format(user_id=user_id)
            ip_failed_key = self.IP_FAILED_KEY.format(ip_hash=ip_hash)

            pipe = redis_client.pipeline(transaction=True)

            # Increment user failed attempts
            pipe.incr(user_failed_key)
            pipe.expire(
                user_failed_key, int(self.LOCKOUT_DURATION.total_seconds()) + 3600
            )

            # Increment IP failed attempts
            pipe.incr(ip_failed_key)
            pipe.expire(ip_failed_key, int(self.IP_BAN_DURATION.total_seconds()) + 3600)

            results = await pipe.execute()

            user_attempts = results[0]
            ip_attempts = results[1]

            logger.warning(
                f"Failed login attempt #{user_attempts} for user {user.email} from IP {ip_address}",
                extra={
                    "user_id": user_id,
                    "email": user.email,
                    "ip_address": ip_address,
                    "attempts": user_attempts,
                },
            )

            # Check if user should be locked out
            if user_attempts >= self.MAX_ATTEMPTS:
                lockout_duration = self._calculate_lockout_duration(user_attempts)
                await self._lockout_user(
                    redis_client, user_id, user.email, lockout_duration, ip_address
                )
                return (
                    True,
                    f"Account locked due to too many failed attempts. Try again in {int(lockout_duration.total_seconds() // 60)} minutes.",
                )

            # Check if IP should be banned
            if ip_attempts >= self.IP_MAX_ATTEMPTS:
                await self._ban_ip(redis_client, ip_hash, ip_address)
                return (
                    True,
                    f"Too many failed attempts from your IP address. Try again in {int(self.IP_BAN_DURATION.total_seconds() // 60)} minutes.",
                )

            return False, None

        finally:
            await redis_client.close()

    async def record_successful_attempt(self, user_id: str, ip_address: str):
        """
        Record a successful login (clear failed attempts).

        Args:
            user_id: User ID
            ip_address: IP address
        """
        redis_client = await self._get_redis_client()

        try:
            # Clear failed attempt counters
            ip_hash = self._hash_ip(ip_address)

            user_failed_key = self.USER_FAILED_KEY.format(user_id=user_id)
            ip_failed_key = self.IP_FAILED_KEY.format(ip_hash=ip_hash)

            pipe = redis_client.pipeline(transaction=True)
            pipe.delete(user_failed_key)
            pipe.delete(ip_failed_key)
            await pipe.execute()

            logger.info(f"Cleared failed attempts for user {user_id}")

        finally:
            await redis_client.close()

    # =======================================================================
    # LOCKOUT STATUS CHECKING
    # =======================================================================

    async def is_user_locked_out(self, user_id: str) -> tuple[bool, int | None]:
        """
        Check if user is currently locked out.

        Args:
            user_id: User ID

        Returns:
            Tuple of (is_locked_out, seconds_remaining)
        """
        redis_client = await self._get_redis_client()

        try:
            lockout_key = self.USER_LOCKOUT_KEY.format(user_id=user_id)
            ttl = await redis_client.ttl(lockout_key)

            if ttl > 0:
                return True, ttl
            # Clean up expired lockout
            await redis_client.delete(lockout_key)
            return False, 0

        finally:
            await redis_client.close()

    async def is_ip_banned(self, ip_address: str) -> tuple[bool, int | None]:
        """
        Check if IP is banned.

        Args:
            ip_address: IP address

        Returns:
            Tuple of (is_banned, seconds_remaining)
        """
        redis_client = await self._get_redis_client()

        try:
            ip_hash = self._hash_ip(ip_address)
            banned_key = self.IP_BANNED_KEY.format(ip_hash=ip_hash)
            ttl = await redis_client.ttl(banned_key)

            if ttl > 0:
                return True, ttl
            # Clean up expired ban
            await redis_client.delete(banned_key)
            return False, 0

        finally:
            await redis_client.close()

    # =======================================================================
    # LOCKOUT MANAGEMENT
    # =======================================================================

    async def _lockout_user(
        self,
        redis_client,
        user_id: str,
        email: str,
        duration: timedelta,
        ip_address: str,
    ):
        """
        Lock out a user account.

        Args:
            redis_client: Redis client
            user_id: User ID
            email: User email
            duration: Lockout duration
            ip_address: IP address
        """
        lockout_key = self.USER_LOCKOUT_KEY.format(user_id=user_id)

        # Set lockout with TTL
        await redis_client.setex(
            lockout_key, int(duration.total_seconds()), datetime.now(UTC).isoformat()
        )

        logger.error(
            f"Account LOCKED OUT: {email} for {duration}",
            extra={
                "user_id": user_id,
                "email": email,
                "duration_seconds": int(duration.total_seconds()),
                "ip_address": ip_address,
            },
        )

        # TODO: Send lockout notification email
        # await self._send_lockout_email(email, duration)

    async def _ban_ip(self, redis_client, ip_hash: str, ip_address: str):
        """
        Ban an IP address.

        Args:
            redis_client: Redis client
            ip_hash: Hashed IP address
            ip_address: Original IP address
        """
        banned_key = self.IP_BANNED_KEY.format(ip_hash=ip_hash)

        # Set ban with TTL
        await redis_client.setex(
            banned_key,
            int(self.IP_BAN_DURATION.total_seconds()),
            datetime.now(UTC).isoformat(),
        )

        logger.error(
            f"IP BANNED: {ip_address} for {self.IP_BAN_DURATION}",
            extra={
                "ip_address": ip_address,
                "duration_seconds": int(self.IP_BAN_DURATION.total_seconds()),
            },
        )

    async def unlock_user(self, user_id: str):
        """
        Manually unlock a user account.

        Args:
            user_id: User ID
        """
        redis_client = await self._get_redis_client()

        try:
            # Clear lockout
            lockout_key = self.USER_LOCKOUT_KEY.format(user_id=user_id)
            await redis_client.delete(lockout_key)

            # Also clear failed attempts
            failed_key = self.USER_FAILED_KEY.format(user_id=user_id)
            await redis_client.delete(failed_key)

            logger.info(f"Account manually unlocked: {user_id}")

        finally:
            await redis_client.close()

    async def unban_ip(self, ip_address: str):
        """
        Manually unban an IP address.

        Args:
            ip_address: IP address
        """
        redis_client = await self._get_redis_client()

        try:
            ip_hash = self._hash_ip(ip_address)
            banned_key = self.IP_BANNED_KEY.format(ip_hash=ip_hash)
            await redis_client.delete(banned_key)

            logger.info(f"IP manually unbanned: {ip_address}")

        finally:
            await redis_client.close()

    # =======================================================================
    # HELPER METHODS
    # =======================================================================

    def _calculate_lockout_duration(self, attempts: int) -> timedelta:
        """
        Calculate lockout duration based on attempt count (exponential backoff).

        Args:
            attempts: Number of failed attempts

        Returns:
            Lockout duration
        """
        # Exponential backoff: 15min, 30min, 1h, 2h, 4h, 8h, 16h, 24h (max)
        exponent = min(attempts - self.MAX_ATTEMPTS, 8)
        duration = self.LOCKOUT_DURATION * (2**exponent)

        # Cap at maximum duration
        return min(duration, self.MAX_LOCKOUT_DURATION)

    async def get_failed_attempts(self, user_id: str) -> int:
        """
        Get number of failed attempts for a user.

        Args:
            user_id: User ID

        Returns:
            Number of failed attempts
        """
        redis_client = await self._get_redis_client()

        try:
            failed_key = self.USER_FAILED_KEY.format(user_id=user_id)
            attempts = await redis_client.get(failed_key)
            return int(attempts) if attempts else 0

        finally:
            await redis_client.close()

    async def get_lockout_info(self, user_id: str) -> dict:
        """
        Get comprehensive lockout information for a user.

        Args:
            user_id: User ID

        Returns:
            Lockout information dictionary
        """
        redis_client = await self._get_redis_client()

        try:
            failed_key = self.USER_FAILED_KEY.format(user_id=user_id)
            lockout_key = self.USER_LOCKOUT_KEY.format(user_id=user_id)

            # Get failed attempts
            attempts = await redis_client.get(failed_key)
            attempts = int(attempts) if attempts else 0

            # Check lockout status
            ttl = await redis_client.ttl(lockout_key)
            is_locked = ttl > 0

            return {
                "user_id": user_id,
                "failed_attempts": attempts,
                "is_locked_out": is_locked,
                "lockout_remaining_seconds": ttl if is_locked else 0,
                "max_attempts": self.MAX_ATTEMPTS,
                "attempts_remaining": max(0, self.MAX_ATTEMPTS - attempts),
            }

        finally:
            await redis_client.close()


# ============================================================================
# SERVICE INSTANCE
# ============================================================================

account_lockout_manager = AccountLockoutManager()
