# app/core/database_index_optimizer.py
"""
Advanced Database Index Optimization System for PsychSync
Intelligent index management, analysis, and automated optimization
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.query_optimizer import QueryMetrics
from app.core.structured_logging import EventType, get_logger

logger = get_logger(__name__)


class IndexType(Enum):
    """Types of database indexes"""

    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    PARTIAL = "partial"
    EXPRESSION = "expression"
    COMPOSITE = "composite"


class IndexPriority(Enum):
    """Priority levels for index creation"""

    CRITICAL = "critical"  # Immediate impact on performance
    HIGH = "high"  # Significant improvement
    MEDIUM = "medium"  # Moderate improvement
    LOW = "low"  # Minor improvement


@dataclass
class IndexMetrics:
    """Metrics for a specific database index"""

    index_name: str
    table_name: str
    column_names: list[str]
    index_type: IndexType
    size_mb: float
    usage_count: int = 0
    last_used: datetime | None = None
    scan_count: int = 0
    tuples_read: int = 0
    tuples_returned: int = 0
    creation_time: datetime | None = None
    is_partial: bool = False
    is_unique: bool = False


@dataclass
class IndexRecommendation:
    """Intelligent index recommendation based on query analysis"""

    table_name: str
    column_names: list[str]
    index_type: IndexType
    priority: IndexPriority
    estimated_improvement_ms: float
    estimated_impact_queries: int
    creation_sql: str
    removal_sql: str | None = None
    rationale: str = ""
    dependencies: list[str] = field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    implementation_cost: str = "LOW"  # LOW, MEDIUM, HIGH


@dataclass
class IndexAnalysisReport:
    """Comprehensive index analysis report"""

    total_indexes: int
    unused_indexes: list[IndexMetrics]
    underutilized_indexes: list[IndexMetrics]
    missing_indexes: list[IndexRecommendation]
    oversized_indexes: list[IndexMetrics]
    duplicate_indexes: list[IndexMetrics]
    index_efficiency_score: float
    potential_improvement_ms: float
    recommendations: list[str]


class DatabaseIndexOptimizer:
    """
    Advanced database index optimization system
    Analyzes query patterns, monitors index usage, and provides intelligent recommendations
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.index_cache: dict[str, IndexMetrics] = {}
        self.query_index_mapping: dict[str, list[str]] = {}
        self.analysis_cache: dict[str, Any] = {}
        self.last_analysis_time: datetime | None = None

    async def analyze_current_indexes(self, db: AsyncSession) -> list[IndexMetrics]:
        """
        Analyze current database indexes and their usage statistics
        """
        try:
            # Get current index information
            index_query = text(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef,
                    pg_size_pretty(pg_relation_size(indexname::regclass)) as size,
                    pg_relation_size(indexname::regclass) as size_bytes
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """
            )

            result = await db.execute(index_query)
            indexes = []

            for row in result:
                # Parse index definition to extract columns and type
                columns, index_type = self._parse_index_definition(row.indexdef)

                index_metrics = IndexMetrics(
                    index_name=row.indexname,
                    table_name=row.tablename,
                    column_names=columns,
                    index_type=index_type,
                    size_mb=row.size_bytes / (1024 * 1024),
                    is_partial="WHERE" in row.indexdef.upper(),
                    is_unique="UNIQUE" in row.indexdef.upper(),
                )

                indexes.append(index_metrics)
                self.index_cache[row.indexname] = index_metrics

            # Get usage statistics
            await self._update_index_usage_stats(db, indexes)

            logger.info(
                EventType.DATABASE_OPERATION,
                f"Analyzed {len(indexes)} database indexes",
                operation_name="index_analysis",
                index_count=len(indexes),
            )

            return indexes

        except Exception as e:
            self.logger.log_error(e, operation="analyze_current_indexes")
            raise

    async def _update_index_usage_stats(
        self, db: AsyncSession, indexes: list[IndexMetrics]
    ):
        """Update index usage statistics from PostgreSQL"""
        try:
            usage_query = text(
                """
                SELECT
                    schemaname,
                    tablename,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_stat_get_last_vacuum_time(indexrelid) as last_vacuum
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
            """
            )

            result = await db.execute(usage_query)

            for row in result:
                index_name = row.indexrelname
                if index_name in self.index_cache:
                    index_metrics = self.index_cache[index_name]
                    index_metrics.usage_count = row.idx_scan or 0
                    index_metrics.scan_count = row.idx_scan or 0
                    index_metrics.tuples_read = row.idx_tup_read or 0
                    index_metrics.tuples_returned = row.idx_tup_fetch or 0

        except Exception as e:
            # Usage stats might not be available in all PostgreSQL versions
            logger.warning(f"Could not fetch index usage stats: {e}")

    def _parse_index_definition(self, index_def: str) -> tuple[list[str], IndexType]:
        """Parse index definition to extract columns and type"""
        # Extract columns between parentheses
        columns_match = re.search(r"\(([^)]+)\)", index_def)
        if not columns_match:
            return [], IndexType.BTREE

        columns_str = columns_match.group(1)

        # Clean up column names
        columns = []
        for col in columns_str.split(","):
            col = col.strip()
            # Remove quotes if present
            if col.startswith('"') and col.endswith('"'):
                col = col[1:-1]
            # Handle expressions (simplified)
            if "(" in col or ")" in col:
                return [col], IndexType.EXPRESSION
            columns.append(col)

        # Determine index type
        index_def_upper = index_def.upper()
        if "USING HASH" in index_def_upper:
            index_type = IndexType.HASH
        elif "USING GIN" in index_def_upper:
            index_type = IndexType.GIN
        elif "USING GIST" in index_def_upper:
            index_type = IndexType.GIST
        elif "USING BRIN" in index_def_upper:
            index_type = IndexType.BRIN
        elif "WHERE" in index_def_upper:
            index_type = IndexType.PARTIAL
        elif len(columns) > 1:
            index_type = IndexType.COMPOSITE
        else:
            index_type = IndexType.BTREE

        return columns, index_type

    async def generate_index_recommendations(
        self,
        db: AsyncSession,
        query_history: list[QueryMetrics],
        min_priority: IndexPriority = IndexPriority.MEDIUM,
    ) -> list[IndexRecommendation]:
        """
        Generate intelligent index recommendations based on query analysis
        """
        recommendations = []

        # Analyze query patterns for missing indexes
        query_patterns = self._analyze_query_patterns(query_history)

        for pattern, queries in query_patterns.items():
            if len(queries) < 3:  # Only consider patterns with multiple queries
                continue

            recommendation = await self._create_index_recommendation(pattern, queries)
            if recommendation and self._meets_priority_threshold(
                recommendation, min_priority
            ):
                recommendations.append(recommendation)

        # Sort by estimated impact
        recommendations.sort(
            key=lambda x: x.estimated_improvement_ms * x.estimated_impact_queries,
            reverse=True,
        )

        return recommendations

    def _analyze_query_patterns(
        self, query_history: list[QueryMetrics]
    ) -> dict[str, list[QueryMetrics]]:
        """Group queries by patterns for analysis"""
        patterns = {}

        for metrics in query_history:
            # Skip fast queries
            if metrics.execution_time_ms < 50:
                continue

            # Create normalized pattern
            pattern = self._create_query_pattern(metrics.query_text)

            if pattern not in patterns:
                patterns[pattern] = []
            patterns[pattern].append(metrics)

        return patterns

    def _create_query_pattern(self, query: str) -> str:
        """Create a normalized pattern for query grouping"""
        # Convert to lowercase and normalize
        pattern = query.lower().strip()

        # Remove specific values
        pattern = re.sub(r"\b\d+\b", "N", pattern)  # Numbers
        pattern = re.sub(r":\w+", ":param", pattern)  # Named parameters
        pattern = re.sub(r"'[^']*'", "'VALUE'", pattern)  # String literals
        pattern = re.sub(r"\s+", " ", pattern)  # Normalize whitespace

        return pattern

    async def _create_index_recommendation(
        self, pattern: str, queries: list[QueryMetrics]
    ) -> IndexRecommendation | None:
        """Create index recommendation for a query pattern"""
        # Extract table and column information
        table_columns = self._extract_table_columns_from_pattern(pattern)

        if not table_columns:
            return None

        # Calculate impact metrics
        total_execution_time = sum(q.execution_time_ms for q in queries)
        estimated_improvement = total_execution_time * 0.6  # 60% improvement estimate

        # Determine best index configuration
        best_config = self._determine_optimal_index_config(pattern, table_columns)

        if not best_config:
            return None

        # Generate recommendation
        recommendation = IndexRecommendation(
            table_name=best_config["table"],
            column_names=best_config["columns"],
            index_type=best_config["type"],
            priority=self._calculate_recommendation_priority(
                estimated_improvement, len(queries)
            ),
            estimated_improvement_ms=estimated_improvement,
            estimated_impact_queries=len(queries),
            creation_sql=self._generate_index_creation_sql(best_config),
            rationale=best_config["rationale"],
            risk_level=best_config["risk_level"],
            implementation_cost=best_config["cost"],
        )

        return recommendation

    def _extract_table_columns_from_pattern(
        self, pattern: str
    ) -> list[tuple[str, list[str]]]:
        """Extract table and column information from query pattern"""
        table_columns = []

        # Simple regex patterns for common query structures
        # FROM clause
        from_match = re.search(r"from\s+(\w+)", pattern)
        if from_match:
            table = from_match.group(1)
            columns = self._extract_where_columns(pattern, table)
            if columns:
                table_columns.append((table, columns))

        # JOIN clauses
        join_matches = re.findall(r"join\s+(\w+)", pattern)
        for table in join_matches:
            columns = self._extract_where_columns(pattern, table)
            if columns:
                table_columns.append((table, columns))

        return table_columns

    def _extract_where_columns(self, pattern: str, table: str) -> list[str]:
        """Extract columns used in WHERE clauses for a specific table"""
        columns = []

        # WHERE conditions
        where_patterns = [
            rf"where\s+{table}\.(\w+)\s*=",
            rf"where\s+{table}\.(\w+)\s+>",
            rf"where\s+{table}\.(\w+)\s+<",
            rf"where\s+{table}\.(\w+)\s+between",
            rf"where\s+{table}\.(\w+)\s+in",
            rf"where\s+{table}\.(\w+)\s+like",
            rf"join.*on\s+{table}\.(\w+)\s*=",
        ]

        for pattern_regex in where_patterns:
            matches = re.findall(pattern_regex, pattern)
            columns.extend(matches)

        return list(set(columns))  # Remove duplicates

    def _determine_optimal_index_config(
        self, pattern: str, table_columns: list[tuple[str, list[str]]]
    ) -> dict[str, Any] | None:
        """Determine optimal index configuration based on usage pattern"""
        if not table_columns:
            return None

        # Simple heuristic: use first table with most columns
        table, columns = max(table_columns, key=lambda x: len(x[1]))

        if not columns:
            return None

        # Determine index type based on query characteristics
        pattern_lower = pattern.lower()
        index_type = IndexType.BTREE
        risk_level = "LOW"
        cost = "LOW"
        rationale = ""

        if any(keyword in pattern_lower for keyword in ["like", "ilike"]):
            index_type = IndexType.BTREE
            rationale = "Pattern matching queries benefit from B-tree indexes"

        elif "order by" in pattern_lower and "created_at" in pattern_lower:
            index_type = IndexType.BTREE
            columns.append("created_at")  # Include ordering column
            rationale = "Index includes ORDER BY column to eliminate sorting"
            cost = "MEDIUM"

        elif "count(" in pattern_lower:
            index_type = IndexType.BTREE
            rationale = "Index supports COUNT operations with better scanning"
            risk_level = "MEDIUM"

        elif len(columns) == 1:
            # Single column index
            pass  # Default B-tree is fine
        else:
            # Multiple columns - composite index
            index_type = IndexType.COMPOSITE
            rationale = f"Composite index on {', '.join(columns)} covers multiple query conditions"
            cost = "MEDIUM"

        # Limit index columns to reasonable number
        if len(columns) > 5:
            columns = columns[:5]
            rationale += " (truncated for performance)"

        return {
            "table": table,
            "columns": columns,
            "type": index_type,
            "rationale": rationale,
            "risk_level": risk_level,
            "cost": cost,
        }

    def _calculate_recommendation_priority(
        self, improvement_ms: float, query_count: int
    ) -> IndexPriority:
        """Calculate priority for index recommendation"""
        total_impact = improvement_ms * query_count

        if total_impact > 10000:  # > 10 seconds total improvement
            return IndexPriority.CRITICAL
        if total_impact > 5000:  # > 5 seconds total improvement
            return IndexPriority.HIGH
        if total_impact > 1000:  # > 1 second total improvement
            return IndexPriority.MEDIUM
        return IndexPriority.LOW

    def _generate_index_creation_sql(self, config: dict[str, Any]) -> str:
        """Generate SQL for index creation"""
        table = config["table"]
        columns = config["columns"]
        index_type = config["type"]

        index_name = f"idx_{table}_{'_'.join(columns)}"
        # Truncate if too long (PostgreSQL limit is 63 characters)
        if len(index_name) > 60:
            index_name = f"idx_{table}_composite"

        columns_str = ", ".join(columns)

        if index_type == IndexType.HASH:
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table} USING HASH ({columns_str});"
        if index_type == IndexType.GIN:
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table} USING GIN ({columns_str});"
        if index_type == IndexType.BRIN:
            return f"CREATE INDEX CONCURRENTLY {index_name} ON {table} USING BRIN ({columns_str});"
        # BTREE or COMPOSITE
        return f"CREATE INDEX CONCURRENTLY {index_name} ON {table} ({columns_str});"

    def _meets_priority_threshold(
        self, recommendation: IndexRecommendation, min_priority: IndexPriority
    ) -> bool:
        """Check if recommendation meets minimum priority threshold"""
        priority_order = {
            IndexPriority.CRITICAL: 0,
            IndexPriority.HIGH: 1,
            IndexPriority.MEDIUM: 2,
            IndexPriority.LOW: 3,
        }

        return priority_order[recommendation.priority] <= priority_order[min_priority]

    async def identify_unused_indexes(
        self, db: AsyncSession, days_unused: int = 30
    ) -> list[IndexMetrics]:
        """Identify indexes that haven't been used recently"""
        if not self.index_cache:
            await self.analyze_current_indexes(db)

        cutoff_time = datetime.utcnow() - timedelta(days=days_unused)
        unused_indexes = []

        for index_metrics in self.index_cache.values():
            # Skip primary key and essential indexes
            if self._is_essential_index(index_metrics):
                continue

            # Check if index has never been used or not used recently
            if index_metrics.usage_count == 0 or (
                index_metrics.last_used and index_metrics.last_used < cutoff_time
            ):
                unused_indexes.append(index_metrics)

        return unused_indexes

    def _is_essential_index(self, index_metrics: IndexMetrics) -> bool:
        """Determine if an index is essential and should not be dropped"""
        # Primary key indexes
        if index_metrics.index_name.endswith("_pkey"):
            return True

        # Foreign key indexes
        if index_metrics.index_name.startswith("fki_"):
            return True

        # Unique constraints
        if index_metrics.index_name.startswith("uq_"):
            return True

        return False

    async def generate_index_analysis_report(
        self, db: AsyncSession, query_history: list[QueryMetrics]
    ) -> IndexAnalysisReport:
        """Generate comprehensive index analysis report"""
        # Analyze current indexes
        current_indexes = await self.analyze_current_indexes(db)

        # Generate recommendations
        recommendations = await self.generate_index_recommendations(db, query_history)

        # Find unused indexes
        unused_indexes = await self.identify_unused_indexes(db)

        # Find underutilized indexes (low usage but not zero)
        underutilized = [
            idx
            for idx in current_indexes
            if 0 < idx.usage_count < 10 and not self._is_essential_index(idx)
        ]

        # Calculate efficiency score
        total_impact = sum(rec.estimated_improvement_ms for rec in recommendations)
        efficiency_score = max(0, 100 - (len(unused_indexes) * 10))

        # Generate recommendations
        analysis_recommendations = []
        if len(unused_indexes) > 0:
            analysis_recommendations.append(
                f"Consider dropping {len(unused_indexes)} unused indexes"
            )
        if len(recommendations) > 0:
            analysis_recommendations.append(
                f"Create {len(recommendations)} new indexes for potential {total_impact:.0f}ms improvement"
            )
        if len(underutilized) > 0:
            analysis_recommendations.append(
                f"Review {len(underutilized)} underutilized indexes"
            )

        return IndexAnalysisReport(
            total_indexes=len(current_indexes),
            unused_indexes=unused_indexes,
            underutilized_indexes=underutilized,
            missing_indexes=recommendations,
            oversized_indexes=[],  # TODO: Implement size analysis
            duplicate_indexes=[],  # TODO: Implement duplicate detection
            index_efficiency_score=efficiency_score,
            potential_improvement_ms=total_impact,
            recommendations=analysis_recommendations,
        )


# Global optimizer instance
database_index_optimizer = DatabaseIndexOptimizer()
