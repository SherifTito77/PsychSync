"""
Unified Rate Limiter - Consolidated rate limiting with multiple strategies

This module consolidates all rate limiter implementations into a single,
coherent system using the Strategy pattern.

Strategies:
- Sliding Window: Accurate rate limiting using Redis sorted sets
- Token Bucket: Smooth rate limiting with burst capacity
- Fixed Window: Simple counter-based rate limiting

Backends:
- Redis: Distributed rate limiting for production
- Memory: In-memory fallback for development/testing

Key Features:
- Multiple rate limiting strategies
- Pluggable storage backends
- Decorator and middleware interfaces
- Graceful fallback on Redis failures
- Comprehensive metadata (retry-after, remaining, reset time)
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting algorithm strategies"""

    SLIDING_WINDOW = "sliding_window"  # Most accurate, uses Redis sorted sets
    TOKEN_BUCKET = "token_bucket"  # Smooth rate limiting with burst capacity
    FIXED_WINDOW = "fixed_window"  # Simple counter-based, least accurate


class StorageBackend(Enum):
    """Storage backend types"""

    REDIS = "redis"  # Distributed, production-ready
    MEMORY = "memory"  # In-memory, for development/testing


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    limit: int = 100  # Maximum requests
    window: int = 60  # Time window in seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst: int = 0  # Burst capacity (for token bucket)
    enabled: bool = True

    # Per-endpoint/user/ip configuration
    per_user: bool = False
    per_ip: bool = True
    key_prefix: str = "rate_limit"

    def __post_init__(self):
        """Set burst capacity if not specified"""
        if self.burst == 0:
            self.burst = int(self.limit * 1.5)  # Default burst to 1.5x limit


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""

    allowed: bool
    limit: int
    remaining: int
    reset_time: float  # Unix timestamp
    retry_after: int = 0  # Seconds until retry
    current_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers"""
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_time)),
            "Retry-After": str(self.retry_after) if self.retry_after > 0 else "0",
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_time": self.reset_time,
            "retry_after": self.retry_after,
            "current_count": self.current_count,
        }


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, result: RateLimitResult):
        self.result = result
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                **result.to_dict(),
            },
            headers=result.to_headers(),
        )


# ============================================================================
# STORAGE BACKENDS
# ============================================================================


class StorageBackendInterface(ABC):
    """Abstract interface for storage backends"""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Get value from storage"""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, expire: int | None = None):
        """Set value in storage with optional expiration"""
        pass

    @abstractmethod
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter and return new value"""
        pass

    @abstractmethod
    async def expire(self, key: str, seconds: int):
        """Set expiration on key"""
        pass

    @abstractmethod
    async def delete(self, key: str):
        """Delete key"""
        pass

    @abstractmethod
    async def zadd(self, key: str, mapping: dict[str, float]):
        """Add to sorted set (for sliding window)"""
        pass

    @abstractmethod
    async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        """Remove from sorted set by score (for sliding window)"""
        pass

    @abstractmethod
    async def zcard(self, key: str) -> int:
        """Get count in sorted set"""
        pass

    @abstractmethod
    async def zrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        """Get range from sorted set"""
        pass


class RedisStorage(StorageBackendInterface):
    """Redis storage backend with thread-safe connection initialization"""

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or getattr(
            settings, "REDIS_URL", "redis://localhost:6379"
        )
        self._redis: aioredis.Redis | None = None
        self._initialized = False
        self._connection_lock = (
            asyncio.Lock()
        )  # **Fixed Race:** Add lock for connection initialization

    async def _ensure_connected(self):
        """
        Ensure Redis connection is established.

        **Fixed Race Condition:** Uses lock to prevent multiple concurrent connections.
        Previously, multiple coroutines could pass the `_initialized` check simultaneously,
        creating duplicate Redis connections.
        """
        # Fast path: already initialized
        if self._initialized and self._redis:
            return

        # Use lock to prevent race condition during initialization
        async with self._connection_lock:
            # Double-check inside lock (another coroutine may have initialized while we waited)
            if self._initialized and self._redis:
                return

            try:
                self._redis = aioredis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
                await self._redis.ping()
                self._initialized = True
                logger.info(f"Rate limiter connected to Redis: {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
                self._initialized = False
                raise

    async def get(self, key: str) -> str | None:
        await self._ensure_connected()
        return await self._redis.get(key) if self._redis else None

    async def set(self, key: str, value: str, expire: int | None = None):
        await self._ensure_connected()
        if self._redis:
            await self._redis.set(key, value, ex=expire)

    async def incr(self, key: str, amount: int = 1) -> int:
        await self._ensure_connected()
        return await self._redis.incrby(key, amount) if self._redis else 0

    async def expire(self, key: str, seconds: int):
        await self._ensure_connected()
        if self._redis:
            await self._redis.expire(key, seconds)

    async def delete(self, key: str):
        await self._ensure_connected()
        if self._redis:
            await self._redis.delete(key)

    async def zadd(self, key: str, mapping: dict[str, float]):
        await self._ensure_connected()
        if self._redis:
            await self._redis.zadd(key, mapping)

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        await self._ensure_connected()
        if self._redis:
            await self._redis.zremrangebyscore(key, min_score, max_score)

    async def zcard(self, key: str) -> int:
        await self._ensure_connected()
        return await self._redis.zcard(key) if self._redis else 0

    async def zrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        await self._ensure_connected()
        if self._redis:
            return await self._redis.zrange(key, start, end, withscores=withscores)
        return []

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._initialized = False


class MemoryStorage(StorageBackendInterface):
    """In-memory storage backend (for development/testing)"""

    def __init__(self):
        self._storage: dict[str, Any] = {}
        self._sorted_sets: dict[str, dict[str, float]] = {}
        self._expires: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def _cleanup_expired(self):
        """
        Remove expired entries.

        **Fixed Race Condition:** Creates snapshot before iteration to avoid
        RuntimeError: dictionary changed size during iteration.
        """
        now = time.time()
        async with self._lock:
            # Create snapshot of expired keys BEFORE modifying dictionaries
            expired_keys = [
                key for key, expiry in self._expires.items() if expiry < now
            ]

            # Now safe to modify dictionaries
            for key in expired_keys:
                self._storage.pop(key, None)
                self._sorted_sets.pop(key, None)
                self._expires.pop(key, None)

    async def get(self, key: str) -> str | None:
        await self._cleanup_expired()
        async with self._lock:
            return self._storage.get(key)

    async def set(self, key: str, value: str, expire: int | None = None):
        async with self._lock:
            self._storage[key] = value
            if expire:
                self._expires[key] = time.time() + expire

    async def incr(self, key: str, amount: int = 1) -> int:
        await self._cleanup_expired()
        async with self._lock:
            current = int(self._storage.get(key, 0))
            new_value = current + amount
            self._storage[key] = str(new_value)
            return new_value

    async def expire(self, key: str, seconds: int):
        async with self._lock:
            self._expires[key] = time.time() + seconds

    async def delete(self, key: str):
        async with self._lock:
            self._storage.pop(key, None)
            self._sorted_sets.pop(key, None)
            self._expires.pop(key, None)

    async def zadd(self, key: str, mapping: dict[str, float]):
        async with self._lock:
            if key not in self._sorted_sets:
                self._sorted_sets[key] = {}
            self._sorted_sets[key].update(mapping)

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float):
        async with self._lock:
            if key in self._sorted_sets:
                self._sorted_sets[key] = {
                    k: v
                    for k, v in self._sorted_sets[key].items()
                    if not (min_score <= v <= max_score)
                }

    async def zcard(self, key: str) -> int:
        async with self._lock:
            return len(self._sorted_sets.get(key, {}))

    async def zrange(
        self, key: str, start: int, end: int, withscores: bool = False
    ) -> list:
        async with self._lock:
            sorted_items = sorted(
                self._sorted_sets.get(key, {}).items(), key=lambda x: x[1]
            )
            if withscores:
                return (
                    sorted_items[start : end + 1] if end >= 0 else sorted_items[start:]
                )
            return (
                [k for k, v in sorted_items[start : end + 1]]
                if end >= 0
                else [k for k, v in sorted_items[start:]]
            )


# ============================================================================
# RATE LIMITING STRATEGIES
# ============================================================================


class RateLimitStrategyInterface(ABC):
    """Abstract interface for rate limiting strategies"""

    @abstractmethod
    async def check(
        self,
        storage: StorageBackendInterface,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check if request is allowed"""
        pass


