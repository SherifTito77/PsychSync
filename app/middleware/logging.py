# app/middleware/logging.py
"""
Structured Request/Response Logging Middleware
Provides comprehensive logging for all API calls with correlation IDs
"""

from collections.abc import Callable
import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.correlation import set_correlation_id, clear_correlation_id

# Configure structured logger
logger = logging.getLogger("psychsync.api")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging of API requests and responses
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list = None,
        log_headers: bool = True,
        log_body: bool = False,
        max_body_size: int = 10000,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
        ]
        self.log_headers = log_headers
        self.log_body = log_body
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Set correlation ID in context for all downstream code
        set_correlation_id(correlation_id)

        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            try:
                response = await call_next(request)
                return response
            finally:
                # Clear correlation context at end of request
                clear_correlation_id()

        # Record start time
        start_time = time.time()

        # Extract request information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        request_id = request.headers.get("x-request-id", correlation_id)

        # Log request
        request_log = {
            "event": "api_request",
            "correlation_id": correlation_id,
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": time.time(),
        }

        # Add headers if enabled
        if self.log_headers:
            request_log["headers"] = dict(request.headers)

        # Add body if enabled (for POST/PUT/PATCH)
        # Skip logging for auth endpoints to avoid consuming the body before OAuth2PasswordRequestForm reads it
        skip_body_logging = "/auth/" in request.url.path or "/token" in request.url.path

        if self.log_body and request.method in ["POST", "PUT", "PATCH"] and not skip_body_logging:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="replace")
                    if len(body_str) > self.max_body_size:
                        body_str = body_str[: self.max_body_size] + "...[truncated]"
                    request_log["body"] = body_str
            except (UnicodeDecodeError, AttributeError) as e:
                # Expected errors - body encoding issues or missing body attribute
                request_log["body"] = f"[Unable to read body: {type(e).__name__}]"
            except Exception as e:
                # Unexpected errors - log with context but don't fail the request
                logger.warning(
                    f"Unexpected error reading request body: {e!s}",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "error_type": type(e).__name__,
                        "correlation_id": correlation_id
                    },
                    exc_info=True
                )
                request_log["body"] = "[Unable to read body]"

        logger.info("API Request", extra=request_log)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Extract response information
            response_content_type = response.headers.get("content-type", "")
            response_size = 0

            # Try to get response size
            if hasattr(response, "body"):
                try:
                    response_size = len(response.body) if response.body else 0
                except (TypeError, AttributeError) as e:
                    # Expected errors - response body might not be a string/bytes or might not have length
                    response_size = 0
                except Exception as e:
                    # Unexpected errors - log but don't fail
                    logger.warning(
                        f"Unexpected error getting response size: {e!s}",
                        extra={
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "error_type": type(e).__name__,
                            "correlation_id": correlation_id
                        },
                        exc_info=True
                    )
                    response_size = 0

            # Log response
            response_log = {
                "event": "api_response",
                "correlation_id": correlation_id,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": response_size,
                "content_type": response_content_type,
                "timestamp": time.time(),
            }

            # Add response headers if enabled
            if self.log_headers:
                response_log["response_headers"] = dict(response.headers)

            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error("API Response - Server Error", extra=response_log)
            elif response.status_code >= 400:
                logger.warning("API Response - Client Error", extra=response_log)
            else:
                logger.info("API Response - Success", extra=response_log)

            # Add correlation ID to response headers
            response.headers["x-correlation-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(round(duration * 1000, 2))

            return response

        except Exception as e:
            # Log error
            duration = time.time() - start_time
            error_log = {
                "event": "api_error",
                "correlation_id": correlation_id,
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
                "duration_ms": round(duration * 1000, 2),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": time.time(),
            }
            logger.error("API Request Failed", extra=error_log, exc_info=True)
            raise
        finally:
            # Clear correlation context at end of request
            clear_correlation_id()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, considering proxies"""
        # Check for forwarded header
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client host
        return request.client.host if request.client else "unknown"


class SecurityEventLogger:
    """
    Logger for security-related events
    """

    @staticmethod
    def log_login_attempt(
        email: str, success: bool, ip: str, user_agent: str, correlation_id: str = None
    ):
        """Log login attempt"""
        event_log = {
            "event": "security_login_attempt",
            "correlation_id": correlation_id,
            "email": email,
            "success": success,
            "ip": ip,
            "user_agent": user_agent,
            "timestamp": time.time(),
        }

        if success:
            logger.info("Login Success", extra=event_log)
        else:
            logger.warning("Login Failed", extra=event_log)

    @staticmethod
    def log_password_change(user_id: str, ip: str, success: bool, correlation_id: str = None):
        """Log password change attempt"""
        event_log = {
            "event": "security_password_change",
            "correlation_id": correlation_id,
            "user_id": user_id,
            "success": success,
            "ip": ip,
            "timestamp": time.time(),
        }

        if success:
            logger.info("Password Change Success", extra=event_log)
        else:
            logger.warning("Password Change Failed", extra=event_log)

    @staticmethod
    def log_permission_denied(
        user_id: str, resource: str, action: str, ip: str, correlation_id: str = None
    ):
        """Log permission denied event"""
        event_log = {
            "event": "security_permission_denied",
            "correlation_id": correlation_id,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip": ip,
            "timestamp": time.time(),
        }
        logger.warning("Permission Denied", extra=event_log)

    @staticmethod
    def log_suspicious_activity(
        description: str, details: dict, severity: str = "medium", correlation_id: str = None
    ):
        """Log suspicious activity"""
        event_log = {
            "event": "security_suspicious_activity",
            "correlation_id": correlation_id,
            "description": description,
            "severity": severity,
            "details": details,
            "timestamp": time.time(),
        }

        if severity == "high":
            logger.error("Suspicious Activity - High Severity", extra=event_log)
        else:
            logger.warning("Suspicious Activity", extra=event_log)


def setup_logging():
    """Configure structured logging for the application"""
    import structlog

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
