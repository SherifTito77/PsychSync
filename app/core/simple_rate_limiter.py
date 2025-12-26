"""
Simple in-memory rate limiter for authentication endpoints.
Uses a sliding window algorithm to track requests per IP.
"""

import time
from typing import Dict
from functools import wraps
from fastapi import Request, HTTPException, status

class SimpleRateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self):
        # Store request timestamps per key
        self.requests: Dict[str, list] = {}
        # Clean up old entries periodically
        self._last_cleanup = time.time()

    def _cleanup(self):
        """Remove entries older than 1 hour."""
        now = time.time()
        if now - self._last_cleanup > 3600:  # Cleanup every hour
            self.requests = {
                key: timestamps
                for key, timestamps in self.requests.items()
                if any(now - ts < 3600 for ts in timestamps)
            }
            self._last_cleanup = now

    def is_rate_limited(
        self,
        key: str,
        max_requests: int = 5,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if the given key has exceeded the rate limit.

        Args:
            key: Unique identifier (e.g., IP address, user ID)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if rate limited, False otherwise
        """
        self._cleanup()

        now = time.time()

        # Get or initialize request list for this key
        if key not in self.requests:
            self.requests[key] = []

        # Remove timestamps outside the window
        window_start = now - window_seconds
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]

        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            return True

        # Add current request timestamp
        self.requests[key].append(now)
        return False

# Global rate limiter instance
rate_limiter = SimpleRateLimiter()


def rate_limit(max_requests: int = 5, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoint access.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Example:
        @rate_limit(max_requests=5, window_seconds=60)
        async def login_endpoint(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the Request object in arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                # Try to get request from kwargs
                request = kwargs.get('request')

            if request is None:
                # No request object found, skip rate limiting
                return await func(*args, **kwargs)

            # Get client IP as rate limit key
            client_ip = request.client.host if request.client else "unknown"
            key = f"{request.url.path}:{client_ip}"

            # Check rate limit
            if rate_limiter.is_rate_limited(key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Maximum {max_requests} requests per {window_seconds} seconds.",
                        "retry_after": window_seconds
                    },
                    headers={
                        "Retry-After": str(window_seconds),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + window_seconds)
                    }
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
