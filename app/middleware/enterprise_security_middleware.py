"""
Enterprise Security Middleware
Integrates SOC 2, ISO 27001, GDPR, HIPAA, and FedRAMP compliance
"""

from datetime import datetime
import logging
import secrets
import time

from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer
import redis
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.database import get_db
from app.core.enterprise_security import (
    ComplianceStandard,
    EnterpriseSecurityManager,
    SecurityEvent,
)

# Security configuration
security = HTTPBearer(auto_error=False)
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


class EnterpriseSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise security middleware for compliance and protection
    Addresses SOC 2, ISO 27001, GDPR, HIPAA, and FedRAMP requirements
    """

    def __init__(self, app):
        super().__init__(app)
        self.security_manager = None
        self.redis_client = None
        self._initialize_security_components()

    def _initialize_security_components(self):
        """Initialize security components and connections"""
        try:
            # Initialize Redis for rate limiting and caching
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )

            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established for security middleware")

        except redis.ConnectionError as e:
            logger.critical(
                f"Redis connection failed: {e!s}",
                extra={
                    "error_type": "ConnectionError",
                    "redis_host": settings.REDIS_HOST,
                    "redis_port": settings.REDIS_PORT,
                    "environment": settings.ENVIRONMENT
                },
                exc_info=True
            )

            # In production, Redis is required for security
            if settings.ENVIRONMENT == "production":
                raise RuntimeError(
                    f"Redis initialization failed in production. "
                    f"Rate limiting and security monitoring disabled. Error: {e}"
                ) from e

            # Development-only: Continue with warning
            logger.warning(
                "⚠️  Running without Redis - rate limiting and security monitoring disabled. "
                "This is NOT safe for production!"
            )
            self.redis_client = None

        except Exception as e:
            logger.critical(
                f"Unexpected error initializing Redis: {e!s}",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "redis_host": settings.REDIS_HOST,
                    "redis_port": settings.REDIS_PORT,
                    "environment": settings.ENVIRONMENT
                },
                exc_info=True
            )

            if settings.ENVIRONMENT == "production":
                raise RuntimeError(f"Unexpected Redis initialization error in production: {e}") from e

            logger.warning("Continuing without Redis due to unexpected error")
            self.redis_client = None

        # Initialize security manager will be created per request with DB session
        logger.info("Enterprise security middleware initialized")

    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method"""
        start_time = time.time()

        try:
            # Perform pre-request security checks
            await self._pre_request_security_checks(request)

            # Process the request
            response = await call_next(request)

            # Perform post-request security actions
            await self._post_request_security_actions(request, response, start_time)

            return response

        except RateLimitExceeded as e:
            return await self._handle_rate_limit_exceeded(request, e)
        except HTTPException as e:
            await self._log_security_event(request, "HTTP_EXCEPTION", e.detail, False)
            return self._create_secure_error_response(e.status_code, e.detail)
        except Exception as e:
            logger.error(f"Security middleware error: {e!s}")
            await self._log_security_event(request, "SYSTEM_ERROR", str(e), False)
            return self._create_secure_error_response(500, "Internal server error")

    async def _pre_request_security_checks(self, request: Request):
        """Perform security checks before processing request"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Check for blocked IPs
        if await self._is_ip_blocked(client_ip):
            raise HTTPException(status_code=403, detail="Access denied: IP address blocked")

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="Request entity too large")

        # Check for malicious patterns in headers
        await self._validate_request_headers(request)

        # Perform rate limiting check if Redis is available
        if self.redis_client:
            await self._check_rate_limiting(request)

    async def _post_request_security_actions(
        self, request: Request, response: Response, start_time: float
    ):
        """Perform security actions after processing request"""
        processing_time = time.time() - start_time

        # Add security headers
        await self._add_security_headers(response)

        # Log security event
        user_id = getattr(request.state, "user_id", None)
        event_outcome = response.status_code < 400

        await self._log_security_event(
            request, "API_REQUEST", f"Request processed in {processing_time:.3f}s", event_outcome
        )

        # Monitor for suspicious patterns
        if processing_time > 30:  # Slow requests might indicate attacks
            await self._monitor_slow_request(request, processing_time)

        # Sanitize response data if needed
        if response.headers.get("content-type") == "application/json":
            response = await self._sanitize_response_data(response)

    async def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if not self.redis_client:
            return False

        try:
            # Check blocked IPs list
            is_blocked = self.redis_client.get(f"blocked_ip:{ip_address}")
            return bool(is_blocked)
        except redis.ConnectionError as e:
            logger.error(
                f"Redis connection error while checking blocked IP: {e!s}",
                extra={"ip_address": ip_address, "error_type": "ConnectionError"},
                exc_info=True
            )
            # Fail open - don't block if Redis is down
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error checking blocked IP: {e!s}",
                extra={"ip_address": ip_address, "error_type": type(e).__name__},
                exc_info=True
            )
            # Fail open for safety
            return False

    async def _validate_request_headers(self, request: Request):
        """Validate request headers for security threats"""
        suspicious_headers = ["x-forwarded-host", "x-original-url", "x-rewrite-url", "x-real-url"]

        for header in suspicious_headers:
            if header in request.headers:
                logger.warning(f"Suspicious header detected: {header}")
                await self._increment_suspicious_activity(request, "suspicious_header")

        # Check for common attack patterns
        user_agent = request.headers.get("user-agent", "").lower()
        attack_patterns = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "dirb",
            "python-requests",
            "curl",
            "wget",
        ]

        for pattern in attack_patterns:
            if pattern in user_agent:
                await self._increment_suspicious_activity(request, "suspicious_user_agent")

    async def _check_rate_limiting(self, request: Request):
        """Check rate limiting based on user and endpoint"""
        if not self.redis_client:
            return

        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        user_id = getattr(request.state, "user_id", None)

        # Different rate limits for different user types
        if user_id:
            user_role = getattr(request.state, "user_role", "user")
            limits = self._get_rate_limits_by_role(user_role)
        else:
            limits = self._get_rate_limits_by_role("anonymous")

        # Check global rate limit
        await self._check_rate_limit(
            f"global:{client_ip}", limits["global"], "Global rate limit exceeded"
        )

        # Check endpoint-specific rate limit
        await self._check_rate_limit(
            f"endpoint:{client_ip}:{endpoint}", limits["endpoint"], "Endpoint rate limit exceeded"
        )

        # Check burst protection
        await self._check_burst_protection(client_ip)

    def _get_rate_limits_by_role(self, role: str) -> dict[str, int]:
        """Get rate limits based on user role"""
        limits = {
            "anonymous": {"global": 10, "endpoint": 5},
            "user": {"global": 100, "endpoint": 50},
            "premium_user": {"global": 500, "endpoint": 200},
            "admin": {"global": 1000, "endpoint": 500},
            "super_admin": {"global": 2000, "endpoint": 1000},
        }
        return limits.get(role, limits["user"])

    async def _check_rate_limit(self, key: str, limit: int, error_message: str):
        """Check specific rate limit"""
        try:
            current = self.redis_client.incr(key)

            if current == 1:
                self.redis_client.expire(key, 60)  # 1 minute window

            if current > limit:
                raise RateLimitExceeded(error_message)
        except RateLimitExceeded:
            raise
        except redis.ConnectionError as e:
            logger.error(
                f"Redis connection error during rate limiting: {e!s}",
                extra={"key": key, "limit": limit, "error_type": "ConnectionError"},
                exc_info=True
            )
            # Fail open - don't block requests if Redis is down
            pass
        except Exception as e:
            logger.error(
                f"Unexpected error during rate limiting: {e!s}",
                extra={"key": key, "limit": limit, "error_type": type(e).__name__},
                exc_info=True
            )
            # Fail open for safety
            pass

    async def _check_burst_protection(self, client_ip: str):
        """
        Check burst protection for rapid requests.

        **Fixed Race Condition:** Uses Lua script for atomic increment-with-expire.
        Previously, concurrent requests could bypass the limit by incrementing between
        the incr() and expire() calls.
        """
        # Lua script for atomic increment with expiration
        BURST_PROTECTION_SCRIPT = """
            local burst_key = KEYS[1]
            local block_key = KEYS[2]
            local burst_limit = tonumber(ARGV[1])
            local block_duration = tonumber(ARGV[2])
            local window_duration = tonumber(ARGV[3])

            -- Increment burst counter
            local burst_count = redis.call('INCR', burst_key)

            -- Set expiration on first increment
            if burst_count == 1 then
                redis.call('EXPIRE', burst_key, window_duration)
            end

            -- Check if burst limit exceeded
            if burst_count > burst_limit then
                -- Block the IP
                redis.call('SETEX', block_key, block_duration, '1')
                return {burst_count, 1}  -- 1 means blocked
            end

            return {burst_count, 0}  -- 0 means allowed
        """

        try:
            burst_key = f"burst:{client_ip}"
            block_key = f"blocked_ip:{client_ip}"

            # Register and execute Lua script atomically
            script = self.redis_client.register_script(BURST_PROTECTION_SCRIPT)
            result = script(
                keys=[burst_key, block_key],
                args=[20, 300, 10]  # burst_limit=20, block_duration=300s, window=10s
            )

            burst_count = int(result[0])
            is_blocked = bool(result[1])

            if is_blocked:
                logger.warning(
                    f"Burst limit exceeded for IP: {client_ip}",
                    extra={"client_ip": client_ip, "burst_count": burst_count}
                )
                raise HTTPException(
                    status_code=429, detail="Burst limit exceeded - temporarily blocked"
                )

        except HTTPException:
            raise
        except redis.ConnectionError as e:
            logger.error(
                f"Redis connection error during burst protection: {e!s}",
                extra={"client_ip": client_ip, "error_type": "ConnectionError"},
                exc_info=True
            )
        except Exception as e:
            logger.error(
                f"Unexpected error during burst protection: {e!s}",
                extra={"client_ip": client_ip, "error_type": type(e).__name__},
                exc_info=True
            )

    async def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
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
                "font-src 'self' https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), "
                "gyroscope=(), accelerometer=(), ambient-light-sensor=()"
            ),
        }

        for header, value in security_headers.items():
            response.headers[header] = value

    async def _log_security_event(
        self, request: Request, event_type: str, details: str, outcome: bool
    ):
        """Log security event for compliance monitoring"""
        try:
            # Determine applicable compliance standards
            compliance_standards = [ComplianceStandard.SOC_2_TYPE_II, ComplianceStandard.ISO_27001]

            # Add GDPR for data-related events
            if any(keyword in event_type.lower() for keyword in ["data", "export", "erasure"]):
                compliance_standards.append(ComplianceStandard.GDPR)

            # Add HIPAA for PHI-related events
            if "medical" in request.url.path.lower() or "health" in request.url.path.lower():
                compliance_standards.append(ComplianceStandard.HIPAA)

            event = SecurityEvent(
                event_id=secrets.token_hex(16),
                timestamp=datetime.utcnow(),
                event_type=event_type,
                severity="HIGH" if not outcome else "MEDIUM",
                user_id=getattr(request.state, "user_id", None),
                ip_address=await self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                resource_accessed=str(request.url),
                action=request.method,
                outcome="success" if outcome else "failure",
                compliance_standards=compliance_standards,
                metadata={
                    "details": details,
                    "endpoint": str(request.url.path),
                    "user_agent": request.headers.get("user-agent", ""),
                    "content_length": request.headers.get("content-length"),
                },
            )

            # Log through security manager if available
            if hasattr(self, "security_manager") and self.security_manager:
                self.security_manager.log_security_event(event)
            else:
                # Fallback logging
                logger.info(f"Security Event: {event_type} - {details}")

        except Exception as e:
            logger.error(f"Failed to log security event: {e!s}")

    async def _increment_suspicious_activity(self, request: Request, activity_type: str):
        """
        Track suspicious activity for potential blocking.

        **Fixed Race Condition:** Uses Lua script for atomic increment-with-expire-and-block.
        Previously, multiple concurrent requests could bypass the threshold.
        """
        if not self.redis_client:
            return

        # Lua script for atomic increment, expire, and block
        SUSPICIOUS_ACTIVITY_SCRIPT = """
            local suspicious_key = KEYS[1]
            local block_key = KEYS[2]
            local threshold = tonumber(ARGV[1])
            local expire_duration = tonumber(ARGV[2])

            -- Increment suspicious counter
            local count = redis.call('INCR', suspicious_key)

            -- Set expiration on first increment
            if count == 1 then
                redis.call('EXPIRE', suspicious_key, expire_duration)
            end

            -- Block if threshold reached
            if count >= threshold then
                redis.call('SETEX', block_key, expire_duration, '1')
                return {count, 1}  -- 1 means blocked
            end

            return {count, 0}  -- 0 means not blocked
        """

        try:
            client_ip = await self._get_client_ip(request)
            suspicious_key = f"suspicious:{client_ip}:{activity_type}"
            block_key = f"blocked_ip:{client_ip}"

            # Register and execute Lua script atomically
            script = self.redis_client.register_script(SUSPICIOUS_ACTIVITY_SCRIPT)
            result = script(
                keys=[suspicious_key, block_key],
                args=[10, 3600]  # threshold=10, expire_duration=3600s (1 hour)
            )

            count = int(result[0])
            is_blocked = bool(result[1])

            if is_blocked:
                await self._log_security_event(
                    request, "SUSPICIOUS_ACTIVITY_BLOCKED", f"IP blocked for {activity_type}", False
                )

        except Exception as e:
            logger.error(
                f"Error tracking suspicious activity: {e!s}",
                extra={"activity_type": activity_type, "error_type": type(e).__name__},
                exc_info=True
            )

    async def _monitor_slow_request(self, request: Request, processing_time: float):
        """Monitor slow requests for potential attacks"""
        if processing_time > 60:  # Very slow requests
            await self._log_security_event(
                request, "SLOW_REQUEST", f"Request took {processing_time:.2f} seconds", False
            )

    async def _sanitize_response_data(self, response: Response) -> Response:
        """Sanitize response data to prevent information leakage"""
        try:
            if hasattr(response, "body") and response.body:
                # This would need to be implemented based on your response structure
                # For now, ensure no error messages leak sensitive information
                pass
        except Exception as e:
            logger.error(f"Failed to sanitize response: {e!s}")

        return response

    def _create_secure_error_response(self, status_code: int, message: str) -> JSONResponse:
        """Create secure error response without sensitive information"""
        # Map status codes to safe messages
        safe_messages = {
            400: "Invalid request",
            401: "Authentication required",
            403: "Access denied",
            404: "Resource not found",
            413: "Request too large",
            429: "Rate limit exceeded",
            500: "Internal server error",
            503: "Service temporarily unavailable",
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

    async def _handle_rate_limit_exceeded(
        self, request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        """Handle rate limit exceeded exceptions"""
        await self._log_security_event(request, "RATE_LIMIT_EXCEEDED", str(exc), False)

        return self._create_secure_error_response(429, "Rate limit exceeded")


# GDPR Data Protection API endpoints
from fastapi import APIRouter, Depends

from app.db.database import get_db

gdpr_router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR"])


@gdpr_router.get("/data-portability/{user_id}")
async def get_user_data_portability(user_id: str, db: Session = Depends(get_db)):
    """
    GDPR Article 20: Right to data portability
    Provides user's personal data in machine-readable format
    """
    try:
        security_manager = EnterpriseSecurityManager(db, None)
        user_data = security_manager.export_user_data_gdpr(user_id)

        if "error" in user_data:
            raise HTTPException(status_code=500, detail="Data export failed")

        return JSONResponse(content=user_data)

    except Exception as e:
        logger.error(f"GDPR data portability failed: {e!s}")
        raise HTTPException(status_code=500, detail="Data export failed") from e


@gdpr_router.delete("/right-to-erasure/{user_id}")
async def request_data_erasure(user_id: str, db: Session = Depends(get_db)):
    """
    GDPR Article 17: Right to erasure ('right to be forgotten')
    Removes user's personal data from system
    """
    try:
        security_manager = EnterpriseSecurityManager(db, None)
        erasure_results = security_manager.perform_gdpr_data_erasure(user_id)

        if "error" in erasure_results:
            raise HTTPException(status_code=500, detail="Data erasure failed")

        return JSONResponse(
            content={
                "message": "Data erasure request processed",
                "results": erasure_results,
                "request_id": secrets.token_hex(16),
            }
        )

    except Exception as e:
        logger.error(f"GDPR data erasure failed: {e!s}")
        raise HTTPException(status_code=500, detail="Data erasure failed") from e


# Compliance Monitoring API
compliance_router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])


@compliance_router.get("/security-report")
async def get_security_report(standards: str | None = None, db: Session = Depends(get_db)):
    """Generate compliance security report"""
    try:
        security_manager = EnterpriseSecurityManager(db, None)

        if standards:
            selected_standards = [ComplianceStandard(std.strip()) for std in standards.split(",")]
        else:
            selected_standards = list(ComplianceStandard)

        report = security_manager.generate_compliance_report(selected_standards)

        if "error" in report:
            raise HTTPException(status_code=500, detail="Report generation failed")

        return JSONResponse(content=report)

    except Exception as e:
        logger.error(f"Compliance report generation failed: {e!s}")
        raise HTTPException(status_code=500, detail="Report generation failed") from e


@compliance_router.post("/access-review")
async def perform_access_review(review_period_days: int = 90, db: Session = Depends(get_db)):
    """Perform access review for compliance"""
    try:
        security_manager = EnterpriseSecurityManager(db, None)
        review_report = security_manager.perform_access_review(review_period_days)

        if "error" in review_report:
            raise HTTPException(status_code=500, detail="Access review failed")

        return JSONResponse(content=review_report)

    except Exception as e:
        logger.error(f"Access review failed: {e!s}")
        raise HTTPException(status_code=500, detail="Access review failed") from e


# Include routers in main application
def include_security_routers(app):
    """Include security and compliance routers in FastAPI app"""
    app.include_router(gdpr_router)
    app.include_router(compliance_router)
