"""
System Performance Monitoring Service
Provides comprehensive system performance monitoring, alerting, and analytics
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid
import asyncio
import psutil
import time
from collections import defaultdict, deque
from statistics import mean, median, stdev
import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, text

from app.core.config import settings

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
    tags: Dict[str, str] = field(default_factory=dict)
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
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    notification_sent: bool = False


@dataclass
class SystemPerformanceSnapshot:
    """Complete system performance snapshot"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    disk_io: Dict[str, float]
    network_io: Dict[str, float]
    load_average: List[float]
    process_count: int
    active_connections: int
    database_metrics: Dict[str, float]
    cache_metrics: Dict[str, float]
    application_metrics: Dict[str, float]


@dataclass
class PerformanceReport:
    """Performance analysis report"""
    report_id: str
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    metrics_summary: Dict[str, Dict[str, float]]
    alerts_summary: Dict[str, int]
    trends: Dict[str, str]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


class PerformanceMonitoringService:
    """Comprehensive performance monitoring service"""

    def __init__(self):
        self.metrics_store: Dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.alerts: Dict[str, Alert] = {}
        self.thresholds: Dict[MetricType, MetricThreshold] = {}
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
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.DISK_USAGE,
                warning_threshold=80.0,
                critical_threshold=90.0,
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                warning_threshold=2.0,
                critical_threshold=5.0,
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=5.0,
                critical_threshold=10.0,
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.THROUGHPUT,
                warning_threshold=50.0,
                critical_threshold=20.0,
                comparison_operator="less_than"
            ),
            MetricThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than"
            ),
            MetricThreshold(
                metric_type=MetricType.CACHE_HIT_RATE,
                warning_threshold=80.0,
                critical_threshold=60.0,
                comparison_operator="less_than"
            )
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
                logger.error(f"Error in metrics collection: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_alerts_loop(self):
        """Background loop for checking alerts"""
        while self.monitoring_status == MonitoringStatus.ACTIVE:
            try:
                await self._check_metric_thresholds()
                await asyncio.sleep(self.alert_check_interval)
            except Exception as e:
                logger.error(f"Error in alert checking: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _cleanup_old_metrics_loop(self):
        """Background loop for cleaning up old metrics"""
        while self.monitoring_status == MonitoringStatus.ACTIVE:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in metrics cleanup: {str(e)}")
                await asyncio.sleep(3600)  # Wait before retrying

    async def _collect_system_metrics(self):
        """Collect current system metrics"""
        timestamp = datetime.utcnow()

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.CPU_USAGE,
            value=cpu_percent,
            unit="percent"
        )
        self.metrics_store[MetricType.CPU_USAGE].append(cpu_metric)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.MEMORY_USAGE,
            value=memory.percent,
            unit="percent"
        )
        self.metrics_store[MetricType.MEMORY_USAGE].append(memory_metric)

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.DISK_USAGE,
            value=(disk.used / disk.total) * 100,
            unit="percent"
        )
        self.metrics_store[MetricType.DISK_USAGE].append(disk_metric)

        # Network I/O metrics
        network = psutil.net_io_counters()
        network_in_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.NETWORK_IO,
            value=network.bytes_recv,
            unit="bytes",
            tags={"direction": "inbound"}
        )
        network_out_metric = PerformanceMetric(
            timestamp=timestamp,
            metric_type=MetricType.NETWORK_IO,
            value=network.bytes_sent,
            unit="bytes",
            tags={"direction": "outbound"}
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
                unit="count"
            )
            self.metrics_store[MetricType.ACTIVE_USERS].append(connections_metric)

            # Database connections (simulated)
            db_connections = 50  # Would be actual DB connection count
            db_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.DATABASE_CONNECTIONS,
                value=db_connections,
                unit="count"
            )
            self.metrics_store[MetricType.DATABASE_CONNECTIONS].append(db_metric)

            # Response time (simulated)
            import random
            response_time = random.uniform(0.1, 2.0)
            response_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.RESPONSE_TIME,
                value=response_time,
                unit="seconds"
            )
            self.metrics_store[MetricType.RESPONSE_TIME].append(response_metric)

            # Throughput (simulated)
            throughput = random.uniform(20, 100)
            throughput_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.THROUGHPUT,
                value=throughput,
                unit="requests_per_second"
            )
            self.metrics_store[MetricType.THROUGHPUT].append(throughput_metric)

            # Error rate (simulated)
            error_rate = random.uniform(0.1, 2.0)
            error_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.ERROR_RATE,
                value=error_rate,
                unit="percent"
            )
            self.metrics_store[MetricType.ERROR_RATE].append(error_metric)

            # Cache hit rate (simulated)
            cache_hit_rate = random.uniform(70, 95)
            cache_metric = PerformanceMetric(
                timestamp=timestamp,
                metric_type=MetricType.CACHE_HIT_RATE,
                value=cache_hit_rate,
                unit="percent"
            )
            self.metrics_store[MetricType.CACHE_HIT_RATE].append(cache_metric)

        except Exception as e:
            logger.error(f"Error collecting application metrics: {str(e)}")

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
                        metric_type,
                        latest_value,
                        threshold,
                        avg_value
                    )
                else:
                    # Check if we should resolve existing alerts
                    await self._resolve_alert_if_resolved(metric_type, avg_value, threshold)

            except Exception as e:
                logger.error(f"Error checking thresholds for {metric_type.value}: {str(e)}")

    def _should_trigger_alert(self, threshold: MetricThreshold, value: float) -> bool:
        """Determine if alert should be triggered based on threshold"""
        if threshold.comparison_operator == "greater_than":
            return value >= threshold.critical_threshold
        elif threshold.comparison_operator == "less_than":
            return value <= threshold.critical_threshold
        else:
            return False

    async def _create_or_update_alert(
        self,
        metric_type: MetricType,
        current_value: float,
        threshold: MetricThreshold,
        avg_value: float
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
                    triggered_at=datetime.utcnow()
                )
                self.alerts[alert_id] = new_alert
                await self._send_alert_notification(new_alert)
        else:
            # Create new alert
            severity = AlertSeverity.WARNING if avg_value < threshold.critical_threshold else AlertSeverity.CRITICAL
            alert = Alert(
                id=alert_id,
                metric_type=metric_type,
                severity=severity,
                message=f"{metric_type.value} threshold exceeded",
                current_value=current_value,
                threshold=threshold.warning_threshold if severity == AlertSeverity.WARNING else threshold.critical_threshold,
                triggered_at=datetime.utcnow()
            )
            self.alerts[alert_id] = alert
            await self._send_alert_notification(alert)

    async def _resolve_alert_if_resolved(
        self,
        metric_type: MetricType,
        current_value: float,
        threshold: MetricThreshold
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
