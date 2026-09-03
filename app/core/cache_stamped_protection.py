"""
Cache Stampede Protection Module

Prevents cache stampede (also known as cache thundering herd) where multiple
concurrent requests miss the cache and all try to regenerate the same expensive
operation simultaneously.

Uses Redis-based distributed locks to ensure only one request regenerates
the cache while others wait for the result.

Usage:
    result = await cache_stampede_protect(
        cache_key="expensive_operation:123",
        generator=lambda: expensive_computation(),
        expire=3600
    )
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheStampedeProtector:
    """
    Protects against cache stampede using request coalescing.

    When multiple concurrent requests miss the cache:
    1. First request acquires a lock and generates the data
    2. Other requests wait for the lock or poll for the result
    3. All requests return the same cached data
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the cache stampede protector.

        Args:
            redis_client: Optional Redis client (creates one if not provided)
        """
        self._redis_client: Optional[redis.Redis] = None
        self._provided_client = redis_client
        self._init_lock = asyncio.Lock()

    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client with lazy initialization."""
        if self._redis_client is None:
            async with self._init_lock:
                if self._redis_client is None:
                    if self._provided_client:
                        self._redis_client = self._provided_client
                    else:
                        try:
                            self._redis_client = await redis.from_url(
                                settings.REDIS_URL, health_check_interval=30
                            )
                            logger.info("Cache stampede protector connected to Redis")
                        except Exception as e:
                            logger.error(f"Failed to connect to Redis: {e}")
                            raise
        return self._redis_client

    async def protect(
        self,
        cache_key: str,
        generator: Callable,
        expire: int = 3600,
        lock_timeout: int = 30,
        wait_timeout: int = 10,
        poll_interval: float = 0.1,
    ) -> Any:
        """
        Execute a generator with cache stampede protection.

        Args:
            cache_key: Cache key to store/retrieve result
            generator: Async callable that generates the data
            expire: Cache expiry time in seconds
            lock_timeout: Maximum time to hold the generation lock (seconds)
            wait_timeout: Maximum time to wait for another request to finish (seconds)
            poll_interval: How often to check if cache is populated (seconds)

        Returns:
            The generated or cached data

        Raises:
            TimeoutError: If generation locks exceed timeouts
            Exception: If generator raises an exception
        """
        redis_client = await self._get_redis_client()

        # Try to get from cache first
        cached = await redis_client.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for key: {cache_key}")
            # Deserialize if it's JSON (you may need to adjust based on your cache format)
            import json

            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                return cached

        # Cache miss - check if another request is generating
        lock_key = f"lock:{cache_key}"
        being_generated_key = f"generating:{cache_key}"

        # Try to acquire lock
        lock_acquired = await redis_client.set(
            lock_key,
            "1",
            nx=True,  # Only set if not exists
            ex=lock_timeout,  # Auto-release after timeout
        )

        if lock_acquired:
            # This request will generate the data
            logger.info(f"Acquired generation lock for key: {cache_key}")
            try:
                # Mark that we're generating (for other requests to poll)
                await redis_client.setex(being_generated_key, lock_timeout, "1")

                # Generate the data
                start_time = time.time()
                result = await generator()
                generation_time = time.time() - start_time

                logger.info(
                    f"Generated data for key: {cache_key} in {generation_time:.2f}s"
                )

                # Cache the result
                import json

                try:
                    serialized = json.dumps(result)
                    await redis_client.setex(cache_key, expire, serialized)
                except (TypeError, ValueError):
                    # If not JSON serializable, store as-is
                    await redis_client.setex(cache_key, expire, result)

                # Clean up locks
                await redis_client.delete(lock_key, being_generated_key)

                return result

            except Exception as e:
                logger.error(f"Error generating data for key {cache_key}: {e}")
                # Clean up locks on error
                await redis_client.delete(lock_key, being_generated_key)
                raise

        else:
            # Another request is generating - wait for it
            logger.info(f"Waiting for generation of key: {cache_key}")
            start_wait = time.time()

            while time.time() - start_wait < wait_timeout:
                # Check if cache is now populated
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info(f"Cached data available for key: {cache_key}")
                    try:
                        import json

                        return json.loads(cached)
                    except (json.JSONDecodeError, TypeError):
                        return cached

                # Check if generation is still happening
                is_generating = await redis_client.exists(being_generated_key)
                if not is_generating:
                    # Generation failed or completed without caching
                    logger.warning(f"Generation failed for key: {cache_key}")
                    break

                # Wait a bit before polling again
                await asyncio.sleep(poll_interval)

            # Timeout - fall back to generating ourselves
            logger.warning(
                f"Timeout waiting for cache generation of key: {cache_key}, "
                f"generating ourselves"
            )
            result = await generator()
            return result

    async def invalidate(self, cache_key: str) -> None:
        """
        Invalidate a cache key and clean up associated lock keys.

        Args:
            cache_key: Cache key to invalidate
        """
        redis_client = await self._get_redis_client()

        # Delete the cache key, lock key, and being_generated key
        keys_to_delete = [
            cache_key,
            f"lock:{cache_key}",
            f"generating:{cache_key}",
        ]

        await redis_client.delete(*keys_to_delete)
        logger.info(f"Invalidated cache key and associated locks: {cache_key}")

    async def close(self):
        """Close Redis connection if we created it."""
        if self._redis_client and not self._provided_client:
            await self._redis_client.close()
            self._redis_client = None


# Global singleton instance
_protector: Optional[CacheStampedeProtector] = None
_protector_lock = asyncio.Lock()


async def get_cache_protector() -> CacheStampedeProtector:
    """Get global cache stampede protector instance (thread-safe singleton)."""
    global _protector
    if _protector is None:
        async with _protector_lock:
            if _protector is None:
                _protector = CacheStampedeProtector()
    return _protector


# Convenience function for quick usage
async def cache_stampede_protect(
    cache_key: str,
    generator: Callable,
    expire: int = 3600,
    lock_timeout: int = 30,
    wait_timeout: int = 10,
) -> Any:
    """
    Convenience function for cache stampede protection.

    Args:
        cache_key: Cache key to store/retrieve result
        generator: Async callable that generates the data
        expire: Cache expiry time in seconds
        lock_timeout: Maximum time to hold the generation lock
        wait_timeout: Maximum time to wait for another request to finish

    Returns:
        The generated or cached data

    Example:
        result = await cache_stampede_protect(
            cache_key="team_insights:123",
            generator=lambda: generate_expensive_insights(team_id=123),
            expire=86400  # 24 hours
        )
    """
    protector = await get_cache_protector()
    return await protector.protect(
        cache_key=cache_key,
        generator=generator,
        expire=expire,
        lock_timeout=lock_timeout,
        wait_timeout=wait_timeout,
    )
