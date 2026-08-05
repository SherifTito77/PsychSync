"""
Prometheus Metrics Endpoint

CRITICAL: This is the missing piece that makes all metrics visible to Prometheus.
Without this endpoint, the excellent metrics collection throughout the codebase
is invisible to the monitoring ecosystem.

This creates a standard /metrics endpoint that Prometheus can scrape.
"""

from fastapi import APIRouter
from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    Info,
    Summary,
    generate_latest,
)
from prometheus_client.openmetrics.exposition import (
    generate_latest as generate_latest_openmetrics,
)
from starlette.responses import Response

router = APIRouter(tags=["monitoring"])

# ============================================================================
# HTTP METRICS (RED Method - Rate, Errors, Duration)
# ============================================================================

# Request count by endpoint, method, and status
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    namespace="psychsync",
)

# Request duration histogram (in seconds)
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    ),
    namespace="psychsync",
)

# Request size histogram
http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size",
    ["method", "endpoint"],
    namespace="psychsync",
)

# Response size histogram
http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size",
    ["method", "endpoint"],
    namespace="psychsync",
)

# Active requests gauge
http_requests_active = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
    ["method", "endpoint"],
    namespace="psychsync",
)

# ============================================================================
# DATABASE METRICS
# ============================================================================
# Imported from neutral monitoring module so core/database/monitoring.py
# does not need to import from the API layer.
from app.monitoring.db_metrics import (  # noqa: E402
    db_connections_active,
    db_connections_idle,
    db_query_duration_seconds,
    db_slow_queries_total,
    track_db_query,
    update_db_connections,
)

# ============================================================================
# CACHE METRICS (Redis)
# ============================================================================

# Cache operations
cache_operations_total = Counter(
    "cache_operations_total",
    "Total cache operations",
    ["operation", "cache"],  # operation: get/set/delete, cache: redis
    namespace="psychsync",
)

# Cache hit/miss
cache_hits_total = Counter(
    "cache_hits_total", "Total cache hits", ["cache"], namespace="psychsync"
)

cache_misses_total = Counter(
    "cache_misses_total", "Total cache misses", ["cache"], namespace="psychsync"
)

# Cache duration
cache_operation_duration_seconds = Histogram(
    "cache_operation_duration_seconds",
    "Cache operation duration",
    ["operation", "cache"],
    buckets=(
        0.0001,
        0.0005,
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        float("inf"),
    ),
    namespace="psychsync",
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

# User registrations
user_registrations_total = Counter(
    "user_registrations_total", "Total user registrations", namespace="psychsync"
)

# Active users
users_active_total = Gauge(
    "users_active_total",
    "Number of active users",
    ["timeframe"],  # 24h, 7d, 30d
    namespace="psychsync",
)

# Assessment completions
assessments_completed_total = Counter(
    "assessments_completed_total",
    "Total assessment completions",
    ["assessment_type"],
    namespace="psychsync",
)

# Team operations
team_operations_total = Counter(
    "team_operations_total",
    "Total team operations",
    ["operation"],  # create, update, delete, add_member, remove_member
    namespace="psychsync",
)

# ============================================================================
# SECURITY METRICS
# ============================================================================

# Failed authentication attempts
auth_failures_total = Counter(
    "auth_failures_total",
    "Total failed authentication attempts",
    ["method"],  # password, token, mfa
    namespace="psychsync",
)

# Successful authentication
auth_success_total = Counter(
    "auth_success_total",
    "Total successful authentications",
    ["method"],
    namespace="psychsync",
)

# Security incidents
security_incidents_total = Counter(
    "security_incidents_total",
    "Total security incidents",
    ["severity", "type"],
    namespace="psychsync",
)

# Security score (0-100)
security_score = Gauge(
    "security_score",
    "Overall security score (0-100)",
    ["component"],
    namespace="psychsync",
)

# ============================================================================
# INFRASTRUCTURE METRICS
# ============================================================================

# System info
app_info = Info("app", "Application information", namespace="psychsync")

# Build info
build_info = Info("build", "Build information", namespace="psychsync")

# ============================================================================
# CELERY TASK METRICS
# ============================================================================

# Task executions
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total Celery task executions",
    ["task_name", "status"],  # status: success, failure, retry
    namespace="psychsync",
)

