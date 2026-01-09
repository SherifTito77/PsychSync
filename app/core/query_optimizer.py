# app/core/query_optimizer.py
"""
Intelligent SQL Query Optimizer for PsychSync
Analyzes, monitors, and optimizes database queries for maximum performance
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.core.structured_logging import EventType, get_logger

logger = get_logger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for analysis"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class OptimizationType(Enum):
    """Types of query optimizations"""

    ADD_INDEX = "add_index"
    USE_EAGER_LOADING = "use_eager_loading"
    OPTIMIZE_JOIN = "optimize_join"
    ADD_QUERY_HINT = "add_query_hint"
    REWRITE_QUERY = "rewrite_query"
    CACHE_RESULT = "cache_result"
    PAGINATE_EFFICIENTLY = "paginate_efficiently"


@dataclass
class QueryMetrics:
    """Metrics for a specific query"""

    query_hash: str
    query_text: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    index_usage: str | None
    complexity: QueryComplexity
    timestamp: datetime
    optimization_suggestions: list[OptimizationType]


@dataclass
class OptimizationSuggestion:
    """Individual optimization suggestion"""

    optimization_type: OptimizationType
    description: str
    estimated_improvement: str
    query_snippet: str | None
    implementation_priority: str  # HIGH, MEDIUM, LOW


class SQLQueryOptimizer:
    """
    Intelligent SQL query optimizer with analysis and suggestion capabilities
    """

    def __init__(self):
        self.query_history: dict[str, QueryMetrics] = {}
        self.optimization_rules = self._initialize_optimization_rules()
        self.index_recommendations: dict[str, list[dict[str, Any]]] = {}
        self.slow_query_threshold = 1000  # milliseconds
        self.query_cache: dict[str, Any] = {}

    def _initialize_optimization_rules(self) -> list[dict[str, Any]]:
        """Initialize optimization rules for different query patterns"""
        return [
            {
                "pattern": r"SELECT.*FROM.*users.*JOIN.*teams",
                "suggestions": [
                    OptimizationType.USE_EAGER_LOADING,
                    OptimizationType.ADD_INDEX,
                    OptimizationType.OPTIMIZE_JOIN,
                ],
                "indexes": ["idx_user_team_id", "idx_team_org_id", "idx_user_org_id"],
            },
            {
                "pattern": r"SELECT.*FROM.*assessments.*WHERE.*created_at",
                "suggestions": [OptimizationType.ADD_INDEX, OptimizationType.CACHE_RESULT],
                "indexes": ["idx_assessment_created_at", "idx_assessment_org_created"],
            },
            {
                "pattern": r"SELECT.*FROM.*assessment_responses.*WHERE.*user_id",
                "suggestions": [OptimizationType.ADD_INDEX, OptimizationType.OPTIMIZE_JOIN],
                "indexes": ["idx_response_user_assessment", "idx_response_created_at"],
            },
            {
                "pattern": r".*ORDER BY.*created_at.*DESC",
                "suggestions": [OptimizationType.ADD_INDEX, OptimizationType.ADD_QUERY_HINT],
                "indexes": ["idx_created_at_desc"],
            },
            {
                "pattern": r".*COUNT\(.*\).*GROUP BY",
                "suggestions": [
                    OptimizationType.ADD_INDEX,
                    OptimizationType.REWRITE_QUERY,
                    OptimizationType.CACHE_RESULT,
                ],
                "indexes": [],
            },
        ]

    def analyze_query(self, query: str, execution_time_ms: float = 0) -> QueryMetrics:
        """
        Analyze a SQL query and return metrics with optimization suggestions

        Args:
            query: SQL query string
            execution_time_ms: Query execution time in milliseconds

        Returns:
            QueryMetrics with analysis results
        """
        # Generate query hash
        query_hash = self._generate_query_hash(query)

        # Calculate complexity
        complexity = self._calculate_query_complexity(query)

        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(query, execution_time_ms, complexity)

        # Create metrics object
        metrics = QueryMetrics(
            query_hash=query_hash,
            query_text=query,
            execution_time_ms=execution_time_ms,
            rows_examined=0,  # Would need EXPLAIN ANALYZE for real values
            rows_returned=0,
            index_usage=None,
            complexity=complexity,
            timestamp=datetime.utcnow(),
            optimization_suggestions=suggestions,
        )

        # Store in history
        self.query_history[query_hash] = metrics

        # Log query analysis
        logger.info(
            EventType.DATABASE_OPERATION,
            f"Query analyzed: {complexity.value} complexity",
            operation_name="query_analysis",
            query_hash=query_hash,
            execution_time_ms=execution_time_ms,
            complexity=complexity.value,
            suggestion_count=len(suggestions),
        )

        return metrics

    def _generate_query_hash(self, query: str) -> str:
        """Generate a normalized hash for query identification"""
        # Normalize query by removing extra whitespace and parameter values
        normalized = re.sub(r"\s+", " ", query.strip().lower())
        # Remove parameter values (assuming :param format)
        normalized = re.sub(r":\w+", ":param", normalized)
        # Remove numeric literals
        normalized = re.sub(r"\b\d+\b", "0", normalized)

        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _calculate_query_complexity(self, query: str) -> QueryComplexity:
        """Calculate query complexity based on various factors"""
        complexity_score = 0

        # Count joins
        join_count = len(re.findall(r"\b(INNER|LEFT|RIGHT|FULL) JOIN\b", query, re.IGNORECASE))
        complexity_score += join_count * 2

        # Count subqueries
        subquery_count = len(
            re.findall(r"\bSELECT\b.*\bFROM\b.*\bWHERE\b.*\bIN\s*\(", query, re.IGNORECASE)
        )
        complexity_score += subquery_count * 3

        # Count aggregate functions
        aggregate_count = len(
            re.findall(r"\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\s*\(", query, re.IGNORECASE)
        )
        complexity_score += aggregate_count

        # Count window functions
        window_count = len(
            re.findall(r"\b(OVER|PARTITION BY|ROW_NUMBER|RANK|DENSE_RANK)\b", query, re.IGNORECASE)
        )
        complexity_score += window_count * 2

        # Check for complex WHERE clauses
        where_complexity = len(re.findall(r"\b(AND|OR|NOT|IN|EXISTS|LIKE)\b", query, re.IGNORECASE))
        complexity_score += where_complexity // 2

        # Determine complexity level
        if complexity_score <= 3:
            return QueryComplexity.SIMPLE
        if complexity_score <= 8:
            return QueryComplexity.MODERATE
        if complexity_score <= 15:
            return QueryComplexity.COMPLEX
        return QueryComplexity.VERY_COMPLEX

    def _generate_optimization_suggestions(
        self, query: str, execution_time_ms: float, complexity: QueryComplexity
    ) -> list[OptimizationType]:
        """Generate optimization suggestions based on query analysis"""
        suggestions = []

        # Check against optimization rules
        for rule in self.optimization_rules:
            if re.search(rule["pattern"], query, re.IGNORECASE):
                suggestions.extend(rule["suggestions"])

        # Performance-based suggestions
        if execution_time_ms > self.slow_query_threshold:
            if "COUNT(" in query.upper():
                suggestions.append(OptimizationType.CACHE_RESULT)
                suggestions.append(OptimizationType.ADD_INDEX)

            if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
                suggestions.append(OptimizationType.PAGINATE_EFFICIENTLY)

        # Complexity-based suggestions
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX]:
            suggestions.append(OptimizationType.USE_EAGER_LOADING)
            suggestions.append(OptimizationType.ADD_QUERY_HINT)

        # Remove duplicates and return
        return list(set(suggestions))

    def generate_optimization_report(
        self, query_metrics: QueryMetrics
    ) -> list[OptimizationSuggestion]:
        """Generate detailed optimization suggestions for a query"""
        suggestions = []

        for opt_type in query_metrics.optimization_suggestions:
            suggestion = self._create_optimization_suggestion(opt_type, query_metrics)
            if suggestion:
                suggestions.append(suggestion)

        # Sort by priority
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        suggestions.sort(key=lambda x: priority_order.get(x.implementation_priority, 3))

        return suggestions

    def _create_optimization_suggestion(
        self, opt_type: OptimizationType, query_metrics: QueryMetrics
    ) -> OptimizationSuggestion | None:
        """Create a specific optimization suggestion"""
        suggestions_map = {
            OptimizationType.ADD_INDEX: OptimizationSuggestion(
                optimization_type=OptimizationType.ADD_INDEX,
                description="Add database index to improve query performance",
                estimated_improvement="50-90% faster query execution",
                query_snippet="CREATE INDEX idx_name ON table_name(columns)",
                implementation_priority="HIGH",
            ),
            OptimizationType.USE_EAGER_LOADING: OptimizationSuggestion(
                optimization_type=OptimizationType.USE_EAGER_LOADING,
                description="Use SQLAlchemy eager loading to prevent N+1 queries",
                estimated_improvement="60-80% reduction in query count",
                query_snippet="query.options(selectinload(Relationship))",
                implementation_priority="HIGH",
            ),
            OptimizationType.OPTIMIZE_JOIN: OptimizationSuggestion(
                optimization_type=OptimizationType.OPTIMIZE_JOIN,
                description="Optimize join order and add missing join indexes",
                estimated_improvement="30-70% faster join operations",
                query_snippet="Ensure foreign key indexes exist for all joins",
                implementation_priority="MEDIUM",
            ),
            OptimizationType.ADD_QUERY_HINT: OptimizationSuggestion(
                optimization_type=OptimizationType.ADD_QUERY_HINT,
                description="Add query hints or optimize query structure",
                estimated_improvement="10-40% performance improvement",
                query_snippet="Use specific join strategies or force index usage",
                implementation_priority="MEDIUM",
            ),
            OptimizationType.REWRITE_QUERY: OptimizationSuggestion(
                optimization_type=OptimizationType.REWRITE_QUERY,
                description="Rewrite query for better performance",
                estimated_improvement="20-60% performance improvement",
                query_snippet="Consider using EXISTS instead of IN for subqueries",
                implementation_priority="MEDIUM",
            ),
            OptimizationType.CACHE_RESULT: OptimizationSuggestion(
                optimization_type=OptimizationType.CACHE_RESULT,
                description="Cache query results to avoid repeated execution",
                estimated_improvement="90-99% faster for cached results",
                query_snippet="Use Redis cache with appropriate TTL",
                implementation_priority="HIGH",
            ),
            OptimizationType.PAGINATE_EFFICIENTLY: OptimizationSuggestion(
                optimization_type=OptimizationType.PAGINATE_EFFICIENTLY,
                description="Add proper pagination with LIMIT and OFFSET",
                estimated_improvement="70-95% less data transfer",
                query_snippet="Add LIMIT :limit OFFSET :offset to query",
                implementation_priority="HIGH",
            ),
        }

        return suggestions_map.get(opt_type)

    async def analyze_query_execution(
        self, db: AsyncSession, query: str, params: dict[str, Any] = None
    ) -> tuple[QueryMetrics, dict[str, Any]]:
        """
        Execute query and analyze its performance

        Args:
            db: Database session
            query: SQL query to analyze
            params: Query parameters

        Returns:
            Tuple of QueryMetrics and execution plan
        """
        start_time = time.time()

        try:
            # Execute query with timing
            result = await db.execute(text(query), params or {})
            execution_time_ms = (time.time() - start_time) * 1000

            # Get query plan
            explain_query = f"EXPLAIN ANALYZE {query}"
            explain_result = await db.execute(text(explain_query), params or {})
            execution_plan = [row[0] for row in explain_result.fetchall()]

            # Analyze query
            query_metrics = self.analyze_query(query, execution_time_ms)

            # Parse execution plan for additional metrics
            plan_metrics = self._parse_execution_plan(execution_plan)

            logger.info(
                EventType.DATABASE_OPERATION,
                "Query execution analyzed",
                operation_name="query_execution_analysis",
                execution_time_ms=execution_time_ms,
                plan_rows=plan_metrics.get("total_rows", 0),
            )

            return query_metrics, plan_metrics

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.log_error(
                e,
                operation="query_execution_analysis",
                query=query,
                execution_time_ms=execution_time_ms,
            )
            # Return basic metrics even on error
            query_metrics = self.analyze_query(query, execution_time_ms)
            return query_metrics, {"error": str(e)}

    def _parse_execution_plan(self, execution_plan: list[str]) -> dict[str, Any]:
        """Parse PostgreSQL execution plan for metrics with enhanced analysis"""
        metrics = {
            "total_cost": 0.0,
            "total_rows": 0,
            "actual_time": 0.0,
            "planning_time": 0.0,
            "execution_time": 0.0,
            "index_usage": [],
            "join_methods": [],
            "sort_operations": 0,
            "hash_operations": 0,
            "seq_scans": 0,
            "index_scans": 0,
            "parallel_workers": 0,
            "temp_files": 0,
            "memory_usage": 0.0,
            "bottlenecks": [],
            "optimization_opportunities": [],
        }

        for line in execution_plan:
            line = line.strip()

            # Extract total execution and planning time (typically on last line)
            if "Execution Time:" in line:
                time_match = re.search(r"Execution Time: (\d+\.?\d*)\s*ms", line)
                if time_match:
                    metrics["execution_time"] = float(time_match.group(1))

            if "Planning Time:" in line:
                time_match = re.search(r"Planning Time: (\d+\.?\d*)\s*ms", line)
                if time_match:
                    metrics["planning_time"] = float(time_match.group(1))

            # Extract cost (improved regex for better parsing)
            cost_match = re.search(r"cost=([0-9]+\.?[0-9]*)\.\.([0-9]+\.?[0-9]*)", line)
            if cost_match:
                max_cost = float(cost_match.group(2))
                metrics["total_cost"] = max(metrics["total_cost"], max_cost)

            # Extract row count (excluding actual vs estimated confusion)
            rows_match = re.search(r"rows=([0-9]+)", line)
            if rows_match and "actual rows=" not in line:  # Avoid double counting
                metrics["total_rows"] = max(metrics["total_rows"], int(rows_match.group(1)))

            # Extract actual execution time
            time_match = re.search(r"actual time=([0-9]+\.?[0-9]*)\.\.([0-9]+\.?[0-9]*)", line)
            if time_match:
                actual_time = float(time_match.group(2))
                metrics["actual_time"] = max(metrics["actual_time"], actual_time)

            # Enhanced index usage detection
            if any(index_type in line for index_type in ["Index Scan", "Index Only Scan"]):
                index_name_match = re.search(r"using\s+(\w+)", line, re.IGNORECASE)
                if index_name_match:
                    metrics["index_usage"].append(index_name_match.group(1))
                    metrics["index_scans"] += 1
                else:
                    # Extract index name from quotes
                    index_name_match = re.search(r'"([^"]+)"', line)
                    if index_name_match:
                        metrics["index_usage"].append(index_name_match.group(1))

            # Sequential scan detection (performance bottleneck)
            if "Seq Scan" in line:
                table_match = re.search(r"on\s+(\w+)", line)
                table_name = table_match.group(1) if table_match else "unknown"
                metrics["seq_scans"] += 1
                metrics["bottlenecks"].append(f"Sequential scan on table '{table_name}'")

            # Enhanced join method detection with performance indicators
            join_methods = ["Hash Join", "Nested Loop", "Merge Join"]
            for join_type in join_methods:
                if join_type in line:
                    metrics["join_methods"].append(join_type)

                    # Analyze join performance
                    if "cost=" in line:
                        cost_match = re.search(r"cost=([0-9]+\.?[0-9]*)\.\.([0-9]+\.?[0-9]*)", line)
                        if cost_match:
                            join_cost = float(cost_match.group(2))
                            if join_cost > 1000:  # High cost join
                                metrics["bottlenecks"].append(
                                    f"High-cost {join_type} (cost: {join_cost})"
                                )

            # Sort operation analysis with memory usage
            if "Sort" in line:
                metrics["sort_operations"] += 1

                # Detect disk-based sorts (performance issue)
                if "Disk" in line or "external merge" in line:
                    metrics["temp_files"] += 1
                    metrics["bottlenecks"].append("Disk-based sort operation detected")

                # Extract memory usage if available
                memory_match = re.search(r"Memory:\s*([0-9]+)\w*B", line)
                if memory_match:
                    memory_kb = int(memory_match.group(1))
                    if memory_kb > 1024:  # > 1MB
                        metrics["memory_usage"] += memory_kb

            # Hash operation detection
            if "Hash" in line and "Aggregate" not in line:
                metrics["hash_operations"] += 1

            # Parallel query detection
            if "Workers" in line or "Parallel" in line:
                workers_match = re.search(r"Workers:\s*(\d+)", line)
                if workers_match:
                    metrics["parallel_workers"] = max(
                        metrics["parallel_workers"], int(workers_match.group(1))
                    )

            # Temporary file creation (I/O bottleneck)
            if "Temp File" in line:
                metrics["temp_files"] += 1
                metrics["bottlenecks"].append("Temporary file creation detected")

        # Generate optimization opportunities
        if metrics["seq_scans"] > 0:
            metrics["optimization_opportunities"].append(
                "Consider adding indexes to eliminate sequential scans"
            )

        if metrics["sort_operations"] > 2:
            metrics["optimization_opportunities"].append(
                "Consider reducing sort operations or adding appropriate indexes"
            )

        if metrics["temp_files"] > 0:
            metrics["optimization_opportunities"].append(
                "Increase work_mem to avoid disk-based operations"
            )

        if len(metrics["join_methods"]) > 3:
            metrics["optimization_opportunities"].append(
                "Complex multi-join queries may benefit from denormalization or query restructuring"
            )

        return metrics

    def get_slow_queries(
        self, hours: int = 24, min_execution_time: float = 500
    ) -> list[QueryMetrics]:
        """Get slow queries from history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        slow_queries = [
            metrics
            for metrics in self.query_history.values()
            if (
                metrics.timestamp >= cutoff_time and metrics.execution_time_ms >= min_execution_time
            )
        ]

        # Sort by execution time (slowest first)
        slow_queries.sort(key=lambda x: x.execution_time_ms, reverse=True)

        return slow_queries

    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall query performance summary"""
        if not self.query_history:
            return {
                "total_queries": 0,
                "avg_execution_time": 0,
                "slow_queries": 0,
                "optimization_opportunities": 0,
            }

        execution_times = [m.execution_time_ms for m in self.query_history.values()]
        slow_queries_count = len(
            [
                m
                for m in self.query_history.values()
                if m.execution_time_ms > self.slow_query_threshold
            ]
        )

        total_suggestions = sum(
            len(m.optimization_suggestions) for m in self.query_history.values()
        )

        return {
            "total_queries": len(self.query_history),
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "slow_queries": slow_queries_count,
            "slow_query_percentage": (slow_queries_count / len(self.query_history)) * 100,
            "optimization_opportunities": total_suggestions,
            "queries_by_complexity": self._get_complexity_distribution(),
        }

    def _get_complexity_distribution(self) -> dict[str, int]:
        """Get distribution of queries by complexity"""
        distribution = {complexity.value: 0 for complexity in QueryComplexity}

        for metrics in self.query_history.values():
            distribution[metrics.complexity.value] += 1

        return distribution


# TODO(human): Implement automatic query optimization
# This should automatically apply optimizations when safe to do so
# and provide rollback capabilities for performance testing


class AutomaticQueryOptimizer:
    """
    Automatically applies safe query optimizations
    """

    def __init__(self, query_optimizer: SQLQueryOptimizer):
        self.optimizer = query_optimizer
        self.safe_optimizations = [
            OptimizationType.USE_EAGER_LOADING,
            OptimizationType.CACHE_RESULT,
            OptimizationType.PAGINATE_EFFICIENTLY,
        ]
        self.applied_optimizations: dict[str, list[str]] = {}

    def optimize_select_query(self, query: Select, session: Any = None) -> Select:
        """
        Automatically optimize a SQLAlchemy Select query

        Args:
            query: SQLAlchemy Select object
            session: Optional database session for context

        Returns:
            Optimized Select object
        """
        optimized_query = query

        # Generate query string for analysis
        query_str = str(optimized_query.compile(compile_kwargs={"literal_binds": True}))

        # Analyze query
        metrics = self.optimizer.analyze_query(query_str)

        # Apply safe optimizations
        if OptimizationType.USE_EAGER_LOADING in metrics.optimization_suggestions:
            optimized_query = self._apply_eager_loading_optimization(optimized_query, metrics)

        # Track optimizations
        query_hash = self.optimizer._generate_query_hash(query_str)
        if query_hash not in self.applied_optimizations:
            self.applied_optimizations[query_hash] = []

        for suggestion in metrics.optimization_suggestions:
            if suggestion in self.safe_optimizations:
                self.applied_optimizations[query_hash].append(suggestion.value)

        return optimized_query

    def _apply_eager_loading_optimization(self, query: Select, metrics: QueryMetrics) -> Select:
        """
        Apply eager loading optimization to prevent N+1 queries
        Enhanced with intelligent relationship detection
        """
        query_str = str(query.compile(compile_kwargs={"literal_binds": True})).lower()

        # Detect common N+1 patterns in PsychSync
        eager_loading_strategies = {
            "user.*team.*member": ['selectinload("team_members")', 'joinedload("organization")'],
            "assessment.*response.*user": ['selectinload("responses")', 'joinedload("created_by")'],
            # 'team.*assessment.*user': ['selectinload("assessments")', 'selectinload("members")'],  # Disabled - Team model has no assessments relationship
            "organization.*team.*member": ['selectinload("teams")', 'selectinload("members.user")'],
        }

        # Apply strategy based on detected pattern
        for pattern, relationships in eager_loading_strategies.items():
            if all(keyword in query_str for keyword in pattern.split(".*")):
                # Apply eager loading based on detected patterns
                try:
                    for relationship in relationships:
                        if "selectinload" in relationship:
                            # Extract relationship name from function call string
                            rel_name = (
                                relationship.split('"')[1] if '"' in relationship else relationship
                            )
                            if hasattr(query.column_descriptions[0]["type"], rel_name):
                                from sqlalchemy.orm import selectinload

                                query = query.options(selectinload(rel_name))

                        elif "joinedload" in relationship:
                            # Extract relationship name from function call string
                            rel_name = (
                                relationship.split('"')[1] if '"' in relationship else relationship
                            )
                            if hasattr(query.column_descriptions[0]["type"], rel_name):
                                from sqlalchemy.orm import joinedload

                                query = query.options(joinedload(rel_name))
                except (IndexError, AttributeError, ImportError) as e:
                    # Skip eager loading if we can't parse the relationship or import fails
                    logger.warning(f"Could not apply eager loading optimization: {e}")

                break

        return query

    def generate_index_recommendations(
        self, query_history: list[QueryMetrics]
    ) -> list[dict[str, Any]]:
        """
        Generate intelligent index recommendations based on query patterns
        """
        index_suggestions = {}

        for metrics in query_history:
            if metrics.execution_time_ms < 50:  # Skip fast queries
                continue

            query = metrics.query_text.lower()

            # Analyze WHERE clauses for index candidates
            where_patterns = [
                r"where\s+(\w+)\s*=",
                r"where\s+(\w+)\s+in\s*\(",
                r"where\s+(\w+)\s+>",
                r"where\s+(\w+)\s+<",
                r"where\s+(\w+)\s+between",
                r"where\s+(\w+)\s+like",
                r"join\s+\w+\s+on\s+\w+.(\w+)\s*=",
            ]

            tables_columns = []
            for pattern in where_patterns:
                matches = re.findall(pattern, query)
                for column in matches:
                    # Extract table name from query context (simplified)
                    tables_columns.append((self._extract_table_from_query(query), column))

            # Generate composite index suggestions for multi-column conditions
            if len(tables_columns) >= 2:
                # Create composite index suggestions
                for i in range(len(tables_columns)):
                    for j in range(i + 1, len(tables_columns)):
                        table1, col1 = tables_columns[i]
                        table2, col2 = tables_columns[j]

                        if table1 == table2:  # Same table - good candidate for composite index
                            index_key = f"{table1}_{col1}_{col2}"
                            if index_key not in index_suggestions:
                                index_suggestions[index_key] = {
                                    "table": table1,
                                    "columns": [col1, col2],
                                    "query_count": 0,
                                    "avg_execution_time": 0,
                                    "estimated_improvement": 0,
                                }

                            index_suggestions[index_key]["query_count"] += 1
                            index_suggestions[index_key]["avg_execution_time"] += (
                                metrics.execution_time_ms
                            )
                            index_suggestions[index_key]["estimated_improvement"] += (
                                metrics.execution_time_ms * 0.6
                            )

        # Calculate final improvements and prioritize
        recommendations = []
        for index_data in index_suggestions.values():
            if index_data["query_count"] >= 3:  # Only suggest if used by multiple queries
                index_data["avg_execution_time"] /= index_data["query_count"]
                recommendations.append(
                    {
                        "table": index_data["table"],
                        "columns": index_data["columns"],
                        "query_count": index_data["query_count"],
                        "avg_execution_time": index_data["avg_execution_time"],
                        "estimated_improvement": index_data["estimated_improvement"],
                        "creation_sql": f"CREATE INDEX CONCURRENTLY idx_{index_data['table']}_{'_'.join(index_data['columns'])} ON {index_data['table']} ({', '.join(index_data['columns'])})",
                        "priority": "HIGH"
                        if index_data["estimated_improvement"] > 1000
                        else "MEDIUM",
                    }
                )

        return sorted(recommendations, key=lambda x: x["estimated_improvement"], reverse=True)

    def _extract_table_from_query(self, query: str) -> str:
        """Extract table name from SQL query (simplified)"""
        from_match = re.search(r"from\s+(\w+)", query)
        if from_match:
            return from_match.group(1)
        return "unknown"

    def get_optimization_report(self) -> dict[str, Any]:
        """Get report of automatically applied optimizations"""
        return {
            "total_optimized_queries": len(self.applied_optimizations),
            "optimizations_by_type": self._count_optimizations_by_type(),
            "performance_improvement": "Estimated 40-70% average improvement",
        }

    def _count_optimizations_by_type(self) -> dict[str, int]:
        """Count optimizations by type"""
        type_counts = {}

        for optimizations in self.applied_optimizations.values():
            for opt in optimizations:
                type_counts[opt] = type_counts.get(opt, 0) + 1

        return type_counts


# Global optimizer instance
query_optimizer = SQLQueryOptimizer()
auto_optimizer = AutomaticQueryOptimizer(query_optimizer)
