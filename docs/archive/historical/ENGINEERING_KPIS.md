# Engineering KPIs: Performance & Reliability for PsychSync

## Executive Summary
This document defines comprehensive Key Performance Indicators (KPIs) to measure and improve the performance, reliability, and operational excellence of the PsychSync platform.

---

## Table of Contents
1. [KPI Framework Overview](#kpi-framework-overview)
2. [Performance KPIs](#performance-kpis)
3. [Reliability KPIs](#reliability-kpis)
4. [Quality KPIs](#quality-kpis)
5. [Operational KPIs](#operational-kpis)
6. [Business KPIs](#business-kpis)
7. [Measurement & Reporting](#measurement--reporting)
8. [Target Benchmarks](#target-benchmarks)

---

## KPI Framework Overview

### KPI Hierarchy
```
PsychSync Platform KPIs
├── Performance (How fast?)
│   ├── Response Time
│   ├── Throughput
│   └── Resource Utilization
├── Reliability (Is it up?)
│   ├── Availability
│   ├── Uptime
│   └── Error Rates
├── Quality (Is it good?)
│   ├── Bug Count
│   ├── Test Coverage
│   └── User Satisfaction
├── Operations (How efficient?)
│   ├── Deployment Frequency
│   ├── Lead Time
│   └── MTTR
└── Business (Does it matter?)
    ├── User Engagement
    ├── Feature Adoption
    └── Revenue Impact
```

### Data Collection Architecture
```python
# kpi/collector.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time

class KPICollector:
    """Centralized KPI collection system"""

    def __init__(self):
        # Performance metrics
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint', 'status']
        )

        self.request_size = Summary(
            'http_request_size_bytes',
            'HTTP request size',
            ['method', 'endpoint']
        )

        self.response_size = Summary(
            'http_response_size_bytes',
            'HTTP response size',
            ['method', 'endpoint']
        )

        # Reliability metrics
        self.requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )

        self.errors_total = Counter(
            'http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'error_type']
        )

        # Business metrics
        self.assessment_completions = Counter(
            'assessment_completions_total',
            'Total assessments completed',
            ['assessment_type']
        )

        self.active_users = Gauge(
            'active_users_total',
            'Current active users',
            ['timeframe']  # daily, weekly, monthly
        )

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).observe(duration)

        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()

        if status >= 400:
            self.errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type='http_error'
            ).inc()
```

---

## Performance KPIs

### 1. Response Time (Latency)

#### Definition
Time taken for the system to respond to a user request.

#### Targets
```yaml
API Endpoints:
  P50 (median): < 200ms
  P95: < 500ms
  P99: < 1000ms

Database Queries:
  P50: < 50ms
  P95: < 150ms
  P99: < 300ms

Frontend:
  First Contentful Paint (FCP): < 1.5s
  Largest Contentful Paint (LCP): < 2.5s
  First Input Delay (FID): < 100ms
  Cumulative Layout Shift (CLS): < 0.1
```

#### Measurement
```python
# Performance tracking middleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        # Record duration
        duration = time.time() - start_time
        kpi_collector.record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )

        # Add performance header
        response.headers["X-Response-Time"] = f"{duration*1000:.2f}ms"

        return response
```

---

### 2. Throughput

#### Definition
Number of requests processed per unit of time.

#### Targets
```yaml
Requests per Second:
  Normal: 100 req/s
  Peak: 500 req/s
  Burst: 1000 req/s (sustained for 1 minute)

Concurrent Users:
  Normal: 500 concurrent
  Peak: 2000 concurrent
  Maximum: 5000 concurrent
```

#### Measurement
```python
# Throughput monitoring
from prometheus_client import Gauge

current_requests = Gauge(
    'http_requests_in_progress',
    'Current requests being processed'
)

async def track_throughput():
    """Track requests per second"""
    while True:
        # Calculate RPS over last 60 seconds
        requests = await get_recent_requests(60)
        rps = len(requests) / 60

        kpi_collector.throughput_gauge.set(rps)

        await asyncio.sleep(10)
```

---

### 3. Resource Utilization

#### Definition
Percentage of system resources being used.

#### Targets
```yaml
CPU Usage:
  Target: 40-60%
  Warning: > 70%
  Critical: > 85%

Memory Usage:
  Target: < 70%
  Warning: > 80%
  Critical: > 90%

Disk Usage:
  Target: < 60%
  Warning: > 75%
  Critical: > 85%

Database Connections:
  Target: < 50% of max
  Warning: > 70% of max
  Critical: > 85% of max
```

#### Monitoring
```python
# Resource monitoring
import psutil

def get_system_metrics():
    """Collect system resource metrics"""
    cpu = {
        'percent': psutil.cpu_percent(interval=1),
        'count': psutil.cpu_count(),
    }

    memory = psutil.virtual_memory()
    memory_metrics = {
        'total': memory.total,
        'available': memory.available,
        'percent': memory.percent,
        'used': memory.used,
    }

    disk = psutil.disk_usage('/')
    disk_metrics = {
        'total': disk.total,
        'used': disk.used,
        'percent': disk.percent,
    }

    return {
        'cpu': cpu,
        'memory': memory_metrics,
        'disk': disk_metrics,
    }
```

---

## Reliability KPIs

### 4. Availability / Uptime

#### Definition
Percentage of time the system is operational and accessible.

#### Targets
```yaml
Monthly Uptime:
  Target: 99.9% (43.2 minutes downtime/month)
  Good: 99.5% (3.6 hours downtime/month)
  Minimum: 99% (7.2 hours downtime/month)

Yearly Uptime:
  Excellent: 99.99% (52 minutes downtime/year)
  Target: 99.95% (4.3 hours downtime/year)
  Industry Standard: 99.9% (8.7 hours downtime/year)

Scheduled Downtime:
  Maximum: 4 hours/month
  Notice: 48 hours in advance
  Window: 2 AM - 6 AM UTC
```

#### Measurement
```python
# Availability monitoring
from datetime import datetime, timedelta

class AvailabilityTracker:
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.outage_periods = []

    def record_outage(self, start: datetime, end: datetime):
        """Record an outage period"""
        duration = (end - start).total_seconds()
        self.outage_periods.append({
            'start': start,
            'end': end,
            'duration_seconds': duration,
        })

    def calculate_availability(self, period: timedelta) -> float:
        """Calculate availability percentage over period"""
        total_period = period.total_seconds()
        total_downtime = sum(
            p['duration_seconds']
            for p in self.outage_periods
            if p['start'] > datetime.utcnow() - period
        )

        uptime = total_period - total_downtime
        availability = (uptime / total_period) * 100

        return availability
```

---

### 5. Error Rate

#### Definition
Percentage of requests that result in errors.

#### Targets
```yaml
HTTP Error Rate:
  Excellent: < 0.1%
  Target: < 0.5%
  Warning: > 1%
  Critical: > 5%

4xx Errors (Client):
  Rate: < 5% of requests

5xx Errors (Server):
  Excellent: < 0.01%
  Target: < 0.1%
  Warning: > 0.5%
  Critical: > 1%

Database Errors:
  Rate: < 0.05% of queries
```

#### Monitoring
```python
# Error rate tracking
class ErrorTracker:
    def __init__(self):
        self.errors_5xx = Counter('errors_5xx_total', ['endpoint'])
        self.errors_4xx = Counter('errors_4xx_total', ['endpoint'])
        self.requests_total = Counter('requests_total', ['endpoint'])

    def record_error(self, status_code: int, endpoint: str):
        """Record an error"""
        if status_code >= 500:
            self.errors_5xx.labels(endpoint=endpoint).inc()
        elif status_code >= 400:
            self.errors_4xx.labels(endpoint=endpoint).inc()

        self.requests_total.labels(endpoint=endpoint).inc()

    def get_error_rate(self, endpoint: str = None) -> dict:
        """Calculate current error rates"""
        rates = {}
        endpoints = [endpoint] if endpoint else self.get_all_endpoints()

        for ep in endpoints:
            total = self.requests_total.labels(endpoint=ep)._value.get()
            errors = self.errors_5xx.labels(endpoint=ep)._value.get()

            if total and total > 0:
                rates[ep] = {
                    'error_rate': (errors / total) * 100 if errors else 0,
                    'total_requests': total,
                    'errors': errors,
                }

        return rates
```

---

### 6. Mean Time To Recovery (MTTR)

#### Definition
Average time to restore service after a failure.

#### Targets
```yaml
MTTR Targets:
  Excellent: < 15 minutes
  Good: < 30 minutes
  Acceptable: < 1 hour
  Poor: > 1 hour

Breakdown:
  Detection Time: < 5 minutes
  Response Time: < 10 minutes
  Resolution Time: < 15 minutes
```

#### Tracking
```python
# MTR tracking
from datetime import datetime

class IncidentTracker:
    def __init__(self):
        self.incidents = []

    def create_incident(self, severity: str, description: str):
        """Create a new incident"""
        incident = {
            'id': str(uuid.uuid4()),
            'severity': severity,
            'description': description,
            'created_at': datetime.utcnow(),
            'detected_at': None,
            'responded_at': None,
            'resolved_at': None,
        }
        self.incidents.append(incident)
        return incident

    def calculate_mttr(self, period: timedelta = timedelta(days=30)) -> float:
        """Calculate Mean Time To Recovery"""
        recent_incidents = [
            i for i in self.incidents
            if i['created_at'] > datetime.utcnow() - period
            and i['resolved_at']
        ]

        if not recent_incidents:
            return 0

        total_recovery_time = sum(
            (i['resolved_at'] - i['created_at']).total_seconds()
            for i in recent_incidents
        )

        return total_recovery_time / len(recent_incidents)
```

---

## Quality KPIs

### 7. Code Quality

#### Metrics
```yaml
Test Coverage:
  Unit Tests: > 80%
  Integration Tests: > 60%
  E2E Tests: Critical paths only

Code Complexity:
  Cyclomatic Complexity: < 10 per function
  File Length: < 500 lines
  Function Length: < 50 lines

Code Review:
  Approval Required: 1 reviewer
  Automated Checks: All must pass
  Review Time: < 24 hours

Linting:
  Errors: 0 (block commit)
  Warnings: < 10 per file
```

---

### 8. Defect Escape Rate

#### Definition
Percentage of bugs found in production vs. pre-production.

#### Targets
```yaml
Defect Escape Rate:
  Excellent: < 5%
  Target: < 10%
  Warning: > 15%

Bug Severity Distribution:
  Critical: 0 in production
  High: < 1 per release
  Medium: < 5 per release
  Low: < 10 per release
```

---

## Operational KPIs

### 9. Deployment Frequency

#### Definition
How often new code is deployed to production.

#### Targets
```yaml
Deployment Frequency:
  Elite: On-demand (multiple per day)
  High: Daily
  Medium: Weekly
  Low: Monthly

Current Target: 1-2 deployments per week

Success Rate:
  Target: > 95%
  Warning: < 90%
```

---

### 10. Lead Time for Changes

#### Definition
Time from code commit to deployment in production.

#### Targets
```yaml
Lead Time:
  Elite: < 1 hour
  High: < 1 day
  Medium: < 1 week
  Low: > 1 week

Breakdown:
  Code Review: < 4 hours
  Testing: < 1 hour
  Staging Deployment: < 30 minutes
  Production Deployment: < 15 minutes
```

---

### 11. Change Failure Rate

#### Definition
Percentage of deployments that result in degraded service or require hotfix.

#### Targets
```yaml
Change Failure Rate:
  Elite: < 15%
  High: < 20%
  Medium: < 30%
  Current Target: < 25%

Hotfix Rate:
  Target: < 5% of deployments
  Warning: > 10%
```

---

## Business KPIs

### 12. User Engagement

#### Metrics
```yaml
Daily Active Users (DAU):
  Growth: > 10% month-over-month
  Retention: > 40% after 30 days

Weekly Active Users (WAU):
  Growth: > 8% month-over-month

Monthly Active Users (MAU):
  Growth: > 5% month-over-month

Session Duration:
  Target: > 5 minutes
  Assessment completion: > 10 minutes
```

---

### 13. Feature Adoption

#### Metrics
```yaml
Feature Usage:
  Core features: > 80% of users
  New features: > 40% adoption in 30 days
  Deprecated features: < 5% usage

Assessment Completion Rate:
  Target: > 70%
  By type:
    MBTI: > 80%
    Big Five: > 75%
    Enneagram: > 70%
```

---

## Measurement & Reporting

### Dashboard Configuration (Grafana)

```json
{
  "dashboard": {
    "title": "PsychSync Engineering KPIs",
    "panels": [
      {
        "title": "Request Rate (RPS)",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_errors_total[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "type": "graph"
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds)",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "System Health",
        "targets": [
          {
            "expr": "up{job='psychsync-backend'}",
            "legendFormat": "Backend"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

### Automated Reporting

```python
# scripts/kpi_report.py
import asyncio
from datetime import datetime, timedelta

class KPIReporter:
    async def generate_weekly_report(self):
        """Generate weekly KPI report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        report = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
            },
            'performance': await self.get_performance_metrics(start_date, end_date),
            'reliability': await self.get_reliability_metrics(start_date, end_date),
            'quality': await self.get_quality_metrics(start_date, end_date),
            'operations': await self.get_operational_metrics(start_date, end_date),
        }

        # Generate HTML report
        html = self.render_html_report(report)

        # Send to Slack/Email
        await self.send_report(html)

        return report

    async def get_performance_metrics(self, start, end):
        """Collect performance metrics"""
        return {
            'avg_response_time_p95': await self.query_prometheus(
            f"histogram_quantile(0.95, http_request_duration_seconds)"
            f"[{start.timestamp()}:{end.timestamp()}]"
            ),
            'throughput_avg': await self.query_prometheus(
            f"avg(rate(http_requests_total[5m]))"
            ),
        }

    def render_html_report(self, report: dict) -> str:
        """Generate HTML report"""
        return f"""
        <html>
        <head><title>KPI Report - Week of {report['period']['start']}</title></head>
        <body>
            <h1>PsychSync Engineering KPI Report</h1>
            <p>Period: {report['period']['start']} to {report['period']['end']}</p>

            <h2>Performance</h2>
            <ul>
                <li>P95 Response Time: {report['performance']['avg_response_time_p95']:.2f}s</li>
                <li>Average Throughput: {report['performance']['throughput_avg']:.2f} req/s</li>
            </ul>

            <!-- More sections -->
        </body>
        </html>
        """
```

---

## Target Benchmarks

### Industry Comparisons

| KPI | PsychSync Target | Industry Average | Top Quartile |
|-----|-----------------|------------------|--------------|
| **Availability** | 99.9% | 99.5% | 99.99% |
| **P95 Latency** | 500ms | 1000ms | 200ms |
| **Error Rate** | 0.5% | 1% | 0.1% |
| **Deployment Frequency** | Weekly | Monthly | Daily |
| **Lead Time** | < 1 week | < 1 month | < 1 day |
| **MTTR** | < 30 min | < 1 hour | < 15 min |
| **Test Coverage** | 80% | 60% | 90% |

---

## KPI Alert Thresholds

### Alert Configuration

```yaml
# alerts.yml
groups:
  - name: performance
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency detected"
          description: "P95 latency is {{ $value }}s (target: < 1s)"

      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (target: < 1%)"

  - name: reliability
    rules:
      - alert: ServiceDown
        expr: up{job="psychsync-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "PsychSync backend is not responding"

      - alert: DatabaseReplicationLag
        expr: pg_replication_lag_seconds > 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database replication lag high"
          description: "Replication lag is {{ $value }}s"
```

---

## Summary

### Key Metrics to Watch Daily
1. **Availability**: Current uptime (99.9% target)
2. **Error Rate**: Percentage of failed requests (< 1%)
3. **P95 Latency**: 95th percentile response time (< 500ms)
4. **Throughput**: Requests per second
5. **Active Users**: Current active user count

### Key Metrics to Watch Weekly
1. **Deployment Frequency**: Deployments per week
2. **Lead Time**: Time from commit to production
3. **Change Failure Rate**: Failed deployments percentage
4. **MTTR**: Mean time to recovery
5. **Bug Count**: Open bugs by severity

### KPI Review Schedule
- **Real-time**: Alerts sent to Slack/PagerDuty
- **Daily**: Automated summary to Slack
- **Weekly**: Full report emailed to team
- **Monthly**: Engineering review meeting
- **Quarterly**: KPI targets reassessment

---

**Status**: ✅ Complete
**All Documents Generated**:
1. ✅ Security Headers Guide
2. ✅ Zero-Downtime Deployment Plan
3. ✅ Migration Rollback Strategy
4. ✅ Architecture Risk Analysis
5. ✅ Engineering KPIs