# Task duration
celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution duration",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
    namespace="psychsync",
)

# Queue length
celery_queue_length = Gauge(
    "celery_queue_length",
    "Number of tasks in queue",
    ["queue_name"],
    namespace="psychsync",
)

# Task latency (time in queue)
celery_task_latency_seconds = Histogram(
    "celery_task_latency_seconds",
    "Task queue latency",
    ["task_name", "queue_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf")),
    namespace="psychsync",
)

# Dead letter queue
celery_dlq_size = Gauge(
    "celery_dlq_size", "Number of tasks in dead letter queue", namespace="psychsync"
)

# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """
    Standard Prometheus metrics endpoint.

    This is the CRITICAL missing piece - Prometheus scrapes this endpoint
    every 15-30 seconds to collect metrics.

    Returns:
        Prometheus text format metrics
    """
    # Update info metrics
    app_info.info({"version": "1.0.0", "environment": "production"})

    build_info.info(
        {"build_date": "2025-02-10", "git_commit": "abc123", "branch": "main"}
    )

    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/metrics/openmetrics", include_in_schema=False)
async def prometheus_metrics_openmetrics():
    """
    OpenMetrics format endpoint (newer Prometheus format).

    Returns:
        OpenMetrics format metrics
    """
    return Response(
        content=generate_latest_openmetrics(REGISTRY),
        media_type="application/openmetrics-text; version=1.0.0; charset=utf-8",
    )


# ============================================================================
# MIDDLEWARE INTEGRATION HELPERS
# ============================================================================


def track_http_request(method: str, endpoint: str, status: int, duration: float):
    """
    Track HTTP request metrics

    Call this from middleware after each request completes.

    Args:
        method: HTTP method
        endpoint: Request path
        status: HTTP status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(
        method=method, endpoint=endpoint, status=str(status)
    ).inc()

    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )


def track_cache_operation(operation: str, cache: str, hit: bool, duration: float):
    """
    Track cache operation metrics

    Args:
        operation: get, set, delete
        cache: Cache name (redis, etc.)
        hit: Whether it was a hit
        duration: Operation duration in seconds
    """
    cache_operations_total.labels(operation=operation, cache=cache).inc()

    if hit:
        cache_hits_total.labels(cache=cache).inc()
    else:
        cache_misses_total.labels(cache=cache).inc()

    cache_operation_duration_seconds.labels(operation=operation, cache=cache).observe(
        duration
    )


def track_celery_task(task_name: str, status: str, duration: float):
    """
    Track Celery task execution

    Args:
        task_name: Task name
        status: success, failure, retry
        duration: Task duration in seconds
    """
    celery_tasks_total.labels(task_name=task_name, status=status).inc()

    celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def update_security_score(component: str, score: float):
    """
    Update security score metric

    Args:
        component: Component name
        score: Score 0-100
    """
    security_score.labels(component=component).set(score)


def update_active_users(timeframe: str, count: int):
    """
    Update active users gauge

    Args:
        timeframe: 24h, 7d, 30d
        count: Number of active users
    """
    users_active_total.labels(timeframe=timeframe).set(count)


# ============================================================================
# EXPORTS FOR USE IN OTHER MODULES
# ============================================================================

__all__ = [
    # HTTP Metrics
    "http_requests_total",
    "http_request_duration_seconds",
    "http_request_size_bytes",
    "http_response_size_bytes",
    "http_requests_active",
    # Database Metrics
    "db_query_duration_seconds",
    "db_connections_active",
    "db_connections_idle",
    "db_slow_queries_total",
    # Cache Metrics
    "cache_operations_total",
    "cache_hits_total",
    "cache_misses_total",
    "cache_operation_duration_seconds",
    # Business Metrics
    "user_registrations_total",
    "users_active_total",
    "assessments_completed_total",
    "team_operations_total",
    # Security Metrics
    "auth_failures_total",
    "auth_success_total",
    "security_incidents_total",
    "security_score",
    # Celery Metrics
    "celery_tasks_total",
    "celery_task_duration_seconds",
    "celery_queue_length",
    "celery_task_latency_seconds",
    "celery_dlq_size",
    # Helper functions
    "track_http_request",
    "track_db_query",
    "track_cache_operation",
    "track_celery_task",
    "update_security_score",
    "update_active_users",
    "update_db_connections",
]
