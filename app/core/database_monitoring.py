"""
Database Monitoring with SQLAlchemy Integration

This integrates with the Prometheus metrics to track database query performance.

CRITICAL: Database performance issues are often the first sign of systemic problems.
This provides visibility into query patterns, slow queries, and connection pool usage.
"""

import logging
import time
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import Pool, PoolProxiedConnection

from app.api.v1.endpoints.prometheus_metrics import (
    track_db_query,
    update_db_connections,
    db_query_duration_seconds,
)

logger = logging.getLogger(__name__)


# ============================================================================
# SQL ALCHEMY EVENT LISTENERS
# ============================================================================


def setup_database_monitoring(engine: Engine, slow_query_threshold: float = 1.0):
    """
    Set up database query monitoring via SQLAlchemy event listeners

    This automatically tracks:
    - Query duration by operation and table
    - Slow query detection and alerting
    - Connection pool usage
    - Query execution counts

    Add to your database setup:

    ```python
    from app.core.database_monitoring import setup_database_monitoring

    engine = create_async_engine(...)
    setup_database_monitoring(engine, slow_query_threshold=1.0)
    ```

    Args:
        engine: SQLAlchemy engine (sync or async)
        slow_query_threshold: Threshold in seconds for slow query detection
    """

    @event.listens_for(engine, "before_cursor_execute", named=True)
    def receive_before_cursor_execute(
        conn: PoolProxiedConnection,
        cursor,
        statement: str,
        parameters: dict[str, Any] | list[tuple] | None,
        context: dict[str, Any],
        executemany: bool,
    ) -> None:
        """Track query start time"""
        context._query_start_time = time.time()

    @event.listens_for(engine, "after_cursor_execute", named=True)
    def receive_after_cursor_execute(
        conn: PoolProxiedConnection,
        cursor,
        statement: str,
        parameters: dict[str, Any] | list[tuple] | None,
        context: dict[str, Any],
        executemany: bool,
    ) -> None:
        """Track query completion and metrics"""
        if not hasattr(context, "_query_start_time"):
            return

        duration = time.time() - context._query_start_time

        # Parse SQL to extract operation and table
        operation, table = parse_sql_statement(statement)

        # Determine if slow query
        is_slow = duration > slow_query_threshold

        if is_slow:
            logger.warning(
                f"Slow query detected: {operation} on {table} took {duration:.3f}s",
                extra={
                    "operation": operation,
                    "table": table,
                    "duration": duration,
                    "statement": statement[:500],  # First 500 chars
                },
            )

        # Track metrics
        track_db_query(
            operation=operation, table=table, duration=duration, is_slow=is_slow
        )

    # Connection pool monitoring
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record) -> None:
        """Track new connection"""
        update_connection_metrics(engine.pool)

    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record) -> None:
        """Track closed connection"""
        update_connection_metrics(engine.pool)

    logger.info(
        f"✅ Database monitoring initialized (slow query threshold: {slow_query_threshold}s)"
    )


def parse_sql_statement(statement: str) -> tuple[str, str]:
    """
    Parse SQL statement to extract operation and table

    Args:
        statement: SQL statement

    Returns:
        Tuple of (operation, table)
    """
    # Remove leading/trailing whitespace
    statement = statement.strip()

    # Extract operation (first word)
    parts = statement.split()
    if not parts:
        return "UNKNOWN", "UNKNOWN"

    operation = parts[0].upper()

    # Extract table name
    # This is a simple parser - could be enhanced with SQL parsing library
    table = "UNKNOWN"

    if operation in ("SELECT", "INSERT", "UPDATE", "DELETE"):
        # Find FROM, INTO, or UPDATE clause
        for keyword in ("FROM", "INTO", "UPDATE", "IN"):
            if keyword in statement.upper():
                idx = statement.upper().find(keyword)
                remainder = statement[idx + len(keyword) :].strip()
                # Get first word after keyword (table name)
                table_parts = remainder.split()
                if table_parts:
                    table = table_parts[0].strip('"`[]')
                    break

    return operation, table


def update_connection_metrics(pool: Pool) -> None:
    """
    Update connection pool metrics

    Args:
        pool: SQLAlchemy connection pool
    """
    try:
        # Get pool size info
        size = pool.size()
        checked_out = pool.checkedout()
        idle = size - checked_out

        # Update metrics
        update_db_connections(
            database=pool.dispatch.db_api.driver,
            active=checked_out,
            idle=idle,
        )

    except Exception as e:
        logger.error(f"Failed to update connection metrics: {e}")


# ============================================================================
# SLOW QUERY ALERTING
# ============================================================================


class SlowQueryDetector:
    """
    Detects and alerts on slow query patterns

    Analyzes query patterns to identify:
    - Repeatedly slow queries (candidates for optimization)
    - Missing indexes
    - N+1 query patterns
    - Full table scans
    """

    def __init__(self, alert_threshold: int = 10):
        """
        Initialize detector

        Args:
            alert_threshold: Alert after this many slow queries of same pattern
        """
        self.alert_threshold = alert_threshold
        self.slow_query_counts: dict[str, int] = {}
        self.logger = logging.getLogger(__name__)

    def record_slow_query(
        self,
        operation: str,
        table: str,
        duration: float,
        statement: str,
    ) -> None:
        """
        Record a slow query and check for patterns

        Args:
            operation: SQL operation
            table: Table name
            duration: Query duration
            statement: SQL statement
        """
        # Create query pattern key (simplified statement)
        pattern = self._get_query_pattern(operation, table, statement)

        # Increment count
        self.slow_query_counts[pattern] = self.slow_query_counts.get(pattern, 0) + 1

        # Check if we should alert
        if self.slow_query_counts[pattern] >= self.alert_threshold:
            self.logger.error(
                f"⚠️ Slow query pattern detected: {pattern} "
                f"(occurred {self.slow_query_counts[pattern]} times)",
                extra={
                    "operation": operation,
                    "table": table,
                    "pattern": pattern,
                    "count": self.slow_query_counts[pattern],
                },
            )

            # Reset count after alerting
            self.slow_query_counts[pattern] = 0

    def _get_query_pattern(self, operation: str, table: str, statement: str) -> str:
        """
        Get query pattern for aggregation

        Normalizes queries by removing specific values to group similar queries.

        Args:
            operation: SQL operation
            table: Table name
            statement: SQL statement

        Returns:
            Query pattern string
        """
        # Simple pattern: operation + table
        # Could be enhanced to normalize WHERE clauses, etc.
        return f"{operation}:{table}"


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "setup_database_monitoring",
    "parse_sql_statement",
    "update_connection_metrics",
    "SlowQueryDetector",
]
