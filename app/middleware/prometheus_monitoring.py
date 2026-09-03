"""
Prometheus Monitoring Middleware

This middleware automatically tracks HTTP requests using the Prometheus metrics.
It integrates with the metrics endpoint to provide visibility into request rates,
errors, and durations (RED method).

CRITICAL: This middleware is what makes the metrics endpoint useful.
Without it, the /metrics endpoint would return empty data.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.api.v1.endpoints.prometheus_metrics import (
    http_requests_active,
    track_http_request,
)


class PrometheusMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Prometheus monitoring middleware for FastAPI

    Automatically tracks:
    - Request count by endpoint, method, status
    - Request duration (p50, p95, p99 via histogram)
    - Active requests gauge

    This implements the RED method:
    - Rate: Request rate (tracked via http_requests_total counter)
    - Errors: Error rate (via status code label)
    - Duration: Request duration (via histogram)
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] | None = None,
        histogram_buckets: list[float] | None = None,
    ):
        """
        Initialize middleware

        Args:
            app: ASGI application
            exclude_paths: Paths to exclude from monitoring (e.g., /health, /metrics)
            histogram_buckets: Custom histogram buckets (optional)
        """
        super().__init__(app)

        # Exclude common health check and metrics endpoints
        self.exclude_paths = set(
            exclude_paths
            or [
                "/health",
                "/health/public",
                "/health/detailed",
                "/metrics",
                "/metrics/openmetrics",
                "/docs",
                "/redoc",
                "/openapi.json",
            ]
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from downstream
        """
        # Skip monitoring for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract endpoint path (strip query parameters)
        path = request.url.path

        # Use route template instead of actual path for better aggregation
        # e.g., /users/123 -> /users/{id}
        endpoint = getattr(request.state, "route", self._get_route_template(request))

        # Increment active requests gauge
        http_requests_active.labels(method=request.method, endpoint=endpoint).inc()

        # Track request start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Track metrics
            track_http_request(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code,
                duration=duration,
            )

            return response

        except Exception as e:
            # Track failed request
            duration = time.time() - start_time
            track_http_request(
                method=request.method,
                endpoint=endpoint,
                status=500,  # Internal server error
                duration=duration,
            )
            raise

        finally:
            # Decrement active requests gauge
            http_requests_active.labels(method=request.method, endpoint=endpoint).dec()

    def _get_route_template(self, request: Request) -> str:
        """
        Get route template from request

        Converts /users/123 to /users/{id}
        """
        # Try to get route from app routes
        for route in request.app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                if request.url.path.matches(route.path):
                    return route.path

        # Fallback: return actual path
        return request.url.path


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """
    Tracks request and response sizes

    Useful for identifying bandwidth-intensive endpoints
    and detecting potential abuse (e.g., extremely large requests).
    """

    def __init__(
        self,
        app: ASGIApp,
        max_request_size_mb: float = 10.0,
        max_response_size_mb: float = 10.0,
    ):
        """
        Initialize middleware

        Args:
            app: ASGI application
            max_request_size_mb: Maximum request size in MB (for logging)
            max_response_size_mb: Maximum response size in MB (for logging)
        """
        super().__init__(app)
        self.max_request_size_bytes = max_request_size_mb * 1024 * 1024
        self.max_response_size_bytes = max_response_size_mb * 1024 * 1024

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request and response sizes"""
        # Track request size
        if request.headers.get("content-length"):
            request_size = int(request.headers["content-length"])

            # Import here to avoid circular dependency
            from app.api.v1.endpoints.prometheus_metrics import http_request_size_bytes

            endpoint = getattr(request.state, "route", request.url.path)
            http_request_size_bytes.labels(
                method=request.method, endpoint=endpoint
            ).observe(request_size)

        # Process request
        response = await call_next(request)

        # Track response size
        response_size = len(response.body)
        from app.api.v1.endpoints.prometheus_metrics import http_response_size_bytes

        endpoint = getattr(request.state, "route", request.url.path)
        http_response_size_bytes.labels(
            method=request.method, endpoint=endpoint
        ).observe(response_size)

        return response


# ============================================================================
# SETUP HELPER
# ============================================================================


def setup_prometheus_middleware(app):
    """
    Set up Prometheus monitoring middleware for FastAPI app

    Add to main.py:

    ```python
    from app.middleware.prometheus_monitoring import setup_prometheus_middleware
    from app.api.v1.endpoints import prometheus_metrics

    # Include metrics router
    app.include_router(prometheus_metrics.router)

    # Add middleware
    setup_prometheus_middleware(app)
    ```

    Args:
        app: FastAPI application instance
    """
    # Add monitoring middleware
    app.add_middleware(PrometheusMonitoringMiddleware)
    app.add_middleware(RequestSizeMiddleware)

    # Log initialization
    import logging

    logger = logging.getLogger(__name__)
    logger.info("✅ Prometheus monitoring middleware initialized")
    logger.info("📊 Metrics available at: /metrics")
