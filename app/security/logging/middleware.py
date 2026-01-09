"""
Security Logging Middleware

Automatically logs all API requests/responses for security monitoring.
Extracts user context, request details, and response information.

Usage:
    from fastapi import FastAPI
    from app.security.logging.middleware import SecurityLoggingMiddleware

    app = FastAPI()
    app.add_middleware(SecurityLoggingMiddleware)
"""

from collections.abc import Callable
import json
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from user_agent import parse

from app.security.logging import security_logger
from app.security.logging.schemas import EventSeverity, EventType


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic security logging of all HTTP requests.

    Logs:
    - All API access with user context
    - Failed authentication attempts
    - Privileged operations
    - Data access patterns
    - Suspicious request patterns
    """

    def __init__(
        self,
        app: ASGIApp,
        log_all_requests: bool = True,
        log_bodies: bool = False,  # Set to True for debugging (careful with PII!)
        log_headers: bool = False,  # Set to True for debugging (careful with tokens!)
        skipped_paths: list | None = None,
        log_responses: bool = True
    ):
        super().__init__(app)
        self.log_all_requests = log_all_requests
        self.log_bodies = log_bodies
        self.log_headers = log_headers
        self.log_responses = log_responses

        # Default paths to skip (health checks, metrics, etc.)
        self.skipped_paths = set(skipped_paths or [
            "/health",
            "/metrics",
            "/api/v1/monitoring/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log security events"""

        # Skip logging for certain paths
        if request.url.path in self.skipped_paths:
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Extract request context
        request_context = await self._extract_request_context(request)

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Extract response context
            response_context = self._extract_response_context(response)

            # Log the event
            await self._log_request(request_context, response_context, duration_ms)

            return response

        except Exception as e:
            # Log error
            duration_ms = int((time.time() - start_time) * 1000)

            await self._log_error(
                request_context,
                str(e),
                duration_ms
            )

            raise

    async def _extract_request_context(self, request: Request) -> dict[str, Any]:
        """Extract relevant context from request"""
        context = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }

        # Parse user agent
        if context["user_agent"]:
            ua = parse(context["user_agent"])
            context["ua_browser"] = str(ua.browser.family)
            context["ua_os"] = str(ua.os.family)
            context["ua_device"] = str(ua.device.family)

        # Extract user from JWT (if authenticated)
        context["user_id"] = self._get_user_id(request)
        context["session_id"] = request.headers.get("x-session-id")

        # Log body if enabled (be careful with PII!)
        if self.log_bodies and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    context["body"] = json.loads(body.decode())
            except Exception:
                context["body"] = None

        # Log headers if enabled (be careful with tokens!)
        if self.log_headers:
            context["headers"] = dict(request.headers)

        return context

    def _extract_response_context(self, response: Response) -> dict[str, Any]:
        """Extract relevant context from response"""
        context = {
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
        }

        # Log response body if enabled
        if self.log_responses and self.log_bodies:
            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                context["body"] = json.loads(response_body.decode())

                # Need to recreate response since we consumed the body
                from starlette.responses import Response
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            except Exception:
                pass

        return context

    def _get_client_ip(self, request: Request) -> str | None:
        """Get client IP address, handling proxies"""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return None

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from JWT token"""
        try:
            # This assumes JWT authentication is being used
            # Adjust based on your auth implementation
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Token is in format "Bearer <token>"
                # In production, decode JWT and extract user_id
                # For now, return None and let endpoints handle auth
                pass
        except Exception:
            pass

        return None

    async def _log_request(
        self,
        request_context: dict[str, Any],
        response_context: dict[str, Any],
        duration_ms: int
    ):
        """Log successful request"""

        # Determine event type and severity based on request
        path = request_context["path"]
        method = request_context["method"]
        status_code = response_context["status_code"]
        user_id = request_context.get("user_id")

        # Skip successful GET requests (informational)
        if method == "GET" and 200 <= status_code < 300 and not self.log_all_requests:
            return

        # Determine severity based on status code and endpoint
        if status_code >= 500:
            severity = EventSeverity.HIGH
            description = f"Server error: {method} {path}"
        elif status_code >= 400:
            severity = EventSeverity.MEDIUM
            description = f"Client error: {method} {path}"
        elif self._is_privileged_operation(path):
            severity = EventSeverity.MEDIUM
            description = f"Privileged operation: {method} {path}"
        elif method in ["POST", "PUT", "DELETE", "PATCH"]:
            severity = EventSeverity.LOW
            description = f"Data modification: {method} {path}"
        else:
            severity = EventSeverity.INFO
            description = f"API access: {method} {path}"

        # Create metadata
        metadata = {
            "method": method,
            "path": path,
            "query_params": request_context.get("query_params"),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "content_type": response_context.get("content_type"),
        }

        if request_context.get("ua_browser"):
            metadata["browser"] = request_context["ua_browser"]
            metadata["os"] = request_context["ua_os"]
            metadata["device"] = request_context["ua_device"]

        # Log event
        await security_logger.log_event(
            event={
                "event_type": EventType(f"http.{method.lower()}"),
                "severity": severity,
                "actor_user_id": user_id,
                "actor_ip_address": request_context["client_ip"],
                "actor_user_agent": request_context["user_agent"],
                "actor_session_id": request_context.get("session_id"),
                "resource_type": "api_endpoint",
                "resource_path": path,
                "description": description,
                "status": "success" if status_code < 400 else "error",
                "metadata": metadata,
                "tags": ["http_request", method, path.split("/")[1] if "/" in path else "root"]
            }
        )

    async def _log_error(
        self,
        request_context: dict[str, Any],
        error_message: str,
        duration_ms: int
    ):
        """Log request error"""

        path = request_context["path"]
        method = request_context["method"]
        user_id = request_context.get("user_id")

        await security_logger.log_event(
            event={
                "event_type": EventType.SYSTEM_ERROR,
                "severity": EventSeverity.HIGH,
                "actor_user_id": user_id,
                "actor_ip_address": request_context["client_ip"],
                "actor_user_agent": request_context["user_agent"],
                "resource_path": path,
                "description": f"Request error: {method} {path}",
                "status": "error",
                "outcome": error_message,
                "metadata": {
                    "method": method,
                    "path": path,
                    "error": error_message,
                    "duration_ms": duration_ms,
                },
                "tags": ["error", method]
            }
        )

    def _is_privileged_operation(self, path: str) -> bool:
        """Check if path represents a privileged operation"""
        privileged_prefixes = [
            "/api/v1/admin",
            "/api/v1/users",
            "/api/v1/teams",
            "/api/v1/organizations",
            "/api/v1/assessments",
            "/api/v1/responses",
            "/auth",
        ]

        return any(path.startswith(prefix) for prefix in privileged_prefixes)


class SecurityAuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    Specialized middleware for authentication endpoint logging.

    Provides detailed logging of auth events including:
    - Login attempts (success/failure)
    - Token refresh
    - Password changes
    - MFA events
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process auth request with enhanced logging"""

        # Only process auth endpoints
        if not request.url.path.startswith("/auth"):
            return await call_next(request)

        start_time = time.time()
        request_context = await self._extract_request_context(request)

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            # Log auth event based on endpoint
            await self._log_auth_event(
                request_context,
                response.status_code,
                duration_ms
            )

            return response

        except Exception as e:
            await self._log_auth_failure(request_context, str(e))
            raise

    async def _extract_request_context(self, request: Request) -> dict[str, Any]:
        """Extract auth request context"""
        context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
        }

        # Parse user agent
        if context["user_agent"]:
            ua = parse(context["user_agent"])
            context["ua_browser"] = str(ua.browser.family)
            context["ua_os"] = str(ua.os.family)
            context["ua_device"] = str(ua.device.family)

        # Extract username/email from request body for login attempts
        if request.method in ["POST", "PUT"]:
            try:
                body = await request.body()
                if body:
                    body_data = json.loads(body.decode())
                    context["username"] = body_data.get("email") or body_data.get("username")
            except Exception:
                pass

        return context

    def _get_client_ip(self, request: Request) -> str | None:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return None

    async def _log_auth_event(
        self,
        request_context: dict[str, Any],
        status_code: int,
        duration_ms: int
    ):
        """Log authentication event"""

        path = request_context["path"]
        username = request_context.get("username")

        # Map paths to event types
        event_mapping = {
            "/auth/login": (EventType.AUTH_LOGIN_SUCCESS, EventType.AUTH_LOGIN_FAILURE),
            "/auth/register": (EventType.AUTH_LOGIN_SUCCESS, EventType.AUTH_LOGIN_FAILURE),
            "/auth/logout": (EventType.AUTH_LOGOUT, EventType.AUTH_LOGOUT),
            "/auth/refresh": (EventType.AUTH_TOKEN_REFRESH, EventType.AUTH_TOKEN_REFRESH),
            "/auth/password/change": (EventType.AUTH_PASSWORD_CHANGE, EventType.AUTH_PASSWORD_CHANGE),
            "/auth/mfa/enable": (EventType.AUTH_MFA_ENABLED, EventType.AUTH_MFA_ENABLED),
            "/auth/mfa/disable": (EventType.AUTH_MFA_DISABLED, EventType.AUTH_MFA_DISABLED),
        }

        event_types = event_mapping.get(path)
        if not event_types:
            return

        # Determine success/failure
        event_type = event_types[0] if status_code < 400 else event_types[1]

        # Log auth event
        await security_logger.log_auth_event(
            event_type=event_type,
            username=username,
            ip_address=request_context["client_ip"],
            user_agent=request_context["user_agent"],
            failure_reason=None if status_code < 400 else "authentication_failed",
            is_anomalous=False,  # TODO: Integrate with anomaly detection
            risk_score=0.0,
            metadata={
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "browser": request_context.get("ua_browser"),
                "os": request_context.get("ua_os"),
                "device": request_context.get("ua_device"),
            }
        )

    async def _log_auth_failure(self, request_context: dict[str, Any], error_message: str):
        """Log authentication failure due to exception"""

        await security_logger.log_auth_event(
            event_type=EventType.AUTH_LOGIN_FAILURE,
            username=request_context.get("username"),
            ip_address=request_context["client_ip"],
            user_agent=request_context["user_agent"],
            failure_reason=error_message,
            is_anomalous=False,
            risk_score=50.0,  # Higher risk for exceptions
            metadata={
                "path": request_context["path"],
                "error": error_message,
                "browser": request_context.get("ua_browser"),
                "os": request_context.get("ua_os"),
            }
        )
