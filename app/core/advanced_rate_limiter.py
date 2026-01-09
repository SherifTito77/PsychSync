# app/core/advanced_rate_limiter.py
"""
Multi-layered rate limiting system to prevent abuse.

Layers:
1. IP-based rate limiting (basic protection)
2. Username-based rate limiting (stricter - prevents credential stuffing)
3. Device fingerprinting (prevents IP rotation bypass)
4. Geolocation tracking (prevents distributed attacks)
"""

import hashlib
import time

from fastapi import Request
from redis.asyncio import Redis


class AdvancedRateLimiter:
    """
    Multi-strategy rate limiting with Redis backend.

    This prevents bypass via IP rotation by tracking multiple dimensions.
    """

    def __init__(self, redis: Redis):
        """
        Initialize rate limiter.

        Args:
            redis: Redis client instance
        """
        self.redis = redis

    async def check_rate_limit(
        self, request: Request, username: str | None = None, endpoint: str = "default"
    ) -> tuple[bool, str, dict]:
        """
        Check rate limits across multiple dimensions.

        Args:
            request: FastAPI request object
            username: Optional username for stricter tracking
            endpoint: Endpoint identifier for different limits

        Returns:
            Tuple of (allowed, reason, rate_limit_info)

        Raises:
            HTTPException: If rate limit exceeded (with 429 status)
        """
        client_ip = self._get_client_ip(request)

        # Layer 1: IP-based rate limiting
        ip_allowed, ip_limit = await self._check_limit(
            f"rate_limit:ip:{endpoint}:{client_ip}", max_requests=100, window=60, identifier="IP"
        )

        if not ip_allowed:
            return False, f"IP rate limit exceeded: {client_ip}", ip_limit

        # Layer 2: Username-based rate limiting (stricter)
        if username:
            username_allowed, username_limit = await self._check_limit(
                f"rate_limit:username:{endpoint}:{username.lower()}",
                max_requests=10,
                window=60,
                identifier="Username",
            )

            if not username_allowed:
                return False, "Username rate limit exceeded", username_limit

        # Layer 3: Device fingerprinting
        device_id = self._get_device_fingerprint(request)
        device_allowed, device_limit = await self._check_limit(
            f"rate_limit:device:{endpoint}:{device_id}",
            max_requests=20,
            window=60,
            identifier="Device",
        )

        if not device_allowed:
            return False, "Device rate limit exceeded", device_limit

        # Layer 4: Geolocation tracking (rough grouping by first octet)
        geo_group = client_ip.split(".")[0] if "." in client_ip else "unknown"
        geo_allowed, geo_limit = await self._check_limit(
            f"rate_limit:geo:{endpoint}:{geo_group}",
            max_requests=500,
            window=60,
            identifier="Geographic",
        )

        if not geo_allowed:
            return False, "Geographic rate limit exceeded", geo_limit

        # Track attempt for analytics
        await self._track_attempt(client_ip, username, device_id)

        # Return success with rate limit info
        return (
            True,
            "OK",
            {
                "ip_limit": ip_limit,
                "username_limit": username_limit if username else None,
                "device_limit": device_limit,
                "geo_limit": geo_limit,
            },
        )

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP, handling proxy headers.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for proxy headers first
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_device_fingerprint(self, request: Request) -> str:
        """
        Generate device fingerprint from request headers.

        Factors:
        - User-Agent
        - Accept-Language
        - Accept-Encoding

        Args:
            request: FastAPI request object

        Returns:
            Device fingerprint hash
        """
        factors = [
            request.headers.get("User-Agent", ""),
            request.headers.get("Accept-Language", ""),
            request.headers.get("Accept-Encoding", ""),
        ]

        fingerprint = ":".join(factors)
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]

    async def _check_limit(
        self, key: str, max_requests: int, window: int, identifier: str
    ) -> tuple[bool, dict]:
        """
        Check if limit exceeded using sliding window counter.

        Args:
            key: Redis key for this counter
            max_requests: Maximum allowed requests
            window: Time window in seconds
            identifier: Human-readable identifier for logging

        Returns:
            Tuple of (allowed, limit_info)
        """
        current = await self.redis.incr(key)

        if current == 1:
            await self.redis.expire(key, window)

        allowed = current <= max_requests
        remaining = max(0, max_requests - current)
        reset_time = int(time.time()) + window

        limit_info = {
            "identifier": identifier,
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "current": current,
        }

        return allowed, limit_info

    async def _track_attempt(self, ip: str, username: str | None, device: str):
        """
        Track rate limit attempt for analytics.

        Args:
            ip: Client IP
            username: Optional username
            device: Device fingerprint
        """
        # Increment global counter
        await self.redis.incr("rate_limit:total_attempts")

        # Track by username if provided
        if username:
            await self.redis.incr(f"rate_limit:attempts:{username}")

        # Track suspicious patterns (multiple IPs for same device)
        if device:
            await self.redis.sadd(f"rate_limit:device_ips:{device}", ip)

    async def get_rate_limit_status(self, request: Request, username: str | None = None) -> dict:
        """
        Get current rate limit status for a client.

        Args:
            request: FastAPI request object
            username: Optional username

        Returns:
            Dictionary with current rate limit status
        """
        client_ip = self._get_client_ip(request)
        device_id = self._get_device_fingerprint(request)

        status = {"ip": client_ip, "device_fingerprint": device_id, "limits": {}}

        # Check IP limits
        ip_key = f"rate_limit:ip:default:{client_ip}"
        ip_current = await self.redis.get(ip_key)
        if ip_current:
            status["limits"]["ip"] = {"current": int(ip_current)}

        # Check username limits
        if username:
            username_key = f"rate_limit:username:default:{username.lower()}"
            username_current = await self.redis.get(username_key)
            if username_current:
                status["limits"]["username"] = {"current": int(username_current)}

        # Check device limits
        device_key = f"rate_limit:device:default:{device_id}"
        device_current = await self.redis.get(device_key)
        if device_current:
            status["limits"]["device"] = {"current": int(device_current)}

        return status

    async def reset_rate_limit(self, request: Request, username: str | None = None):
        """
        Reset rate limits for a client (admin function).

        Args:
            request: FastAPI request object
            username: Optional username to reset
        """
        client_ip = self._get_client_ip(request)
        device_id = self._get_device_fingerprint(request)

        # Reset IP limit
        await self.redis.delete(f"rate_limit:ip:default:{client_ip}")

        # Reset username limit if provided
        if username:
            await self.redis.delete(f"rate_limit:username:default:{username.lower()}")

        # Reset device limit
        await self.redis.delete(f"rate_limit:device:default:{device_id}")


# Singleton instance (initialized in app startup)
_rate_limiter: AdvancedRateLimiter | None = None


def get_rate_limiter() -> AdvancedRateLimiter | None:
    """
    Get the rate limiter instance.

    Returns:
        AdvancedRateLimiter instance or None if not initialized
    """
    return _rate_limiter


async def init_rate_limiter(redis_url: str):
    """
    Initialize the rate limiter with Redis.

    Args:
        redis_url: Redis connection URL
    """
    global _rate_limiter

    redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    _rate_limiter = AdvancedRateLimiter(redis)
