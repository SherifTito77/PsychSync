# PsychSync Monitoring & Alerting Setup Guide

**Version:** 1.0.0
**Last Updated:** November 22, 2025

## 🎯 Overview

This guide provides comprehensive monitoring and alerting configuration for PsychSync production deployment using industry-standard tools: Prometheus, Grafana, AlertManager, and custom monitoring solutions.

## 📊 Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Prometheus    │    │   AlertManager  │
│   (FastAPI)     │────│   (Metrics DB)  │────│   (Alerting)    │
│   /metrics      │    │   + Scraping    │    │   + Routing     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Node Exporter │    │   Grafana       │    │   Slack/Email   │
│   (System Met.) │    │   (Dashboards)  │    │   (Notifications)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DB/Redis Exp. │    │   Loki (Logs)   │    │   PagerDuty     │
│   (DB Metrics)  │    │   (Log Agg.)    │    │   (Escalation)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Installation & Setup

### 1. Docker Compose Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    container_name: psychsync-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.0.0
    container_name: psychsync-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_grafana_password
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:v0.25.0
    container_name: psychsync-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:v1.6.0
    container_name: psychsync-node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      - monitoring

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.12.0
    container_name: psychsync-postgres-exporter
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://psychsync_user:password@localhost:5432/psychsync?sslmode=require
    networks:
      - monitoring

  redis-exporter:
    image: oliver006/redis_exporter:v1.45.0
    container_name: psychsync-redis-exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://localhost:6379
      - REDIS_PASSWORD=your_redis_password
    networks:
      - monitoring

  loki:
    image: grafana/loki:2.8.0
    container_name: psychsync-loki
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki:/etc/loki
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:2.8.0
    container_name: psychsync-promtail
    ports:
      - "9080:9080"
    volumes:
      - ./monitoring/promtail:/etc/promtail
      - /var/log:/var/log:ro
      - /opt/psychsync/logs:/opt/psychsync/logs:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
  loki_data:

networks:
  monitoring:
    driver: bridge
```

### 2. Prometheus Configuration

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'psychsync-production'
    replica: 'prometheus-1'

rule_files:
  - "rules/*.yml"
  - "alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Application Metrics
  - job_name: 'psychsync-app'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    scrape_timeout: 5s

  # System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  # PostgreSQL Metrics
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis Metrics
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # Prometheus Self-Monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # AlertManager
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']

  # Blackbox Probing
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - https://app.psychsync.com/health
        - https://api.psychsync.com/api/v1/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # Kubernetes Service Discovery (if using K8s)
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
```

### 3. AlertManager Configuration

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.psychsync.com:587'
  smtp_from: 'alerts@psychsync.com'
  smtp_auth_username: 'alerts@psychsync.com'
  smtp_auth_password: 'your_smtp_password'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    # Critical alerts - immediate
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 5m

    # Security alerts - immediate
    - match:
        severity: security
      receiver: 'security-alerts'
      group_wait: 0s
      repeat_interval: 1h

    # Warning alerts - 5 minute delay
    - match:
        severity: warning
      receiver: 'warning-alerts'
      group_wait: 5m
      repeat_interval: 4h

    # Business hours only for info alerts
    - match:
        severity: info
      receiver: 'info-alerts'
      active_time_intervals:
        - business-hours

inhibit_rules:
  # Inhibit info alerts if critical alert is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'info'
    equal: ['alertname', 'instance']

time_intervals:
  - name: business-hours
    time_intervals:
      - times:
          - start_time: '09:00'
            end_time: '17:00'
        weekdays: ['monday:friday']

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@psychsync.com'
        subject: '[PsychSync] {{ .GroupLabels.alertname }} Alert'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          {{ end }}

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@psychsync.com,security@psychsync.com'
        subject: '[CRITICAL] PsychSync Production Alert'
        body: |
          🚨 CRITICAL ALERT 🚨

          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Severity: {{ .Labels.severity }}
          Instance: {{ .Labels.instance }}
          Started: {{ .StartsAt.Format "2006-01-02 15:04:05" }}
          {{ end }}

          🔧 Immediate action required!
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-critical'
        title: '🚨 Critical PsychSync Alert'
        text: |
          {{ range .Alerts }}
          {{ .Annotations.summary }}
          {{ .Annotations.description }}
          {{ end }}

  - name: 'security-alerts'
    email_configs:
      - to: 'security@psychsync.com,compliance@psychsync.com'
        subject: '[SECURITY] PsychSync Security Alert'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#security-alerts'
        title: '🔒 Security Alert'

  - name: 'warning-alerts'
    email_configs:
      - to: 'devops@psychsync.com'
        subject: '[WARNING] PsychSync Alert'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-warning'

  - name: 'info-alerts'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-info'
