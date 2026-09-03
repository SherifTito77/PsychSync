"""
Database Prometheus metric definitions and helper functions.

Extracted here so that app/core/database/monitoring.py (inner layer) does not
need to import from app/api/v1/endpoints/ (outer layer).  Both the DB event
listeners and the Prometheus endpoint import from this neutral module instead.
"""

from prometheus_client import Counter, Gauge, Histogram

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["operation", "table"],
    buckets=(
        0.001,
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        float("inf"),
    ),
    namespace="psychsync",
)

db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
    ["database"],
    namespace="psychsync",
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Idle database connections",
    ["database"],
    namespace="psychsync",
)

db_slow_queries_total = Counter(
    "db_slow_queries_total",
    "Total number of slow queries (>1s)",
    ["table", "operation"],
    namespace="psychsync",
)


def track_db_query(
    operation: str, table: str, duration: float, is_slow: bool = False
) -> None:
    """Record a database query in Prometheus metrics."""
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
    if is_slow:
        db_slow_queries_total.labels(table=table, operation=operation).inc()


def update_db_connections(database: str, active: int, idle: int) -> None:
    """Update database connection pool metrics."""
    db_connections_active.labels(database=database).set(active)
    db_connections_idle.labels(database=database).set(idle)
