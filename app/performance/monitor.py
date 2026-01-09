# app/performance/monitor.py

"""
ENTERPRISE PERFORMANCE MONITOR
Comprehensive application performance monitoring and alerting

PERFORMANCE MONITOR FEATURES:
- Real-time performance metrics
- Request/response time tracking
- Resource usage monitoring
- Performance baseline comparison
- Automated alerting system
- Historical performance data
- Performance trend analysis

Author: Security Team
Version: 2.0 Enterprise Security
"""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading
import time
from typing import Any

import psutil

# Initialize performance monitor logger
perf_logger = logging.getLogger("app.performance.monitor")


class PerformanceLevel(Enum):
    """Performance severity levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    POOR = "poor"
    CRITICAL = "critical"


class AlertType(Enum):
    """Performance alert types"""

    HIGH_RESPONSE_TIME = "high_response_time"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    HIGH_CPU_USAGE = "high_cpu_usage"
    LOW_CACHE_HIT_RATIO = "low_cache_hit_ratio"
    SLOW_QUERIES = "slow_queries"


@dataclass
class PerformanceMetric:
    """Single performance metric data point"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert definition"""

    alert_type: AlertType
    severity: PerformanceLevel
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: datetime | None = None


@dataclass
class RequestMetrics:
    """HTTP request performance metrics"""

    endpoint: str
    method: str
    status_code: int
    response_time: float
    timestamp: datetime
    user_id: str | None = None
    ip_address: str | None = None


