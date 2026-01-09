# app/performance/cache_manager.py

"""
ENTERPRISE CACHE MANAGER
High-performance caching system with multiple backends and strategies

CACHE MANAGER FEATURES:
- Multi-level caching (L1: Memory, L2: Redis)
- Cache invalidation strategies
- Performance monitoring
- Automatic cache warming
- Intelligent cache sizing
- Cache hit ratio optimization

Author: Security Team
Version: 2.0 Enterprise Security
"""

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import logging
import pickle
import threading
import time
from typing import Any

# Initialize cache logger
cache_logger = logging.getLogger("app.performance.cache")


class CacheStrategy(Enum):
    """Cache eviction strategies"""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


class CacheLevel(Enum):
    """Cache levels"""

    MEMORY = "memory"
    REDIS = "redis"
    DISTRIBUTED = "distributed"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: float | None = None
    size_bytes: int = 0
    tags: list[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    def touch(self):
        """Update access statistics"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheBackend(ABC):
    """Abstract cache backend interface"""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry | None:
        """Get cache entry"""

    @abstractmethod
    async def set(self, entry: CacheEntry) -> bool:
        """Set cache entry"""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cache entry"""

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""

    @abstractmethod
    async def size(self) -> int:
        """Get cache size"""


class MemoryCache(CacheBackend):
    """In-memory cache backend with LRU eviction"""

    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.LRU):
        self.max_size = max_size
        self.strategy = strategy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "evictions": 0}

    async def get(self, key: str) -> CacheEntry | None:
        """Get entry from memory cache"""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Update access statistics
            entry.touch()

            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)

            self._stats["hits"] += 1
            return entry

    async def set(self, entry: CacheEntry) -> bool:
        """Set entry in memory cache"""
        with self._lock:
            try:
                # Calculate size
                if entry.size_bytes == 0:
                    entry.size_bytes = len(pickle.dumps(entry.value))

                # Evict if necessary
                while len(self._cache) >= self.max_size and entry.key not in self._cache:
                    await self._evict_one()

                self._cache[entry.key] = entry
                self._stats["sets"] += 1
                return True

            except Exception as e:
                cache_logger.error(f"Memory cache set error: {e}")
                return False

    async def delete(self, key: str) -> bool:
        """Delete entry from memory cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

    async def clear(self) -> bool:
        """Clear memory cache"""
        with self._lock:
            self._cache.clear()
            return True

    async def size(self) -> int:
        """Get memory cache size"""
        return len(self._cache)

    async def _evict_one(self):
        """Evict one entry based on strategy"""
        if not self._cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Remove oldest (first) item
            self._cache.popitem(last=False)
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            least_used_key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
            del self._cache[least_used_key]
        elif self.strategy == CacheStrategy.FIFO:
            # Remove first inserted
            self._cache.popitem(last=False)

        self._stats["evictions"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get memory cache statistics"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_ratio = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_ratio": round(hit_ratio, 4),
                "total_requests": total_requests,
            }


class RedisCache(CacheBackend):
    """Redis cache backend for distributed caching"""

    def __init__(self, redis_client, key_prefix: str = "psychsync:cache:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}

    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> CacheEntry | None:
        """Get entry from Redis"""
        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)

            if data is None:
                self._stats["misses"] += 1
                return None

            entry_data = pickle.loads(data)
            entry = CacheEntry(**entry_data)

            # Check expiration
            if entry.is_expired():
                await self.delete(key)
                self._stats["misses"] += 1
                return None

            entry.touch()
            self._stats["hits"] += 1
            return entry

        except Exception as e:
            cache_logger.error(f"Redis cache get error: {e}")
            self._stats["errors"] += 1
            return None

    async def set(self, entry: CacheEntry) -> bool:
        """Set entry in Redis"""
        try:
            redis_key = self._make_key(entry.key)
            data = pickle.dumps(entry.__dict__)

            # Set TTL if specified
            ttl_seconds = int(entry.ttl) if entry.ttl else None

            if ttl_seconds:
                await self.redis.setex(redis_key, ttl_seconds, data)
            else:
                await self.redis.set(redis_key, data)

            self._stats["sets"] += 1
            return True

        except Exception as e:
            cache_logger.error(f"Redis cache set error: {e}")
            self._stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from Redis"""
        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)

            if result:
                self._stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            cache_logger.error(f"Redis cache delete error: {e}")
            self._stats["errors"] += 1
            return False

    async def clear(self) -> bool:
        """Clear all cache entries with prefix"""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)

            if keys:
                await self.redis.delete(*keys)

            return True

        except Exception as e:
            cache_logger.error(f"Redis cache clear error: {e}")
            self._stats["errors"] += 1
            return False

    async def size(self) -> int:
        """Get Redis cache size"""
        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis.keys(pattern)
            return len(keys)

        except Exception as e:
            cache_logger.error(f"Redis cache size error: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Get Redis cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_ratio = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {**self._stats, "hit_ratio": round(hit_ratio, 4), "total_requests": total_requests}


class CacheManager:
    """
    Enterprise cache manager with multi-level caching and intelligent strategies
    """

    def __init__(
        self,
        l1_cache: CacheBackend | None = None,
        l2_cache: CacheBackend | None = None,
        enable_l1: bool = True,
        enable_l2: bool = True,
    ):
        self.enable_l1 = enable_l1
        self.enable_l2 = enable_l2

        # Initialize cache backends
        self.l1_cache = l1_cache or MemoryCache()
        self.l2_cache = l2_cache

        # Tag-based invalidation
        self._tag_mappings: dict[str, list[str]] = {}

        # Performance monitoring
        self._performance_stats = {
            "total_requests": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "cache_writes": 0,
            "cache_invalidations": 0,
        }

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = {"args": args, "kwargs": sorted(kwargs.items())}
        key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Any | None:
        """Get value from cache (L1, then L2)"""
        self._performance_stats["total_requests"] += 1

        try:
            # Try L1 cache first
            if self.enable_l1:
                l1_entry = await self.l1_cache.get(key)
                if l1_entry and not l1_entry.is_expired():
                    self._performance_stats["l1_hits"] += 1
                    return l1_entry.value

            # Try L2 cache
            if self.enable_l2 and self.l2_cache:
                l2_entry = await self.l2_cache.get(key)
                if l2_entry and not l2_entry.is_expired():
                    self._performance_stats["l2_hits"] += 1

                    # Promote to L1 cache
                    if self.enable_l1:
                        await self.l1_cache.set(l2_entry)

                    return l2_entry.value

            # Cache miss
            self._performance_stats["misses"] += 1
            return None

        except Exception as e:
            cache_logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self, key: str, value: Any, ttl: float | None = None, tags: list[str] | None = None
    ) -> bool:
        """Set value in cache (both L1 and L2)"""
        try:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl,
                tags=tags or [],
            )

            # Set in L1 cache
            if self.enable_l1:
                await self.l1_cache.set(entry)

            # Set in L2 cache
            if self.enable_l2 and self.l2_cache:
                await self.l2_cache.set(entry)

            # Update tag mappings
            if tags:
                for tag in tags:
                    if tag not in self._tag_mappings:
                        self._tag_mappings[tag] = []
                    if key not in self._tag_mappings[tag]:
                        self._tag_mappings[tag].append(key)

            self._performance_stats["cache_writes"] += 1
            return True

        except Exception as e:
            cache_logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache (both levels)"""
        try:
            success = True

            # Delete from L1 cache
            if self.enable_l1:
                l1_result = await self.l1_cache.delete(key)
                success = success and l1_result

            # Delete from L2 cache
            if self.enable_l2 and self.l2_cache:
                l2_result = await self.l2_cache.delete(key)
                success = success and l2_result

            # Remove from tag mappings
            for tag, keys in self._tag_mappings.items():
                if key in keys:
                    keys.remove(key)

            return success

        except Exception as e:
            cache_logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with specified tag"""
        try:
            if tag not in self._tag_mappings:
                return 0

            keys = self._tag_mappings[tag].copy()
            invalidated_count = 0

            for key in keys:
                if await self.delete(key):
                    invalidated_count += 1

            # Clear tag mapping
            del self._tag_mappings[tag]

            self._performance_stats["cache_invalidations"] += invalidated_count
            cache_logger.info(f"Invalidated {invalidated_count} cache entries for tag: {tag}")

            return invalidated_count

        except Exception as e:
            cache_logger.error(f"Cache tag invalidation error for tag {tag}: {e}")
            return 0

    def cache(
        self,
        prefix: str,
        ttl: float | None = None,
        tags: list[str] | None = None,
        key_generator: Callable | None = None,
    ):
        """
        Decorator for caching function results

        Usage:
            @cache_manager.cache("user_profile", ttl=300, tags=["user"])
            async def get_user_profile(user_id: str):
                return await user_service.get_profile(user_id)
        """

        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = self._generate_cache_key(prefix, *args, **kwargs)

                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl=ttl, tags=tags)
                return result

            return wrapper

        return decorator

    async def warm_cache(self, warmup_functions: list[tuple[str, Callable, list, dict]]):
        """
        Warm up cache with precomputed values

        Args:
            warmup_functions: List of (prefix, function, args, kwargs) tuples
        """
        cache_logger.info(f"Starting cache warmup for {len(warmup_functions)} functions")

        for prefix, func, args, kwargs in warmup_functions:
            try:
                # Generate cache key
                cache_key = self._generate_cache_key(prefix, *args, **kwargs)

                # Check if already cached
                if await self.get(cache_key) is not None:
                    continue

                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl=3600)  # 1 hour default

                cache_logger.debug(f"Warmed cache for key: {cache_key}")

            except Exception as e:
                cache_logger.error(f"Cache warmup error for {prefix}: {e}")

        cache_logger.info("Cache warmup completed")

    async def clear_all(self) -> bool:
        """Clear all cache levels"""
        try:
            success = True

            if self.enable_l1:
                l1_result = await self.l1_cache.clear()
                success = success and l1_result

            if self.enable_l2 and self.l2_cache:
                l2_result = await self.l2_cache.clear()
                success = success and l2_result

            # Clear tag mappings
            self._tag_mappings.clear()

            cache_logger.info("All caches cleared")
            return success

        except Exception as e:
            cache_logger.error(f"Cache clear all error: {e}")
            return False

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        total_requests = self._performance_stats["total_requests"]
        total_hits = self._performance_stats["l1_hits"] + self._performance_stats["l2_hits"]
        overall_hit_ratio = total_hits / total_requests if total_requests > 0 else 0

        stats = {
            "overall": {
                **self._performance_stats,
                "hit_ratio": round(overall_hit_ratio, 4),
                "total_requests": total_requests,
            }
        }

        # Add L1 cache stats
        if self.enable_l1 and hasattr(self.l1_cache, "get_stats"):
            stats["l1_memory"] = self.l1_cache.get_stats()

        # Add L2 cache stats
        if self.enable_l2 and self.l2_cache and hasattr(self.l2_cache, "get_stats"):
            stats["l2_redis"] = self.l2_cache.get_stats()

        # Add tag statistics
        stats["tags"] = {
            "total_tags": len(self._tag_mappings),
            "tagged_keys": sum(len(keys) for keys in self._tag_mappings.values()),
        }

        return stats


# Global cache manager instance
_cache_manager: CacheManager | None = None


async def initialize_cache_manager(redis_client=None) -> CacheManager:
    """Initialize the global cache manager"""
    global _cache_manager

    # Create L1 memory cache
    l1_cache = MemoryCache(max_size=1000, strategy=CacheStrategy.LRU)

    # Create L2 Redis cache if available
    l2_cache = RedisCache(redis_client) if redis_client else None

    _cache_manager = CacheManager(
        l1_cache=l1_cache, l2_cache=l2_cache, enable_l1=True, enable_l2=(redis_client is not None)
    )

    cache_logger.info("Cache manager initialized")
    return _cache_manager


def get_cache_manager() -> CacheManager | None:
    """Get the global cache manager instance"""
    return _cache_manager
