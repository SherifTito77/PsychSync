# app/core/cache_advanced.py
"""
Advanced Redis caching strategies for PsychSync
Multi-layer caching with intelligent invalidation, cache warming, and performance monitoring
"""

import json
import pickle
import hashlib
import time
import logging
from typing import Any, Optional, Dict, List, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from app.core.config import settings
from app.core.constants import CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

class CacheMetrics:
    """Advanced cache performance metrics"""

    def __init__(self):
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_response_time': 0.0,
            'keys_by_type': {},
            'slow_operations': [],
        }

    def record_hit(self, key_type: str = 'unknown', response_time: float = 0.0):
        self.stats['hits'] += 1
        self.stats['total_response_time'] += response_time
        self.stats['keys_by_type'][key_type] = self.stats['keys_by_type'].get(key_type, 0) + 1

    def record_miss(self, key_type: str = 'unknown'):
        self.stats['misses'] += 1
        self.stats['keys_by_type'][key_type] = self.stats['keys_by_type'].get(key_type, 0) + 1

    def record_set(self, key_type: str = 'unknown'):
        self.stats['sets'] += 1
        self.stats['keys_by_type'][key_type] = self.stats['keys_by_type'].get(key_type, 0) + 1

    def record_delete(self):
        self.stats['deletes'] += 1

    def record_error(self):
        self.stats['errors'] += 1

    def record_slow_operation(self, operation: str, duration: float):
        self.stats['slow_operations'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        })

    def get_hit_ratio(self) -> float:
        total = self.stats['hits'] + self.stats['misses']
        return (self.stats['hits'] / total * 100) if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            'hit_ratio': self.get_hit_ratio(),
            'avg_response_time': (
                self.stats['total_response_time'] / self.stats['hits']
                if self.stats['hits'] > 0 else 0.0
            )
        }

