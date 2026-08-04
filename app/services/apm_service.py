"""
Application Performance Monitoring (APM) Service
Provides comprehensive application performance monitoring, tracing, and analytics
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """APM metric types"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class PerformanceLevel(Enum):
    """Performance levels for alerts"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert types"""

    SLOW_REQUEST = "slow_request"
    HIGH_ERROR_RATE = "high_error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_SLOW = "database_slow"
    EXTERNAL_API_SLOW = "external_api_slow"
    QUEUE_BACKLOG = "queue_backlog"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""

    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)
    dimensions: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""

    name: str
    metric_type: MetricType
    warning_threshold: float | None = None
    critical_threshold: float
    comparison_operator: str = "greater_than"  # greater_than, less_than, equals
    evaluation_window: int = 300  # seconds
    enabled: bool = True
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert"""

    id: str
    name: str
    alert_type: AlertType
    level: str  # warning, critical
    message: str
    current_value: float
    threshold: float
    triggered_at: datetime
    resolved_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceSpan:
    """Distributed tracing span"""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status_code: int | None = None
    status: str = "ok"  # ok, error, timeout, cancelled
    service_name: str
    resource: str
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    baggage: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profiling data"""

    profile_id: str
    operation_name: str
    service_name: str
    start_time: datetime
    duration_ms: float
    cpu_usage: float
    memory_usage: float
    database_queries: int
    cache_hits: int
    cache_misses: int
    external_api_calls: int
    spans: list[TraceSpan] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class APMService:
    """Comprehensive Application Performance Monitoring service"""

    def __init__(self):
        self.metrics_store: dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.thresholds: dict[str, PerformanceThreshold] = {}
        self.alerts: dict[str, PerformanceAlert] = {}
        self.active_traces: dict[str, list[TraceSpan]] = {}
        self.performance_profiles: dict[str, PerformanceProfile] = {}
        self.collection_enabled = True
        self.sampling_rate = 1.0
        self.background_tasks = []

        # Initialize default thresholds
        self._initialize_default_thresholds()

        # Start background collection tasks
        self._start_background_tasks()

    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds"""
        default_thresholds = [
            PerformanceThreshold(
                name="response_time",
                metric_type=MetricType.TIMER,
                warning_threshold=1000.0,  # 1 second
                critical_threshold=5000.0,  # 5 seconds
                comparison_operator="greater_than",
                tags={"endpoint": "*"},
            ),
            PerformanceThreshold(
                name="cpu_usage",
                metric_type=MetricType.GAUGE,
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison_operator="greater_than",
                tags={"host": "*"},
            ),
            PerformanceThreshold(
                name="memory_usage",
                metric_type=MetricType.GAUGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than",
                tags={"host": "*"},
            ),
            PerformanceThreshold(
                name="error_rate",
                metric_type=MetricType.GAUGE,
                warning_threshold=5.0,  # 5%
                critical_threshold=10.0,  # 10%
                comparison_operator="greater_than",
                tags={"service": "*"},
            ),
            PerformanceThreshold(
                name="database_query_time",
                metric_type=MetricType.TIMER,
                warning_threshold=500.0,  # 500ms
                critical_threshold=2000.0,  # 2 seconds
                comparison_operator="greater_than",
                tags={"query_type": "*"},
            ),
            PerformanceThreshold(
                name="queue_length",
                metric_type=MetricType.GAUGE,
                warning_threshold=100,
                critical_threshold=500,
                comparison_operator="greater_than",
                tags={"queue": "*"},
            ),
        ]

        for threshold in default_thresholds:
            self.thresholds[threshold.name] = threshold

    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Metrics collection task
        metrics_task = asyncio.create_task(self._collect_system_metrics_loop())

        # Alert checking task
        alert_task = asyncio.create_task(self._check_thresholds_loop())

        # Cleanup old data task
        cleanup_task = asyncio.create_task(self._cleanup_old_data_loop())

        self.background_tasks = [metrics_task, alert_task, cleanup_task]

    async def _collect_system_metrics_loop(self):
        """Background loop for collecting system metrics"""
        while self.collection_enabled:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e!s}")
                await asyncio.sleep(60)

    async def _check_thresholds_loop(self):
        """Background loop for checking performance thresholds"""
        while self.collection_enabled:
            try:
                await self._check_all_thresholds()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error checking thresholds: {e!s}")
                await asyncio.sleep(60)

    async def _cleanup_old_data_loop(self):
        """Background loop for cleaning up old data"""
        while self.collection_enabled:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Clean every hour
            except Exception as e:
                logger.error(f"Error cleaning up old data: {e!s}")
                await asyncio.sleep(3600)

    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        timestamp = datetime.utcnow()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        await self.record_metric(
            name="cpu_usage",
            metric_type=MetricType.GAUGE,
            value=cpu_percent,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api"},
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        await self.record_metric(
            name="memory_usage",
            metric_type=MetricType.GAUGE,
            value=memory.percent,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api"},
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        await self.record_metric(
            name="disk_usage",
            metric_type=MetricType.GAUGE,
            value=(disk.used / disk.total) * 100,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api"},
        )

        # Network metrics
        network = psutil.net_io_counters()
        await self.record_metric(
            name="network_bytes_sent",
            metric_type=MetricType.COUNTER,
            value=network.bytes_sent,
            unit="bytes",
            timestamp=timestamp,
            tags={
                "host": "localhost",
                "service": "psychsync-api",
                "direction": "outbound",
            },
        )

        await self.record_metric(
            name="network_bytes_received",
            metric_type=MetricType.COUNTER,
            value=network.bytes_recv,
            unit="bytes",
            timestamp=timestamp,
            tags={
                "host": "localhost",
                "service": "psychsync-api",
                "direction": "inbound",
            },
        )

    async def _check_all_thresholds(self):
        """Check all performance thresholds and create alerts"""
        for threshold_name, threshold in self.thresholds.items():
            if not threshold.enabled:
                continue

            try:
                metrics = list(self.metrics_store.get(threshold_name, []))
                if not metrics:
                    continue

                # Get recent metrics within evaluation window
                cutoff_time = datetime.utcnow() - timedelta(
                    seconds=threshold.evaluation_window
                )
                recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]

                if not recent_metrics:
                    continue

                # Calculate value based on metric type
                if threshold.metric_type == MetricType.GAUGE:
                    current_value = recent_metrics[-1].value
                elif threshold.metric_type == MetricType.TIMER:
                    current_value = mean(m.value for m in recent_metrics)
                elif threshold.metric_type == MetricType.COUNTER:
                    # Rate calculation for counters
                    if len(recent_metrics) >= 2:
                        time_diff = (
                            recent_metrics[-1].timestamp - recent_metrics[0].timestamp
                        ).total_seconds()
                        if time_diff > 0:
                            value_diff = (
                                recent_metrics[-1].value - recent_metrics[0].value
                            )
                            current_value = value_diff / time_diff
                        else:
                            current_value = 0
                    else:
                        current_value = recent_metrics[-1].value
                else:
                    current_value = mean(m.value for m in recent_metrics)

                # Check if alert should be triggered
                should_alert = False
                alert_level = "warning"

                if threshold.comparison_operator == "greater_than":
                    if current_value >= threshold.critical_threshold:
                        should_alert = True
                        alert_level = "critical"
                    elif (
                        threshold.warning_threshold
                        and current_value >= threshold.warning_threshold
                    ):
                        should_alert = True
                        alert_level = "warning"
                elif threshold.comparison_operator == "less_than":
                    if current_value <= threshold.critical_threshold:
                        should_alert = True
                        alert_level = "critical"
                    elif (
                        threshold.warning_threshold
                        and current_value <= threshold.warning_threshold
                    ):
                        should_alert = True
                        alert_level = "warning"

                if should_alert:
                    await self._create_or_update_alert(
                        threshold_name, current_value, threshold, alert_level
                    )
                else:
                    # Check if existing alert should be resolved
                    await self._resolve_alert_if_resolved(
                        threshold_name, current_value, threshold
                    )

            except Exception as e:
                logger.error(f"Error checking threshold {threshold_name}: {e!s}")

    async def _create_or_update_alert(
        self,
        threshold_name: str,
        current_value: float,
        threshold: PerformanceThreshold,
        alert_level: str,
    ):
        """Create or update performance alert"""
        alert_id = f"{threshold_name}_alert"

        # Check if alert already exists
        if alert_id in self.alerts:
            existing_alert = self.alerts[alert_id]
            if existing_alert.resolved_at:
                # Alert was resolved, create new one
                new_alert = PerformanceAlert(
                    id=alert_id,
                    name=f"{threshold_name} {alert_level.upper()}",
                    alert_type=self._get_alert_type(threshold_name),
                    level=alert_level,
                    message=f"{threshold_name} threshold exceeded",
                    current_value=current_value,
                    threshold=(
                        threshold.critical_threshold
                        if alert_level == "critical"
                        else threshold.warning_threshold
                    ),
                    triggered_at=datetime.utcnow(),
                    tags=threshold.tags,
                )
                self.alerts[alert_id] = new_alert
                await self._send_alert_notification(new_alert)
        else:
            # Create new alert
            alert = PerformanceAlert(
                id=alert_id,
                name=f"{threshold_name} {alert_level.upper()}",
                alert_type=self._get_alert_type(threshold_name),
                level=alert_level,
                message=f"{threshold_name} threshold exceeded",
                current_value=current_value,
                threshold=(
                    threshold.critical_threshold
                    if alert_level == "critical"
                    else threshold.warning_threshold
                ),
                triggered_at=datetime.utcnow(),
                tags=threshold.tags,
            )
            self.alerts[alert_id] = alert
            await self._send_alert_notification(alert)

    def _get_alert_type(self, threshold_name: str) -> AlertType:
        """Get alert type based on threshold name"""
        if "response_time" in threshold_name or "duration" in threshold_name:
            return AlertType.SLOW_REQUEST
        if "error_rate" in threshold_name:
            return AlertType.HIGH_ERROR_RATE
        if "memory" in threshold_name:
            return AlertType.MEMORY_USAGE
        if "cpu" in threshold_name:
            return AlertType.CPU_USAGE
        if "database" in threshold_name:
            return AlertType.DATABASE_SLOW
        if "queue" in threshold_name:
            return AlertType.QUEUE_BACKLOG
        return AlertType.EXTERNAL_API_SLOW

    async def _resolve_alert_if_resolved(
        self, threshold_name: str, current_value: float, threshold: PerformanceThreshold
    ):
        """Resolve alert if metric value is back within normal range"""
        alert_id = f"{threshold_name}_alert"

        if alert_id not in self.alerts:
            return

        alert = self.alerts[alert_id]
        if alert.resolved_at:
            return

        # Check if value is back to normal
        is_normal = False
        if threshold.comparison_operator == "greater_than":
            if (
                threshold.warning_threshold
                and current_value < threshold.warning_threshold
            ):
                is_normal = True
        elif threshold.comparison_operator == "less_than":
            if (
                threshold.warning_threshold
                and current_value > threshold.warning_threshold
            ):
                is_normal = True

        if is_normal:
            alert.resolved_at = datetime.utcnow()
            await self._send_alert_resolution_notification(alert)

    async def _send_alert_notification(self, alert: PerformanceAlert):
        """Send alert notification"""
        try:
            # In a real implementation, this would send to various channels:
            # - Slack, Microsoft Teams, Discord
            # - PagerDuty, OpsGenie
            # - Email notifications
            # - Webhook notifications

            message = f"=¨ {alert.level.upper()} Performance Alert: {alert.message}\n"
            message += f"Metric: {alert.name}\n"
            message += f"Current Value: {alert.current_value:.2f}\n"
            message += f"Threshold: {alert.threshold:.2f}\n"
            message += (
                f"Triggered: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            logger.warning(f"PERFORMANCE ALERT: {message}")
            alert.metadata["notification_sent"] = True

        except Exception as e:
            logger.error(f"Failed to send performance alert notification: {e!s}")

    async def _send_alert_resolution_notification(self, alert: PerformanceAlert):
        """Send alert resolution notification"""
        try:
            message = f" Performance Alert Resolved: {alert.name}\n"
            message += "Value returned to normal range\n"
            message += (
                f"Resolved: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

            logger.info(f"PERFORMANCE ALERT RESOLVED: {message}")

        except Exception as e:
            logger.error(f"Failed to send alert resolution notification: {e!s}")

    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        # Keep 24 hours of metrics
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for metric_name in list(self.metrics_store.keys()):
            metrics = self.metrics_store[metric_name]
            recent_metrics = deque(
                (m for m in metrics if m.timestamp >= cutoff_time), maxlen=10000
            )
            self.metrics_store[metric_name] = recent_metrics

        # Clean up resolved alerts older than 7 days
        old_alert_cutoff = datetime.utcnow() - timedelta(days=7)
        resolved_alerts_to_remove = [
            alert_id
            for alert_id, alert in self.alerts.items()
            if alert.resolved_at and alert.resolved_at < old_alert_cutoff
        ]

        for alert_id in resolved_alerts_to_remove:
            del self.alerts[alert_id]

        # Clean up old performance profiles
        profile_cutoff = datetime.utcnow() - timedelta(hours=6)
        old_profiles_to_remove = [
            profile_id
            for profile_id, profile in self.performance_profiles.items()
            if profile.start_time < profile_cutoff
        ]

        for profile_id in old_profiles_to_remove:
            del self.performance_profiles[profile_id]

    async def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
        tags: dict[str, str] | None = None,
        dimensions: dict[str, str] | None = None,
    ):
        """Record a performance metric"""
        if not self.collection_enabled:
            return

        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            unit=unit,
            timestamp=timestamp or datetime.utcnow(),
            tags=tags or {},
            dimensions=dimensions or {},
        )

        self.metrics_store[name].append(metric)

    def trace_request(
        self, operation_name: str, service_name: str = "psychsync-api"
    ) -> Callable:
        """Decorator for tracing function execution"""

        def decorator(func):
            if asyncio.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    trace_id = str(uuid.uuid4())
                    span_id = str(uuid.uuid4())[:8]

                    start_time = datetime.utcnow()

                    # Create initial span
                    span = TraceSpan(
                        span_id=span_id,
                        trace_id=trace_id,
                        parent_span_id=None,
                        operation_name=operation_name,
                        start_time=start_time,
                        service_name=service_name,
                        resource=func.__name__,
                        tags={"function": func.__name__, "module": func.__module__},
                    )

                    # Add to active traces
                    self.active_traces[trace_id] = [span]

                    try:
                        # Execute function
                        result = await func(*args, **kwargs)

                        # Update span with success
                        end_time = datetime.utcnow()
                        span.end_time = end_time
                        span.duration_ms = (
                            end_time - start_time
                        ).total_seconds() * 1000
                        span.status = "ok"

                        # Record performance metrics
                        await self.record_metric(
                            name="function_execution_time",
                            metric_type=MetricType.TIMER,
                            value=span.duration_ms,
                            unit="milliseconds",
                            tags={
                                "function": func.__name__,
                                "module": func.__module__,
                                "operation": operation_name,
                            },
                        )

                        return result

                    except Exception as e:
                        # Update span with error
                        end_time = datetime.utcnow()
                        span.end_time = end_time
                        span.duration_ms = (
                            end_time - start_time
                        ).total_seconds() * 1000
                        span.status = "error"
                        span.logs.append(f"Error: {e!s}")

                        # Record error metrics
                        await self.record_metric(
                            name="function_errors",
                            metric_type=MetricType.COUNTER,
                            value=1,
                            unit="count",
                            tags={
                                "function": func.__name__,
                                "module": func.__module__,
                                "operation": operation_name,
                                "error_type": type(e).__name__,
                            },
                        )

                        raise

                    finally:
                        # Remove from active traces
                        if trace_id in self.active_traces:
                            del self.active_traces[trace_id]

                return async_wrapper

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                trace_id = str(uuid.uuid4())
                span_id = str(uuid.uuid4())[:8]

                start_time = datetime.utcnow()

                # Create initial span
                span = TraceSpan(
                    span_id=span_id,
                    trace_id=trace_id,
                    parent_span_id=None,
                    operation_name=operation_name,
                    start_time=start_time,
                    service_name=service_name,
                    resource=func.__name__,
                    tags={"function": func.__name__, "module": func.__module__},
                )

                # Add to active traces
                self.active_traces[trace_id] = [span]

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Update span with success
                    end_time = datetime.utcnow()
                    span.end_time = end_time
                    span.duration_ms = (end_time - start_time).total_seconds() * 1000
                    span.status = "ok"

                    # Record performance metrics
                    self._record_metric_sync(
                        name="function_execution_time",
                        metric_type=MetricType.TIMER,
                        value=span.duration_ms,
                        unit="milliseconds",
                        tags={
                            "function": func.__name__,
                            "module": func.__module__,
                            "operation": operation_name,
                        },
                    )

                    return result

                except Exception as e:
                    # Update span with error
                    end_time = datetime.utcnow()
                    span.end_time = end_time
                    span.duration_ms = (end_time - start_time).total_seconds() * 1000
                    span.status = "error"
                    span.logs.append(f"Error: {e!s}")

                    # Record error metrics
                    self._record_metric_sync(
                        name="function_errors",
                        metric_type=MetricType.COUNTER,
                        value=1,
                        unit="count",
                        tags={
                            "function": func.__name__,
                            "module": func.__module__,
                            "operation": operation_name,
                            "error_type": type(e).__name__,
                        },
                    )

                    raise

                finally:
                    # Remove from active traces
                    if trace_id in self.active_traces:
                        del self.active_traces[trace_id]

            return sync_wrapper

        return decorator

    def _record_metric_sync(
        self, name: str, metric_type: MetricType, value: float, unit: str, **kwargs
    ):
        """Synchronous version of record_metric for use in sync functions"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule the async call
                asyncio.create_task(
                    self.record_metric(name, metric_type, value, unit, **kwargs)
                )
            else:
                # If no loop running, create a new one
                asyncio.run(
                    self.record_metric(name, metric_type, value, unit, **kwargs)
                )
        except (OSError, IOError, ValueError) as e:
            # Fallback - ignore if we can't record the metric
            pass

    @asynccontextmanager
    async def profile_operation(
        self,
        operation_name: str,
        service_name: str = "psychsync-api",
        tags: dict[str, str] | None = None,
    ):
        """Context manager for profiling operations"""
        profile_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        # Get initial system metrics
        initial_cpu = psutil.cpu_percent()
        initial_memory = psutil.virtual_memory().percent

        profile = PerformanceProfile(
            profile_id=profile_id,
            operation_name=operation_name,
            service_name=service_name,
            start_time=start_time,
            duration_ms=0,
            cpu_usage=initial_cpu,
            memory_usage=initial_memory,
            database_queries=0,
            cache_hits=0,
            cache_misses=0,
            external_api_calls=0,
            tags=tags or {},
        )

        self.performance_profiles[profile_id] = profile

        try:
            yield profile_id
        finally:
            # Update profile with final metrics
            end_time = datetime.utcnow()
            profile.duration_ms = (end_time - start_time).total_seconds() * 1000

            # Calculate resource usage during operation
            final_cpu = psutil.cpu_percent()
            final_memory = psutil.virtual_memory().percent

            profile.cpu_usage = max(initial_cpu, final_cpu)
            profile.memory_usage = max(initial_memory, final_memory)

            # Remove from active profiles after some time
            await asyncio.sleep(600)  # Keep for 10 minutes
            if profile_id in self.performance_profiles:
                del self.performance_profiles[profile_id]

    async def get_performance_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get comprehensive performance summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Collect metrics summary
        metrics_summary = {}
        for metric_name, metrics in self.metrics_store.items():
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                metrics_summary[metric_name] = {
                    "count": len(values),
                    "average": mean(values),
                    "min": min(values),
                    "max": max(values),
                    "last_value": recent_metrics[-1].value,
                    "trend": self._calculate_trend(values),
                }

        # Alert summary
        alert_summary = {
            "total": len(self.alerts),
            "active": len([a for a in self.alerts.values() if not a.resolved_at]),
            "by_level": {
                "critical": len(
                    [a for a in self.alerts.values() if a.level == "critical"]
                ),
                "warning": len(
                    [a for a in self.alerts.values() if a.level == "warning"]
                ),
            },
            "by_type": {},
        }

        for alert_type in AlertType:
            alert_summary["by_type"][alert_type.value] = len(
                [a for a in self.alerts.values() if a.alert_type == alert_type]
            )

        # Performance level assessment
        performance_level = self._assess_performance_level(
            metrics_summary, alert_summary
        )

        return {
            "period_hours": hours,
            "metrics": metrics_summary,
            "alerts": alert_summary,
            "performance_level": performance_level.value,
            "active_traces": len(self.active_traces),
            "performance_profiles": len(self.performance_profiles),
            "recommendations": self._generate_recommendations(
                metrics_summary, alert_summary
            ),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend from a list of values"""
        if len(values) < 2:
            return "stable"

        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = mean(first_half)
        second_avg = mean(second_half)

        if second_avg > first_avg * 1.1:
            return "increasing"
        if second_avg < first_avg * 0.9:
            return "decreasing"
        return "stable"

    def _assess_performance_level(
        self, metrics_summary: dict[str, Any], alert_summary: dict[str, Any]
    ) -> PerformanceLevel:
        """Assess overall performance level"""
        critical_alerts = alert_summary["by_level"]["critical"]
        active_alerts = alert_summary["active"]

        if critical_alerts > 0 or active_alerts > 10:
            return PerformanceLevel.CRITICAL
        if active_alerts > 5:
            return PerformanceLevel.POOR
        if active_alerts > 0:
            return PerformanceLevel.ACCEPTABLE
        if metrics_summary.get("cpu_usage", {}).get("average", 0) > 70:
            return PerformanceLevel.GOOD
        return PerformanceLevel.EXCELLENT

    def _generate_recommendations(
        self, metrics_summary: dict[str, Any], alert_summary: dict[str, Any]
    ) -> list[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # CPU usage recommendations
        if "cpu_usage" in metrics_summary:
            cpu_avg = metrics_summary["cpu_usage"]["average"]
            if cpu_avg > 80:
                recommendations.append(
                    "High CPU usage detected. Consider optimizing CPU-intensive operations or scaling horizontally."
                )
            elif cpu_avg > 60:
                recommendations.append(
                    "CPU usage is elevated. Monitor for potential performance bottlenecks."
                )

        # Memory usage recommendations
        if "memory_usage" in metrics_summary:
            mem_avg = metrics_summary["memory_usage"]["average"]
            if mem_avg > 85:
                recommendations.append(
                    "High memory usage detected. Consider optimizing memory usage or adding more memory."
                )
            elif mem_avg > 70:
                recommendations.append(
                    "Memory usage is elevated. Monitor for potential memory leaks."
                )

        # Response time recommendations
        if "function_execution_time" in metrics_summary:
            response_avg = metrics_summary["function_execution_time"]["average"]
            if response_avg > 2000:  # 2 seconds
                recommendations.append(
                    "Slow function execution detected. Consider optimizing algorithms or implementing caching."
                )
            elif response_avg > 1000:  # 1 second
                recommendations.append(
                    "Function execution could be optimized for better performance."
                )

        # Error rate recommendations
        if "function_errors" in metrics_summary:
            error_count = metrics_summary["function_errors"]["count"]
            if error_count > 50:
                recommendations.append(
                    "High error rate detected. Review error logs and fix critical issues."
                )
            elif error_count > 10:
                recommendations.append(
                    "Multiple errors detected. Investigate and resolve recurring issues."
                )

        # Alert-based recommendations
        if alert_summary["active"] > 5:
            recommendations.append(
                f"There are {alert_summary['active']} active performance alerts. Address critical issues first."
            )

        return recommendations

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str, notes: str | None = None
    ) -> bool:
        """Acknowledge a performance alert"""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        if notes:
            alert.metadata["acknowledgment_notes"] = notes

        logger.info(f"Performance alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    async def update_threshold(
        self,
        name: str,
        warning_threshold: float | None,
        critical_threshold: float,
        **kwargs,
    ) -> PerformanceThreshold:
        """Update performance threshold"""
        threshold = PerformanceThreshold(
            name=name,
            metric_type=kwargs.get("metric_type", MetricType.GAUGE),
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            **kwargs,
        )

        self.thresholds[name] = threshold
        logger.info(
            f"Updated performance threshold for {name}: warning={warning_threshold}, critical={critical_threshold}"
        )

        return threshold

    def get_active_alerts(self) -> list[PerformanceAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved_at]

    def disable_collection(self):
        """Disable performance monitoring collection"""
        self.collection_enabled = False
        logger.info("Performance monitoring collection disabled")

    def enable_collection(self):
        """Enable performance monitoring collection"""
        self.collection_enabled = True
        logger.info("Performance monitoring collection enabled")

    async def shutdown(self):
        """Shutdown APM service"""
        logger.info("Shutting down APM service")
        self.collection_enabled = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info("APM service shutdown complete")


# Initialize APM service
apm_service = APMService()
