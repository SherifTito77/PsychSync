# app/core/enhanced_query_optimizer.py
"""
Enhanced SQL Query Optimizer for PsychSync
Advanced query analysis, optimization, and performance enhancement system
Builds upon existing query optimization infrastructure
"""

import asyncio
import hashlib
import re
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.sql import Select

from app.core.config import settings
from app.core.structured_logging import get_logger

logger = get_logger(__name__)


class QueryPattern(Enum):
    """Common query patterns that can be optimized"""

    USER_LOOKUP = "user_lookup"
    TEAM_ANALYTICS = "team_analytics"
    ASSESSMENT_RESULTS = "assessment_results"
    PERFORMANCE_REPORTS = "performance_reports"
    DATETIME_RANGE = "datetime_range"
    PAGINATED_LISTS = "paginated_lists"
    AGGREGATE_QUERIES = "aggregate_queries"
    N_PLUS_ONE = "n_plus_one"


class OptimizationPriority(Enum):
    """Priority levels for optimization recommendations"""

    CRITICAL = "critical"  # > 1000ms improvement
    HIGH = "high"  # 500-1000ms improvement
    MEDIUM = "medium"  # 100-500ms improvement
    LOW = "low"  # < 100ms improvement


@dataclass
class QueryStatistics:
    """Comprehensive query performance statistics"""

    query_hash: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    median_time_ms: float = 0.0
    rows_examined_total: int = 0
    rows_returned_total: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    last_executed: datetime | None = None
    optimization_applied: list[str] = field(default_factory=list)


@dataclass
class IndexSuggestion:
    """Database index optimization suggestion"""

    table_name: str
    column_names: list[str]
    index_type: str = "btree"
    unique: bool = False
    estimated_impact: str = ""
    creation_sql: str = ""


@dataclass
class OptimizationRecommendation:
    """Detailed optimization recommendation"""

    query_hash: str
    query_type: QueryPattern
    priority: OptimizationPriority
    description: str
    implementation: str
    estimated_improvement_ms: float
    implementation_effort: str  # LOW, MEDIUM, HIGH
    risk_level: str  # LOW, MEDIUM, HIGH
    dependencies: list[str] = field(default_factory=list)
    index_suggestions: list[IndexSuggestion] = field(default_factory=list)


