"""
PsychSync Datadog Configuration for APM and Log Management
Comprehensive application performance monitoring and centralized logging
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any

from ddtrace import Span, config, tracer
from ddtrace.contrib.celery import patch as patch_celery
from ddtrace.contrib.fastapi import patch as patch_fastapi
from ddtrace.contrib.httpx import patch as patch_httpx
from ddtrace.contrib.redis import patch as patch_redis
from ddtrace.contrib.sqlalchemy import patch as patch_sqlalchemy
from ddtrace.internal.logger import get_logger

# Datadog Configuration
DD_SERVICE = os.getenv("DD_SERVICE", "psychsync-api")
DD_ENV = os.getenv("DD_ENV", "production")
DD_VERSION = os.getenv("DD_VERSION", "1.0.0")
DD_SITE = os.getenv("DD_SITE", "datadoghq.com")
DD_API_KEY = os.getenv("DD_API_KEY")
DD_APP_KEY = os.getenv("DD_APP_KEY")
DD_LOGS_ENABLED = os.getenv("DD_LOGS_ENABLED", "true").lower() == "true"
DD_PROFILING_ENABLED = os.getenv("DD_PROFILING_ENABLED", "true").lower() == "true"

# Sampling and filtering
DD_TRACE_SAMPLE_RATE = float(os.getenv("DD_TRACE_SAMPLE_RATE", "0.1"))  # 10% sampling
DD_TRACE_ENABLED = os.getenv("DD_TRACE_ENABLED", "true").lower() == "true"
DD_LOGS_INJECTION = os.getenv("DD_LOGS_INJECTION", "true").lower() == "true"

# Custom tags
CUSTOM_TAGS = [
    "service:psychsync-api",
    "environment:" + DD_ENV,
    "version:" + DD_VERSION,
    "team:backend",
]

# Initialize logger
dd_logger = get_logger(__name__)


def init_datadog() -> None:
    """Initialize Datadog tracing and logging"""

    if not DD_API_KEY:
        logging.warning("DD_API_KEY not configured - Datadog disabled")
        return

    try:
        # Configure global tracer settings
        config.service = DD_SERVICE
        config.env = DD_ENV
        config.version = DD_VERSION
        config.site = DD_SITE

        # Enable profiling if configured
        if DD_PROFILING_ENABLED:
            config.profiling_enabled = True

        # Configure sampling
        if DD_TRACE_ENABLED:
            config.trace_sampling_enabled = True
            config.trace_sample_rate = DD_TRACE_SAMPLE_RATE

        # Configure log injection
        config.logs_injection = DD_LOGS_INJECTION

        # Patch relevant libraries
        _patch_libraries()

        # Configure global tags
        tracer.set_tags(
            {
                "service": DD_SERVICE,
                "environment": DD_ENV,
                "version": DD_VERSION,
                "team": "backend",
            }
        )

        # Configure filters for sensitive data
        _configure_filters()

        logging.info(f"Datadog initialized - Service: {DD_SERVICE}, Env: {DD_ENV}")

    except Exception as e:
        logging.exception(f"Failed to initialize Datadog: {e}")


def _patch_libraries() -> None:
    """Patch relevant libraries for tracing"""

    if not DD_TRACE_ENABLED:
        return

    try:
        # Patch FastAPI
        patch_fastapi()
        dd_logger.debug("FastAPI patched for tracing")

        # Patch SQLAlchemy
        patch_sqlalchemy()
        dd_logger.debug("SQLAlchemy patched for tracing")

        # Patch Redis
        patch_redis()
        dd_logger.debug("Redis patched for tracing")

        # Patch HTTP clients
        patch_httpx()
        dd_logger.debug("HTTPX patched for tracing")

        # Patch Celery if available
        try:
            patch_celery()
            dd_logger.debug("Celery patched for tracing")
        except ImportError:
            dd_logger.debug("Celery not available, skipping patch")

    except Exception as e:
        dd_logger.error(f"Failed to patch libraries: {e}")


def _configure_filters() -> None:
    """Configure filters to remove sensitive data"""

    if not DD_TRACE_ENABLED:
        return

    # Configure URL filtering
    @tracer.wrap("http.client")
    def filter_sensitive_urls(span: Span):
        if span.get_tag("http.url"):
            url = span.get_tag("http.url")
            if any(
                sensitive in url.lower()
                for sensitive in ["password", "token", "secret"]
            ):
                # Replace sensitive parameters
                import re

                url = re.sub(
                    r"([?&])(password|token|secret|key)=[^&]*", r"\1\2=[FILTERED]", url
                )
                span.set_tag("http.url", url)

    # Configure header filtering
    @tracer.wrap("http.client")
    def filter_sensitive_headers(span: Span):
        sensitive_headers = ["authorization", "cookie", "x-api-key", "password"]
        for header in sensitive_headers:
            if span.get_tag(f"http.request.headers.{header}"):
                span.set_tag(f"http.request.headers.{header}", "[FILTERED]")


class DatadogTracingMiddleware:
    """FastAPI middleware for enhanced Datadog tracing"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Start trace
        with tracer.trace("fastapi.request", service=DD_SERVICE) as span:
            # Extract request information
            method = scope.get("method", "")
            path = scope.get("path", "")
            headers = dict(scope.get("headers", []))

            # Set span tags
            span.set_tag("http.method", method)
            span.set_tag("http.url", path)
            span.set_tag("http.useragent", headers.get(b"user-agent", b"").decode())

            # Add custom tags
            span.set_tags(
                {
                    "component": "fastapi",
                    "span.kind": "server",
                    **{
                        tag.split(":")[0]: tag.split(":")[1]
                        for tag in CUSTOM_TAGS
                        if ":" in tag
                    },
                }
            )

            # Wrap send to capture response
            async def wrapped_send(message):
                if message["type"] == "http.response.start":
                    status = message.get("status", 200)
                    span.set_tag("http.status_code", status)

                    # Set error status for 5xx responses
                    if 500 <= status < 600:
                        span.set_tag("error", 1)
                        span.set_tag("error.msg", f"HTTP {status} Error")

                await send(message)

            try:
                await self.app(scope, receive, wrapped_send)
            except Exception as e:
                span.set_tag("error", 1)
                span.set_tag("error.msg", str(e))
                span.set_tag("error.type", type(e).__name__)
                raise


