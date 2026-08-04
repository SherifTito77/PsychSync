"""
Distributed Tracing and Observability System

This module provides comprehensive distributed tracing capabilities for the application,
including request tracing, performance monitoring, and cross-service visibility.

Features:
- OpenTelemetry integration
- Request tracing across services
- Performance monitoring
- Error tracking and analysis
- Distributed context propagation
- Custom span creation
- Trace sampling
- Export to multiple backends (Jaeger, Zipkin, etc.)
"""

import asyncio
import logging
import os
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Try to import OpenTelemetry, but make it optional for development
try:
    from opentelemetry import baggage, context, trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.propagate import extract, inject
    from opentelemetry.propagators.b3 import B3MultiFormat
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry.semconv.trace import SpanAttributes

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    baggage = None

logger = logging.getLogger(__name__)

# Context variables for trace propagation
current_span: ContextVar[str | None] = ContextVar("current_span", default=None)
current_trace_id: ContextVar[str | None] = ContextVar("current_trace_id", default=None)
current_request_id: ContextVar[str | None] = ContextVar(
    "current_request_id", default=None
)


class SpanKind(Enum):
    """Span kind types"""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(Enum):
    """Span status codes"""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanAttributes:
    """Standard span attributes"""

    service_name: str
    operation_name: str
    component: str
    span_kind: SpanKind
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    status: SpanStatus = SpanStatus.OK
    error_message: str | None = None
    error_type: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TraceContext:
    """Trace context for propagation"""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    baggage: dict[str, str] = field(default_factory=dict)
    flags: int = 0