class AdvancedCache:
    """Advanced Redis caching with multiple strategies"""

    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.metrics = CacheMetrics()
        self.local_cache: Dict[str, Any] = {}  # L1 cache (memory)
        self.local_cache_max_size = 1000
        self.cache_warmers: Dict[str, Callable] = {}

    async def connect(self):
        """Initialize Redis connection with optimized settings"""
        try:
            self.redis_client = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=50
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Advanced cache connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None

    async def disconnect(self):
        """Gracefully close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Advanced cache disconnected")

    def _generate_cache_key(self, prefix: str, identifier: str, version: str = "v1") -> str:
        """Generate structured cache key with versioning"""
        return f"{CacheKeys.get_user_key(identifier) if prefix == CacheKeys.USER else f"{prefix}:{identifier}"}:{version}"

    def _get_local_cache_key(self, key: str) -> str:
        """Generate local cache key"""
        return f"local:{key}"

    def _is_local_cache_valid(self, data: Dict[str, Any]) -> bool:
        """Check if local cache data is still valid"""
        if not data or 'expires_at' not in data:
            return False
        return datetime.utcnow() < datetime.fromisoformat(data['expires_at'])

    async def get(
        self,
        key: str,
        use_fallback: bool = True,
        default: Any = None
    ) -> Optional[Any]:
        """
        Get value from cache with multi-layer strategy (L1: Memory, L2: Redis)
        """
        start_time = time.time()
        key_type = key.split(':')[0] if ':' in key else 'unknown'

        try:
            # L1 Cache (Memory) - fastest
            local_key = self._get_local_cache_key(key)
            if local_key in self.local_cache:
                local_data = self.local_cache[local_key]
                if self._is_local_cache_valid(local_data):
                    response_time = time.time() - start_time
                    self.metrics.record_hit(key_type, response_time)
                    return local_data['value']
                else:
                    # Remove expired local cache
                    del self.local_cache[local_key]

            # L2 Cache (Redis) - fast
            if self.redis_client:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    try:
                        data = json.loads(cached_data)

                        # Update L1 cache
                        self._update_local_cache(local_key, data)

                        response_time = time.time() - start_time
                        self.metrics.record_hit(key_type, response_time)
                        return data
                    except json.JSONDecodeError:
                        # Fallback to raw value
                        self._update_local_cache(local_key, {'value': cached_data})
                        response_time = time.time() - start_time
                        self.metrics.record_hit(key_type, response_time)
                        return cached_data

            # Cache miss
            self.metrics.record_miss(key_type)

            # Try cache warmer if available
            if use_fallback and key in self.cache_warmers:
                return await self._warm_cache(key)

            return default

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            self.metrics.record_error()
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = CacheTTL.MEDIUM,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Set value in cache with intelligent invalidation"""
        key_type = key.split(':')[0] if ':' in key else 'unknown'

        try:
            # Prepare data with metadata
            cache_data = {
                'value': value,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(seconds=ttl)).isoformat(),
                'tags': tags or [],
                'version': 'v1'
            }

            # Set in L2 Cache (Redis)
            if self.redis_client:
                serialized_data = json.dumps(cache_data, default=str)
                await self.redis_client.setex(key, ttl, serialized_data)

                # Set tags for cache invalidation
                if tags:
                    for tag in tags:
                        tag_key = f"tag:{tag}"
                        await self.redis_client.sadd(tag_key, key)
                        await self.redis_client.expire(tag_key, ttl)

            # Update L1 Cache (Memory)
            local_key = self._get_local_cache_key(key)
            self._update_local_cache(local_key, cache_data)

            self.metrics.record_set(key_type)
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            self.metrics.record_error()
            return False

    def _update_local_cache(self, key: str, data: Dict[str, Any]):
        """Update local cache with LRU eviction"""
        # Remove oldest item if cache is full
        if len(self.local_cache) >= self.local_cache_max_size:
            oldest_key = next(iter(self.local_cache))
            del self.local_cache[oldest_key]

        self.local_cache[key] = data

    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers"""
        try:
            # Delete from L2 Cache (Redis)
            if self.redis_client:
                await self.redis_client.delete(key)

            # Delete from L1 Cache (Memory)
            local_key = self._get_local_cache_key(key)
            if local_key in self.local_cache:
                del self.local_cache[local_key]

            self.metrics.record_delete()
            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            self.metrics.record_error()
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with specific tag"""
        try:
            if not self.redis_client:
                return 0

            tag_key = f"tag:{tag}"
            keys_to_delete = await self.redis_client.smembers(tag_key)

            if keys_to_delete:
                # Delete from Redis
                await self.redis_client.delete(*keys_to_delete)
                await self.redis_client.delete(tag_key)

                # Remove from local cache
                for key in keys_to_delete:
                    local_key = self._get_local_cache_key(key)
                    if local_key in self.local_cache:
                        del self.local_cache[local_key]

                logger.info(f"Invalidated {len(keys_to_delete)} cache entries for tag: {tag}")
                return len(keys_to_delete)

            return 0

        except Exception as e:
            logger.error(f"Cache invalidation error for tag {tag}: {str(e)}")
            return 0

    async def clear_all(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                await self.redis_client.flushdb()
            self.local_cache.clear()
            logger.info("All cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False

    def register_cache_warmer(self, key_pattern: str, warmer_func: Callable):
        """Register a cache warming function for a key pattern"""
        self.cache_warmers[key_pattern] = warmer_func

    async def _warm_cache(self, key: str) -> Optional[Any]:
        """Warm cache using registered warmer function"""
        for pattern, warmer in self.cache_warmers.items():
            if pattern in key or key.startswith(pattern):
                try:
                    result = await warmer(key)
                    if result is not None:
                        await self.set(key, result, ttl=CacheTTL.LONG)
                        return result
                except Exception as e:
                    logger.error(f"Cache warmer error for {key}: {str(e)}")
        return None

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        redis_info = {}

        if self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_info = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'redis_hit_ratio': (
                        (info.get('keyspace_hits', 0) /
                        (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1))) * 100
                    )
                }
            except Exception as e:
                logger.error(f"Error getting Redis info: {str(e)}")

        return {
            'local_cache_size': len(self.local_cache),
            'local_cache_max_size': self.local_cache_max_size,
            'registered_warmers': len(self.cache_warmers),
            'metrics': self.metrics.get_stats(),
            'redis_info': redis_info
        }

# Global advanced cache instance
advanced_cache = AdvancedCache()

