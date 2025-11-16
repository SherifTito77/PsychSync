# app/core/security_middleware.py
"""
Advanced security middleware for PsychSync API
"""
import time
import hashlib
from typing import Dict, Set, Optional, Callable
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis
import logging

from app.core.config import settings
from app.core.response import ErrorResponse

logger = logging.getLogger(__name__)


class AdvancedRateLimiter:
    """Advanced rate limiter with Redis backend and sliding window"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache: Dict[str, deque] = defaultdict(deque)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: str = "ip"
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if request should be rate limited

        Returns:
            Tuple of (is_limited, rate_limit_info)
        """
        current_time = int(time.time())
        window_start = current_time - window

        # Try Redis first
        if self.redis_client:
            try:
                # Remove old entries
                await self.redis_client.zremrangebyscore(key, 0, window_start)

                # Count current entries
                current_count = await self.redis_client.zcard(key)

                if current_count >= limit:
                    # Get oldest timestamp for retry-after calculation
                    oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                    retry_after = int(oldest[0][1] + window - current_time) if oldest else window

                    return True, {
                        "limit": limit,
                        "remaining": 0,
                        "reset": oldest[0][1] + window if oldest else current_time + window,
                        "retry_after": retry_after
                    }

                # Add current request
                await self.redis_client.zadd(key, {str(current_time): current_time})
                await self.redis_client.expire(key, window)

                return False, {
                    "limit": limit,
                    "remaining": limit - current_count - 1,
                    "reset": current_time + window,
                    "retry_after": 0
                }

            except Exception as e:
                logger.warning(f"Redis rate limiter failed, falling back to local cache: {e}")

        # Fallback to local cache
        await self._cleanup_local_cache()

        request_times = self.local_cache[key]

        # Remove old entries
        while request_times and request_times[0] <= window_start:
            request_times.popleft()

        current_count = len(request_times)

        if current_count >= limit:
            retry_after = request_times[0] + window - current_time if request_times else window
            return True, {
                "limit": limit,
                "remaining": 0,
                "reset": request_times[0] + window if request_times else current_time + window,
                "retry_after": int(retry_after)
            }

        # Add current request
        request_times.append(current_time)

        return False, {
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": current_time + window,
            "retry_after": 0
        }

    async def _cleanup_local_cache(self):
        """Clean up old entries in local cache"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff = current_time - 3600  # Remove entries older than 1 hour
        for key in list(self.local_cache.keys()):
            times = self.local_cache[key]
            while times and times[0] < cutoff:
                times.popleft()
            if not times:
                del self.local_cache[key]

        self.last_cleanup = current_time


class SecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware with multiple protection layers"""

    def __init__(
        self,
        app,
        redis_client: Optional[redis.Redis] = None,
        enable_rate_limiting: bool = True,
        enable_request_validation: bool = True,
        enable_ip_whitelist: bool = False
    ):
        super().__init__(app)
        self.rate_limiter = AdvancedRateLimiter(redis_client)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_request_validation = enable_request_validation
        self.enable_ip_whitelist = enable_ip_whitelist

        # Security configuration
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, Dict] = {}

        # Rate limiting configuration
        self.rate_limits = {
            "default": {"limit": 100, "window": 60},  # 100 requests per minute
            "auth": {"limit": 10, "window": 60},      # 10 auth requests per minute
            "register": {"limit": 5, "window": 300},  # 5 registrations per 5 minutes
            "password_reset": {"limit": 3, "window": 900},  # 3 password resets per 15 minutes
            "upload": {"limit": 20, "window": 60},     # 20 uploads per minute
        }

        # IP whitelist (if enabled)
        self.whitelisted_ips = {
            "127.0.0.1",
            "::1",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security pipeline"""

        try:
            # Get client IP
            client_ip = self._get_client_ip(request)

            # Check IP whitelist (if enabled)
            if self.enable_ip_whitelist and not self._is_ip_whitelisted(client_ip):
                return self._create_security_response(
                    "IP address not allowed",
                    status.HTTP_403_FORBIDDEN,
                    "IP_BLOCKED"
                )

            # Check if IP is blocked
            if client_ip in self.blocked_ips:
                return self._create_security_response(
                    "Access denied",
                    status.HTTP_403_FORBIDDEN,
                    "IP_BLOCKED"
                )

            # Rate limiting
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limit(request, client_ip)
                if rate_limit_result:
                    return rate_limit_result

            # Request validation
            if self.enable_request_validation:
                validation_result = await self._validate_request(request, client_ip)
                if validation_result:
                    return validation_result

            # Process request
            response = await call_next(request)

            # Add security headers
            response = await self._add_security_headers(request, response)

            # Add rate limit headers
            if self.enable_rate_limiting:
                response = await self._add_rate_limit_headers(response, client_ip, request)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            # Continue processing if security middleware fails
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist"""
        return ip in self.whitelisted_ips

    async def _check_rate_limit(self, request: Request, client_ip: str) -> Optional[Response]:
        """Check if request exceeds rate limits"""
        path = request.url.path.lower()
        method = request.method.upper()

        # Determine rate limit category
        rate_limit_key = "default"

        if any(endpoint in path for endpoint in ["/login", "/auth", "/token"]):
            rate_limit_key = "auth"
        elif "/register" in path:
            rate_limit_key = "register"
        elif "/password-reset" in path:
            rate_limit_key = "password_reset"
        elif "/upload" in path:
            rate_limit_key = "upload"

        # Create unique rate limit key
        key_data = f"{client_ip}:{path}:{method}"
        rate_key = f"rate_limit:{hashlib.md5(key_data.encode()).hexdigest()}"

        config = self.rate_limits[rate_limit_key]

        # Check rate limit
        is_limited, limit_info = await self.rate_limiter.is_rate_limited(
            key=rate_key,
            limit=config["limit"],
            window=config["window"],
            identifier=client_ip
        )

        if is_limited:
            # Track suspicious activity
            await self._track_suspicious_activity(client_ip, "rate_limit_exceeded", {
                "path": path,
                "method": method,
                "limit_info": limit_info
            })

            return self._create_rate_limit_response(limit_info)

        # Store limit info for headers
        request.state.rate_limit_info = limit_info
        return None

    async def _validate_request(self, request: Request, client_ip: str) -> Optional[Response]:
        """Validate request for security threats"""

        # Check for suspicious headers
        suspicious_headers = [
            "X-Forwarded-Host",
            "X-Originating-IP",
            "X-Remote-IP",
            "X-Remote-Addr"
        ]

        for header in suspicious_headers:
            if header in request.headers:
                await self._track_suspicious_activity(client_ip, "suspicious_header", {
                    "header": header,
                    "value": request.headers[header]
                })

        # Check user agent
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent or len(user_agent) > 500:
            await self._track_suspicious_activity(client_ip, "invalid_user_agent", {
                "user_agent_length": len(user_agent)
            })

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 100 * 1024 * 1024:  # 100MB
            return self._create_security_response(
                "Request entity too large",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                "PAYLOAD_TOO_LARGE"
            )

        return None

    async def _add_security_headers(self, request: Request, response: Response) -> Response:
        """Add comprehensive security headers"""

        # Content Security Policy (enhanced)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests;"
        )

        # Security headers
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # HSTS (only in production HTTPS)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Remove server information
        response.headers["Server"] = "PsychSync"

        # Add request ID for tracking
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")

        return response

    async def _add_rate_limit_headers(self, response: Response, client_ip: str, request: Request) -> Response:
        """Add rate limit headers to response"""
        if hasattr(request.state, "rate_limit_info"):
            info = request.state.rate_limit_info
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])

            if info["retry_after"] > 0:
                response.headers["Retry-After"] = str(info["retry_after"])

        return response

    async def _track_suspicious_activity(self, ip: str, activity_type: str, details: Dict):
        """Track suspicious activity and potentially block IP"""
        if ip not in self.suspicious_ips:
            self.suspicious_ips[ip] = {"count": 0, "activities": []}

        self.suspicious_ips[ip]["count"] += 1
        self.suspicious_ips[ip]["activities"].append({
            "type": activity_type,
            "timestamp": time.time(),
            "details": details
        })

        # Block IP if too many suspicious activities
        if self.suspicious_ips[ip]["count"] > 50:
            self.blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked due to suspicious activity")

        # Clean old activities
        cutoff = time.time() - 3600  # 1 hour
        self.suspicious_ips[ip]["activities"] = [
            activity for activity in self.suspicious_ips[ip]["activities"]
            if activity["timestamp"] > cutoff
        ]

    def _create_security_response(self, message: str, status_code: int, error_code: str) -> JSONResponse:
        """Create standardized security error response"""
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                message=message,
                error_code=error_code,
                data={"timestamp": int(time.time())}
            ).dict()
        )

    def _create_rate_limit_response(self, limit_info: Dict) -> JSONResponse:
        """Create rate limit error response"""
        headers = {}
        if limit_info["retry_after"] > 0:
            headers["Retry-After"] = str(limit_info["retry_after"])

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponse(
                message="Rate limit exceeded",
                error_code="RATE_LIMIT_EXCEEDED",
                data={
                    "limit": limit_info["limit"],
                    "reset": limit_info["reset"],
                    "retry_after": limit_info["retry_after"]
                }
            ).dict(),
            headers=headers
        )