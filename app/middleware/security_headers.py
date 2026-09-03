# app/middleware/security_headers.py
"""
Comprehensive Security Headers Middleware
- OWASP recommended security headers
- Content Security Policy (CSP)
- HTTPS enforcement
- Clickjacking protection
- XSS protection
- MIME type sniffing protection
- Referrer policy control
- Feature policy/Permissions Policy
- Custom security headers
- HSTS preload support
"""

import logging

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security headers middleware for FastAPI applications

    Implements OWASP recommended security headers and best practices
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        enable_csp: bool = True,
        custom_headers: dict[str, str] | None = None,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.enable_csp = enable_csp
        self.custom_headers = custom_headers or {}
        self.exclude_paths = set(exclude_paths or [])

    async def dispatch(self, request: Request, call_next):
        # Process the request
        response = await call_next(request)

        # Skip security headers for excluded paths (health checks, static files, etc.)
        if self._should_skip_headers(request):
            return response

        # Add comprehensive security headers
        self._add_security_headers(request, response)

        return response

    def _should_skip_headers(self, request: Request) -> bool:
        """Check if security headers should be skipped for this path"""
        path = request.url.path

        # Skip for health checks and monitoring
        if (
            path.startswith("/health")
            or path.startswith("/metrics")
            or path.startswith("/status")
        ):
            return True

        # Skip for static files
        if path.startswith("/static/") or path.startswith("/favicon"):
            return True

        # Skip for documentation
        if (
            path.startswith("/docs")
            or path.startswith("/redoc")
            or path.startswith("/openapi")
        ):
            return True

        # Skip custom excluded paths
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    def _add_security_headers(self, request: Request, response: Response):
        """Add comprehensive security headers to response"""

        # HTTP Strict Transport Security (HSTS)
        if self.enable_hsts and request.url.scheme == "https":
            self._add_hsts_headers(response)

        # Content Security Policy (CSP)
        if self.enable_csp:
            self._add_csp_headers(request, response)

        # X-Frame-Options (Clickjacking Protection)
        self._add_frame_options_headers(response)

        # X-Content-Type-Options (MIME Sniffing Protection)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (Legacy XSS Protection)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        self._add_referrer_policy_headers(response)

        # Permissions Policy (Feature Policy)
        self._add_permissions_policy_headers(response)

        # Cross-Origin Embedder Policy
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Cross-Origin Resource Policy
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Content-Type Options
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cache Control for API responses
        if request.url.path.startswith("/api/"):
            self._add_api_cache_headers(response)

        # Remove server information headers (information leakage prevention)
        for header_to_remove in ["Server", "X-Powered-By", "X-AspNet-Version"]:
            if header_to_remove in response.headers:
                del response.headers[header_to_remove]

        # HIPAA-specific headers for clinical/PHI endpoints
        if self._is_phi_endpoint(request):
            self._add_phi_headers(response)

        # Custom security headers
        for header, value in self.custom_headers.items():
            response.headers[header] = value

    def _add_hsts_headers(self, response: Response):
        """Add HTTP Strict Transport Security headers"""
        max_age = getattr(settings, "HSTS_MAX_AGE", 31536000)  # 1 year
        include_subdomains = getattr(settings, "HSTS_INCLUDE_SUBDOMAINS", True)
        preload = getattr(settings, "HSTS_PRELOAD", False)

        hsts_value = f"max-age={max_age}"

        if include_subdomains:
            hsts_value += "; includeSubDomains"

        if preload:
            hsts_value += "; preload"

        response.headers["Strict-Transport-Security"] = hsts_value

    def _add_csp_headers(self, request: Request, response: Response):
        """Add Content Security Policy headers"""
        csp_config = self._build_csp_policy(request)

        # Add CSP header
        response.headers["Content-Security-Policy"] = csp_config

        # Add CSP report-only header for development
        if getattr(settings, "ENVIRONMENT", "development") == "development":
            csp_report_only = self._build_csp_policy(request, report_only=True)
            response.headers["Content-Security-Policy-Report-Only"] = csp_report_only

    def _build_csp_policy(self, request: Request, report_only: bool = False) -> str:
        """Build Content Security Policy based on environment and request"""
        is_development = (
            getattr(settings, "ENVIRONMENT", "development") == "development"
        )
        is_production = getattr(settings, "ENVIRONMENT", "development") == "production"

        # Base CSP directives
        directives = {
            # Default policy for everything
            "default-src": ["'self'"],
            # Script sources
            "script-src": ["'self'"],
            # Style sources
            "style-src": [
                "'self'",
                "'unsafe-inline'",
            ],  # Inline styles needed for some CSS frameworks
            # Image sources
            "img-src": ["'self'", "data:", "https:"],
            # Font sources
            "font-src": ["'self'", "data:", "https:"],
            # Connect sources (API calls, WebSockets)
            "connect-src": ["'self'"],
            # Frame sources
            "frame-src": ["'none'"],
            # Frame ancestors
            "frame-ancestors": ["'none'"],
            # Form action
            "form-action": ["'self'"],
            # Base URI
            "base-uri": ["'self'"],
            # Manifest
            "manifest-src": ["'self'"],
            # Object sources
            "object-src": ["'none'"],
            # Worker sources
            "worker-src": ["'self'"],
            # Prefetch sources
            "prefetch-src": ["'self'"],
            # Child sources
            "child-src": ["'none'"],
        }

        # Development-specific CSP adjustments
        if is_development:
            # Allow hot reload and dev tools
            directives["script-src"].extend(
                [
                    "'unsafe-eval'",  # Required for hot reload
                    "'unsafe-inline'",  # For development
                    "ws:",  # WebSockets for hot reload
                ]
            )

            # Allow local development servers
            directives["connect-src"].extend(
                [
                    "ws:",
                    "wss:",
                    "http://localhost:*",
                    "https://localhost:*",
                    "http://127.0.0.1:*",
                    "https://127.0.0.1:*",
                ]
            )

        # Production-specific CSP adjustments
        if is_production:
            # Remove unsafe sources in production
            directives["script-src"] = [
                src
                for src in directives["script-src"]
                if src not in ["'unsafe-eval'", "'unsafe-inline'"]
            ]
            directives["style-src"] = [
                src for src in directives["style-src"] if src != "'unsafe-inline'"
            ]

        # Add third-party domains as needed
        allowed_third_parties = getattr(settings, "CSP_ALLOWED_THIRD_PARTIES", [])
        if allowed_third_parties:
            # Add to connect-src for API calls
            directives["connect-src"].extend(allowed_third_parties)

            # Add to script-src for external scripts
            directives["script-src"].extend(allowed_third_parties)

            # Add to style-src for external stylesheets
            directives["style-src"].extend(allowed_third_parties)

        # Add CDN domains
        cdn_domains = getattr(settings, "CSP_CDN_DOMAINS", [])
        if cdn_domains:
            directives["script-src"].extend(cdn_domains)
            directives["style-src"].extend(cdn_domains)
            directives["font-src"].extend(cdn_domains)
            directives["img-src"].extend(cdn_domains)

        # Add CSP violation reporting endpoint
        directives["report-uri"] = ["/api/v1/security/reports"]

        # Build CSP string
        csp_parts = []
        for directive, sources in directives.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")

        return "; ".join(csp_parts)

    def _add_frame_options_headers(self, response: Response):
        """Add X-Frame-Options header for clickjacking protection"""
        # 'DENY' completely prevents framing
        # 'SAMEORIGIN' allows framing from same origin
        # 'ALLOW-FROM uri' allows framing from specific origin

        frame_options = getattr(settings, "X_FRAME_OPTIONS", "DENY")
        response.headers["X-Frame-Options"] = frame_options

    def _add_referrer_policy_headers(self, response: Response):
        """Add Referrer-Policy header"""
        referrer_policy = getattr(
            settings, "REFERRER_POLICY", "strict-origin-when-cross-origin"
        )
        response.headers["Referrer-Policy"] = referrer_policy

    def _add_permissions_policy_headers(self, response: Response):
        """Add Permissions Policy (Feature Policy) header"""
        # Control which browser features can be used
        features = {
            # Geolocation
            "geolocation": [],
            # Camera and microphone
            "camera": [],
            "microphone": [],
            # Payment
            "payment": [],
            # USB
            "usb": [],
            # Magnetometer
            "magnetometer": [],
            # Gyroscope and accelerometer
            "gyroscope": [],
            "accelerometer": [],
            # Ambient light sensor
            "ambient-light-sensor": [],
            # WebVR
            "vr": [],
            # Fullscreen
            "fullscreen": ["'self'"],
            # Screen wake lock
            "wake-lock": [],
            # Web-share API
            "web-share": [],
            # Sync-XHR (XMLHttpRequest)
            "sync-xhr": [],
            # Document domain
            "document-domain": [],
        }

        # Build permissions policy string
        policy_parts = []
        for feature, allowlist in features.items():
            if allowlist:
                policy_parts.append(f"{feature}={' '.join(allowlist)}")
            else:
                policy_parts.append(f"{feature}=()")

        if policy_parts:
            response.headers["Permissions-Policy"] = ", ".join(policy_parts)

    def _is_phi_endpoint(self, request: Request) -> bool:
        """Check if the endpoint handles PHI (Protected Health Information)."""
        phi_prefixes = (
            "/api/v1/clinical/",
            "/api/v1/screening/",
            "/api/v1/users-secure/",
            "/api/v1/responses-secure/",
        )
        return request.url.path.startswith(phi_prefixes)

    def _add_phi_headers(self, response: Response):
        """Add HIPAA-specific security headers for PHI endpoints."""
        # Strict no-cache for PHI data — browser must never store PHI
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Prevent PHI from being included in Referer headers
        response.headers["Referrer-Policy"] = "no-referrer"

        # Mark response as containing sensitive data (non-standard, for proxies/WAFs)
        response.headers["X-Content-Classification"] = "PHI-HIPAA"

    def _add_api_cache_headers(self, response: Response):
        """Add cache control headers for API responses"""
        # Prevent caching of API responses by default
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"