# Advanced caching decorators
def advanced_cache(
    key_prefix: str,
    ttl: int = CacheTTL.MEDIUM,
    tags: Optional[List[str]] = None,
    use_user_context: bool = False,
    cache_on_error: bool = False
):
    """
    Advanced caching decorator with intelligent invalidation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key_from_func(
                func, key_prefix, args, kwargs, use_user_context
            )

            # Try to get from cache
            cached_result = await advanced_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            try:
                result = await func(*args, **kwargs)

                # Cache successful result
                await advanced_cache.set(cache_key, result, ttl, tags)
                return result

            except Exception as e:
                # Optionally cache error results
                if cache_on_error:
                    error_data = {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    await advanced_cache.set(f"{cache_key}:error", error_data, ttl=CacheTTL.SHORT)
                raise

        return wrapper
    return decorator

def _generate_cache_key_from_func(
    func: Callable,
    key_prefix: str,
    args: tuple,
    kwargs: dict,
    use_user_context: bool = False
) -> str:
    """Generate cache key from function call"""
    # Create a hash of function parameters
    params = {
        'args': args[1:] if use_user_context else args,  # Skip self/cls if present
        'kwargs': sorted(kwargs.items())
    }

    params_str = json.dumps(params, sort_keys=True, default=str)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

    return f"{key_prefix}:{func.__name__}:{params_hash}"

class CacheWarmer:
    """Automatic cache warming for frequently accessed data"""

    def __init__(self, cache_instance: AdvancedCache):
        self.cache = cache_instance
        self.warmup_jobs: List[Dict[str, Any]] = []

    def register_warmup_job(
        self,
        name: str,
        warmer_func: Callable,
        schedule: str = "0 */5 * * * *",  # Every 5 minutes
        key_patterns: List[str] = None
    ):
        """Register a cache warming job"""
        self.warmup_jobs.append({
            'name': name,
            'func': warmer_func,
            'schedule': schedule,
            'key_patterns': key_patterns or [],
            'last_run': None,
            'run_count': 0
        })

    async def run_warmup_job(self, job_name: str):
        """Run a specific cache warming job"""
        job = next((j for j in self.warmup_jobs if j['name'] == job_name), None)
        if not job:
            logger.error(f"Warmup job not found: {job_name}")
            return

        try:
            start_time = time.time()
            result = await job['func']()
            duration = time.time() - start_time

            job['last_run'] = datetime.utcnow()
            job['run_count'] += 1

            logger.info(f"Warmup job '{job_name}' completed in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Warmup job '{job_name}' failed: {str(e)}")

# Initialize cache warmer
cache_warmer = CacheWarmer(advanced_cache)

# Cache utility functions
async def invalidate_user_cache(user_id: str):
    """Invalidate all cache entries for a specific user"""
    patterns = [
        f"user:{user_id}:*",
        f"session:{user_id}:*",
        f"permissions:{user_id}:*"
    ]

    total_invalidated = 0
    for pattern in patterns:
        try:
            if advanced_cache.redis_client:
                keys = await advanced_cache.redis_client.keys(pattern)
                if keys:
                    await advanced_cache.redis_client.delete(*keys)
                    total_invalidated += len(keys)

                    # Remove from local cache
                    for key in keys:
                        local_key = advanced_cache._get_local_cache_key(key)
                        if local_key in advanced_cache.local_cache:
                            del advanced_cache.local_cache[local_key]

        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {str(e)}")

    logger.info(f"Invalidated {total_invalidated} cache entries for user {user_id}")
    return total_invalidated

async def cache_heartbeat():
    """Periodic cache maintenance and health check"""
    try:
        if advanced_cache.redis_client:
            # Check Redis connection
            await advanced_cache.redis_client.ping()

            # Clean up expired local cache entries
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, data in advanced_cache.local_cache.items()
                if 'expires_at' in data and
                datetime.fromisoformat(data['expires_at']) < current_time
            ]

            for key in expired_keys:
                del advanced_cache.local_cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired local cache entries")

    except Exception as e:
        logger.error(f"Cache heartbeat error: {str(e)}")

# Initialize advanced cache
async def init_advanced_cache():
    """Initialize advanced caching system"""
    await advanced_cache.connect()
    logger.info("Advanced cache system initialized")