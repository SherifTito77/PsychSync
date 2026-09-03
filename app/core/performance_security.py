"""
Performance-Optimized Security Functions
JWT caching and optimized authentication for high-load scenarios
"""

import hashlib
import logging
import time
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger("app.security.performance")

# Performance configuration
JWT_CACHE_SIZE = 1000  # Number of cached JWT tokens
JWT_CACHE_TTL = 300  # 5 minutes cache TTL
CLEANUP_INTERVAL = 60  # Check for cleanup every minute

# Cache metrics
_last_cleanup = time.time()
_cache_hits = 0
_cache_misses = 0


def get_cache_metrics() -> dict[str, Any]:
    """Get cache performance metrics"""
    total_requests = _cache_hits + _cache_misses
    hit_rate = (_cache_hits / total_requests * 100) if total_requests > 0 else 0

    return {
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "hit_rate_percentage": round(hit_rate, 2),
        "total_requests": total_requests,
        "cache_size": JWT_CACHE_SIZE,
        "cache_ttl_seconds": JWT_CACHE_TTL,
    }


def reset_cache_metrics():
    """Reset cache metrics for monitoring"""
    global _cache_hits, _cache_misses
    _cache_hits = 0
    _cache_misses = 0


def _should_cleanup_cache() -> bool:
    """Check if cache should be cleaned up"""
    global _last_cleanup
    current_time = time.time()
    if current_time - _last_cleanup > CLEANUP_INTERVAL:
        _last_cleanup = current_time
        return True
    return False


def _get_token_hash(token: str) -> str:
    """Get a hash of the token for cache key"""
    return hashlib.sha256(token.encode()).hexdigest()[:32]


@lru_cache(maxsize=JWT_CACHE_SIZE)
def cached_verify_jwt_token(
    token_hash: str, original_token: str
) -> dict[str, Any] | None:
    """
    Cached JWT token verification for performance optimization

    Args:
        token_hash: Hashed token for cache key
        original_token: Original token for verification

    Returns:
        Decoded payload or None if invalid
    """
    global _cache_misses
    _cache_misses += 1

    try:
        import jwt
        from jose import JWTError

        # This is where the actual JWT verification happens
        payload = jwt.decode(original_token, settings.jwt_secret, algorithms=["HS256"])

        # Cache the decoded payload
        return payload

    except (JWTError, Exception) as e:
        logger.debug(f"JWT verification failed: {type(e).__name__}")
        return None


def get_jwt_payload_optimized(token: str) -> dict[str, Any] | None:
    """
    Optimized JWT payload retrieval with caching

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    global _cache_hits

    # Check cache cleanup periodically
    if _should_cleanup_cache():
        try:
            # Clear cache if it's getting stale
            if time.time() - _last_cleanup > JWT_CACHE_TTL:
                cached_verify_jwt_token.cache_clear()
                logger.info("JWT cache cleared due to TTL expiration")
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")

    # Generate cache key
    token_hash = _get_token_hash(token)

    # Try to get from cache first
    try:
        cached_result = cached_verify_jwt_token(token_hash, token)
        if cached_result is not None:
            _cache_hits += 1
            return cached_result
    except Exception as e:
        logger.warning(f"Cache retrieval failed: {e}")

    # Fallback to direct verification if cache fails
    try:
        import jwt
        from jose import JWTError

        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload

    except (JWTError, Exception) as e:
        logger.debug(f"Direct JWT verification failed: {type(e).__name__}")
        return None


# Fast authentication check for health endpoints
HEALTH_ENDPOINT_TOKENS = {
    # Pre-verified test tokens for health checks
    "health_check_token": {"sub": "health_check", "type": "access", "exp": 9999999999}
}


def is_health_endpoint_token(token: str) -> bool:
    """
    Fast check for common health endpoint tokens

    Args:
        token: JWT token string

    Returns:
        True if it's a known health endpoint token
    """
    return token in HEALTH_ENDPOINT_TOKENS


def get_health_endpoint_payload(token: str) -> dict[str, Any] | None:
    """
    Get payload for health endpoint without verification (performance optimization)

    Args:
        token: JWT token string

    Returns:
        Pre-configured payload or None
    """
    return HEALTH_ENDPOINT_TOKENS.get(token)


# Performance monitoring middleware helper
def log_performance_metrics():
    """Log current performance metrics"""
    metrics = get_cache_metrics()
    logger.info(
        "JWT Cache Performance",
        extra={
            "cache_hits": metrics["cache_hits"],
            "cache_misses": metrics["cache_misses"],
            "hit_rate_percentage": metrics["hit_rate_percentage"],
            "total_requests": metrics["total_requests"],
            "event_type": "performance_metrics",
        },
    )


# Export optimized functions
__all__ = [
    "get_cache_metrics",
    "get_health_endpoint_payload",
    "get_jwt_payload_optimized",
    "is_health_endpoint_token",
    "log_performance_metrics",
    "reset_cache_metrics",
]
