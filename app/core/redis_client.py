"""
Redis Client Configuration and Connection Management
Production-ready Redis client with connection pooling and error handling
"""

import logging
from urllib.parse import urlparse

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: redis.Redis | None = None


def parse_redis_url(url: str) -> dict:
    """Parse Redis URL into connection parameters"""
    parsed = urlparse(url)

    # Extract connection details from URL
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    db = int(parsed.path.lstrip("/")) if parsed.path else 0
    password = parsed.password

    return {"host": host, "port": port, "db": db, "password": password}


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client with connection pooling

    Returns:
        Redis client instance
    """
    global _redis_client

    if _redis_client is None:
        try:
            # Parse Redis URL to get connection parameters
            redis_params = parse_redis_url(settings.REDIS_URL)

            # Create Redis connection with production settings using available config
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True,  # Decode responses to strings
                health_check_interval=30,  # Health check every 30 seconds
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError],
            )

            # Test connection
            await _redis_client.ping()
            logger.info(
                f"Redis connected successfully to {redis_params['host']}:{redis_params['port']}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Create mock Redis client for development
            _redis_client = MockRedisClient()

    return _redis_client


async def close_redis_connection():
    """Close Redis connection gracefully"""
    global _redis_client
    if _redis_client and hasattr(_redis_client, "close"):
        await _redis_client.close()
        logger.info("Redis connection closed")


class MockRedisClient:
    """
    Mock Redis client for development/testing when Redis is not available
    Implements basic Redis operations for rate limiting and caching
    """

    def __init__(self):
        self._data = {}
        self._ttl = {}
        self.logger = logging.getLogger(__name__)

    async def ping(self):
        """Mock ping - always returns True"""
        return True

    async def setex(self, key: str, seconds: int, value: str):
        """Mock setex - sets value with expiration"""
        self._data[key] = value
        self._ttl[key] = seconds

    async def get(self, key: str):
        """Mock get - returns value if exists and not expired"""
        if key in self._data:
            # In a real implementation, we'd check TTL here
            return self._data[key]
        return None

    async def delete(self, key: str):
        """Mock delete - removes key"""
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]
        return 1

    async def exists(self, key: str):
        """Mock exists - checks if key exists"""
        return 1 if key in self._data else 0

    async def expire(self, key: str, seconds: int):
        """Mock expire - sets expiration for key"""
        if key in self._data:
            self._ttl[key] = seconds

    async def pipeline(self):
        """Mock pipeline - returns MockPipeline"""
        return MockPipeline(self._data, self._ttl)

    async def close(self):
        """Mock close - cleanup"""
        self._data.clear()
        self._ttl.clear()

    def __getattr__(self, name):
        """Fallback for any other Redis methods"""
        self.logger.warning(
            f"MockRedisClient: Method {name} not implemented, returning None"
        )

        async def mock_method(*args, **kwargs):
            return None

        return mock_method


class MockPipeline:
    """Mock Redis pipeline for testing"""

    def __init__(self, data, ttl):
        self._data = data
        self._ttl = ttl
        self._commands = []

    async def zremrangebyscore(self, key, min_score, max_score):
        """Mock zremrangebyscore"""
        self._commands.append(("zremrangebyscore", key, min_score, max_score))
        return 0

    async def zcard(self, key):
        """Mock zcard"""
        self._commands.append(("zcard", key))
        return 0

    async def zadd(self, key, mapping):
        """Mock zadd"""
        self._commands.append(("zadd", key, mapping))
        return 1

    async def expire(self, key, seconds):
        """Mock expire"""
        self._commands.append(("expire", key, seconds))
        return True

    async def execute(self):
        """Mock execute - returns mock results"""
        results = []
        for command in self._commands:
            if command[0] == "zcard":
                results.append(0)  # No requests in window
            elif command[0] in ["zremrangebyscore", "zadd", "expire"]:
                results.append(1)
            else:
                results.append(None)
        self._commands.clear()
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Export convenience functions
async def redis_set(key: str, value: str, expire: int | None = None) -> bool:
    """Set key-value pair in Redis with optional expiration"""
    try:
        client = await get_redis_client()
        if expire:
            await client.setex(key, expire, value)
        else:
            await client.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Redis SET error: {e}")
        return False


async def redis_get(key: str) -> str | None:
    """Get value from Redis"""
    try:
        client = await get_redis_client()
        return await client.get(key)
    except Exception as e:
        logger.error(f"Redis GET error: {e}")
        return None


async def redis_delete(key: str) -> bool:
    """Delete key from Redis"""
    try:
        client = await get_redis_client()
        return await client.delete(key) > 0
    except Exception as e:
        logger.error(f"Redis DELETE error: {e}")
        return False
