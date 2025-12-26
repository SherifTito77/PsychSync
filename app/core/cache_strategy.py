# app/core/cache_strategy.py
"""
Intelligent Caching Strategy for PsychSync
Provides automated caching for frequently accessed data with intelligent invalidation
"""

import json
import pickle
import hashlib
from functools import wraps
from typing import Any, Optional, Callable, Union, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from enum import Enum

from app.core.cache import cache_get, cache_set, cache_delete, cache_delete_pattern
from app.core.structured_logging import get_logger, EventType

logger = get_logger(__name__)

class CacheStrategy(Enum):
    """Different caching strategies for different data types"""
    USER_PROFILE = "user_profile"
    TEAM_DATA = "team_data"
    ASSESSMENT_DATA = "assessment_data"
    ASSESSMENT_RESULTS = "assessment_results"
    ORGANIZATION_DATA = "organization_data"
    AUTH_TOKENS = "auth_tokens"
    API_RESPONSES = "api_responses"
    SESSION_DATA = "session_data"

@dataclass
class CacheConfig:
    """Configuration for caching strategies"""
    ttl_seconds: int
    max_size: Optional[int] = None
    warm_on_startup: bool = False
    invalidate_on_change: bool = True
    compress_large_objects: bool = True
    version: int = 1

# Cache configurations for different data types
CACHE_CONFIGS: Dict[CacheStrategy, CacheConfig] = {
    CacheStrategy.USER_PROFILE: CacheConfig(
        ttl_seconds=300,  # 5 minutes
        max_size=10000,
        warm_on_startup=True,
        invalidate_on_change=True
    ),
    CacheStrategy.TEAM_DATA: CacheConfig(
        ttl_seconds=600,  # 10 minutes
        max_size=5000,
        warm_on_startup=False,
        invalidate_on_change=True
    ),
    CacheStrategy.ASSESSMENT_DATA: CacheConfig(
        ttl_seconds=1800,  # 30 minutes
        max_size=2000,
        warm_on_startup=False,
        invalidate_on_change=True
    ),
    CacheStrategy.ASSESSMENT_RESULTS: CacheConfig(
        ttl_seconds=3600,  # 1 hour
        max_size=10000,
        warm_on_startup=False,
        invalidate_on_change=False  # Results don't change
    ),
    CacheStrategy.ORGANIZATION_DATA: CacheConfig(
        ttl_seconds=3600,  # 1 hour
        max_size=1000,
        warm_on_startup=True,
        invalidate_on_change=True
    ),
    CacheStrategy.AUTH_TOKENS: CacheConfig(
        ttl_seconds=1800,  # 30 minutes
        max_size=50000,
        warm_on_startup=False,
        invalidate_on_change=True
    ),
    CacheStrategy.API_RESPONSES: CacheConfig(
        ttl_seconds=60,  # 1 minute
        max_size=1000,
        warm_on_startup=False,
        invalidate_on_change=True
    ),
    CacheStrategy.SESSION_DATA: CacheConfig(
        ttl_seconds=7200,  # 2 hours
        max_size=10000,
        warm_on_startup=False,
        invalidate_on_change=True
    )
}

