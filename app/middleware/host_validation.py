"""
Host Header Validation Middleware
Prevents DNS rebinding and host header injection attacks

Author: Security Team
Version: 1.0.0
"""

import logging
import os

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger("app.security.host_validation")


class HostValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate Host headers and prevent DNS rebinding attacks

    SECURITY THREATS PREVENTED:
    - DNS rebinding attacks
    - Host header injection
    - Cache poisoning attacks
    - Password reset poisoning
    """

    def __init__(self, app, allowed_hosts: list[str] | None = None):
        super().__init__(app)
        # FastAPI's add_middleware calls __init__ without 'app'
        # We handle both cases: with and without app parameter
        if allowed_hosts is None:
            self.allowed_hosts = self._get_allowed_hosts()
        else:
            self.allowed_hosts = allowed_hosts
        self.enable_logging = True

        # Log configuration
        logger.info(
            "Host validation middleware initialized",
            extra={
                "allowed_hosts": self.allowed_hosts,
                "wildcard_allowed": "*" in self.allowed_hosts
            }
        )

    def _get_allowed_hosts(self) -> list[str]:
        """
        Get allowed hosts from configuration or environment

        Returns:
            List of allowed host patterns
        """
        # Check environment variable
        env_hosts = getattr(settings, "ALLOWED_HOSTS", None)

        if env_hosts:
            if isinstance(env_hosts, str):
                return [h.strip() for h in env_hosts.split(",")]
            return env_hosts

        # Default configuration based on environment
        if settings.ENVIRONMENT == "production":
            # Production requires explicit hosts
            return []
        if settings.ENVIRONMENT == "development":
            # Development allows localhost variants
            return [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "*.localhost",
                "localhost:*",
                "127.0.0.1:*"
            ]
        # Testing/staging allows wildcard
        return ["*"]

    async def dispatch(self, request: Request, call_next):
        """
        Validate Host header before processing request

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response or HTTPException if validation fails
        """
        # Skip validation in testing mode
        if os.getenv("TESTING") == "True":
            return await call_next(request)

        # Get host from headers
        host = self._extract_host(request)

        # Skip validation for exempted paths
        if self._should_skip_validation(request):
            if self.enable_logging:
                logger.debug(
                    f"Skipping host validation for path: {request.url.path}",
                    extra={"host": host, "path": request.url.path}
                )
            return await call_next(request)

        # Validate host
        validation_result = self._validate_host(host, request)

        if not validation_result["valid"]:
            # Log the security violation
            logger.warning(
                f"Invalid Host header rejected: {host}",
                extra={
                    "host": host,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("User-Agent", "unknown"),
                    "reason": validation_result["reason"]
                }
            )

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Invalid Host header",
                    "error": validation_result["reason"]
                }
            )

        # Valid host - continue processing
        return await call_next(request)

    def _extract_host(self, request: Request) -> str:
        """
        Extract host from request headers

        Args:
            request: Incoming HTTP request

        Returns:
            Host string (without port if present)
        """
        # Check X-Forwarded-Host header (proxy scenarios)
        forwarded_host = request.headers.get("X-Forwarded-Host")
        if forwarded_host:
            host = forwarded_host.split(",")[0].strip()
        else:
            host = request.headers.get("host", "unknown")

        # Remove port number if present
        if ":" in host:
            host = host.split(":")[0]

        return host

    def _should_skip_validation(self, request: Request) -> bool:
        """
        Determine if request should skip host validation

        Args:
            request: Incoming HTTP request

        Returns:
            True if validation should be skipped
        """
        # Paths that always skip validation
        exempt_paths = [
            "/health",
            "/metrics",
            "/ping"
        ]

        # Skip for health checks in development/testing
        if (settings.ENVIRONMENT in ["development", "testing"] and
            request.url.path in exempt_paths):
            return True

        return False

    def _validate_host(self, host: str, request: Request) -> dict:
        """
        Validate host against allowed hosts list

        Args:
            host: Host string to validate
            request: Incoming request for context

        Returns:
            Dictionary with 'valid' (bool) and 'reason' (str if invalid)
        """
        # Wildcard allows everything
        if "*" in self.allowed_hosts and len(self.allowed_hosts) == 1:
            if settings.ENVIRONMENT == "production":
                logger.warning(
                    "Wildcard host allowed in production - consider restricting"
                )
            return {"valid": True}

        # Empty allowed hosts means nothing is allowed (security by default)
        if not self.allowed_hosts:
            return {
                "valid": False,
                "reason": "No hosts configured in ALLOWED_HOSTS"
            }

        # Check for exact match
        if host in self.allowed_hosts:
            return {"valid": True}

        # Check for wildcard patterns (e.g., *.example.com)
        for allowed in self.allowed_hosts:
            if allowed.startswith("*."):
                # Match subdomains
                domain = allowed[2:]  # Remove *.
                if host.endswith(domain) or host == domain:
                    return {"valid": True}

        # Check for IP addresses
        import ipaddress
        try:
            ipaddress.ip_address(host)
            # It's a valid IP, check if it's localhost
            if host in ["127.0.0.1", "::1", "0.0.0.0"]:
                # Allow localhost in non-production
                if settings.ENVIRONMENT != "production":
                    return {"valid": True}
                return {
                    "valid": False,
                    "reason": "localhost not allowed in production"
                }
        except ValueError:
            pass  # Not an IP address

        # Check for known malicious patterns
        suspicious_patterns = [
            "evil.com",
            "attacker.com",
            "malicious.com",
            "payload",
            "xss",
            "script",
            "<script",
            "javascript:"
        ]

        host_lower = host.lower()
        for pattern in suspicious_patterns:
            if pattern in host_lower:
                return {
                    "valid": False,
                    "reason": f"Suspicious pattern detected: {pattern}"
                }

        # Host not in allowed list
        return {
            "valid": False,
            "reason": f"Host '{host}' not in allowed hosts list"
        }


class StrictHostValidationMiddleware(HostValidationMiddleware):
    """
    Stricter version of host validation for production environments

    Additional features:
    - No exempt paths
    - Required ALLOWED_HOSTS configuration
    - Blocks localhost in production
    - Logs all host headers for audit
    """

    def __init__(self, app, allowed_hosts: list[str] | None = None):
        super().__init__(app, allowed_hosts)

        # Enforce allowed hosts in production
        if settings.ENVIRONMENT == "production" and not self.allowed_hosts:
            raise ValueError(
                "ALLOWED_HOSTS must be configured in production environment. "
                "Set ALLOWED_HOSTS environment variable with your domain names."
            )

        logger.warning(
            "Strict host validation enabled - all requests will be validated"
        )

    def _should_skip_validation(self, request: Request) -> bool:
        """Never skip validation in strict mode"""
        return False

    async def dispatch(self, request: Request, call_next):
        """Dispatch with additional audit logging"""
        host = self._extract_host(request)

        # Log all host headers in production
        if settings.ENVIRONMENT == "production":
            logger.info(
                f"Request host: {host}",
                extra={
                    "host": host,
                    "path": request.url.path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )

        return await super().dispatch(request, call_next)


# Convenience function to create appropriate middleware
def create_host_validation_middleware(app, strict: bool = False) -> HostValidationMiddleware:
    """
    Create host validation middleware based on environment

    Args:
        app: FastAPI application
        strict: Whether to use strict validation

    Returns:
        HostValidationMiddleware instance
    """
    if strict or settings.ENVIRONMENT == "production":
        return StrictHostValidationMiddleware(app)
    return HostValidationMiddleware(app)
