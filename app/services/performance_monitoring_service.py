"""
System Performance Monitoring Service
Provides comprehensive system performance monitoring, alerting, and analytics
"""

import asyncio
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from statistics import mean, median, stdev
from typing import Any
import uuid

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    DATABASE_CONNECTIONS = "database_connections"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_SIZE = "queue_size"
    ACTIVE_USERS = "active_users"


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringStatus(Enum):
    """Monitoring system status"""

    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class MetricThreshold:
    """Metric threshold configuration"""

    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    time_window: int = 300  # seconds
    comparison_operator: str = "greater_than"  # greater_than, less_than, equals
    enabled: bool = True


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""

    timestamp: datetime
    metric_type: MetricType
    value: float
    unit: str
    tags: dict[str, str] = field(default_factory=dict)
    source: str = "system"
    host: str = "localhost"


@dataclass
class Alert:
    """Performance alert"""

    id: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    current_value: float
    threshold: float
    triggered_at: datetime
    resolved_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    notification_sent: bool = False


@dataclass
class SystemPerformanceSnapshot:
    """Complete system performance snapshot"""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    disk_io: dict[str, float]
    network_io: dict[str, float]
    load_average: list[float]
    process_count: int
    active_connections: int
    database_metrics: dict[str, float]
    cache_metrics: dict[str, float]
    application_metrics: dict[str, float]


