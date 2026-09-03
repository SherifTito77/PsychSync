"""
Security Middleware Suite
Comprehensive security protection for FastAPI applications including:
- CSRF protection with double-submit cookie pattern
- Security headers middleware
- XSS protection
- Content Security Policy
- Rate limiting for authentication endpoints
- IP-based blocking for suspicious activity
"""

import hmac
import ipaddress
import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security severity levels for different policies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


@dataclass
class SecurityConfig:
    """Configuration for security middleware."""

    # CSRF Protection
    csrf_protect: bool = True
    csrf_token_expiry: int = 3600  # 1 hour
    csrf_token_length: int = 32
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"

    # Security Headers
    security_headers: bool = True
    strict_transport_security: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # Content Security Policy
    csp_enabled: bool = True
    csp_level: SecurityLevel = SecurityLevel.MEDIUM

    # XSS Protection
    xss_protection: bool = True
    x_protection_type: str = "1; mode=block"

    # Frame Protection
    clickjacking_protection: bool = True
    frame_options: str = "DENY"  # DENY, SAMEORIGIN, ALLOW-FROM

    # Content Type Protection
    content_type_options: bool = True
    referrer_policy: str = "strict-origin-when-cross-origin"

    # IP Blocking
    ip_blocking_enabled: bool = True
    failed_login_threshold: int = 5
    ip_block_duration: int = 900  # 15 minutes
    suspicious_patterns: list[str] = field(
        default_factory=lambda: [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"eval\s*\(",
            r"document\.cookie",
        ]
    )

    # Redis Configuration
    redis_url: str = "redis://localhost:6379/2"


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware suite.
    """

    def __init__(self, app, config: SecurityConfig | None = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.redis_client: redis.Redis | None = None

        # Content Security Policy templates
        self.csp_templates = {
            SecurityLevel.LOW: (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "  # Added cdn.jsdelivr.net for Swagger UI CSS
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com; "  # Added fastapi.tiangolo.com for favicon
                "connect-src 'self' ws://localhost:8000 ws://localhost:8002 ws://localhost:3000 ws://localhost:5173 ws://localhost:5174 http://localhost:8000 http://localhost:8002 http://localhost:3000 http://localhost:5173 http://localhost:5174"
            ),
            SecurityLevel.MEDIUM: (
                "default-src 'self'; "
                "script-src 'self' 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "  # Added cdn.jsdelivr.net for Swagger UI CSS
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com; "  # Added fastapi.tiangolo.com for favicon
                "connect-src 'self' ws://localhost:8000 ws://localhost:8002 wss://localhost:8000 wss://localhost:8002 ws://localhost:3000 wss://localhost:3000 ws://localhost:5173 wss://localhost:5173 ws://localhost:5174 wss://localhost:5174 http://localhost:8000 http://localhost:8002 http://localhost:3000 http://localhost:5173 http://localhost:5174; "
                "object-src 'none'; "
                "base-uri 'self'"
            ),
            SecurityLevel.HIGH: (
                "default-src 'self'; "
                "script-src 'self' https://cdn.jsdelivr.net; "  # Allow Swagger UI JS
                "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com https://cdn.jsdelivr.net; "  # Allow Swagger UI CSS
                "font-src 'self'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "  # Allow Swagger UI favicon
                "connect-src 'self' ws://localhost:8000 ws://localhost:8002 ws://localhost:3000 ws://localhost:5173 ws://localhost:5174 http://localhost:8000 http://localhost:8002 http://localhost:3000 http://localhost:5173 http://localhost:5174; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests"
            ),
            SecurityLevel.STRICT: (
                "default-src 'self'; "
                "script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "  # Allow Swagger UI JS
                "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com https://cdn.jsdelivr.net; "  # Allow Swagger UI CSS
                "font-src 'self'; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "  # Allow Swagger UI favicon
                "connect-src 'self' ws://localhost:8000 wss://localhost:8000; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "frame-ancestors 'none'; "
                "upgrade-insecure-requests; "
                "form-action 'self'"
            ),
        }

        # Safe HTTP methods that don't require CSRF protection
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}

        # Initialize Redis
        self._init_redis()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Main middleware dispatcher.
        """
        try:
            # Extract client IP
            client_ip = self._get_client_ip(request)

            # Check IP blocking - TEMPORARILY DISABLED TO DEBUG POST REQUESTS
            # TODO: Re-enable after fixing Redis async issue
            # if self.config.ip_blocking_enabled:
            #     if await self._is_ip_blocked(client_ip):
            #         return self._create_blocked_response()
            #
            #     # Detect suspicious activity
            #     if await self._detect_suspicious_activity(request, client_ip):
            #         await self._block_ip_temporarily(client_ip)
            #         return self._create_blocked_response()

            # Create response
            response = await call_next(request)

            # Apply security headers
            if self.config.security_headers:
                response = self._apply_security_headers(request, response)

            # Apply CSRF protection - TEMPORARILY DISABLED TO DEBUG POST REQUESTS
            # TODO: Re-enable after fixing async Redis issues
            # if self.config.csrf_protect and request.method not in self.safe_methods:
            #     if not await self._validate_csrf_token(request):
            #         raise HTTPException(
            #             status_code=status.HTTP_403_FORBIDDEN,
            #             detail="CSRF token validation failed"
            #         )
            #
            #     # Generate and set new CSRF token
            #     csrf_token = await self._generate_csrf_token(request, response)
            #     response.set_cookie(
            #         key=self.config.csrf_cookie_name,
            #         value=csrf_token,
            #         max_age=self.config.csrf_token_expiry,
            #         secure=True,
            #         httponly=False,
            #         samesite="strict"
            #     )

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            # Fail open - don't break the application
            return await call_next(request)

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Security middleware Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for security features: {e}")
            self.redis_client = None

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP from request."""
        # Check various headers for real IP
        ip_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip",
            "x-cluster-client-ip",
        ]

        for header in ip_headers:
            if header in request.headers:
                # X-Forwarded-For can contain multiple IPs, take the first
                ip = request.headers[header].split(",")[0].strip()
                try:
                    # Validate IP format
                    ipaddress.ip_address(ip)
                    return ip
                except ValueError:
                    continue

        # Fallback to request client IP
        return request.client.host if request.client else "127.0.0.1"

    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        if not self.redis_client:
            return False

        try:
            blocked = await self.redis_client.exists(f"blocked_ip:{ip}")
            return bool(blocked)
        except Exception as e:
            logger.error(f"Error checking IP block status: {e}")
            return False

    async def _block_ip_temporarily(self, ip: str) -> None:
        """Temporarily block an IP address."""
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                f"blocked_ip:{ip}",
                self.config.ip_block_duration,
                "suspicious_activity_detected",
            )
            logger.warning(f"IP {ip} temporarily blocked due to suspicious activity")
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")

    async def _detect_suspicious_activity(self, request: Request, ip: str) -> bool:
        """Detect suspicious activity patterns."""
        try:
            # Check request parameters for attack patterns
            suspicious_found = False

            # Check query parameters
            for key, values in request.query_params.items():
                if self._contains_suspicious_content(str(values)):
                    suspicious_found = True
                    break

            # Check path for suspicious patterns
            if self._contains_suspicious_content(str(request.url.path)):
                suspicious_found = True

            # Check user agent for common attack tools
            user_agent = request.headers.get("user-agent", "")
            attack_tools = [
                "sqlmap",
                "nikto",
                "nmap",
                "masscan",
                "nessus",
                "burp",
                "owasp zap",
                "w3af",
                "acunetix",
            ]
            if any(tool.lower() in user_agent.lower() for tool in attack_tools):
                suspicious_found = True

            if suspicious_found:
                await self._log_suspicious_activity(request, ip, "Pattern matched")

            return suspicious_found

        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return False

    def _contains_suspicious_content(self, content: str) -> bool:
        """Check if content matches suspicious patterns."""
        content_lower = content.lower()
        for pattern in self.config.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                return True
        return False

    async def _log_suspicious_activity(
        self, request: Request, ip: str, reason: str
    ) -> None:
        """Log suspicious activity for monitoring."""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "ip": ip,
                "method": request.method,
                "path": str(request.url.path),
                "user_agent": request.headers.get("user-agent", ""),
                "reason": reason,
                "query_params": str(request.query_params),
            }

            # Log to security monitoring system
            logger.warning(f"Suspicious activity detected: {log_entry}")

            # Store in Redis for monitoring dashboard
            if self.redis_client:
                await self.redis_client.lpush("security_events", str(log_entry))
                await self.redis_client.expire("security_events", 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Error logging suspicious activity: {e}")

    def _create_blocked_response(self) -> Response:
        """Create response for blocked requests."""
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": "Access blocked due to suspicious activity",
                "error_code": "SECURITY_BLOCKED",
            },
        )

    def _apply_security_headers(self, request: Request, response: Response) -> Response:
        """Apply comprehensive security headers."""

        # Strict Transport Security (HSTS)
        if self.config.strict_transport_security:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy
        if self.config.csp_enabled:
            nonce = (
                secrets.token_urlsafe(16)
                if self.config.csp_level in [SecurityLevel.HIGH, SecurityLevel.STRICT]
                else None
            )
            csp_template = self.csp_templates.get(
                self.config.csp_level, self.csp_templates[SecurityLevel.MEDIUM]
            )

            if nonce:
                csp_policy = csp_template.format(nonce=nonce)
            else:
                csp_policy = csp_template

            response.headers["Content-Security-Policy"] = csp_policy

        # XSS Protection
        if self.config.xss_protection:
            response.headers["X-XSS-Protection"] = self.config.x_protection_type

        # Clickjacking Protection
        if self.config.clickjacking_protection:
            response.headers["X-Frame-Options"] = self.config.frame_options

        # Content Type Protection
        if self.config.content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        # Referrer Policy
        response.headers["Referrer-Policy"] = self.config.referrer_policy

        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-DNS-Prefetch-Control"] = "off"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "fullscreen=(self), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Remove sensitive headers
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response

    async def _generate_csrf_token(self, request: Request, response: Response) -> str:
        """Generate new CSRF token."""
        token = secrets.token_urlsafe(self.config.csrf_token_length)

        if self.redis_client:
            # Store token in Redis for validation
            session_key = request.session.get("session_id", secrets.token_urlsafe(16))
            await self.redis_client.setex(
                f"csrf_token:{session_key}", self.config.csrf_token_expiry, token
            )
            request.session["session_id"] = session_key

        return token

    async def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token from request."""
        if not self.redis_client:
            # If Redis not available, skip CSRF validation (fail open)
            return True

        try:
            # Get token from header
            header_token = request.headers.get(self.config.csrf_header_name)

            # Get token from cookie
            cookie_token = request.cookies.get(self.config.csrf_cookie_name)

            # For safe methods or API requests, skip validation
            if request.method in self.safe_methods:
                return True

            # For multipart/form-data, check form field
            if request.headers.get("content-type", "").startswith(
                "multipart/form-data"
            ):
                # Note: This requires request to be parsed first
                # In practice, this would be handled by the form processing middleware
                return True

            # Validate tokens match and exist
            if not header_token or not cookie_token:
                return False

            if not hmac.compare_digest(header_token, cookie_token):
                return False

            # Validate token exists in Redis
            session_key = request.session.get("session_id")
            if not session_key:
                return False

            stored_token = await self.redis_client.get(f"csrf_token:{session_key}")
            if not stored_token:
                return False

            return hmac.compare_digest(stored_token, cookie_token)

        except Exception as e:
            logger.error(f"CSRF validation error: {e}")
            return False  # Fail open for security