class TokenBucketStrategy(RateLimitStrategyInterface):
    """Token bucket rate limiting strategy with atomic operations"""

    # Lua script for atomic token bucket check and consume
    TOKEN_BUCKET_SCRIPT = """
        local tokens_key = KEYS[1]
        local refill_key = KEYS[2]
        local current_time = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])

        -- Get current state
        local tokens_str = redis.call('GET', tokens_key)
        local last_refill_str = redis.call('GET', refill_key)

        local tokens
        local last_refill

        if tokens_str == false then
            -- First request - start with full bucket
            tokens = capacity
            last_refill = current_time
            redis.call('SET', tokens_key, tostring(tokens))
            redis.call('SET', refill_key, tostring(last_refill))
            redis.call('EXPIRE', tokens_key, tonumber(ARGV[4]))
            redis.call('EXPIRE', refill_key, tonumber(ARGV[4]))
        else
            tokens = tonumber(tokens_str)
            last_refill = tonumber(last_refill_str)

            -- Calculate tokens to add based on elapsed time
            local elapsed = current_time - last_refill
            local tokens_to_add = elapsed * refill_rate

            -- Refill tokens up to capacity
            tokens = math.min(capacity, tokens + tokens_to_add)
        end

        -- Check if we have enough tokens
        local allowed = tokens >= 1.0
        local remaining
        local retry_after

        if allowed then
            -- Consume one token
            tokens = tokens - 1.0
            redis.call('SET', tokens_key, tostring(tokens))
            redis.call('SET', refill_key, tostring(current_time))
            remaining = math.floor(tokens)
            retry_after = 0
        else
            -- Calculate retry_after: time needed for 1 token
            local tokens_needed = 1.0 - tokens
            retry_after = math.ceil(tokens_needed / refill_rate)
            remaining = 0
        end

        -- Calculate reset time (when bucket will be full again)
        local tokens_until_full = capacity - tokens
        local reset_time
        if tokens_until_full > 0 then
            reset_time = current_time + (tokens_until_full / refill_rate)
        else
            reset_time = current_time
        end

        -- Return: allowed, remaining, reset_time, retry_after
        return {allowed and 1 or 0, remaining, reset_time, retry_after}
    """

    def __init__(self):
        super().__init__()
        self._lua_scripts: dict[str, Any] = {}

    async def check(
        self,
        storage: StorageBackendInterface,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """
        Token bucket algorithm with ATOMIC operations using Lua script.

        The bucket has capacity and refill rate. Tokens are added at a constant rate.
        Requests consume tokens. If insufficient tokens, request is denied.

        **Fixed Race Condition:** Uses Redis Lua script for atomic check-and-consume.
        """
        current_time = time.time()
        bucket_key = f"{key}:token_bucket"

        tokens_key = f"{bucket_key}:tokens"
        refill_key = f"{bucket_key}:last_refill"

        # Calculate parameters
        capacity = config.limit + config.burst
        refill_rate = config.limit / config.window  # tokens per second
        expire_time = config.window * 2

        # Use atomic Lua script for Redis backend
        if isinstance(storage, RedisStorage):
            result = await self._check_atomic_redis(
                storage,
                tokens_key,
                refill_key,
                current_time,
                capacity,
                refill_rate,
                expire_time,
            )
        else:
            # Fallback for in-memory storage (still has race, but only for development)
            result = await self._check_memory(
                storage,
                tokens_key,
                refill_key,
                current_time,
                capacity,
                refill_rate,
                expire_time,
            )

        return RateLimitResult(
            allowed=result["allowed"],
            limit=config.limit,
            remaining=result["remaining"],
            reset_time=result["reset_time"],
            retry_after=result["retry_after"],
            current_count=0,  # Token bucket doesn't track count in window
            metadata={"capacity": capacity, "refill_rate": refill_rate},
        )

    async def _check_atomic_redis(
        self,
        storage: "RedisStorage",
        tokens_key: str,
        refill_key: str,
        current_time: float,
        capacity: float,
        refill_rate: float,
        expire_time: int,
    ) -> dict[str, Any]:
        """Execute atomic token bucket check using Lua script"""
        # Get or register Lua script
        script_key = "token_bucket"
        if script_key not in self._lua_scripts:
            self._lua_scripts[script_key] = storage._redis.register_script(
                self.TOKEN_BUCKET_SCRIPT
            )

        script = self._lua_scripts[script_key]

        # Execute script atomically
        result = await script(
            keys=[tokens_key, refill_key],
            args=[current_time, capacity, refill_rate, expire_time],
        )

        return {
            "allowed": bool(result[0]),
            "remaining": int(result[1]),
            "reset_time": float(result[2]),
            "retry_after": int(result[3]),
        }

    async def _check_memory(
        self,
        storage: "MemoryStorage",
        tokens_key: str,
        refill_key: str,
        current_time: float,
        capacity: float,
        refill_rate: float,
        expire_time: int,
    ) -> dict[str, Any]:
        """Fallback check for in-memory storage (dev/test only)"""
        tokens_str = await storage.get(tokens_key)
        last_refill_str = await storage.get(refill_key)

        if tokens_str is None:
            tokens = capacity
            last_refill = current_time
            await storage.set(tokens_key, str(tokens))
            await storage.set(refill_key, str(last_refill))
            await storage.expire(tokens_key, expire_time)
            await storage.expire(refill_key, expire_time)
        else:
            tokens = float(tokens_str)
            last_refill = float(last_refill_str)

            elapsed = current_time - last_refill
            tokens_to_add = elapsed * refill_rate
            tokens = min(capacity, tokens + tokens_to_add)

        allowed = tokens >= 1.0

        if allowed:
            tokens -= 1.0
            await storage.set(tokens_key, str(tokens))
            await storage.set(refill_key, str(current_time))
            retry_after = 0
            remaining = int(tokens)
        else:
            tokens_needed = 1.0 - tokens
            retry_after = int((tokens_needed / refill_rate) + 1)
            remaining = 0

        tokens_until_full = capacity - tokens
        reset_time = (
            current_time + (tokens_until_full / refill_rate)
            if tokens_until_full > 0
            else current_time
        )

        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_time": reset_time,
            "retry_after": retry_after,
        }