class IntelligentCache:
    """
    Intelligent caching system with automatic invalidation and warming
    """

    def __init__(self):
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "invalidations": 0
        }
        self.cache_keys: Dict[str, datetime] = {}
        self.running = True

    def generate_cache_key(self, strategy: CacheStrategy, operation: str, **kwargs) -> str:
        """Generate consistent cache keys"""
        # Create a deterministic key from parameters
        key_data = {
            "strategy": strategy.value,
            "operation": operation,
            "params": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        return f"{strategy.value}:{operation}:{key_hash}"

    async def get(self, strategy: CacheStrategy, operation: str, **kwargs) -> Optional[Any]:
        """Get data from cache with statistics tracking"""
        cache_key = self.generate_cache_key(strategy, operation, **kwargs)

        try:
            cached_data = await cache_get(cache_key)

            if cached_data is not None:
                self.cache_stats["hits"] += 1
                self.cache_keys[cache_key] = datetime.utcnow()

                logger.debug(
                    EventType.DATABASE_OPERATION,
                    f"Cache hit for {strategy.value}:{operation}",
                    operation_name="cache_hit",
                    cache_key=cache_key,
                    strategy=strategy.value
                )

                return cached_data
            else:
                self.cache_stats["misses"] += 1

                logger.debug(
                    EventType.DATABASE_OPERATION,
                    f"Cache miss for {strategy.value}:{operation}",
                    operation_name="cache_miss",
                    cache_key=cache_key,
                    strategy=strategy.value
                )

                return None

        except Exception as e:
            logger.log_error(
                e,
                operation="cache_get",
                cache_key=cache_key,
                strategy=strategy.value
            )
            return None

    async def set(self, strategy: CacheStrategy, operation: str, data: Any, **kwargs) -> bool:
        """Set data in cache with TTL and compression"""
        cache_key = self.generate_cache_key(strategy, operation, **kwargs)
        config = CACHE_CONFIGS[strategy]

        try:
            # Compress large objects if enabled
            if config.compress_large_objects and self._should_compress(data):
                data = self._compress_data(data)

            success = await cache_set(
                cache_key,
                data,
                ttl=config.ttl_seconds
            )

            if success:
                self.cache_stats["sets"] += 1
                self.cache_keys[cache_key] = datetime.utcnow()

                logger.debug(
                    EventType.DATABASE_OPERATION,
                    f"Cache set for {strategy.value}:{operation}",
                    operation_name="cache_set",
                    cache_key=cache_key,
                    strategy=strategy.value,
                    ttl=config.ttl_seconds
                )

            return success

        except Exception as e:
            logger.log_error(
                e,
                operation="cache_set",
                cache_key=cache_key,
                strategy=strategy.value
            )
            return False

    async def invalidate(self, strategy: CacheStrategy, pattern: str = None, **kwargs):
        """Invalidate cache entries by strategy or pattern"""
        try:
            if pattern:
                # Invalidate by pattern
                cache_key_pattern = f"{strategy.value}:{pattern}:*"
                await cache_delete_pattern(cache_key_pattern)
                invalidated_count = len([k for k in self.cache_keys.keys() if k.startswith(f"{strategy.value}:{pattern}:")])
            else:
                # Invalidate specific key
                cache_key = self.generate_cache_key(strategy, pattern or "invalidate", **kwargs)
                await cache_delete(cache_key)
                invalidated_count = 1

            self.cache_stats["invalidations"] += invalidated_count

            logger.info(
                EventType.DATABASE_OPERATION,
                f"Cache invalidation for {strategy.value}",
                operation_name="cache_invalidate",
                strategy=strategy.value,
                pattern=pattern,
                invalidated_count=invalidated_count
            )

        except Exception as e:
            logger.log_error(
                e,
                operation="cache_invalidate",
                strategy=strategy.value,
                pattern=pattern
            )

    async def warm_cache(self, strategy: CacheStrategy, data_loader: Callable):
        """Warm cache with frequently accessed data"""
        config = CACHE_CONFIGS[strategy]

        if not config.warm_on_startup:
            return

        try:
            logger.info(
                EventType.SYSTEM_EVENT,
                f"Warming cache for {strategy.value}",
                operation_name="cache_warm",
                strategy=strategy.value
            )

            # Load data based on strategy
            if strategy == CacheStrategy.USER_PROFILE:
                await self._warm_user_cache(data_loader)
            elif strategy == CacheStrategy.ORGANIZATION_DATA:
                await self._warm_organization_cache(data_loader)

        except Exception as e:
            logger.log_error(
                e,
                operation="cache_warm",
                strategy=strategy.value
            )

    async def _warm_user_cache(self, data_loader: Callable):
        """Warm user profile cache"""
        # Load active users and cache their profiles
        active_users = await data_loader.get_active_users()

        tasks = []
        for user in active_users:
            tasks.append(self.set(
                CacheStrategy.USER_PROFILE,
                "profile",
                user,
                user_id=str(user.id)
            ))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(
                EventType.SYSTEM_EVENT,
                f"Warmed cache with {len(active_users)} user profiles",
                operation_name="cache_warm_users",
                user_count=len(active_users)
            )

    async def _warm_organization_cache(self, data_loader: Callable):
        """Warm organization cache"""
        # Load all organizations and cache their data
        organizations = await data_loader.get_all_organizations()

        tasks = []
        for org in organizations:
            tasks.append(self.set(
                CacheStrategy.ORGANIZATION_DATA,
                "profile",
                org,
                org_id=str(org.id)
            ))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(
                EventType.SYSTEM_EVENT,
                f"Warmed cache with {len(organizations)} organizations",
                operation_name="cache_warm_organizations",
                org_count=len(organizations)
            )

    def _should_compress(self, data: Any) -> bool:
        """Check if data should be compressed"""
        try:
            # Check if data is large enough to benefit from compression
            serialized = pickle.dumps(data)
            return len(serialized) > 1024  # Compress if > 1KB
        except:
            return False

    def _compress_data(self, data: Any) -> bytes:
        """Compress data using pickle"""
        return pickle.dumps(data)

    def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data from pickle"""
        return pickle.loads(compressed_data)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / max(total_requests, 1)) * 100

        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "active_keys": len(self.cache_keys),
            "cache_keys_by_strategy": self._get_keys_by_strategy()
        }

    def _get_keys_by_strategy(self) -> Dict[str, int]:
        """Get count of cache keys by strategy"""
        strategy_counts = {}

        for key in self.cache_keys.keys():
            strategy = key.split(":")[0]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return strategy_counts

    async def cleanup_expired_keys(self):
        """Clean up expired cache keys from memory tracking"""
        current_time = datetime.utcnow()
        expired_keys = []

        for key, timestamp in self.cache_keys.items():
            # Remove keys older than 1 hour (they should be expired from Redis)
            if (current_time - timestamp).total_seconds() > 3600:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache_keys[key]

        if expired_keys:
            logger.debug(
                EventType.SYSTEM_EVENT,
                f"Cleaned up {len(expired_keys)} expired cache keys",
                operation_name="cache_cleanup",
                expired_keys_count=len(expired_keys)
            )

# Global cache instance
intelligent_cache = IntelligentCache()

def cached(strategy: CacheStrategy, operation: str = None, ttl_override: int = None):
    """
    Decorator for automatic caching of function results

    Args:
        strategy: Caching strategy to use
        operation: Operation name for cache key (defaults to function name)
        ttl_override: Override default TTL for this function
    """
    def decorator(func: Callable) -> Callable:
        operation_name = operation or func.__name__

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_kwargs = {}

            # Extract meaningful parameters for cache key
            if hasattr(func, '__code__'):
                param_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                for i, param_name in enumerate(param_names):
                    if i < len(args):
                        cache_kwargs[param_name] = args[i]

                # Add keyword arguments
                cache_kwargs.update(kwargs)

            # Remove non-serializable arguments
            cache_kwargs = {
                k: v for k, v in cache_kwargs.items()
                if k not in ['db'] and not callable(v)
            }

            # Try to get from cache
            cached_result = await intelligent_cache.get(strategy, operation_name, **cache_kwargs)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)

            # Cache the result
            if ttl_override:
                # Use custom TTL by temporarily modifying config
                original_ttl = CACHE_CONFIGS[strategy].ttl_seconds
                CACHE_CONFIGS[strategy].ttl_seconds = ttl_override
                await intelligent_cache.set(strategy, operation_name, result, **cache_kwargs)
                CACHE_CONFIGS[strategy].ttl_seconds = original_ttl
            else:
                await intelligent_cache.set(strategy, operation_name, result, **cache_kwargs)

            return result

        return wrapper
    return decorator

# ✅ IMPLEMENTED: Advanced cache invalidation strategies
# Provides intelligent cache invalidation based on data relationships
# and business events with cache tagging and hierarchical invalidation.

class CacheInvalidationManager:
    """
    Manages intelligent cache invalidation based on data relationships
    """

    def __init__(self):
        # Enhanced dependency graph with hierarchical relationships
        self.dependency_graph: Dict[str, List[str]] = {
            "user_profile": ["user_teams", "user_assessments", "user_permissions"],
            "team_data": ["team_members", "team_assessments", "team_analytics"],
            "assessment_data": ["assessment_results", "assessment_analytics"],
            "organization_data": ["org_teams", "org_users", "org_assessments"]
        }

        # Cache tagging system for multi-dimensional invalidation
        self.cache_tags: Dict[str, set] = {}
        self.tag_index: Dict[str, set] = {}  # Reverse index for fast tag lookups

        self.invalidation_queue = asyncio.Queue()
        self.processing = False

    def add_cache_tags(self, cache_key: str, tags: List[str]):
        """
        Add tags to a cache key for intelligent invalidation

        Args:
            cache_key: The cache key to tag
            tags: List of tags to associate with this cache entry
        """
        if cache_key not in self.cache_tags:
            self.cache_tags[cache_key] = set()

        for tag in tags:
            self.cache_tags[cache_key].add(tag)

            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(cache_key)

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate all cache entries associated with the given tags

        Args:
            tags: List of tags to invalidate

        Returns:
            Number of cache entries invalidated
        """
        cache_keys_to_invalidate = set()

        for tag in tags:
            if tag in self.tag_index:
                cache_keys_to_invalidate.update(self.tag_index[tag])

        # Invalidate all identified cache keys
        for cache_key in cache_keys_to_invalidate:
            await cache_delete(cache_key)

            # Clean up tag indices
            if cache_key in self.cache_tags:
                for tag in self.cache_tags[cache_key]:
                    if tag in self.tag_index and cache_key in self.tag_index[tag]:
                        self.tag_index[tag].remove(cache_key)
                del self.cache_tags[cache_key]

        logger.info(f"Invalidated {len(cache_keys_to_invalidate)} cache entries by tags: {tags}")
        return len(cache_keys_to_invalidate)

    async def invalidate_related_caches(self, entity_type: str, entity_id: str, operation: str = "update"):
        """
        Invalidate caches related to a specific entity

        Args:
            entity_type: Type of entity (user, team, organization, etc.)
            entity_id: ID of the entity
            operation: Type of operation (create, update, delete)
        """
        invalidation_tasks = []

        # Direct cache invalidation
        direct_cache_key = f"{entity_type}:{entity_id}"
        invalidation_tasks.append(
            self._queue_invalidation(CacheStrategy.USER_PROFILE, direct_cache_key)
        )

        # Related cache invalidation based on dependency graph
        related_caches = self.dependency_graph.get(entity_type, [])

        for related_cache in related_caches:
            if entity_type == "user" and related_cache in ["user_teams", "user_assessments"]:
                invalidation_tasks.append(
                    self._queue_invalidation(CacheStrategy.TEAM_DATA, f"user_{entity_id}_*")
                )
                invalidation_tasks.append(
                    self._queue_invalidation(CacheStrategy.ASSESSMENT_DATA, f"user_{entity_id}_*")
                )
            elif entity_type == "team" and related_cache in ["team_members", "team_assessments"]:
                invalidation_tasks.append(
                    self._queue_invalidation(CacheStrategy.USER_PROFILE, f"team_{entity_id}_*")
                )
                invalidation_tasks.append(
                    self._queue_invalidation(CacheStrategy.ASSESSMENT_DATA, f"team_{entity_id}_*")
                )

        # Execute invalidation tasks
        if invalidation_tasks:
            await asyncio.gather(*invalidation_tasks, return_exceptions=True)

        logger.info(
            EventType.BUSINESS_EVENT,
            f"Invalidated caches for {entity_type}:{entity_id}",
            operation_name="cache_invalidation",
            entity_type=entity_type,
            entity_id=entity_id,
            operation_type=operation,
            related_caches=related_caches
        )

    async def _queue_invalidation(self, strategy: CacheStrategy, pattern: str):
        """Queue cache invalidation for processing"""
        await self.invalidation_queue.put((strategy, pattern))

        if not self.processing:
            asyncio.create_task(self._process_invalidation_queue())

    async def _process_invalidation_queue(self):
        """Process cache invalidation queue"""
        if self.processing:
            return

        self.processing = True

        try:
            while not self.invalidation_queue.empty():
                strategy, pattern = await self.invalidation_queue.get()
                await intelligent_cache.invalidate(strategy, pattern)
        finally:
            self.processing = False

    async def invalidate_user_caches(self, user_id: str):
        """Invalidate all caches related to a user"""
        await self.invalidate_related_caches("user", user_id)

    async def invalidate_team_caches(self, team_id: str):
        """Invalidate all caches related to a team"""
        await self.invalidate_related_caches("team", team_id)

    async def invalidate_assessment_caches(self, assessment_id: str):
        """Invalidate all caches related to an assessment"""
        await self.invalidate_related_caches("assessment", assessment_id)

    async def invalidate_organization_caches(self, org_id: str):
        """Invalidate all caches related to an organization"""
        await self.invalidate_related_caches("organization", org_id)

# Global cache invalidation manager
cache_invalidation_manager = CacheInvalidationManager()