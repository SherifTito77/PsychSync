#!/usr/bin/env python3
"""
PsychSync Monitoring & Observability System
Comprehensive monitoring, alerting, and observability automation

Implements:
- Application performance monitoring (APM)
- Infrastructure monitoring setup
- Log aggregation and analysis
- Alert rule configuration
- Dashboard creation
- Health check automation
- Metrics collection
- Error tracking and analysis
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import psutil
import requests
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import logging

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    disk_available_gb: float
    network_io: Dict[str, float]
    process_count: int
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """Application performance metrics"""
    timestamp: datetime
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    requests_per_second: float
    error_rate: float
    active_connections: int
    database_connections: int
    cache_hit_rate: float
    queue_depth: int

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    condition: str  # >, <, >=, <=, ==
    threshold: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    duration_minutes: int
    enabled: bool
    description: str
    notification_channels: List[str]

@dataclass
class HealthCheckResult:
    """Health check result"""
    service_name: str
    status: str  # HEALTHY, DEGRADED, UNHEALTHY
    response_time: float
    last_check: datetime
    checks_performed: List[Dict[str, Any]]
    issues: List[str]

@dataclass
class LogAnalysisResult:
    """Log analysis result"""
    timestamp_range: Tuple[datetime, datetime]
    total_lines: int
    error_count: int
    warning_count: int
    critical_errors: List[Dict[str, Any]]
    error_patterns: Dict[str, int]
    top_errors: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]

@dataclass
class DashboardConfiguration:
    """Dashboard configuration"""
    name: str
    description: str
    panels: List[Dict[str, Any]]
    refresh_interval: int  # seconds
    time_range: str  # 1h, 6h, 24h, 7d

class MonitoringObservabilitySystem:
    """
    Comprehensive monitoring and observability system
    """

    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path(__file__).parent.parent)
        self.monitoring_config = {}
        self.alert_rules = []
        self.health_checks = []
        self.dashboard_configs = []

    async def setup_monitoring_infrastructure(self) -> Dict[str, Any]:
        """Set up monitoring infrastructure components"""
        print("🔧 Setting up monitoring infrastructure...")

        setup_results = {
            'prometheus': {'installed': False, 'issues': []},
            'grafana': {'installed': False, 'issues': []},
            'elasticsearch': {'installed': False, 'issues': []},
            'kibana': {'installed': False, 'issues': []},
            'alertmanager': {'installed': False, 'issues': []},
            'jaeger': {'installed': False, 'issues': []}  # For distributed tracing
        }

        # Check and setup Prometheus
        setup_results['prometheus'] = await self._setup_prometheus()

        # Check and setup Grafana
        setup_results['grafana'] = await self._setup_grafana()

        # Check and setup ELK stack for logging
        setup_results['elasticsearch'] = await self._setup_elasticsearch()
        setup_results['kibana'] = await self._setup_kibana()

        # Setup Alertmanager
        setup_results['alertmanager'] = await self._setup_alertmanager()

        # Setup Jaeger for distributed tracing
        setup_results['jaeger'] = await self._setup_jaeger()

        return setup_results

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_available_gb = disk.free / (1024**3)

            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # Process count
            process_count = len(psutil.pids())

            # Load average (Unix-like systems)
            try:
                load_average = list(psutil.getloadavg())
            except AttributeError:
                load_average = [0.0, 0.0, 0.0]  # Windows fallback

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_usage_percent,
                disk_available_gb=disk_available_gb,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_gb=0.0,
                disk_usage_percent=0.0,
                disk_available_gb=0.0,
                network_io={},
                process_count=0,
                load_average=[0.0, 0.0, 0.0]
            )

    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application performance metrics"""
        try:
            # Get metrics from application endpoints
            metrics_url = "http://localhost:8000/metrics"

            # Default values
            app_metrics = ApplicationMetrics(
                timestamp=datetime.now(),
                response_time_p50=0.0,
                response_time_p95=0.0,
                response_time_p99=0.0,
                requests_per_second=0.0,
                error_rate=0.0,
                active_connections=0,
                database_connections=0,
                cache_hit_rate=0.0,
                queue_depth=0
            )

            try:
                response = requests.get(metrics_url, timeout=10)
                if response.status_code == 200:
                    # Parse Prometheus metrics (simplified)
                    metrics_text = response.text
                    app_metrics = self._parse_prometheus_metrics(metrics_text)
            except requests.RequestException:
                # Application not available, use defaults
                pass

            return app_metrics

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now(),
                response_time_p50=0.0,
                response_time_p95=0.0,
                response_time_p99=0.0,
                requests_per_second=0.0,
                error_rate=0.0,
                active_connections=0,
                database_connections=0,
                cache_hit_rate=0.0,
                queue_depth=0
            )

    async def configure_alert_rules(self) -> List[AlertRule]:
        """Configure monitoring alert rules"""
        print("🚨 Configuring alert rules...")

        alert_rules = [
            # System alerts
            AlertRule(
                name="High CPU Usage",
                metric="cpu_percent",
                condition=">",
                threshold=80.0,
                severity="HIGH",
                duration_minutes=5,
                enabled=True,
                description="CPU usage is above 80% for 5 minutes",
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="High Memory Usage",
                metric="memory_percent",
                condition=">",
                threshold=85.0,
                severity="HIGH",
                duration_minutes=5,
                enabled=True,
                description="Memory usage is above 85% for 5 minutes",
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="Low Disk Space",
                metric="disk_usage_percent",
                condition=">",
                threshold=90.0,
                severity="CRITICAL",
                duration_minutes=2,
                enabled=True,
                description="Disk usage is above 90%",
                notification_channels=["email", "slack", "pagerduty"]
            ),

            # Application alerts
            AlertRule(
                name="High Error Rate",
                metric="error_rate",
                condition=">",
                threshold=5.0,
                severity="HIGH",
                duration_minutes=3,
                enabled=True,
                description="Application error rate is above 5%",
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                name="Slow Response Time",
                metric="response_time_p95",
                condition=">",
                threshold=1000.0,
                severity="MEDIUM",
                duration_minutes=5,
                enabled=True,
                description="95th percentile response time is above 1 second",
                notification_channels=["slack"]
            ),
            AlertRule(
                name="Service Unavailable",
                metric="service_health",
                condition="==",
                threshold=0.0,
                severity="CRITICAL",
                duration_minutes=1,
                enabled=True,
                description="Service health check is failing",
                notification_channels=["email", "slack", "pagerduty"]
            ),

            # Database alerts
            AlertRule(
                name="Database Connection Issues",
                metric="database_connections",
                condition=">",
                threshold=80.0,
                severity="MEDIUM",
                duration_minutes=3,
                enabled=True,
                description="Database connections are above 80% of pool",
                notification_channels=["slack"]
            ),
            AlertRule(
                name="Low Cache Hit Rate",
                metric="cache_hit_rate",
                condition="<",
                threshold=70.0,
                severity="LOW",
                duration_minutes=10,
                enabled=True,
                description="Cache hit rate is below 70%",
                notification_channels=["slack"]
            )
        ]

        self.alert_rules = alert_rules
        return alert_rules

    async def setup_health_checks(self) -> List[Dict[str, Any]]:
        """Set up application health checks"""
        print("💓 Setting up health checks...")

        health_checks = [
            {
                'name': 'Application Health',
                'endpoint': 'http://localhost:8000/api/v1/health',
                'method': 'GET',
                'expected_status': 200,
                'timeout_seconds': 10,
                'check_interval': 30,
                'description': 'Main application health endpoint'
            },
            {
                'name': 'Database Health',
                'endpoint': 'http://localhost:8000/api/v1/health/db',
                'method': 'GET',
                'expected_status': 200,
                'timeout_seconds': 5,
                'check_interval': 60,
                'description': 'Database connectivity check'
            },
            {
                'name': 'Redis Health',
                'endpoint': 'http://localhost:8000/api/v1/health/redis',
                'method': 'GET',
                'expected_status': 200,
                'timeout_seconds': 5,
                'check_interval': 60,
                'description': 'Redis connectivity check'
            },
            {
                'name': 'External API Health',
                'endpoint': 'https://api.example.com/health',
                'method': 'GET',
                'expected_status': 200,
                'timeout_seconds': 10,
                'check_interval': 120,
                'description': 'External API dependency check'
            }
        ]

        self.health_checks = health_checks
        return health_checks

    async def run_health_checks(self) -> List[HealthCheckResult]:
        """Run all configured health checks"""
        print("💓 Running health checks...")

        health_results = []

        for check in self.health_checks:
            try:
                result = await self._execute_health_check(check)
                health_results.append(result)
                status_icon = '✅' if result.status == 'HEALTHY' else '⚠️' if result.status == 'DEGRADED' else '❌'
                print(f"  {status_icon} {result.service_name}: {result.status} ({result.response_time:.2f}s)")
            except Exception as e:
                logger.error(f"Health check failed for {check['name']}: {e}")
                health_results.append(HealthCheckResult(
                    service_name=check['name'],
                    status='UNHEALTHY',
                    response_time=0.0,
                    last_check=datetime.now(),
                    checks_performed=[],
                    issues=[f"Health check failed: {e}"]
                ))

        return health_results

    async def analyze_logs(self, time_window_hours: int = 24) -> LogAnalysisResult:
        """Analyze application logs for issues and patterns"""
        print(f"📋 Analyzing logs for the last {time_window_hours} hours...")

        try:
            # Find log files
            log_files = self._find_log_files()

            total_lines = 0
            error_count = 0
            warning_count = 0
            critical_errors = []
            error_patterns = {}
            top_errors = []
            performance_issues = []

            end_time = datetime.now()
            start_time = end_time - timedelta(hours=time_window_hours)

            for log_file in log_files:
                try:
                    file_analysis = await self._analyze_log_file(log_file, start_time, end_time)
                    total_lines += file_analysis['total_lines']
                    error_count += file_analysis['error_count']
                    warning_count += file_analysis['warning_count']
                    critical_errors.extend(file_analysis['critical_errors'])

                    # Merge error patterns
                    for pattern, count in file_analysis['error_patterns'].items():
                        error_patterns[pattern] = error_patterns.get(pattern, 0) + count

                    top_errors.extend(file_analysis['top_errors'])
                    performance_issues.extend(file_analysis['performance_issues'])

                except Exception as e:
                    logger.error(f"Error analyzing log file {log_file}: {e}")

            # Sort and limit results
            critical_errors.sort(key=lambda x: x.get('severity', 'MEDIUM'), reverse=True)
            top_errors.sort(key=lambda x: x.get('count', 0), reverse=True)
            performance_issues.sort(key=lambda x: x.get('impact', 'LOW'), reverse=True)

            return LogAnalysisResult(
                timestamp_range=(start_time, end_time),
                total_lines=total_lines,
                error_count=error_count,
                warning_count=warning_count,
                critical_errors=critical_errors[:10],
                error_patterns=error_patterns,
                top_errors=top_errors[:20],
                performance_issues=performance_issues[:10]
            )

        except Exception as e:
            logger.error(f"Error in log analysis: {e}")
            return LogAnalysisResult(
                timestamp_range=(datetime.now(), datetime.now()),
                total_lines=0,
                error_count=0,
                warning_count=0,
                critical_errors=[],
                error_patterns={},
                top_errors=[],
                performance_issues=[]
            )

    async def create_dashboards(self) -> List[DashboardConfiguration]:
        """Create monitoring dashboards"""
        print("📊 Creating monitoring dashboards...")

        dashboards = []

        # System Overview Dashboard
        system_dashboard = DashboardConfiguration(
            name="System Overview",
            description="Overall system health and performance",
            panels=[
                {
                    'title': 'CPU Usage',
                    'type': 'stat',
                    'metrics': ['cpu_percent'],
                    'unit': 'percent'
                },
                {
                    'title': 'Memory Usage',
                    'type': 'stat',
                    'metrics': ['memory_percent'],
                    'unit': 'percent'
                },
                {
                    'title': 'Disk Usage',
                    'type': 'stat',
                    'metrics': ['disk_usage_percent'],
                    'unit': 'percent'
                },
                {
                    'title': 'Network I/O',
                    'type': 'graph',
                    'metrics': ['network_io_bytes_sent', 'network_io_bytes_recv'],
                    'unit': 'bytes'
                }
            ],
            refresh_interval=30,
            time_range='1h'
        )
        dashboards.append(system_dashboard)

        # Application Performance Dashboard
        app_dashboard = DashboardConfiguration(
            name="Application Performance",
            description="Application performance metrics and health",
            panels=[
                {
                    'title': 'Response Time Percentiles',
                    'type': 'graph',
                    'metrics': ['response_time_p50', 'response_time_p95', 'response_time_p99'],
                    'unit': 'milliseconds'
                },
                {
                    'title': 'Request Rate',
                    'type': 'graph',
                    'metrics': ['requests_per_second'],
                    'unit': 'requests/sec'
                },
                {
                    'title': 'Error Rate',
                    'type': 'graph',
                    'metrics': ['error_rate'],
                    'unit': 'percent'
                },
                {
                    'title': 'Active Connections',
                    'type': 'stat',
                    'metrics': ['active_connections'],
                    'unit': 'count'
                }
            ],
            refresh_interval=15,
            time_range='1h'
        )
        dashboards.append(app_dashboard)

        # Database Dashboard
        db_dashboard = DashboardConfiguration(
            name="Database Performance",
            description="Database performance and connection metrics",
            panels=[
                {
                    'title': 'Database Connections',
                    'type': 'stat',
                    'metrics': ['database_connections'],
                    'unit': 'count'
                },
                {
                    'title': 'Query Performance',
                    'type': 'graph',
                    'metrics': ['avg_query_time', 'slow_queries'],
                    'unit': 'milliseconds'
                },
                {
                    'title': 'Cache Hit Rate',
                    'type': 'stat',
                    'metrics': ['cache_hit_rate'],
                    'unit': 'percent'
                }
            ],
            refresh_interval=60,
            time_range='6h'
        )
        dashboards.append(db_dashboard)

        # Error Monitoring Dashboard
        error_dashboard = DashboardConfiguration(
            name="Error Monitoring",
            description="Application errors and issues",
            panels=[
                {
                    'title': 'Error Rate',
                    'type': 'graph',
                    'metrics': ['error_rate'],
                    'unit': 'percent'
                },
                {
                    'title': 'Top Errors',
                    'type': 'table',
                    'metrics': ['error_counts'],
                    'unit': 'count'
                },
                {
                    'title': 'Critical Errors',
                    'type': 'table',
                    'metrics': ['critical_error_count'],
                    'unit': 'count'
                }
            ],
            refresh_interval=30,
            time_range='24h'
        )
        dashboards.append(error_dashboard)

        self.dashboard_configs = dashboards
        return dashboards

    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring and observability report"""
        print("📊 Generating monitoring and observability report...")

        # Collect current metrics
        system_metrics = await self.collect_system_metrics()
        app_metrics = await self.collect_application_metrics()
        health_results = await self.run_health_checks()
        log_analysis = await self.analyze_logs()

        # Setup monitoring components
        infrastructure_setup = await self.setup_monitoring_infrastructure()
        alert_rules = await self.configure_alert_rules()
        dashboards = await self.create_dashboards()

        # Calculate health scores
        system_health_score = self._calculate_system_health_score(system_metrics)
        app_health_score = self._calculate_app_health_score(app_metrics)
        log_health_score = self._calculate_log_health_score(log_analysis)
        infrastructure_health_score = self._calculate_infrastructure_health_score(infrastructure_setup)

        overall_score = (system_health_score + app_health_score + log_health_score + infrastructure_health_score) / 4

        # Generate recommendations
        recommendations = []
        critical_issues = []

        # System recommendations
        if system_metrics.cpu_percent > 80:
            critical_issues.append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
            recommendations.append("Investigate high CPU usage and consider scaling")

        if system_metrics.memory_percent > 85:
            critical_issues.append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
            recommendations.append("Monitor memory usage and optimize memory-intensive processes")

        if system_metrics.disk_usage_percent > 90:
            critical_issues.append(f"Low disk space: {system_metrics.disk_usage_percent:.1f}% used")
            recommendations.append("Clean up disk space and monitor storage growth")

        # Application recommendations
        if app_metrics.error_rate > 5:
            critical_issues.append(f"High error rate: {app_metrics.error_rate:.1f}%")
            recommendations.append("Investigate and fix application errors")

        if app_metrics.response_time_p95 > 1000:
            recommendations.append(f"Optimize slow responses: P95 at {app_metrics.response_time_p95:.1f}ms")

        # Health check recommendations
        unhealthy_services = [h for h in health_results if h.status != 'HEALTHY']
        if unhealthy_services:
            critical_issues.append(f"{len(unhealthy_services)} services are unhealthy")
            recommendations.append("Address unhealthy services immediately")

        # Log analysis recommendations
        if log_analysis.critical_errors:
            recommendations.append(f"Address {len(log_analysis.critical_errors)} critical errors from logs")

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health_score': overall_score,
            'health_grade': self._get_health_grade(overall_score),
            'component_scores': {
                'system': system_health_score,
                'application': app_health_score,
                'logs': log_health_score,
                'infrastructure': infrastructure_health_score
            },
            'current_metrics': {
                'system': asdict(system_metrics),
                'application': asdict(app_metrics)
            },
            'health_checks': [asdict(h) for h in health_results],
            'log_analysis': asdict(log_analysis),
            'infrastructure_setup': infrastructure_setup,
            'alert_rules_count': len([r for r in alert_rules if r.enabled]),
            'dashboards_count': len(dashboards),
            'critical_issues': critical_issues,
            'recommendations': recommendations,
            'monitoring_complete': overall_score >= 80 and len(critical_issues) == 0
        }

    async def _setup_prometheus(self) -> Dict[str, Any]:
        """Setup Prometheus monitoring"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Prometheus is running
            response = requests.get("http://localhost:9090/-/healthy", timeout=5)
            if response.status_code == 200:
                result['installed'] = True
            else:
                result['issues'].append("Prometheus is not healthy")
        except requests.RequestException:
            result['issues'].append("Prometheus is not accessible at localhost:9090")

        return result

    async def _setup_grafana(self) -> Dict[str, Any]:
        """Setup Grafana dashboards"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Grafana is running
            response = requests.get("http://localhost:3000/api/health", timeout=5)
            if response.status_code == 200:
                result['installed'] = True
            else:
                result['issues'].append("Grafana is not healthy")
        except requests.RequestException:
            result['issues'].append("Grafana is not accessible at localhost:3000")

        return result

    async def _setup_elasticsearch(self) -> Dict[str, Any]:
        """Setup Elasticsearch for log aggregation"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Elasticsearch is running
            response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                if health.get('status') in ['yellow', 'green']:
                    result['installed'] = True
                else:
                    result['issues'].append(f"Elasticsearch cluster status: {health.get('status')}")
            else:
                result['issues'].append("Elasticsearch is not healthy")
        except requests.RequestException:
            result['issues'].append("Elasticsearch is not accessible at localhost:9200")

        return result

    async def _setup_kibana(self) -> Dict[str, Any]:
        """Setup Kibana for log visualization"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Kibana is running
            response = requests.get("http://localhost:5601/api/status", timeout=5)
            if response.status_code == 200:
                result['installed'] = True
            else:
                result['issues'].append("Kibana is not healthy")
        except requests.RequestException:
            result['issues'].append("Kibana is not accessible at localhost:5601")

        return result

    async def _setup_alertmanager(self) -> Dict[str, Any]:
        """Setup Alertmanager for alerting"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Alertmanager is running
            response = requests.get("http://localhost:9093/-/healthy", timeout=5)
            if response.status_code == 200:
                result['installed'] = True
            else:
                result['issues'].append("Alertmanager is not healthy")
        except requests.RequestException:
            result['issues'].append("Alertmanager is not accessible at localhost:9093")

        return result

    async def _setup_jaeger(self) -> Dict[str, Any]:
        """Setup Jaeger for distributed tracing"""
        result = {'installed': False, 'issues': []}

        try:
            # Check if Jaeger is running
            response = requests.get("http://localhost:16686/api/services", timeout=5)
            if response.status_code == 200:
                result['installed'] = True
            else:
                result['issues'].append("Jaeger is not healthy")
        except requests.RequestException:
            result['issues'].append("Jaeger is not accessible at localhost:16686")

        return result

    def _parse_prometheus_metrics(self, metrics_text: str) -> ApplicationMetrics:
        """Parse Prometheus metrics text"""
        app_metrics = ApplicationMetrics(
            timestamp=datetime.now(),
            response_time_p50=0.0,
            response_time_p95=0.0,
            response_time_p99=0.0,
            requests_per_second=0.0,
            error_rate=0.0,
            active_connections=0,
            database_connections=0,
            cache_hit_rate=0.0,
            queue_depth=0
        )

        lines = metrics_text.split('\n')
        for line in lines:
            if line.startswith('http_request_duration_seconds_bucket{le="0.5"}'):
                # P50 approximation
                value = float(line.split()[-1])
                app_metrics.response_time_p50 = value * 1000  # Convert to ms
            elif line.startswith('http_request_duration_seconds_bucket{le="0.95"}'):
                # P95 approximation
                value = float(line.split()[-1])
                app_metrics.response_time_p95 = value * 1000
            elif line.startswith('http_request_duration_seconds_bucket{le="0.99"}'):
                # P99 approximation
                value = float(line.split()[-1])
                app_metrics.response_time_p99 = value * 1000
            elif line.startswith('http_requests_total'):
                value = float(line.split()[-1])
                # Calculate RPS (simplified)
                app_metrics.requests_per_second = value / 3600  # Rough estimate
            elif line.startswith('http_requests_total{status=~"5.."}'):
                value = float(line.split()[-1])
                app_metrics.error_rate = value * 100  # Convert to percentage

        return app_metrics

    async def _execute_health_check(self, check: Dict[str, Any]) -> HealthCheckResult:
        """Execute a single health check"""
        start_time = time.time()

        try:
            response = requests.request(
                method=check['method'],
                url=check['endpoint'],
                timeout=check['timeout_seconds']
            )

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Determine status
            if response.status_code == check['expected_status']:
                status = 'HEALTHY'
            elif response.status_code >= 500:
                status = 'UNHEALTHY'
            else:
                status = 'DEGRADED'

            # Check specific health indicators
            checks_performed = [
                {
                    'name': 'HTTP Status',
                    'expected': check['expected_status'],
                    'actual': response.status_code,
                    'passed': response.status_code == check['expected_status']
                },
                {
                    'name': 'Response Time',
                    'expected': f"< {check['timeout_seconds']}s",
                    'actual': f"{response_time:.2f}ms",
                    'passed': response_time < (check['timeout_seconds'] * 1000)
                }
            ]

            # Parse response body if JSON
            issues = []
            try:
                response_data = response.json()
                if isinstance(response_data, dict):
                    if 'status' in response_data and response_data['status'] != 'healthy':
                        issues.append(f"Service reports status: {response_data['status']}")
                    if 'checks' in response_data:
                        for check_name, check_result in response_data['checks'].items():
                            if not check_result.get('passed', True):
                                issues.append(f"{check_name}: {check_result.get('message', 'Failed')}")
            except:
                pass

            if status == 'UNHEALTHY' and not issues:
                issues.append(f"HTTP {response.status_code} response")

            return HealthCheckResult(
                service_name=check['name'],
                status=status,
                response_time=response_time,
                last_check=datetime.now(),
                checks_performed=checks_performed,
                issues=issues
            )

        except requests.RequestException as e:
            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                service_name=check['name'],
                status='UNHEALTHY',
                response_time=response_time,
                last_check=datetime.now(),
                checks_performed=[],
                issues=[f"Request failed: {str(e)}"]
            )

    def _find_log_files(self) -> List[str]:
        """Find application log files"""
        log_files = []
        log_directories = [
            'logs/',
            'app/logs/',
            '/var/log/psychsync/',
            os.path.join(self.project_root, 'logs')
        ]

        for log_dir in log_directories:
            if os.path.exists(log_dir):
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(('.log', '.out', '.err')):
                            log_files.append(os.path.join(root, file))

        return log_files

    async def _analyze_log_file(self, log_file: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze a single log file"""
        analysis = {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'critical_errors': [],
            'error_patterns': {},
            'top_errors': [],
            'performance_issues': []
        }

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    analysis['total_lines'] += 1

                    # Simple timestamp checking (would need better parsing in production)
                    if self._is_log_line_in_range(line, start_time, end_time):
                        # Count error levels
                        if any(level in line.upper() for level in ['ERROR', 'FATAL', 'CRITICAL']):
                            analysis['error_count'] += 1

                            # Extract error patterns
                            error_pattern = self._extract_error_pattern(line)
                            if error_pattern:
                                analysis['error_patterns'][error_pattern] = analysis['error_patterns'].get(error_pattern, 0) + 1

                            # Check for critical errors
                            if any(critical in line.upper() for critical in ['CRITICAL', 'FATAL', 'OUT_OF_MEMORY']):
                                analysis['critical_errors'].append({
                                    'timestamp': datetime.now().isoformat(),
                                    'message': line.strip(),
                                    'severity': 'CRITICAL'
                                })

                        elif any(level in line.upper() for level in ['WARNING', 'WARN']):
                            analysis['warning_count'] += 1

                        # Check for performance issues
                        if any(perf in line.upper() for perf in ['TIMEOUT', 'SLOW_QUERY', 'HIGH_LATENCY']):
                            analysis['performance_issues'].append({
                                'timestamp': datetime.now().isoformat(),
                                'message': line.strip(),
                                'impact': 'MEDIUM'
                            })

        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")

        # Convert error patterns to top errors
        for pattern, count in analysis['error_patterns'].items():
            analysis['top_errors'].append({
                'pattern': pattern,
                'count': count
            })

        return analysis

    def _is_log_line_in_range(self, line: str, start_time: datetime, end_time: datetime) -> bool:
        """Check if log line timestamp is within range"""
        # Simplified timestamp checking - would need proper log parser in production
        return True

    def _extract_error_pattern(self, line: str) -> Optional[str]:
        """Extract error pattern from log line"""
        # Simple pattern extraction - would need more sophisticated parsing
        if 'Exception' in line:
            return 'Exception'
        elif 'Connection' in line and 'failed' in line.lower():
            return 'Connection Error'
        elif 'Timeout' in line:
            return 'Timeout'
        elif '404' in line or 'Not Found' in line:
            return '404 Error'
        elif '500' in line or 'Internal Server Error' in line:
            return '500 Error'
        return None

    def _calculate_system_health_score(self, metrics: SystemMetrics) -> float:
        """Calculate system health score"""
        score = 100

        # CPU score (20% weight)
        if metrics.cpu_percent > 90:
            score -= 20
        elif metrics.cpu_percent > 80:
            score -= 15
        elif metrics.cpu_percent > 70:
            score -= 10

        # Memory score (20% weight)
        if metrics.memory_percent > 90:
            score -= 20
        elif metrics.memory_percent > 85:
            score -= 15
        elif metrics.memory_percent > 75:
            score -= 10

        # Disk score (20% weight)
        if metrics.disk_usage_percent > 95:
            score -= 20
        elif metrics.disk_usage_percent > 90:
            score -= 15
        elif metrics.disk_usage_percent > 80:
            score -= 10

        # Load average score (20% weight)
        if metrics.load_average[0] > 2.0:  # 1-minute load average
            score -= 20
        elif metrics.load_average[0] > 1.5:
            score -= 10

        # Network I/O score (20% weight) - simplified
        # Would need baseline comparison in production

        return max(0, min(100, score))

    def _calculate_app_health_score(self, metrics: ApplicationMetrics) -> float:
        """Calculate application health score"""
        score = 100

        # Error rate (30% weight)
        if metrics.error_rate > 10:
            score -= 30
        elif metrics.error_rate > 5:
            score -= 20
        elif metrics.error_rate > 1:
            score -= 10

        # Response time (30% weight)
        if metrics.response_time_p95 > 2000:  # 2 seconds
            score -= 30
        elif metrics.response_time_p95 > 1000:  # 1 second
            score -= 20
        elif metrics.response_time_p95 > 500:  # 500ms
            score -= 10

        # Request rate (20% weight) - simplified
        if metrics.requests_per_second < 1:
            score -= 20
        elif metrics.requests_per_second < 10:
            score -= 10

        # Cache hit rate (20% weight)
        if metrics.cache_hit_rate < 50:
            score -= 20
        elif metrics.cache_hit_rate < 70:
            score -= 10
        elif metrics.cache_hit_rate < 85:
            score -= 5

        return max(0, min(100, score))

    def _calculate_log_health_score(self, analysis: LogAnalysisResult) -> float:
        """Calculate log health score"""
        if analysis.total_lines == 0:
            return 100  # No logs to analyze

        score = 100

        # Error rate score (50% weight)
        error_rate = (analysis.error_count / analysis.total_lines) * 100
        if error_rate > 10:
            score -= 50
        elif error_rate > 5:
            score -= 30
        elif error_rate > 1:
            score -= 15

        # Critical errors score (30% weight)
        if len(analysis.critical_errors) > 10:
            score -= 30
        elif len(analysis.critical_errors) > 5:
            score -= 20
        elif len(analysis.critical_errors) > 0:
            score -= 10

        # Performance issues score (20% weight)
        if len(analysis.performance_issues) > 20:
            score -= 20
        elif len(analysis.performance_issues) > 10:
            score -= 10
        elif len(analysis.performance_issues) > 5:
            score -= 5

        return max(0, min(100, score))

    def _calculate_infrastructure_health_score(self, setup: Dict[str, Any]) -> float:
        """Calculate infrastructure health score"""
        total_components = len(setup)
        healthy_components = sum(1 for component in setup.values() if component['installed'])

        return (healthy_components / total_components) * 100 if total_components > 0 else 0

    def _get_health_grade(self, score: float) -> str:
        """Get health grade from score"""
        if score >= 95:
            return 'EXCELLENT'
        elif score >= 85:
            return 'GOOD'
        elif score >= 70:
            return 'FAIR'
        elif score >= 50:
            return 'POOR'
        else:
            return 'CRITICAL'

async def main():
    """Main execution function"""
    print("🚀 PsychSync Monitoring & Observability System")
    print("=" * 50)

    monitoring_system = MonitoringObservabilitySystem()

    try:
        # Generate comprehensive monitoring report
        report = await monitoring_system.generate_monitoring_report()

        # Display results
        print(f"\n📊 Overall System Health Score: {report['overall_health_score']:.1f}/100")
        print(f"📈 Health Grade: {report['health_grade']}")

        print(f"\n📊 Component Health Scores:")
        for component, score in report['component_scores'].items():
            print(f"   {component.capitalize()}: {score:.1f}/100")

        # Display current metrics
        print(f"\n💻 Current System Metrics:")
        sys_metrics = report['current_metrics']['system']
        print(f"   CPU Usage: {sys_metrics['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {sys_metrics['memory_percent']:.1f}%")
        print(f"   Disk Usage: {sys_metrics['disk_usage_percent']:.1f}%")
        print(f"   Available Disk: {sys_metrics['disk_available_gb']:.1f}GB")

        print(f"\n⚡ Current Application Metrics:")
        app_metrics = report['current_metrics']['application']
        print(f"   P95 Response Time: {app_metrics['response_time_p95']:.1f}ms")
        print(f"   Error Rate: {app_metrics['error_rate']:.1f}%")
        print(f"   Requests/sec: {app_metrics['requests_per_second']:.1f}")
        print(f"   Cache Hit Rate: {app_metrics['cache_hit_rate']:.1f}%")

        # Display health check results
        print(f"\n💓 Health Check Results:")
        for health in report['health_checks']:
            status_icon = '✅' if health['status'] == 'HEALTHY' else '⚠️' if health['status'] == 'DEGRADED' else '❌'
            print(f"   {status_icon} {health['service_name']}: {health['status']} ({health['response_time']:.1f}ms)")

        # Display infrastructure status
        print(f"\n🏗️  Infrastructure Status:")
        infra = report['infrastructure_setup']
        for component, status in infra.items():
            status_icon = '✅' if status['installed'] else '❌'
            print(f"   {status_icon} {component.capitalize()}: {'Installed' if status['installed'] else 'Not Available'}")

        # Display log analysis summary
        log_analysis = report['log_analysis']
        if log_analysis['total_lines'] > 0:
            print(f"\n📋 Log Analysis Summary:")
            print(f"   Total Lines: {log_analysis['total_lines']}")
            print(f"   Errors: {log_analysis['error_count']}")
            print(f"   Warnings: {log_analysis['warning_count']}")
            print(f"   Critical Errors: {len(log_analysis['critical_errors'])}")

        # Display alert and dashboard setup
        print(f"\n🚨 Alert Configuration:")
        print(f"   Active Alert Rules: {report['alert_rules_count']}")
        print(f"   Monitoring Dashboards: {report['dashboards_count']}")

        # Display critical issues
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues:")
            for issue in report['critical_issues']:
                print(f"   • {issue}")

        # Display recommendations
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")

        # Overall assessment
        if report['monitoring_complete']:
            print(f"\n✅ Monitoring setup is COMPLETE and system is HEALTHY")
            exit_code = 0
        else:
            print(f"\n⚠️  Monitoring setup has issues that need attention")
            exit_code = 0  # Still success, but with warnings

        # Save detailed report
        report_file = "monitoring_observability_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return exit_code

    except Exception as e:
        logger.error(f"Error during monitoring setup: {e}")
        print(f"❌ Monitoring setup failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
