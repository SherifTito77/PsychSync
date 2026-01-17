"""
Application Performance Monitoring (APM) Service
Provides comprehensive application performance monitoring, tracing, and analytics
"""

from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
import json
import uuid
import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from functools import wraps
import psutil
import threading

from sqlalchemy.orm import Session
from fastapi import Request, Response

from app.core.config import settings

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
    tags: Dict[str, str] = field(default_factory=dict)
    dimensions: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    name: str
    metric_type: MetricType
    warning_threshold: Optional[float] = None
    critical_threshold: float
    comparison_operator: str = "greater_than"  # greater_than, less_than, equals
    evaluation_window: int = 300  # seconds
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)


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
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceSpan:
    """Distributed tracing span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    status: str = "ok"  # ok, error, timeout, cancelled
    service_name: str
    resource: str
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    baggage: Dict[str, str] = field(default_factory=dict)


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
    spans: List[TraceSpan] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class APMService:
    """Comprehensive Application Performance Monitoring service"""

    def __init__(self):
        self.metrics_store: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.thresholds: Dict[str, PerformanceThreshold] = {}
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.active_traces: Dict[str, List[TraceSpan]] = {}
        self.performance_profiles: Dict[str, PerformanceProfile] = {}
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
                tags={"endpoint": "*"}
            ),
            PerformanceThreshold(
                name="cpu_usage",
                metric_type=MetricType.GAUGE,
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison_operator="greater_than",
                tags={"host": "*"}
            ),
            PerformanceThreshold(
                name="memory_usage",
                metric_type=MetricType.GAUGE,
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator="greater_than",
                tags={"host": "*"}
            ),
            PerformanceThreshold(
                name="error_rate",
                metric_type=MetricType.GAUGE,
                warning_threshold=5.0,  # 5%
                critical_threshold=10.0,  # 10%
                comparison_operator="greater_than",
                tags={"service": "*"}
            ),
            PerformanceThreshold(
                name="database_query_time",
                metric_type=MetricType.TIMER,
                warning_threshold=500.0,  # 500ms
                critical_threshold=2000.0,  # 2 seconds
                comparison_operator="greater_than",
                tags={"query_type": "*"}
            ),
            PerformanceThreshold(
                name="queue_length",
                metric_type=MetricType.GAUGE,
                warning_threshold=100,
                critical_threshold=500,
                comparison_operator="greater_than",
                tags={"queue": "*"}
            )
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
                logger.error(f"Error collecting system metrics: {str(e)}")
                await asyncio.sleep(60)

    async def _check_thresholds_loop(self):
        """Background loop for checking performance thresholds"""
        while self.collection_enabled:
            try:
                await self._check_all_thresholds()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error checking thresholds: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_old_data_loop(self):
        """Background loop for cleaning up old data"""
        while self.collection_enabled:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Clean every hour
            except Exception as e:
                logger.error(f"Error cleaning up old data: {str(e)}")
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
            tags={"host": "localhost", "service": "psychsync-api"}
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        await self.record_metric(
            name="memory_usage",
            metric_type=MetricType.GAUGE,
            value=memory.percent,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api"}
        )

        # Disk metrics
        disk = psutil.disk_usage('/')
        await self.record_metric(
            name="disk_usage",
            metric_type=MetricType.GAUGE,
            value=(disk.used / disk.total) * 100,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api"}
        )

        # Network metrics
        network = psutil.net_io_counters()
        await self.record_metric(
            name="network_bytes_sent",
            metric_type=MetricType.COUNTER,
            value=network.bytes_sent,
            unit="bytes",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api", "direction": "outbound"}
        )

        await self.record_metric(
            name="network_bytes_received",
            metric_type=MetricType.COUNTER,
            value=network.bytes_recv,
            unit="bytes",
            timestamp=timestamp,
            tags={"host": "localhost", "service": "psychsync-api", "direction": "inbound"}
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
                cutoff_time = datetime.utcnow() - timedelta(seconds=threshold.evaluation_window)
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
                        time_diff = (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds()
                        if time_diff > 0:
                            value_diff = recent_metrics[-1].value - recent_metrics[0].value
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
                    elif threshold.warning_threshold and current_value >= threshold.warning_threshold:
                        should_alert = True
                        alert_level = "warning"
                elif threshold.comparison_operator == "less_than":
                    if current_value <= threshold.critical_threshold:
                        should_alert = True
                        alert_level = "critical"
                    elif threshold.warning_threshold and current_value <= threshold.warning_threshold:
                        should_alert = True
                        alert_level = "warning"

                if should_alert:
                    await self._create_or_update_alert(
                        threshold_name,
                        current_value,
                        threshold,
                        alert_level
                    )
                else:
                    # Check if existing alert should be resolved
                    await self._resolve_alert_if_resolved(
                        threshold_name,
                        current_value,
                        threshold
                    )

            except Exception as e:
                logger.error(f"Error checking threshold {threshold_name}: {str(e)}")

    async def _create_or_update_alert(
        self,
        threshold_name: str,
        current_value: float,
        threshold: PerformanceThreshold,
        alert_level: str
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
                    threshold=threshold.critical_threshold if alert_level == "critical" else threshold.warning_threshold,
                    triggered_at=datetime.utcnow(),
                    tags=threshold.tags
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
                threshold=threshold.critical_threshold if alert_level == "critical" else threshold.warning_threshold,
                triggered_at=datetime.utcnow(),
                tags=threshold.tags
            )
            self.alerts[alert_id] = alert
            await self._send_alert_notification(alert)

    def _get_alert_type(self, threshold_name: str) -> AlertType:
        """Get alert type based on threshold name"""
        if "response_time" in threshold_name or "duration" in threshold_name:
            return AlertType.SLOW_REQUEST
        elif "error_rate" in threshold_name:
            return AlertType.HIGH_ERROR_RATE
        elif "memory" in threshold_name:
            return AlertType.MEMORY_USAGE
        elif "cpu" in threshold_name:
            return AlertType.CPU_USAGE
        elif "database" in threshold_name:
            return AlertType.DATABASE_SLOW
        elif "queue" in threshold_name:
            return AlertType.QUEUE_BACKLOG
        else:
            return AlertType.EXTERNAL_API_SLOW

    async def _resolve_alert_if_resolved(
        self,
        threshold_name: str,
        current_value: float,
        threshold: PerformanceThreshold
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
            if threshold.warning_threshold and current_value < threshold.warning_threshold:
                is_normal = True
        elif threshold.comparison_operator == "less_than":
            if threshold.warning_threshold and current_value > threshold.warning_threshold:
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
