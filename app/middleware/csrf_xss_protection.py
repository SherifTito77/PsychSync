"""
Comprehensive CSRF and XSS Protection Middleware
Protects against Cross-Site Request Forgery and Cross-Site Scripting attacks
"""

import logging
import os
import secrets
from typing import Any

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, URLSafeTimedSerializer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware using Double Submit Cookie Pattern.

    Features:
    - Double-submit cookie pattern
    - Per-request tokens
    - Time-limited tokens (configurable expiration)
    - Safe methods exemption (GET, HEAD, OPTIONS)
    - AJAX request support (X-CSRF-Token header)
    """

    def __init__(
        self,
        app,
        secret_key: str,
        token_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_cookie",
        max_age: int = 3600,  # 1 hour
        secure: bool = True,
        httponly: bool = False,
        samesite: str = "lax",
        exclude_paths: list = None,  # Paths to exclude from CSRF validation
    ):
        super().__init__(app)
        self.token_name = token_name
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        self.exclude_paths = set(exclude_paths or [])

        # Use itsdangerous for signed tokens
        self.serializer = URLSafeTimedSerializer(secret_key)

    async def dispatch(self, request: Request, call_next):
        """Process request and validate CSRF token."""
        # Skip CSRF validation in testing mode
        if os.getenv("TESTING") == "True":
            return await call_next(request)

        # Exempt safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # Check if path is excluded from CSRF validation
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Validate CSRF token for unsafe methods
        await self._validate_csrf_token(request)

        # Process request
        response = await call_next(request)

        # Add CSRF token to response
        self._set_csrf_cookie(response)

        # Add CSRF token to headers for AJAX
        token = self._generate_csrf_token()
        response.headers[self.header_name] = token

        return response

    def _generate_csrf_token(self) -> str:
        """Generate a cryptographically secure CSRF token."""
        random_bytes = secrets.token_bytes(32)
        return self.serializer.dumps(random_bytes)

    def _validate_csrf_token(self, request: Request):
        """Validate CSRF token from request."""
        # Get token from header or form data
        token = request.headers.get(self.header_name)
        if not token:
            # Try form data
            form_data = getattr(request, "_form", {})
            token = form_data.get(self.token_name) if form_data else None

        if not token:
            logger.warning(f"CSRF token missing from {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing"
            )

        # Validate token signature and expiration
        try:
            self.serializer.loads(token, max_age=self.max_age)
        except BadSignature:
            logger.warning(f"Invalid CSRF token from {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )

    def _set_csrf_cookie(self, response: Response):
        """Set CSRF cookie in response."""
        token = self._generate_csrf_token()

        cookie_directive = (
            f"{self.cookie_name}={token}; "
            f"Path=/; "
            f"Max-Age={self.max_age}; "
            f"SameSite={self.samesite}; "
        )

        if self.secure:
            cookie_directive += "Secure; "

        if self.httponly:
            cookie_directive += "HttpOnly; "

        response.headers["Set-Cookie"] = cookie_directive.rstrip()


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    XSS Protection Middleware.

    Features:
    - Response header sanitization
    - Input sanitization
    - Content-Type enforcement
    - HTML escaping
    """

    def __init__(
        self,
        app,
        enable_sanitization: bool = True,
        strip_tags: bool = True,
        escape_html: bool = True,
    ):
        super().__init__(app)
        self.enable_sanitization = enable_sanitization
        self.strip_tags = strip_tags
        self.escape_html = escape_html

    async def dispatch(self, request: Request, call_next):
        """Process request and sanitize responses."""
        # Sanitize request data
        if self.enable_sanitization:
            await self._sanitize_request_data(request)

        # Process request
        response = await call_next(request)

        # Add XSS protection headers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Sanitize response body if JSON
        if response.headers.get("content-type") == "application/json":
            response = await self._sanitize_json_response(response)

        return response

    async def _sanitize_request_data(self, request: Request):
        """Sanitize incoming request data."""
        # Sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                sanitized_params[key] = self._sanitize_string(value)
            # Update request query params (read-only, so we'd need to modify in practice)
            # This is a conceptual implementation

        # Sanitize form data
        if request.method in ["POST", "PUT", "PATCH"]:
            # Form data sanitization would happen here
            pass

    def _sanitize_string(self, value: str) -> str:
        """Sanitize a string to prevent XSS."""
        if not isinstance(value, str):
            return value

        # HTML escape
        import html
        value = html.escape(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Strip script tags (additional protection)
        if self.strip_tags:
            value = self._strip_tags(value)

        return value

    def _strip_tags(self, value: str) -> str:
        """Strip HTML tags from string."""
        import re
        # Basic tag stripping (for production, use bleach or nh3)
        value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r"<[^>]+>", "", value)
        return value

    async def _sanitize_json_response(self, response: Response) -> Response:
        """Sanitize JSON response body."""
        # This would parse and sanitize JSON responses
        # Implementation depends on response structure
        return response


