# app/middleware/security_middleware.py

"""
ENTERPRISE-GRADE SECURITY MIDDLEWARE
Comprehensive security middleware for request protection and monitoring

SECURITY FEATURES:
- Request validation and sanitization
- Suspicious activity detection
- IP-based security controls
- Device fingerprinting
- Security event logging
- Emergency response controls

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.audit_logger import AuditLogger

# Initialize security middleware logger
security_middleware_logger = logging.getLogger("app.middleware.security")


class SecurityEventLogger:
    """Handles security event logging with structured data"""

    def __init__(self):
        self.logger = AuditLogger()
        self._suspicious_patterns = [
            "sqlmap",
            "nikto",
            "nmap",
            "masscan",
            "dirb",
            "gobuster",
            "sql injection",
            "xss",
            "csrf",
            "lfi",
            "rfi",
        ]

    async def log_security_event(
        self,
        event_type: str,
        request: Request,
        details: dict[str, Any],
        severity: str = "medium",
    ):
        """Log security event with comprehensive context"""
        try:
            client_info = self._get_client_info(request)

            event_data = {
                "event_type": event_type,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat(),
                "client": client_info,
                "details": details,
            }

            await self.logger.log_security_event(
                event_type=event_type,
                details=str(details),
                client_ip=client_info.get("ip", "unknown"),
                user_agent=client_info.get("user_agent", "unknown"),
            )

            security_middleware_logger.warning(
                f"Security event: {event_type}", extra=event_data
            )

        except Exception as e:
            security_middleware_logger.error(f"Error logging security event: {e}")

    def _get_client_info(self, request: Request) -> dict[str, Any]:
        """Extract comprehensive client information"""
        return {
            "ip": getattr(request, "client", {}).get("host", "unknown"),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
        }


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Enterprise-grade security middleware for comprehensive request protection
    """

    def __init__(self, app):
        super().__init__(app)
        self.event_logger = SecurityEventLogger()
        self._blocked_ips: set[str] = set()
        self._suspicious_ips: dict[str, dict[str, Any]] = {}
        self._emergency_mode = False
        self._rate_limit_cache: dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        """
        Process request through security pipeline
        """
        start_time = time.time()
        client_ip = getattr(request, "client", {}).get("host", "unknown")

        try:
            # Security pipeline
            if await self._should_block_request(request):
                return await self._create_blocked_response(
                    request, "Request blocked by security policy"
                )

            # Security monitoring
            await self._monitor_request(request)

            # Process request
            response = await call_next(request)

            # Security headers
            response = await self._add_security_headers(response)

            # Log successful request
            processing_time = time.time() - start_time
            await self._log_request_completion(
                request, response, processing_time, "success"
            )

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            await self._log_request_completion(
                request, None, processing_time, "error", str(e)
            )
            raise

    async def _should_block_request(self, request: Request) -> bool:
        """Determine if request should be blocked"""
        client_ip = getattr(request, "client", {}).get("host", "unknown")
        user_agent = request.headers.get("user-agent", "").lower()
        url_path = request.url.path.lower()

        # Emergency mode
        if self._emergency_mode:
            # Only allow health checks and essential endpoints
            if not self._is_essential_endpoint(url_path):
                return True

        # IP-based blocking
        if client_ip in self._blocked_ips:
            return True

        # Suspicious activity patterns
        if await self._detect_suspicious_patterns(request):
            return True

        # Rate limiting for suspicious IPs
        if await self._is_rate_limited(client_ip):
            return True

        return False

    def _is_essential_endpoint(self, path: str) -> bool:
        """Check if endpoint is essential during emergency mode"""
        essential_endpoints = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
        ]
        return any(endpoint in path for endpoint in essential_endpoints)

    async def _detect_suspicious_patterns(self, request: Request) -> bool:
        """Detect suspicious patterns in request"""
        user_agent = request.headers.get("user-agent", "").lower()
        url_path = request.url.path.lower()
        query_string = str(request.url.query).lower()

        # Check for attack tools in user agent
        attack_tools = ["sqlmap", "nikto", "nmap", "gobuster", "dirb"]
        if any(tool in user_agent for tool in attack_tools):
            await self.event_logger.log_security_event(
                "attack_tool_detected",
                request,
                {"user_agent": user_agent, "tool": "unknown"},
                "high",
            )
            return True

        # Check for injection patterns
        injection_patterns = [
            "union select",
            "select * from",
            "drop table",
            "exec(",
            "system(",
            "eval(",
            "<script>",
            "javascript:",
            "onerror=",
        ]

        combined_input = f"{url_path} {query_string}".lower()
        if any(pattern in combined_input for pattern in injection_patterns):
            await self.event_logger.log_security_event(
                "injection_attempt_detected",
                request,
                {
                    "url_path": url_path,
                    "query_string": query_string,
                    "pattern": "unknown",
                },
                "high",
            )
            return True

        # Check for unusual request patterns
        if self._has_unusual_request_patterns(request):
            await self.event_logger.log_security_event(
                "unusual_request_pattern",
                request,
                {"details": "Request deviates from normal patterns"},
                "medium",
            )
            return True

        return False

    def _has_unusual_request_patterns(self, request: Request) -> bool:
        """Detect unusual request patterns"""
        # Very long URLs
        if len(str(request.url)) > 2000:
            return True

        # Suspicious header combinations
        headers = dict(request.headers)
        if "x-forwarded-for" in headers and "user-agent" not in headers:
            return True

        # Many query parameters
        query_params = dict(request.query_params)
        if len(query_params) > 50:
            return True

        return False

    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited"""
        current_time = time.time()

        # Initialize or get existing requests
        if client_ip not in self._rate_limit_cache:
            self._rate_limit_cache[client_ip] = []

        # Clean old requests (older than 1 minute)
        self._rate_limit_cache[client_ip] = [
            req_time
            for req_time in self._rate_limit_cache[client_ip]
            if current_time - req_time < 60
        ]

        # Check rate limit (100 requests per minute for normal IPs)
        max_requests = 10 if client_ip in self._suspicious_ips else 100

        if len(self._rate_limit_cache[client_ip]) >= max_requests:
            return True

        # Add current request
        self._rate_limit_cache[client_ip].append(current_time)

        # Clean up old entries periodically
        if len(self._rate_limit_cache) > 10000:
            self._cleanup_rate_limit_cache()

        return False

    def _cleanup_rate_limit_cache(self):
        """Clean up old entries from rate limit cache"""
        current_time = time.time()
        cutoff_time = current_time - 300  # 5 minutes

        for ip in list(self._rate_limit_cache.keys()):
            self._rate_limit_cache[ip] = [
                req_time
                for req_time in self._rate_limit_cache[ip]
                if req_time > cutoff_time
            ]
            if not self._rate_limit_cache[ip]:
                del self._rate_limit_cache[ip]

    async def _monitor_request(self, request: Request):
        """Monitor request for security analysis"""
        client_ip = getattr(request, "client", {}).get("host", "unknown")
        url_path = request.url.path

        # Track suspicious IPs
        if await self._is_suspicious_request(request):
            if client_ip not in self._suspicious_ips:
                self._suspicious_ips[client_ip] = {
                    "first_seen": datetime.utcnow(),
                    "suspicious_count": 0,
                }

            self._suspicious_ips[client_ip]["suspicious_count"] += 1
            self._suspicious_ips[client_ip]["last_seen"] = datetime.utcnow()

            # Block IP if too many suspicious requests
            if self._suspicious_ips[client_ip]["suspicious_count"] > 10:
                self._blocked_ips.add(client_ip)
                await self.event_logger.log_security_event(
                    "ip_blocked",
                    request,
                    {"reason": "Too many suspicious requests"},
                    "high",
                )

    async def _is_suspicious_request(self, request: Request) -> bool:
        """Check if request appears suspicious"""
        # Check for suspicious URLs
        suspicious_paths = [
            "/admin",
            "/wp-admin",
            "/.git",
            "/.env",
            "/config",
            "/backup",
            "/database",
        ]

        url_path = request.url.path.lower()
        if any(path in url_path for path in suspicious_paths):
            return True

        # Check for suspicious headers
        headers = dict(request.headers)
        suspicious_headers = ["x-real-ip", "x-forwarded-for", "x-originating-ip"]
        if len([h for h in suspicious_headers if h in headers]) > 2:
            return True

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return True

        return False

    async def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Cache control for sensitive endpoints
        if hasattr(response, "url") and any(
            endpoint in str(response.url).lower()
            for endpoint in ["/auth/", "/admin/", "/user/"]
        ):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    async def _create_blocked_response(
        self, request: Request, reason: str
    ) -> JSONResponse:
        """Create standardized blocked response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Request blocked",
                "message": "Your request has been blocked by our security systems",
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _log_request_completion(
        self,
        request: Request,
        response: Response | None,
        processing_time: float,
        status: str,
        error: str | None = None,
    ):
        """Log request completion with security context"""
        try:
            client_info = self.event_logger._get_client_info(request)

            log_data = {
                "status": status,
                "processing_time_ms": processing_time * 1000,
                "client": client_info,
                "request_method": request.method,
                "request_path": str(request.url.path),
                "request_size": len(str(request.url)) + len(str(request.headers)),
                "timestamp": datetime.utcnow().isoformat(),
            }

            if response:
                log_data["response_status"] = response.status_code
                log_data["response_size"] = len(str(response.headers))

            if error:
                log_data["error"] = error

            if status == "success" and processing_time > 5.0:  # Slow requests
                security_middleware_logger.warning(
                    f"Slow request detected: {processing_time:.2f}s", extra=log_data
                )
            elif status == "error":
                security_middleware_logger.error(
                    f"Request failed: {error}", extra=log_data
                )

        except Exception as e:
            security_middleware_logger.error(f"Error logging request completion: {e}")

    def enable_emergency_mode(self):
        """Enable emergency security mode"""
        self._emergency_mode = True
        security_middleware_logger.critical("Emergency security mode enabled")

    def disable_emergency_mode(self):
        """Disable emergency security mode"""
        self._emergency_mode = False
        security_middleware_logger.info("Emergency security mode disabled")

    def block_ip(self, ip: str, reason: str = "Manual block"):
        """Manually block an IP address"""
        self._blocked_ips.add(ip)
        security_middleware_logger.warning(f"IP blocked manually: {ip} - {reason}")

    def unblock_ip(self, ip: str):
        """Manually unblock an IP address"""
        self._blocked_ips.discard(ip)
        if ip in self._suspicious_ips:
            del self._suspicious_ips[ip]
        security_middleware_logger.info(f"IP unblocked: {ip}")

    def get_security_stats(self) -> dict[str, Any]:
        """Get security statistics"""
        return {
            "blocked_ips_count": len(self._blocked_ips),
            "suspicious_ips_count": len(self._suspicious_ips),
            "emergency_mode": self._emergency_mode,
            "rate_limit_cache_size": len(self._rate_limit_cache),
        }
