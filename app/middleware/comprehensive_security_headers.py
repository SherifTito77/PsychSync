"""
Comprehensive Security Headers Middleware
Implements OWASP recommended security headers for FastAPI
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class ComprehensiveSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds comprehensive security headers to all responses based on OWASP guidelines.

    Security Headers:
    - X-Content-Type-Options: Prevents MIME-sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Enables browser XSS filtering
    - Strict-Transport-Security: Enforces HTTPS connections
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Controls browser features and APIs
    - Cross-Origin-Opener-Policy: Controls cross-origin window access
    - Cross-Origin-Resource-Policy: Controls cross-origin resource access
    - Cross-Origin-Embedder-Policy: Controls cross-origin embedding
    """

    def __init__(
        self,
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        enable_csp: bool = True,
        csp_directives: dict = None,
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.enable_csp = enable_csp

        # Default CSP directives (strict but functional)
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src": "'self' data: https: blob:",
            "font-src": "'self' https://fonts.gstatic.com",
            "connect-src": "'self' https://api.stripe.com wss://localhost:* ws://localhost:*",
            "frame-src": "'none'",
            "object-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "frame-ancestors": "'none'",
            "navigate-to": "'self'",
        }

        # Build CSP string
        self.csp_string = self._build_csp_string()

    def _build_csp_string(self) -> str:
        """Build Content-Security-Policy header string from directives."""
        if not self.enable_csp:
            return ""

        parts = []
        for directive, value in self.csp_directives.items():
            if value:
                parts.append(f"{directive} {value}")
            else:
                parts.append(directive)

        return "; ".join(parts)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response."""
        response: Response = await call_next(request)

        # 1. X-Content-Type-Options: Prevents MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. X-Frame-Options: Prevents clickjacking (legacy, CSP frame-ancestors is preferred)
        response.headers["X-Frame-Options"] = "DENY"

        # 3. X-XSS-Protection: Enables browser XSS filter (legacy, modern browsers ignore)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict-Transport-Security (HSTS): Enforces HTTPS
        hsts_value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if self.hsts_preload:
            hsts_value += "; preload"

        # Only add HSTS header if the connection is already HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = hsts_value

        # 5. Content-Security-Policy (CSP): Controls resource loading
        if self.csp_string:
            response.headers["Content-Security-Policy"] = self.csp_string

        # 6. Referrer-Policy: Controls referrer information leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy (formerly Feature-Policy): Controls browser features
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

        # 8. Cross-Origin-Opener-Policy (COOP): Controls cross-origin window access
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # 9. Cross-Origin-Resource-Policy (CORP): Controls cross-origin resource access
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # 10. Cross-Origin-Embedder-Policy (COEP): Controls cross-origin embedding
        # Requires COOP to be same-origin as well
        # response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # 11. Cache-Control for sensitive endpoints
        if self._is_sensitive_endpoint(request):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # 12. Remove server header (security by obscurity)
        if "Server" in response.headers:
            del response.headers["Server"]

        # 13. Remove X-Powered-By header (exposes technology)
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        # Log security headers (for debugging, disable in production)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Security headers added to {request.url.path}")

        return response

    def _is_sensitive_endpoint(self, request: Request) -> bool:
        """Check if the endpoint is sensitive and shouldn't be cached."""
        sensitive_paths = [
            "/api/v1/auth/",
            "/api/v1/users/",
            "/api/v1/admin/",
            "/api/v1/assessments/",
            "/api/v1/responses/",
            "/api/v1/clinical/",
        ]
        return any(request.url.path.startswith(path) for path in sensitive_paths)


class ReportingEndpointsMiddleware(BaseHTTPMiddleware):
    """
    Adds Reporting API endpoints for security violation reports.
    Part of the Content Security Policy Level 3 specification.
    """

    def __init__(
        self,
        app: ASGIApp,
        csp_report_endpoint: str = "/api/v1/security/csp-report",
        network_report_endpoint: str = "/api/v1/security/network-report",
    ):
        super().__init__(app)
        self.csp_report_endpoint = csp_report_endpoint
        self.network_report_endpoint = network_report_endpoint

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add Reporting-API headers."""
        response: Response = await call_next(request)

        # Add Reporting-API headers for CSP violations and network errors
        response.headers["Reporting-Endpoints"] = (
            f'csp-endpoint="{self.csp_report_endpoint}", '
            f'network-endpoint="{self.network_report_endpoint}"'
        )

        # Require Report-To header for deprecation period
        response.headers["Report-To"] = (
            f'{{"group":"csp-endpoint","max_age":10886400,"endpoints":[{{"url":"{self.csp_report_endpoint}"}}]}},'
            f'{{"group":"network-endpoint","max_age":10886400,"endpoints":[{{"url":"{self.network_report_endpoint}"}}]}}'
        )

        # Monitor violations in production
        response.headers["Document-Policy"] = "report-violations"

        return response
