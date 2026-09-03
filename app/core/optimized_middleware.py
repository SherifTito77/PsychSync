"""
Performance-Optimized Middleware Configuration
Conditional middleware loading based on environment and load
"""

import gzip
import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.config import settings

logger = logging.getLogger("app.middleware.optimized")


class OptimizedCompressionMiddleware(BaseHTTPMiddleware):
    """
    Performance-optimized compression middleware
    Only compresses responses larger than threshold and uses optimal settings
    """

    def __init__(self, app, min_size: int = 1024, compresslevel: int = 3):
        super().__init__(app)
        self.min_size = min_size
        self.compresslevel = compresslevel

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Only compress if response meets criteria
        if self.should_compress(response) and not isinstance(
            response, StreamingResponse
        ):
            response = await self.compress_response(response)

        return response

    def should_compress(self, response: Response) -> bool:
        """Determine if response should be compressed"""

        # Don't compress small responses
        content_length = self.get_content_length(response)
        if content_length < self.min_size:
            return False

        # Don't compress already compressed content
        content_encoding = response.headers.get("content-encoding", "").lower()
        if content_encoding in ["gzip", "deflate", "br"]:
            return False

        # Don't compress images, videos, and other binary content
        content_type = response.headers.get("content-type", "").lower()
        skip_types = [
            "image/",
            "video/",
            "audio/",
            "application/pdf",
            "application/zip",
            "application/octet-stream",
        ]
        if any(skip_type in content_type for skip_type in skip_types):
            return False

        return True

    def get_content_length(self, response: Response) -> int:
        """Get content length from response"""
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                return int(content_length)
            except (ValueError, TypeError):
                pass
        return 0

    async def compress_response(self, response: Response) -> Response:
        """Compress response body"""
        try:
            # Get response body
            if hasattr(response, "body"):
                body = response.body
            elif hasattr(response, "content"):
                body = response.content
            else:
                # For response types we can't easily compress
                return response

            # Compress the body
            compressed_body = gzip.compress(body, compresslevel=self.compresslevel)

            # Update headers
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed_body))

            # Update body
            if hasattr(response, "body"):
                response.body = compressed_body
            else:
                response.content = compressed_body

        except Exception as e:
            logger.warning(f"Compression failed: {e}")

        return response


class SmartLoggingMiddleware(BaseHTTPMiddleware):
    """
    Smart logging middleware that reduces overhead under load
    """

    def __init__(
        self,
        app,
        log_slow_requests_only: bool = True,
        slow_request_threshold: float = 1.0,
    ):
        super().__init__(app)
        self.log_slow_requests_only = log_slow_requests_only
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        # Log based on configuration and response time
        should_log = (
            not self.log_slow_requests_only
            or duration > self.slow_request_threshold
            or response.status_code >= 500
        )

        if should_log:
            self.log_request(request, response, duration)

        return response

    def log_request(self, request: Request, response: Response, duration: float):
        """Log request with optimized format"""
        try:
            log_data = {
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "client_ip": self.get_client_ip(request),
            }

            # Use appropriate log level
            if response.status_code >= 500:
                logger.error(
                    f"Server Error: {request.method} {request.url} - {response.status_code} ({log_data['duration_ms']}ms)"
                )
            elif duration > self.slow_request_threshold:
                logger.warning(
                    f"Slow Request: {request.method} {request.url} - {response.status_code} ({log_data['duration_ms']}ms)"
                )
            else:
                logger.info(
                    f"Request: {request.method} {request.url} - {response.status_code} ({log_data['duration_ms']}ms)"
                )

        except Exception as e:
            logger.error(f"Logging failed: {e}")

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


def setup_optimized_middleware(app) -> None:
    """
    Setup optimized middleware based on environment and load conditions
    """

    if settings.ENVIRONMENT == "production":
        # Production: Enable optimized compression and smart logging
        app.add_middleware(
            OptimizedCompressionMiddleware, min_size=1024, compresslevel=3
        )
        app.add_middleware(
            SmartLoggingMiddleware,
            log_slow_requests_only=True,
            slow_request_threshold=1.0,
        )

        logger.info("✅ Optimized middleware enabled for production")

    elif settings.ENVIRONMENT == "development":
        # Development: Full logging and debugging features
        # You can uncomment these if you want full middleware in development
        # from app.middleware.response_compression import ResponseCompressionMiddleware
        # from app.middleware.request_tracking import RequestTrackingMiddleware
        # app.add_middleware(ResponseCompressionMiddleware)
        # app.add_middleware(RequestTrackingMiddleware)

        logger.info("ℹ️  Development mode: Full logging enabled")

    else:
        # Testing/Other: Minimal middleware
        app.add_middleware(
            OptimizedCompressionMiddleware, min_size=2048, compresslevel=1
        )
        logger.info("⚡ Minimal middleware enabled for optimal performance")


# Performance monitoring
def get_middleware_performance_info() -> dict[str, Any]:
    """Get current middleware performance information"""
    return {
        "compression_middleware": {
            "enabled": settings.ENVIRONMENT != "development",
            "min_size": 1024 if settings.ENVIRONMENT == "production" else 2048,
            "compresslevel": 3 if settings.ENVIRONMENT == "production" else 1,
        },
        "logging_middleware": {
            "enabled": settings.ENVIRONMENT != "development",
            "slow_request_only": settings.ENVIRONMENT == "production",
            "slow_request_threshold": (
                1.0 if settings.ENVIRONMENT == "production" else 0.5
            ),
        },
        "environment": settings.ENVIRONMENT,
        "optimizations_applied": [
            "Conditional compression",
            "Smart logging",
            "Performance-first design",
        ],
    }


__all__ = [
    "OptimizedCompressionMiddleware",
    "SmartLoggingMiddleware",
    "get_middleware_performance_info",
    "setup_optimized_middleware",
]
