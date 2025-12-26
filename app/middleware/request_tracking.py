# app/middleware/request_tracking.py
"""
Request Tracking Middleware for PsychSync
Provides request ID tracking, performance monitoring, and security logging
"""

import time
import uuid
import asyncio
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.structured_logging import get_logger, EventType, LogLevel

logger = get_logger(__name__)

class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track requests with unique IDs and monitor performance
    """

    def __init__(self, app,
                 exclude_paths: Optional[list] = None,
                 include_health_check: bool = False):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/"
        ]
        self.include_health_check = include_health_check

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for use in other components
        request.state.request_id = request_id

        # Skip tracking for excluded paths
        if not self.include_health_check and self._should_exclude_path(request.url.path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Extract request information
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_string = str(request.url.query) if request.url.query else None

        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Set logging context
        logger.set_context(
            request_id=request_id,
            ip_address=client_ip,
            user_agent=user_agent,
            endpoint=method + " " + path,
            method=method
        )

        # Log request start
        logger.info(
            EventType.API_CALL,
            f"Request started: {method} {path}",
            operation_name="request_start",
            request_id=request_id,
            method=method,
            path=path,
            query_string=query_string,
            client_ip=client_ip,
            user_agent=user_agent
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Add performance headers
            response.headers["X-Response-Time-MS"] = str(round(duration_ms, 2))

            # Log successful response
            logger.log_api_call(
                endpoint=f"{method} {path}",
                method=method,
                user_id=getattr(request.state, 'user_id', None),
                status_code=response.status_code,
                duration_ms=duration_ms,
                query_string=query_string,
                client_ip=client_ip
            )

            return response

        except HTTPException as e:
            # Handle HTTP exceptions
            duration_ms = (time.time() - start_time) * 1000

            # Log HTTP exception
            logger.log_api_call(
                endpoint=f"{method} {path}",
                method=method,
                user_id=getattr(request.state, 'user_id', None),
                status_code=e.status_code,
                duration_ms=duration_ms,
                error_details={"detail": e.detail},
                query_string=query_string,
                client_ip=client_ip
            )

            # Create JSON response with request ID
            response = JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "message": e.detail,
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-MS"] = str(round(duration_ms, 2))

            return response

        except Exception as e:
            # Handle unexpected exceptions
            duration_ms = (time.time() - start_time) * 1000

            # Log unexpected error
            logger.log_error(
                error=e,
                operation=f"{method} {path}",
                user_id=getattr(request.state, 'user_id', None),
                duration_ms=duration_ms,
                query_string=query_string,
                client_ip=client_ip
            )

            # Create error response with request ID
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-MS"] = str(round(duration_ms, 2))

            return response

        finally:
            # Clear logging context
            logger.clear_context()

    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from tracking"""
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, accounting for proxy headers"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the forwarded list
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if hasattr(request, 'client') and request.client:
            return request.client.host

        return "unknown"

class SecurityMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor security-related events and potential attacks
    """

    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {
            "auth_endpoints": {"window": 300, "max_requests": 10},  # 5 minutes, 10 requests
            "general": {"window": 60, "max_requests": 100}  # 1 minute, 100 requests
        }
        self.request_history: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Check rate limiting
        if self._is_rate_limited(client_ip, path):
            logger.warning(
                EventType.AUTHORIZATION,
                f"Rate limit exceeded for IP: {client_ip}",
                operation_name="rate_limit_check",
                client_ip=client_ip,
                path=path
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time()
                }
            )

        # Check for suspicious patterns
        suspicious_activity = self._check_suspicious_activity(request)
        if suspicious_activity:
            logger.warning(
                EventType.AUTHORIZATION,
                f"Suspicious activity detected from IP: {client_ip}",
                operation_name="security_monitoring",
                client_ip=client_ip,
                suspicious_activity=suspicious_activity
            )

        response = await call_next(request)
        return response

    def _is_rate_limited(self, client_ip: str, path: str) -> bool:
        """Check if IP has exceeded rate limits"""
        import time
        current_time = time.time()

        # Determine which rate limit to apply
        if self._is_auth_endpoint(path):
            config = self.rate_limits["auth_endpoints"]
        else:
            config = self.rate_limits["general"]

        # Initialize history for IP if not exists
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []

        # Clean old requests outside the window
        self.request_history[client_ip] = [
            timestamp for timestamp in self.request_history[client_ip]
            if current_time - timestamp < config["window"]
        ]

        # Add current request
        self.request_history[client_ip].append(current_time)

        # Check if limit exceeded
        return len(self.request_history[client_ip]) > config["max_requests"]

    def _is_auth_endpoint(self, path: str) -> bool:
        """Check if path is an authentication endpoint"""
        auth_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/token"
        ]
        return any(path.startswith(auth_path) for auth_path in auth_paths)

    def _check_suspicious_activity(self, request: Request) -> Optional[Dict[str, Any]]:
        """Check for suspicious request patterns"""
        suspicious_indicators = []

        # Check for SQL injection patterns
        sql_patterns = ["'", "--", "/*", "*/", "xp_", "sp_", "drop", "delete", "insert", "update"]
        query_string = str(request.url.query).lower()
        for pattern in sql_patterns:
            if pattern in query_string:
                suspicious_indicators.append(f"SQL injection pattern: {pattern}")

        # Check for XSS patterns
        xss_patterns = ["<script", "javascript:", "onload=", "onerror=", "<iframe"]
        for pattern in xss_patterns:
            if pattern in query_string:
                suspicious_indicators.append(f"XSS pattern: {pattern}")

        # Check for path traversal
        path_traversal_patterns = ["../", "..\\", "%2e%2e", "%2e%2e%2f"]
        path = request.url.path.lower()
        for pattern in path_traversal_patterns:
            if pattern in path:
                suspicious_indicators.append(f"Path traversal pattern: {pattern}")

        # Check for large headers (potential DoS)
        total_header_size = sum(len(str(value)) for value in request.headers.values())
        if total_header_size > 8192:  # 8KB
            suspicious_indicators.append(f"Large headers: {total_header_size} bytes")

        # Return suspicious indicators if any found
        return {
            "indicators": suspicious_indicators,
            "header_size": total_header_size
        } if suspicious_indicators else None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if hasattr(request, 'client') and request.client:
            return request.client.host

        return "unknown"

# TODO(human): Implement API rate limiting middleware
# This should provide more granular rate limiting based on user tiers,
# endpoint types, and business requirements

class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced API rate limiting with user-based and endpoint-based limits
    """

    def __init__(self, app):
        super().__init__(app)
        self.user_rate_limits = {
            "free": {"requests_per_minute": 60, "requests_per_hour": 1000},
            "basic": {"requests_per_minute": 300, "requests_per_hour": 10000},
            "premium": {"requests_per_minute": 1000, "requests_per_hour": 100000},
            "enterprise": {"requests_per_minute": 5000, "requests_per_hour": 1000000}
        }

        self.endpoint_limits = {
            "/api/v1/auth/login": {"requests_per_minute": 10, "requests_per_hour": 100},
            "/api/v1/auth/register": {"requests_per_minute": 5, "requests_per_hour": 50},
            "/api/v1/assessments": {"requests_per_minute": 100, "requests_per_hour": 5000}
        }

        self.usage_tracker: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get user information from request (if available)
        user_tier = getattr(request.state, 'user_tier', 'free')
        user_id = getattr(request.state, 'user_id', None) or self._get_client_ip(request)
        path = request.url.path

        # Check if user is rate limited
        if self._is_user_rate_limited(user_id, user_tier, path):
            logger.warning(
                EventType.AUTHORIZATION,
                f"User rate limit exceeded: {user_id}",
                operation_name="user_rate_limit",
                user_id=user_id,
                user_tier=user_tier,
                path=path
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "API rate limit exceeded",
                    "request_id": getattr(request.state, 'request_id', None),
                    "timestamp": time.time(),
                    "tier": user_tier
                }
            )

        response = await call_next(request)
        return response

    def _is_user_rate_limited(self, user_id: str, user_tier: str, path: str) -> bool:
        """Check if user has exceeded their rate limits"""
        import time
        current_time = time.time()

        # Initialize user tracking if not exists
        if user_id not in self.usage_tracker:
            self.usage_tracker[user_id] = {
                "requests": [],
                "tier": user_tier
            }

        user_data = self.usage_tracker[user_id]
        user_tier_limits = self.user_rate_limits.get(user_tier, self.user_rate_limits["free"])

        # Clean old requests outside the windows
        user_data["requests"] = [
            req_time for req_time in user_data["requests"]
            if current_time - req_time < 3600  # Keep last hour
        ]

        # Add current request
        user_data["requests"].append(current_time)

        # Check minute-based limit
        minute_requests = [
            req_time for req_time in user_data["requests"]
            if current_time - req_time < 60
        ]

        # Check endpoint-specific limits
        endpoint_limit = self.endpoint_limits.get(path)
        if endpoint_limit:
            if len(minute_requests) > endpoint_limit["requests_per_minute"]:
                return True

        # Check user tier limits
        if len(minute_requests) > user_tier_limits["requests_per_minute"]:
            return True

        if len(user_data["requests"]) > user_tier_limits["requests_per_hour"]:
            return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if hasattr(request, 'client') and request.client:
            return request.client.host

        return "unknown"

    def get_user_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        import time
        current_time = time.time()

        if user_id not in self.usage_tracker:
            return {"user_id": user_id, "usage": "not_tracked"}

        user_data = self.usage_tracker[user_id]

        minute_requests = [
            req_time for req_time in user_data["requests"]
            if current_time - req_time < 60
        ]

        hour_requests = [
            req_time for req_time in user_data["requests"]
            if current_time - req_time < 3600
        ]

        return {
            "user_id": user_id,
            "tier": user_data["tier"],
            "requests_last_minute": len(minute_requests),
            "requests_last_hour": len(hour_requests),
            "total_requests_tracked": len(user_data["requests"])
        }


def setup_request_tracking(app, exclude_paths: Optional[list] = None, include_health_check: bool = False):
    """
    Set up request tracking middleware for a FastAPI application

    Args:
        app: FastAPI application instance
        exclude_paths: List of paths to exclude from tracking
        include_health_check: Whether to include health checks in tracking

    Returns:
        RequestTrackingMiddleware instance for further configuration
    """
    try:
        request_tracking_middleware = RequestTrackingMiddleware(
            app,
            exclude_paths=exclude_paths,
            include_health_check=include_health_check
        )
        app.add_middleware(RequestTrackingMiddleware, exclude_paths=exclude_paths, include_health_check=include_health_check)

        logger.info(EventType.SYSTEM_EVENT, "Request tracking middleware setup completed successfully")
        return request_tracking_middleware

    except Exception as e:
        logger.error(EventType.ERROR_EVENT, f"Failed to setup request tracking middleware: {e}")
        # Fail open - continue without request tracking if setup fails
        return None