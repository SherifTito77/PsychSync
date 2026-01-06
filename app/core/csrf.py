# app/core/csrf.py
"""
CSRF Protection Middleware for PsychSync API
Implements secure CSRF token generation and validation
"""

import hashlib
import os
import secrets

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache_get, cache_set
from app.core.structured_logging import EventType, get_logger

logger = get_logger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware with token-based protection

    This middleware provides:
    - CSRF token generation for authenticated users
    - CSRF token validation for state-changing requests
    - Token expiration and rotation
    - Secure token storage using hashing
    """

    def __init__(
        self,
        app,
        exclude_paths: list[str] = None,
        token_expire_seconds: int = 3600,
        header_name: str = "X-CSRF-Token"
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health", "/docs", "/redoc", "/openapi.json",
            "/api/v1/token", "/api/v1/auth/token", "/api/v1/auth/register", "/api/v1/auth/refresh", "/api/v1/auth/login",
            "/static", "/favicon.ico"
        ]
        self.token_expire_seconds = token_expire_seconds
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe paths and safe HTTP methods
        if self._should_skip_csrf_check(request):
            return await call_next(request)

        # For state-changing operations, validate CSRF token
        if self._requires_csrf_protection(request):
            await self._validate_csrf_token(request)

        # Process the request
        response = await call_next(request)

        # Add new CSRF token to response for safe methods on authenticated requests
        if self._should_generate_token(request):
            new_csrf_token = await self._generate_csrf_token(request)
            response.headers[self.header_name] = new_csrf_token

        return response

    def _should_skip_csrf_check(self, request: Request) -> bool:
        """Check if CSRF protection should be skipped for this request"""
        # Skip CSRF validation in testing mode
        if os.getenv("TESTING") == "True":
            return True

        # Debug logging
        logger.debug(
            EventType.SYSTEM_EVENT,
            f"CSRF check for path: {request.url.path}, method: {request.method}",
            metadata={"exclude_paths": self.exclude_paths}
        )

        # Skip based on path
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            logger.debug(
                EventType.SYSTEM_EVENT,
                f"CSRF check skipped for path: {request.url.path}"
            )
            return True

        # Skip based on HTTP method (safe methods don't need CSRF protection)
        safe_methods = ["GET", "HEAD", "OPTIONS", "TRACE"]
        if request.method.upper() in safe_methods:
            return True

        logger.debug(
            EventType.SYSTEM_EVENT,
            f"CSRF check required for path: {request.url.path}"
        )
        return False

    def _requires_csrf_protection(self, request: Request) -> bool:
        """Check if CSRF token validation is required for this request"""
        # Only required for state-changing methods (POST, PUT, DELETE, PATCH)
        dangerous_methods = ["POST", "PUT", "DELETE", "PATCH"]
        return request.method.upper() in dangerous_methods

    def _should_generate_token(self, request: Request) -> bool:
        """Check if CSRF token should be generated for this request"""
        # Only generate tokens for authenticated users on safe methods
        safe_methods = ["GET", "HEAD"]
        return (
            request.method.upper() in safe_methods and
            self._is_authenticated_request(request)
        )

    async def _validate_csrf_token(self, request: Request):
        """Validate CSRF token from request"""
        csrf_token = self._extract_csrf_token(request)

        if not csrf_token:
            logger.warning(
                EventType.VALIDATION_ERROR,
                "CSRF token missing",
                metadata={
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("User-Agent"),
                    "remote_addr": request.client.host if request.client else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required for state-changing requests"
            )

        # Get user session token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for CSRF-protected requests"
            )

        user_token = auth_header[7:]  # Remove "Bearer "

        # Validate CSRF token against user session
        if not await self._validate_csrf_token_against_session(csrf_token, user_token):
            logger.warning(
                EventType.VALIDATION_ERROR,
                "Invalid CSRF token provided",
                metadata={
                    "path": request.url.path,
                    "method": request.method,
                    "token_length": len(csrf_token),
                    "user_agent": request.headers.get("User-Agent"),
                    "remote_addr": request.client.host if request.client else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )

    def _extract_csrf_token(self, request: Request) -> str | None:
        """Extract CSRF token from various sources"""
        # Check header first (preferred method)
        csrf_token = request.headers.get(self.header_name)
        if csrf_token:
            return csrf_token

        # Check form data
        if hasattr(request, "_form") and request._form:
            csrf_token = request._form.get("csrf_token")
            if csrf_token:
                return csrf_token

        # Check JSON body (if already parsed)
        if hasattr(request, "_json") and request._json:
            csrf_token = request._json.get("csrf_token")
            if csrf_token:
                return csrf_token

        return None

    def _is_authenticated_request(self, request: Request) -> bool:
        """Check if request is from authenticated user"""
        auth_header = request.headers.get("Authorization")
        return auth_header is not None and auth_header.startswith("Bearer ")

    async def _generate_csrf_token(self, request: Request) -> str:
        """Generate CSRF token tied to user session"""
        # Get user token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return ""

        user_token = auth_header[7:]  # Remove "Bearer "

        # Generate cryptographically secure token
        token = secrets.token_urlsafe(32)

        # Store hashed token linked to user session
        session_key = self._get_session_key(user_token)
        await cache_set(session_key, token, expire_seconds=self.token_expire_seconds)

        logger.debug(
            EventType.SYSTEM_EVENT,
            "CSRF token generated",
            metadata={
                "session_key_hash": hashlib.sha256(session_key.encode()).hexdigest()[:16],
                "token_length": len(token)
            }
        )

        return token

    async def _validate_csrf_token_against_session(self, provided_token: str, user_token: str) -> bool:
        """Validate CSRF token against user session"""
        session_key = self._get_session_key(user_token)
        stored_token = await cache_get(session_key)

        if not stored_token:
            logger.warning(
                EventType.AUTHENTICATION,
                "CSRF token expired or not found in session"
            )
            return False

        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(stored_token or "", provided_token)

    def _get_session_key(self, user_token: str) -> str:
        """Generate session key for CSRF token storage"""
        # Hash the user token to create a session identifier
        # This prevents storing the actual JWT token in cache
        return f"csrf:{hashlib.sha256(user_token.encode()).hexdigest()}"


class CSRFProtection:
    """
    Helper class for CSRF protection utilities
    """

    @staticmethod
    def generate_csrf_token_for_user(user_id: str, expire_seconds: int = 3600) -> str:
        """
        Generate CSRF token for specific user (for API usage)
        """
        import time

        token = secrets.token_urlsafe(32)
        timestamp = int(time.time())

        # Create token with timestamp and user ID
        token_data = f"{user_id}:{timestamp}:{token}"
        token_signature = hashlib.sha256(token_data.encode()).hexdigest()

        return f"{token}:{timestamp}:{token_signature}"

    @staticmethod
    def validate_csrf_token_for_user(csrf_token: str, user_id: str, max_age_seconds: int = 3600) -> bool:
        """
        Validate CSRF token for specific user (for API usage)
        """
        try:
            parts = csrf_token.split(":")
            if len(parts) != 3:
                return False

            token, timestamp_str, signature = parts

            # Check timestamp
            timestamp = int(timestamp_str)
            import time
            if time.time() - timestamp > max_age_seconds:
                return False

            # Recreate expected data and verify signature
            expected_data = f"{user_id}:{timestamp_str}:{token}"
            expected_signature = hashlib.sha256(expected_data.encode()).hexdigest()

            return secrets.compare_digest(signature, expected_signature)

        except (ValueError, IndexError):
            return False

    @staticmethod
    def get_csrf_headers() -> dict:
        """
        Get CSRF-related headers for API responses
        """
        return {
            "X-CSRF-Protection": "1; mode=strict",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }


# Global CSRF protection instance
csrf_protection = CSRFProtection()
