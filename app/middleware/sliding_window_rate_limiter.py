# app/middleware/sliding_window_rate_limiter.py
"""
Sliding-window rate limiting middleware.
Uses Redis sorted sets for accurate per-IP and per-user tracking.
Falls back to in-memory counters when Redis is unavailable.
"""

import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.rate_limit_config import get_rate_limit_for_path, RateLimitConfig

logger = logging.getLogger("app.middleware.rate_limiter")

# In-memory fallback (per-process, not shared across workers)
_memory_store: dict[str, list[float]] = defaultdict(list)
_MEMORY_STORE_MAX_KEYS = 10_000


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter with Redis backend and in-memory fallback.

    Uses sorted sets keyed by (client_key, endpoint_path, window) to count
    requests within each time window. Returns standard rate-limit headers.
    """

    def __init__(self, app, redis_client=None, enabled: bool = True):
        super().__init__(app)
        self._redis = redis_client
        self._enabled = enabled

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self._enabled:
            return await call_next(request)

        path = request.url.path
        config = get_rate_limit_for_path(path)

        if not config.enabled:
            return await call_next(request)

        client_key = self._get_client_key(request)
        now = time.time()

        # Check minute window (primary enforcement)
        allowed, remaining, reset_at = await self._check_window(
            client_key=client_key,
            path=path,
            window_seconds=60,
            max_requests=config.requests_per_minute,
            now=now,
        )

        if not allowed:
            retry_after = int(reset_at - now) + 1
            logger.warning(
                "Rate limit exceeded: %s on %s (%d/min)",
                client_key,
                path,
                config.requests_per_minute,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                },
            )

        # Also check hourly window
        hourly_allowed, _, _ = await self._check_window(
            client_key=client_key,
            path=path,
            window_seconds=3600,
            max_requests=config.requests_per_hour,
            now=now,
        )

        if not hourly_allowed:
            logger.warning("Hourly rate limit exceeded: %s on %s", client_key, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Hourly rate limit exceeded", "retry_after": 60},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))

        return response

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier: authenticated user ID or IP."""
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "id"):
            return f"user:{user.id}"

        # Use X-Forwarded-For if behind a proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"

        client = request.client
        return f"ip:{client.host}" if client else "ip:unknown"

    async def _check_window(
        self,
        client_key: str,
        path: str,
        window_seconds: int,
        max_requests: int,
        now: float,
    ) -> tuple[bool, int, float]:
        """
        Check if request is within the rate limit for a given window.

        Returns (allowed, remaining, window_reset_timestamp).
        """
        bucket_key = f"rl:{client_key}:{path}:{window_seconds}"
        window_start = now - window_seconds
        reset_at = now + window_seconds

        if self._redis:
            try:
                return await self._check_redis(
                    bucket_key, window_start, now, max_requests, reset_at
                )
            except Exception:
                pass  # Fall through to in-memory

        return self._check_memory(bucket_key, window_start, now, max_requests, reset_at)

    async def _check_redis(
        self,
        key: str,
        window_start: float,
        now: float,
        max_requests: int,
        reset_at: float,
    ) -> tuple[bool, int, float]:
        """Redis sorted-set sliding window."""
        # Step 1: prune old entries and count current
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        results = await pipe.execute()

        count = results[1]
        allowed = count < max_requests
        remaining = max(0, max_requests - count - 1)

        # Step 2: only record the request if allowed
        if allowed:
            await self._redis.zadd(key, {str(now): now})
            await self._redis.expire(key, int(reset_at - now) + 10)

        return allowed, remaining, reset_at

    def _check_memory(
        self,
        key: str,
        window_start: float,
        now: float,
        max_requests: int,
        reset_at: float,
    ) -> tuple[bool, int, float]:
        """In-memory fallback using timestamp lists."""
        timestamps = _memory_store[key]
        # Prune old entries
        _memory_store[key] = [ts for ts in timestamps if ts > window_start]
        timestamps = _memory_store[key]

        # Evict oldest keys if store grows too large (DDoS protection)
        if len(_memory_store) > _MEMORY_STORE_MAX_KEYS:
            excess = len(_memory_store) - _MEMORY_STORE_MAX_KEYS
            for old_key in list(_memory_store.keys())[:excess]:
                del _memory_store[old_key]

        count = len(timestamps)
        allowed = count < max_requests
        remaining = max(0, max_requests - count - 1)

        if allowed:
            timestamps.append(now)

        return allowed, remaining, reset_at
