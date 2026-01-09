# app/performance/database_optimizer.py

"""
DATABASE PERFORMANCE OPTIMIZER
Enterprise-grade database query optimization and monitoring

DATABASE OPTIMIZATION FEATURES:
- Query execution plan analysis
- Index recommendation system
- Connection pool optimization
- Query caching strategies
- Performance metrics collection
- Automatic optimization suggestions

Author: Security Team
Version: 2.0 Enterprise Security
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.sql import ClauseElement

# Initialize performance logger
perf_logger = logging.getLogger("app.performance.database")


@dataclass
class QueryMetrics:
    """Metrics for database query performance"""

    query: str
    execution_time: float
    rows_affected: int
    index_used: str | None = None
    table_name: str | None = None
    timestamp: float = 0.0


@dataclass
class IndexRecommendation:
    """Database index recommendation"""

    table_name: str
    column_names: list[str]
    index_type: str
    estimated_improvement: float
    reason: str


class DatabaseOptimizer:
    """
    Enterprise database performance optimizer with analysis and optimization capabilities
    """

    def __init__(self, db_session_maker: async_sessionmaker):
        self.db_session_maker = db_session_maker
        self.query_history: list[QueryMetrics] = []
        self.max_history_size = 1000
        self.slow_query_threshold = 1.0  # seconds
        self._index_cache: dict[str, list[dict]] = {}

    @asynccontextmanager
    async def monitored_query(self, query: ClauseElement):
        """
        Context manager for monitoring query performance

        Usage:
            async with optimizer.monitored_query(select(User)) as result:
                data = await result.fetchall()
        """
        start_time = time.time()
        rows_affected = 0

        async with self.db_session_maker() as session:
            try:
                # Start timer
                start_time = time.time()

                # Execute query
                result = await session.execute(query)
                rows_affected = result.rowcount

                # Calculate execution time
                execution_time = time.time() - start_time

                # Record metrics
                await self._record_query_metrics(str(query), execution_time, rows_affected)

                yield result

            except Exception as e:
                perf_logger.error(f"Query execution error: {e}")
                raise

    async def _record_query_metrics(self, query: str, execution_time: float, rows_affected: int):
        """Record query performance metrics"""
        try:
            # Extract table name from query (simplified)
            table_name = self._extract_table_name(query)

            metrics = QueryMetrics(
                query=query[:200],  # Limit query length for storage
                execution_time=execution_time,
                rows_affected=rows_affected,
                table_name=table_name,
                timestamp=time.time(),
            )

            # Add to history
            self.query_history.append(metrics)

            # Maintain history size
            if len(self.query_history) > self.max_history_size:
                self.query_history = self.query_history[-self.max_history_size :]

            # Log slow queries
            if execution_time > self.slow_query_threshold:
                perf_logger.warning(
                    f"Slow query detected: {execution_time:.3f}s - {table_name} - {query[:100]}..."
                )

        except Exception as e:
            perf_logger.error(f"Failed to record query metrics: {e}")

    def _extract_table_name(self, query: str) -> str | None:
        """Extract table name from SQL query (simplified)"""
        try:
            import re

            # Look for FROM clause
            from_match = re.search(r"\bFROM\s+(\w+)", query.upper())
            if from_match:
                return from_match.group(1).lower()

            # Look for INSERT INTO
            insert_match = re.search(r"\bINSERT\s+INTO\s+(\w+)", query.upper())
            if insert_match:
                return insert_match.group(1).lower()

            # Look for UPDATE
            update_match = re.search(r"\bUPDATE\s+(\w+)", query.upper())
            if update_match:
                return update_match.group(1).lower()

            return None

        except Exception:
            return None

    async def analyze_query_performance(self, query: str) -> dict[str, Any]:
        """Analyze query execution plan and performance"""
        try:
            async with self.db_session_maker() as session:
                # Get execution plan
                explain_query = f"EXPLAIN ANALYZE {query}"
                result = await session.execute(text(explain_query))
                execution_plan = result.fetchall()

                # Analyze the plan
                analysis = self._analyze_execution_plan(execution_plan)

                return {
                    "query": query,
                    "execution_plan": [str(row[0]) for row in execution_plan],
                    "analysis": analysis,
                    "recommendations": await self._generate_query_recommendations(query, analysis),
                }

        except Exception as e:
            perf_logger.error(f"Query performance analysis failed: {e}")
            return {"error": str(e)}

    def _analyze_execution_plan(self, execution_plan: list) -> dict[str, Any]:
        """Analyze SQL execution plan"""
        try:
            plan_text = "\n".join(str(row[0]) for row in execution_plan)

            analysis = {
                "uses_index": "Index Scan" in plan_text or "Index Only Scan" in plan_text,
                "full_table_scan": "Seq Scan" in plan_text,
                "nested_loops": "Nested Loop" in plan_text,
                "hash_operations": "Hash" in plan_text,
                "sort_operations": "Sort" in plan_text,
                "estimated_cost": self._extract_cost(plan_text),
                "planning_time": self._extract_planning_time(plan_text),
                "execution_time": self._extract_execution_time(plan_text),
            }

            return analysis

        except Exception as e:
            perf_logger.error(f"Execution plan analysis failed: {e}")
            return {"error": str(e)}

    def _extract_cost(self, plan_text: str) -> float | None:
        """Extract cost from execution plan"""
        try:
            import re

            cost_match = re.search(r"cost=(\d+\.\d+)\.\.(\d+\.\d+)", plan_text)
            if cost_match:
                return float(cost_match.group(2))  # Return total cost
            return None
        except Exception:
            return None

    def _extract_planning_time(self, plan_text: str) -> float | None:
        """Extract planning time from execution plan"""
        try:
            import re

            planning_match = re.search(r"planning time: (\d+\.\d+) ms", plan_text.lower())
            if planning_match:
                return float(planning_match.group(1))
            return None
        except Exception:
            return None

    def _extract_execution_time(self, plan_text: str) -> float | None:
        """Extract execution time from execution plan"""
        try:
            import re

            execution_match = re.search(r"execution time: (\d+\.\d+) ms", plan_text.lower())
            if execution_match:
                return float(execution_match.group(1))
            return None
        except Exception:
            return None

    async def _generate_query_recommendations(
        self, query: str, analysis: dict[str, Any]
    ) -> list[str]:
        """Generate optimization recommendations for a query"""
        recommendations = []

        try:
            if not analysis.get("uses_index") and analysis.get("full_table_scan"):
                recommendations.append("Consider adding indexes for columns used in WHERE clauses")

            if analysis.get("nested_loops"):
                recommendations.append("Consider rewriting joins to avoid nested loops")

            if analysis.get("sort_operations"):
                recommendations.append("Consider adding indexes to support ORDER BY clauses")

            if analysis.get("estimated_cost", 0) > 1000:
                recommendations.append("Query has high estimated cost - consider optimization")

            # Add general recommendations based on query patterns
            if "SELECT *" in query.upper():
                recommendations.append("Avoid SELECT * - specify only needed columns")

            if query.count("JOIN") > 3:
                recommendations.append("Consider breaking complex joins into multiple queries")

            return recommendations

        except Exception as e:
            perf_logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to error"]

    async def get_index_recommendations(self) -> list[IndexRecommendation]:
        """Generate index recommendations based on query history"""
        recommendations = []

        try:
            # Analyze slow queries
            slow_queries = [
                q for q in self.query_history if q.execution_time > self.slow_query_threshold
            ]

            # Group queries by table
            table_queries = {}
            for query in slow_queries:
                if query.table_name:
                    if query.table_name not in table_queries:
                        table_queries[query.table_name] = []
                    table_queries[query.table_name].append(query)

            # Generate recommendations for each table
            for table_name, queries in table_queries.items():
                # Get existing indexes
                existing_indexes = await self._get_table_indexes(table_name)

                # Analyze WHERE clauses
                where_columns = self._analyze_where_columns(queries)

                for column in where_columns:
                    if not self._has_index(existing_indexes, column):
                        recommendation = IndexRecommendation(
                            table_name=table_name,
                            column_names=[column],
                            index_type="btree",
                            estimated_improvement=self._estimate_improvement(queries, column),
                            reason=f"Frequent WHERE clause usage in {len(queries)} slow queries",
                        )
                        recommendations.append(recommendation)

            return recommendations

        except Exception as e:
            perf_logger.error(f"Failed to generate index recommendations: {e}")
            return []

    async def _get_table_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Get existing indexes for a table"""
        try:
            if table_name in self._index_cache:
                return self._index_cache[table_name]

            async with self.db_session_maker() as session:
                result = await session.execute(
                    text(f"""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = '{table_name}'
                """)
                )

                indexes = [{"name": row[0], "definition": row[1]} for row in result.fetchall()]
                self._index_cache[table_name] = indexes

                return indexes

        except Exception as e:
            perf_logger.error(f"Failed to get indexes for {table_name}: {e}")
            return []

    def _analyze_where_columns(self, queries: list[QueryMetrics]) -> list[str]:
        """Analyze WHERE clauses to identify frequently used columns"""
        try:
            import re

            column_counts = {}

            for query in queries:
                # Find WHERE clause patterns
                where_matches = re.findall(r"WHERE\s+([\w\s=><!]+)", query.query, re.IGNORECASE)

                for match in where_matches:
                    # Extract column names (simplified)
                    columns = re.findall(r"(\w+)\s*[=><!]", match)
                    for column in columns:
                        if column.lower() not in ["and", "or", "not"]:
                            column_counts[column.lower()] = column_counts.get(column.lower(), 0) + 1

            # Return columns used in multiple queries
            return [col for col, count in column_counts.items() if count > 1]

        except Exception as e:
            perf_logger.error(f"Failed to analyze WHERE clauses: {e}")
            return []

    def _has_index(self, indexes: list[dict[str, Any]], column: str) -> bool:
        """Check if a column already has an index"""
        try:
            for index in indexes:
                if column.lower() in index["definition"].lower():
                    return True
            return False
        except Exception:
            return False

    def _estimate_improvement(self, queries: list[QueryMetrics], column: str) -> float:
        """Estimate performance improvement from adding an index"""
        try:
            # Simple heuristic based on average execution time
            if not queries:
                return 0.0

            avg_time = sum(q.execution_time for q in queries) / len(queries)

            # Estimate 50-80% improvement for properly indexed queries
            estimated_improvement = avg_time * 0.65  # 65% average improvement

            return round(estimated_improvement, 3)

        except Exception:
            return 0.0

    async def get_performance_summary(self) -> dict[str, Any]:
        """Get overall database performance summary"""
        try:
            if not self.query_history:
                return {"message": "No query history available"}

            # Calculate statistics
            total_queries = len(self.query_history)
            total_time = sum(q.execution_time for q in self.query_history)
            avg_time = total_time / total_queries if total_queries > 0 else 0

            slow_queries = [
                q for q in self.query_history if q.execution_time > self.slow_query_threshold
            ]

            # Group by table
            table_stats = {}
            for query in self.query_history:
                if query.table_name:
                    if query.table_name not in table_stats:
                        table_stats[query.table_name] = {
                            "count": 0,
                            "total_time": 0,
                            "avg_time": 0,
                            "slow_queries": 0,
                        }

                    stats = table_stats[query.table_name]
                    stats["count"] += 1
                    stats["total_time"] += query.execution_time
                    stats["avg_time"] = stats["total_time"] / stats["count"]

                    if query.execution_time > self.slow_query_threshold:
                        stats["slow_queries"] += 1

            return {
                "total_queries": total_queries,
                "total_execution_time": round(total_time, 3),
                "average_execution_time": round(avg_time, 3),
                "slow_queries": len(slow_queries),
                "slow_query_percentage": round((len(slow_queries) / total_queries) * 100, 2),
                "slow_query_threshold": self.slow_query_threshold,
                "table_statistics": table_stats,
                "index_recommendations": await self.get_index_recommendations(),
            }

        except Exception as e:
            perf_logger.error(f"Failed to generate performance summary: {e}")
            return {"error": str(e)}

    async def optimize_table(self, table_name: str) -> dict[str, Any]:
        """Optimize a specific table"""
        try:
            async with self.db_session_maker() as session:
                # Get table statistics
                await session.execute(text(f"ANALYZE {table_name}"))

                # Get row count
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()

                # Get table size
                result = await session.execute(
                    text(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
                """)
                )
                table_size = result.scalar()

                # Check for fragmentation (simplified)
                result = await session.execute(
                    text(f"""
                    SELECT schemaname, tablename, attname, n_distinct, correlation
                    FROM pg_stats
                    WHERE tablename = '{table_name}'
                """)
                )
                stats = result.fetchall()

                return {
                    "table_name": table_name,
                    "row_count": row_count,
                    "table_size": table_size,
                    "column_statistics": [
                        {"column": row[2], "distinct_values": row[3], "correlation": row[4]}
                        for row in stats
                    ],
                    "optimization_actions": [
                        "ANALYZE completed",
                        "Statistics updated",
                        "Consider VACUUM if high fragmentation detected",
                    ],
                }

        except Exception as e:
            perf_logger.error(f"Failed to optimize table {table_name}: {e}")
            return {"error": str(e)}

    async def clear_cache(self):
        """Clear internal caches"""
        self._index_cache.clear()
        perf_logger.info("Database optimizer cache cleared")

    def set_slow_query_threshold(self, threshold_seconds: float):
        """Update slow query threshold"""
        self.slow_query_threshold = threshold_seconds
        perf_logger.info(f"Slow query threshold set to {threshold_seconds} seconds")


# Global optimizer instance
_database_optimizer: DatabaseOptimizer | None = None


def get_database_optimizer() -> DatabaseOptimizer | None:
    """Get the global database optimizer instance"""
    return _database_optimizer


def initialize_database_optimizer(db_session_maker: async_sessionmaker) -> DatabaseOptimizer:
    """Initialize the global database optimizer"""
    global _database_optimizer
    _database_optimizer = DatabaseOptimizer(db_session_maker)
    perf_logger.info("Database optimizer initialized")
    return _database_optimizer