class SecurityReportingMiddleware(BaseHTTPMiddleware):
    """
    Security reporting middleware for CSP violations and other security events
    """

    def __init__(self, app, report_endpoint: str = "/api/v1/security/reports"):
        super().__init__(app)
        self.report_endpoint = report_endpoint

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Handle CSP violation reports
        if request.url.path == self.report_endpoint and request.method == "POST":
            return await self._handle_security_report(request)

        return response

    async def _handle_security_report(self, request: Request):
        """Handle security violation reports (CSP, etc.)"""
        try:
            report_data = await request.json()

            # Log security violation
            logger.warning(
                "Security violation reported",
                extra={
                    "report_type": "csp_violation",
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                    "blocked_uri": report_data.get("csp-report", {}).get("blocked-uri"),
                    "violated_directive": report_data.get("csp-report", {}).get(
                        "violated-directive"
                    ),
                    "document_uri": report_data.get("csp-report", {}).get(
                        "document-uri"
                    ),
                },
            )

            # TODO: Store report in database for analysis
            # TODO: Send alert to security team if critical violation

            return Response(status_code=204)

        except Exception as e:
            logger.error(f"Failed to handle security report: {e!s}")
            return JSONResponse(
                status_code=400, content={"error": "Invalid report format"}
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"


# Factory function for creating security middleware stack
def create_security_middleware_stack(
    app, environment: str = None, custom_config: dict[str, any] = None
) -> None:
    """
    Create and add security middleware stack to FastAPI app

    Args:
        app: FastAPI application instance
        environment: Environment name (development, staging, production)
        custom_config: Custom security configuration
    """
    environment = environment or getattr(settings, "ENVIRONMENT", "development")
    custom_config = custom_config or {}

    # Security headers middleware (always enabled)
    app.add_middleware(
        SecurityHeadersMiddleware,
        enable_hsts=environment == "production",
        enable_csp=True,
        custom_headers=custom_config.get("headers", {}),
        exclude_paths=custom_config.get("exclude_paths", []),
    )

    # Security reporting middleware
    app.add_middleware(
        SecurityReportingMiddleware, report_endpoint="/api/v1/security/reports"
    )
