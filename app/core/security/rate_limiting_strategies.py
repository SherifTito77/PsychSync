"""
Rate Limiting Strategies for Security Middleware

This module provides pluggable rate limiting strategies:
- Redis-based rate limiting (production)
- In-memory fallback (development/testing)

Strategy Pattern allows easy switching between implementations.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict
import redis
from slowapi.errors import RateLimitExceeded
from app.core.security.redis_connection_manager import RedisConnectionManager

logger = logging.getLogger(__name__)


class RateLimitStrategy(ABC):
    """Base strategy for rate limiting"""

    @abstractmethod
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if rate limit is exceeded

        Args:
            key: Unique identifier for rate limit bucket
            limit: Maximum requests allowed
            window: Time window in seconds

        Returns:
            True if under limit, False if exceeded

        Raises:
            RateLimitExceeded: If limit is exceeded
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if rate limiting strategy is available"""
        pass


class RedisRateLimiter(RateLimitStrategy):
    """
    Redis-based rate limiting using sliding window counter.

    Pros:
    - Distributed rate limiting across multiple instances
    - Persistent across restarts
    - Accurate rate limiting

    Cons:
    - Requires Redis dependency
    - Network latency
    """

    def __init__(self, redis_manager: RedisConnectionManager):
        """
        Initialize Redis rate limiter

        Args:
            redis_manager: Redis connection manager instance
        """
        self.redis_manager = redis_manager

    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check rate limit using Redis sliding window

        Args:
            key: Rate limit key (e.g., "user:123:endpoint:/api/test")
            limit: Max requests allowed
            window: Time window in seconds

        Returns:
            True if under limit

        Raises:
            RateLimitExceeded: If limit exceeded
        """
        if not self.is_available():
            # Fail open - don't block if Redis is down
            logger.warning(f"Redis unavailable, allowing request for key: {key}")
            return True

        try:
            client = self.redis_manager.get_client()
            current = client.incr(key)

            # Set expiry on first request
            if current == 1:
                client.expire(key, window)

            if current > limit:
                logger.warning(
                    f"Rate limit exceeded for {key}: {current}/{limit}",
                    extra={"key": key, "limit": limit, "window": window}
                )
                raise RateLimitExceeded(f"Rate limit exceeded: {limit} requests per {window}s")

            return True

        except RateLimitExceeded:
            raise
        except redis.ConnectionError as e:
            logger.error(
                f"Redis connection error during rate limiting: {e!s}",
                extra={"key": key, "limit": limit, "error_type": "ConnectionError"},
                exc_info=True
            )
            # Fail open - don't block if Redis is down
            return True
        except Exception as e:
            logger.error(
                f"Unexpected error during rate limiting: {e!s}",
                extra={"key": key, "limit": limit, "error_type": type(e).__name__},
                exc_info=True
            )
            # Fail open for safety
            return True

    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_manager.is_available


class InMemoryRateLimiter(RateLimitStrategy):
    """
    In-memory rate limiting as fallback.

    Pros:
    - No external dependencies
    - Fast (no network calls)
    - Works in development

    Cons:
    - Not distributed (each instance has own counters)
    - Lost on restart
    - Not suitable for production
    """

    def __init__(self):
        """Initialize in-memory rate limiter"""
        self._counters: Dict[str, tuple[int, float]] = {}  # key -> (count, expiry)

    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check rate limit using in-memory counter

        Args:
            key: Rate limit key
            limit: Max requests allowed
            window: Time window in seconds

        Returns:
            True if under limit

        Raises:
            RateLimitExceeded: If limit exceeded
        """
        now = time.time()

        # Clean up expired entries
        self._cleanup_expired(now)

        # Get or create counter
        if key not in self._counters:
            self._counters[key] = (1, now + window)
            return True

        count, expiry = self._counters[key]

        # Check if window expired
        if now > expiry:
            self._counters[key] = (1, now + window)
            return True

        # Increment counter
        new_count = count + 1

        if new_count > limit:
            logger.warning(
                f"In-memory rate limit exceeded for {key}: {new_count}/{limit}",
                extra={"key": key, "limit": limit, "window": window}
            )
            raise RateLimitExceeded(f"Rate limit exceeded: {limit} requests per {window}s")

        self._counters[key] = (new_count, expiry)
        return True

    def _cleanup_expired(self, now: float) -> None:
        """Remove expired entries from counter"""
        expired_keys = [
            key for key, (_, expiry) in self._counters.items()
            if now > expiry
        ]
        for key in expired_keys:
            del self._counters[key]

    def is_available(self) -> bool:
        """In-memory rate limiter is always available"""
        return True


class RateLimiterFactory:
    """
    Factory for creating rate limiters with automatic fallback.

    Tries Redis first, falls back to in-memory if unavailable.
    """

    @staticmethod
    def create(redis_manager: RedisConnectionManager, allow_fallback: bool = True) -> RateLimitStrategy:
        """
        Create rate limiter with automatic fallback

        Args:
            redis_manager: Redis connection manager
            allow_fallback: Whether to fall back to in-memory if Redis fails

        Returns:
            RateLimitStrategy instance

        Note:
            In production, fallback should be False to enforce Redis usage
        """
        try:
            redis_limiter = RedisRateLimiter(redis_manager)
            if redis_limiter.is_available():
                logger.info("Using Redis-based rate limiting")
                return redis_limiter
        except Exception as e:
            logger.warning(f"Failed to create Redis rate limiter: {e}")

        if allow_fallback:
            logger.warning(
                "⚠️  Falling back to in-memory rate limiting. "
                "This is NOT safe for production!"
            )
            return InMemoryRateLimiter()

        raise RuntimeError("Redis rate limiter unavailable and fallback disabled")