def trace_async_function(
    name: str,
    service: str | None = None,
    resource: str | None = None,
    tags: dict[str, str] | None = None,
):
    """Decorator for tracing async functions"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with tracer.trace(
                name,
                service=service or DD_SERVICE,
                resource=resource or func.__name__,
                tags=tags or {},
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("success", 1)
                    return result
                except Exception as e:
                    span.set_tag("error", 1)
                    span.set_tag("error.msg", str(e))
                    span.set_tag("error.type", type(e).__name__)
                    raise

        return wrapper

    return decorator


def trace_function(
    name: str,
    service: str | None = None,
    resource: str | None = None,
    tags: dict[str, str] | None = None,
):
    """Decorator for tracing synchronous functions"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.trace(
                name,
                service=service or DD_SERVICE,
                resource=resource or func.__name__,
                tags=tags or {},
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("success", 1)
                    return result
                except Exception as e:
                    span.set_tag("error", 1)
                    span.set_tag("error.msg", str(e))
                    span.set_tag("error.type", type(e).__name__)
                    raise

        return wrapper

    return decorator


class DatadogLogger:
    """Custom logger for Datadog log management"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Configure logger for Datadog integration"""

        # Set up formatter with trace injection
        if DD_LOGS_INJECTION:
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] [%(dd.service)s] [%(dd.trace_id)s] [%(dd.span_id)s] - %(message)s"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] - %(message)s"
            )

        # Create handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def info(self, message: str, extra: dict[str, Any] | None = None):
        """Log info message with optional extra data"""
        if extra:
            self.logger.info(message, extra=extra)
        else:
            self.logger.info(message)

    def warning(self, message: str, extra: dict[str, Any] | None = None):
        """Log warning message with optional extra data"""
        if extra:
            self.logger.warning(message, extra=extra)
        else:
            self.logger.warning(message)

    def error(self, message: str, extra: dict[str, Any] | None = None):
        """Log error message with optional extra data"""
        if extra:
            self.logger.error(message, extra=extra)
        else:
            self.logger.error(message)

    def debug(self, message: str, extra: dict[str, Any] | None = None):
        """Log debug message with optional extra data"""
        if extra:
            self.logger.debug(message, extra=extra)
        else:
            self.logger.debug(message)

    def log_structured(self, level: str, message: str, data: dict[str, Any]):
        """Log structured message with data"""
        log_data = {
            "message": message,
            "service": DD_SERVICE,
            "environment": DD_ENV,
            "version": DD_VERSION,
            **data,
        }

        if DD_LOGS_INJECTION:
            current_span = tracer.current_span()
            if current_span:
                log_data["dd.trace_id"] = format(current_span.trace_id, "032x")
                log_data["dd.span_id"] = format(current_span.span_id, "016x")

        getattr(self.logger, level.lower())(json.dumps(log_data))


