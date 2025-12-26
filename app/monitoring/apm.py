# app/monitoring/apm.py
"""
Application Performance Monitoring (APM) System
- Request tracing and performance metrics
- Database query monitoring
- Error tracking and alerting
- Resource utilization monitoring
- Custom metrics and dashboards
"""

import time
import asyncio
import psutil
import gc
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.core.enhanced_cache import get_cache_manager

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RequestTrace:
    """Request trace information"""
    trace_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error: Optional[str] = None
    db_queries: List[Dict[str, Any]] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0

@dataclass
class DatabaseMetric:
    """Database performance metric"""
    query: str
    duration_ms: float
    timestamp: datetime
    success: bool
    rows_affected: Optional[int] = None
    error: Optional[str] = None

class MetricsCollector:
    """Collects and aggregates performance metrics"""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.request_traces: deque = deque(maxlen=max_metrics)
        self.db_metrics: deque = deque(maxlen=max_metrics)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric"""
        async with self._lock:
            self.metrics.append(metric)
            # Update aggregates
            if metric.name == "http_request_duration":
                endpoint = metric.tags.get("endpoint", "unknown")
                self.endpoint_stats[endpoint].append(metric.value)
                # Keep only last 1000 measurements per endpoint
                if len(self.endpoint_stats[endpoint]) > 1000:
                    self.endpoint_stats[endpoint] = self.endpoint_stats[endpoint][-1000:]

    async def add_request_trace(self, trace: RequestTrace):
        """Add a request trace"""
        async with self._lock:
            self.request_traces.append(trace)
            if trace.error:
                error_key = f"{trace.status_code}:{trace.error[:50]}"
                self.error_counts[error_key] += 1

    async def add_db_metric(self, metric: DatabaseMetric):
        """Add a database metric"""
        async with self._lock:
            self.db_metrics.append(metric)

    async def get_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get metrics summary for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        async with self._lock:
            # Filter recent metrics
            recent_metrics = [
                m for m in self.metrics
                if m.timestamp >= cutoff_time
            ]

            recent_traces = [
                t for t in self.request_traces
                if t.timestamp >= cutoff_time
            ]

            recent_db_metrics = [
                d for d in self.db_metrics
                if d.timestamp >= cutoff_time
            ]

            # Calculate aggregates
            total_requests = len(recent_traces)
            error_requests = len([t for t in recent_traces if t.error])
            avg_response_time = sum(t.duration_ms for t in recent_traces) / total_requests if total_requests > 0 else 0

            # Database metrics
            total_db_queries = len(recent_db_metrics)
            avg_db_duration = sum(d.duration_ms for d in recent_db_metrics) / total_db_queries if total_db_queries > 0 else 0
            db_error_rate = len([d for d in recent_db_metrics if not d.success]) / total_db_queries if total_db_queries > 0 else 0

            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            return {
                "time_range_minutes": minutes,
                "timestamp": datetime.utcnow().isoformat(),
                "requests": {
                    "total": total_requests,
                    "errors": error_requests,
                    "error_rate": error_requests / total_requests if total_requests > 0 else 0,
                    "avg_response_time_ms": round(avg_response_time, 2),
                    "requests_per_minute": round(total_requests / minutes, 2)
                },
                "database": {
                    "total_queries": total_db_queries,
                    "avg_duration_ms": round(avg_db_duration, 2),
                    "error_rate": round(db_error_rate, 4),
                    "queries_per_minute": round(total_db_queries / minutes, 2)
                },
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_info.percent,
                    "memory_used_gb": round(memory_info.used / (1024**3), 2),
                    "memory_total_gb": round(memory_info.total / (1024**3), 2),
                    "disk_percent": disk_info.percent,
                    "disk_used_gb": round(disk_info.used / (1024**3), 2),
                    "disk_total_gb": round(disk_info.total / (1024**3), 2)
                },
                "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5])
            }

    async def get_endpoint_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """Get endpoint-specific statistics"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        async with self._lock:
            endpoint_stats = {}
            for endpoint, durations in self.endpoint_stats.items():
                # Filter recent durations
                recent_durations = [
                    d for _, trace in zip(durations, self.request_traces)
                    if trace.timestamp >= cutoff_time
                ]

                if recent_durations:
                    endpoint_stats[endpoint] = {
                        "count": len(recent_durations),
                        "avg_duration_ms": round(sum(recent_durations) / len(recent_durations), 2),
                        "min_duration_ms": round(min(recent_durations), 2),
                        "max_duration_ms": round(max(recent_durations), 2),
                        "p95_duration_ms": round(sorted(recent_durations)[int(len(recent_durations) * 0.95)], 2),
                        "p99_duration_ms": round(sorted(recent_durations)[int(len(recent_durations) * 0.99)], 2)
                    }

            return endpoint_stats

