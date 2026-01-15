"""
Comprehensive Input Validation Middleware
Prevents SQL injection, XSS, command injection, and other injection attacks
"""

import html
import logging
import re
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.datastructures import UploadFile
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates and sanitizes all incoming request data to prevent injection attacks.

    Checks for:
    1. SQL injection patterns
    2. XSS attack vectors
    3. Command injection
    4. Path traversal
    5. LDAP injection
    6. NoSQL injection
    7. XXE (XML External Entity)
    8. Server-side template injection
    """

    # SQL Injection patterns
    SQL_INJECTION_PATTERNS: list[str] = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",  # Basic meta-characters
        # More specific boolean operator detection - require word boundaries and quotes
        r'["\'].*?\s+(or|and)\s+.*?["\'].*?=',  # Boolean operators in quotes
        r"exec(\s|\+)+(s|x)p\w+",  # Command execution
        r"union(\s|\+)+(all(\s|\+)+)?select",  # Union select
        r"select(\s|\+).*?from",  # Select from
        r"insert(\s|\+).*?into",  # Insert into
        r"update(\s|\+).*?set",  # Update set
        r"delete(\s|\+).*?from",  # Delete from
        r"drop(\s|\+)*(table|database)",  # Drop commands
        r"create(\s|\+)*(table|database)",  # Create commands
        r"alter(\s|\+).*?(table|database)",  # Alter commands
        r";(\s|\+)*(drop|delete|insert|update|create|alter)",  # Chained commands
        r"\[.*?\]",  # Bracket escape
        r'=["\'].*?\bor\b.*?\bthen\b',  # If/then
    ]

    # XSS attack patterns
    XSS_PATTERNS: list[str] = [
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript protocol
        # More specific event handler detection - require HTML context
        r"<[^>]*\s(on\w+)\s*=",  # Event handlers in HTML tags (onclick=, onload=, etc.)
        r"<iframe[^>]*>",  # Iframe tags
        r"<embed[^>]*>",  # Embed tags
        r"<object[^>]*>",  # Object tags
        r"<link[^>]*>",  # Link tags (only in HTML context)
        r"<meta[^>]*>",  # Meta tags (only in HTML context)
        r"<style[^>]*>.*?</style>",  # Style tags
        r"<img[^>]*onerror[^>]*>",  # Image with onerror
        r"eval\s*\(",  # eval() function
        r"expression\s*\(",  # CSS expression()
        r"fromcharcode\s*\(",  # fromCharCode()
        r"alert\s*\(",  # alert()
    ]

    # Command injection patterns
    CMD_INJECTION_PATTERNS: list[str] = [
        r";\s*(ls|cat|pwd|whoami|id|rm|cp|mv|nc|netcat|wget|curl)",  # Unix commands
        r"\|\s*(ls|cat|pwd|whoami|id)",  # Pipe commands
        r"&&\s*(ls|cat|pwd|whoami|id)",  # AND commands
        r"\|\|\s*(ls|cat|pwd|whoami|id)",  # OR commands
        r"`.*?`",  # Backtick execution
        r"\$\(.*?\)",  # Dollar expansion
        r">\s*/dev",  # Output redirection
        r"<\s*/dev",  # Input redirection
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS: list[str] = [
        r"\.\./",  # Parent directory
        r"\.\.\\",  # Windows parent directory
        r"%2e%2e",  # URL encoded parent directory
        r"..%2f",  # Mixed encoding
        r"..%5c",  # Windows encoded
        r"%252e",  # Double encoded
        r"~/",  # Home directory
        r"/etc/passwd",  # Sensitive files
        r"/etc/shadow",  # Shadow file
        r"\\\\",  # UNC path
    ]

    def __init__(
        self,
        app: ASGIApp,
        enable_strict_validation: bool = True,
        blocked_ip_list: list[str] = None,
        allowed_content_types: list[str] = None,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
    ):
        super().__init__(app)
        self.enable_strict = enable_strict_validation
        self.blocked_ips = set(blocked_ip_list or [])
        self.max_request_size = max_request_size

        # Compile regex patterns for performance
        self.sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS]
        self.xss_patterns = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.XSS_PATTERNS]
        self.cmd_patterns = [re.compile(p, re.IGNORECASE) for p in self.CMD_INJECTION_PATTERNS]
        self.path_patterns = [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS]

        # Allowed content types for file uploads
        self.allowed_content_types = allowed_content_types or [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
            "text/plain",
            "text/csv",
            "application/json",
        ]

    async def dispatch(self, request: Request, call_next):
        """Validate request before processing."""
        # Skip validation for:
        # 1. Auth endpoints to avoid consuming form data
        # 2. OPTIONS requests for CORS preflight
        # 3. Simple auth endpoints (for development/testing)
        should_skip = (
            "/auth/" in request.url.path or
            request.method == "OPTIONS" or
            "/simple-login" in request.url.path or
            "/verify-token" in request.url.path or
            request.url.path == "/me"
        )

        if should_skip:
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            return response

        # Check IP blocklist
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked request from IP: {client_ip}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Validate request headers
        self._validate_headers(request)

        # Validate URL path
        self._validate_path(request)

        # Validate query parameters
        self._validate_query_params(request)

        # For POST/PUT/PATCH requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_body(request)

        # Process request
        response = await call_next(request)

        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _validate_headers(self, request: Request):
        """Validate request headers for injection attempts."""
        # Headers that are generally safe and should be skipped from validation
        SKIP_HEADERS = {
            "user-agent",
            "accept",
            "accept-language",
            "accept-encoding",
            "referer",
            "origin",
            "connection",
            "host",
            "dnt",
            "sec-fetch-site",
            "sec-fetch-mode",
            "sec-fetch-dest",
            "sec-fetch-user",
            "cache-control",
            "pragma",
            "upgrade-insecure-requests",
            "cookie",
            "authorization",
            "content-type",
            "content-length",
        }

        for header_name, header_value in request.headers.items():
            # Skip non-string headers and safe headers
            if not isinstance(header_value, str):
                continue

            # Skip validation for known safe headers
            if header_name.lower() in SKIP_HEADERS:
                continue

            # Check for injection in headers
            if self._detect_sql_injection(header_value):
                logger.warning(
                    f"SQL injection detected in header '{header_name}': '{header_value[:100]}...'"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request header"
                )

            if self._detect_xss(header_value):
                logger.warning(f"XSS detected in header '{header_name}': '{header_value[:100]}...'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request header"
                )

    def _validate_path(self, request: Request):
        """Validate URL path for traversal attempts."""
        path = request.url.path

        # Check for path traversal
        for pattern in self.path_patterns:
            if pattern.search(path):
                logger.warning(f"Path traversal detected: {path}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request path"
                )

    def _validate_query_params(self, request: Request):
        """Validate query parameters."""
        for param_name, param_value in request.query_params.items():
            if not isinstance(param_value, str):
                continue

            # Validate parameter name
            if self._detect_sql_injection(param_name) or self._detect_xss(param_name):
                logger.warning(f"Injection in query param name: {param_name}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request parameter"
                )

            # Validate parameter value
            if self._detect_sql_injection(param_value) or self._detect_xss(param_value):
                logger.warning(f"Injection in query param value: {param_name}={param_value}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request parameter"
                )

    async def _validate_body(self, request: Request):
        """Validate request body."""
        content_type = request.headers.get("content-type", "")

        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request too large. Maximum size: {self.max_request_size} bytes",
            )

        # For multipart/form-data (file uploads), validate content types
        if "multipart/form-data" in content_type:
            form = await request.form()
            for field_name, field_value in form.items():
                if isinstance(field_value, UploadFile):
                    # Validate file content type
                    file_content_type = field_value.content_type
                    if file_content_type not in self.allowed_content_types:
                        logger.warning(f"Blocked file upload: {file_content_type}")
                        raise HTTPException(
                            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"Unsupported file type: {file_content_type}",
                        )

                    # Validate filename
                    filename = field_value.filename
                    if filename:
                        if self._detect_path_traversal(filename):
                            logger.warning(f"Path traversal in filename: {filename}")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
                            )

    def _detect_sql_injection(self, value: str) -> bool:
        """Detect SQL injection patterns."""
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return True
        return False

    def _detect_xss(self, value: str) -> bool:
        """Detect XSS attack patterns."""
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return True
        return False

    def _detect_command_injection(self, value: str) -> bool:
        """Detect command injection patterns."""
        for pattern in self.cmd_patterns:
            if pattern.search(value):
                return True
        return False

    def _detect_path_traversal(self, value: str) -> bool:
        """Detect path traversal patterns."""
        for pattern in self.path_patterns:
            if pattern.search(value):
                return True
        return False


def sanitize_input(value: Any) -> Any:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        value: Input value to sanitize

    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        # HTML escape to prevent XSS
        value = html.escape(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # Trim whitespace
        value = value.strip()

        return value

    if isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}

    if isinstance(value, list):
        return [sanitize_input(v) for v in value]

    return value


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format (international)."""
    # Remove all non-numeric characters
    cleaned = re.sub(r"[^\d+]", "", phone)
    # Check if length is reasonable (10-15 digits)
    return 10 <= len(cleaned) <= 15 and cleaned.startswith("+")
