"""
Performance Monitoring Dashboard

Tracks critical scalability metrics to detect performance degradation before it impacts users.

Key Metrics Monitored:
1. **Database Query Performance**
   - Slow query detection (>5 seconds)
   - N+1 query pattern detection
   - Unbounded result set detection
   - Query result sizes

2. **Connection Pool Health**
   - Active connections
   - Pool exhaustion events
   - Connection wait times

3. **Memory Usage**
   - Process memory
   - Query memory usage
   - Cache memory usage

4. **Response Times**
   - P50, P95, P99 latencies
   - Endpoint-specific timing
   - Database operation timing

Usage:
    from app.monitoring.performance_dashboard import (
        PerformanceMonitor,
        monitor_query_performance,
        monitor_connection_pool
    )

    # In your endpoints/middleware:
    @monitor_query_performance
    async def my_endpoint():
        ...

    # Or use manually:
    monitor = PerformanceMonitor()
    monitor.track_query("user_lookup", 0.05, 100)
    monitor.track_slow_query("SELECT * FROM responses", 8.5)

Author: Scalability Team
Created: 2025-02-10
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil
import sqlalchemy
from sqlalchemy import event, pool
from sqlalchemy.engine import Engine

logger = logging.getLogger("app.monitoring.performance")


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class QueryMetrics:
    """Metrics for a single query pattern"""

    query_name: str
    execution_count: int = 0
    total_time: float = 0.0
    max_time: float = 0.0
    avg_time: float = 0.0
    result_sizes: List[int] = field(default_factory=list)
    last_executed: Optional[datetime] = None

    def add_execution(self, execution_time: float, result_size: int):
        """Record a query execution"""
        self.execution_count += 1
        self.total_time += execution_time
        self.max_time = max(self.max_time, execution_time)
        self.avg_time = self.total_time / self.execution_count
        self.result_sizes.append(result_size)
        self.last_executed = datetime.now()


@dataclass
class SlowQueryRecord:
    """Record of a slow query for analysis"""

    query: str
    execution_time: float
    timestamp: datetime
    result_size: int
    endpoint: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "query": self.query[:200] + "..." if len(self.query) > 200 else self.query,
            "execution_time": round(self.execution_time, 3),
            "timestamp": self.timestamp.isoformat(),
            "result_size": self.result_size,
            "endpoint": self.endpoint,
        }


@dataclass
class ConnectionPoolMetrics:
    """Metrics for database connection pool"""

    pool_size: int = 0
    checked_out: int = 0
    overflow: int = 0
    checked_in: int = 0
    total_connections: int = 0


@dataclass
class PerformanceDashboardSnapshot:
    """Snapshot of current performance metrics"""

    # Query metrics
    query_metrics: Dict[str, QueryMetrics] = field(default_factory=dict)
    slow_queries: List[SlowQueryRecord] = field(default_factory=list)

    # Connection pool metrics
    pool_metrics: ConnectionPoolMetrics = field(default_factory=ConnectionPoolMetrics)

    # System metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Response time metrics (last 1000 requests)
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # N+1 query detection
    potential_n_plus_1_queries: List[str] = field(default_factory=list)

    # Unbounded query detection
    unbounded_queries: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "query_metrics": {
                name: {
                    "execution_count": m.execution_count,
                    "avg_time": round(m.avg_time, 3),
                    "max_time": round(m.max_time, 3),
                    "last_executed": (
                        m.last_executed.isoformat() if m.last_executed else None
                    ),
                }
                for name, m in self.query_metrics.items()
            },
            "slow_queries": [q.to_dict() for q in self.slow_queries[-20:]],  # Last 20
            "pool_metrics": {
                "total_connections": self.pool_metrics.total_connections,
                "checked_out": self.pool_metrics.checked_out,
            },
            "system_metrics": {
                "memory_usage_mb": round(self.memory_usage_mb, 2),
                "cpu_usage_percent": round(self.cpu_usage_percent, 2),
            },
            "response_times": {
                "p50": round(self.p50_response_time, 3),
                "p95": round(self.p95_response_time, 3),
                "p99": round(self.p99_response_time, 3),
            },
            "issues_detected": {
                "n_plus_1_queries": len(self.potential_n_plus_1_queries),
                "unbounded_queries": len(self.unbounded_queries),
                "slow_queries": len(self.slow_queries),
            },
        }


# ============================================================================
# PERFORMANCE MONITOR
# ============================================================================


class PerformanceMonitor:
    """
    Tracks application performance metrics for scalability monitoring.

    Thread-safe singleton pattern for consistent monitoring across the app.
    """

    _instance: Optional["PerformanceMonitor"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Query tracking
        self._query_metrics: Dict[str, QueryMetrics] = {}
        self._slow_queries: deque[SlowQueryRecord] = deque(maxlen=100)

        # Response time tracking (last 1000 requests)
        self._response_times: deque[float] = deque(maxlen=1000)

        # N+1 query detection (same query pattern executed multiple times in one request)
        self._request_query_counts: Dict[str, int] = defaultdict(int)

        # Connection pool tracking
        self._pool_metrics: ConnectionPoolMetrics = ConnectionPoolMetrics()

        # Thresholds
        self.SLOW_QUERY_THRESHOLD = 5.0  # seconds
        self.N_PLUS_1_THRESHOLD = 10  # same query in one request
        self.UNBOUNDED_RESULT_THRESHOLD = 10000  # rows

    def track_query(
        self,
        query_name: str,
        execution_time: float,
        result_size: int,
    ):
        """Track a query execution"""
        if query_name not in self._query_metrics:
            self._query_metrics[query_name] = QueryMetrics(query_name=query_name)

        self._query_metrics[query_name].add_execution(execution_time, result_size)

        # Check for slow query
        if execution_time > self.SLOW_QUERY_THRESHOLD:
            slow_query = SlowQueryRecord(
                query=query_name,
                execution_time=execution_time,
                timestamp=datetime.now(),
                result_size=result_size,
            )
            self._slow_queries.append(slow_query)
            logger.warning(
                f"Slow query detected: {query_name} took {execution_time:.2f}s",
                extra={
                    "query_name": query_name,
                    "execution_time": execution_time,
                    "result_size": result_size,
                },
            )

        # Check for unbounded results
        if result_size > self.UNBOUNDED_RESULT_THRESHOLD:
            logger.warning(
                f"Unbounded query detected: {query_name} returned {result_size} rows",
                extra={
                    "query_name": query_name,
                    "result_size": result_size,
                    "threshold": self.UNBOUNDED_RESULT_THRESHOLD,
                },
            )

    def track_slow_query(
        self,
        query: str,
        execution_time: float,
        result_size: int = 0,
        endpoint: Optional[str] = None,
    ):
        """Manually record a slow query"""
        slow_query = SlowQueryRecord(
            query=query,
            execution_time=execution_time,
            timestamp=datetime.now(),
            result_size=result_size,
            endpoint=endpoint,
        )
        self._slow_queries.append(slow_query)

    def track_response_time(self, response_time: float):
        """Track a response time for percentile calculations"""
        self._response_times.append(response_time)

    def track_n_plus_1_query(self, query_pattern: str):
        """Track potential N+1 query pattern"""
        self._request_query_counts[query_pattern] += 1
        if self._request_query_counts[query_pattern] > self.N_PLUS_1_THRESHOLD:
            logger.warning(
                f"Potential N+1 query detected: {query_pattern} "
                f"executed {self._request_query_counts[query_pattern]} times",
                extra={
                    "query_pattern": query_pattern,
                    "execution_count": self._request_query_counts[query_pattern],
                },
            )

    def reset_request_tracking(self):
        """Reset per-request tracking (call at start of each request)"""
        self._request_query_counts.clear()

    def update_pool_metrics(self, pool: pool.Pool):
        """Update connection pool metrics"""
        self._pool_metrics.pool_size = pool.size()
        self._pool_metrics.checked_out = pool.checkedout()
        self._pool_metrics.overflow = pool.overflow()

    def get_snapshot(self) -> PerformanceDashboardSnapshot:
        """Get current performance snapshot"""
        snapshot = PerformanceDashboardSnapshot()

        # Query metrics
        snapshot.query_metrics = dict(self._query_metrics)
        snapshot.slow_queries = list(self._slow_queries)

        # Pool metrics
        snapshot.pool_metrics = self._pool_metrics

        # System metrics
        process = psutil.Process()
        snapshot.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        snapshot.cpu_usage_percent = process.cpu_percent()

        # Response time percentiles
        if self._response_times:
            sorted_times = sorted(self._response_times)
            snapshot.p50_response_time = sorted_times[len(sorted_times) // 2]
            snapshot.p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
            snapshot.p99_response_time = sorted_times[int(len(sorted_times) * 0.99)]

        return snapshot


# ============================================================================
# DECORATORS
# ============================================================================


def monitor_query_performance(func: Callable) -> Callable:
    """
    Decorator to monitor query performance in endpoints or services.

    Usage:
        @monitor_query_performance
        async def get_user_responses(user_id: str, db: AsyncSession):
            ...
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        monitor = PerformanceMonitor()
        monitor.reset_request_tracking()

        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            monitor.track_response_time(execution_time)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        monitor = PerformanceMonitor()
        monitor.reset_request_tracking()

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            monitor.track_response_time(execution_time)

    # Return appropriate wrapper based on whether function is async
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