class APMMiddleware(BaseHTTPMiddleware):
    """APM middleware for request tracing and metrics collection"""

    def __init__(self, app, metrics_collector: MetricsCollector = None):
        super().__init__(app)
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.cache_manager = get_cache_manager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start request tracing
        start_time = time.time()
        trace_id = request.headers.get("x-request-id", f"trace_{int(time.time() * 1000000)}")

        # Initialize trace data
        trace_data = RequestTrace(
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=0,  # Will be set later
            duration_ms=0,  # Will be calculated later
            timestamp=datetime.utcnow(),
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent")
        )

        # Add trace ID to request state
        request.state.trace_id = trace_id
        request.state.trace_start_time = start_time
        request.state.db_queries = []
        request.state.cache_hits = 0
        request.state.cache_misses = 0

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Update trace data
            trace_data.status_code = response.status_code
            trace_data.duration_ms = duration_ms
            trace_data.db_queries = getattr(request.state, 'db_queries', [])
            trace_data.cache_hits = getattr(request.state, 'cache_hits', 0)
            trace_data.cache_misses = getattr(request.state, 'cache_misses', 0)

            # Add metrics
            await self.metrics_collector.add_metric(PerformanceMetric(
                name="http_request_duration",
                value=duration_ms,
                unit="ms",
                timestamp=datetime.utcnow(),
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status_code": str(response.status_code),
                    "trace_id": trace_id
                }
            ))

            # Add response size metric
            content_length = response.headers.get("content-length")
            if content_length:
                await self.metrics_collector.add_metric(PerformanceMetric(
                    name="http_response_size",
                    value=float(content_length),
                    unit="bytes",
                    timestamp=datetime.utcnow(),
                    tags={
                        "endpoint": request.url.path,
                        "method": request.method
                    }
                ))

            # Add trace to collector
            await self.metrics_collector.add_request_trace(trace_data)

            # Add APM headers to response
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))
            response.headers["X-DB-Queries"] = str(len(trace_data.db_queries))

            return response

        except Exception as e:
            # Calculate duration for failed request
            duration_ms = (time.time() - start_time) * 1000

            # Update trace data with error
            trace_data.status_code = 500
            trace_data.duration_ms = duration_ms
            trace_data.error = str(e)
            trace_data.db_queries = getattr(request.state, 'db_queries', [])
            trace_data.cache_hits = getattr(request.state, 'cache_hits', 0)
            trace_data.cache_misses = getattr(request.state, 'cache_misses', 0)

            # Add error metric
            await self.metrics_collector.add_metric(PerformanceMetric(
                name="http_request_error",
                value=1,
                unit="count",
                timestamp=datetime.utcnow(),
                tags={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "error_type": type(e).__name__,
                    "trace_id": trace_id
                }
            ))

            # Add trace to collector
            await self.metrics_collector.add_request_trace(trace_data)

            # Re-raise exception
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

