# app/core/security_advanced.py
"""
Advanced security middleware for PsychSync
Includes rate limiting, request validation, IP filtering, and security headers
"""

import time
import json
import hashlib
import logging
import ipaddress
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.constants import Security, RateLimit
from app.core.exceptions import RateLimitExceededError, SecurityViolationError

logger = logging.getLogger(__name__)

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Dict[str, datetime] = {}
        self.rate_limits = {
            'global': RateLimit.DEFAULT_REQUESTS_PER_MINUTE,
            'auth': RateLimit.AUTH_REQUESTS_PER_MINUTE,
            'upload': RateLimit.UPLOAD_REQUESTS_PER_HOUR,
            'sensitive': RateLimit.SENSITIVE_REQUESTS_PER_MINUTE,
            'api': RateLimit.DEFAULT_REQUESTS_PER_MINUTE
        }

    def get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from authenticated request
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        ip = get_remote_address(request)
        return f"ip:{ip}"

    def get_rate_limit_key(self, identifier: str, endpoint_type: str) -> str:
        """Generate rate limit key"""
        return f"rate_limit:{endpoint_type}:{identifier}"

    async def is_rate_limited(
        self,
        identifier: str,
        endpoint_type: str,
        limit: Optional[int] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """Check if request is rate limited"""
        current_time = int(time.time())
        window = 60  # 1 minute window
        limit = limit or self.rate_limits.get(endpoint_type, RateLimit.DEFAULT_REQUESTS_PER_MINUTE)
        key = self.get_rate_limit_key(identifier, endpoint_type)

        try:
            # Try Redis first
            if self.redis:
                pipe = self.redis.pipeline()
                pipe.zremrangebyscore(key, 0, current_time - window)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, window)
                results = await pipe.execute()

                request_count = results[1] + 1  # +1 for current request
            else:
                # Fallback to local cache
                local_key = f"local_{key}"
                requests = self.local_cache[local_key]

                # Remove old requests
                while requests and requests[0] < current_time - window:
                    requests.popleft()

                request_count = len(requests) + 1
                requests.append(current_time)

            is_limited = request_count > limit

            return is_limited, {
                'limit': limit,
                'remaining': max(0, limit - request_count),
                'reset_time': current_time + window,
                'current_count': request_count,
                'window': window
            }

        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Fail open - allow request if rate limiting fails
            return False, {'limit': limit, 'remaining': limit - 1}

    async def block_ip(self, ip: str, duration_minutes: int = 60):
        """Block an IP address"""
        block_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.blocked_ips[ip] = block_until

        if self.redis:
            await self.redis.setex(
                f"blocked_ip:{ip}",
                duration_minutes * 60,
                block_until.isoformat()
            )

        logger.warning(f"IP blocked: {ip} until {block_until}")

    async def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        # Check local cache
        if ip in self.blocked_ips:
            if datetime.utcnow() > self.blocked_ips[ip]:
                del self.blocked_ips[ip]
            else:
                return True

        # Check Redis
        if self.redis:
            try:
                blocked_until = await self.redis.get(f"blocked_ip:{ip}")
                if blocked_until:
                    block_time = datetime.fromisoformat(blocked_until)
                    if datetime.utcnow() > block_time:
                        await self.redis.delete(f"blocked_ip:{ip}")
                    else:
                        return True
            except Exception:
                pass

        return False

