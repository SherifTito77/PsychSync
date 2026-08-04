"""
Unified Security Middleware - Main Orchestrator

Consolidates all security middleware into a single, modular system.
Uses composition to enable/disable security features as needed.

This replaces 7+ duplicate SecurityMiddleware classes (~3,500 lines) with
one unified, configurable implementation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.security_unified.utils import (
    detect_attack_tool,
    get_client_info,
    get_client_ip,
    get_csp_template,
    get_security_headers_default,
    is_private_ip,
    is_sensitive_endpoint,
    is_suspicious_path,
)

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Configuration for unified security middleware."""

    # Feature toggles
    security_headers_enabled: bool = True
    csrf_protection_enabled: bool = True
    ip_blocking_enabled: bool = True
    attack_detection_enabled: bool = True
    request_logging_enabled: bool = False

    # Security Headers Configuration
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    csp_level: str = "medium"  # low, medium, high, strict

    # CSRF Configuration
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_token_expiry: int = 3600  # 1 hour
    csrf_safe_methods: set = field(
        default_factory=lambda: {"GET", "HEAD", "OPTIONS", "TRACE"}
    )

    # IP Blocking Configuration
    failed_login_threshold: int = 5
    ip_block_duration: int = 900  # 15 minutes
    max_requests_per_minute: int = 60

    # Attack Detection Configuration
    block_known_attack_tools: bool = True
    log_suspicious_paths: bool = True

    # Exclusions
    exclude_paths: set = field(
        default_factory=lambda: {"/health", "/metrics", "/docs", "/redoc"}
    )
    exclude_ips: set = field(default_factory=set)  # IPs to skip security checks


class UnifiedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Unified security middleware consolidating all security features.

    Features:
    - Security headers (OWASP compliant)
    - CSRF protection
    - IP-based blocking
    - Attack tool detection
    - Request logging
    - Suspicious activity detection

    This replaces multiple duplicate security middleware implementations.
    """

    def __init__(self, app, config: SecurityConfig | None = None):
        super().__init__(app)
        self.config = config or SecurityConfig()

        # Runtime state
        self._blocked_ips: dict[str, dict[str, Any]] = {}
        self._failed_attempts: dict[str, int] = {}
        self._suspicious_ips: set[str] = set()

        # Pre-compile CSP template
        self._csp_template = get_csp_template(self.config.csp_level)

        logger.info(
            f"Unified Security Middleware initialized with: "
            f"headers={self.config.security_headers_enabled}, "
            f"csrf={self.config.csrf_protection_enabled}, "
            f"ip_blocking={self.config.ip_blocking_enabled}, "
            f"attack_detection={self.config.attack_detection_enabled}"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Main middleware dispatcher - applies all security checks.

        Security flow:
        1. Check exclusions (path/IP)
        2. Extract client info
        3. Apply attack detection
        4. Apply IP blocking
        5. Apply CSRF validation
        6. Process request
        7. Apply security headers to response
        8. Log security events
        """
        start_time = datetime.utcnow()

        # 1. Check exclusions
        if self._should_skip_security(request):
            return await call_next(request)

        # 2. Extract client information
        client_ip = get_client_ip(request)
        client_info = get_client_info(request)

        # 3. Attack Detection
        if self.config.attack_detection_enabled:
            attack_result = await self._check_attack_patterns(
                request, client_ip, client_info
            )
            if attack_result:
                return attack_result  # Block request

        # 4. IP Blocking
        if self.config.ip_blocking_enabled:
            block_result = await self._check_ip_block(client_ip, request)
            if block_result:
                return block_result  # Block request

        # 5. CSRF Protection (for unsafe methods)
        if (
            self.config.csrf_protection_enabled
            and request.method not in self.config.csrf_safe_methods
        ):
            csrf_result = await self._validate_csrf(request)
            if csrf_result:
                return csrf_result  # Block request

        # 6. Process the actual request
        try:
            response = await call_next(request)

            # 7. Apply Security Headers
            if self.config.security_headers_enabled:
                response = self._apply_security_headers(request, response)

            # 8. Add CSRF token to response
            if self.config.csrf_protection_enabled:
                response = await self._add_csrf_token(request, response)

            return response

        except HTTPException as e:
            # Track failed attempts for IP blocking
            if self.config.ip_blocking_enabled and e.status_code >= 400:
                await self._track_failed_attempt(client_ip, request)

            raise

        finally:
            # Log security events
            if self.config.request_logging_enabled:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self._log_security_event(request, client_info, duration)

    def _should_skip_security(self, request: Request) -> bool:
        """Check if request should skip security checks."""
        # Skip excluded paths
        if request.url.path in self.config.exclude_paths:
            return True

        # Skip excluded IPs
        client_ip = get_client_ip(request)
        if client_ip in self.config.exclude_ips:
            return True

        # Skip private IPs if configured (e.g., internal monitoring)
        if is_private_ip(client_ip) and client_ip in self.config.exclude_ips:
            return True

        return False

    async def _check_attack_patterns(
        self, request: Request, client_ip: str, client_info: dict
    ) -> Response | None:
        """
        Check for attack tool signatures and suspicious patterns.

        Returns blocking response if attack detected, None otherwise.
        """
        # Check for known attack tools in User-Agent
        user_agent = client_info.get("user_agent", "")

        if self.config.block_known_attack_tools:
            detected_tool = detect_attack_tool(user_agent)
            if detected_tool:
                logger.warning(
                    f"Attack tool detected: {detected_tool} from {client_ip}",
                    extra={
                        "tool": detected_tool,
                        "ip": client_ip,
                        "user_agent": user_agent,
                        "path": request.url.path,
                    },
                )
                return self._create_blocked_response(
                    f"Attack tool '{detected_tool}' detected", 403
                )

        # Check for suspicious paths
        if self.config.log_suspicious_paths and is_suspicious_path(request.url.path):
            logger.warning(
                f"Suspicious path detected from {client_ip}: {request.url.path}",
                extra={
                    "ip": client_ip,
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": user_agent,
                },
            )
            # Mark IP as suspicious (don't block yet)
            self._suspicious_ips.add(client_ip)

        return None

    async def _check_ip_block(
        self, client_ip: str, request: Request
    ) -> Response | None:
        """
        Check if IP is currently blocked.

        Returns blocking response if IP is blocked, None otherwise.
        """
        # Check if IP is in blocked list
        if client_ip in self._blocked_ips:
            block_info = self._blocked_ips[client_ip]

            # Check if block has expired
            if datetime.utcnow().timestamp() > block_info["expires_at"]:
                # Block expired, remove it
                del self._blocked_ips[client_ip]
                logger.info(f"IP block expired for {client_ip}")
                return None

            # Still blocked
            logger.warning(
                f"Blocked IP attempted access: {client_ip} -> {request.url.path}",
                extra={"ip": client_ip, "path": request.url.path},
            )
            return self._create_blocked_response(
                f"Too many failed attempts. Try again later.", 429
            )

        return None

    async def _validate_csrf(self, request: Request) -> Response | None:
        """
        Validate CSRF token for unsafe methods.

        Returns error response if validation fails, None otherwise.
        """
        # Check if path is excluded from CSRF
        if request.url.path in self.config.exclude_paths:
            return None

        # Get token from header
        token = request.headers.get(self.config.csrf_header_name)

        if not token:
            logger.warning(
                f"CSRF token missing from {get_client_ip(request)}",
                extra={"ip": get_client_ip(request), "path": request.url.path},
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Please reload the page."},
            )

        # TODO: Validate token signature (requires token storage)
        # For now, just check presence
        return None

    async def _add_csrf_token(self, request: Request, response: Response) -> Response:
        """Add CSRF token to response."""
        # Only add CSRF token to safe methods or after successful validation
        if request.method in self.config.csrf_safe_methods:
            # TODO: Generate and sign token
            token = "placeholder_token"  # Would be cryptographically secure

            # Add to headers for AJAX requests
            response.headers[self.config.csrf_header_name] = token

        return response

    async def _track_failed_attempt(self, client_ip: str, request: Request):
        """Track failed login/security attempts for IP blocking."""
        # Increment failed attempt counter
        self._failed_attempts[client_ip] = self._failed_attempts.get(client_ip, 0) + 1

        failed_count = self._failed_attempts[client_ip]

        logger.warning(
            f"Failed attempt #{failed_count} from {client_ip}",
            extra={"ip": client_ip, "path": request.url.path},
        )

        # Check if threshold reached
        if failed_count >= self.config.failed_login_threshold:
            # Block the IP
            block_duration = self.config.ip_block_duration
            expires_at = datetime.utcnow().timestamp() + block_duration

            self._blocked_ips[client_ip] = {
                "blocked_at": datetime.utcnow().timestamp(),
                "expires_at": expires_at,
                "attempt_count": failed_count,
                "reason": "too_many_failed_attempts",
            }

            logger.critical(
                f"IP blocked after {failed_count} failed attempts: {client_ip}",
                extra={"ip": client_ip, "duration": block_duration},
            )

    def _apply_security_headers(self, request: Request, response: Response) -> Response:
        """Apply OWASP-compliant security headers to response."""
        # Get default headers
        headers = get_security_headers_default()

        # Apply each header
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        # Apply HSTS (only on HTTPS)
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Apply CSP
        if self._csp_template:
            response.headers["Content-Security-Policy"] = self._csp_template

        # Additional cache control for sensitive endpoints
        if is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Remove information leakage headers
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response

    def _create_blocked_response(self, message: str, status_code: int) -> Response:
        """Create a standardized blocked response."""
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message,
                "status": "blocked",
                "timestamp": datetime.utcnow().isoformat(),
            },
            headers={
                "X-Blocked-By": "UnifiedSecurityMiddleware",
                "X-Retry-After": (
                    str(self.config.ip_block_duration) if status_code == 429 else ""
                ),
            },
        )

    def _log_security_event(self, request: Request, client_info: dict, duration: float):
        """Log security event for monitoring and analysis."""
        logger.debug(
            f"Request: {request.method} {request.url.path} from {client_info['ip']} ({duration:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "ip": client_info["ip"],
                "user_agent": client_info.get("user_agent", ""),
                "duration": duration,
                "sensitive": is_sensitive_endpoint(request.url.path),
            },
        )

    # Management methods

    def block_ip(self, ip: str, duration: int | None = None, reason: str = "manual"):
        """Manually block an IP address."""
        block_duration = duration or self.config.ip_block_duration
        expires_at = datetime.utcnow().timestamp() + block_duration

        self._blocked_ips[ip] = {
            "blocked_at": datetime.utcnow().timestamp(),
            "expires_at": expires_at,
            "reason": reason,
        }

        logger.info(f"Manually blocked IP: {ip} for {reason}")

    def unblock_ip(self, ip: str):
        """Manually unblock an IP address."""
        if ip in self._blocked_ips:
            del self._blocked_ips[ip]
            logger.info(f"Manually unblocked IP: {ip}")

    def get_blocked_ips(self) -> dict[str, dict]:
        """Get list of currently blocked IPs."""
        return self._blocked_ips.copy()

    def clear_failed_attempts(self, ip: str):
        """Clear failed attempt counter for an IP."""
        if ip in self._failed_attempts:
            del self._failed_attempts[ip]
            logger.info(f"Cleared failed attempts for IP: {ip}")

    def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics."""
        return {
            "blocked_ips": len(self._blocked_ips),
            "suspicious_ips": len(self._suspicious_ips),
            "failed_attempts": dict(self._failed_attempts),
            "config": {
                "csrf_enabled": self.config.csrf_protection_enabled,
                "ip_blocking_enabled": self.config.ip_blocking_enabled,
                "attack_detection_enabled": self.config.attack_detection_enabled,
                "csp_level": self.config.csp_level,
            },
        }
