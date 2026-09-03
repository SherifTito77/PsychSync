# app/core/enhanced_cache.py
"""
Enhanced Redis Caching Strategy with Multiple Cache Patterns
- LRU Cache for frequently accessed data
- Write-through cache for data consistency
- Cache invalidation strategies
- Distributed cache locks
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheKey:
    """Standardized cache key generation"""

    @staticmethod
    def user(user_id: str, data_type: str) -> str:
        return f"user:{user_id}:{data_type}"

    @staticmethod
    def team(team_id: str, data_type: str) -> str:
        return f"team:{team_id}:{data_type}"

    @staticmethod
    def assessment(assessment_id: str, data_type: str) -> str:
        return f"assessment:{assessment_id}:{data_type}"

    @staticmethod
    def api_response(endpoint: str, params: dict = None) -> str:
        param_hash = hashlib.md5(
            json.dumps(params or {}, sort_keys=True).encode()
        ).hexdigest()
        return f"api:{endpoint}:{param_hash}"

    @staticmethod
    def session(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def rate_limit(identifier: str, window: str) -> str:
        return f"rate_limit:{identifier}:{window}"


class EnhancedCacheManager:
    """
    Enhanced cache manager with multiple caching strategies
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = settings.CACHE_DEFAULT_EXPIRE
        self.user_ttl = settings.CACHE_USER_EXPIRE
        self.assessment_ttl = settings.CACHE_ASSESSMENT_EXPIRE
        self.team_ttl = settings.CACHE_TEAM_EXPIRE

        # Cache configuration
        self.max_retries = 3
        self.retry_delay = 0.1

    async def get(self, key: str) -> Any | None:
        """Get value from cache with error handling"""
        try:
            for attempt in range(self.max_retries):
                try:
                    value = await self.redis.get(key)
                    if value:
                        # Try to deserialize as JSON first, then pickle
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            try:
                                return pickle.loads(value)
                            except (pickle.PickleError, TypeError):
                                return value.decode("utf-8")
                    return None
                except redis.ConnectionError as e:
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"Cache connection failed after {self.max_retries} attempts: {e}"
                        )
                        return None
                    await asyncio.sleep(self.retry_delay * (2**attempt))
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        serialize_as: str = "json",  # "json" or "pickle"
    ) -> bool:
        """Set value in cache with error handling"""
        try:
            # Serialize value
            if serialize_as == "json":
                try:
                    serialized = json.dumps(value, default=str)
                except (TypeError, ValueError):
                    # Fallback to pickle if JSON fails
                    serialized = pickle.dumps(value)
                    serialize_as = "pickle"
            else:
                serialized = pickle.dumps(value)

            # Set with TTL
            ttl = ttl or self.default_ttl
            for attempt in range(self.max_retries):
                try:
                    result = await self.redis.setex(key, ttl, serialized)
                    return result
                except redis.ConnectionError as e:
                    if attempt == self.max_retries - 1:
                        logger.error(
                            f"Cache connection failed after {self.max_retries} attempts: {e}"
                        )
                        return False
                    await asyncio.sleep(self.retry_delay * (2**attempt))
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                result = await self.redis.delete(*keys)
                return result
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def increment(
        self, key: str, amount: int = 1, ttl: int | None = None
    ) -> int | None:
        """Increment counter in cache"""
        try:
            pipe = self.redis.pipeline()
            pipe.incrby(key, amount)
            if ttl:
                pipe.expire(key, ttl)
            result = await pipe.execute()
            return result[0]
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None

    # Cache invalidation methods
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a user"""
        pattern = f"user:{user_id}:*"
        return await self.delete_pattern(pattern)

    async def invalidate_team_cache(self, team_id: str) -> int:
        """Invalidate all cache entries for a team"""
        pattern = f"team:{team_id}:*"
        return await self.delete_pattern(pattern)

    async def invalidate_assessment_cache(self, assessment_id: str) -> int:
        """Invalidate all cache entries for an assessment"""
        pattern = f"assessment:{assessment_id}:*"
        return await self.delete_pattern(pattern)


class CacheDecorator:
    """
    Decorators for caching function results
    """

    def __init__(self, cache_manager: EnhancedCacheManager):
        self.cache = cache_manager

    def cache_result(
        self,
        key_prefix: str,
        ttl: int | None = None,
        serialize_as: str = "json",
        cache_key_func: Callable | None = None,
    ):
        """
        Cache function result decorator

        Args:
            key_prefix: Cache key prefix
            ttl: Time to live in seconds
            serialize_as: Serialization method ('json' or 'pickle')
            cache_key_func: Function to generate custom cache key
        """

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    # Default key generation
                    key_parts = [key_prefix]
                    # Add positional args (skip self and db session)
                    for arg in args[2:]:  # Skip self and db session
                        if hasattr(arg, "id"):
                            key_parts.append(str(arg.id))
                        elif isinstance(arg, (str, int, float)):
                            key_parts.append(str(arg))
                    # Add keyword args
                    for k, v in sorted(kwargs.items()):
                        if k != "db" and hasattr(v, "id"):
                            key_parts.append(f"{k}:{v.id}")
                        elif k != "db" and isinstance(v, (str, int, float)):
                            key_parts.append(f"{k}:{v}")

                    cache_key = ":".join(key_parts)

                # Try to get from cache
                cached_result = await self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await self.cache.set(cache_key, result, ttl, serialize_as)

                return result

            return wrapper

        return decorator

    def cache_user_data(self, data_type: str, ttl: int | None = None):
        """Cache user-specific data"""
        return self.cache_result(
            key_prefix=f"user_data:{data_type}",
            ttl=ttl or settings.CACHE_USER_EXPIRE,
            cache_key_func=lambda self, db, user_id, *args, **kwargs: CacheKey.user(
                user_id, data_type
            ),
        )

    def cache_team_data(self, data_type: str, ttl: int | None = None):
        """Cache team-specific data"""
        return self.cache_result(
            key_prefix=f"team_data:{data_type}",
            ttl=ttl or settings.CACHE_TEAM_EXPIRE,
            cache_key_func=lambda self, db, team_id, *args, **kwargs: CacheKey.team(
                team_id, data_type
            ),
        )

    def cache_assessment_data(self, data_type: str, ttl: int | None = None):
        """Cache assessment-specific data"""
        return self.cache_result(
            key_prefix=f"assessment_data:{data_type}",
            ttl=ttl or settings.CACHE_ASSESSMENT_EXPIRE,
            cache_key_func=lambda self, db, assessment_id, *args, **kwargs: CacheKey.assessment(
                assessment_id, data_type
            ),
        )


class RateLimiter:
    """
    Redis-based rate limiter with sliding window
    """

    def __init__(self, cache_manager: EnhancedCacheManager):
        self.cache = cache_manager

    async def is_allowed(
        self, identifier: str, limit: int, window: int, window_unit: str = "seconds"
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if request is allowed based on rate limit

        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            limit: Maximum number of requests
            window: Time window
            window_unit: "seconds", "minutes", "hours"

        Returns:
            (allowed, info_dict) where info_dict contains:
            - remaining: Remaining requests
            - reset_time: When the limit resets
            - total: Total limit
        """
        # Convert window to seconds
        window_seconds = window
        if window_unit == "minutes":
            window_seconds = window * 60
        elif window_unit == "hours":
            window_seconds = window * 3600

        current_time = int(time.time())
        window_start = current_time - window_seconds

        # Use sorted set for sliding window
        key = CacheKey.rate_limit(identifier, f"{window}{window_unit[0]}")

        try:
            # Remove old entries
            await self.cache.redis.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_requests = await self.cache.redis.zcard(key)

            # Check if over limit
            if current_requests >= limit:
                # Get oldest request to calculate reset time
                oldest = await self.cache.redis.zrange(key, 0, 0, withscores=True)
                reset_time = (
                    int(oldest[0][1]) + window_seconds
                    if oldest
                    else current_time + window_seconds
                )

                return False, {
                    "remaining": 0,
                    "reset_time": reset_time,
                    "total": limit,
                    "current": current_requests,
                }

            # Add current request
            await self.cache.redis.zadd(key, {str(current_time): current_time})
            await self.cache.redis.expire(key, window_seconds)

            remaining = limit - current_requests - 1
            reset_time = current_time + window_seconds

            return True, {
                "remaining": max(0, remaining),
                "reset_time": reset_time,
                "total": limit,
                "current": current_requests + 1,
            }

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {
                "remaining": limit - 1,
                "reset_time": current_time + window_seconds,
                "total": limit,
                "current": 1,
            }


