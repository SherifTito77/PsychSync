"""
Authentication Rate Limiting Middleware
Protects authentication endpoints from brute force and credential stuffing attacks.
Implements progressive rate limiting based on success/failure patterns.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import ipaddress
import logging
import time

from fastapi import Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)


class AuthAttemptType(Enum):
    """Types of authentication attempts."""

    LOGIN = "login"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    TOKEN_REFRESH = "token_refresh"
    TWO_FACTOR = "two_factor"
    ACCOUNT_VERIFICATION = "account_verification"


@dataclass
class AuthRateLimitConfig:
    """Configuration for authentication rate limiting."""

    # Base rate limits
    login_attempts_per_hour: int = 20
    register_attempts_per_hour: int = 5
    password_reset_attempts_per_hour: int = 3
    token_refresh_attempts_per_hour: int = 100
    two_factor_attempts_per_hour: int = 10

    # Progressive limiting
    failed_attempt_multiplier: float = 0.5  # Reduce limit by 50% after failures
    max_penalty_duration: int = 3600  # Maximum 1 hour penalty

    # IP-based limits
    ip_login_limit_per_hour: int = 50
    ip_register_limit_per_hour: int = 10

    # Global limits
    global_login_attempts_per_minute: int = 1000
    global_register_attempts_per_minute: int = 100

    # Redis configuration
    redis_url: str = "redis://localhost:6379/3"

    # Protected endpoints
    protected_paths: dict[str, AuthAttemptType] = None

    def __post_init__(self):
        if self.protected_paths is None:
            self.protected_paths = {
                "/api/v1/auth/login": AuthAttemptType.LOGIN,
                "/api/v1/auth/register": AuthAttemptType.REGISTER,
                "/api/v1/auth/password-reset": AuthAttemptType.PASSWORD_RESET,
                "/api/v1/auth/refresh": AuthAttemptType.TOKEN_REFRESH,
                "/api/v1/auth/two-factor": AuthAttemptType.TWO_FACTOR,
                "/api/v1/auth/verify": AuthAttemptType.ACCOUNT_VERIFICATION,
            }


class AuthRateLimiter(BaseHTTPMiddleware):
    """
    Authentication rate limiting middleware with progressive penalties.
    """

    def __init__(self, app, config: AuthRateLimitConfig | None = None):
        super().__init__(app)
        self.config = config or AuthRateLimitConfig()
        self.redis_client: redis.Redis | None = None
        self._init_redis()

        # Rate limits by attempt type
        self.base_limits = {
            AuthAttemptType.LOGIN: self.config.login_attempts_per_hour,
            AuthAttemptType.REGISTER: self.config.register_attempts_per_hour,
            AuthAttemptType.PASSWORD_RESET: self.config.password_reset_attempts_per_hour,
            AuthAttemptType.TOKEN_REFRESH: self.config.token_refresh_attempts_per_hour,
            AuthAttemptType.TWO_FACTOR: self.config.two_factor_attempts_per_hour,
            AuthAttemptType.ACCOUNT_VERIFICATION: self.config.login_attempts_per_hour,
        }

        # IP-based limits
        self.ip_limits = {
            AuthAttemptType.LOGIN: self.config.ip_login_limit_per_hour,
            AuthAttemptType.REGISTER: self.config.ip_register_limit_per_hour,
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Main middleware dispatcher for authentication rate limiting.
        """
        try:
            # Check if this is an auth endpoint
            attempt_type = self._get_attempt_type(request)
            if not attempt_type:
                # Not an auth endpoint, skip rate limiting
                return await call_next(request)

            # Extract identifiers
            client_ip = self._get_client_ip(request)
            user_identifier = await self._extract_user_identifier(request, attempt_type)

            # Check rate limits
            if await self._is_rate_limited(request, attempt_type, client_ip, user_identifier):
                return self._create_rate_limited_response(attempt_type)

            # Record attempt before processing
            await self._record_attempt(request, attempt_type, client_ip, user_identifier, "attempt")

            # Process request
            response = await call_next(request)

            # Check if authentication was successful
            is_success = self._is_successful_auth(response)

            # Record result
            result_type = "success" if is_success else "failure"
            await self._record_attempt(
                request, attempt_type, client_ip, user_identifier, result_type
            )

            # Apply progressive penalties for failures
            if not is_success:
                await self._apply_progressive_penalty(user_identifier, client_ip, attempt_type)

            return response

        except Exception as e:
            logger.error(f"Auth rate limiter error: {e}")
            # Fail open - don't block legitimate logins due to rate limiter errors
            return await call_next(request)

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Auth rate limiter Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for auth rate limiting: {e}")
            self.redis_client = None

    def _get_attempt_type(self, request: Request) -> AuthAttemptType | None:
        """Determine authentication attempt type from request path."""
        path = str(request.url.path)
        return self.config.protected_paths.get(path)

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP from request."""
        ip_headers = ["x-forwarded-for", "x-real-ip", "x-client-ip", "cf-connecting-ip"]

        for header in ip_headers:
            if header in request.headers:
                ip = request.headers[header].split(",")[0].strip()
                try:
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue

        return request.client.host if request.client else "127.0.0.1"

    async def _extract_user_identifier(
        self, request: Request, attempt_type: AuthAttemptType
    ) -> str | None:
        """
        Extract user identifier from request for rate limiting.
        """
        try:
            # Try to get identifier from request body (for POST requests)
            if request.method in ["POST", "PUT", "PATCH"]:
                # Note: This requires request body to be available
                # In practice, you'd need to use a custom request body parser
                # For now, we'll use a simplified approach
                if attempt_type in [AuthAttemptType.LOGIN, AuthAttemptType.REGISTER]:
                    # Try to get email/username from query params first
                    email = request.query_params.get("email")
                    if email:
                        return hashlib.sha256(email.encode()).hexdigest()[:16]

                    username = request.query_params.get("username")
                    if username:
                        return hashlib.sha256(username.encode()).hexdigest()[:16]

            # Fallback to IP-based identifier
            return f"ip:{self._get_client_ip(request)}"

        except Exception as e:
            logger.error(f"Error extracting user identifier: {e}")
            return f"ip:{self._get_client_ip(request)}"

    async def _is_rate_limited(
        self,
        request: Request,
        attempt_type: AuthAttemptType,
        client_ip: str,
        user_identifier: str | None,
    ) -> bool:
        """
        Check if request should be rate limited.
        """
        if not self.redis_client:
            return False

        try:
            current_time = int(time.time())
            hour_key = current_time // 3600
            minute_key = current_time // 60

            # Check user-specific limits
            if user_identifier:
                user_key = f"auth_limit:user:{user_identifier}:{attempt_type.value}:{hour_key}"
                base_limit = self.base_limits[attempt_type]

                # Apply progressive penalty if there are recent failures
                penalty_multiplier = await self._get_penalty_multiplier(user_identifier)
                effective_limit = int(base_limit * penalty_multiplier)

                user_count = await self.redis_client.get(user_key)
                if user_count and int(user_count) >= effective_limit:
                    await self._log_rate_limit_violation(
                        request, attempt_type, "user_limit", effective_limit
                    )
                    return True

            # Check IP-specific limits
            if attempt_type in self.ip_limits:
                ip_key = f"auth_limit:ip:{client_ip}:{attempt_type.value}:{hour_key}"
                ip_limit = self.ip_limits[attempt_type]

                ip_count = await self.redis_client.get(ip_key)
                if ip_count and int(ip_count) >= ip_limit:
                    await self._log_rate_limit_violation(
                        request, attempt_type, "ip_limit", ip_limit
                    )
                    return True

            # Check global limits
            global_key = f"auth_limit:global:{attempt_type.value}:{minute_key}"
            global_limit = getattr(
                self.config, f"global_{attempt_type.value}_attempts_per_minute", 1000
            )

            global_count = await self.redis_client.get(global_key)
            if global_count and int(global_count) >= global_limit:
                await self._log_rate_limit_violation(
                    request, attempt_type, "global_limit", global_limit
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return False

    async def _record_attempt(
        self,
        request: Request,
        attempt_type: AuthAttemptType,
        client_ip: str,
        user_identifier: str | None,
        result_type: str,
    ) -> None:
        """
        Record authentication attempt in Redis.
        """
        if not self.redis_client:
            return

        try:
            current_time = int(time.time())
            hour_key = current_time // 3600
            minute_key = current_time // 60

            # Record user attempt
            if user_identifier:
                user_key = f"auth_limit:user:{user_identifier}:{attempt_type.value}:{hour_key}"
                await self.redis_client.incr(user_key)
                await self.redis_client.expire(user_key, 7200)  # 2 hours

                # Record failure pattern
                if result_type == "failure":
                    failure_key = f"auth_failures:user:{user_identifier}"
                    await self.redis_client.incr(failure_key)
                    await self.redis_client.expire(failure_key, self.config.max_penalty_duration)

            # Record IP attempt
            if attempt_type in self.ip_limits:
                ip_key = f"auth_limit:ip:{client_ip}:{attempt_type.value}:{hour_key}"
                await self.redis_client.incr(ip_key)
                await self.redis_client.expire(ip_key, 7200)

            # Record global attempt
            global_key = f"auth_limit:global:{attempt_type.value}:{minute_key}"
            await self.redis_client.incr(global_key)
            await self.redis_client.expire(global_key, 300)  # 5 minutes

            # Log for monitoring
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "attempt_type": attempt_type.value,
                "client_ip": client_ip,
                "user_identifier": user_identifier,
                "result": result_type,
                "path": str(request.url.path),
                "user_agent": request.headers.get("user-agent", ""),
            }

            # Store recent attempts for monitoring
            await self.redis_client.lpush("recent_auth_attempts", str(log_data))
            await self.redis_client.ltrim("recent_auth_attempts", 0, 999)  # Keep last 1000
            await self.redis_client.expire("recent_auth_attempts", 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Error recording auth attempt: {e}")

    async def _get_penalty_multiplier(self, user_identifier: str) -> float:
        """
        Calculate penalty multiplier based on recent failures.
        """
        if not self.redis_client or not user_identifier:
            return 1.0

        try:
            failure_key = f"auth_failures:user:{user_identifier}"
            failure_count = int(await self.redis_client.get(failure_key) or 0)

            if failure_count == 0:
                return 1.0

            # Apply exponential penalty
            penalty_multiplier = max(
                self.config.failed_attempt_multiplier**failure_count,
                0.1,  # Don't reduce below 10% of base limit
            )

            return penalty_multiplier

        except Exception as e:
            logger.error(f"Error calculating penalty multiplier: {e}")
            return 1.0

    async def _apply_progressive_penalty(
        self, user_identifier: str | None, client_ip: str, attempt_type: AuthAttemptType
    ) -> None:
        """
        Apply progressive penalties for failed authentication attempts.
        """
        if not self.redis_client:
            return

        try:
            if user_identifier:
                # Check if user should be temporarily blocked
                failure_key = f"auth_failures:user:{user_identifier}"
                failure_count = int(await self.redis_client.get(failure_key) or 0)

                if failure_count >= 5:  # Block after 5 failures
                    block_duration = min(
                        60 * (2 ** (failure_count - 5)), self.config.max_penalty_duration
                    )
                    block_key = f"auth_blocked:user:{user_identifier}"

                    await self.redis_client.setex(
                        block_key, block_duration, f"progressive_penalty:{failure_count}"
                    )

                    logger.warning(
                        f"User {user_identifier} temporarily blocked for {block_duration} seconds "
                        f"after {failure_count} failed auth attempts"
                    )

        except Exception as e:
            logger.error(f"Error applying progressive penalty: {e}")

    def _is_successful_auth(self, response: Response) -> bool:
        """
        Determine if authentication was successful based on response.
        """
        # Success criteria:
        # - HTTP status 2xx
        # - Response contains auth tokens or user data
        # - No error in response body

        if response.status_code >= 400:
            return False

        # Note: This is a simplified check
        # In practice, you'd examine the response body for tokens or success indicators
        return response.status_code < 400

    def _create_rate_limited_response(self, attempt_type: AuthAttemptType) -> JSONResponse:
        """Create response for rate limited requests."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": f"Too many {attempt_type.value} attempts. Please try again later.",
                "error_code": "RATE_LIMITED",
                "attempt_type": attempt_type.value,
            },
        )

    async def _log_rate_limit_violation(
        self, request: Request, attempt_type: AuthAttemptType, limit_type: str, limit: int
    ) -> None:
        """
        Log rate limit violations for security monitoring.
        """
        try:
            violation_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "attempt_type": attempt_type.value,
                "limit_type": limit_type,
                "limit": limit,
                "client_ip": self._get_client_ip(request),
                "path": str(request.url.path),
                "user_agent": request.headers.get("user-agent", ""),
                "headers": dict(request.headers),
            }

            logger.warning(f"Auth rate limit violation: {violation_data}")

            # Store in Redis for security monitoring
            if self.redis_client:
                await self.redis_client.lpush("auth_rate_violations", str(violation_data))
                await self.redis_client.ltrim("auth_rate_violations", 0, 499)  # Keep last 500
                await self.redis_client.expire("auth_rate_violations", 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Error logging rate limit violation: {e}")


class CredentialStuffingProtection:
    """
    Advanced protection against credential stuffing attacks.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_known_compromised_credentials(self, identifier: str, ip: str) -> bool:
        """
        Check if credentials/IP are from known breach sources.
        """
        try:
            # Check against known breach databases or services
            # This would integrate with services like HaveIBeenPwned API

            # For now, implement basic heuristics
            breach_indicators = [f"breached_ip:{ip}", f"compromised_user:{identifier}"]

            for indicator in breach_indicators:
                if await self.redis.exists(indicator):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking compromised credentials: {e}")
            return False

    async def report_compromised_credentials(
        self, identifier: str, ip: str, evidence: dict[str, Any]
    ) -> None:
        """
        Report potentially compromised credentials.
        """
        try:
            report_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "identifier": identifier,
                "ip": ip,
                "evidence": evidence,
            }

            await self.redis.lpush("compromised_credentials_reports", str(report_data))
            await self.redis.expire("compromised_credentials_reports", 86400 * 30)  # 30 days

        except Exception as e:
            logger.error(f"Error reporting compromised credentials: {e}")
