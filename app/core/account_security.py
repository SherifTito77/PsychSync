# app/core/account_security.py
"""
Account Security Features for PsychSync
Includes account lockout, login attempt tracking, and security monitoring
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import logging
import secrets
from typing import Any

from fastapi import HTTPException

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityEvent(Enum):
    """Security event types for tracking"""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"


class LockoutReason(Enum):
    """Reasons for account lockout"""

    TOO_MANY_ATTEMPTS = "too_many_attempts"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ADMIN_ACTION = "admin_action"
    SECURITY_POLICY = "security_policy"


@dataclass
class LoginAttempt:
    """Represents a login attempt with security context"""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = ""
    user_agent: str = ""
    success: bool = False
    reason: str | None = None
    location: str | None = None


@dataclass
class SecurityEventRecord:
    """Represents a security event record"""

    event_type: SecurityEvent
    user_id: str | None = None
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # low, medium, high, critical


class AccountLockoutManager:
    """
    Manages account lockout policies and security event tracking
    """

    def __init__(self):
        # Lockout policies
        self.max_failed_attempts = getattr(settings, "MAX_LOGIN_ATTEMPTS", 5)
        self.lockout_duration_minutes = getattr(settings, "LOCKOUT_DURATION_MINUTES", 15)
        self.progressive_lockout_enabled = getattr(settings, "PROGRESSIVE_LOCKOUT_ENABLED", True)
        self.suspicious_activity_threshold = getattr(settings, "SUSPICIOUS_ACTIVITY_THRESHOLD", 10)

        # Security tracking
        self.failed_attempts: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.security_events: dict[str, list[SecurityEventRecord]] = defaultdict(list)

        # Cache keys
        self.LOCKOUT_PREFIX = "lockout:"
        self.FAILED_ATTEMPTS_PREFIX = "failed_attempts:"
        self.SECURITY_EVENTS_PREFIX = "security_events:"

        self._lock = asyncio.Lock()

    async def record_login_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str = "",
        user_agent: str = "",
        reason: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Record a login attempt and apply security policies

        Returns:
            Dict with security status and actions taken
        """
        async with self._lock:
            try:
                # Create login attempt record
                attempt = LoginAttempt(
                    ip_address=ip_address, user_agent=user_agent, success=success, reason=reason
                )

                if success:
                    # Successful login - clear failed attempts and record success
                    await self._clear_failed_attempts(email)
                    await self._record_security_event(
                        SecurityEvent.LOGIN_SUCCESS,
                        user_id=user_id or email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={"email": email},
                    )

                    logger.info(
                        f"Successful login for {email}",
                        extra={
                            "user_id": user_id,
                            "ip_address": ip_address,
                            "user_agent": user_agent[:100],  # Truncate for logging
                        },
                    )

                    return {
                        "locked": False,
                        "attempts_remaining": self.max_failed_attempts,
                        "lockout_time_remaining": 0,
                        "security_score": 100,
                    }
                # Failed login - record attempt and check for lockout
                await self._record_failed_attempt(email, attempt)

                # Check if account should be locked
                should_lock, lockout_duration = await self._should_lockout_account(email)

                if should_lock:
                    await self._lock_account(
                        email, lockout_duration, LockoutReason.TOO_MANY_ATTEMPTS
                    )

                    # Record security event
                    await self._record_security_event(
                        SecurityEvent.MULTIPLE_FAILED_LOGINS,
                        user_id=user_id or email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            "email": email,
                            "failed_attempts": await self._get_failed_attempt_count(email),
                            "lockout_duration": lockout_duration,
                        },
                        severity="high",
                    )

                    return {
                        "locked": True,
                        "attempts_remaining": 0,
                        "lockout_time_remaining": lockout_duration,
                        "security_score": 0,
                    }
                attempts_remaining = max(
                    0, self.max_failed_attempts - await self._get_failed_attempt_count(email)
                )

                return {
                    "locked": False,
                    "attempts_remaining": attempts_remaining,
                    "lockout_time_remaining": 0,
                    "security_score": max(
                        0, 100 - (self.max_failed_attempts - attempts_remaining) * 20
                    ),
                }

            except Exception as e:
                logger.error(f"Error recording login attempt for {email}: {e}")
                # Return safe defaults on error
                return {
                    "locked": False,
                    "attempts_remaining": self.max_failed_attempts,
                    "lockout_time_remaining": 0,
                    "security_score": 50,
                }

    async def is_account_locked(self, email: str) -> dict[str, Any]:
        """
        Check if an account is currently locked

        Returns:
            Dict with lockout status and remaining time
        """
        try:
            lockout_key = f"{self.LOCKOUT_PREFIX}{email}"
            lockout_data = await cache_get(lockout_key)

            if not lockout_data:
                return {
                    "locked": False,
                    "lockout_time_remaining": 0,
                    "lockout_reason": None,
                    "locked_at": None,
                }

            # Check if lockout has expired
            locked_at = datetime.fromisoformat(lockout_data["locked_at"])
            lockout_duration = timedelta(minutes=lockout_data["duration_minutes"])

            if datetime.utcnow() > locked_at + lockout_duration:
                # Lockout expired, clear it
                await self._unlock_account(email)
                return {
                    "locked": False,
                    "lockout_time_remaining": 0,
                    "lockout_reason": None,
                    "locked_at": None,
                }

            # Calculate remaining lockout time
            remaining_time = (locked_at + lockout_duration) - datetime.utcnow()
            remaining_seconds = int(remaining_time.total_seconds())

            return {
                "locked": True,
                "lockout_time_remaining": remaining_seconds,
                "lockout_reason": lockout_data["reason"],
                "locked_at": locked_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error checking account lockout for {email}: {e}")
            return {
                "locked": False,
                "lockout_time_remaining": 0,
                "lockout_reason": None,
                "locked_at": None,
            }

    async def get_failed_attempts(self, email: str) -> list[LoginAttempt]:
        """
        Get recent failed login attempts for an account
        """
        try:
            cache_key = f"{self.FAILED_ATTEMPTS_PREFIX}{email}"
            attempts_data = await cache_get(cache_key) or []

            attempts = []
            for attempt_data in attempts_data[-10:]:  # Return last 10 attempts
                attempt = LoginAttempt(
                    timestamp=datetime.fromisoformat(attempt_data["timestamp"]),
                    ip_address=attempt_data.get("ip_address", ""),
                    user_agent=attempt_data.get("user_agent", ""),
                    success=False,
                    reason=attempt_data.get("reason"),
                )
                attempts.append(attempt)

            return attempts

        except Exception as e:
            logger.error(f"Error getting failed attempts for {email}: {e}")
            return []

    async def get_security_events(
        self,
        email: str | None = None,
        event_types: list[SecurityEvent] | None = None,
        hours: int = 24,
    ) -> list[SecurityEventRecord]:
        """
        Get security events for analysis
        """
        try:
            events = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # Get events from cache (in production, this would be from a database)
            cache_key = f"{self.SECURITY_EVENTS_PREFIX}{email or 'global'}"
            events_data = await cache_get(cache_key) or []

            for event_data in events_data:
                event_timestamp = datetime.fromisoformat(event_data["timestamp"])

                if event_timestamp < cutoff_time:
                    continue

                if event_types and SecurityEvent(event_data["event_type"]) not in event_types:
                    continue

                event = SecurityEventRecord(
                    event_type=SecurityEvent(event_data["event_type"]),
                    user_id=event_data.get("user_id"),
                    ip_address=event_data.get("ip_address", ""),
                    user_agent=event_data.get("user_agent", ""),
                    timestamp=event_timestamp,
                    metadata=event_data.get("metadata", {}),
                    severity=event_data.get("severity", "medium"),
                )
                events.append(event)

            return sorted(events, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            logger.error(f"Error getting security events: {e}")
            return []

    async def unlock_account(self, email: str, reason: str = "Manual unlock"):
        """
        Manually unlock an account
        """
        try:
            await self._unlock_account(email)
            await self._record_security_event(
                SecurityEvent.ACCOUNT_UNLOCKED, user_id=email, metadata={"reason": reason}
            )

            logger.info(f"Account unlocked: {email}", extra={"reason": reason})

        except Exception as e:
            logger.error(f"Error unlocking account {email}: {e}")

    async def lock_account_manually(
        self, email: str, duration_minutes: int, reason: str = "Admin action"
    ):
        """
        Manually lock an account
        """
        try:
            await self._lock_account(email, duration_minutes, LockoutReason.ADMIN_ACTION)
            await self._record_security_event(
                SecurityEvent.ACCOUNT_LOCKED,
                user_id=email,
                metadata={"reason": reason, "duration_minutes": duration_minutes},
                severity="high",
            )

            logger.info(
                f"Account locked manually: {email}",
                extra={"reason": reason, "duration_minutes": duration_minutes},
            )

        except Exception as e:
            logger.error(f"Error manually locking account {email}: {e}")

    async def _record_failed_attempt(self, email: str, attempt: LoginAttempt):
        """Record a failed login attempt"""
        try:
            cache_key = f"{self.FAILED_ATTEMPTS_PREFIX}{email}"
            existing_attempts = await cache_get(cache_key) or []

            # Add new attempt
            attempt_data = {
                "timestamp": attempt.timestamp.isoformat(),
                "ip_address": attempt.ip_address,
                "user_agent": attempt.user_agent,
                "reason": attempt.reason,
            }
            existing_attempts.append(attempt_data)

            # Keep only recent attempts (last 100)
            if len(existing_attempts) > 100:
                existing_attempts = existing_attempts[-100:]

            # Store with expiration
            await cache_set(cache_key, existing_attempts, expire_seconds=86400)  # 24 hours

        except Exception as e:
            logger.error(f"Error recording failed attempt for {email}: {e}")

    async def _clear_failed_attempts(self, email: str):
        """Clear failed login attempts for successful login"""
        try:
            cache_key = f"{self.FAILED_ATTEMPTS_PREFIX}{email}"
            await cache_delete(cache_key)

        except Exception as e:
            logger.error(f"Error clearing failed attempts for {email}: {e}")

    async def _get_failed_attempt_count(self, email: str) -> int:
        """Get current failed attempt count"""
        try:
            cache_key = f"{self.FAILED_ATTEMPTS_PREFIX}{email}"
            attempts = await cache_get(cache_key) or []
            return len(attempts)

        except Exception as e:
            logger.error(f"Error getting failed attempt count for {email}: {e}")
            return 0

    async def _should_lockout_account(self, email: str) -> tuple[bool, int]:
        """Determine if account should be locked and for how long"""
        failed_count = await self._get_failed_attempt_count(email)

        if failed_count < self.max_failed_attempts:
            return False, 0

        # Progressive lockout duration
        if self.progressive_lockout_enabled:
            excess_attempts = failed_count - self.max_failed_attempts
            progressive_multiplier = 1 + (excess_attempts * 0.5)
            duration = int(self.lockout_duration_minutes * progressive_multiplier)
            duration = min(duration, 1440)  # Max 24 hours
        else:
            duration = self.lockout_duration_minutes

        return True, duration

    async def _lock_account(self, email: str, duration_minutes: int, reason: LockoutReason):
        """Lock an account"""
        try:
            lockout_key = f"{self.LOCKOUT_PREFIX}{email}"
            lockout_data = {
                "locked_at": datetime.utcnow().isoformat(),
                "duration_minutes": duration_minutes,
                "reason": reason.value,
            }

            # Store lockout with expiration
            await cache_set(lockout_key, lockout_data, expire_seconds=duration_minutes * 60)

        except Exception as e:
            logger.error(f"Error locking account {email}: {e}")

    async def _unlock_account(self, email: str):
        """Unlock an account"""
        try:
            lockout_key = f"{self.LOCKOUT_PREFIX}{email}"
            await cache_delete(lockout_key)

        except Exception as e:
            logger.error(f"Error unlocking account {email}: {e}")

    async def _record_security_event(
        self,
        event_type: SecurityEvent,
        user_id: str | None,
        ip_address: str = "",
        user_agent: str = "",
        metadata: dict[str, Any] | None = None,
        severity: str = "medium",
    ):
        """Record a security event"""
        try:
            event = SecurityEventRecord(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
                severity=severity,
            )

            # Store in cache (in production, this would be in a database)
            cache_key = f"{self.SECURITY_EVENTS_PREFIX}{user_id or 'global'}"
            existing_events = await cache_get(cache_key) or []

            event_data = {
                "event_type": event.event_type.value,
                "user_id": event.user_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "timestamp": event.timestamp.isoformat(),
                "metadata": event.metadata,
                "severity": event.severity,
            }

            existing_events.append(event_data)

            # Keep only recent events (last 1000)
            if len(existing_events) > 1000:
                existing_events = existing_events[-1000:]

            # Store with longer expiration for security events
            await cache_set(cache_key, existing_events, expire_seconds=86400 * 30)  # 30 days

        except Exception as e:
            logger.error(f"Error recording security event: {e}")

    async def generate_password_reset_token(
        self, email: str, ip_address: str = "system", user_agent: str = "password_reset"
    ) -> str:
        """
        Generate secure password reset token

        Args:
            email: User email address
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            Secure password reset token
        """
        # Check rate limiting for password reset requests
        await self._check_password_reset_rate_limit(email, ip_address)

        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Create token metadata
        token_data = {
            "email": email.lower(),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=3600)).isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "token_hash": token_hash,
            "uses": 0,
            "max_uses": 1,
        }

        # Store in cache with expiration
        try:
            # Store new token
            await cache_set(f"reset_token:{token_hash}", token_data, expire_seconds=3600)

            # Log security event
            await self._record_security_event(
                SecurityEvent.LOGIN_FAILED,  # Using existing enum
                user_id=email,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "token_hash": token_hash[:8] + "...",  # Partial hash for logging
                    "expires_in": 3600,
                },
                severity="medium",
            )

            logger.info(
                f"Password reset token generated for email: {email[:10]}... from IP: {ip_address}"
            )

            return token

        except Exception as e:
            logger.error(f"Failed to generate password reset token: {e}")
            raise RuntimeError("Token generation failed")

    async def verify_password_reset_token(
        self, token: str, email: str, ip_address: str = "system", user_agent: str = "password_reset"
    ) -> bool:
        """
        Verify password reset token

        Args:
            token: Password reset token
            email: User email address
            ip_address: Request IP address
            user_agent: User agent string

        Returns:
            True if token is valid and belongs to email
        """
        try:
            # Calculate token hash
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Get token data from cache
            token_data_json = await cache_get(f"reset_token:{token_hash}")
            if not token_data_json:
                await self._record_security_event(
                    SecurityEvent.LOGIN_FAILED,
                    user_id=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"reason": "token_not_found"},
                    severity="high",
                )
                return False

            token_data = json.loads(token_data_json)

            # Validate token data
            if token_data["email"] != email.lower():
                await self._record_security_event(
                    SecurityEvent.LOGIN_FAILED,
                    user_id=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"reason": "email_mismatch", "token_email": token_data["email"]},
                    severity="high",
                )
                return False

            # Check if token has expired
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            if datetime.utcnow() > expires_at:
                await self._record_security_event(
                    SecurityEvent.LOGIN_FAILED,
                    user_id=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"reason": "token_expired"},
                    severity="medium",
                )
                return False

            # Check token usage count
            if token_data["uses"] >= token_data["max_uses"]:
                await self._record_security_event(
                    SecurityEvent.LOGIN_FAILED,
                    user_id=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={"reason": "token_already_used"},
                    severity="high",
                )
                return False

            # Mark token as used
            token_data["uses"] += 1
            token_data["used_at"] = datetime.utcnow().isoformat()
            token_data["used_ip"] = ip_address
            token_data["used_user_agent"] = user_agent

            # Update token data
            await cache_set(f"reset_token:{token_hash}", token_data, expire_seconds=3600)

            # Log successful verification
            await self._record_security_event(
                SecurityEvent.LOGIN_SUCCESS,
                user_id=email,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "token_uses": token_data["uses"],
                    "remaining_uses": token_data["max_uses"] - token_data["uses"],
                },
                severity="low",
            )

            logger.info(
                f"Password reset token verified for email: {email[:10]}... from IP: {ip_address}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to verify password reset token: {e}")
            return False

    async def revoke_reset_token(self, token: str) -> bool:
        """
        Revoke password reset token

        Args:
            token: Token to revoke

        Returns:
            True if token was found and revoked
        """
        try:
            # Calculate token hash
            token_hash = hashlib.sha256(token.encode()).hexdigest()

            # Delete token from cache
            result = await cache_delete(f"reset_token:{token_hash}")
            logger.info("Password reset token revoked")

            return result is not None

        except Exception as e:
            logger.error(f"Failed to revoke password reset token: {e}")
            return False

    async def _check_password_reset_rate_limit(self, email: str, ip_address: str):
        """
        Check rate limiting for password reset requests
        """
        rate_limit_key = f"password_reset_limit:{email.lower()}"
        ip_limit_key = f"password_reset_limit_ip:{ip_address}"

        try:
            # Check per-email limit (3 requests per hour)
            email_count = await cache_get(rate_limit_key) or 0
            if email_count and int(email_count) >= 3:
                raise HTTPException(
                    status_code=429,
                    detail="Too many password reset requests. Please try again later.",
                    headers={"Retry-After": "3600"},
                )

            # Check per-IP limit (5 requests per hour)
            ip_count = await cache_get(ip_limit_key) or 0
            if ip_count and int(ip_count) >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Too many password reset requests from this IP. Please try again later.",
                    headers={"Retry-After": "3600"},
                )

            # Increment counters with expiration
            current_email_count = await cache_get(rate_limit_key) or 0
            await cache_set(rate_limit_key, int(current_email_count) + 1, expire_seconds=3600)

            current_ip_count = await cache_get(ip_limit_key) or 0
            await cache_set(ip_limit_key, int(current_ip_count) + 1, expire_seconds=3600)

        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(f"Failed to check password reset rate limit: {e}")


# Global instance
account_security_manager = AccountLockoutManager()