# Global cache instance
_cache_manager: EnhancedCacheManager | None = None
_cache_decorator: CacheDecorator | None = None
_rate_limiter: RateLimiter | None = None

# Cache statistics for performance monitoring
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "hit_ratio": 0.0,
    "target_hit_ratio": 80.0,
}


def get_cache_manager() -> EnhancedCacheManager:
    """Get global cache manager instance"""
    return _cache_manager


def get_cache_decorator() -> CacheDecorator:
    """Get global cache decorator instance"""
    return _cache_decorator


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter


async def init_cache(redis_client: Redis):
    """Initialize cache manager"""
    global _cache_manager, _cache_decorator, _rate_limiter

    _cache_manager = EnhancedCacheManager(redis_client)
    _cache_decorator = CacheDecorator(_cache_manager)
    _rate_limiter = RateLimiter(_cache_manager)

    logger.info("Enhanced cache manager initialized")


# Cache utility functions
async def cache_user_profile(user_id: str, profile_data: dict):
    """Cache user profile data"""
    cache = get_cache_manager()
    if cache:
        await cache.set(CacheKey.user(user_id, "profile"), profile_data, cache.user_ttl)


async def get_cached_user_profile(user_id: str) -> dict | None:
    """Get cached user profile data"""
    cache = get_cache_manager()
    if cache:
        return await cache.get(CacheKey.user(user_id, "profile"))
    return None


async def invalidate_user_cache(user_id: str):
    """Invalidate all user cache entries"""
    cache = get_cache_manager()
    if cache:
        await cache.invalidate_user_cache(user_id)