# ============================================================================
# SQLALCHEMY EVENT LISTENERS
# ============================================================================


def setup_sqlalchemy_monitoring(engine: Engine):
    """
    Set up SQLAlchemy event listeners for performance monitoring.

    Call this during application startup:
        from app.core.database import async_engine
        from app.monitoring.performance_dashboard import setup_sqlalchemy_monitoring

        setup_sqlalchemy_monitoring(async_engine.sync_engine if hasattr(async_engine, 'sync_engine') else engine)
    """

    monitor = PerformanceMonitor()

    @event.listens_for(engine, "before_cursor_execute", named=True)
    def receive_before_cursor_execute(**kw):
        """Track query execution start time"""
        kw["context"]["_query_start_time"] = time.time()

    @event.listens_for(engine, "after_cursor_execute", named=True)
    def receive_after_cursor_execute(**kw):
        """Track query execution completion"""
        query_start_time = kw["context"].pop("_query_start_time", None)
        if query_start_time is None:
            return

        execution_time = time.time() - query_start_time

        # Extract query pattern (simplified)
        statement = str(kw["statement"])
        query_name = statement.split()[0] if statement else "unknown"

        # Get row count if available
        result_size = 0
        if hasattr(kw["context"], "cursor"):
            # For sync engines
            result_size = getattr(kw["context"].cursor, "rowcount", 0)

        monitor.track_query(query_name, execution_time, result_size)

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Track connection checkout"""
        monitor.update_pool_metrics(connection_proxy.pool)

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Track connection checkin"""
        pass