```

### 4. Application Metrics Implementation

```python
# app/monitoring/metrics.py
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Business Metrics
REQUEST_COUNT = Counter(
    'psychsync_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'psychsync_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_USERS = Gauge(
    'psychsync_active_users_total',
    'Number of active users'
)

DATABASE_CONNECTIONS = Gauge(
    'psychsync_database_connections_active',
    'Active database connections'
)

REDIS_CONNECTIONS = Gauge(
    'psychsync_redis_connections_active',
    'Active Redis connections'
)

# Security Metrics
SECURITY_EVENTS = Counter(
    'psychsync_security_events_total',
    'Security events',
    ['event_type', 'severity']
)

FAILED_LOGIN_ATTEMPTS = Counter(
    'psychsync_failed_login_attempts_total',
    'Failed login attempts',
    ['ip_address', 'user_agent']
)

SUCCESSFUL_LOGINS = Counter(
    'psychsync_successful_logins_total',
    'Successful logins',
    ['user_id']

# Business Metrics
ASSESSMENTS_COMPLETED = Counter(
    'psychsync_assessments_completed_total',
    'Completed assessments',
    ['assessment_type']
)

USER_REGISTRATIONS = Counter(
    'psychsync_user_registrations_total',
    'New user registrations'
)

# Performance Metrics
CPU_USAGE = Gauge('psychsync_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('psychsync_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('psychsync_disk_usage_percent', 'Disk usage percentage')

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

async def update_system_metrics():
    """Update system resource metrics"""
    try:
        CPU_USAGE.set(psutil.cpu_percent())
        memory = psutil.virtual_memory()
        MEMORY_USAGE.set(memory.percent)
        disk = psutil.disk_usage('/')
        DISK_USAGE.set(disk.percent)
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")

async def get_metrics():
    """Generate Prometheus metrics"""
    await update_system_metrics()
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

### 5. Custom Alerts Configuration

```yaml
# monitoring/alerts/psychsync.yml
groups:
  - name: psychsync.application
    rules:
      # Application Health
      - alert: ApplicationDown
        expr: up{job="psychsync-app"} == 0
        for: 1m
        labels:
          severity: critical
          service: psychsync
        annotations:
          summary: "PsychSync application is down"
          description: "PsychSync application has been down for more than 1 minute"

      # High Error Rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(psychsync_http_requests_total{status_code=~"5.."}[5m])) /
            sum(rate(psychsync_http_requests_total[5m]))
          ) > 0.05
        for: 2m
        labels:
          severity: critical
          service: psychsync
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High Response Time
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(psychsync_http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
          service: psychsync
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # Low Request Rate
      - alert: LowRequestRate
        expr: |
          sum(rate(psychsync_http_requests_total[5m])) < 0.1
        for: 10m
        labels:
          severity: warning
          service: psychsync
        annotations:
          summary: "Low request rate detected"
          description: "Request rate is {{ $value }} requests/second"

  - name: psychsync.security
    rules:
      # Security Events
      - alert: SecurityEventDetected
        expr: increase(psychsync_security_events_total[1m]) > 5
        for: 0m
        labels:
          severity: security
          service: psychsync
        annotations:
          summary: "Security events detected"
          description: "{{ $value }} security events in the last minute"

      # Failed Login Attempts
      - alert: BruteForceAttack
        expr: |
          sum(rate(psychsync_failed_login_attempts_total[1m])) > 10
        for: 2m
        labels:
          severity: security
          service: psychsync
        annotations:
          summary: "Potential brute force attack detected"
          description: "{{ $value }} failed login attempts per second"

  - name: psychsync.infrastructure
    rules:
      # Database Connections
      - alert: DatabaseConnectionsHigh
        expr: psychsync_database_connections_active > 80
        for: 5m
        labels:
          severity: warning
          service: database
        annotations:
          summary: "High database connections"
          description: "{{ $value }} active database connections"

      # Redis Connections
      - alert: RedisConnectionsHigh
        expr: psychsync_redis_connections_active > 50
        for: 5m
        labels:
          severity: warning
          service: redis
        annotations:
          summary: "High Redis connections"
          description: "{{ $value }} active Redis connections"

      # System Resources
      - alert: HighCPUUsage
        expr: psychsync_cpu_usage_percent > 85
        for: 10m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}%"

      - alert: HighMemoryUsage
        expr: psychsync_memory_usage_percent > 90
        for: 5m
        labels:
          severity: critical
          service: system
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}%"

      - alert: HighDiskUsage
        expr: psychsync_disk_usage_percent > 85
        for: 10m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "High disk usage"
          description: "Disk usage is {{ $value }}%"

  - name: psychsync.business
    rules:
      # Business Metrics
      - alert: NoNewUsers
        expr: increase(psychsync_user_registrations_total[1h]) == 0
        for: 2h
        labels:
          severity: warning
          service: business
        annotations:
          summary: "No new user registrations"
          description: "No new user registrations in the last hour"

      - alert: NoAssessmentsCompleted
        expr: increase(psychsync_assessments_completed_total[1h]) == 0
        for: 4h
        labels:
          severity: info
          service: business
        annotations:
          summary: "No assessments completed"
          description: "No assessments completed in the last hour"
```

### 6. Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "id": null,
    "title": "PsychSync Production Dashboard",
    "tags": ["psychsync", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(psychsync_http_requests_total[5m])) by (method)",
            "legendFormat": "{{method}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(psychsync_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(psychsync_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(psychsync_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sum(rate(psychsync_http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(psychsync_http_requests_total[5m]))"
          }
        ],
        "valueMaps": [
          {
            "value": null,
            "text": "N/A"
          }
        ],
        "thresholds": "0.01,0.05,0.1"
      },
      {
        "id": 4,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "psychsync_active_users_total"
          }
        ]
      },
      {
        "id": 5,
        "title": "System Resources",
        "type": "graph",
        "targets": [
          {
            "expr": "psychsync_cpu_usage_percent",
            "legendFormat": "CPU"
          },
          {
            "expr": "psychsync_memory_usage_percent",
            "legendFormat": "Memory"
          },
          {
            "expr": "psychsync_disk_usage_percent",
            "legendFormat": "Disk"
          }
        ],
        "yAxes": [
          {
            "label": "Percentage",
            "max": 100,
            "min": 0
          }
        ]
      },
      {
        "id": 6,
        "title": "Security Events",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(psychsync_security_events_total[5m])) by (event_type)",
            "legendFormat": "{{event_type}}"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 7. Log Configuration (Loki & Promtail)