class SlidingWindowStrategy(RateLimitStrategyInterface):
    """Sliding window rate limiting strategy with atomic operations"""

    # Lua script for atomic sliding window check
    SLIDING_WINDOW_SCRIPT = """
        local key = KEYS[1]
        local current_time = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local window_size = tonumber(ARGV[3])
        local limit = tonumber(ARGV[4])

        -- Remove old entries (outside window)
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- Add current request timestamp
        redis.call('ZADD', key, current_time, tostring(current_time))

        -- Set expiration
        redis.call('EXPIRE', key, window_size + 1)

        -- Count requests in window
        local count = redis.call('ZCARD', key)

        -- Get oldest timestamp for reset time calculation
        local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
        local reset_time
        if oldest and #oldest > 0 then
            reset_time = tonumber(oldest[2]) + window_size
        else
            reset_time = current_time + window_size
        end

        local allowed = count <= limit
        local remaining = math.max(0, limit - count)
        local retry_after
        if not allowed then
            retry_after = math.ceil(reset_time - current_time)
        else
            retry_after = 0
        end

        -- Return: count, allowed, remaining, reset_time, retry_after
        return {count, allowed and 1 or 0, remaining, reset_time, retry_after}
    """

    def __init__(self):
        super().__init__()
        self._lua_scripts: dict[str, Any] = {}

    async def check(
        self,
        storage: StorageBackendInterface,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """
        Sliding window algorithm with ATOMIC operations using Lua script.

        Each request adds a timestamp to the sorted set.
        Old timestamps outside the window are removed.
        Count is the number of timestamps in the window.

        **Fixed Race Condition:** Uses Redis Lua script for atomic remove-add-count.
        """
        current_time = time.time()
        window_start = current_time - config.window

        # Use atomic Lua script for Redis backend
        if isinstance(storage, RedisStorage):
            result = await self._check_atomic_redis(
                storage, key, current_time, window_start, config.window, config.limit
            )
        else:
            # Fallback for in-memory storage
            result = await self._check_memory(
                storage, key, current_time, window_start, config
            )

        return RateLimitResult(
            allowed=result["allowed"],
            limit=config.limit,
            remaining=result["remaining"],
            reset_time=result["reset_time"],
            retry_after=result["retry_after"],
            current_count=result["count"],
        )

    async def _check_atomic_redis(
        self,
        storage: "RedisStorage",
        key: str,
        current_time: float,
        window_start: float,
        window_size: int,
        limit: int,
    ) -> dict[str, Any]:
        """Execute atomic sliding window check using Lua script"""
        # Get or register Lua script
        script_key = "sliding_window"
        if script_key not in self._lua_scripts:
            self._lua_scripts[script_key] = storage._redis.register_script(
                self.SLIDING_WINDOW_SCRIPT
            )

        script = self._lua_scripts[script_key]

        # Execute script atomically
        result = await script(
            keys=[key], args=[current_time, window_start, window_size, limit]
        )

        return {
            "count": int(result[0]),
            "allowed": bool(result[1]),
            "remaining": int(result[2]),
            "reset_time": float(result[3]),
            "retry_after": int(result[4]),
        }

    async def _check_memory(
        self,
        storage: "MemoryStorage",
        key: str,
        current_time: float,
        window_start: float,
        config: RateLimitConfig,
    ) -> dict[str, Any]:
        """Fallback check for in-memory storage (dev/test only)"""
        # Remove old entries
        await storage.zremrangebyscore(key, 0, window_start)

        # Add current request
        await storage.zadd(key, {str(current_time): current_time})

        # Count requests in window
        count = await storage.zcard(key)

        # Set expiration
        await storage.expire(key, config.window + 1)

        # Calculate reset time (oldest request + window)
        oldest = await storage.zrange(key, 0, 0, withscores=True)
        if oldest:
            reset_time = oldest[0][1] + config.window
        else:
            reset_time = current_time + config.window

        allowed = count <= config.limit
        retry_after = int(reset_time - current_time) if not allowed else 0

        return {
            "count": count,
            "allowed": allowed,
            "remaining": max(0, config.limit - count + 1),
            "reset_time": reset_time,
            "retry_after": retry_after,
        }


class FixedWindowStrategy(RateLimitStrategyInterface):
    """Fixed window rate limiting strategy with atomic operations"""

    # Lua script for atomic fixed window check and increment
    FIXED_WINDOW_SCRIPT = """
        local window_key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window_expire = tonumber(ARGV[2])

        -- Get current count
        local count_str = redis.call('GET', window_key)
        local count = count_str and tonumber(count_str) or 0

        -- Check if allowed
        local allowed = count < limit
        local new_count
        local remaining

        if allowed then
            -- Increment atomically
            new_count = redis.call('INCR', window_key)

            -- Set expiration on first increment
            if new_count == 1 then
                redis.call('EXPIRE', window_key, window_expire)
            end

            count = new_count
            remaining = math.max(0, limit - count)
        else
            -- Already at limit, return current count
            remaining = 0
        end

        -- Return: allowed, count, remaining
        return {allowed and 1 or 0, count, remaining}
    """

    def __init__(self):
        super().__init__()
        self._lua_scripts: dict[str, Any] = {}

    async def check(
        self,
        storage: StorageBackendInterface,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """
        Fixed window algorithm with ATOMIC check-and-increment.

        Window resets at fixed intervals (e.g., every minute).
        Less accurate but simpler than sliding window.

        **Fixed Oversubscription:** Uses Redis Lua script for atomic check-then-increment.
        Prevents race condition where multiple concurrent requests all pass the check.
        """
        current_time = time.time()
        window_id = int(current_time / config.window)
        window_key = f"{key}:window:{window_id}"

        # Use atomic Lua script for Redis backend
        if isinstance(storage, RedisStorage):
            result = await self._check_atomic_redis(
                storage, window_key, config.limit, config.window + 1
            )
            count = result["count"]
            allowed = result["allowed"]
            remaining = result["remaining"]
        else:
            # Fallback for in-memory storage
            count_str = await storage.get(window_key)
            count = int(count_str) if count_str else 0

            allowed = count < config.limit

            if allowed:
                # Increment counter
                new_count = await storage.incr(window_key)
                # Set expiration
                await storage.expire(window_key, config.window + 1)
                count = new_count

            remaining = max(0, config.limit - count - 1)

        # Calculate reset time (start of next window)
        reset_time = (window_id + 1) * config.window
        retry_after = int(reset_time - current_time) if not allowed else 0

        return RateLimitResult(
            allowed=allowed,
            limit=config.limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            current_count=count,
        )

    async def _check_atomic_redis(
        self,
        storage: "RedisStorage",
        window_key: str,
        limit: int,
        window_expire: int,
    ) -> dict[str, Any]:
        """Execute atomic fixed window check using Lua script"""
        # Get or register Lua script
        script_key = "fixed_window"
        if script_key not in self._lua_scripts:
            self._lua_scripts[script_key] = storage._redis.register_script(
                self.FIXED_WINDOW_SCRIPT
            )

        script = self._lua_scripts[script_key]

        # Execute script atomically
        result = await script(keys=[window_key], args=[limit, window_expire])

        return {
            "allowed": bool(result[0]),
            "count": int(result[1]),
            "remaining": int(result[2]),
        }


# ============================================================================
# UNIFIED RATE LIMITER
# ============================================================================


class UnifiedRateLimiter:
    """
    Unified rate limiter with pluggable strategies and backends.

    Example:
        limiter = UnifiedRateLimiter(
            config=RateLimitConfig(limit=100, window=60),
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            backend=StorageBackend.REDIS,
        )

        result = await limiter.check("user:123")
        if not result.allowed:
            raise RateLimitExceeded(result)
    """

    def __init__(
        self,
        config: RateLimitConfig,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
        backend: StorageBackend = StorageBackend.REDIS,
        redis_url: str | None = None,
    ):
        self.config = config
        self.strategy_type = strategy
        self.backend_type = backend

        # Initialize storage
        if backend == StorageBackend.REDIS:
            self.storage: StorageBackendInterface = RedisStorage(redis_url)
        else:
            self.storage = MemoryStorage()

        # Initialize strategy
        self.strategy: RateLimitStrategyInterface = self._create_strategy(strategy)

    def _create_strategy(
        self, strategy_type: RateLimitStrategy
    ) -> RateLimitStrategyInterface:
        """Factory method to create strategy instance"""
        strategies = {
            RateLimitStrategy.TOKEN_BUCKET: TokenBucketStrategy(),
            RateLimitStrategy.SLIDING_WINDOW: SlidingWindowStrategy(),
            RateLimitStrategy.FIXED_WINDOW: FixedWindowStrategy(),
        }
        return strategies.get(strategy_type, SlidingWindowStrategy())

    def _generate_key(
        self,
        identifier: str,
        endpoint: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> str:
        """Generate unique rate limit key"""
        parts = [self.config.key_prefix]

        if identifier:
            parts.append(identifier)

        if endpoint:
            parts.append(endpoint)

        if user_id:
            parts.append(f"user:{user_id}")

        if ip_address:
            parts.append(f"ip:{ip_address}")

        # Hash to prevent key length issues
        key_string = ":".join(parts)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"rl:{key_hash}"

    def _extract_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxy headers"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def check(
        self,
        identifier: str,
        endpoint: str | None = None,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> RateLimitResult:
        """
        Check if request is allowed.

        Args:
            identifier: Unique identifier (e.g., "api", "auth", custom)
            endpoint: Endpoint path (optional)
            user_id: User ID (optional, if per_user=True)
            ip_address: IP address (optional, if per_ip=True)

        Returns:
            RateLimitResult with all metadata
        """
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                limit=self.config.limit,
                remaining=self.config.limit,
                reset_time=time.time() + self.config.window,
            )

        key = self._generate_key(identifier, endpoint, user_id, ip_address)

        try:
            result = await self.strategy.check(self.storage, key, self.config)
            return result
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}, failing open")
            # Fail open - allow request if rate limiter fails
            return RateLimitResult(
                allowed=True,
                limit=self.config.limit,
                remaining=self.config.limit,
                reset_time=time.time() + self.config.window,
                metadata={"error": str(e)},
            )

    async def reset(self, identifier: str, endpoint: str | None = None):
        """Reset rate limit for identifier"""
        key = self._generate_key(identifier, endpoint)
        await self.storage.delete(key)

    async def close(self):
        """Close storage connections"""
        if hasattr(self.storage, "close"):
            await self.storage.close()


# ============================================================================
# DECORATOR INTERFACE
# ============================================================================


def rate_limit(
    limit: int = 100,
    window: int = 60,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    backend: StorageBackend = StorageBackend.REDIS,
    key_func: Callable | None = None,
    per_user: bool = False,
    per_ip: bool = True,
):
    """
    Rate limiting decorator for FastAPI endpoints.

    Example:
        @rate_limit(limit=10, window=60)
        async def my_endpoint(request: Request):
            return {"message": "Hello"}

        @rate_limit(limit=5, window=60, per_user=True)
        async def protected_endpoint(request: Request, current_user: User):
            return {"message": "Protected"}
    """

    def decorator(func):
        # Create limiter instance
        config = RateLimitConfig(
            limit=limit,
            window=window,
            strategy=strategy,
            per_user=per_user,
            per_ip=per_ip,
        )
        limiter = UnifiedRateLimiter(config, strategy, backend)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            current_user = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                elif hasattr(arg, "id"):  # User-like object
                    current_user = arg

            if not request:
                # Try to get from kwargs
                request = kwargs.get("request")
                current_user = kwargs.get("current_user") or kwargs.get("user")

            if not request:
                # No request object, skip rate limiting
                return await func(*args, **kwargs)

            # Generate identifier
            if key_func:
                identifier = key_func(request, current_user, *args, **kwargs)
            else:
                identifier = func.__name__

            # Extract user_id and ip
            user_id = str(current_user.id) if (per_user and current_user) else None
            ip = limiter._extract_client_ip(request) if per_ip else None

            # Check rate limit
            result = await limiter.check(
                identifier=identifier,
                endpoint=request.url.path,
                user_id=user_id,
                ip_address=ip,
            )

            if not result.allowed:
                raise RateLimitExceeded(result)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# MIDDLEWARE INTERFACE
# ============================================================================


class RateLimitMiddleware:
    """
    ASGI middleware for rate limiting.

    Example:
        app = FastAPI()
        app.add_middleware(
            RateLimitMiddleware,
            default_config=RateLimitConfig(limit=100, window=60),
        )
    """

    def __init__(
        self,
        app,
        default_config: RateLimitConfig | None = None,
        endpoint_configs: dict[str, RateLimitConfig] | None = None,
    ):
        self.app = app
        self.default_config = default_config or RateLimitConfig()
        self.endpoint_configs = endpoint_configs or {}
        self._limiters: dict[str, UnifiedRateLimiter] = {}

    async def __call__(self, scope, receive, send):
        """ASGI middleware entry point"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Skip rate limiting for certain paths
        if self._should_skip(scope["path"]):
            await self.app(scope, receive, send)
            return

        # Create request object
        request = Request(scope, receive)

        # Get config for this endpoint
        config = self._get_config_for_path(request.url.path)

        # Get or create limiter
        limiter_key = f"{config.strategy.value}:{config.limit}:{config.window}"
        if limiter_key not in self._limiters:
            self._limiters[limiter_key] = UnifiedRateLimiter(
                config=config,
                strategy=config.strategy,
            )

        limiter = self._limiters[limiter_key]

        # Check rate limit
        ip = limiter._extract_client_ip(request)
        result = await limiter.check(
            identifier="middleware",
            endpoint=request.url.path,
            ip_address=ip,
        )

        if not result.allowed:
            # Send 429 response
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", **result.to_dict()},
                headers=result.to_headers(),
            )
            await response(scope, receive, send)
            return

        # Wrap send to add rate limit headers
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in result.to_headers().items():
                    headers.append((key.encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting"""
        skip_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        ]
        return any(path.startswith(p) for p in skip_paths)

    def _get_config_for_path(self, path: str) -> RateLimitConfig:
        """Get rate limit config for path"""
        # Direct match
        if path in self.endpoint_configs:
            return self.endpoint_configs[path]

        # Prefix match
        for pattern, config in self.endpoint_configs.items():
            if pattern.endswith("*") and path.startswith(pattern[:-1]):
                return config

        return self.default_config