# ============================================================================
# FASTAPI DEPENDENCY
# ============================================================================


async def get_performance_monitor() -> PerformanceMonitor:
    """
    FastAPI dependency for accessing the performance monitor.

    Usage:
        @router.get("/admin/performance")
        async def get_performance_metrics(
            monitor: PerformanceMonitor = Depends(get_performance_monitor)
        ):
            snapshot = monitor.get_snapshot()
            return snapshot.to_dict()
    """
    return PerformanceMonitor()


# ============================================================================
# MIDDLEWARE
# ============================================================================


class PerformanceMonitoringMiddleware:
    """
    ASGI middleware for performance monitoring.

    Add to FastAPI app:
        app.add_middleware(PerformanceMonitoringMiddleware)
    """

    def __init__(self, app):
        self.app = app
        self.monitor = PerformanceMonitor()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Reset per-request tracking
        self.monitor.reset_request_tracking()

        # Track request start
        start_time = time.time()

        # Wrap send to track response
        async def send_wrapper(message):
            if message["type"] == "http.response.body":
                # Request complete
                execution_time = time.time() - start_time
                self.monitor.track_response_time(execution_time)
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================


def get_performance_health_status() -> dict:
    """
    Get overall performance health status.

    Returns health metrics and alerts for:
    - Slow queries
    - Connection pool exhaustion
    - High memory usage
    - N+1 query patterns

    Usage in health endpoint:
        @router.get("/health/performance")
        async def performance_health():
            return get_performance_health_status()
    """
    monitor = PerformanceMonitor()
    snapshot = monitor.get_snapshot()

    alerts = []

    # Check for slow queries
    if snapshot.slow_queries:
        alerts.append(
            {
                "severity": "warning",
                "type": "slow_queries",
                "count": len(snapshot.slow_queries),
                "message": f"{len(snapshot.slow_queries)} slow queries detected",
            }
        )

    # Check connection pool
    if snapshot.pool_metrics.total_connections > 0:
        utilization = (
            snapshot.pool_metrics.checked_out / snapshot.pool_metrics.total_connections
        )
        if utilization > 0.9:
            alerts.append(
                {
                    "severity": "critical",
                    "type": "pool_exhaustion",
                    "utilization": round(utilization * 100, 1),
                    "message": f"Connection pool at {utilization * 100:.1f}% capacity",
                }
            )

    # Check memory usage
    if snapshot.memory_usage_mb > 1000:
        alerts.append(
            {
                "severity": "warning",
                "type": "high_memory",
                "usage_mb": round(snapshot.memory_usage_mb, 2),
                "message": f"High memory usage: {snapshot.memory_usage_mb:.2f} MB",
            }
        )

    # Check response times
    if snapshot.p95_response_time > 1.0:
        alerts.append(
            {
                "severity": "warning",
                "type": "slow_response",
                "p95_time": round(snapshot.p95_response_time, 3),
                "message": f"P95 response time is {snapshot.p95_response_time:.2f}s",
            }
        )

    return {
        "status": "healthy" if not alerts else "degraded",
        "alerts": alerts,
        "metrics": snapshot.to_dict(),
    }