class DatabaseAPM:
    """Database performance monitoring"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def register_engine_listeners(self, engine: Engine):
        """Register SQLAlchemy event listeners for database monitoring"""

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                duration_ms = (time.time() - context._query_start_time) * 1000

                # Add database metric
                asyncio.create_task(self.metrics_collector.add_db_metric(DatabaseMetric(
                    query=statement[:200] + "..." if len(statement) > 200 else statement,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    success=True,
                    rows_affected=cursor.rowcount if cursor else None
                )))

        @event.listens_for(engine, "handle_error")
        def handle_error(context, exception):
            if hasattr(context, '_query_start_time'):
                duration_ms = (time.time() - context._query_start_time) * 1000

                # Add error metric
                asyncio.create_task(self.metrics_collector.add_db_metric(DatabaseMetric(
                    query=str(context.statement)[:200] + "..." if len(str(context.statement)) > 200 else str(context.statement),
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    success=False,
                    error=str(exception)
                )))

class CustomMetrics:
    """Custom metrics collection"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    async def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, Any] = None):
        """Increment a counter metric"""
        await self.metrics_collector.add_metric(PerformanceMetric(
            name=name,
            value=value,
            unit="count",
            timestamp=datetime.utcnow(),
            tags=tags or {}
        ))

    async def record_gauge(self, name: str, value: float, tags: Dict[str, Any] = None):
        """Record a gauge metric"""
        await self.metrics_collector.add_metric(PerformanceMetric(
            name=name,
            value=value,
            unit="value",
            timestamp=datetime.utcnow(),
            tags=tags or {}
        ))

    async def record_histogram(self, name: str, value: float, tags: Dict[str, Any] = None):
        """Record a histogram metric"""
        await self.metrics_collector.add_metric(PerformanceMetric(
            name=name,
            value=value,
            unit="value",
            timestamp=datetime.utcnow(),
            tags=tags or {}
        ))

    async def record_user_activity(self, user_id: str, activity: str, metadata: Dict[str, Any] = None):
        """Record user activity metric"""
        await self.metrics_collector.add_metric(PerformanceMetric(
            name="user_activity",
            value=1,
            unit="count",
            timestamp=datetime.utcnow(),
            tags={
                "user_id": user_id,
                "activity": activity,
                **(metadata or {})
            }
        ))

    async def record_business_metric(self, name: str, value: float, business_context: Dict[str, Any] = None):
        """Record business-specific metric"""
        await self.metrics_collector.add_metric(PerformanceMetric(
            name=name,
            value=value,
            unit="value",
            timestamp=datetime.utcnow(),
            tags=business_context or {}
        ))

# Global APM instances
_metrics_collector: Optional[MetricsCollector] = None
_custom_metrics: Optional[CustomMetrics] = None
_db_apm: Optional[DatabaseAPM] = None

def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def get_custom_metrics() -> CustomMetrics:
    """Get global custom metrics instance"""
    global _custom_metrics
    if _custom_metrics is None:
        _custom_metrics = CustomMetrics(get_metrics_collector())
    return _custom_metrics

def get_db_apm() -> DatabaseAPM:
    """Get global database APM instance"""
    global _db_apm
    if _db_apm is None:
        _db_apm = DatabaseAPM(get_metrics_collector())
    return _db_apm

@asynccontextmanager
async def trace_operation(operation_name: str, tags: Dict[str, Any] = None):
    """Context manager for tracing custom operations"""
    start_time = time.time()
    trace_id = f"op_{int(time.time() * 1000000)}"

    try:
        yield trace_id
        duration_ms = (time.time() - start_time) * 1000

        # Record successful operation
        await get_metrics_collector().add_metric(PerformanceMetric(
            name="operation_duration",
            value=duration_ms,
            unit="ms",
            timestamp=datetime.utcnow(),
            tags={
                "operation": operation_name,
                "trace_id": trace_id,
                "success": "true",
                **(tags or {})
            }
        ))
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        # Record failed operation
        await get_metrics_collector().add_metric(PerformanceMetric(
            name="operation_error",
            value=1,
            unit="count",
            timestamp=datetime.utcnow(),
            tags={
                "operation": operation_name,
                "trace_id": trace_id,
                "error_type": type(e).__name__,
                "error": str(e)[:100],
                **(tags or {})
            }
        ))
        raise

# Performance monitoring utilities
def monitor_performance(func_name: str = None):
    """Decorator for monitoring function performance"""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                await get_metrics_collector().add_metric(PerformanceMetric(
                    name="function_duration",
                    value=duration_ms,
                    unit="ms",
                    timestamp=datetime.utcnow(),
                    tags={
                        "function": name,
                        "success": "true"
                    }
                ))

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                await get_metrics_collector().add_metric(PerformanceMetric(
                    name="function_error",
                    value=1,
                    unit="count",
                    timestamp=datetime.utcnow(),
                    tags={
                        "function": name,
                        "error_type": type(e).__name__
                    }
                ))
                raise
        return wrapper
    return decorator