"""
Query Performance Monitoring

This module provides utilities for tracking database query performance.
It helps identify slow queries and provides metrics for optimization.

Features:
- Automatic query timing
- Slow query logging (queries > 1s)
- Prometheus metrics integration
- Query performance statistics

Usage:
    from app.core.query_performance import track_query_performance

    @track_query_performance("get_user_with_teams")
    async def get_user_teams(user_id: UUID, db: AsyncSession):
        # ... query logic ...
        pass
"""

import contextlib
import logging
import time
from collections import defaultdict
from contextvars import ContextVar
from typing import Any, Callable

from prometheus_client import Histogram

logger = logging.getLogger(__name__)

# Context variable for tracking nested queries
query_depth: ContextVar[int] = ContextVar("query_depth", default=0)


# ==================== PROMETHEUS METRICS ====================

query_duration_histogram = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_name", "slow_query"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

query_count_total = Histogram(
    "db_query_count_total",
    "Total number of database queries",
    ["query_name"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000],
)


# ==================== QUERY STATISTICS ====================


class QueryStatistics:
    """Track query execution statistics."""

    def __init__(self):
        self.query_counts: dict[str, int] = defaultdict(int)
        self.query_durations: dict[str, list[float]] = defaultdict(list)
        self.slow_queries: list[dict[str, Any]] = []

    def record_query(
        self,
        query_name: str,
        duration: float,
        is_slow: bool = False,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record query execution statistics."""
        self.query_counts[query_name] += 1
        self.query_durations[query_name].append(duration)

        if is_slow:
            self.slow_queries.append(
                {
                    "query_name": query_name,
                    "duration": duration,
                    "timestamp": time.time(),
                    "context": context or {},
                }
            )

    def get_stats(self) -> dict[str, Any]:
        """Get current statistics."""
        stats = {
            "total_queries": sum(self.query_counts.values()),
            "unique_queries": len(self.query_counts),
            "slow_query_count": len(self.slow_queries),
            "top_queries": {},
        }

        # Calculate average durations and top queries
        for query_name, durations in self.query_durations.items():
            avg_duration = sum(durations) / len(durations)
            count = self.query_counts[query_name]
            stats["top_queries"][query_name] = {
                "count": count,
                "avg_duration": avg_duration,
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_duration": sum(durations),
            }

        # Sort by total duration
        stats["top_queries"] = dict(
            sorted(
                stats["top_queries"].items(),
                key=lambda x: x[1]["total_duration"],
                reverse=True,
            )[:10]
        )

        return stats


# Global statistics instance
query_stats = QueryStatistics()


# ==================== QUERY TRACKING DECORATOR ====================


def track_query_performance(
    query_name: str | None = None,
    slow_threshold: float = 1.0,
    log_context: bool = False,
) -> Callable:
    """
    Decorator to track query performance.

    Args:
        query_name: Name for the query (defaults to function name)
        slow_threshold: Duration threshold for "slow" queries (seconds)
        log_context: Whether to log additional context

    Example:
        @track_query_performance("get_user_teams")
        async def get_user_teams(user_id: UUID, db: AsyncSession):
            # Query logic here
            pass

    Metrics:
    - Query duration (histogram)
    - Query count (histogram)
    - Slow query logging
    """

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            name = query_name or func.__name__
            start_time = time.time()

            # Track query depth
            depth = query_depth.get()
            query_depth.set(depth + 1)

            try:
                # Execute query
                result = await func(*args, **kwargs)

                # Calculate duration
                duration = time.time() - start_time
                is_slow = duration > slow_threshold

                # Record Prometheus metrics
                query_duration_histogram.labels(
                    query_name=name, slow_query=str(is_slow)
                ).observe(duration)

                query_count_total.labels(query_name=name).observe(1)

                # Record statistics
                context_data = (
                    {
                        "function": func.__name__,
                        "depth": depth,
                    }
                    if log_context
                    else None
                )

                query_stats.record_query(name, duration, is_slow, context_data)

                # Log slow queries
                if is_slow:
                    logger.warning(
                        f"Slow query detected: {name} took {duration:.3f}s",
                        extra={
                            "query_name": name,
                            "duration_seconds": duration,
                            "threshold": slow_threshold,
                            "depth": depth,
                        },
                    )
                else:
                    logger.debug(
                        f"Query {name} completed in {duration:.3f}s",
                        extra={"query_name": name, "duration_seconds": duration},
                    )

                return result

            finally:
                # Restore query depth
                query_depth.set(depth)

        return async_wrapper

    return decorator


# ==================== CONTEXT MANAGER ====================


@contextlib.contextmanager
def track_query_timing(query_name: str, slow_threshold: float = 1.0):
    """
    Context manager for tracking query timing.

    Use this when you can't use the decorator (e.g., inline queries).

    Args:
        query_name: Name for the query
        slow_threshold: Duration threshold for "slow" queries

    Example:
        with track_query_timing("get_all_teams"):
            teams = await db.execute(select(Team))
    """
    start_time = time.time()
    depth = query_depth.get()
    query_depth.set(depth + 1)

    try:
        yield
    finally:
        duration = time.time() - start_time
        is_slow = duration > slow_threshold

        # Record Prometheus metrics
        query_duration_histogram.labels(
            query_name=query_name, slow_query=str(is_slow)
        ).observe(duration)

        query_count_total.labels(query_name=query_name).observe(1)

        # Record statistics
        query_stats.record_query(query_name, duration, is_slow)

        # Log slow queries
        if is_slow:
            logger.warning(
                f"Slow query detected: {query_name} took {duration:.3f}s",
                extra={
                    "query_name": query_name,
                    "duration_seconds": duration,
                    "threshold": slow_threshold,
                },
            )

        # Restore query depth
        query_depth.set(depth)


# ==================== UTILITY FUNCTIONS ====================


def get_query_statistics() -> dict[str, Any]:
    """Get current query statistics."""
    return query_stats.get_stats()


def get_slow_queries(limit: int = 100) -> list[dict[str, Any]]:
    """
    Get recent slow queries.

    Args:
        limit: Maximum number of slow queries to return

    Returns:
        List of slow query information
    """
    return query_stats.slow_queries[-limit:]


def reset_statistics() -> None:
    """Reset query statistics (useful for testing)."""
    query_stats.query_counts.clear()
    query_stats.query_durations.clear()
    query_stats.slow_queries.clear()


# ==================== ENDPOINT EXAMPLES ====================


class QueryPerformanceExamples:
    """
    Examples of using query performance tracking in endpoints.

    These examples show how to integrate performance tracking into your code.
    """

    @staticmethod
    @track_query_performance("get_user_profile", slow_threshold=0.5)
    async def example_tracked_query(user_id: str, db):
        """
        Example: Query with performance tracking via decorator.

        Performance is automatically tracked and logged.
        """
        # Your query logic here
        pass

    @staticmethod
    async def example_manual_tracking(db):
        """
        Example: Query with manual performance tracking via context manager.

        Use this when you can't use the decorator.
        """
        with track_query_timing("get_all_teams", slow_threshold=0.3):
            # Your query logic here
            result = await db.execute("SELECT * FROM teams")
            return result


# ==================== EXPORTS ====================

__all__ = [
    # Decorator
    "track_query_performance",
    # Context manager
    "track_query_timing",
    # Statistics
    "get_query_statistics",
    "get_slow_queries",
    "reset_statistics",
    # Examples
    "QueryPerformanceExamples",
]
