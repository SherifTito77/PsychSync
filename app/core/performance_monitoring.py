"""
Production Performance Monitoring System

Features:
- Request timing measurement
- Performance metrics collection
- Alerting for performance degradation
- Integration with monitoring systems
- Real-time performance dashboards
"""

import time
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import statistics

from app.core.config import settings
from app.core.redis_client import redis_get, redis_set

logger = logging.getLogger(__name__)

class OperationType(str, Enum):
    """Operation types for monitoring"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    AUTH = "auth"
    CACHE = "cache"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    FILE_OPERATION = "file_operation"

class PerformanceLevel(str, Enum):
    """Performance level classifications"""
    EXCELLENT = "excellent"  # < 100ms
    GOOD = "good"           # 100-300ms
    ACCEPTABLE = "acceptable"  # 300-1000ms
    POOR = "poor"           # > 1000ms

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    operation: str
    operation_type: OperationType
    duration_ms: float
    timestamp: datetime
    success: bool
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['operation_type'] = self.operation_type.value
        data['performance_level'] = self.get_performance_level().value
        return data

    def get_performance_level(self) -> PerformanceLevel:
        """Get performance level based on duration"""
        if self.duration_ms < 100:
            return PerformanceLevel.EXCELLENT
        elif self.duration_ms < 300:
            return PerformanceLevel.GOOD
        elif self.duration_ms < 1000:
            return PerformanceLevel.ACCEPTABLE
        else:
            return PerformanceLevel.POOR

class PerformanceMonitor:
    """
    Production performance monitoring system
    """

    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics_in_memory = 10000
        self.alert_thresholds = {
            "warning_ms": 500,
            "critical_ms": 2000,
            "error_rate_threshold": 0.05,  # 5%
            "slow_request_threshold": 0.1,  # 10% of requests
        }
        self.performance_windows = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "24h": 86400
        }

    async def record_metric(self, metric: PerformanceMetric) -> bool:
        """
        Record a performance metric

        Args:
            metric: Performance metric to record

        Returns:
            True if recorded successfully
        """
        try:
            # Add to in-memory metrics
            self.metrics.append(metric)

            # Trim if too many metrics
            if len(self.metrics) > self.max_metrics_in_memory:
                self.metrics = self.metrics[-self.max_metrics_in_memory:]

            # Store in Redis for persistence
            await self._store_in_redis(metric)

            # Check for performance alerts
            await self._check_alerts(metric)

            return True

        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")
            return False

    def get_metrics_summary(
        self,
        operation_type: Optional[OperationType] = None,
        window_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Get performance metrics summary

        Args:
            operation_type: Filter by operation type
            window_minutes: Time window in minutes

        Returns:
            Performance summary
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Filter metrics
        filtered_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff_time and
            (operation_type is None or m.operation == operation_type)
        ]

        if not filtered_metrics:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "performance_levels": {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}
            }

        # Calculate statistics
        durations = [m.duration_ms for m in filtered_metrics]
        success_count = sum(1 for m in filtered_metrics if m.success)

        # Performance level distribution
        level_counts = {
            "excellent": 0,
            "good": 0,
            "acceptable": 0,
            "poor": 0
        }

        for metric in filtered_metrics:
            level = metric.get_performance_level().value
            level_counts[level] += 1

        # Percentiles
        sorted_durations = sorted(durations)
        percentiles = {}
        for p in [50, 90, 95, 99]:
            index = int(len(sorted_durations) * (p / 100))
            if index < len(sorted_durations):
                percentiles[f"p{p}"] = sorted_durations[index]

        return {
            "total_requests": len(filtered_metrics),
            "success_rate": (success_count / len(filtered_metrics)) * 100,
            "average_duration_ms": statistics.mean(durations),
            "median_duration_ms": statistics.median(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "percentiles": percentiles,
            "performance_levels": level_counts,
            "window_minutes": window_minutes,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_slow_requests(
        self,
        threshold_ms: float = 1000,
        limit: int = 100,
        window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get slow requests exceeding threshold

        Args:
            threshold_ms: Duration threshold in milliseconds
            limit: Maximum number of requests to return
            window_minutes: Time window in minutes

        Returns:
            List of slow requests
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        slow_metrics = [
            m for m in self.metrics
            if (m.timestamp >= cutoff_time and
                m.duration_ms > threshold_ms)
        ]

        # Sort by duration (slowest first) and limit
        slow_metrics.sort(key=lambda x: x.duration_ms, reverse=True)
        slow_metrics = slow_metrics[:limit]

        return [m.to_dict() for m in slow_metrics]

    def get_error_rate_trend(
        self,
        window_minutes: int = 60,
        bucket_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get error rate trend over time

        Args:
            window_minutes: Total time window
            bucket_minutes: Size of each time bucket

        Returns:
            Error rate trend data
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        buckets = []

        for i in range(0, window_minutes, bucket_minutes):
            bucket_start = cutoff_time + timedelta(minutes=i)
            bucket_end = bucket_start + timedelta(minutes=bucket_minutes)

            bucket_metrics = [
                m for m in self.metrics
                if bucket_start <= m.timestamp < bucket_end
            ]

            if bucket_metrics:
                error_count = sum(1 for m in bucket_metrics if not m.success)
                error_rate = (error_count / len(bucket_metrics)) * 100
            else:
                error_rate = 0.0

            buckets.append({
                "timestamp": bucket_start.isoformat(),
                "error_rate": error_rate,
                "total_requests": len(bucket_metrics),
                "error_count": error_count
            })

        return buckets

    async def _store_in_redis(self, metric: PerformanceMetric):
        """Store metric in Redis for persistence"""
        try:
            # Store in time-series data
            key = f"perf:{metric.operation_type.value}:{metric.timestamp.strftime('%Y%m%d%H%M')}"
            data = json.dumps(metric.to_dict())

            # Store with expiration (24 hours)
            await redis_set(key, data, expire_seconds=86400)

            # Store in recent metrics list
            recent_key = "perf:recent"
            await redis_set(recent_key, data, expire_seconds=3600)  # 1 hour

        except Exception as e:
            logger.warning(f"Failed to store performance metric in Redis: {e}")

    async def _check_alerts(self, metric: PerformanceMetric):
        """Check for performance alerts"""
        try:
            # Check for slow request
            if metric.duration_ms > self.alert_thresholds["critical_ms"]:
                await self._trigger_alert(
                    "CRITICAL_PERFORMANCE",
                    f"Critical slow request: {metric.operation} took {metric.duration_ms:.0f}ms",
                    {
                        "operation": metric.operation,
                        "duration_ms": metric.duration_ms,
                        "request_id": metric.request_id,
                        "user_id": metric.user_id
                    }
                )
            elif metric.duration_ms > self.alert_thresholds["warning_ms"]:
                await self._trigger_alert(
                    "PERFORMANCE_WARNING",
                    f"Slow request: {metric.operation} took {metric.duration_ms:.0f}ms",
                    {
                        "operation": metric.operation,
                        "duration_ms": metric.duration_ms,
                        "request_id": metric.request_id
                    }
                )

            # Check for error patterns
            if not metric.success:
                await self._check_error_patterns(metric)

        except Exception as e:
            logger.error(f"Failed to check performance alerts: {e}")

    async def _check_error_patterns(self, metric: PerformanceMetric):
        """Check for error patterns and trends"""
        try:
            # Get recent error rate for this operation
            summary = self.get_metrics_summary(
                operation_type=metric.operation_type,
                window_minutes=5
            )

            if summary["total_requests"] > 0:
                error_rate = 100 - summary["success_rate"]
                if error_rate > self.alert_thresholds["error_rate_threshold"] * 100:
                    await self._trigger_alert(
                        "HIGH_ERROR_RATE",
                        f"High error rate for {metric.operation}: {error_rate:.1f}%",
                        {
                            "operation": metric.operation,
                            "error_rate": error_rate,
                            "total_requests": summary["total_requests"],
                            "window_minutes": 5
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to check error patterns: {e}")

    async def _trigger_alert(
        self,
        alert_type: str,
        message: str,
        metadata: Dict[str, Any]
    ):
        """Trigger performance alert"""
        try:
            alert_data = {
                "alert_type": alert_type,
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "psychsync_api"
            }

            # Log to alert logger
            alert_logger = logging.getLogger("performance_alerts")
            alert_logger.warning(
                f"Performance Alert: {alert_type}",
                extra=alert_data
            )

            # Store alert in Redis
            alert_key = f"alerts:performance:{int(time.time())}"
            await redis_set(alert_key, json.dumps(alert_data), expire_seconds=86400)

        except Exception as e:
            logger.error(f"Failed to trigger performance alert: {e}")

    def cleanup_old_metrics(self, retention_hours: int = 24):
        """Clean up old metrics from memory"""
        cutoff_time = datetime.utcnow() - timedelta(hours=retention_hours)
        original_count = len(self.metrics)

        self.metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff_time
        ]

        cleaned_count = original_count - len(self.metrics)
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old performance metrics")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorator for automatic performance monitoring
def measure_performance(
    operation_name: str = None,
    operation_type: OperationType = OperationType.READ,
    include_args: bool = False
):
    """
    Decorator for automatic performance monitoring

    Args:
        operation_name: Name of the operation
        operation_type: Type of operation
        include_args: Whether to include function arguments in metadata
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            # Extract context information
            request_id = None
            user_id = None
            endpoint = None

            try:
                # Extract from function arguments if available
                if hasattr(args[0], '__self__'):  # Method call
                    self_obj = args[0]
                    if hasattr(self_obj, 'request'):
                        request_id = getattr(self_obj.request, 'request_id', None)
                        user_id = getattr(self_obj.request, 'user_id', None)
                        endpoint = getattr(self_obj.request, 'url', None)

                # Call the function
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                success = False
                error_message = str(e)
                raise

            finally:
                # Record performance metric
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                # Prepare metadata
                metadata = {}
                if include_args:
                    metadata.update({
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    })

                if error_message:
                    metadata["error_message"] = error_message

                metric = PerformanceMetric(
                    operation=operation_name or f"{func.__module__}.{func.__name__}",
                    operation_type=operation_type,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    success=success,
                    request_id=request_id,
                    user_id=user_id,
                    endpoint=str(endpoint) if endpoint else None,
                    metadata=metadata if metadata else None,
                    error_message=error_message
                )

                # Record metric asynchronously
                asyncio.create_task(performance_monitor.record_metric(metric))

        return wrapper
    return decorator


