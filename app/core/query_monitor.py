# app/core/query_monitor.py
"""
Query Performance Monitoring System for PsychSync
Real-time monitoring and analysis of database query performance
"""

import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache_strategy import intelligent_cache
from app.core.query_optimizer import QueryComplexity, query_optimizer
from app.core.structured_logging import EventType, get_logger

logger = get_logger(__name__)


@dataclass
class QueryPerformanceStats:
    """Real-time query performance statistics"""

    total_queries: int = 0
    avg_execution_time: float = 0.0
    max_execution_time: float = 0.0
    min_execution_time: float = float("inf")
    slow_query_count: int = 0
    error_count: int = 0
    cache_hit_rate: float = 0.0
    queries_per_second: float = 0.0


@dataclass
class AlertThreshold:
    """Alert configuration for query performance"""

    max_execution_time: float = 1000.0  # milliseconds
    max_slow_query_rate: float = 10.0  # percentage
    max_error_rate: float = 5.0  # percentage
    min_cache_hit_rate: float = 70.0  # percentage
    max_queries_per_second: float = 100.0


class QueryMonitor:
    """
    Real-time query performance monitoring and alerting system
    """

    def __init__(self, alert_thresholds: AlertThreshold | None = None):
        self.alert_thresholds = alert_thresholds or AlertThreshold()
        self.current_stats = QueryPerformanceStats()
        self.query_history: deque = deque(maxlen=10000)  # Last 10k queries
        self.slow_query_history: deque = deque(maxlen=1000)  # Last 1k slow queries
        self.error_history: deque = deque(maxlen=100)  # Last 100 errors
        self.alerts: deque = deque(maxlen=1000)  # Last 1k alerts

        # Real-time counters
        self.query_times: deque = deque(maxlen=1000)  # Last 1k query times
        self.query_timestamps: deque = deque(maxlen=1000)  # Last 1k timestamps
        self.cache_hits = 0
        self.cache_misses = 0

        # Background monitoring
        self.monitoring_active = True
        self.last_alert_check = datetime.utcnow()

        # Performance tracking by operation type
        self.operation_stats: dict[str, QueryPerformanceStats] = defaultdict(
            QueryPerformanceStats
        )

    @asynccontextmanager
    async def monitor_query(
        self,
        query: str,
        operation_name: str = "unknown",
        session: AsyncSession | None = None,
        params: dict[str, Any] | None = None,
    ):
        """
        Context manager for monitoring query execution
        """
        start_time = time.time()
        query_id = f"{operation_name}_{int(start_time * 1000)}"

        try:
            # Pre-execution logging
            logger.debug(
                EventType.DATABASE_OPERATION,
                f"Executing query: {operation_name}",
                operation_name="query_start",
                query_id=query_id,
                query_operation=operation_name,
            )

            # Execute the query (yielding control back to caller)
            yield query_id

            # Record successful execution
            execution_time_ms = (time.time() - start_time) * 1000
            await self._record_query_execution(
                query, execution_time_ms, operation_name, query_id, success=True
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            await self._record_query_execution(
                query,
                execution_time_ms,
                operation_name,
                query_id,
                success=False,
                error=str(e),
            )

            # Re-raise the exception
            raise

    async def _record_query_execution(
        self,
        query: str,
        execution_time_ms: float,
        operation_name: str,
        query_id: str,
        success: bool,
        error: str | None = None,
    ):
        """Record query execution metrics"""
        timestamp = datetime.utcnow()

        # Update general statistics
        self.current_stats.total_queries += 1
        self.query_times.append(execution_time_ms)
        self.query_timestamps.append(timestamp)

        self.current_stats.max_execution_time = max(
            self.current_stats.max_execution_time, execution_time_ms
        )

        self.current_stats.min_execution_time = min(
            self.current_stats.min_execution_time, execution_time_ms
        )

        # Calculate new average
        total_time = sum(self.query_times)
        self.current_stats.avg_execution_time = total_time / len(self.query_times)

        # Track slow queries
        if execution_time_ms > self.alert_thresholds.max_execution_time:
            self.current_stats.slow_query_count += 1
            self.slow_query_history.append(
                {
                    "query_id": query_id,
                    "query": query[:200],  # Truncate for storage
                    "execution_time_ms": execution_time_ms,
                    "timestamp": timestamp,
                    "operation_name": operation_name,
                }
            )

        # Track errors
        if not success:
            self.current_stats.error_count += 1
            self.error_history.append(
                {
                    "query_id": query_id,
                    "query": query[:200],
                    "error": error,
                    "execution_time_ms": execution_time_ms,
                    "timestamp": timestamp,
                    "operation_name": operation_name,
                }
            )

        # Store in history
        query_record = {
            "query_id": query_id,
            "query": query[:200],
            "execution_time_ms": execution_time_ms,
            "timestamp": timestamp,
            "operation_name": operation_name,
            "success": success,
        }
        self.query_history.append(query_record)

        # Update operation-specific stats
        op_stats = self.operation_stats[operation_name]
        op_stats.total_queries += 1
        op_stats.avg_execution_time = (
            (op_stats.avg_execution_time * (op_stats.total_queries - 1))
            + execution_time_ms
        ) / op_stats.total_queries

        op_stats.max_execution_time = max(
            op_stats.max_execution_time, execution_time_ms
        )

        # Analyze query using optimizer
        try:
            query_metrics = query_optimizer.analyze_query(query, execution_time_ms)

            # Log detailed query analysis
            if (
                query_metrics.complexity == QueryComplexity.VERY_COMPLEX
                or execution_time_ms > self.alert_thresholds.max_execution_time
            ):
                logger.warning(
                    EventType.DATABASE_OPERATION,
                    f"Complex or slow query detected: {operation_name}",
                    operation_name="complex_query_detected",
                    query_id=query_id,
                    complexity=query_metrics.complexity.value,
                    execution_time_ms=execution_time_ms,
                    suggestions=len(query_metrics.optimization_suggestions),
                )
        except Exception as e:
            logger.log_error(e, operation="query_analysis", query_id=query_id)

        # Update queries per second
        await self._update_queries_per_second()

        # Check for alerts
        await self._check_alerts()

    async def _update_queries_per_second(self):
        """Update queries per second calculation"""
        if len(self.query_timestamps) < 2:
            return

        now = datetime.utcnow()
        one_second_ago = now - timedelta(seconds=1)

        # Count queries in the last second
        recent_queries = [ts for ts in self.query_timestamps if ts >= one_second_ago]

        self.current_stats.queries_per_second = len(recent_queries)

    async def _check_alerts(self):
        """Check if any performance thresholds are exceeded"""
        now = datetime.utcnow()

        # Don't check alerts too frequently
        if (now - self.last_alert_check).total_seconds() < 30:
            return

        self.last_alert_check = now
        alerts_generated = []

        # Check slow query rate
        if self.current_stats.total_queries > 0:
            slow_query_rate = (
                self.current_stats.slow_query_count / self.current_stats.total_queries
            ) * 100

            if slow_query_rate > self.alert_thresholds.max_slow_query_rate:
                alert = {
                    "type": "high_slow_query_rate",
                    "message": f"Slow query rate is {slow_query_rate:.1f}% (threshold: {self.alert_thresholds.max_slow_query_rate}%)",
                    "timestamp": now,
                    "severity": "WARNING",
                }
                alerts_generated.append(alert)

        # Check error rate
        if self.current_stats.total_queries > 0:
            error_rate = (
                self.current_stats.error_count / self.current_stats.total_queries
            ) * 100

            if error_rate > self.alert_thresholds.max_error_rate:
                alert = {
                    "type": "high_error_rate",
                    "message": f"Error rate is {error_rate:.1f}% (threshold: {self.alert_thresholds.max_error_rate}%)",
                    "timestamp": now,
                    "severity": "ERROR",
                }
                alerts_generated.append(alert)

        # Check queries per second
        if (
            self.current_stats.queries_per_second
            > self.alert_thresholds.max_queries_per_second
        ):
            alert = {
                "type": "high_qps",
                "message": f"Queries per second is {self.current_stats.queries_per_second:.1f} (threshold: {self.alert_thresholds.max_queries_per_second})",
                "timestamp": now,
                "severity": "WARNING",
            }
            alerts_generated.append(alert)

        # Check cache performance
        try:
            cache_stats = intelligent_cache.get_cache_stats()
            total_cache_requests = cache_stats["hits"] + cache_stats["misses"]

            if total_cache_requests > 0:
                hit_rate = (cache_stats["hits"] / total_cache_requests) * 100
                self.current_stats.cache_hit_rate = hit_rate

                if hit_rate < self.alert_thresholds.min_cache_hit_rate:
                    alert = {
                        "type": "low_cache_hit_rate",
                        "message": f"Cache hit rate is {hit_rate:.1f}% (threshold: {self.alert_thresholds.min_cache_hit_rate}%)",
                        "timestamp": now,
                        "severity": "INFO",
                    }
                    alerts_generated.append(alert)
        except Exception:
            pass  # Cache stats might not be available

        # Store alerts
        for alert in alerts_generated:
            self.alerts.append(alert)

            # Log alert
            logger.warning(
                EventType.DATABASE_OPERATION,
                f"Performance alert: {alert['type']}",
                operation_name="performance_alert",
                alert_type=alert["type"],
                message=alert["message"],
                severity=alert["severity"],
            )

    def get_real_time_stats(self) -> dict[str, Any]:
        """Get current real-time performance statistics"""
        return asdict(self.current_stats)

    def get_operation_breakdown(self) -> dict[str, Any]:
        """Get performance breakdown by operation type"""
        return {
            op_name: asdict(stats) for op_name, stats in self.operation_stats.items()
        }

    def get_recent_slow_queries(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent slow queries"""
        return list(self.slow_query_history)[-limit:]

    def get_recent_errors(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent query errors"""
        return list(self.error_history)[-limit:]

    def get_recent_alerts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent performance alerts"""
        return list(self.alerts)[-limit:]

    def get_performance_summary(self, minutes: int = 60) -> dict[str, Any]:
        """Get enhanced performance summary for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        # Filter recent queries
        recent_queries = [
            q for q in self.query_history if q["timestamp"] >= cutoff_time
        ]

        if not recent_queries:
            return {
                "period_minutes": minutes,
                "total_queries": 0,
                "avg_execution_time": 0,
                "slow_queries": 0,
                "errors": 0,
                "performance_grade": "N/A",
                "throughput_score": 0,
                "latency_score": 0,
                "reliability_score": 0,
            }

        execution_times = [q["execution_time_ms"] for q in recent_queries]
        slow_count = len(
            [
                q
                for q in recent_queries
                if q["execution_time_ms"] > self.alert_thresholds.max_execution_time
            ]
        )
        error_count = len([q for q in recent_queries if not q["success"]])

        # Calculate performance scores (0-100)
        total_queries = len(recent_queries)
        avg_time = sum(execution_times) / len(execution_times)

        # Throughput score: queries per minute (scaled to 0-100)
        throughput = total_queries / max(minutes, 1)
        throughput_score = min(100, (throughput / 100) * 100)  # 100 QPM = 100 score

        # Latency score: inverse of average execution time (scaled)
        latency_score = max(
            0, 100 - (avg_time / 10)
        )  # 1000ms = 0 score, 0ms = 100 score

        # Reliability score: based on error rate (100% success = 100 score)
        reliability_score = ((total_queries - error_count) / total_queries) * 100

        # Overall performance grade
        overall_score = (throughput_score + latency_score + reliability_score) / 3
        if overall_score >= 90:
            performance_grade = "A"
        elif overall_score >= 80:
            performance_grade = "B"
        elif overall_score >= 70:
            performance_grade = "C"
        elif overall_score >= 60:
            performance_grade = "D"
        else:
            performance_grade = "F"

        # Calculate percentiles for better understanding
        sorted_times = sorted(execution_times)
        p50 = sorted_times[len(sorted_times) // 2]  # Median
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]

        return {
            "period_minutes": minutes,
            "total_queries": total_queries,
            "avg_execution_time": avg_time,
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "median_execution_time": p50,
            "p95_execution_time": p95,
            "p99_execution_time": p99,
            "slow_queries": slow_count,
            "slow_query_rate": (slow_count / total_queries) * 100,
            "errors": error_count,
            "error_rate": (error_count / total_queries) * 100,
            "queries_per_minute": total_queries / minutes,
            "performance_grade": performance_grade,
            "throughput_score": round(throughput_score, 1),
            "latency_score": round(latency_score, 1),
            "reliability_score": round(reliability_score, 1),
            "overall_score": round(overall_score, 1),
        }

    def reset_statistics(self):
        """Reset all performance statistics"""
        self.current_stats = QueryPerformanceStats()
        self.query_history.clear()
        self.slow_query_history.clear()
        self.error_history.clear()
        self.alerts.clear()
        self.query_times.clear()
        self.query_timestamps.clear()
        self.operation_stats.clear()


class QueryPerformanceDashboard:
    """
    Enhanced query performance dashboard with real-time analytics
    and predictive performance insights
    """

    def __init__(self, monitor: QueryMonitor):
        self.monitor = monitor
        self.performance_trends: deque = deque(
            maxlen=1440
        )  # 24 hours of minute-by-minute data

    def get_dashboard_data(self) -> dict[str, Any]:
        """Get all data needed for the performance dashboard"""
        return {
            "real_time_stats": self.monitor.get_real_time_stats(),
            "performance_summary": self.monitor.get_performance_summary(minutes=60),
            "operation_breakdown": self.monitor.get_operation_breakdown(),
            "recent_slow_queries": self.monitor.get_recent_slow_queries(limit=10),
            "recent_errors": self.monitor.get_recent_errors(limit=10),
            "recent_alerts": self.monitor.get_recent_alerts(limit=20),
            "optimization_opportunities": self._get_optimization_opportunities(),
        }

    def _get_optimization_opportunities(self) -> list[dict[str, Any]]:
        """Get optimization opportunities from query history"""
        opportunities = []

        # Group slow queries by pattern
        query_patterns = defaultdict(list)

        for query in self.monitor.slow_query_history:
            # Create a simple pattern by removing specific values
            pattern = re.sub(r"\d+", "N", query["query"])
            pattern = re.sub(r":\w+", ":param", pattern)
            query_patterns[pattern].append(query)

        # Analyze each pattern
        for pattern, queries in query_patterns.items():
            if len(queries) >= 3:  # Pattern that appears multiple times
                avg_time = sum(q["execution_time_ms"] for q in queries) / len(queries)

                opportunities.append(
                    {
                        "pattern": (
                            pattern[:100] + "..." if len(pattern) > 100 else pattern
                        ),
                        "occurrence_count": len(queries),
                        "avg_execution_time": avg_time,
                        "max_execution_time": max(
                            q["execution_time_ms"] for q in queries
                        ),
                        "impact_score": len(queries)
                        * avg_time,  # Simple impact calculation
                        "recommendation": self._get_pattern_recommendation(pattern),
                    }
                )

        # Sort by impact score
        opportunities.sort(key=lambda x: x["impact_score"], reverse=True)

        return opportunities[:10]  # Top 10 opportunities

    def _get_pattern_recommendation(self, pattern: str) -> str:
        """Get optimization recommendation for a query pattern"""
        pattern_lower = pattern.lower()

        if "join" in pattern_lower and "users" in pattern_lower:
            return "Consider adding composite indexes on user_id columns and using eager loading"
        if "count(" in pattern_lower:
            return "Consider caching count results or using materialized views"
        if "order by" in pattern_lower and "created_at" in pattern_lower:
            return (
                "Add index on created_at with DESC order for better sorting performance"
            )
        if "assessment_responses" in pattern_lower:
            return "Add indexes on (user_id, assessment_id) and created_at for this frequently queried table"
        return (
            "Analyze query execution plan and consider appropriate indexing strategies"
        )

    def export_performance_report(self, hours: int = 24) -> dict[str, Any]:
        """Export comprehensive performance report"""
        return {
            "report_generated_at": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "summary": self.monitor.get_performance_summary(minutes=hours * 60),
            "real_time_stats": self.monitor.get_real_time_stats(),
            "operation_breakdown": self.monitor.get_operation_breakdown(),
            "slow_queries": self.monitor.get_recent_slow_queries(limit=100),
            "errors": self.monitor.get_recent_errors(limit=100),
            "alerts": self.monitor.get_recent_alerts(limit=100),
            "optimization_opportunities": self._get_optimization_opportunities(),
            "recommendations": self._generate_overall_recommendations(),
        }

    def _generate_overall_recommendations(self) -> list[str]:
        """Generate overall performance recommendations"""
        recommendations = []
        stats = self.monitor.current_stats

        if stats.avg_execution_time > 500:
            recommendations.append(
                "Average query time is high. Consider database optimization and query review."
            )

        if stats.cache_hit_rate < 70:
            recommendations.append(
                "Cache hit rate is low. Review caching strategy and implement more aggressive caching."
            )

        if (stats.slow_query_count / max(stats.total_queries, 1)) * 100 > 10:
            recommendations.append(
                "Slow query rate is high. Prioritize query optimization and indexing."
            )

        if stats.queries_per_second > 80:
            recommendations.append(
                "High query rate detected. Consider implementing query throttling or better caching."
            )

        if stats.error_count > 0:
            recommendations.append(
                "Query errors detected. Review error handling and database constraints."
            )

        return recommendations


# Global monitor instance
query_monitor = QueryMonitor()
performance_dashboard = QueryPerformanceDashboard(query_monitor)