class DatadogMetrics:
    """Custom metrics collection for Datadog"""

    def __init__(self):
        self.counters: dict[str, float] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}

    def increment(self, metric: str, value: float = 1.0, tags: list[str] | None = None):
        """Increment a counter metric"""
        key = self._make_key(metric, tags)
        self.counters[key] = self.counters.get(key, 0.0) + value
        self._send_to_datadog("counter", key, self.counters[key], tags)

    def gauge(self, metric: str, value: float, tags: list[str] | None = None):
        """Set a gauge metric"""
        key = self._make_key(metric, tags)
        self.gauges[key] = value
        self._send_to_datadog("gauge", key, value, tags)

    def histogram(self, metric: str, value: float, tags: list[str] | None = None):
        """Add value to histogram metric"""
        key = self._make_key(metric, tags)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        self._send_to_datadog("histogram", key, value, tags)

    def _make_key(self, metric: str, tags: list[str] | None = None) -> str:
        """Create a key for the metric"""
        if tags:
            tag_str = ",".join(sorted(tags))
            return f"{metric},{tag_str}"
        return metric

    def _send_to_datadog(
        self, metric_type: str, key: str, value: float, tags: list[str] | None = None
    ):
        """Send metric to Datadog (placeholder for actual implementation)"""
        # In a real implementation, this would send to Datadog API
        # For now, we'll just log the metric
        dd_logger.debug(f"Datadog metric: {metric_type} {key}={value}")


# Global metrics instance
metrics = DatadogMetrics()


def set_datadog_user(user_data: dict[str, Any]) -> None:
    """Set user context for Datadog traces"""
    current_span = tracer.current_span()
    if current_span:
        # Filter sensitive data
        filtered_user = {
            "id": user_data.get("id"),
            "email": user_data.get("email"),
            "username": user_data.get("username"),
            "organization_id": user_data.get("organization_id"),
            "role": user_data.get("role"),
        }

        # Remove None values
        filtered_user = {k: v for k, v in filtered_user.items() if v is not None}

        current_span.set_tag("user.id", str(filtered_user.get("id", "unknown")))
        current_span.set_tag("user.email", filtered_user.get("email", "unknown"))
        current_span.set_tag("user.role", filtered_user.get("role", "unknown"))


def add_datadog_tags(tags: dict[str, str]) -> None:
    """Add tags to current span"""
    current_span = tracer.current_span()
    if current_span:
        current_span.set_tags(tags)


@asynccontextmanager
async def datadog_transaction(name: str, operation: str = "function"):
    """Context manager for Datadog transaction tracing"""
    if not DD_TRACE_ENABLED:
        yield
        return

    with tracer.trace(name, service=DD_SERVICE, span_type=operation) as span:
        try:
            yield span
        except Exception as e:
            span.set_tag("error", 1)
            span.set_tag("error.msg", str(e))
            span.set_tag("error.type", type(e).__name__)
            raise


def check_datadog_health() -> dict[str, Any]:
    """Check Datadog health and configuration"""
    return {
        "configured": bool(DD_API_KEY),
        "service": DD_SERVICE,
        "environment": DD_ENV,
        "version": DD_VERSION,
        "trace_enabled": DD_TRACE_ENABLED,
        "logs_enabled": DD_LOGS_ENABLED,
        "profiling_enabled": DD_PROFILING_ENABLED,
        "sample_rate": DD_TRACE_SAMPLE_RATE,
        "logs_injection": DD_LOGS_INJECTION,
    }