class EnhancedQueryOptimizer:
    """
    Advanced SQL query optimizer with pattern recognition,
    automated optimization, and performance tracking
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.query_stats: dict[str, QueryStatistics] = {}
        self.optimization_cache: dict[str, list[OptimizationRecommendation]] = {}
        self.pattern_recognition_rules = self._initialize_pattern_rules()
        self.index_analysis_cache: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _initialize_pattern_rules(self) -> dict[QueryPattern, dict[str, Any]]:
        """Initialize query pattern recognition rules"""
        return {
            QueryPattern.USER_LOOKUP: {
                "regex": r"(?i)SELECT.*FROM\s+(users?)\s+WHERE\s+(email|id)\s*=",
                "common_columns": ["id", "email", "created_at"],
                "suggested_indexes": [["email"], ["id"]],
                "eager_load": [],
                "optimization_potential": "HIGH",
            },
            QueryPattern.TEAM_ANALYTICS: {
                "regex": r"(?i)SELECT.*FROM\s+(teams?.*team_members?.*users?)",
                "common_columns": ["team_id", "user_id", "role"],
                "suggested_indexes": [["team_id", "user_id"], ["organization_id"]],
                "eager_load": ["members", "organization"],
                "optimization_potential": "HIGH",
            },
            QueryPattern.ASSESSMENT_RESULTS: {
                "regex": r"(?i)SELECT.*FROM\s+(assessment_responses?).*WHERE\s+assessment_id",
                "common_columns": ["assessment_id", "user_id", "created_at"],
                "suggested_indexes": [
                    ["assessment_id", "user_id"],
                    ["user_id", "created_at"],
                ],
                "eager_load": ["user", "assessment"],
                "optimization_potential": "VERY_HIGH",
            },
            QueryPattern.DATETIME_RANGE: {
                "regex": r"(?i)WHERE\s+.*created_at\s*(>=|<=|BETWEEN)",
                "common_columns": ["created_at", "updated_at"],
                "suggested_indexes": [
                    ["created_at"],
                    ["updated_at"],
                    ["created_at", "user_id"],
                ],
                "eager_load": [],
                "optimization_potential": "HIGH",
            },
            QueryPattern.PAGINATED_LISTS: {
                "regex": r"(?i)LIMIT\s+\d+.*OFFSET\s+\d+|FETCH\s+FIRST\s+\d+\s+ROWS\s+ONLY",
                "common_columns": ["id", "created_at"],
                "suggested_indexes": [["id"], ["created_at", "id"]],
                "eager_load": [],
                "optimization_potential": "MEDIUM",
            },
        }

    async def analyze_query_performance(
        self,
        query: str,
        execution_time_ms: float,
        rows_examined: int = 0,
        rows_returned: int = 0,
        from_cache: bool = False,
    ) -> QueryStatistics:
        """Analyze individual query performance and update statistics"""
        query_hash = self._generate_query_hash(query)

        async with self._lock:
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = QueryStatistics(query_hash=query_hash)

            stats = self.query_stats[query_hash]
            stats.execution_count += 1
            stats.total_time_ms += execution_time_ms
            stats.avg_time_ms = stats.total_time_ms / stats.execution_count
            stats.min_time_ms = min(stats.min_time_ms, execution_time_ms)
            stats.max_time_ms = max(stats.max_time_ms, execution_time_ms)
            stats.rows_examined_total += rows_examined
            stats.rows_returned_total += rows_returned
            stats.last_executed = datetime.utcnow()

            if from_cache:
                stats.cache_hits += 1
            else:
                stats.cache_misses += 1

            # Trigger optimization analysis if query is slow
            if execution_time_ms > settings.SLOW_QUERY_THRESHOLD_MS:
                await self._generate_optimization_recommendations(query_hash, query)

        self.logger.info(
            "Query performance analyzed",
            query_hash=query_hash[:8],
            execution_time_ms=execution_time_ms,
            avg_time_ms=stats.avg_time_ms,
            cache_hit=(
                f"{stats.cache_hits / (stats.cache_hits + stats.cache_misses) * 100:.1f}%"
                if stats.cache_hits + stats.cache_misses > 0
                else "0%"
            ),
        )

        return stats

    async def get_query_optimization_recommendations(
        self,
        query_hash: str | None = None,
        min_priority: OptimizationPriority = OptimizationPriority.MEDIUM,
    ) -> list[OptimizationRecommendation]:
        """Get optimization recommendations for queries"""
        if query_hash:
            return self.optimization_cache.get(query_hash, [])

        # Filter by priority
        all_recommendations = []
        for recs in self.optimization_cache.values():
            all_recommendations.extend(recs)

        # Sort by priority and estimated improvement
        priority_order = {
            OptimizationPriority.CRITICAL: 0,
            OptimizationPriority.HIGH: 1,
            OptimizationPriority.MEDIUM: 2,
            OptimizationPriority.LOW: 3,
        }

        return sorted(
            [
                r
                for r in all_recommendations
                if priority_order[r.priority] <= priority_order[min_priority]
            ],
            key=lambda x: (priority_order[x.priority], x.estimated_improvement_ms),
            reverse=True,
        )

    async def generate_index_recommendations(
        self, db: AsyncSession
    ) -> list[IndexSuggestion]:
        """Generate database index recommendations based on query patterns"""
        recommendations = []

        # Analyze current index usage
        current_indexes = await self._get_current_indexes(db)

        for query_hash, stats in self.query_stats.items():
            if stats.avg_time_ms > 100:  # Only analyze slower queries
                pattern = await self._identify_query_pattern(query_hash)
                if pattern and pattern in self.pattern_recognition_rules:
                    pattern_rules = self.pattern_recognition_rules[pattern]

                    for index_cols in pattern_rules["suggested_indexes"]:
                        index_name = f"idx_{'_'.join(index_cols)}"

                        # Check if index already exists
                        if not self._index_exists(index_name, current_indexes):
                            recommendation = IndexSuggestion(
                                table_name=self._extract_table_name(query_hash),
                                column_names=index_cols,
                                index_type="btree",
                                unique=False,
                                estimated_impact=f"Estimated {stats.avg_time_ms * 0.5:.1f}ms reduction",
                                creation_sql=f"CREATE INDEX CONCURRENTLY {index_name} ON {self._extract_table_name(query_hash)} ({', '.join(index_cols)});",
                            )
                            recommendations.append(recommendation)

        return recommendations

    async def optimize_query_execution(
        self, query: Select, db: AsyncSession, query_pattern: QueryPattern | None = None
    ) -> tuple[Any, float]:
        """Execute query with automatic optimizations applied"""
        start_time = time.time()

        # Apply optimizations based on pattern
        if query_pattern:
            query = await self._apply_pattern_optimizations(query, query_pattern)

        # Execute with monitoring
        query_str = str(query.compile(compile_kwargs={"literal_binds": True}))

        try:
            result = await db.execute(query)
            execution_time = (time.time() - start_time) * 1000

            # Record performance
            await self.analyze_query_performance(
                query_str,
                execution_time,
                rows_returned=len(result.all()) if hasattr(result, "all") else 0,
            )

            return result, execution_time

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Query execution failed",
                query_hash=self._generate_query_hash(query_str)[:8],
                execution_time_ms=execution_time,
                error=str(e),
            )
            raise

    @asynccontextmanager
    async def query_execution_context(
        self, db: AsyncSession, query_description: str = ""
    ):
        """Context manager for monitoring query execution"""
        start_time = time.time()
        query_hash = None

        try:
            yield self
        finally:
            execution_time = (time.time() - start_time) * 1000
            if query_hash:
                await self.analyze_query_performance(query_hash, execution_time)

    async def get_performance_report(self, hours: int = 24) -> dict[str, Any]:
        """Generate comprehensive performance report"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        recent_stats = {
            hash_key: stats
            for hash_key, stats in self.query_stats.items()
            if stats.last_executed and stats.last_executed > cutoff_time
        }

        if not recent_stats:
            return {"message": "No recent query data available"}

        total_queries = sum(stats.execution_count for stats in recent_stats.values())
        total_time = sum(stats.total_time_ms for stats in recent_stats.values())
        avg_query_time = total_time / total_queries if total_queries > 0 else 0

        slow_queries = [
            (hash_key, stats)
            for hash_key, stats in recent_stats.items()
            if stats.avg_time_ms > settings.SLOW_QUERY_THRESHOLD_MS
        ]

        cache_performance = {}
        for hash_key, stats in recent_stats.items():
            total_requests = stats.cache_hits + stats.cache_misses
            if total_requests > 0:
                cache_performance[hash_key] = stats.cache_hits / total_requests

        return {
            "period_hours": hours,
            "total_queries": total_queries,
            "total_execution_time_ms": total_time,
            "average_query_time_ms": avg_query_time,
            "slow_query_count": len(slow_queries),
            "slow_queries": [
                {
                    "query_hash": hash_key[:8],
                    "avg_time_ms": stats.avg_time_ms,
                    "execution_count": stats.execution_count,
                }
                for hash_key, stats in sorted(
                    slow_queries, key=lambda x: x[1].avg_time_ms, reverse=True
                )
            ],
            "cache_hit_rate": (
                sum(stats.cache_hits for stats in recent_stats.values())
                / sum(
                    stats.cache_hits + stats.cache_misses
                    for stats in recent_stats.values()
                )
                if sum(
                    stats.cache_hits + stats.cache_misses
                    for stats in recent_stats.values()
                )
                > 0
                else 0
            )
            * 100,
            "top_optimization_opportunities": await self.get_query_optimization_recommendations(
                min_priority=OptimizationPriority.HIGH
            )[
                :5
            ],
        }

    async def _generate_optimization_recommendations(self, query_hash: str, query: str):
        """Generate optimization recommendations for a specific query"""
        if query_hash not in self.optimization_cache:
            pattern = await self._identify_query_pattern(query)
            if not pattern:
                return

            stats = self.query_stats.get(query_hash)
            if not stats or stats.avg_time_ms < 50:  # Don't optimize fast queries
                return

            recommendations = []
            pattern_rules = self.pattern_recognition_rules[pattern]

            # Index recommendations
            for index_cols in pattern_rules["suggested_indexes"]:
                rec = OptimizationRecommendation(
                    query_hash=query_hash,
                    query_type=pattern,
                    priority=self._calculate_priority(stats.avg_time_ms),
                    description=f"Add composite index on {', '.join(index_cols)} for {pattern.value} queries",
                    implementation=f"CREATE INDEX idx_{'_'.join(index_cols)} ON table_name ({', '.join(index_cols)})",
                    estimated_improvement_ms=stats.avg_time_ms * 0.6,
                    implementation_effort="LOW",
                    risk_level="LOW",
                    dependencies=["database_migration"],
                )
                recommendations.append(rec)

            # Query rewrite recommendations
            if "ORDER BY" in query.upper() and "LIMIT" in query.upper():
                rec = OptimizationRecommendation(
                    query_hash=query_hash,
                    query_type=pattern,
                    priority=OptimizationPriority.MEDIUM,
                    description="Optimize ORDER BY with appropriate index for better pagination",
                    implementation="Add index covering ORDER BY columns or use cursor-based pagination",
                    estimated_improvement_ms=stats.avg_time_ms * 0.3,
                    implementation_effort="MEDIUM",
                    risk_level="LOW",
                )
                recommendations.append(rec)

            self.optimization_cache[query_hash] = recommendations

    async def _identify_query_pattern(self, query: str) -> QueryPattern | None:
        """Identify the pattern of a query for optimization"""
        for pattern, rules in self.pattern_recognition_rules.items():
            if re.search(rules["regex"], query):
                return pattern
        return None

    def _generate_query_hash(self, query: str) -> str:
        """Generate consistent hash for query identification"""
        # Normalize query by removing parameter values
        normalized = re.sub(r"\b\d+\b", "?", query)  # Replace numbers
        normalized = re.sub(r"'[^']*'", "?", normalized)  # Replace string literals
        normalized = re.sub(r"\s+", " ", normalized).strip()  # Normalize whitespace

        return hashlib.md5(normalized.encode()).hexdigest()

    def _calculate_priority(self, avg_time_ms: float) -> OptimizationPriority:
        """Calculate optimization priority based on execution time"""
        if avg_time_ms > 1000:
            return OptimizationPriority.CRITICAL
        if avg_time_ms > 500:
            return OptimizationPriority.HIGH
        if avg_time_ms > 100:
            return OptimizationPriority.MEDIUM
        return OptimizationPriority.LOW

    async def _apply_pattern_optimizations(
        self, query: Select, pattern: QueryPattern
    ) -> Select:
        """Apply pattern-specific optimizations to a query"""
        if pattern == QueryPattern.TEAM_ANALYTICS:
            # Add eager loading for team analytics
            query = query.options(selectinload("*"), joinedload("*"))
        elif pattern == QueryPattern.ASSESSMENT_RESULTS:
            # Optimize assessment result queries with proper joins
            query = query.options(selectinload("user"), selectinload("assessment"))

        return query

    async def _get_current_indexes(self, db: AsyncSession) -> dict[str, list[str]]:
        """Get current database indexes"""
        result = await db.execute(
            text(
                """
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
        """
            )
        )

        indexes = {}
        for row in result:
            table_name = row.tablename
            if table_name not in indexes:
                indexes[table_name] = []
            indexes[table_name].append(row.indexname)

        return indexes

    def _index_exists(
        self, index_name: str, current_indexes: dict[str, list[str]]
    ) -> bool:
        """Check if an index already exists"""
        for table_indexes in current_indexes.values():
            if index_name in table_indexes:
                return True
        return False

    def _extract_table_name(self, query_hash: str) -> str:
        """Extract table name from query (simplified)"""
        # In a real implementation, this would parse the SQL query
        # For now, return a placeholder
        return "unknown_table"


# Global optimizer instance
enhanced_query_optimizer = EnhancedQueryOptimizer()