```yaml
# monitoring/promtail/config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Application Logs
  - job_name: psychsync-app
    static_configs:
      - targets:
          - localhost
        labels:
          job: psychsync
          __path__: /opt/psychsync/logs/*.log

    pipeline_stages:
      - json:
          expressions:
            level: level
            message: message
            timestamp: timestamp
            module: module
            user_id: user_id

      - timestamp:
          format: RFC3339
          source: timestamp

      - labels:
          level:
          module:
          user_id:

  # Nginx Logs
  - job_name: nginx
    static_configs:
      - targets:
          - localhost
        labels:
          job: nginx
          __path__: /var/log/nginx/*.log

    pipeline_stages:
      - regex:
          expression: '(?P<remote_addr>[\w\.]+) - (?P<remote_user>[\w-]+) \[(?P<time_local>.+)\] "(?P<method>\w+) (?P<path>.+?) (?P<protocol>\w+/\d\.\d+)" (?P<status_code>\d{3}) (?P<body_bytes_sent>\d+) "(?P<referer>.+?)" "(?P<user_agent>.+?)"'

      - labels:
          method:
          status_code:
          remote_addr:

  # System Logs
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: system
          __path__: /var/log/syslog

    pipeline_stages:
      - regex:
          expression: '(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+) (?P<hostname>\w+) (?P<process>\w+)(\[(?P<pid>\d+)\])?: (?P<message>.*)'

      - timestamp:
          format: RFC3339
          source: timestamp
```

```yaml
# monitoring/loki/local-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

## 🔧 Setup Commands

### Start Monitoring Stack
```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps

# Check logs
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### Test Metrics Collection
```bash
# Test application metrics endpoint
curl http://localhost:8000/metrics

# Test Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test AlertManager
curl http://localhost:9093/api/v1/alerts
```

### Setup Grafana Dashboards
```bash
# Import dashboards using API
curl -X POST \
  http://admin:secure_grafana_password@localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @monitoring/grafana/dashboards/psychsync.json

# Add Prometheus data source
curl -X POST \
  http://admin:secure_grafana_password@localhost:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

## 📱 Monitoring Best Practices

### 1. Alerting Strategy
- **Critical Alerts:** Immediate notification (within 1 minute)
- **Warning Alerts:** 5-minute delay to prevent alert fatigue
- **Info Alerts:** Business hours only
- **Escalation:** PagerDuty for critical alerts after 15 minutes

### 2. Dashboard Strategy
- **Overview Dashboard:** High-level KPIs and health
- **Technical Dashboard:** Detailed metrics for engineers
- **Business Dashboard:** User-facing metrics
- **Security Dashboard:** Security events and compliance

### 3. Log Strategy
- **Structured Logging:** JSON format for all application logs
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Retention:** 30 days for application logs, 90 days for security logs
- **Log Aggregation:** Centralized in Loki with alerts for patterns

### 4. Performance Monitoring
- **SLA Targets:** 99.9% uptime, <500ms response time
- **Resource Utilization:** <80% CPU, <90% memory, <85% disk
- **Database Performance:** <1 second query time, <100 connections
- **Cache Performance:** >90% hit rate

This comprehensive monitoring setup provides complete visibility into PsychSync production operations with proactive alerting and detailed observability.
