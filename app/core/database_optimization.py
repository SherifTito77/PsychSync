# app/core/database_optimization.py
"""
Database Query Optimization and Index Management
- Query performance analysis
- Automatic index recommendations
- Connection pool optimization
- Query pattern analysis
- Performance monitoring for database operations
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class QueryMetric:
    """Database query performance metric"""

    query_hash: str
    query_sql: str
    duration_ms: float
    timestamp: datetime
    rows_returned: int
    success: bool
    error: str | None = None


class QueryAnalyzer:
    """Analyzes query performance and recommends optimizations"""

    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.query_history: deque = deque(maxlen=max_history)
        self.slow_queries: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()

    async def analyze_query(
        self,
        query: str,
        duration_ms: float,
        rows_returned: int,
        success: bool = True,
        error: str | None = None,
    ) -> QueryMetric:
        """Analyze a database query and record metrics"""

        # Generate query hash for tracking
        query_hash = self._generate_query_hash(query)

        metric = QueryMetric(
            query_hash=query_hash,
            query_sql=query,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
            rows_returned=rows_returned,
            success=success,
            error=error,
        )

        async with self._lock:
            self.query_history.append(metric)

            # Track slow queries (over 100ms)
            if duration_ms > 100:
                self.slow_queries.append(metric)

        return metric

    def _generate_query_hash(self, query: str) -> str:
        """Generate a normalized hash for query comparison"""
        import hashlib

        normalized = " ".join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    async def get_slow_queries_summary(self, hours: int = 1) -> dict[str, Any]:
        """Get summary of slow queries"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        slow_queries = [q for q in self.slow_queries if q.timestamp >= cutoff_time]

        if not slow_queries:
            return {"total": 0, "queries": []}

        # Group by query hash
        query_groups = defaultdict(list)
        for query in slow_queries:
            query_groups[query.query_hash].append(query)

        # Analyze each unique query
        analyzed_queries = []
        for query_hash, queries in query_groups.items():
            avg_duration = sum(q.duration_ms for q in queries) / len(queries)
            max_duration = max(q.duration_ms for q in queries)
            total_executions = len(queries)
            error_rate = sum(1 for q in queries if not q.success) / total_executions

            analyzed_queries.append(
                {
                    "query_hash": query_hash,
                    "query_sql": queries[0].query_sql[:200] + "..."
                    if len(queries[0].query_sql) > 200
                    else queries[0].query_sql,
                    "avg_duration_ms": round(avg_duration, 2),
                    "max_duration_ms": round(max_duration, 2),
                    "total_executions": total_executions,
                    "error_rate": round(error_rate, 4),
                    "last_seen": queries[-1].timestamp.isoformat(),
                }
            )

        # Sort by average duration
        analyzed_queries.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

        return {
            "total": len(analyzed_queries),
            "time_range_hours": hours,
            "queries": analyzed_queries[:20],  # Top 20 slowest queries
        }


class DatabaseOptimizer:
    """Database optimization utilities"""

    def __init__(self, query_analyzer: QueryAnalyzer = None):
        self.query_analyzer = query_analyzer or QueryAnalyzer()

    async def analyze_table_indexes(self, db: AsyncSession, table_name: str) -> dict[str, Any]:
        """Analyze existing indexes on a table"""

        # Get current indexes
        indexes_query = text("""
            SELECT
                indexname as index_name,
                indexdef as index_definition,
                schemaname as schema_name,
                tablename as table_name
            FROM pg_indexes
            WHERE tablename = :table_name
            ORDER BY indexname
        """)

        result = await db.execute(indexes_query, {"table_name": table_name})
        indexes = result.fetchall()

        # Get index usage statistics
        usage_query = text("""
            SELECT
                schemaname,
                tablename,
                indexrelname as index_name,
                idx_tup_read as tuples_read,
                idx_tup_fetch as tuples_fetched,
                idx_scan as index_scans
            FROM pg_stat_user_indexes
            WHERE tablename = :table_name
            ORDER BY idx_scan DESC
        """)

        usage_result = await db.execute(usage_query, {"table_name": table_name})
        usage_stats = usage_result.fetchall()

        return {
            "table_name": table_name,
            "total_indexes": len(indexes),
            "indexes": [
                {
                    "name": idx.index_name,
                    "definition": idx.index_definition,
                    "schema": idx.schema_name,
                }
                for idx in indexes
            ],
            "usage_stats": [
                {
                    "name": usage.index_name,
                    "scans": usage.index_scans,
                    "tuples_read": usage.tuples_read,
                    "tuples_fetched": usage.tuples_fetched,
                }
                for usage in usage_stats
            ],
        }

    async def get_table_statistics(self, db: AsyncSession, table_name: str) -> dict[str, Any]:
        """Get comprehensive table statistics"""

        try:
            # Row count
            count_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
            count_result = await db.execute(count_query)
            row_count = count_result.scalar() or 0

            # Table size
            size_query = text(f"""
                SELECT
                    pg_size_pretty(pg_total_relation_size('{table_name}')) as total_size,
                    pg_size_pretty(pg_relation_size('{table_name}')) as table_size,
                    pg_size_pretty(pg_total_relation_size('{table_name}') - pg_relation_size('{table_name}')) as indexes_size
            """)
            size_result = await db.execute(size_query)
            size_row = size_result.fetchone()

            return {
                "table_name": table_name,
                "row_count": row_count,
                "sizes": dict(size_row._mapping) if size_row else {},
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "table_name": table_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global optimizer instance
_db_optimizer: DatabaseOptimizer | None = None


def get_db_optimizer() -> DatabaseOptimizer:
    """Get global database optimizer instance"""
    global _db_optimizer
    if _db_optimizer is None:
        _db_optimizer = DatabaseOptimizer()
    return _db_optimizer


# Decorator for query performance monitoring
def monitor_query_performance(min_duration_ms: float = 100):
    """Decorator to monitor query performance"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                # Find database session in arguments
                db = None
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                        break

                result = await func(*args, **kwargs)

                duration_ms = (time.time() - start_time) * 1000

                # Record metric if slow
                if duration_ms > min_duration_ms:
                    optimizer = get_db_optimizer()
                    await optimizer.query_analyzer.analyze_query(
                        query=str(func.__name__),
                        duration_ms=duration_ms,
                        rows_returned=len(result) if isinstance(result, list) else 1,
                        success=True,
                    )

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000

                # Record failed query
                optimizer = get_db_optimizer()
                await optimizer.query_analyzer.analyze_query(
                    query=str(func.__name__),
                    duration_ms=duration_ms,
                    rows_returned=0,
                    success=False,
                    error=str(e),
                )

                raise

        return wrapper

    return decorator
