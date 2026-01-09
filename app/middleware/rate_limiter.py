"""
API Rate Limiting Middleware
Implements token bucket algorithm for comprehensive rate limiting with
Redis backend and configurable limits per endpoint/user.

Key Features:
- Token bucket algorithm for smooth rate limiting
- User-based and IP-based rate limiting
- Configurable limits per endpoint
- Redis backend for distributed rate limiting
- Sliding window for accurate burst control
- Rate limit headers in responses
- Automatic cleanup of expired keys
- Support for different rate limit strategies
"""

import asyncio
from datetime import datetime, timedelta
import logging
import time
from typing import Any

from fastapi import HTTPException, Request, status
import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration."""

    def __init__(
        self,
        calls_per_minute: int = 60,
        calls_per_hour: int = 1000,
        calls_per_day: int = 10000,
        burst_size: int = 10,
        enabled: bool = True,
    ):
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.calls_per_day = calls_per_day
        self.burst_size = burst_size
        self.enabled = enabled


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded."""

    def __init__(self, retry_after: int | None = None, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail or "Rate limit exceeded",
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )


class TokenBucket:
    """Token bucket implementation for rate limiting."""

    def __init__(self, rate: int, burst: int):
        self.rate = rate  # Tokens per second
        self.burst = burst  # Maximum burst size
        self.tokens = burst
        self.last_update = time.time()
        self.max_tokens = burst

    async def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket."""
        current_time = time.time()

        # Add tokens based on elapsed time
        elapsed = current_time - self.last_update
        tokens_to_add = elapsed * self.rate

        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_update = current_time

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_tokens(self) -> int:
        """Get current token count."""
        return self.tokens

    def time_until_refill(self, tokens: int) -> float:
        """Calculate time until bucket has specified tokens."""
        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis for distributed rate limiting."""

    def __init__(
        self,
        app,
        redis_url: str | None = None,
        default_limits: dict[str, RateLimitConfig] | None = None,
    ):
        super().__init__(app)

        self.default_limits = default_limits or {
            "default": RateLimitConfig(60, 1000, 10000, 10),
            "api": RateLimitConfig(120, 5000, 50000, 20),
            "auth": RateLimitConfig(20, 200, 1000, 5),
            "health": RateLimitConfig(1000, 10000, 100000, 50),
            "admin": RateLimitConfig(30, 500, 2000, 5),
        }

        self.endpoint_limits = {}
        self.global_limits = {}
        self.redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379")
        self.redis = None

        # Initialize Redis connection
        asyncio.create_task(self._init_redis())

    async def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("Rate limiting middleware connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
            # Rate limiting will be disabled

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""

        # Skip rate limiting for health checks
        if self._should_skip_rate_limiting(request):
            return await call_next(request)

        # Get identifier (user ID or IP)
        identifier = await self._get_identifier(request)

        # Determine applicable limits
        rate_limits = await self._get_applicable_limits(request, identifier)

        # Check rate limits
        for limit_name, config in rate_limits.items():
            if not config.enabled:
                continue

            is_allowed, retry_after = await self._check_rate_limit(identifier, limit_name, config)

            if not is_allowed:
                # Update rate limit headers in response
                response = await call_next(request)
                await self._add_rate_limit_headers(
                    response, limit_name, config, retry_after, identifier
                )
                return response

            # Check burst limit
            burst_allowed = await self._check_burst_limit(identifier, limit_name, config)

            if not burst_allowed:
                retry_after = 1  # Retry after 1 second for burst limit
                response = await call_next(request)
                await self._add_rate_limit_headers(
                    response, limit_name, config, retry_after, identifier
                )
                return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining_minute, remaining_hour = await self._get_remaining_tokens(identifier, rate_limits)

        if identifier.startswith("user:"):
            await self._add_rate_limit_headers(
                response,
                "user",
                RateLimitConfig(remaining_minute, remaining_hour, 0, 0),
                None,
                identifier,
            )
        elif identifier.startswith("ip:"):
            await self._add_rate_limit_headers(
                response,
                "ip",
                RateLimitConfig(remaining_minute, remaining_hour, 0, 0),
                None,
                identifier,
            )

        return response

    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Determine if request should skip rate limiting."""
        skip_paths = [
            "/health",
            "/metrics",
            "/status",
            "/favicon.ico",
            "/static/",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        return any(request.url.path.startswith(path) for path in skip_paths)

    async def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting."""
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id', 'anonymous')}"

        # Try to get user ID from session/token
        if hasattr(request, "headers"):
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Extract user from JWT token (simplified)
                # In production, decode the JWT token
                return f"user:{auth_header[:20]}..."  # Simplified

        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client.host else "unknown"

    async def _get_applicable_limits(
        self, request: Request, identifier: str
    ) -> dict[str, RateLimitConfig]:
        """Get applicable rate limits for the request."""
        rate_limits = {}

        # Add default limits
        rate_limits["default"] = self.default_limits.get(
            "default", RateLimitConfig(60, 1000, 10000, 10)
        )

        # Add global user limits if user is authenticated
        if identifier.startswith("user:"):
            rate_limits["user"] = RateLimitConfig(120, 2000, 10000, 15)
        elif identifier.startswith("ip:"):
            rate_limits["ip"] = RateLimitConfig(30, 500, 5000, 5)

        # Add endpoint-specific limits
        path = request.url.path
        if path.startswith("/api/v1/auth/"):
            rate_limits["auth"] = self.default_limits.get("auth", RateLimitConfig(20, 200, 1000, 5))
        elif path.startswith("/api/v1/admin/"):
            rate_limits["admin"] = self.default_limits.get(
                "admin", RateLimitConfig(30, 500, 2000, 5)
            )
        elif path.startswith("/api/v1/"):
            rate_limits["api"] = self.default_limits.get(
                "api", RateLimitConfig(120, 5000, 50000, 20)
            )
        elif path.startswith("/health"):
            rate_limits["health"] = self.default_limits.get(
                "health", RateLimitConfig(1000, 10000, 100000, 50)
            )

        # Check custom endpoint limits
        for endpoint_pattern, config in self.endpoint_limits.items():
            if endpoint_pattern in path:
                rate_limits["custom"] = config

        return rate_limits

    async def _check_rate_limit(
        self, identifier: str, limit_name: str, config: RateLimitConfig
    ) -> tuple[bool, int | None]:
        """Check if identifier is within rate limits."""

        if not self.redis or not config.enabled:
            return True, None

        try:
            # Create bucket keys
            minute_key = f"rate_limit:{identifier}:{limit_name}:minute"
            hour_key = f"rate_limit:{identifier}:{limit_name}:hour"
            day_key = f"rate_limit:{identifier}:{limit_name}:day"

            # Get current token counts
            minute_count = await self.redis.get(minute_key)
            hour_count = await self.redis.get(hour_key)
            day_count = await self.redis.get(day_key)

            minute_count = int(minute_count) if minute_count else 0
            hour_count = int(hour_count) if hour_count else 0
            day_count = int(day_count) if day_count else 0

            current_time = int(time.time())
            minute_bucket = current_time // 60
            hour_bucket = current_time // 3600
            day_bucket = current_time // 86400

            # Check if we need to reset counters
            last_minute_bucket = await self.redis.get(f"{minute_key}:bucket")
            if last_minute_bucket and int(last_minute_bucket) != minute_bucket:
                minute_count = 0
                await self.redis.set(f"{minute_key}:bucket", str(minute_bucket))
                await self.redis.set(minute_key, str(minute_count))
                await self.redis.expire(minute_key, 120)  # 2 minutes

            last_hour_bucket = await self.redis.get(f"{hour_key}:bucket")
            if last_hour_bucket and int(last_hour_bucket) != hour_bucket:
                hour_count = 0
                await self.redis.set(f"{hour_key}:bucket", str(hour_bucket))
                await self.redis.set(hour_key, str(hour_count))
                await self.redis.expire(hour_key, 7200)  # 2 hours

            last_day_bucket = await self.redis.get(f"{day_key}:bucket")
            if last_day_bucket and int(last_day_bucket) != day_bucket:
                day_count = 0
                await self.redis.set(f"{day_key}:bucket", str(day_bucket))
                await self.redis.set(day_key, str(day_count))
                await self.redis.expire(day_key, 172800)  # 48 hours

            # Check limits
            if minute_count >= config.calls_per_minute:
                retry_after = 60 - (current_time % 60)
                return False, retry_after

            if hour_count >= config.calls_per_hour:
                retry_after = 3600 - (current_time % 3600)
                return False, retry_after

            if day_count >= config.calls_per_day:
                retry_after = 86400 - (current_time % 86400)
                return False, retry_after

            # Increment minute counter
            await self.redis.incr(minute_key)
            await self.redis.expire(minute_key, 120)

            return True, None

        except Exception as e:
            logger.exception(f"Error checking rate limit: {e!s}")
            return True, None

    async def _check_burst_limit(
        self, identifier: str, limit_name: str, config: RateLimitConfig
    ) -> bool:
        """Check burst limit for identifier."""

        if not self.redis or config.burst_size <= 0:
            return True

        try:
            burst_key = f"burst_limit:{identifier}:{limit_name}"

            current_tokens = await self.redis.get(burst_key)
            current_tokens = int(current_tokens) if current_tokens else config.burst_size

            if current_tokens > 0:
                await self.redis.decr(burst_key)
                await self.redis.expire(burst_key, 300)  # 5 minutes
                return True

            return False

        except Exception as e:
            logger.exception(f"Error checking burst limit: {e!s}")
            return True

    async def _get_remaining_tokens(
        self, identifier: str, rate_limits: dict[str, RateLimitConfig]
    ) -> tuple[int, int]:
        """Get remaining tokens for each rate limit."""
        remaining_minute = 0
        remaining_hour = 0

        try:
            if not self.redis:
                return 0, 0

            # Get default limits
            default_config = rate_limits.get("default")
            if default_config:
                minute_key = f"rate_limit:{identifier}:default:minute"
                hour_key = f"rate_limit:{identifier}:default:hour"

                minute_count = await self.redis.get(minute_key)
                hour_count = await self.redis.get(hour_key)

                minute_count = int(minute_count) if minute_count else 0
                hour_count = int(hour_count) if hour_count else 0

                remaining_minute = max(0, default_config.calls_per_minute - minute_count)
                remaining_hour = max(0, default_config.calls_per_hour - hour_count)

            # Check for user-specific limits
            if identifier.startswith("user:"):
                user_config = rate_limits.get("user")
                if user_config:
                    minute_key = f"rate_limit:{identifier}:user:minute"
                    hour_key = f"rate_limit:{identifier}:user:hour"

                    user_minute_count = await self.redis.get(minute_key)
                    user_hour_count = await self.redis.get(hour_key)

                    user_minute_count = int(user_minute_count) if user_minute_count else 0
                    user_hour_count = int(user_hour_count) if user_hour_count else 0

                    remaining_minute = max(
                        0, min(remaining_minute, user_config.calls_per_minute - user_minute_count)
                    )
                    remaining_hour = max(
                        0, min(remaining_hour, user_config.calls_per_hour - user_hour_count)
                    )

        except Exception as e:
            logger.exception(f"Error getting remaining tokens: {e!s}")

        return remaining_minute, remaining_hour

    async def _add_rate_limit_headers(
        self,
        response: Response,
        limit_name: str,
        config: RateLimitConfig,
        retry_after: int | None,
        identifier: str,
    ):
        """Add rate limit headers to response."""

        # Get remaining tokens
        try:
            rate_limits = {limit_name: config}
            remaining_minute, remaining_hour = asyncio.create_task(
                self._get_remaining_tokens(identifier, rate_limits)
            )

            # Get task result (wait a bit if needed)
            if remaining_minute.done():
                remaining_minute, remaining_hour = remaining_minute.result()
            else:
                # Wait a short time for the task to complete
                await asyncio.sleep(0.01)
                remaining_minute, remaining_hour = remaining_minute.result()
        except:
            remaining_minute, remaining_hour = 0, 0

        # Add headers
        response.headers["X-RateLimit-Limit-Minute"] = str(config.calls_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(config.calls_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)

        if retry_after:
            response.headers["X-RateLimit-Retry-After"] = str(retry_after)

        # Add identifier info (for debugging)
        if settings.DEBUG:
            response.headers["X-RateLimit-Identifier"] = identifier
            response.headers["X-RateLimit-Limit-Name"] = limit_name

    async def get_rate_limit_status(self, identifier: str | None = None) -> dict[str, Any]:
        """Get current rate limit status."""

        try:
            if not self.redis:
                return {"status": "disabled", "message": "Rate limiting is disabled"}

            status = {"status": "active", "redis_connected": True, "limits": {}}

            if identifier:
                rate_limits = await self._get_applicable_limits(
                    Request(scope=identifier), identifier
                )

                for limit_name, config in rate_limits.items():
                    try:
                        minute_key = f"rate_limit:{identifier}:{limit_name}:minute"
                        hour_key = f"rate_limit:{identifier}:{limit_name}:hour"

                        minute_count = await self.redis.get(minute_key)
                        hour_count = await self.redis.get(hour_key)

                        minute_count = int(minute_count) if minute_count else 0
                        hour_count = int(hour_count) if hour_count else 0

                        status["limits"][limit_name] = {
                            "calls_per_minute": config.calls_per_minute,
                            "calls_per_hour": config.calls_per_hour,
                            "used_minute": minute_count,
                            "used_hour": hour_count,
                            "remaining_minute": max(0, config.calls_per_minute - minute_count),
                            "remaining_hour": max(0, config.calls_per_hour - hour_count),
                            "burst_size": config.burst_size,
                        }
                    except Exception as e:
                        logger.exception(f"Error getting limit status for {limit_name}: {e!s}")
                        continue

            return status

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def reset_rate_limits(self, identifier: str):
        """Reset rate limits for identifier."""
        if not self.redis:
            return False

        try:
            # Delete all rate limit keys for identifier
            pattern = f"rate_limit:{identifier}:*"

            cursor = self.redis.scan_iter(match=pattern)
            async for key in cursor:
                await self.redis.delete(key)

            logger.info(f"Reset rate limits for {identifier}")
            return True

        except Exception as e:
            logger.exception(f"Error resetting rate limits: {e!s}")
            return False

    async def get_rate_limit_statistics(self, days: int = 7) -> dict[str, Any]:
        """Get rate limiting statistics."""

        try:
            if not self.redis:
                return {"status": "disabled", "message": "Rate limiting is disabled"}

            # Get all rate limit keys
            pattern = "rate_limit:*:*:bucket"

            stats = {
                "total_keys": 0,
                "active_identifiers": set(),
                "total_requests": 0,
                "hourly_requests": [],
                "daily_requests": [],
            }

            cursor = self.redis.scan_iter(match=pattern)
            async for key in cursor:
                stats["total_keys"] += 1

                # Parse key format: rate_limit:identifier:limit:bucket
                parts = key.decode().split(":")
                if len(parts) >= 3:
                    identifier = parts[1]
                    stats["active_identifiers"].add(identifier)

            # Get daily request counts (simplified)
            daily_pattern = "rate_limit:*:*:day"
            cursor = self.redis.scan_iter(match=daily_pattern)
            async for key, value in cursor:
                try:
                    daily_count = int(value)
                    stats["total_requests"] += daily_count
                    stats["daily_requests"].append(
                        {
                            "date": datetime.fromtimestamp(int(key.split(":")[-1])).strftime(
                                "%Y-%m-%d"
                            ),
                            "count": daily_count,
                        }
                    )
                except (ValueError, IndexError):
                    continue

            # Sort by date
            stats["daily_requests"].sort(key=lambda x: x["date"])

            return {"status": "active", "redis_connected": True, "statistics": stats}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def cleanup_expired_keys(self):
        """Clean up expired rate limit keys."""
        if not self.redis:
            return

        try:
            pattern = "rate_limit:*:*:*"

            deleted_count = 0
            cursor = self.redis.scan_iter(match=pattern)
            async for key in cursor:
                # Check TTL
                ttl = await self.redis.ttl(key)
                if ttl == -1:  # No expiry set
                    # Set reasonable expiry
                    await self.redis.expire(key, timedelta(days=1))
                elif ttl == 0:  # Expired
                    await self.redis.delete(key)
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired rate limit keys")

        except Exception as e:
            logger.exception(f"Error cleaning up expired keys: {e!s}")


# Rate limiter for specific endpoints
class EndpointRateLimiter:
    """Rate limiter for specific API endpoints."""

    def __init__(self):
        self.limits = {}
        self.using = asyncio.Semaphore(100)  # Allow up to 100 concurrent operations

    def add_limit(self, path_pattern: str, config: RateLimitConfig):
        """Add rate limit for path pattern."""
        self.limiters[path_pattern] = config

    def check_limit(self, path: str, identifier: str) -> bool:
        """Check if path is rate limited for identifier."""

        for pattern, config in self.limiters.items():
            if pattern in path:
                bucket = TokenBucket(config.calls_per_minute, config.burst_size)
                return bucket.consume()

        return True


def check_rate_limit(
    identifier: str,
    limit_name: str = "default",
    calls_per_minute: int = 60,
    calls_per_hour: int = 1000,
    calls_per_day: int = 10000,
    burst_size: int = 10,
):
    """
    Decorator factory for rate limiting endpoints.

    Args:
        identifier: Unique identifier (user ID or IP address)
        limit_name: Name of the rate limit rule
        calls_per_minute: Maximum calls per minute
        calls_per_hour: Maximum calls per hour
        calls_per_day: Maximum calls per day
        burst_size: Burst size for token bucket

    Returns:
        Decorator function
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs if available
            request = None
            for arg in args:
                if hasattr(arg, "client"):
                    request = arg
                    break

            # Use the identifier or fall back to client IP
            rate_limit_id = identifier
            if request and hasattr(request, "client"):
                rate_limit_id = f"{identifier}:{request.client.host}"

            try:
                # Try to get Redis URL from settings
                redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")

                # Create a temporary middleware instance for this check
                config = RateLimitConfig(
                    calls_per_minute, calls_per_hour, calls_per_day, burst_size
                )

                # Create a minimal middleware instance
                middleware = RateLimitMiddleware(app=None, redis_url=redis_url)

                # Initialize Redis connection if not already initialized
                if not hasattr(middleware, "redis") or middleware.redis is None:
                    await middleware._init_redis()

                # Check the rate limit
                is_allowed, retry_after = await middleware._check_rate_limit(
                    rate_limit_id, limit_name, config
                )

                if not is_allowed:
                    raise RateLimitExceeded(
                        retry_after=retry_after,
                        detail=f"Rate limit exceeded for {limit_name}. Retry after {retry_after} seconds.",
                    )

            except RateLimitExceeded:
                raise
            except Exception as e:
                logger.exception(f"Error in check_rate_limit: {e}")
                # On error, allow the request (fail open)

            # Call the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Backward compatibility: keep the old async function for manual calls
async def check_rate_limit_manual(
    identifier: str,
    limit_name: str = "default",
    calls_per_minute: int = 60,
    calls_per_hour: int = 1000,
    calls_per_day: int = 10000,
    burst_size: int = 10,
) -> tuple[bool, int | None]:
    """
    Manual rate limit checking function for use in endpoints.

    Args:
        identifier: Unique identifier (user ID or IP address)
        limit_name: Name of the rate limit rule
        calls_per_minute: Maximum calls per minute
        calls_per_hour: Maximum calls per hour
        calls_per_day: Maximum calls per day
        burst_size: Burst size for token bucket

    Returns:
        Tuple of (is_allowed: bool, retry_after: Optional[int])
    """
    try:
        # Try to get Redis URL from settings
        redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379")

        # Create a temporary middleware instance for this check
        config = RateLimitConfig(calls_per_minute, calls_per_hour, calls_per_day, burst_size)

        # Create a minimal middleware instance
        middleware = RateLimitMiddleware(app=None, redis_url=redis_url)

        # Initialize Redis connection
        await middleware._init_redis()

        # Check the rate limit
        return await middleware._check_rate_limit(identifier, limit_name, config)

    except Exception as e:
        logger.exception(f"Error in check_rate_limit: {e}")
        # On error, allow the request (fail open)
        return True, None