class PerformanceMonitor:
    """
    Enterprise performance monitor with real-time metrics and alerting
    """

    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.is_monitoring = False
        self._monitor_task: asyncio.Task | None = None

        # Performance metrics storage
        self._metrics: dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._request_metrics: deque = deque(maxlen=5000)
        self._alerts: list[PerformanceAlert] = []

        # Performance thresholds
        self.thresholds = {
            "response_time_p95": 2.0,  # seconds
            "response_time_p99": 5.0,  # seconds
            "error_rate": 0.05,  # 5%
            "memory_usage": 0.80,  # 80%
            "cpu_usage": 0.70,  # 70%
            "cache_hit_ratio": 0.80,  # 80%
            "disk_usage": 0.85,  # 85%
        }

        # Performance history for trend analysis
        self._hourly_stats: dict[str, deque] = defaultdict(lambda: deque(maxlen=24))

        # Alert callbacks
        self._alert_callbacks: list[Callable[[PerformanceAlert], None]] = []

        # Lock for thread safety
        self._lock = threading.RLock()

    def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        perf_logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()

        perf_logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._collect_system_metrics()
                await self._analyze_performance()
                await self._check_alerts()

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                perf_logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        try:
            timestamp = datetime.utcnow()

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._record_metric("system.cpu.usage", cpu_percent, "percent", timestamp)

            # Memory usage
            memory = psutil.virtual_memory()
            self._record_metric("system.memory.usage", memory.percent, "percent", timestamp)
            self._record_metric("system.memory.available", memory.available, "bytes", timestamp)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage = (disk.used / disk.total) * 100
            self._record_metric("system.disk.usage", disk_usage, "percent", timestamp)

            # Network I/O
            network = psutil.net_io_counters()
            self._record_metric("system.network.bytes_sent", network.bytes_sent, "bytes", timestamp)
            self._record_metric("system.network.bytes_recv", network.bytes_recv, "bytes", timestamp)

            # Process-specific metrics
            process = psutil.Process()
            self._record_metric("process.memory.rss", process.memory_info().rss, "bytes", timestamp)
            self._record_metric("process.cpu.percent", process.cpu_percent(), "percent", timestamp)
            self._record_metric("process.num_threads", process.num_threads(), "count", timestamp)

        except Exception as e:
            perf_logger.error(f"System metrics collection error: {e}")

    def _record_metric(self, name: str, value: float, unit: str, timestamp: datetime):
        """Record a performance metric"""
        with self._lock:
            metric = PerformanceMetric(name=name, value=value, unit=unit, timestamp=timestamp)
            self._metrics[name].append(metric)

    def record_request_metric(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time: float,
        user_id: str | None = None,
        ip_address: str | None = None,
    ):
        """Record HTTP request performance metric"""
        metric = RequestMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=ip_address,
        )

        with self._lock:
            self._request_metrics.append(metric)

        # Also record as general metric
        self._record_metric(
            f"http.request.duration.{endpoint.replace('/', '_')}",
            response_time,
            "seconds",
            metric.timestamp,
        )

        # Record status code
        self._record_metric(
            f"http.request.status.{method.lower()}.{status_code}", 1, "count", metric.timestamp
        )

    @asynccontextmanager
    async def monitor_request(self, endpoint: str, method: str, **kwargs):
        """Context manager for monitoring HTTP request performance"""
        start_time = time.time()

        try:
            yield
            status_code = 200  # Default success status
            success = True
        except Exception:
            status_code = 500
            success = False
            raise
        finally:
            response_time = time.time() - start_time

            # Record metrics
            self.record_request_metric(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                **kwargs,
            )

            # Log slow requests
            if response_time > self.thresholds["response_time_p99"]:
                perf_logger.warning(
                    f"Slow request detected: {method} {endpoint} - {response_time:.3f}s"
                )

    async def _analyze_performance(self):
        """Analyze performance metrics and calculate statistics"""
        try:
            timestamp = datetime.utcnow()

            # Analyze response times
            if self._request_metrics:
                recent_requests = [
                    r
                    for r in self._request_metrics
                    if (timestamp - r.timestamp).total_seconds() < 300  # Last 5 minutes
                ]

                if recent_requests:
                    response_times = [r.response_time for r in recent_requests]
                    response_times.sort()

                    # Calculate percentiles
                    p50 = response_times[len(response_times) // 2]
                    p95 = response_times[int(len(response_times) * 0.95)]
                    p99 = response_times[int(len(response_times) * 0.99)]

                    self._record_metric("http.response_time.p50", p50, "seconds", timestamp)
                    self._record_metric("http.response_time.p95", p95, "seconds", timestamp)
                    self._record_metric("http.response_time.p99", p99, "seconds", timestamp)

                    # Calculate error rate
                    error_count = sum(1 for r in recent_requests if r.status_code >= 400)
                    error_rate = error_count / len(recent_requests)
                    self._record_metric("http.error_rate", error_rate, "percent", timestamp)

                    # Calculate request rate
                    request_rate = len(recent_requests) / 300  # requests per second
                    self._record_metric(
                        "http.request_rate", request_rate, "requests_per_second", timestamp
                    )

            # Update hourly statistics
            await self._update_hourly_stats(timestamp)

        except Exception as e:
            perf_logger.error(f"Performance analysis error: {e}")

    async def _update_hourly_stats(self, timestamp: datetime):
        """Update hourly performance statistics"""
        try:
            # Get metrics from the last hour
            one_hour_ago = timestamp - timedelta(hours=1)

            for metric_name, metrics in self._metrics.items():
                recent_metrics = [m for m in metrics if m.timestamp >= one_hour_ago]

                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    avg_value = sum(values) / len(values)
                    max_value = max(values)
                    min_value = min(values)

                    self._hourly_stats[f"{metric_name}.avg"].append(avg_value)
                    self._hourly_stats[f"{metric_name}.max"].append(max_value)
                    self._hourly_stats[f"{metric_name}.min"].append(min_value)

        except Exception as e:
            perf_logger.error(f"Hourly stats update error: {e}")

    async def _check_alerts(self):
        """Check performance thresholds and generate alerts"""
        try:
            timestamp = datetime.utcnow()
            new_alerts = []

            # Check response time
            if "http.response_time.p95" in self._metrics:
                recent_p95 = self._metrics["http.response_time.p95"]
                if recent_p95:
                    latest_p95 = recent_p95[-1].value
                    if latest_p95 > self.thresholds["response_time_p95"]:
                        alert = PerformanceAlert(
                            alert_type=AlertType.HIGH_RESPONSE_TIME,
                            severity=self._calculate_severity(
                                latest_p95, self.thresholds["response_time_p95"]
                            ),
                            message=f"95th percentile response time is high: {latest_p95:.3f}s",
                            current_value=latest_p95,
                            threshold=self.thresholds["response_time_p95"],
                            timestamp=timestamp,
                        )
                        new_alerts.append(alert)

            # Check error rate
            if "http.error_rate" in self._metrics:
                recent_error_rate = self._metrics["http.error_rate"]
                if recent_error_rate:
                    latest_error_rate = recent_error_rate[-1].value
                    if latest_error_rate > self.thresholds["error_rate"]:
                        alert = PerformanceAlert(
                            alert_type=AlertType.HIGH_ERROR_RATE,
                            severity=self._calculate_severity(
                                latest_error_rate, self.thresholds["error_rate"]
                            ),
                            message=f"Error rate is high: {latest_error_rate:.2%}",
                            current_value=latest_error_rate,
                            threshold=self.thresholds["error_rate"],
                            timestamp=timestamp,
                        )
                        new_alerts.append(alert)

            # Check memory usage
            if "system.memory.usage" in self._metrics:
                recent_memory = self._metrics["system.memory.usage"]
                if recent_memory:
                    latest_memory = recent_memory[-1].value
                    if latest_memory > self.thresholds["memory_usage"]:
                        alert = PerformanceAlert(
                            alert_type=AlertType.HIGH_MEMORY_USAGE,
                            severity=self._calculate_severity(
                                latest_memory, self.thresholds["memory_usage"]
                            ),
                            message=f"Memory usage is high: {latest_memory:.1%}",
                            current_value=latest_memory,
                            threshold=self.thresholds["memory_usage"],
                            timestamp=timestamp,
                        )
                        new_alerts.append(alert)

            # Check CPU usage
            if "system.cpu.usage" in self._metrics:
                recent_cpu = self._metrics["system.cpu.usage"]
                if recent_cpu:
                    latest_cpu = recent_cpu[-1].value
                    if latest_cpu > self.thresholds["cpu_usage"]:
                        alert = PerformanceAlert(
                            alert_type=AlertType.HIGH_CPU_USAGE,
                            severity=self._calculate_severity(
                                latest_cpu, self.thresholds["cpu_usage"]
                            ),
                            message=f"CPU usage is high: {latest_cpu:.1%}",
                            current_value=latest_cpu,
                            threshold=self.thresholds["cpu_usage"],
                            timestamp=timestamp,
                        )
                        new_alerts.append(alert)

            # Process new alerts
            for alert in new_alerts:
                if not self._is_duplicate_alert(alert):
                    self._add_alert(alert)
                    await self._trigger_alert_callbacks(alert)

        except Exception as e:
            perf_logger.error(f"Alert checking error: {e}")

    def _calculate_severity(self, value: float, threshold: float) -> PerformanceLevel:
        """Calculate alert severity based on value vs threshold"""
        ratio = value / threshold

        if ratio <= 1.0:
            return PerformanceLevel.GOOD
        if ratio <= 1.5:
            return PerformanceLevel.DEGRADED
        if ratio <= 2.0:
            return PerformanceLevel.POOR
        return PerformanceLevel.CRITICAL

    def _is_duplicate_alert(self, new_alert: PerformanceAlert) -> bool:
        """Check if alert is a duplicate of recent alert"""
        with self._lock:
            for existing_alert in self._alerts[-10:]:  # Check last 10 alerts
                if (
                    not existing_alert.resolved
                    and existing_alert.alert_type == new_alert.alert_type
                    and (new_alert.timestamp - existing_alert.timestamp).total_seconds() < 300
                ):
                    return True
            return False

    def _add_alert(self, alert: PerformanceAlert):
        """Add new alert to the list"""
        with self._lock:
            self._alerts.append(alert)

            # Keep only recent alerts (last 100)
            if len(self._alerts) > 100:
                self._alerts = self._alerts[-100:]

        # Log alert
        if alert.severity in [PerformanceLevel.POOR, PerformanceLevel.CRITICAL]:
            perf_logger.error(f"Performance alert: {alert.message}")
        else:
            perf_logger.warning(f"Performance alert: {alert.message}")

    async def _trigger_alert_callbacks(self, alert: PerformanceAlert):
        """Trigger registered alert callbacks"""
        for callback in self._alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                perf_logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add alert callback function"""
        self._alert_callbacks.append(callback)

    def get_performance_summary(self, time_window_minutes: int = 60) -> dict[str, Any]:
        """Get performance summary for specified time window"""
        try:
            timestamp = datetime.utcnow()
            window_start = timestamp - timedelta(minutes=time_window_minutes)

            with self._lock:
                # Collect metrics in time window
                window_metrics = {}
                for metric_name, metrics in self._metrics.items():
                    recent_metrics = [m for m in metrics if m.timestamp >= window_start]

                    if recent_metrics:
                        values = [m.value for m in recent_metrics]
                        window_metrics[metric_name] = {
                            "count": len(values),
                            "avg": sum(values) / len(values),
                            "min": min(values),
                            "max": max(values),
                            "latest": values[-1],
                        }

                # Request metrics
                recent_requests = [r for r in self._request_metrics if r.timestamp >= window_start]

                request_stats = {}
                if recent_requests:
                    response_times = [r.response_time for r in recent_requests]
                    response_times.sort()

                    request_stats = {
                        "total_requests": len(recent_requests),
                        "avg_response_time": sum(response_times) / len(response_times),
                        "p50_response_time": response_times[len(response_times) // 2],
                        "p95_response_time": response_times[int(len(response_times) * 0.95)],
                        "p99_response_time": response_times[int(len(response_times) * 0.99)],
                        "error_rate": sum(1 for r in recent_requests if r.status_code >= 400)
                        / len(recent_requests),
                        "status_codes": {
                            "2xx": sum(1 for r in recent_requests if 200 <= r.status_code < 300),
                            "3xx": sum(1 for r in recent_requests if 300 <= r.status_code < 400),
                            "4xx": sum(1 for r in recent_requests if 400 <= r.status_code < 500),
                            "5xx": sum(1 for r in recent_requests if 500 <= r.status_code < 600),
                        },
                    }

                # Recent alerts
                recent_alerts = [
                    a for a in self._alerts if a.timestamp >= window_start and not a.resolved
                ]

                return {
                    "time_window_minutes": time_window_minutes,
                    "timestamp": timestamp.isoformat(),
                    "metrics": window_metrics,
                    "requests": request_stats,
                    "alerts": {
                        "total": len(recent_alerts),
                        "by_severity": {
                            severity.value: len(
                                [a for a in recent_alerts if a.severity == severity]
                            )
                            for severity in PerformanceLevel
                        },
                        "recent": [
                            {
                                "type": a.alert_type.value,
                                "severity": a.severity.value,
                                "message": a.message,
                                "timestamp": a.timestamp.isoformat(),
                            }
                            for a in recent_alerts[-5:]  # Last 5 alerts
                        ],
                    },
                    "system_status": self._get_system_status(window_metrics, request_stats),
                }

        except Exception as e:
            perf_logger.error(f"Performance summary error: {e}")
            return {"error": str(e)}

    def _get_system_status(
        self, metrics: dict[str, Any], requests: dict[str, Any]
    ) -> PerformanceLevel:
        """Calculate overall system performance status"""
        try:
            issues = []

            # Check response times
            if (
                requests
                and requests.get("p95_response_time", 0) > self.thresholds["response_time_p95"]
            ):
                issues.append("slow_response")

            # Check error rate
            if requests and requests.get("error_rate", 0) > self.thresholds["error_rate"]:
                issues.append("high_error_rate")

            # Check system resources
            if (
                metrics.get("system.memory.usage", {}).get("latest", 0)
                > self.thresholds["memory_usage"]
            ):
                issues.append("high_memory")

            if metrics.get("system.cpu.usage", {}).get("latest", 0) > self.thresholds["cpu_usage"]:
                issues.append("high_cpu")

            # Determine status
            if len(issues) == 0:
                return PerformanceLevel.EXCELLENT
            if len(issues) == 1:
                return PerformanceLevel.GOOD
            if len(issues) <= 2:
                return PerformanceLevel.DEGRADED
            if len(issues) <= 3:
                return PerformanceLevel.POOR
            return PerformanceLevel.CRITICAL

        except Exception:
            return PerformanceLevel.GOOD

    def get_metrics_history(self, metric_name: str, hours: int = 24) -> list[dict[str, Any]]:
        """Get historical data for a specific metric"""
        try:
            with self._lock:
                if metric_name not in self._metrics:
                    return []

                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                historical_data = [
                    {"timestamp": m.timestamp.isoformat(), "value": m.value}
                    for m in self._metrics[metric_name]
                    if m.timestamp >= cutoff_time
                ]

                return historical_data

        except Exception as e:
            perf_logger.error(f"Metrics history error: {e}")
            return []

    def update_threshold(self, metric: str, threshold: float):
        """Update performance threshold"""
        if metric in self.thresholds:
            self.thresholds[metric] = threshold
            perf_logger.info(f"Updated {metric} threshold to {threshold}")


# Global performance monitor instance
_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor | None:
    """Get the global performance monitor instance"""
    return _performance_monitor


def initialize_performance_monitor(collection_interval: int = 60) -> PerformanceMonitor:
    """Initialize the global performance monitor"""
    global _performance_monitor
    _performance_monitor = PerformanceMonitor(collection_interval)
    perf_logger.info("Performance monitor initialized")
    return _performance_monitor
