"""
CAPTCHA Service for Suspicious Registration Attempts

Implements CAPTCHA verification to prevent:
- Automated bot registrations
- Credential stuffing attacks
- Mass account creation attacks

Security Features:
- Integration with Google reCAPTCHA v3
- Suspicious activity detection
- Adaptive CAPTCHA triggering
- Score-based verification
- IP-based suspicious tracking
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

import httpx

try:
    from redis.asyncio import redis as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CaptchaAction(str, Enum):
    """CAPTCHA action types"""

    REGISTER = "register"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


class SuspicionLevel(str, Enum):
    """Suspicion level for CAPTCHA triggering"""

    LOW = "low"  # No CAPTCHA required
    MEDIUM = "medium"  # v3 invisible CAPTCHA
    HIGH = "high"  # v2 checkbox CAPTCHA
    CRITICAL = "critical"  # v2 challenge CAPTCHA


class CaptchaVerificationResult:
    """CAPTCHA verification result"""

    def __init__(self, success: bool, score: float = 0.0, error: str = ""):
        self.success = success
        self.score = score  # 0.0 to 1.0, higher is better
        self.error = error
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "score": self.score,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class CaptchaService:
    """
    CAPTCHA verification service with Redis-backed suspicious activity tracking
    """

    # CAPTCHA thresholds
    V3_THRESHOLD_LOW = 0.3  # Allow most human-like interactions
    V3_THRESHOLD_MEDIUM = 0.5  # Require for moderate suspicion
    V3_THRESHOLD_HIGH = 0.7  # Stricter for high suspicion

    # Suspicious activity thresholds
    FAILED_ATTEMPTS_THRESHOLD = 3  # Trigger after N failed attempts
    IP_REGISTRATION_THRESHOLD = 5  # Max registrations per hour from IP
    SUSPICIOUS_USER_AGENTS = [
        "bot",
        "crawler",
        "spider",
        "scraper",
        "curl",
        "wget",
        "python",
        "requests",
    ]

    def __init__(
        self,
        secret_key: Optional[str] = None,
        redis_client=None,
        enabled: bool = True,
    ):
        """
        Initialize CAPTCHA service

        Args:
            secret_key: Google reCAPTCHA secret key
            redis_client: Redis client for activity tracking
            enabled: Whether CAPTCHA is enabled
        """
        self.secret_key = secret_key
        self.redis_client = redis_client
        self.enabled = enabled

    async def _get_redis_client(self):
        """Get or create Redis client"""
        if self.redis_client is None and REDIS_AVAILABLE:
            try:
                self.redis_client = await aioredis.from_url(
                    "redis://localhost:6379",
                    decode_responses=True,
                    health_check_interval=30,
                )
                logger.info("Connected to Redis for CAPTCHA service")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        return self.redis_client

    def _is_enabled(self) -> bool:
        """Check if CAPTCHA service is enabled"""
        return self.enabled and self.secret_key is not None

    async def verify_v3(
        self,
        token: str,
        remote_ip: Optional[str] = None,
        action: Optional[CaptchaAction] = None,
    ) -> CaptchaVerificationResult:
        """
        Verify reCAPTCHA v3 token

        Args:
            token: reCAPTCHA response token
            remote_ip: User's IP address
            action: Expected action type

        Returns:
            CaptchaVerificationResult with success status
        """
        if not self._is_enabled():
            logger.warning("CAPTCHA verification requested but service is disabled")
            return CaptchaVerificationResult(
                success=True, score=1.0, error="CAPTCHA disabled"
            )

        if not token:
            logger.warning("CAPTCHA verification failed: No token provided")
            return CaptchaVerificationResult(
                success=False, score=0.0, error="No CAPTCHA token provided"
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data={
                        "secret": self.secret_key,
                        "response": token,
                        "remoteip": remote_ip,
                    },
                )

                result = response.json()

                if not result.get("success", False):
                    error_codes = result.get("error-codes", [])
                    logger.warning(
                        f"CAPTCHA verification failed: {error_codes}",
                        extra={
                            "remote_ip": remote_ip,
                            "action": action.value if action else None,
                        },
                    )
                    return CaptchaVerificationResult(
                        success=False,
                        score=0.0,
                        error=f"CAPTCHA verification failed: {', '.join(error_codes)}",
                    )

                # Check action match (if specified)
                if action:
                    response_action = result.get("action")
                    if response_action != action.value:
                        logger.warning(
                            f"CAPTCHA action mismatch: expected {action.value}, got {response_action}",
                            extra={"remote_ip": remote_ip},
                        )
                        return CaptchaVerificationResult(
                            success=False,
                            score=result.get("score", 0.0),
                            error="CAPTCHA action mismatch",
                        )

                score = result.get("score", 0.0)

                logger.info(
                    f"CAPTCHA verification successful",
                    extra={
                        "remote_ip": remote_ip,
                        "action": action.value if action else None,
                        "score": score,
                        "hostname": result.get("hostname"),
                    },
                )

                return CaptchaVerificationResult(success=True, score=score, error="")

        except httpx.TimeoutError:
            logger.error("CAPTCHA verification timeout")
            return CaptchaVerificationResult(
                success=False, score=0.0, error="CAPTCHA verification timeout"
            )
        except Exception as e:
            logger.error(f"CAPTCHA verification error: {e}")
            return CaptchaVerificationResult(success=False, score=0.0, error=str(e))

    async def get_suspicion_level(
        self,
        ip: str,
        user_agent: Optional[str] = None,
        email_domain: Optional[str] = None,
    ) -> SuspicionLevel:
        """
        Determine suspicion level for an IP/user

        Args:
            ip: User's IP address
            user_agent: User-Agent string
            email_domain: Email domain being registered

        Returns:
            SuspicionLevel
        """
        if not self._is_enabled():
            return SuspicionLevel.LOW

        redis_client = await self._get_redis_client()
        if not redis_client:
            return SuspicionLevel.LOW

        suspicion_score = 0

        # Check for suspicious user agent
        if user_agent:
            user_agent_lower = user_agent.lower()
            if any(bot in user_agent_lower for bot in self.SUSPICIOUS_USER_AGENTS):
                logger.warning(
                    f"Suspicious user agent detected: {user_agent[:100]}",
                    extra={"ip": ip},
                )
                suspicion_score += 3

        # Check for failed attempts
        failed_attempts_key = f"captcha:failed_attempts:{ip}"
        failed_attempts = await redis_client.get(failed_attempts_key)
        if failed_attempts:
            failed_count = int(failed_attempts)
            if failed_count >= self.FAILED_ATTEMPTS_THRESHOLD:
                logger.warning(
                    f"Multiple failed CAPTCHA attempts from IP: {ip}",
                    extra={"failed_attempts": failed_count, "ip": ip},
                )
                suspicion_score += 2 * failed_count

        # Check registration rate
        registration_key = (
            f"captcha:registrations:{ip}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        )
        registration_count = await redis_client.get(registration_key)
        if registration_count:
            reg_count = int(registration_count)
            if reg_count >= self.IP_REGISTRATION_THRESHOLD:
                logger.warning(
                    f"High registration rate from IP: {ip}",
                    extra={"registrations": reg_count, "ip": ip},
                )
                suspicion_score += reg_count

        # Check for disposable email domains
        if email_domain and self._is_disposable_email_domain(email_domain):
            logger.warning(
                f"Disposable email domain detected: {email_domain}", extra={"ip": ip}
            )
            suspicion_score += 2

        # Determine suspicion level
        if suspicion_score >= 10:
            return SuspicionLevel.CRITICAL
        elif suspicion_score >= 6:
            return SuspicionLevel.HIGH
        elif suspicion_score >= 3:
            return SuspicionLevel.MEDIUM
        else:
            return SuspicionLevel.LOW

    async def record_failed_attempt(self, ip: str, reason: str = ""):
        """
        Record a failed CAPTCHA attempt

        Args:
            ip: User's IP address
            reason: Reason for failure
        """
        redis_client = await self._get_redis_client()
        if not redis_client:
            return

        key = f"captcha:failed_attempts:{ip}"

        try:
            await redis_client.incr(key)
            await redis_client.expire(key, 3600)  # 1 hour

            failed_count = await redis_client.get(key)
            logger.warning(
                f"Failed CAPTCHA attempt recorded: {ip}",
                extra={
                    "ip": ip,
                    "reason": reason,
                    "total_failed": int(failed_count) if failed_count else 0,
                },
            )
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")

    async def record_successful_registration(self, ip: str):
        """
        Record a successful registration

        Args:
            ip: User's IP address
        """
        redis_client = await self._get_redis_client()
        if not redis_client:
            return

        key = f"captcha:registrations:{ip}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"

        try:
            await redis_client.incr(key)
            await redis_client.expire(key, 3600)  # 1 hour
        except Exception as e:
            logger.error(f"Failed to record registration: {e}")

    async def clear_failed_attempts(self, ip: str):
        """
        Clear failed attempts for an IP (e.g., after successful registration)

        Args:
            ip: User's IP address
        """
        redis_client = await self._get_redis_client()
        if not redis_client:
            return

        key = f"captcha:failed_attempts:{ip}"

        try:
            await redis_client.delete(key)
            logger.debug(f"Cleared failed attempts for IP: {ip}")
        except Exception as e:
            logger.error(f"Failed to clear failed attempts: {e}")

    def _is_disposable_email_domain(self, domain: str) -> bool:
        """
        Check if email domain is disposable

        Args:
            domain: Email domain

        Returns:
            True if disposable, False otherwise
        """
        # Common disposable email domains
        disposable_domains = {
            "tempmail.com",
            "guerrillamail.com",
            "mailinator.com",
            "10minutemail.com",
            "yopmail.com",
            "trashmail.com",
            "throwawaymail.com",
            "getairmail.com",
            "maildrop.cc",
        }

        return domain.lower() in disposable_domains

    def requires_captcha(self, suspicion_level: SuspicionLevel) -> bool:
        """
        Determine if CAPTCHA is required based on suspicion level

        Args:
            suspicion_level: Current suspicion level

        Returns:
            True if CAPTCHA is required
        """
        return suspicion_level in [
            SuspicionLevel.MEDIUM,
            SuspicionLevel.HIGH,
            SuspicionLevel.CRITICAL,
        ]

    def get_captcha_threshold(self, suspicion_level: SuspicionLevel) -> float:
        """
        Get CAPTCHA score threshold based on suspicion level

        Args:
            suspicion_level: Current suspicion level

        Returns:
            Score threshold (0.0 to 1.0)
        """
        thresholds = {
            SuspicionLevel.LOW: 0.0,  # No CAPTCHA required
            SuspicionLevel.MEDIUM: self.V3_THRESHOLD_MEDIUM,
            SuspicionLevel.HIGH: self.V3_THRESHOLD_HIGH,
            SuspicionLevel.CRITICAL: 1.0,  # Always fail
        }

        return thresholds.get(suspicion_level, 0.3)


# Global instance
captcha_service = CaptchaService()


def verify_captcha(
    token: str,
    remote_ip: Optional[str] = None,
    action: Optional[CaptchaAction] = None,
) -> CaptchaVerificationResult:
    """
    Synchronous wrapper for CAPTCHA verification

    Args:
        token: reCAPTCHA response token
        remote_ip: User's IP address
        action: Expected action type

    Returns:
        CaptchaVerificationResult with success status
    """
    # For non-async contexts, create a sync wrapper
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If in async context, create a new event loop
            import threading

            result_container = []

            def run_verification():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(
                    captcha_service.verify_v3(token, remote_ip, action)
                )
                result_container.append(result)
                new_loop.close()

            thread = threading.Thread(target=run_verification)
            thread.start()
            thread.join(timeout=5)
            return (
                result_container[0]
                if result_container
                else CaptchaVerificationResult(
                    success=False, score=0.0, error="Timeout"
                )
            )
        else:
            return loop.run_until_complete(
                captcha_service.verify_v3(token, remote_ip, action)
            )
    except Exception as e:
        logger.error(f"Synchronous CAPTCHA verification error: {e}")
        return CaptchaVerificationResult(success=False, score=0.0, error=str(e))
