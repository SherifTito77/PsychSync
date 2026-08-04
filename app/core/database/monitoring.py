"""
PsychSync Enterprise Database - Monitoring
SQLAlchemy event listeners for performance tracking and Prometheus integration.
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
)

logger = logging.getLogger("app.database.monitoring")


def setup_database_monitoring(engine: Engine, slow_query_threshold: float = 1.0):
    """Set up database query monitoring via SQLAlchemy event listeners"""

    @event.listens_for(engine, "before_cursor_execute", named=True)
    def receive_before_cursor_execute(
        conn: PoolProxiedConnection,
        cursor,
        statement: str,
        parameters: dict[str, Any] | list[tuple] | None,
        context: dict[str, Any],
        executemany: bool,
    ) -> None:
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
        if not hasattr(context, "_query_start_time"):
            return

        duration = time.time() - context._query_start_time
        operation, table = parse_sql_statement(statement)
        is_slow = duration > slow_query_threshold

        if is_slow:
            logger.warning(
                f"Slow query detected: {operation} on {table} took {duration:.3f}s",
                extra={"operation": operation, "table": table, "duration": duration},
            )

        track_db_query(
            operation=operation, table=table, duration=duration, is_slow=is_slow
        )

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record) -> None:
        update_connection_metrics(engine.pool)

    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record) -> None:
        update_connection_metrics(engine.pool)

    logger.info(
        f"✅ Database monitoring initialized (threshold: {slow_query_threshold}s)"
    )


def parse_sql_statement(statement: str) -> tuple[str, str]:
    """Extract operation and table from SQL statement"""
    parts = statement.strip().split()
    if not parts:
        return "UNKNOWN", "UNKNOWN"
    operation = parts[0].upper()
    table = "UNKNOWN"
    if operation in ("SELECT", "INSERT", "UPDATE", "DELETE"):
        for keyword in ("FROM", "INTO", "UPDATE", "IN"):
            if keyword in statement.upper():
                idx = statement.upper().find(keyword)
                table_parts = statement[idx + len(keyword) :].strip().split()
                if table_parts:
                    table = table_parts[0].strip('"`[]')
                    break
    return operation, table


def update_connection_metrics(pool: Pool) -> None:
    """Update connection pool metrics for Prometheus"""
    try:
        update_db_connections(
            database=(
                pool.dispatch.db_api.driver
                if hasattr(pool.dispatch.db_api, "driver")
                else "postgresql"
            ),
            active=pool.checkedout(),
            idle=pool.size() - pool.checkedout(),
        )
    except Exception as e:
        logger.error(f"Failed to update connection metrics: {e}")
