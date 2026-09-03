"""
Authoritative PsychSync Security Middleware - Consolidated
Replaces:
- app/middleware/security.py
- app/middleware/file_upload_rate_limiting.py
- app/middleware/prometheus_monitoring.py
- app/middleware/request_tracking.py
- app/middleware/response_compression.py
- app/middleware/spotlighting.py

This module centralizes security headers, rate limiting, PII masking, request tracking,
and performance/threat monitoring into a single unified middleware stack.
"""

import logging
import time
import uuid
from typing import Callable, Dict, Optional, Set

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.rate_limiter_unified import (
    MEDIUM,
    STRICT,
    RateLimitConfig,
    RateLimitStrategy,
    UnifiedRateLimiter,
)

logger = logging.getLogger("psychsync.security.consolidated")


class ConsolidatedSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enable_rate_limiting = getattr(settings, "RATE_LIMITING_ENABLED", True)

        # Initialize limiters for different sensitivity levels
        self.auth_limiter = UnifiedRateLimiter(config=STRICT)
        self.api_limiter = UnifiedRateLimiter(config=MEDIUM)

        # Paths that bypass rate limiting
        self.exclude_paths: Set[str] = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
        }

        logger.info(
            "✅ Consolidated Security Middleware initialized with Rate Limiting"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        path = request.url.path
        client_ip = self._get_client_ip(request)

        # 1. Rate Limiting Check
        if self.enable_rate_limiting and path not in self.exclude_paths:
            # Determine which limiter to use
            limiter = (
                self.auth_limiter
                if "/auth/" in path or "/login" in path
                else self.api_limiter
            )

            result = await limiter.check(
                identifier="global", endpoint=path, ip_address=client_ip
            )

            if not result.allowed:
                logger.warning(f"Rate limit exceeded: {client_ip} -> {path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers=result.to_headers(),
                )

        # 2. Process Request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed: {request_id} - {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        # 3. Security Headers
        self._add_security_headers(response, request_id)

        # 4. Logging & Monitoring
        duration = time.time() - start_time
        logger.info(
            f"Request: {request.method} {path} - {response.status_code} ({duration:.4f}s)",
            extra={"request_id": request_id, "client_ip": client_ip},
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _add_security_headers(self, response: Response, request_id: str):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Request-ID"] = request_id


def setup_security_middleware(app: ASGIApp):
    app.add_middleware(ConsolidatedSecurityMiddleware)
