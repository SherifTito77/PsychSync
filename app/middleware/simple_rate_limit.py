"""
Simple Rate Limiting Middleware

Supports both in-memory and Redis-backed rate limiting.
Redis-backed is recommended for production/distributed environments.
"""

import time
import logging
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Configuration
USE_REDIS = os.getenv("USE_REDIS_RATE_LIMIT", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")

# Storage backends
_rate_limit_store = {}  # In-memory storage
_redis_client = None  # Redis client (lazy loaded)

# Paths to rate limit (can be configured)
RATE_LIMITED_PATHS = [
    "/api/v1/health",
    "/api/v1/auth/",
]


async def _get_redis_client():
    """Lazy load Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as redis_async

            _redis_client = await redis_async.from_url(
                REDIS_URL, encoding="utf-8", decode_responses=True
            )
            logger.info(f"Connected to Redis for rate limiting: {REDIS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            _redis_client = False  # Mark as failed
    return _redis_client


async def check_rate_limit_redis(request: Request, limit: int = 30, window: int = 60):
    """
    Check rate limit using Redis backend (distributed).

    This is the recommended approach for production with multiple instances.
    """
    redis_client = await _get_redis_client()

    if not redis_client:
        # Fallback to in-memory if Redis unavailable
        logger.warning("Redis unavailable, falling back to in-memory rate limiting")
        return await check_rate_limit_memory(request, limit, window)

    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Create Redis key
    key = f"ratelimit:{client_ip}:{request.url.path}"

    try:
        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = await pipe.execute()

        current_count = results[0]

        logger.info(f"Redis rate limit check: {key}, count: {current_count}/{limit}")

        if current_count > limit:
            # Get TTL to set proper reset time
            ttl = await redis_client.ttl(key)
            retry_after = max(ttl, 1)

            logger.warning(
                f"Redis rate limit exceeded for {client_ip}: {current_count}/{limit}"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + ttl),
                    "Retry-After": str(retry_after),
                },
            )

        logger.info(
            f"Redis rate limit OK: {key}, count: {current_count}/{limit}, remaining: {limit - current_count}"
        )

    except Exception as e:
        logger.error(f"Redis rate limiting error: {e}")
        # Fallback to in-memory on Redis errors
        return await check_rate_limit_memory(request, limit, window)


async def check_rate_limit_memory(request: Request, limit: int = 30, window: int = 60):
    """
    Check rate limit using in-memory storage.

    WARNING: This does NOT work across multiple instances!
    Each instance has its own counter, allowing users to bypass limits.
    """
    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    # Get current time
    now = time.time()

    # Get or create client record
    key = f"ratelimit:{client_ip}:{request.url.path}"
    timestamps = _rate_limit_store.get(key, [])

    # Filter old timestamps (within window)
    cutoff = now - window
    timestamps = [t for t in timestamps if t > cutoff]

    logger.info(f"Memory rate limit check: {key}, count: {len(timestamps)}/{limit}")

    # Check if limit exceeded
    if len(timestamps) >= limit:
        retry_after = int(timestamps[0] + window - now)
        logger.warning(
            f"Memory rate limit exceeded for {client_ip}: {len(timestamps)}/{limit}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(timestamps[0] + window)),
                "Retry-After": str(retry_after),
            },
        )

    # Add current timestamp
    timestamps.append(now)
    _rate_limit_store[key] = timestamps

    logger.info(f"Memory rate limit OK: {key}, count: {len(timestamps)}/{limit}")


async def check_rate_limit(request: Request, limit: int = 30, window: int = 60):
    """
    Check if request should be rate limited.

    Automatically uses Redis if USE_REDIS_RATE_LIMIT=true, otherwise uses in-memory.

    Args:
        request: FastAPI request object
        limit: Max requests per window
        window: Time window in seconds

    Raises:
        HTTPException: If rate limit exceeded
    """
    if USE_REDIS:
        await check_rate_limit_redis(request, limit, window)
    else:
        await check_rate_limit_memory(request, limit, window)


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware that applies to specific paths.

    Supports both in-memory and Redis-backed storage.
    """

    async def dispatch(self, request, call_next):
        """Process request with rate limiting"""
        # Check if path should be rate limited
        path = request.url.path
        should_limit = any(path.startswith(p) for p in RATE_LIMITED_PATHS)

        if should_limit:
            try:
                await check_rate_limit(request, limit=30, window=60)
            except HTTPException as e:
                # Return 429 response directly
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail},
                    headers=e.headers if hasattr(e, "headers") else {},
                )

        # Continue with normal request processing
        response = await call_next(request)
        return response
