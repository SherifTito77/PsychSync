# app/services/auth_service.py

from datetime import UTC, datetime

import redis.asyncio as aioredis

from app.core.config import settings


async def blacklist_token(token: str, expiry: datetime | None = None) -> None:
    """
    Add token to blacklist using Redis atomic operations (THREAD-SAFE)

    This implementation uses Redis SETEX command which is atomic, preventing
    race conditions where multiple threads/processes might try to blacklist
    the same token simultaneously.

    Args:
        token: Token to blacklist
        expiry: Optional expiry time for auto-cleanup (defaults to 24 hours)
    """
    redis_client = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

    try:
        # Set TTL (default 24 hours if not specified)
        if expiry:
            ttl = int((expiry - datetime.now(UTC)).total_seconds())
        else:
            ttl = 86400  # 24 hours

        # ATOMIC OPERATION: SETEX is thread-safe in Redis
        # This prevents race conditions during concurrent blacklist operations
        await redis_client.setex(f"blacklist:{token}", ttl, "1")
    finally:
        await redis_client.close()


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted using Redis EXISTS command (THREAD-SAFE)

    The EXISTS command in Redis is atomic, preventing race conditions where
    a token might be checked for blacklist status while being blacklisted
    by another process.

    Args:
        token: Token to check

    Returns:
        True if blacklisted, False otherwise
    """
    redis_client = await aioredis.from_url(
        settings.REDIS_URL, encoding="utf-8", decode_responses=True
    )

    try:
        # ATOMIC OPERATION: EXISTS is thread-safe in Redis
        result = await redis_client.exists(f"blacklist:{token}")
        return result == 1
    finally:
        await redis_client.close()
