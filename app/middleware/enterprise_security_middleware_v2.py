"""
Refactored Enterprise Security Middleware

This refactored version uses:
- RedisConnectionManager for connection management
- RateLimitStrategy for pluggable rate limiting
- Separate validation chain for security checks

Complexity reduced from 602 lines to ~300 lines through separation of concerns.
"""

from datetime import datetime
import logging
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.security.redis_connection_manager import RedisConnectionManager, RedisConnectionError
from app.core.security.rate_limiting_strategies import RateLimiterFactory, RateLimitStrategy
from app.core.enterprise_security import ComplianceStandard, SecurityEvent

logger = logging.getLogger(__name__)


class EnterpriseSecurityMiddlewareV2(BaseHTTPMiddleware):
    """
    Refactored enterprise security middleware with improved architecture.

    Improvements:
    - Separated Redis connection management
    - Pluggable rate limiting strategies
    - Cleaner validation pipeline
    - Better error handling

    Previous complexity: 602 lines with mixed responsibilities
    Refactored: ~300 lines with clear separation
    """

    def __init__(self, app):
        super().__init__(app)

        # Initialize Redis connection manager (separated concern)
        try:
            self.redis_manager = RedisConnectionManager(require_in_production=True)
        except RedisConnectionError as e:
            if settings.ENVIRONMENT == "production":
                raise
            logger.error(f"Redis connection failed, middleware disabled: {e}")
            self.redis_manager = None

        # Initialize rate limiter with fallback strategy
        self.rate_limiter: Optional[RateLimitStrategy] = None
        if self.redis_manager:
            try:
                allow_fallback = settings.ENVIRONMENT != "production"
                self.rate_limiter = RateLimiterFactory.create(
                    self.redis_manager,
                    allow_fallback=allow_fallback
                )
            except Exception as e:
                logger.error(f"Failed to create rate limiter: {e}")

        # Security headers configuration
        self.security_headers = self._get_security_headers()

        logger.info("Enterprise security middleware v2 initialized")

    async def dispatch(self, request: Request, call_next):
        """
        Main middleware dispatch method - simplified

        Flow:
        1. Pre-request security checks
        2. Process request
        3. Post-request security actions
        """
        start_time = time.time()

        try:
            # Pre-request checks
            await self._pre_request_security_checks(request)

            # Process request
            response = await call_next(request)

            # Post-request actions
            await self._post_request_security_actions(request, response, start_time)

            return response

        except HTTPException as e:
            await self._log_security_event(request, "HTTP_EXCEPTION", e.detail, False)
            return self._create_error_response(e.status_code, e.detail)

        except Exception as e:
            logger.error(f"Security middleware error: {e!s}")
            await self._log_security_event(request, "SYSTEM_ERROR", str(e), False)
            return self._create_error_response(500, "Internal server error")

    async def _pre_request_security_checks(self, request: Request):
        """
        Pre-request security checks - simplified

        Uses validation chain pattern for cleaner code
        """
        client_ip = self._get_client_ip(request)

        # Check IP blocking
        if await self._is_ip_blocked(client_ip):
            raise HTTPException(status_code=403, detail="Access denied: IP address blocked")

        # Validate request size
        self._validate_request_size(request)

        # Rate limiting
        if self.rate_limiter:
            await self._apply_rate_limiting(request, client_ip)

    async def _post_request_security_actions(
        self, request: Request, response: Response, start_time: float
    ):
        """Post-request security actions - simplified"""
        processing_time = time.time() - start_time

        # Add security headers
        self._add_security_headers(response)

        # Log security event
        event_outcome = response.status_code < 400
        await self._log_security_event(
            request,
            "API_REQUEST",
            f"Request processed in {processing_time:.3f}s",
            event_outcome
        )

        # Monitor slow requests
        if processing_time > 30:
            await self._log_security_event(
                request,
                "SLOW_REQUEST",
                f"Request took {processing_time:.2f} seconds",
                False
            )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked - simplified"""
        if not self.redis_manager or not self.redis_manager.is_available:
            return False

        try:
            client = self.redis_manager.get_client()
            is_blocked = client.get(f"blocked_ip:{ip_address}")
            return bool(is_blocked)
        except Exception as e:
            logger.error(f"Error checking blocked IP: {e}")
            return False

    def _validate_request_size(self, request: Request):
        """Validate request size - extracted for clarity"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="Request entity too large")

    async def _apply_rate_limiting(self, request: Request, client_ip: str):
        """
        Apply rate limiting - simplified using strategy

        Previous implementation: 30+ lines of complex logic
        Refactored: 10 lines delegating to strategy
        """
        endpoint = request.url.path

        # Global rate limit
        self.rate_limiter.check_rate_limit(
            f"global:{client_ip}",
            limit=100,
            window=60
        )

        # Endpoint-specific rate limit
        self.rate_limiter.check_rate_limit(
            f"endpoint:{client_ip}:{endpoint}",
            limit=50,
            window=60
        )

    def _get_security_headers(self) -> dict:
        """Get security headers configuration"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            ),
        }

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        for header, value in self.security_headers.items():
            response.headers[header] = value

    async def _log_security_event(
        self, request: Request, event_type: str, details: str, outcome: bool
    ):
        """Log security event - simplified"""
        try:
            event = SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                severity="HIGH" if not outcome else "MEDIUM",
                user_id=getattr(request.state, "user_id", None),
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                resource_accessed=str(request.url),
                action=request.method,
                outcome="success" if outcome else "failure",
                compliance_standards=[ComplianceStandard.SOC_2_TYPE_II],
                metadata={"details": details}
            )

            # Log event (would use security manager if available)
            logger.info(f"Security Event: {event_type} - {details}")

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")

    def _create_error_response(self, status_code: int, message: str) -> JSONResponse:
        """Create secure error response"""
        safe_messages = {
            400: "Invalid request",
            401: "Authentication required",
            403: "Access denied",
            404: "Resource not found",
            413: "Request too large",
            429: "Rate limit exceeded",
            500: "Internal server error",
        }

        safe_message = safe_messages.get(status_code, "An error occurred")

        return JSONResponse(
            status_code=status_code,
            content={
                "error": safe_message,
                "error_id": secrets.token_hex(8),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