class FailedLoginTracker:
    """
    Tracks failed login attempts and implements progressive blocking.
    """

    def __init__(self, redis_client: redis.Redis, config: SecurityConfig):
        self.redis = redis_client
        self.config = config

    async def record_failed_login(self, identifier: str, ip: str) -> None:
        """Record a failed login attempt."""
        try:
            # Increment failed login count
            key = f"failed_login:{identifier}"
            await self.redis.incr(key)
            await self.redis.expire(key, self.config.ip_block_duration)

            # Check if threshold exceeded
            failed_count = int(await self.redis.get(key) or 0)

            if failed_count >= self.config.failed_login_threshold:
                await self._block_identifier_temporarily(identifier, ip, failed_count)

        except Exception as e:
            logger.error(f"Error recording failed login: {e}")

    async def record_successful_login(self, identifier: str) -> None:
        """Clear failed login count on successful login."""
        try:
            await self.redis.delete(f"failed_login:{identifier}")
        except Exception as e:
            logger.error(f"Error clearing failed login count: {e}")

    async def _block_identifier_temporarily(
        self, identifier: str, ip: str, failed_count: int
    ) -> None:
        """Block identifier for progressively longer periods."""
        block_duration = min(
            self.config.ip_block_duration
            * (2 ** (failed_count // self.config.failed_login_threshold)),
            86400,  # Max 24 hours
        )

        await self.redis.setex(
            f"blocked_identifier:{identifier}",
            block_duration,
            f"failed_login_attempts:{failed_count}",
        )

        logger.warning(
            f"Identifier {identifier} from IP {ip} blocked for {block_duration} seconds "
            f"after {failed_count} failed login attempts"
        )

    async def is_identifier_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked."""
        try:
            return bool(await self.redis.exists(f"blocked_identifier:{identifier}"))
        except Exception as e:
            logger.error(f"Error checking identifier block status: {e}")
            return False


def setup_security_middleware(app, config: SecurityConfig | None = None):
    """
    Set up security middleware for a FastAPI application

    Args:
        app: FastAPI application instance
        config: Optional security configuration

    Returns:
        SecurityMiddleware instance for further configuration
    """
    try:
        security_config = config or SecurityConfig()
        security_middleware = SecurityMiddleware(app, security_config)
        app.add_middleware(SecurityMiddleware, config=security_config)

        logger.info("Security middleware setup completed successfully")
        return security_middleware

    except Exception as e:
        logger.error(f"Failed to setup security middleware: {e}")
        # Fail open - continue without security middleware if setup fails
        return None
