# app/core/monitoring.py
"""
Comprehensive monitoring and observability for PsychSync
Includes performance metrics, request tracing, and health monitoring
"""

import time
import uuid
import json
import logging
import psutil
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.constants import Logging

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Individual request metrics"""
    request_id: str
    method: str
    path: str
    status_code: int
    duration: float
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_connections: int
    timestamp: datetime

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int
    idle_connections: int
    total_connections: int
    slow_queries: int
    cache_hit_ratio: float
    avg_query_time: float
    timestamp: datetime

class MetricsCollector:
    """Advanced metrics collection system"""

    def __init__(self):
        self.request_metrics: List[RequestMetrics] = []
        self.system_metrics: List[SystemMetrics] = []
        self.database_metrics: List[DatabaseMetrics] = []
        self.error_counts: Dict[str, int] = {}
        self.endpoint_stats: Dict[str, Dict[str, Any]] = {}
        self.max_metrics_history = 10000  # Keep last 10k metrics

    def record_request(self, metrics: RequestMetrics):
        """Record request metrics"""
        self.request_metrics.append(metrics)

        # Update endpoint statistics
        endpoint_key = f"{metrics.method} {metrics.path}"
        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {
                'count': 0,
                'total_duration': 0.0,
                'min_duration': float('inf'),
                'max_duration': 0.0,
                'error_count': 0,
                'status_codes': {}
            }

        stats = self.endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_duration'] += metrics.duration
        stats['min_duration'] = min(stats['min_duration'], metrics.duration)
        stats['max_duration'] = max(stats['max_duration'], metrics.duration)

        # Track status codes
        status_code = str(metrics.status_code)
        stats['status_codes'][status_code] = stats['status_codes'].get(status_code, 0) + 1

        # Track errors
        if metrics.status_code >= 400:
            stats['error_count'] += 1
            error_key = f"{metrics.status_code}_{metrics.path}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Cleanup old metrics
        self._cleanup_old_metrics()

    def record_system_metrics(self, metrics: SystemMetrics):
        """Record system metrics"""
        self.system_metrics.append(metrics)
        self._cleanup_old_metrics()

    def record_database_metrics(self, metrics: DatabaseMetrics):
        """Record database metrics"""
        self.database_metrics.append(metrics)
        self._cleanup_old_metrics()

    def _cleanup_old_metrics(self):
        """Remove old metrics to prevent memory leaks"""
        if len(self.request_metrics) > self.max_metrics_history:
            self.request_metrics = self.request_metrics[-self.max_metrics_history:]

        if len(self.system_metrics) > 1000:  # Keep fewer system metrics
            self.system_metrics = self.system_metrics[-1000:]

        if len(self.database_metrics) > 1000:
            self.database_metrics = self.database_metrics[-1000:]

    def get_request_stats(
        self,
        minutes: int = 60,
        path_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get request statistics for the last N minutes"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        filtered_metrics = [
            m for m in self.request_metrics
            if m.timestamp >= cutoff_time and
            (path_filter is None or path_filter in m.path)
        ]

        if not filtered_metrics:
            return {
                'total_requests': 0,
                'avg_duration': 0.0,
                'requests_per_minute': 0.0,
                'error_rate': 0.0,
                'status_codes': {}
            }

        total_requests = len(filtered_metrics)
        total_duration = sum(m.duration for m in filtered_metrics)
        error_count = sum(1 for m in filtered_metrics if m.status_code >= 400)

        # Calculate status code distribution
        status_codes = {}
        for metric in filtered_metrics:
            code = str(metric.status_code)
            status_codes[code] = status_codes.get(code, 0) + 1

        return {
            'total_requests': total_requests,
            'avg_duration': total_duration / total_requests,
            'requests_per_minute': total_requests / minutes,
            'error_rate': (error_count / total_requests * 100) if total_requests > 0 else 0,
            'status_codes': status_codes,
            'avg_response_time_95th': self._calculate_percentile(filtered_metrics, 95),
            'avg_response_time_99th': self._calculate_percentile(filtered_metrics, 99)
        }

    def _calculate_percentile(self, metrics: List[RequestMetrics], percentile: int) -> float:
        """Calculate response time percentile"""
        if not metrics:
            return 0.0

        durations = sorted(m.duration for m in metrics)
        index = int(len(durations) * percentile / 100)
        return durations[min(index, len(durations) - 1)]

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        recent_requests = self.get_request_stats(minutes=5)
        recent_system = self.system_metrics[-1] if self.system_metrics else None

        health_indicators = {
            'overall_status': 'healthy',
            'issues': []
        }

        # Check error rate
        if recent_requests['error_rate'] > 10:  # More than 10% errors
            health_indicators['overall_status'] = 'degraded'
            health_indicators['issues'].append(f"High error rate: {recent_requests['error_rate']:.1f}%")

        # Check response time
        if recent_requests['avg_duration'] > 2.0:  # Average > 2 seconds
            health_indicators['overall_status'] = 'degraded'
            health_indicators['issues'].append(f"Slow response time: {recent_requests['avg_duration']:.2f}s")

        # Check system resources
        if recent_system:
            if recent_system.cpu_percent > 80:
                health_indicators['overall_status'] = 'degraded'
                health_indicators['issues'].append(f"High CPU usage: {recent_system.cpu_percent:.1f}%")

            if recent_system.memory_percent > 85:
                health_indicators['overall_status'] = 'degraded'
                health_indicators['issues'].append(f"High memory usage: {recent_system.memory_percent:.1f}%")

        return {
            'status': health_indicators['overall_status'],
            'timestamp': datetime.utcnow().isoformat(),
            'indicators': health_indicators['issues'],
            'request_stats': recent_requests,
            'system_stats': asdict(recent_system) if recent_system else None
        }

# Global metrics collector
metrics_collector = MetricsCollector()

class RequestMonitoringMiddleware(BaseHTTPMiddleware):
    """Advanced request monitoring middleware"""

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Extract request information
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Add request ID to request state for other middleware
        request.state.request_id = request_id
        request.state.start_time = start_time

        # Log request start
        logger.info(
            f"Request started: {method} {path}",
            extra={
                'request_id': request_id,
                'method': method,
                'path': path,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Extract user ID if available
            user_id = getattr(request.state, 'user_id', None)

            # Record metrics
            request_metrics = RequestMetrics(
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration=duration,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                query_params=query_params
            )
            metrics_collector.record_request(request_metrics)

            # Add monitoring headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            # Log request completion
            log_level = "warning" if response.status_code >= 400 else "info"
            getattr(logger, log_level)(
                f"Request completed: {method} {path} - {response.status_code} in {duration:.3f}s",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'path': path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'user_id': user_id
                }
            )

            return response

        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time

            # Record error metrics
            error_metrics = RequestMetrics(
                request_id=request_id,
                method=method,
                path=path,
                status_code=500,
                duration=duration,
                timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                query_params=query_params,
                error_message=str(e)
            )
            metrics_collector.record_request(error_metrics)

            # Log error
            logger.error(
                f"Request failed: {method} {path} - {str(e)} in {duration:.3f}s",
                extra={
                    'request_id': request_id,
                    'method': method,
                    'path': path,
                    'error': str(e),
                    'duration': duration,
                    'exception_type': type(e).__name__
                },
                exc_info=True
            )

            # Re-raise the exception
            raise

async def collect_system_metrics():
    """Collect system performance metrics"""
    try:
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Network connections
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            connections = -1  # Permission denied

        system_metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_usage_percent=disk.percent,
            active_connections=connections,
            timestamp=datetime.utcnow()
        )

        metrics_collector.record_system_metrics(system_metrics)

    except Exception as e:
        logger.error(f"Error collecting system metrics: {str(e)}")

async def collect_database_metrics():
    """Collect database performance metrics"""
    try:
        from app.core.database_advanced import get_database_health, db_monitor

        db_health = await get_database_health()
        db_stats = db_monitor.get_stats()

        database_metrics = DatabaseMetrics(
            active_connections=db_health.get('active_connections', 0),
            idle_connections=db_health.get('idle_connections', 0),
            total_connections=db_health.get('connections', 0),
            slow_queries=db_health.get('slow_queries', 0),
            cache_hit_ratio=db_health.get('cache_hit_ratio', 0.0),
            avg_query_time=db_stats.get('avg_query_time', 0.0),
            timestamp=datetime.utcnow()
        )

        metrics_collector.record_database_metrics(database_metrics)

    except Exception as e:
        logger.error(f"Error collecting database metrics: {str(e)}")

async def metrics_background_task():
    """Background task for collecting metrics"""
    while True:
        try:
            await collect_system_metrics()
            await collect_database_metrics()
            await asyncio.sleep(30)  # Collect metrics every 30 seconds
        except Exception as e:
            logger.error(f"Error in metrics background task: {str(e)}")
            await asyncio.sleep(60)  # Wait longer on error

class AlertManager:
    """Advanced alerting system"""

    def __init__(self):
        self.alert_thresholds = {
            'error_rate': 10.0,  # percentage
            'response_time': 2.0,  # seconds
            'cpu_usage': 80.0,  # percentage
            'memory_usage': 85.0,  # percentage
            'disk_usage': 90.0,  # percentage
        }
        self.alert_cooldown = 300  # 5 minutes
        self.last_alerts: Dict[str, datetime] = {}

    def check_alerts(self, health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions"""
        alerts = []
        current_time = datetime.utcnow()

        # Check error rate
        request_stats = health_data.get('request_stats', {})
        error_rate = request_stats.get('error_rate', 0)
        if error_rate > self.alert_thresholds['error_rate']:
            if self._should_send_alert('error_rate', current_time):
                alerts.append({
                    'type': 'error_rate',
                    'severity': 'warning',
                    'message': f"High error rate: {error_rate:.1f}%",
                    'value': error_rate,
                    'threshold': self.alert_thresholds['error_rate']
                })
                self.last_alerts['error_rate'] = current_time

        # Check response time
        avg_duration = request_stats.get('avg_duration', 0)
        if avg_duration > self.alert_thresholds['response_time']:
            if self._should_send_alert('response_time', current_time):
                alerts.append({
                    'type': 'response_time',
                    'severity': 'warning',
                    'message': f"Slow response time: {avg_duration:.2f}s",
                    'value': avg_duration,
                    'threshold': self.alert_thresholds['response_time']
                })
                self.last_alerts['response_time'] = current_time

        # Check system resources
        system_stats = health_data.get('system_stats')
        if system_stats:
            # CPU usage
            cpu_percent = system_stats.get('cpu_percent', 0)
            if cpu_percent > self.alert_thresholds['cpu_usage']:
                if self._should_send_alert('cpu_usage', current_time):
                    alerts.append({
                        'type': 'cpu_usage',
                        'severity': 'critical',
                        'message': f"High CPU usage: {cpu_percent:.1f}%",
                        'value': cpu_percent,
                        'threshold': self.alert_thresholds['cpu_usage']
                    })
                    self.last_alerts['cpu_usage'] = current_time

            # Memory usage
            memory_percent = system_stats.get('memory_percent', 0)
            if memory_percent > self.alert_thresholds['memory_usage']:
                if self._should_send_alert('memory_usage', current_time):
                    alerts.append({
                        'type': 'memory_usage',
                        'severity': 'critical',
                        'message': f"High memory usage: {memory_percent:.1f}%",
                        'value': memory_percent,
                        'threshold': self.alert_thresholds['memory_usage']
                    })
                    self.last_alerts['memory_usage'] = current_time

        return alerts

    def _should_send_alert(self, alert_type: str, current_time: datetime) -> bool:
        """Check if alert should be sent (cooldown logic)"""
        last_alert = self.last_alerts.get(alert_type)
        if not last_alert:
            return True

        time_diff = (current_time - last_alert).total_seconds()
        return time_diff >= self.alert_cooldown

    def send_alert(self, alert: Dict[str, Any]):
        """Send alert (could integrate with Slack, email, etc.)"""
        logger.warning(
            f"ALERT: {alert['message']}",
            extra={
                'alert_type': alert['type'],
                'severity': alert['severity'],
                'value': alert['value'],
                'threshold': alert['threshold']
            }
        )