class IPWhitelistManager:
    """Manage IP whitelists and blacklists"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.whitelist_patterns: List[str] = []
        self.blacklist_patterns: List[str] = []

    def load_ip_lists(self):
        """Load IP lists from configuration"""
        # Load from environment or config
        whitelist_env = settings.get('IP_WHITELIST', '')
        blacklist_env = settings.get('IP_BLACKLIST', '')

        if whitelist_env:
            self.whitelist_patterns = [ip.strip() for ip in whitelist_env.split(',')]

        if blacklist_env:
            self.blacklist_patterns = [ip.strip() for ip in blacklist_env.split(',')]

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist"""
        if not self.whitelist_patterns:
            return True  # No whitelist configured

        try:
            ip_obj = ipaddress.ip_address(ip)
            for pattern in self.whitelist_patterns:
                if '/' in pattern:
                    # CIDR notation
                    network = ipaddress.ip_network(pattern, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    # Exact IP match
                    if ip == pattern:
                        return True
        except ValueError:
            pass

        return False

    def is_ip_blacklisted(self, ip: str) -> bool:
        """Check if IP is in blacklist"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for pattern in self.blacklist_patterns:
                if '/' in pattern:
                    # CIDR notation
                    network = ipaddress.ip_network(pattern, strict=False)
                    if ip_obj in network:
                        return True
                else:
                    # Exact IP match
                    if ip == pattern:
                        return True
        except ValueError:
            pass

        return False

class SecurityMiddleware(BaseHTTPMiddleware):
    """Advanced security middleware"""

    def __init__(
        self,
        app,
        redis_client,
        enable_rate_limiting: bool = True,
        enable_request_validation: bool = True,
        enable_ip_whitelist: bool = False,
        enable_audit_logging: bool = True
    ):
        super().__init__(app)
        self.redis_client = redis_client
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_request_validation = enable_request_validation
        self.enable_ip_whitelist = enable_ip_whitelist
        self.enable_audit_logging = enable_audit_logging

        # Initialize security components
        self.rate_limiter = AdvancedRateLimiter(redis_client)
        self.ip_manager = IPWhitelistManager(redis_client)

        # Security statistics
        self.security_stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_requests': 0,
            'suspicious_requests': 0,
            'blocked_ips': 0
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with security checks"""
        client_ip = get_remote_address(request)
        user_agent = request.headers.get('user-agent', '')

        self.security_stats['total_requests'] += 1

        try:
            # 1. IP Blocking Check
            if await self.rate_limiter.is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return self._create_security_response("Access denied", status.HTTP_403_FORBIDDEN)

            # 2. IP Whitelist Check
            if self.enable_ip_whitelist and not self.ip_manager.is_ip_whitelisted(client_ip):
                logger.warning(f"Non-whitelisted IP attempted access: {client_ip}")
                return self._create_security_response("Access denied", status.HTTP_403_FORBIDDEN)

            # 3. IP Blacklist Check
            if self.ip_manager.is_ip_blacklisted(client_ip):
                logger.warning(f"Blacklisted IP attempted access: {client_ip}")
                return self._create_security_response("Access denied", status.HTTP_403_FORBIDDEN)

            # 4. Rate Limiting Check
            if self.enable_rate_limiting:
                identifier = self.rate_limiter.get_client_identifier(request)
                endpoint_type = self._get_endpoint_type(request)

                is_limited, limit_info = await self.rate_limiter.is_rate_limited(
                    identifier, endpoint_type
                )

                if is_limited:
                    self.security_stats['rate_limited_requests'] += 1

                    # Block IP if excessive rate limiting
                    if limit_info['remaining'] == 0:
                        await self.rate_limiter.block_ip(client_ip, 5)  # 5 minutes
                        self.security_stats['blocked_ips'] += 1

                    return self._create_rate_limit_response(limit_info)

            # Process request
            response = await call_next(request)

            # 5. Security Headers
            self._add_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            raise

    def _get_endpoint_type(self, request: Request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.url.path.lower()

        # Auth endpoints
        if '/auth' in path or '/token' in path:
            return 'auth'

        # File upload endpoints
        if '/upload' in path:
            return 'upload'

        # Sensitive endpoints
        sensitive_paths = ['/admin', '/users', '/organizations', '/teams']
        if any(sp in path for sp in sensitive_paths):
            return 'sensitive'

        return 'api'

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=()',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
        }

        # Add HSTS in production
        if not settings.DEBUG:
            security_headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        for header, value in security_headers.items():
            response.headers[header] = value

    def _create_security_response(self, message: str, status_code: int) -> JSONResponse:
        """Create standardized security response"""
        return JSONResponse(
            status_code=status_code,
            content={
                'error': True,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'security_violation': True
            }
        )

    def _create_rate_limit_response(self, limit_info: Dict[str, Any]) -> JSONResponse:
        """Create rate limit exceeded response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                'error': True,
                'message': 'Rate limit exceeded. Please try again later.',
                'timestamp': datetime.utcnow().isoformat(),
                'security_violation': True,
                'rate_limit_info': {
                    'limit': limit_info['limit'],
                    'remaining': limit_info['remaining'],
                    'reset_time': limit_info['reset_time']
                }
            },
            headers={
                'X-RateLimit-Limit': str(limit_info['limit']),
                'X-RateLimit-Remaining': str(limit_info['remaining']),
                'X-RateLimit-Reset': str(int(limit_info['reset_time'])),
                'Retry-After': '60'
            }
        )

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        return {
            **self.security_stats,
            'blocked_ips_count': len(self.rate_limiter.blocked_ips),
            'whitelist_enabled': self.enable_ip_whitelist,
            'rate_limiting_enabled': self.enable_rate_limiting,
            'request_validation_enabled': self.enable_request_validation,
            'audit_logging_enabled': self.enable_audit_logging
        }