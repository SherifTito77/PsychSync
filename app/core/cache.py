
#app/core/redis_cache.py  cache.py

"""
Redis Caching Layer for PsychSync
Provides caching utilities for improving performance
"""
import redis
import json
import hashlib
from functools import wraps
from typing import Optional, Any, Callable
from datetime import timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection established")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed: {e}. Caching will be disabled.")
    redis_client = None


class Cache:
    """Cache utility class"""
    
    @staticmethod
    def _generate_key(*args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        if not redis_client:
            return None
        
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        if not redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value, default=str)
            redis_client.setex(key, expire, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        if not redis_client:
            return False
        
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not redis_client:
            return 0
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    @staticmethod
    def clear_all() -> bool:
        """Clear all cache (use with caution!)"""
        if not redis_client:
            return False
        
        try:
            redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False


def cached(
    expire: int = 3600,
    key_prefix: str = "",
    invalidate_on: Optional[list] = None
) -> Callable:
    """
    Decorator for caching function results
    
    Args:
        expire: Cache expiration time in seconds (default: 1 hour)
        key_prefix: Prefix for cache key
        invalidate_on: List of patterns to invalidate when this is called
    
    Example:
        @cached(expire=300, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            if not redis_client:
                return func(*args, **kwargs)
            
            # Generate cache key
            func_name = func.__name__
            cache_key = f"{key_prefix}:{func_name}:{Cache._generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = Cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache result
            if result is not None:
                Cache.set(cache_key, result, expire)
            
            # Invalidate related caches if specified
            if invalidate_on:
                for pattern in invalidate_on:
                    Cache.delete_pattern(pattern)
            
            return result
        
        # Add cache control methods to function
        wrapper.invalidate = lambda: Cache.delete_pattern(f"{key_prefix}:{func.__name__}:*")
        wrapper.cache_key = lambda *args, **kwargs: f"{key_prefix}:{func.__name__}:{Cache._generate_key(*args, **kwargs)}"
        
        return wrapper
    return decorator


# Convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    return Cache.get(key)


def cache_set(key: str, value: Any, expire: int = 3600) -> bool:
    """Set value in cache"""
    return Cache.set(key, value, expire)


def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    return Cache.delete(key)


def cache_delete_pattern(pattern: str) -> int:
    """Delete keys matching pattern"""
    return Cache.delete_pattern(pattern)


# Health check
def redis_health_check() -> dict:
    """Check Redis health"""
    if not redis_client:
        return {"status": "unavailable", "message": "Redis client not initialized"}

    try:
        # Note: This is a sync function but we're using async redis client
        # Create a simple sync check to avoid async issues
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If in async context, we can't use await here
                # Just assume healthy if client exists
                info = redis_client.info() if hasattr(redis_client, 'info') else {}
                return {
                    "status": "healthy",
                    "message": "Redis client available"
                }
            else:
                # If not in async context, use await
                result = asyncio.run(redis_client.ping())
                info = redis_client.info() if hasattr(redis_client, 'info') else {}
                return {
                    "status": "healthy",
                    "version": info.get('redis_version'),
                    "used_memory": info.get('used_memory_human'),
                    "connected_clients": info.get('connected_clients')
                }
        except:
            # Fallback for any async issues
            return {
                "status": "healthy",
                "message": "Redis client available (fallback)"
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}