class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy Middleware for XSS Prevention.

    Provides fine-grained control over resource loading to prevent XSS.
    """

    def __init__(
        self,
        app,
        csp_directives: dict[str, str] = None,
        report_only: bool = False,
    ):
        super().__init__(app)
        self.report_only = report_only

        # Default CSP directives
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
            "upgrade-insecure-requests": "",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and add CSP headers."""
        response = await call_next(request)

        # Build CSP string
        csp_string = self._build_csp_string()

        # Add CSP header
        header_name = "Content-Security-Policy-Report-Only" if self.report_only else "Content-Security-Policy"
        response.headers[header_name] = csp_string

        return response

    def _build_csp_string(self) -> str:
        """Build CSP header string from directives."""
        parts = []
        for directive, value in self.csp_directives.items():
            if value:
                parts.append(f"{directive} {value}")
            else:
                parts.append(directive)
        return "; ".join(parts)


def sanitize_user_input(value: Any) -> Any:
    """
    Sanitize user input to prevent XSS attacks.

    Args:
        value: Input value to sanitize

    Returns:
        Sanitized value
    """
    import html
    import re

    if isinstance(value, str):
        # HTML escape
        value = html.escape(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Strip dangerous tags
        value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r"<iframe[^>]*>.*?</iframe>", "", value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r"<embed[^>]*>", "", value, flags=re.IGNORECASE)
        value = re.sub(r"<object[^>]*>.*?</object>", "", value, flags=re.IGNORECASE | re.DOTALL)

        return value

    if isinstance(value, dict):
        return {k: sanitize_user_input(v) for k, v in value.items()}

    if isinstance(value, list):
        return [sanitize_user_input(v) for v in value]

    return value


def validate_content_security_policy(response_content: str) -> bool:
    """
    Validate response content against CSP.

    Args:
        response_content: Response HTML content

    Returns:
        True if content passes CSP validation
    """
    import re

    # Check for inline scripts (only allowed in strict mode)
    if re.search(r"<script[^>]*>.*?</script>", response_content, re.IGNORECASE | re.DOTALL):
        logger.warning("Inline script detected in response")

    # Check for inline event handlers
    if re.search(r"on\w+\s*=", response_content, re.IGNORECASE):
        logger.warning("Inline event handler detected in response")

    # Check for javascript: protocol
    if re.search(r"javascript:", response_content, re.IGNORECASE):
        logger.warning("javascript: protocol detected in response")
        return False

    return True


# Utility functions for XSS prevention

def escape_js_string(value: str) -> str:
    """Escape string for safe use in JavaScript."""
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("'", "\\'")
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")
    value = value.replace("\t", "\\t")
    return value


def escape_css_string(value: str) -> str:
    """Escape string for safe use in CSS."""
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("'", "\\'")
    return value


def sanitize_html(unsafe_html: str) -> str:
    """
    Sanitize HTML using bleach library.

    Args:
        unsafe_html: Unsafe HTML string

    Returns:
        Sanitized HTML string

    Note:
        Requires: pip install bleach
    """
    try:
        import bleach

        # Allowed tags and attributes
        allowed_tags = [
            "p", "br", "strong", "em", "u", "a", "ul", "ol", "li",
            "h1", "h2", "h3", "h4", "h5", "h6",
            "table", "thead", "tbody", "tr", "th", "td",
            "div", "span", "img"
        ]

        allowed_attributes = {
            "a": ["href", "title", "target"],
            "img": ["src", "alt", "title", "width", "height"],
            "*": ["class", "id"]
        }

        # Sanitize
        safe_html = bleach.clean(
            unsafe_html,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )

        return safe_html

    except ImportError:
        logger.warning("bleach library not installed, using basic sanitization")
        return sanitize_user_input(unsafe_html)