# Global alert manager
alert_manager = AlertManager()

@asynccontextmanager
async def lifespan_monitoring(app):
    """Lifespan manager for monitoring"""
    # Start background metrics collection
    metrics_task = asyncio.create_task(metrics_background_task())

    yield

    # Cleanup
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass

# Performance profiling utilities
class PerformanceProfiler:
    """Performance profiling for critical operations"""

    def __init__(self):
        self.profiles: Dict[str, List[float]] = {}

    def profile(self, operation_name: str):
        """Decorator for profiling operations"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_profile(operation_name, duration)
            return wrapper
        return decorator

    def record_profile(self, operation_name: str, duration: float):
        """Record performance profile"""
        if operation_name not in self.profiles:
            self.profiles[operation_name] = []
        self.profiles[operation_name].append(duration)

        # Keep only last 1000 measurements
        if len(self.profiles[operation_name]) > 1000:
            self.profiles[operation_name] = self.profiles[operation_name][-1000:]

    def get_profile_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get performance statistics for an operation"""
        if operation_name not in self.profiles:
            return {}

        durations = self.profiles[operation_name]
        return {
            'count': len(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p95_duration': sorted(durations)[int(len(durations) * 0.95)],
            'p99_duration': sorted(durations)[int(len(durations) * 0.99)]
        }

# Global profiler
profiler = PerformanceProfiler()