# Performance monitoring middleware
class PerformanceMiddleware:
    """FastAPI middleware for performance monitoring"""

    def __init__(self, app, monitor: PerformanceMonitor = None):
        self.app = app
        self.monitor = monitor or performance_monitor

    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Extract request information
        method = scope["method"]
        path = scope["path"]
        query_string = scope.get("query_string", b"").decode()

        # Generate request ID
        request_id = f"req_{int(start_time * 1000)}_{hash(path)}"

        # Determine operation type based on method
        operation_type_map = {
            "GET": OperationType.READ,
            "POST": OperationType.WRITE,
            "PUT": OperationType.WRITE,
            "PATCH": OperationType.WRITE,
            "DELETE": OperationType.DELETE
        }
        operation_type = operation_type_map.get(method, OperationType.READ)

        # Create custom send function to capture response
        async def custom_send(message):
            if message["type"] == "http.response.start":
                # Record performance metric
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                status_code = message.get("status", 200)

                metric = PerformanceMetric(
                    operation=f"{method} {path}",
                    operation_type=operation_type,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    success=200 <= status_code < 400,
                    request_id=request_id,
                    endpoint=f"{method} {path}{query_string if query_string else ''}",
                    metadata={
                        "method": method,
                        "path": path,
                        "status_code": status_code
                    }
                )

                # Record metric asynchronously
                asyncio.create_task(self.monitor.record_metric(metric))

            await send(message)

        await self.app(scope, receive, custom_send)