class DistributedTracer:
    """Main distributed tracing manager"""

    def __init__(
        self,
        service_name: str = "psychsync-api",
        jaeger_endpoint: str | None = None,
        zipkin_endpoint: str | None = None,
        sample_rate: float = 0.1,
        enable_console: bool = True,
    ):
        self.service_name = service_name
        self.sample_rate = sample_rate
        self.enabled = OPENTELEMETRY_AVAILABLE and os.getenv("ENVIRONMENT") != "test"
        self.tracer = None
        self.span_storage: dict[str, SpanAttributes] = {}

        if self.enabled and trace:
            self._setup_opentelemetry(jaeger_endpoint, zipkin_endpoint, enable_console)
        else:
            logger.warning("OpenTelemetry not available or tracing disabled")

    def _setup_opentelemetry(
        self,
        jaeger_endpoint: str | None,
        zipkin_endpoint: str | None,
        enable_console: bool,
    ):
        """Setup OpenTelemetry tracing"""
        try:
            # Set up resource
            resource = Resource.create(
                {
                    ResourceAttributes.SERVICE_NAME: self.service_name,
                    ResourceAttributes.SERVICE_VERSION: os.getenv(
                        "APP_VERSION", "1.0.0"
                    ),
                    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv(
                        "ENVIRONMENT", "development"
                    ),
                }
            )

            # Set up tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            # Get tracer
            self.tracer = trace.get_tracer(self.service_name)

            # Add exporters
            if jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    endpoint=jaeger_endpoint,
                    collector_endpoint=jaeger_endpoint,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                tracer_provider.add_span_processor(span_processor)
                logger.info(f"Jaeger exporter configured: {jaeger_endpoint}")

            if zipkin_endpoint:
                zipkin_exporter = ZipkinExporter(
                    endpoint=zipkin_endpoint,
                )
                span_processor = BatchSpanProcessor(zipkin_exporter)
                tracer_provider.add_span_processor(span_processor)
                logger.info(f"Zipkin exporter configured: {zipkin_endpoint}")

            if enable_console:
                console_exporter = ConsoleSpanExporter()
                span_processor = BatchSpanProcessor(console_exporter)
                tracer_provider.add_span_processor(span_processor)

            logger.info("OpenTelemetry tracing initialized successfully")

        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {e}")
            self.enabled = False

    @asynccontextmanager
    async def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ):
        """Start a new span"""
        if not self.enabled or not self.tracer:
            # Fallback span creation
            span_id = str(uuid.uuid4())
            span_attrs = SpanAttributes(
                service_name=self.service_name,
                operation_name=name,
                component=self.service_name,
                span_kind=kind,
                start_time=time.time(),
                tags=tags or {},
            )
            self.span_storage[span_id] = span_attrs

            try:
                yield span_id
            except Exception as e:
                span_attrs.status = SpanStatus.ERROR
                span_attrs.error_message = str(e)
                span_attrs.error_type = type(e).__name__
                raise
            finally:
                span_attrs.end_time = time.time()
                span_attrs.duration = span_attrs.end_time - span_attrs.start_time
            return

        # OpenTelemetry span
        span_kind_map = {
            SpanKind.INTERNAL: trace.SpanKind.INTERNAL,
            SpanKind.SERVER: trace.SpanKind.SERVER,
            SpanKind.CLIENT: trace.SpanKind.CLIENT,
            SpanKind.PRODUCER: trace.SpanKind.PRODUCER,
            SpanKind.CONSUMER: trace.SpanKind.CONSUMER,
        }

        with self.tracer.start_as_current_span(
            name,
            kind=span_kind_map.get(kind, trace.SpanKind.INTERNAL),
            attributes=attributes,
        ) as span:
            try:
                if tags:
                    for key, value in tags.items():
                        span.set_attribute(f"custom.{key}", value)

                yield span

            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.type", type(e).__name__)
                raise

    def create_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_span: str | None = None,
        attributes: dict[str, Any] | None = None,
        tags: dict[str, Any] | None = None,
    ) -> str:
        """Create a new span (manual management)"""
        span_id = str(uuid.uuid4())

        span_attrs = SpanAttributes(
            service_name=self.service_name,
            operation_name=name,
            component=self.service_name,
            span_kind=kind,
            start_time=time.time(),
            tags=tags or {},
        )

        self.span_storage[span_id] = span_attrs

        # Set current span context
        current_span.set(span_id)

        if parent_span:
            span_attrs.tags["parent_span"] = parent_span

        if attributes:
            for key, value in attributes.items():
                span_attrs.tags[f"attr.{key}"] = str(value)

        return span_id

    def finish_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        error_message: str | None = None,
        error_type: str | None = None,
        final_tags: dict[str, Any] | None = None,
    ):
        """Finish a span"""
        if span_id not in self.span_storage:
            logger.warning(f"Span {span_id} not found")
            return

        span = self.span_storage[span_id]
        span.end_time = time.time()
        span.duration = span.end_time - span.start_time
        span.status = status

        if error_message:
            span.error_message = error_message
        if error_type:
            span.error_type = error_type

        if final_tags:
            span.tags.update(final_tags)

        logger.debug(
            f"Finished span {span_id}: {span.operation_name} ({span.duration:.3f}s)"
        )

    def add_span_event(
        self, span_id: str, event_name: str, attributes: dict[str, Any] | None = None
    ):
        """Add an event to a span"""
        if span_id not in self.span_storage:
            logger.warning(f"Span {span_id} not found for event")
            return

        event = {
            "name": event_name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        }

        self.span_storage[span_id].logs.append(event)

    def add_span_metric(self, span_id: str, metric_name: str, value: float):
        """Add a metric to a span"""
        if span_id not in self.span_storage:
            logger.warning(f"Span {span_id} not found for metric")
            return

        self.span_storage[span_id].metrics[metric_name] = value

    def get_current_span(self) -> str | None:
        """Get current span ID"""
        return current_span.get()

    def get_current_trace_id(self) -> str | None:
        """Get current trace ID"""
        if self.enabled and trace:
            current_span_context = trace.get_current_span()
            if current_span_context:
                return format(current_span_context.get_span_context().trace_id, "032x")
        return current_trace_id.get()

    def get_span_data(self, span_id: str) -> SpanAttributes | None:
        """Get span data"""
        return self.span_storage.get(span_id)

    def get_trace_data(self, trace_id: str) -> list[SpanAttributes]:
        """Get all spans for a trace"""
        return [
            span
            for span in self.span_storage.values()
            if span.tags.get("trace_id") == trace_id
        ]

    def export_spans(self) -> list[dict[str, Any]]:
        """Export all spans for external processing"""
        exported = []

        for span_id, span in self.span_storage.items():
            exported.append(
                {
                    "span_id": span_id,
                    "trace_id": span.tags.get("trace_id"),
                    "parent_span_id": span.tags.get("parent_span"),
                    "operation_name": span.operation_name,
                    "service_name": span.service_name,
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration": span.duration,
                    "status": span.status.value,
                    "error_message": span.error_message,
                    "error_type": span.error_type,
                    "tags": span.tags,
                    "metrics": span.metrics,
                    "logs": span.logs,
                }
            )

        return exported


class TracingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic request tracing"""

    def __init__(self, app: ASGIApp, tracer: DistributedTracer):
        super().__init__(app)
        self.tracer = tracer

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing"""
        if not self.tracer.enabled:
            return await call_next(request)

        # Generate request ID
        request_id = str(uuid.uuid4())
        current_request_id.set(request_id)

        # Extract trace context from headers
        trace_context = self._extract_trace_context(request)

        # Start server span
        span_name = f"{request.method} {request.url.path}"

        async with self.tracer.start_span(
            span_name,
            kind=SpanKind.SERVER,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "http.target": request.url.path,
                "http.user_agent": request.headers.get("user-agent", ""),
                "http.remote_addr": request.client.host if request.client else None,
                "http.request_id": request_id,
            },
            tags={
                "route": request.url.path,
                "method": request.method,
                "request_id": request_id,
            },
        ) as span_id:
            try:
                # Add request headers to span
                if hasattr(span_id, "set_attribute"):  # OpenTelemetry span
                    for header, value in request.headers.items():
                        if not header.startswith(
                            "authorization"
                        ):  # Skip sensitive headers
                            span_id.set_attribute(
                                f"http.request.header.{header}", value
                            )

                # Process request
                start_time = time.time()
                response = await call_next(request)
                process_time = time.time() - start_time

                # Add response attributes
                response_attributes = {
                    "http.status_code": response.status_code,
                    "http.response_content_length": response.headers.get(
                        "content-length"
                    ),
                    "http.response_time_ms": process_time * 1000,
                }

                if hasattr(span_id, "set_attribute"):
                    for key, value in response_attributes.items():
                        if value is not None:
                            span_id.set_attribute(key, value)

                # Add custom metrics
                if hasattr(self.tracer, "add_span_metric"):
                    self.tracer.add_span_metric(
                        span_id, "response_time_ms", process_time * 1000
                    )
                    self.tracer.add_span_metric(
                        span_id,
                        "response_size_bytes",
                        int(response.headers.get("content-length", 0)),
                    )

                # Add response headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Trace-ID"] = (
                    self.tracer.get_current_trace_id() or ""
                )

                return response

            except Exception as e:
                # Error handling
                if hasattr(span_id, "set_attribute"):
                    span_id.set_attribute("error", True)
                    span_id.set_attribute("error.message", str(e))
                    span_id.set_attribute("error.type", type(e).__name__)

                self.tracer.add_span_event(
                    span_id,
                    "exception",
                    {"exception.message": str(e), "exception.type": type(e).__name__},
                )

                raise

    def _extract_trace_context(self, request: Request) -> TraceContext:
        """Extract trace context from request headers"""
        headers = dict(request.headers)

        trace_id = headers.get("x-trace-id") or str(uuid.uuid4())
        span_id = headers.get("x-span-id") or str(uuid.uuid4())
        parent_span_id = headers.get("x-parent-span-id")

        # Set context variables
        current_trace_id.set(trace_id)
        current_span.set(span_id)

        return TraceContext(
            trace_id=trace_id, span_id=span_id, parent_span_id=parent_span_id
        )


class TraceCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware for trace correlation across services"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation headers to response"""
        response = await call_next(request)

        # Add correlation headers if not already present
        if "X-Request-ID" not in response.headers:
            request_id = current_request_id.get() or str(uuid.uuid4())
            response.headers["X-Request-ID"] = request_id

        if "X-Trace-ID" not in response.headers:
            trace_id = current_trace_id.get() or str(uuid.uuid4())
            response.headers["X-Trace-ID"] = trace_id

        return response


# Instrumentation utilities
def instrument_httpx():
    """Instrument HTTPX for distributed tracing"""
    if OPENTELEMETRY_AVAILABLE:
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except Exception as e:
            logger.warning(f"HTTPX instrumentation failed: {e}")


def instrument_sqlalchemy():
    """Instrument SQLAlchemy for database tracing"""
    if OPENTELEMETRY_AVAILABLE:
        try:
            SQLAlchemyInstrumentor().instrument()
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.warning(f"SQLAlchemy instrumentation failed: {e}")


def instrument_redis():
    """Instrument Redis for cache tracing"""
    if OPENTELEMETRY_AVAILABLE:
        try:
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentation enabled")
        except Exception as e:
            logger.warning(f"Redis instrumentation failed: {e}")


def instrument_fastapi(app):
    """Instrument FastAPI for automatic tracing"""
    if OPENTELEMETRY_AVAILABLE:
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.warning(f"FastAPI instrumentation failed: {e}")


# Global tracer instance
global_tracer: DistributedTracer | None = None


def initialize_tracing(
    service_name: str = "psychsync-api",
    jaeger_endpoint: str | None = None,
    zipkin_endpoint: str | None = None,
    sample_rate: float = 0.1,
    enable_console: bool = True,
) -> DistributedTracer:
    """Initialize global distributed tracing"""
    global global_tracer

    global_tracer = DistributedTracer(
        service_name=service_name,
        jaeger_endpoint=jaeger_endpoint,
        zipkin_endpoint=zipkin_endpoint,
        sample_rate=sample_rate,
        enable_console=enable_console,
    )

    # Instrument common libraries
    instrument_httpx()
    instrument_sqlalchemy()
    instrument_redis()

    logger.info(f"Distributed tracing initialized for {service_name}")
    return global_tracer


def get_tracer() -> DistributedTracer | None:
    """Get global tracer instance"""
    return global_tracer


# Decorators for easy tracing
def trace_operation(name: str = None, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to trace function execution"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return await func(*args, **kwargs)

            operation_name = name or f"{func.__module__}.{func.__name__}"

            async with tracer.start_span(operation_name, kind=kind) as span_id:
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            if not tracer:
                return func(*args, **kwargs)

            operation_name = name or f"{func.__module__}.{func.__name__}"
            span_id = tracer.create_span(operation_name, kind=kind)

            try:
                result = func(*args, **kwargs)
                tracer.finish_span(span_id, SpanStatus.OK)
                return result
            except Exception as e:
                tracer.finish_span(span_id, SpanStatus.ERROR, str(e), type(e).__name__)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