# ============================================================================
# PRESETS
# ============================================================================

# Common presets for quick use
DEFAULT = RateLimitConfig(limit=100, window=60)
STRICT = RateLimitConfig(limit=10, window=60)
LENIENT = RateLimitConfig(limit=1000, window=60)
AUTH = RateLimitConfig(limit=5, window=300)
API = RateLimitConfig(limit=1000, window=60)


# ============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================================================

# Alias for UnifiedRateLimiter (old name)
RateLimiter = UnifiedRateLimiter


# Alias for rate_limit decorator (was used in old imports)
# These are kept for backward compatibility with existing code
def check_rate_limit(
    identifier: str, limit: int = 100, window: int = 60
) -> tuple[bool, str | None, dict]:
    """
    Backward compatibility wrapper for old check_rate_limit function.

    Deprecated: Use UnifiedRateLimiter.check() instead.
    """
    import asyncio

    limiter = UnifiedRateLimiter(
        config=RateLimitConfig(limit=limit, window=window),
        backend=StorageBackend.MEMORY,  # Use memory backend for sync compatibility
    )

    # Run async function in sync context
    result = asyncio.get_event_loop().run_until_complete(
        limiter.check(identifier=identifier)
    )

    if result.allowed:
        return True, None, {"remaining": result.remaining, "limit": result.limit}
    else:
        return (
            False,
            f"Rate limit exceeded: {result.retry_after}s",
            {"retry_after": result.retry_after},
        )


# Legacy class name for middleware
RateLimitMiddleware = RateLimitMiddleware