# Performance reporting utilities
class PerformanceReporter:
    """Generate performance reports"""

    @staticmethod
    def generate_daily_report(date: datetime = None) -> Dict[str, Any]:
        """Generate daily performance report"""
        if date is None:
            date = datetime.utcnow()

        monitor = performance_monitor

        report = {
            "date": date.strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": monitor.get_metrics_summary(window_minutes=1440),  # 24 hours
            "slow_requests": monitor.get_slow_requests(threshold_ms=1000, limit=50),
            "error_trend": monitor.get_error_rate_trend(window_minutes=1440, bucket_minutes=60),
            "alerts": []
        }

        # Add recommendations
        report["recommendations"] = PerformanceReporter._generate_recommendations(report)

        return report

    @staticmethod
    def _generate_recommendations(report: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        summary = report.get("summary", {})

        # Check average response time
        if summary.get("average_duration_ms", 0) > 500:
            recommendations.append(
                "Consider optimizing slow operations. Average response time is above 500ms"
            )

        # Check error rate
        error_rate = 100 - summary.get("success_rate", 100)
        if error_rate > 5:
            recommendations.append(
                f"High error rate detected ({error_rate:.1f}%). Review error logs and fix issues"
            )

        # Check performance distribution
        levels = summary.get("performance_levels", {})
        total_requests = sum(levels.values())
        if total_requests > 0:
            poor_percentage = (levels.get("poor", 0) / total_requests) * 100
            if poor_percentage > 10:
                recommendations.append(
                    f"High percentage of slow requests ({poor_percentage:.1f}%). Consider performance optimization"
                )

        return recommendations