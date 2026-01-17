# PsychSync Enterprise Monitoring Setup Guide

This comprehensive guide covers the complete monitoring stack for the PsychSync platform, including Prometheus, Grafana, Sentry, and Datadog integration for production-ready observability.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Component Setup](#component-setup)
5. [Configuration](#configuration)
6. [Dashboards](#dashboards)
7. [Alerting](#alerting)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Maintenance](#maintenance)

## Overview

The PsychSync monitoring stack provides enterprise-grade observability with:

- **Metrics Collection**: Prometheus for system and application metrics
- **Visualization**: Grafana dashboards for real-time monitoring
- **Error Tracking**: Sentry for error aggregation and alerting
- **APM & Logs**: Datadog for application performance monitoring
- **Log Aggregation**: Loki and Promtail for centralized logging

### Monitoring Components

| Component | Purpose | Port | Access |
|-----------|---------|------|--------|
| Prometheus | Metrics collection and storage | 9090 | http://localhost:9090 |
| Grafana | Visualization and dashboards | 3001 | http://localhost:3001 |
| Alertmanager | Alert routing and management | 9093 | http://localhost:9093 |
| Sentry | Error tracking and alerting | 9000 | http://localhost:9000 |
| Datadog Agent | APM and log collection | 8126 | Internal |

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  React Frontend │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│  - Metrics      │    │  - Browser      │    │  - Query Stats  │
│  - Tracing      │    │  - Errors       │    │  - Connections  │
│  - Logging      │    │  - Performance │    │  - Replication  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Prometheus    │     Grafana     │         Sentry              │
│                 │                 │                             │
│  - Metrics      │  - Dashboards   │  - Error Aggregation       │
│  - Storage      │  - Alerts       │  - Issue Tracking          │
│  - Alerting     │  - Visualization│  - User Feedback           │
└─────────────────┴─────────────────┴─────────────────────────────┘
          │                      │
          ▼                      ▼
┌─────────────────┬─────────────────────────────────────────────────┐
│   Datadog Agent │                Alertmanager                    │
│                 │                                             │
│  - APM          │  - Multi-channel alerts                      │
│  - Logs         │  - Routing and grouping                     │
│  - Tracing      │  - Escalation policies                       │
└─────────────────┴─────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 8GB RAM for monitoring stack
- 50GB+ disk space for metrics retention
- Valid Datadog and Sentry API keys

### Environment Setup

1. **Create environment file:**
```bash
cp .env.example .env.monitoring
```

2. **Configure monitoring variables:**
```bash
# .env.monitoring
DATADOG_API_KEY=your_datadog_api_key
DATADOG_SITE=datadoghq.com
DD_ENV=production

SENTRY_SECRET_KEY=your_sentry_secret_key
SENTRY_DB_PASSWORD=your_sentry_db_password
SENTRY_EMAIL=alerts@psychsync.com

GRAFANA_PASSWORD=secure_grafana_password
GRAFANA_DOMAIN=monitoring.psychsync.com

POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=psychsync

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_smtp_user
SMTP_PASSWORD=your_smtp_password
```

3. **Launch monitoring stack:**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

4. **Verify services:**
```bash
# Check all services are running
docker-compose -f docker-compose.monitoring.yml ps

# Access dashboards
open http://localhost:9090  # Prometheus
open http://localhost:3001  # Grafana
open http://localhost:9000  # Sentry
```

## Component Setup

### 1. Prometheus Configuration

**Location**: `monitoring/prometheus/prometheus.yml`

**Key Features:**
- Multi-service metrics collection
- Advanced metric relabeling
- Remote write to Datadog
- High-cardinality label filtering

**Configuration:**
```yaml
# Global settings
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'psychsync-production'
    environment: 'production'

# Service discovery
scrape_configs:
  - job_name: 'psychsync-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
    scrape_interval: 15s
```

### 2. Grafana Setup

**Location**: `monitoring/grafana/dashboards/`

**Pre-built Dashboards:**
- `fastapi-overview.json` - API performance and health
- `postgresql-overview.json` - Database performance
- `react-frontend.json` - Frontend metrics
- `stripe-billing.json` - Billing and revenue

**Data Sources Configuration:**
```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true
}
```

### 3. Sentry Configuration

**FastAPI Integration**:
```python
# app/main.py
from app.monitoring.sentry_config import init_sentry

# Initialize Sentry
init_sentry()

# Add Sentry middleware
app.add_middleware(SentryTransactionMiddleware)
```

**React Integration**:
```typescript
// frontend/src/index.tsx
import { initSentry, PsychSyncErrorBoundary } from './monitoring/sentryConfig';

// Initialize Sentry
initSentry();

// Wrap app with error boundary
<PsychSyncErrorBoundary>
  <App />
</PsychSyncErrorBoundary>
```

### 4. Datadog Integration

**FastAPI Configuration**:
```python
# app/main.py
from app.monitoring.datadog_config import init_datadog

# Initialize Datadog
init_datadog()

# Add tracing middleware
app.add_middleware(DatadogTracingMiddleware)
```

**React Configuration**:
```typescript
// frontend/src/index.tsx
import { initDatadogRum } from '@datadog/browser-rum';

initDatadogRum({
  applicationId: 'your-app-id',
  clientToken: 'your-client-token',
  site: 'datadoghq.com',
  env: 'production',
  service: 'psychsync-frontend',
  sessionSampleRate: 100,
  trackInteractions: true,
});
```

## Configuration

### Application Metrics

**FastAPI Metrics (Prometheus format):**
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Number of active users')
```

**React Browser Metrics:**
```typescript
import { datadogRum } from '@datadog/browser-rum';

// Custom actions
datadogRum.addAction('assessment_completed', {
  assessment_type: 'big_five',
  duration: 120,
  score: 85
});
```

### Alert Configuration

**Prometheus Alerting Rules**:
```yaml
# monitoring/prometheus/alert_rules.yml
groups:
  - name: psychsync_api_alerts
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
          service: api
        annotations:
          summary: "High API response time detected"
          description: "95th percentile response time is {{ $value }}s"
```

**Alertmanager Configuration**:
```yaml
# monitoring/alertmanager/alertmanager.yml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#alerts'
        title: 'PsychSync Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### Log Configuration

**Structured Logging Format:**
```json
{
  "timestamp": "2023-12-01T10:30:00Z",
  "level": "INFO",
  "service": "psychsync-api",
  "trace_id": "12345678901234567890123456789012",
  "span_id": "1234567890123456",
  "message": "User authentication successful",
  "user_id": "user-123",
  "ip_address": "192.168.1.100"
}
```

## Dashboards

### 1. FastAPI Overview Dashboard

**Metrics Included:**
- Request rate and error rate
- Response time percentiles (P50, P95, P99)
- Active users and session metrics
- Memory usage and CPU utilization
- Database connection health

**Key Queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### 2. PostgreSQL Overview Dashboard

**Metrics Included:**
- Database size and growth rate
- Connection pool utilization
- Query performance statistics
- Index efficiency
- Lock wait times

**Key Queries:**
```promql
# Connection utilization
pg_stat_activity_count / pg_settings_max_connections

# Average query time
rate(pg_stat_statements_total_time_seconds[5m]) / rate(pg_stat_statements_calls[5m])

# Buffer hit ratio
rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))
```

### 3. React Frontend Dashboard

**Metrics Included:**
- Page view rates and bounce rates
- JavaScript error rates
- Page load performance
- User engagement scores
- Assessment completion rates

### 4. Stripe Billing Dashboard

**Metrics Included:**
- Revenue per minute/hour
- Payment success rates
- Active subscriptions and MRR
- Webhook processing times
- Revenue by subscription plan

## Alerting

### Alert Severities

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| Critical | Immediate | Call, SMS, Slack |
| Warning  | 15 minutes | Email, Slack |
| Info     | 1 hour       | Email only |

### Alert Channels

1. **Slack**: Primary notification channel
2. **Email**: Non-critical alerts and summaries
3. **PagerDuty**: Critical alerts requiring immediate response
4. **Webhooks**: Custom integrations and automation

### Alert Examples

**Critical: Service Down**
```yaml
- alert: ServiceDown
  expr: up{job=~"psychsync-(api|frontend|postgres)"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "{{ $labels.job }} service is down"
    description: "{{ $labels.job }} has been down for more than 1 minute"
```

**Warning: High Response Time**
```yaml
- alert: HighResponseTime
  expr: psychsync:api:p95_response_time:5m > 1.0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High API response time"
    description: "P95 response time is {{ $value }}s for more than 5 minutes"
```

**Business: Low Conversion Rate**
```yaml
- alert: LowConversionRate
  expr: psychsync:business:conversion_rate_registration_to_assessment:5m < 0.1
  for: 30m
  labels:
    severity: warning
  annotations:
    summary: "Low user conversion rate"
    description: "Only {{ $value | humanizePercentage }} of users complete assessments"
```

## Troubleshooting

### Common Issues

#### 1. Prometheus Not Collecting Metrics

**Symptoms:**
- No data in Grafana dashboards
- Target status showing "DOWN"

**Solutions:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify metrics endpoint
curl http://localhost:8000/metrics

# Check network connectivity
docker exec -it psychsync-prometheus ping api

# Review Prometheus logs
docker logs psychsync-prometheus
```

#### 2. High Memory Usage in Prometheus

**Symptoms:**
- Prometheus OOM kills
- Slow query performance

**Solutions:**
```yaml
# Adjust retention settings
storage:
  tsdb:
    retention.time: 15d
    retention.size: 10GB

# Implement recording rules
recording_rules.yml:
  - record: psychsync:api:request_rate:5m
    expr: rate(http_requests_total[5m])
```

#### 3. Sentry Not Receiving Events

**Symptoms:**
- No errors showing in Sentry
- Application not appearing in Sentry dashboard

**Solutions:**
```bash
# Test Sentry configuration
curl -X POST https://sentry.io/api/0/projects/your-org/your-project/envelope/ \
  -H 'Authorization: Bearer YOUR_DSN' \
  -H 'Content-Type: application/x-sentry-envelope' \
  -d '{"event_id":"test","dsn":"YOUR_DSN"}'

# Check network connectivity
nc -zv sentry.io 443

# Review application logs for Sentry errors
docker logs psychsync-api
```

#### 4. Grafana Dashboard Import Issues

**Symptoms:**
- Dashboard import fails
- Queries not returning data
- Time series showing "No data"

**Solutions:**
```bash
# Check Grafana data source configuration
curl http://admin:password@localhost:3001/api/datasources

# Verify Prometheus is accessible from Grafana
docker exec -it psychsync-grafana ping prometheus

# Test queries directly in Prometheus
curl 'http://localhost:9090/api/v1/query?query=up'
```

#### 5. Datadog Agent Not Reporting

**Symptoms:**
- No APM traces in Datadog
- Missing infrastructure metrics
- Logs not appearing

**Solutions:**
```bash
# Check Datadog agent status
docker exec psychsync-datadog-agent agent status

# Test agent connectivity
docker exec psychsync-datadog-agent agent flare

# Verify configuration
docker exec psychsync-datadog-agent cat /etc/datadog-agent/datadog.yaml
```

### Performance Tuning

#### Prometheus Optimization

```yaml
# Hardware recommendations
prometheus:
  resources:
    limits:
      memory: 4Gi
      cpu: 2
    requests:
      memory: 2Gi
      cpu: 1

# Configuration optimizations
global:
  scrape_interval: 30s          # Reduce scrape frequency
  evaluation_interval: 30s       # Reduce evaluation frequency

storage:
  tsdb:
    retention.time: 15d         # Reduce retention period
    wal-compression: true        # Enable WAL compression
```

#### Grafana Optimization

```ini
# grafana.ini customizations
[database]
max_open_conns = 10            # Limit database connections
max_idle_conns = 5

[server]
max_request_size = 1048576     # 1MB max request size
enable_gzip = true             # Enable compression
```

## Best Practices

### 1. Metric Design

**DO:**
- Use consistent naming conventions
- Include relevant labels for filtering
- Keep cardinality low
- Document metric purposes

**DON'T:**
- Include high-cardinality labels (user IDs, timestamps)
- Create metrics with vague names
- Mix units in the same metric
- Ignore metric retirement

### 2. Alert Design

**DO:**
- Set appropriate alert thresholds
- Include clear descriptions and runbooks
- Use severity levels appropriately
- Test alert pipelines regularly

**DON'T:**
- Alert on every fluctuation
- Create alert storms
- Ignore alert fatigue
- Skip testing alert escalation

### 3. Dashboard Design

**DO:**
- Create role-based dashboards
- Include performance SLAs
- Use consistent time ranges
- Add clear descriptions

**DON'T:**
- Overcomplicate dashboards
- Use too many panels
- Ignore color blindness
- Skip mobile optimization

### 4. Security

**DO:**
- Filter sensitive data
- Use authentication
- Rotate API keys regularly
- Audit access logs

**DON'T:**
- Expose unsecured endpoints
- Log personal information
- Share credentials
- Ignore security updates

## Maintenance

### Daily Tasks

- [ ] Review alert dashboards
- [ ] Check system resource usage
- [ ] Verify backup processes
- [ ] Monitor error rates

### Weekly Tasks

- [ ] Update dashboards as needed
- [ ] Review and tune alert thresholds
- [ ] Check metric retention policies
- [ ] Audit user access

### Monthly Tasks

- [ ] Update monitoring stack versions
- [ ] Review and optimize queries
- [ ] Clean up old alerts and dashboards
- [ ] Generate monitoring reports

### Quarterly Tasks

- [ ] Conduct performance reviews
- [ ] Update documentation
- [ ] Review security configurations
- [ ] Plan capacity upgrades

### Backup Procedures

```bash
# Prometheus data backup
docker exec psychsync-prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus

# Grafana configuration backup
docker exec psychsync-grafana tar -czf /tmp/grafana-backup.tar.gz /var/lib/grafana

# Database backup
docker exec psychsync-postgres pg_dump -U postgres psychsync > postgres-backup.sql
```

## Additional Resources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [Datadog Documentation](https://docs.datadoghq.com/)

### Communities
- [Prometheus Slack](https://prometheus.io/community/slack/)
- [Grafana Community](https://community.grafana.com/)
- [Sentry Community](https://forum.sentry.io/)
- [Datadog Community](https://community.datadoghq.com/)

### Training
- [Prometheus Training](https://prometheus.io/docs/introduction/overview/)
- [Grafana Tutorials](https://grafana.com/tutorials/)
- [Sentry Best Practices](https://docs.sentry.io/product/)
- [Datadog Best Practices](https://docs.datadoghq.com/getting_started/)

---

For additional support or questions, contact the DevOps team at devops@psychsync.com or create an issue in the monitoring repository.