@dataclass
class PerformanceReport:
    """Performance analysis report"""

    report_id: str
    period_start: datetime
    period_end: datetime
    summary: dict[str, Any]
    metrics_summary: dict[str, dict[str, float]]
    alerts_summary: dict[str, int]
    trends: dict[str, str]
    recommendations: list[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class PerformanceMonitoringService:
    """Comprehensive performance monitoring service"""

    def __init__(self):
        self.metrics_store: dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: dict[str, Alert] = {}
        self.thresholds: dict[MetricType, MetricThreshold] = {}
        self.monitoring_status = MonitoringStatus.ACTIVE
        self.collection_interval = 30  # seconds
        self.alert_check_interval = 60  # seconds
        self.background_tasks = []
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Initialize default thresholds
        self._initialize_default_thresholds()

        # Start background monitoring
        self._start_background_monitoring()

    def _initialize_default_thresholds(self):
        """Initialize default monitoring thresholds"""
        default_thresholds = [
            MetricThreshold(
                metric_type=MetricType.CPU_USAGE,
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.DISK_USAGE,
                warning_threshold=80.0,
                critical_threshold=90.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                warning_threshold=2.0,
                critical_threshold=5.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.THROUGHPUT,
                warning_threshold=50.0,
                critical_threshold=20.0,
                comparison_operator="less_than",
            ),
            MetricThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than",
            ),
            MetricThreshold(
                metric_type=MetricType.CACHE_HIT_RATE,
                warning_threshold=80.0,
                critical_threshold=60.0,
                comparison_operator="less_than",
            ),
        ]

        for threshold in default_thresholds:
            self.thresholds[threshold.metric_type] = threshold

    def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        # Metrics collection task
        metrics_task = asyncio.create_task(self._collect_metrics_loop())

        # Alert checking task
        alert_task = asyncio.create_task(self._check_alerts_loop())

        # Cleanup old metrics task
        cleanup_task = asyncio.create_task(self._cleanup_old_metrics_loop())

        self.background_tasks = [metrics_task, alert_task, cleanup_task]

    async def _collect_metrics_loop(self):
        """Background loop for collecting metrics"""
        while self.monitoring_status == MonitoringStatus.ACTIVE:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e!s}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_alerts_loop(self):
        """Background loop for checking alerts"""
        while self.monitoring_status == MonitoringStatus.ACTIVE:
            try:
                await self._check_metric_thresholds()
                await asyncio.sleep(self.alert_check_interval)
            except Exception as e:
                logger.error(f"Error in alert checking: {e!s}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _cleanup_old_metrics_loop(self):
        """Background loop for cleaning up old metrics"""
        while self.monitoring_status == MonitoringStatus.ACTIVE:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {e!s}")
                await asyncio.sleep(3600)  # Wait before retrying

    async def _collect_system_metrics(self):
        """Collect current system metrics"""
        timestamp = datetime.utcnow()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_metric = PerformanceMetric(
            timestamp=timestamp, metric_type=MetricType.CPU_USAGE, value=cpu_percent, unit="percent"
        )
        self.metrics_store[MetricType.CPU_USAGE].append(cpu_metric)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.MEMORY_USAGE,
            value=memory.percent,
            unit="percent",
        )
        self.metrics_store[MetricType.MEMORY_USAGE].append(memory_metric)

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.DISK_USAGE,
            value=(disk.used / disk.total) * 100,
            unit="percent",
        )
        self.metrics_store[MetricType.DISK_USAGE].append(disk_metric)

        # Network I/O metrics
        network = psutil.net_io_counters()
        network_in_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.NETWORK_IO,
            value=network.bytes_recv,
            unit="bytes",
            tags={"direction": "inbound"},
        )
        network_out_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.NETWORK_IO,
            value=network.bytes_sent,
            unit="bytes",
            tags={"direction": "outbound"},
        )
        self.metrics_store[MetricType.NETWORK_IO].append(network_in_metric)
        self.metrics_store[MetricType.NETWORK_IO].append(network_out_metric)

        # Collect application-specific metrics
        await self._collect_application_metrics(timestamp)

    async def _collect_application_metrics(self, timestamp: datetime):
        """Collect application-specific metrics"""
        try:
            # Active connections (simulated)
            active_connections = len(psutil.net_connections())
            connections_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.ACTIVE_USERS,
                value=active_connections,
                unit="count",
            )
            self.metrics_store[MetricType.ACTIVE_USERS].append(connections_metric)

            # Database connections (simulated)
            db_connections = 50  # Would be actual DB connection count
            db_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.DATABASE_CONNECTIONS,
                value=db_connections,
                unit="count",
            )
            self.metrics_store[MetricType.DATABASE_CONNECTIONS].append(db_metric)

            # Response time (simulated)
            import random

            response_time = random.uniform(0.1, 2.0)
            response_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.RESPONSE_TIME,
                value=response_time,
                unit="seconds",
            )
            self.metrics_store[MetricType.RESPONSE_TIME].append(response_metric)

            # Throughput (simulated)
            throughput = random.uniform(20, 100)
            throughput_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.THROUGHPUT,
                value=throughput,
                unit="requests_per_second",
            )
            self.metrics_store[MetricType.THROUGHPUT].append(throughput_metric)

            # Error rate (simulated)
            error_rate = random.uniform(0.1, 2.0)
            error_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.ERROR_RATE,
                value=error_rate,
                unit="percent",
            )
            self.metrics_store[MetricType.ERROR_RATE].append(error_metric)

            # Cache hit rate (simulated)
            cache_hit_rate = random.uniform(70, 95)
            cache_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.CACHE_HIT_RATE,
                value=cache_hit_rate,
                unit="percent",
            )
            self.metrics_store[MetricType.CACHE_HIT_RATE].append(cache_metric)

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e!s}")

    async def _check_metric_thresholds(self):
        """Check metric values against thresholds and create alerts"""
        for metric_type, threshold in self.thresholds.items():
            if not threshold.enabled:
                continue

            try:
                metrics = list(self.metrics_store[metric_type])
                if not metrics:
                    continue

                # Get recent metrics within time window
                cutoff_time = datetime.utcnow() - timedelta(seconds=threshold.time_window)
                recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]

                if not recent_metrics:
                    continue

                # Calculate average value for the time window
                avg_value = mean(m.value for m in recent_metrics)
                latest_value = recent_metrics[-1].value

                # Check thresholds
                if self._should_trigger_alert(threshold, avg_value):
                    await self._create_or_update_alert(
                        metric_type, latest_value, threshold, avg_value
                    )
                else:
                    # Check if we should resolve existing alerts
                    await self._resolve_alert_if_resolved(metric_type, avg_value, threshold)

            except Exception as e:
                logger.error(f"Error checking thresholds for {metric_type.value}: {e!s}")

    def _should_trigger_alert(self, threshold: MetricThreshold, value: float) -> bool:
        """Determine if alert should be triggered based on threshold"""
        if threshold.comparison_operator == "greater_than":
            return value >= threshold.critical_threshold
        if threshold.comparison_operator == "less_than":
            return value <= threshold.critical_threshold
        return False

    async def _create_or_update_alert(
        self,
        metric_type: MetricType,
        current_value: float,
        threshold: MetricThreshold,
        avg_value: float,
    ):
        """Create or update alert for metric threshold violation"""
        alert_id = f"{metric_type.value}_alert"

        # Check if alert already exists
        if alert_id in self.alerts:
            existing_alert = self.alerts[alert_id]
            if existing_alert.resolved_at:
                # Alert was resolved, create new one
                new_alert = Alert(
                    id=alert_id,
                    metric_type=metric_type,
                    severity=AlertSeverity.CRITICAL,
                    message=f"{metric_type.value} critical threshold exceeded",
                    current_value=current_value,
                    threshold=threshold.critical_threshold,
                    triggered_at=datetime.utcnow(),
                )
                self.alerts[alert_id] = new_alert
                await self._send_alert_notification(new_alert)
        else:
            # Create new alert
            severity = (
                AlertSeverity.WARNING
                if avg_value < threshold.critical_threshold
                else AlertSeverity.CRITICAL
            )
            alert = Alert(
                id=alert_id,
                metric_type=metric_type,
                severity=severity,
                message=f"{metric_type.value} threshold exceeded",
                current_value=current_value,
                threshold=threshold.warning_threshold
                if severity == AlertSeverity.WARNING
                else threshold.critical_threshold,
                triggered_at=datetime.utcnow(),
            )
            self.alerts[alert_id] = alert
            await self._send_alert_notification(alert)

    async def _resolve_alert_if_resolved(
        self, metric_type: MetricType, current_value: float, threshold: MetricThreshold
    ):
        """Resolve alert if metric value is back within normal range"""
        alert_id = f"{metric_type.value}_alert"

        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            if not alert.resolved_at:
                # Check if value is back to normal
                if threshold.comparison_operator == "greater_than":
                    if current_value < threshold.warning_threshold:
                        alert.resolved_at = datetime.utcnow()
                        await self._send_alert_resolution_notification(alert)
                elif threshold.comparison_operator == "less_than":
                    if current_value > threshold.warning_threshold:
                        alert.resolved_at = datetime.utcnow()
                        await self._send_alert_resolution_notification(alert)

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification"""
        try:
            # In a real implementation, this would send to monitoring systems like:
            # - Slack, Microsoft Teams, Discord
            # - PagerDuty, OpsGenie
            # - Email notifications
            # - SMS for critical alerts

            message = f"=¨ {alert.severity.value.upper()} Alert: {alert.message}\n"
            message += f"Metric: {alert.metric_type.value}\n"
            message += f"Current Value: {alert.current_value:.2f}\n"
            message += f"Threshold: {alert.threshold:.2f}\n"
            message += f"Triggered: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"

            logger.warning(f"ALERT: {message}")
            alert.notification_sent = True

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e!s}")

    async def _send_alert_resolution_notification(self, alert: Alert):
        """Send alert resolution notification"""
        try:
            message = f" Alert Resolved: {alert.metric_type.value}\n"
            message += "Value returned to normal range\n"
            message += f"Resolved: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"

            logger.info(f"ALERT RESOLVED: {message}")

        except Exception as e:
            logger.error(f"Failed to send alert resolution notification: {e!s}")

    async def _cleanup_old_metrics(self):
        """Clean up old metrics to prevent memory leaks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep 24 hours of data

        for metric_type in self.metrics_store:
            metrics = self.metrics_store[metric_type]
            # Keep only recent metrics
            recent_metrics = deque((m for m in metrics if m.timestamp >= cutoff_time), maxlen=10000)
            self.metrics_store[metric_type] = recent_metrics

        # Clean up resolved alerts older than 7 days
        old_alert_cutoff = datetime.utcnow() - timedelta(days=7)
        resolved_alerts_to_remove = [
            alert_id
            for alert_id, alert in self.alerts.items()
            if alert.resolved_at and alert.resolved_at < old_alert_cutoff
        ]

        for alert_id in resolved_alerts_to_remove:
            del self.alerts[alert_id]

    async def get_current_metrics(self) -> dict[str, float]:
        """Get current system metrics"""
        current_metrics = {}

        for metric_type in self.metrics_store:
            metrics = list(self.metrics_store[metric_type])
            if metrics:
                current_metrics[metric_type.value] = metrics[-1].value

        return current_metrics

    async def get_metric_history(
        self,
        metric_type: MetricType,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[PerformanceMetric]:
        """Get historical data for a specific metric"""
        if metric_type not in self.metrics_store:
            return []

        metrics = list(self.metrics_store[metric_type])

        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]

        # Sort by timestamp and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        return metrics[:limit]

    async def get_system_performance_snapshot(self) -> SystemPerformanceSnapshot:
        """Get complete system performance snapshot"""
        timestamp = datetime.utcnow()

        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()
        load_avg = psutil.getloadavg()

        snapshot = SystemPerformanceSnapshot(
            timestamp=timestamp,
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=(disk.used / disk.total) * 100,
            disk_io={
                "read_bytes": disk.read_bytes if hasattr(disk, "read_bytes") else 0,
                "write_bytes": disk.write_bytes if hasattr(disk, "write_bytes") else 0,
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
            load_average=list(load_avg),
            process_count=len(psutil.pids()),
            active_connections=len(psutil.net_connections()),
            database_metrics=await self._get_database_metrics(),
            cache_metrics=await self._get_cache_metrics(),
            application_metrics=await self._get_application_metrics(),
        )

        return snapshot

    async def _get_database_metrics(self) -> dict[str, float]:
        """Get database performance metrics"""
        # In a real implementation, this would query the actual database
        # For now, returning simulated metrics
        return {
            "connections": 45,
            "active_connections": 32,
            "idle_connections": 13,
            "queries_per_second": 125.5,
            "slow_queries": 2.1,
            "cache_hit_ratio": 94.5,
        }

    async def _get_cache_metrics(self) -> dict[str, float]:
        """Get cache performance metrics"""
        # In a real implementation, this would query Redis/Memcached
        return {
            "hit_rate": 87.2,
            "miss_rate": 12.8,
            "memory_usage": 65.3,
            "key_count": 15234,
            "evictions_per_second": 1.2,
        }

    async def _get_application_metrics(self) -> dict[str, float]:
        """Get application-specific metrics"""
        current_metrics = await self.get_current_metrics()
        return {
            "active_users": current_metrics.get("active_users", 0),
            "response_time": current_metrics.get("response_time", 0),
            "throughput": current_metrics.get("throughput", 0),
            "error_rate": current_metrics.get("error_rate", 0),
            "cache_hit_rate": current_metrics.get("cache_hit_rate", 0),
        }

    async def generate_performance_report(
        self, start_time: datetime, end_time: datetime, report_id: str | None = None
    ) -> PerformanceReport:
        """Generate comprehensive performance report"""
        if not report_id:
            report_id = str(uuid.uuid4())

        logger.info(
            f"Generating performance report {report_id} for period {start_time} to {end_time}"
        )

        # Collect metrics data for the period
        all_metrics = {}
        for metric_type in self.metrics_store:
            metrics = await self.get_metric_history(metric_type, start_time, end_time, limit=10000)
            all_metrics[metric_type.value] = metrics

        # Calculate summary statistics
        summary_stats = {}
        for metric_name, metrics in all_metrics.items():
            if metrics:
                values = [m.value for m in metrics]
                summary_stats[metric_name] = {
                    "count": len(values),
                    "average": mean(values),
                    "median": median(values),
                    "min": min(values),
                    "max": max(values),
                    "std": stdev(values) if len(values) > 1 else 0,
                }

        # Count alerts
        alerts_in_period = [
            alert for alert in self.alerts.values() if start_time <= alert.triggered_at <= end_time
        ]

        alerts_summary = {
            "total": len(alerts_in_period),
            "resolved": len([a for a in alerts_in_period if a.resolved_at]),
            "active": len([a for a in alerts_in_period if not a.resolved_at]),
            "by_severity": {
                "critical": len(
                    [a for a in alerts_in_period if a.severity == AlertSeverity.CRITICAL]
                ),
                "warning": len(
                    [a for a in alerts_in_period if a.severity == AlertSeverity.WARNING]
                ),
                "info": len([a for a in alerts_in_period if a.severity == AlertSeverity.INFO]),
            },
        }

        # Analyze trends
        trends = {}
        for metric_name, metrics in all_metrics.items():
            if len(metrics) >= 10:  # Need enough data points for trend analysis
                values = [m.value for m in metrics]
                first_half = values[: len(values) // 2]
                second_half = values[len(values) // 2 :]

                first_avg = mean(first_half)
                second_avg = mean(second_half)

                if second_avg > first_avg * 1.1:
                    trends[metric_name] = "increasing"
                elif second_avg < first_avg * 0.9:
                    trends[metric_name] = "decreasing"
                else:
                    trends[metric_name] = "stable"

        # Generate recommendations
        recommendations = await self._generate_performance_recommendations(
            summary_stats, alerts_summary, trends
        )

        return PerformanceReport(
            report_id=report_id,
            period_start=start_time,
            period_end=end_time,
            summary={
                "total_metrics_collected": sum(len(metrics) for metrics in all_metrics.values()),
                "monitoring_coverage": len(all_metrics) / len(MetricType),
                "report_generation_time": datetime.utcnow().isoformat(),
            },
            metrics_summary=summary_stats,
            alerts_summary=alerts_summary,
            trends=trends,
            recommendations=recommendations,
        )

    async def _generate_performance_recommendations(
        self,
        summary_stats: dict[str, dict[str, float]],
        alerts_summary: dict[str, Any],
        trends: dict[str, str],
    ) -> list[str]:
        """Generate performance recommendations"""
        recommendations = []

        # CPU usage recommendations
        if "cpu_usage" in summary_stats:
            cpu_avg = summary_stats["cpu_usage"]["average"]
            if cpu_avg > 80:
                recommendations.append(
                    "CPU usage is consistently high. Consider scaling up or optimizing CPU-intensive operations."
                )
            elif cpu_avg > 60:
                recommendations.append(
                    "CPU usage is elevated. Monitor for potential performance bottlenecks."
                )

        # Memory usage recommendations
        if "memory_usage" in summary_stats:
            mem_avg = summary_stats["memory_usage"]["average"]
            if mem_avg > 85:
                recommendations.append(
                    "Memory usage is critically high. Consider adding more memory or optimizing memory usage."
                )
            elif mem_avg > 70:
                recommendations.append("Memory usage is high. Monitor for potential memory leaks.")

        # Response time recommendations
        if "response_time" in summary_stats:
            response_avg = summary_stats["response_time"]["average"]
            if response_avg > 2.0:
                recommendations.append(
                    "Response times are slow. Investigate slow queries, optimize database operations, or consider caching."
                )
            elif response_avg > 1.0:
                recommendations.append(
                    "Response times could be improved. Consider implementing performance optimizations."
                )

        # Error rate recommendations
        if "error_rate" in summary_stats:
            error_avg = summary_stats["error_rate"]["average"]
            if error_avg > 5.0:
                recommendations.append(
                    "Error rate is high. Investigate application errors and fix critical issues."
                )

        # Alert-based recommendations
        if alerts_summary["active"] > 5:
            recommendations.append(
                f"There are {alerts_summary['active']} active alerts. Address critical issues first."
            )
        elif alerts_summary["total"] > 20:
            recommendations.append(
                "High number of alerts in the period. Consider adjusting thresholds or improving system stability."
            )

        # Trend-based recommendations
        increasing_trends = [metric for metric, trend in trends.items() if trend == "increasing"]
        if len(increasing_trends) > 3:
            recommendations.append(
                f"Multiple metrics are trending upwards: {', '.join(increasing_trends)}. Proactive monitoring recommended."
            )

        return recommendations

    async def update_threshold(
        self, metric_type: MetricType, warning_threshold: float, critical_threshold: float, **kwargs
    ) -> MetricThreshold:
        """Update monitoring threshold for a metric"""
        threshold = MetricThreshold(
            metric_type=metric_type,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            **kwargs,
        )

        self.thresholds[metric_type] = threshold
        logger.info(
            f"Updated thresholds for {metric_type.value}: warning={warning_threshold}, critical={critical_threshold}"
        )

        return threshold

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str, notes: str | None = None
    ) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    async def get_active_alerts(self) -> list[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved_at]

    async def pause_monitoring(self, reason: str):
        """Pause performance monitoring"""
        self.monitoring_status = MonitoringStatus.PAUSED
        logger.info(f"Performance monitoring paused: {reason}")

    async def resume_monitoring(self):
        """Resume performance monitoring"""
        self.monitoring_status = MonitoringStatus.ACTIVE
        logger.info("Performance monitoring resumed")

    async def shutdown(self):
        """Shutdown monitoring service"""
        logger.info("Shutting down performance monitoring service")
        self.monitoring_status = MonitoringStatus.MAINTENANCE

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        logger.info("Performance monitoring service shutdown complete")


# Initialize the performance monitoring service
performance_monitoring_service = PerformanceMonitoringService()
