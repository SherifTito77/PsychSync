# Real-Time Log Analytics Dashboard Architecture
## Live Observability for PsychSync

**Date:** 2026-03-10
**Version:** 1.0.0
**Priority:** P1 (High Priority Enhancement)

---

## Executive Summary

This document provides a comprehensive design for implementing a **real-time log analytics dashboard** using Grafana + Loki stack. This solution enables live log monitoring, instant issue detection, and data-driven operational decisions for PsychSync's production environment.

### Key Objectives

1. **Real-Time Log Streaming** - Sub-second log visibility
2. **Live Metrics Dashboard** - Instant visualization of system health
3. **Custom Alert Rules** - Proactive incident notification
4. **Log Query Interface** - Powerful log search with Loki Query Language (LogQL)
5. **Multi-Tenant Support** - Organization/team-level visibility
6. **Cost-Effective** - Efficient log storage and indexing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PsychSync Services                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ FastAPI  │  │  Celery  │  │  Redis   │  │ PostgreSQL│      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
│                         │                                      │
│                         ▼                                      │
│                  ┌──────────────┐                                │
│                  │ Loki Promtail │                                │
│                  │  (Log Shipper)│                                │
│                  └──────┬───────┘                                │
└─────────────────────────┼────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Storage & Query Layer                             │
│                     ┌─────────────┐                                │
│                     │     Loki     │                                │
│                     │             │                                │
│                     │  - Log Storage│                               │
│                     │  - Indexing   │                               │
│                     │  - Query Engine│                               │
│                     └─────┬───────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Metrics Collection Layer                             │
│                     ┌─────────────┐                                │
│                     │  Prometheus  │                                │
│                     │             │                                │
│                     │  - Metrics   │                               │
│                     │  - Alerts    │                               │
│                     │  - Rules     │                               │
│                     └─────┬───────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Visualization & Alerting                            │
│                    ┌─────────────┐                                │
│                    │   Grafana   │                                │
│                    │             │                                │
│                    │ - Dashboards│                                │
│                    │ - Explore    │                                │
│                    │ - Alerts     │                                │
│                    │ - Annotations│                               │
│                     └─────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Promtail Configuration

**Purpose:** Log shipping agent for Loki

**Configuration:** `promtail/config.yml`

```yaml
server:
  http_listen_port: 9080

# Positions file to track read positions
positions:
  filename: /tmp/positions.yaml

# Loki client configuration
clients:
  - url: http://loki:3100/loki/api/v1/push
    external_labels:
      cluster: psychsync-prod
      environment: ${ENVIRONMENT}

# Scrape configurations
scrape_configs:
  # Application logs
  - job_name: psychsync-api
    static_configs:
      - targets:
          - localhost
        labels:
          job: psychsync-api
          __path__: /var/log/psychsync/app.log
    pipeline_stages:
      # Parse JSON logs
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            correlation_id: correlation_id
            user_id: user_id
            path: path
            method: method
            status_code: status_code
            duration_ms: duration_ms
      # Create proper timestamp
      - timestamp:
          format: RFC3339
          source: timestamp
      # Extract labels from parsed JSON
      - labels:
          level:
          user_id:
          path:
          method:
          status_code:
      # Redact sensitive data
      - replace:
          expression: "(?i)(password)[=:]\s*[^\s,\}]+"
          replace: "password=[REDACTED]"
      - replace:
          expression: "(?i)(token)[=:]\s*[^\s,\}]{20,}"
          replace: "token=[REDACTED]"

  # Security logs
  - job_name: security-logger
    static_configs:
      - targets:
          - localhost
        labels:
          job: security-logger
          __path__: /var/log/psychsync/security.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            event_type: event_type
            severity: severity
            actor_user_id: actor_user_id
            actor_ip_address: actor_ip_address
      - timestamp:
          format: RFC3339
          source: timestamp
      - labels:
          event_type:
          severity:
          actor_user_id:

  # Error logs
  - job_name: error-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: errors
          level: error
          __path__: /var/log/psychsync/errors.log

  # Celery logs
  - job_name: celery-tasks
    static_configs:
      - targets:
          - localhost
        labels:
          job: celery
          __path__: /var/log/celery/worker.log
    pipeline_stages:
      - regex:
          expression: '(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)'
      - labels:
          level:
      - timestamp:
          format: "2006-01-02 15:04:05"
          source: timestamp

# Relabeling to drop unwanted logs
scrape_configs:
  - job_name: psychsync-api
    static_configs:
      - targets: [localhost]
        labels:
          __path__: /var/log/psychsync/app.log
    relabel_configs:
      # Drop debug logs in production
      - source_labels: [__promtail_scraper_level]
        target_label: level
        regex: DEBUG
        action: drop
        if: '{environment} == "production"'
```

### 2. Loki Configuration

**Purpose:** Horizontally scalable, highly available log aggregation system

**Configuration:** `loki/config.yml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

# Storage configuration
schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: s3
      schema: v11
      index:
        prefix: loki_index_
        period: 24h

common:
  storage:
    filesystem:
      chunks_directory: /loki/chunks
    s3:
      s3: s3://loki-logs
      bucketnames: chunks, ruler, admin
      region: us-east-1
      access_key_id: ${AWS_ACCESS_KEY_ID}
      secret_access_key: ${AWS_SECRET_ACCESS_KEY}

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: s3
  retention_enabled: true
  delete_interval: 2h
  retention_delete_delay: 24h

# Limits
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  per_stream_rate_limit: 10MB
  per_stream_rate_limit_burst: 20MB
  max_entries_limit_per_query: 100000
  max_streams_per_user: 10000

# Chunk store
chunk_store_config:
  max_look_back_period: 168h

# Table manager
table_manager:
  retention_deletes_enabled: true
  retention_period: 90d

# Query limits
frontend_worker:
  concurrency: 5

query_range:
  parallelise_shardable_queries: true
  max_retries: 5

ruler:
  storage:
    type: s3
    s3:
      bucketnames: ruler
```

### 3. Grafana Configuration

**Purpose:** Visualization and alerting platform

**Configuration:** `grafana/config.ini`

```ini
[server]
http_port = 3000

[database]
type = postgres
host = postgres:5432
name = grafana
user = ${GRAFANA_DB_USER}
password = ${GRAFANA_DB_PASSWORD}

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}

[auth.anonymous]
enabled = false

[users]
allow_sign_up = false
auto_assign_org_role = Viewer

[dashboards]
min_refresh_interval = 5s

[log]
mode = console
level = info
```

**Data Sources Configuration:**

```json
{
  "datasources": [
    {
      "name": "Loki",
      "type": "loki",
      "access": "proxy",
      "url": "http://loki:3100",
      "isDefault": true,
      "jsonData": {
        "maxLines": 1000,
        "derivedFields": [
          {
            "name": "traceID",
            "matcherRegex": "traceID=(\\w+)",
            "url": "$${__value.traceId}",
            "datasourceUid": "tempo"
          }
        ]
      }
    },
    {
      "name": "Prometheus",
      "type": "prometheus",
      "access": "proxy",
      "url": "http://prometheus:9090",
      "isDefault": false
    }
  ]
}
```

### 4. Dashboard Specifications

#### Dashboard 1: Live System Health

**JSON Configuration:**

```json
{
  "dashboard": {
    "title": "PsychSync Live System Health",
    "refresh": "10s",
    "panels": [
      {
        "id": 1,
        "title": "Requests Per Second",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(loki_distributor_lines_received_total[1m]))",
            "legendFormat": "RPS"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area"
        }
      },
      {
        "id": 2,
        "title": "Error Rate (Last 5m)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate({level=\"ERROR\"} | unwrap() [5m]))",
            "legendFormat": "Errors/sec"
          }
        ],
        "color": {"mode": "thresholds"},
        "thresholds": {
          "steps": [
            {"color": "green", "value": 0},
            {"color": "yellow", "value": 1},
            {"color": "red", "value": 5}
          ]
        }
      },
      {
        "id": 3,
        "title": "Average Response Time",
        "type": "gauge",
        "targets": [
          {
            "expr": "avg_over_time({duration_ms!=\"\"} | unwrap() | drop_empty [1m])",
            "legendFormat": "ms"
          }
        ],
        "options": {
          "min": 0,
          "max": 1000,
          "thresholds": {
            "steps": [
              {"color": "green", "value": 0},
              {"color": "yellow", "value": 500},
              {"color": "red", "value": 800}
            ]
          }
        }
      },
      {
        "id": 4,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "count(count_over_time({user_id!=\"\"} [5m]))",
            "legendFormat": "Users"
          }
        ]
      },
      {
        "id": 5,
        "title": "Log Volume by Level",
        "type": "piechart",
        "targets": [
          {
            "expr": "count_over_time({level=~\".*\"} [1h])",
            "legendFormat": "{{level}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Response Time Trend",
        "type": "timeseries",
        "targets": [
          {
            "expr": "avg_over_time({duration_ms!=\"\"} | unwrap() [5m])",
            "legendFormat": "Avg Response"
          },
          {
            "expr": "max_over_time({duration_ms!=\"\"} | unwrap() [5m])",
            "legendFormat": "Max Response"
          }
        ],
        "options": {
          "legend": {"displayMode": "table"},
          "tooltip": {"mode": "all"}
        }
      },
      {
        "id": 7,
        "title": "Slowest Endpoints (Top 10)",
        "type": "bar gauge",
        "targets": [
          {
            "expr": "topk(10, avg_over_time({path!=\"\"} | unwrap() [15m]))",
            "legendFormat": "{{path}}"
          }
        ]
      },
      {
        "id": 8,
        "title": "Recent Errors",
        "type": "logs",
        "targets": [
          {
            "expr": "{level=\"ERROR\"} | line_format \"{{.timestamp}} [{{.level}}] {{.message}}\""
          }
        ],
        "options": {
          "showTime": true,
          "showLabels": true,
          "showCommonLabels": true
        }
      }
    ],
    "tags": ["psychsync", "production", "health"]
  }
}
```

#### Dashboard 2: Security Events Monitor

```json
{
  "dashboard": {
    "title": "Security Events Real-Time Monitor",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Security Events (Last Hour)",
        "type": "stat",
        "targets": [
          {
            "expr": "count_over_time({event_type=~\".*\"} [1h])",
            "legendFormat": "Events"
          }
        ],
        "color": {"mode": "value"},
        "mappings": [
          {"type": "range", "from": 0, "to": 10, "text": "Normal", "color": "green"},
          {"type": "range", "from": 10, "to": 50, "text": "Elevated", "color": "yellow"},
          {"type": "range", "from": 50, "to": 999999, "text": "Critical", "color": "red"}
        ]
      },
      {
        "id": 2,
        "title": "Failed Login Attempts",
        "type": "stat",
        "targets": [
          {
            "expr": "count_over_time({event_type=\"auth_login_failure\"} [10m])",
            "legendFormat": "Attempts"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "green", "value": 0},
            {"color": "yellow", "value": 3},
            {"color": "red", "value": 10}
          ]
        }
      },
      {
        "id": 3,
        "title": "High Severity Events",
        "type": "stat",
        "targets": [
          {
            "expr": "count_over_time({severity=\"HIGH\"} or {severity=\"CRITICAL\"} [1h])",
            "legendFormat": "High Severity"
          }
        ],
        "color": "red"
      },
      {
        "id": 4,
        "title": "Events by Type",
        "type": "piechart",
        "targets": [
          {
            "expr": "count_over_time({event_type=~\".*\"} [1h])",
            "legendFormat": "{{event_type}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Security Event Timeline",
        "type": "timeseries",
        "targets": [
          {
            "expr": "count_over_time({event_type=~\".*\"} [1m])",
            "legendFormat": "All Events"
          },
          {
            "expr": "count_over_time({severity=\"HIGH\"} or {severity=\"CRITICAL\"} [1m])",
            "legendFormat": "High Severity"
          },
          {
            "expr": "count_over_time({event_type=\"auth_login_failure\"} [1m])",
            "legendFormat": "Failed Logins"
          }
        ]
      },
      {
        "id": 6,
        "title": "Top 5 IPs with Failed Logins",
        "type": "bar gauge",
        "targets": [
          {
            "expr": "topk(5, count_over_time({event_type=\"auth_login_failure\"} [1h]))",
            "legendFormat": "{{actor_ip_address}}"
          }
        ]
      },
      {
        "id": 7,
        "title": "Recent Security Events",
        "type": "logs",
        "targets": [
          {
            "expr": "{event_type=~\".*\"} | line_format \"{{.timestamp}} [{{.severity}}] {{.event_type}} - {{.actor_user_id}} from {{.actor_ip_address}}\""
          }
        ],
        "options": {
          "dedupStrategy": "explicit",
          "dedupCollapsing": false
        }
      },
      {
        "id": 8,
        "title": "Data Access by Classification",
        "type": "bargauge",
        "targets": [
          {
            "expr": "count_over_time({data_classification=\"public\"} [1h])",
            "legendFormat": "Public"
          },
          {
            "expr": "count_over_time({data_classification=\"internal\"} [1h])",
            "legendFormat": "Internal"
          },
          {
            "expr": "count_over_time({data_classification=\"confidential\"} [1h])",
            "legendFormat": "Confidential"
          },
          {
            "expr": "count_over_time({data_classification=\"restricted\"} [1h])",
            "legendFormat": "Restricted"
          }
        ]
      }
    ]
  }
}
```

#### Dashboard 3: Database Performance

```json
{
  "dashboard": {
    "title": "Database Performance Monitor",
    "refresh": "5s",
    "panels": [
      {
        "id": 1,
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "postgres_stat_database_numbackends",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "id": 2,
        "title": "Slow Queries (>1s)",
        "type": "stat",
        "targets": [
          {
            "expr": "count_over_time({duration_ms>1000} [1m])",
            "legendFormat": "Slow Queries"
          }
        ]
      },
      {
        "id": 3,
        "title": "Query Duration P95",
        "type": "gauge",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(postgres_stat_statements_query_duration_seconds_sum[5m])) / sum(rate(postgres_stat_statements_query_duration_seconds_count[5m])))",
            "legendFormat": "P95 Duration"
          }
        ],
        "options": {
          "unit": "s",
          "max": 5
        }
      },
      {
        "id": 4,
        "title": "Database Operations",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate({operation=\"create\"} [1m]))",
            "legendFormat": "Creates"
          },
          {
            "expr": "sum(rate({operation=\"read\"} [1m]))",
            "legendFormat": "Reads"
          },
          {
            "expr": "sum(rate({operation=\"update\"} [1m]))",
            "legendFormat": "Updates"
          },
          {
            "expr": "sum(rate({operation=\"delete\"} [1m]))",
            "legendFormat": "Deletes"
          }
        ]
      },
      {
        "id": 5,
        "title": "Query Performance by Table",
        "type": "heatmap",
        "targets": [
          {
            "expr": "avg_over_time({duration_ms!=\"\"} | unwrap() [5m])",
            "legendFormat": "{{table}}"
          }
        ]
      }
    ]
  }
}
```

### 5. Alert Configuration

#### Alert Rule 1: High Error Rate

**File:** `grafana/provisioning/alerting/alerting.yml`

```yaml
apiVersion: 1

groups:
  - name: psychsync-errors
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({level="ERROR"}[5m])) > 10
        for: 2m
        labels:
          severity: critical
          team: operations
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec (threshold: 10/sec)"
          dashboard: "http://grafana:3000/d/health"
          runbook_url: "https://docs.psychsync.com/runbooks/high-error-rate"
      - alert: ErrorSpike
        expr: |
          sum(rate({level="ERROR"}[1m])) > sum(rate({level="ERROR"}[5m])) * 3
        for: 1m
        labels:
          severity: critical
          team: operations
        annotations:
          summary: "Error spike detected"
          description: "Error rate increased by 3x in last minute"
```

#### Alert Rule 2: Failed Login Threshold

```yaml
  - name: psychsync-security
    interval: 1m
    rules:
      - alert: ExcessiveFailedLogins
        expr: |
          count_over_time({event_type="auth_login_failure"}[10m]) > 10
        for: 2m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Excessive failed login attempts"
          description: "{{ $value }} failed login attempts in 10 minutes"
      - alert: SuspiciousIPActivity
        expr: |
          count_over_time({event_type="auth_login_failure"}[5m]) by (actor_ip_address) > 5
        for: 1m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Suspicious activity from IP"
          description: "IP {{ $labels.actor_ip_address }} has {{ $value }} failed logins in 5 minutes"
```

#### Alert Rule 3: Performance Degradation

```yaml
  - name: psychsync-performance
    interval: 30s
    rules:
      - alert: SlowResponseTime
        expr: |
          avg_over_time({duration_ms!=""} | unwrap() [5m]) > 1000
        for: 5m
        labels:
          severity: warning
          team: operations
        annotations:
          summary: "Slow response time detected"
          description: "Average response time is {{ $value }}ms (threshold: 1000ms)"
      - alert: CriticalSlowResponse
        expr: |
          avg_over_time({duration_ms!=""} | unwrap() [2m]) > 3000
        for: 1m
        labels:
          severity: critical
          team: operations
        annotations:
          summary: "Critical response time"
          description: "Average response time is {{ $value }}ms (threshold: 3000ms)"
```

### 6. Notification Channels

**Slack Integration:**

```yaml
notifiers:
  - name: SlackAlerts
    type: slack
    uid: slack-notifier
    orgId: 1
    isDefault: true
    settings:
      url: ${SLACK_WEBHOOK_URL}
      recipient: "#psychsync-alerts"
      mentionUsers: true
      mentionGroups: true
      mentionChannels: false
```

**Email Integration:**

```yaml
  - name: EmailAlerts
    type: email
    uid: email-notifier
    orgId: 1
    isDefault: true
    settings:
      addresses: "ops-team@psychsync.com"
      singleEmail: true
      uploadImage: true
```

**PagerDuty Integration:**

```yaml
  - name: PagerDutyAlerts
    type: pagerduty
    uid: pagerduty-notifier
    orgId: 1
    isDefault: false
    settings:
      integrationKey: ${PAGERDUTY_INTEGRATION_KEY}
      severity: critical
```

---

## Docker Compose Configuration

**File:** `docker-compose.grafana-loki.yml`

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:2.9.2
    container_name: psychsync-loki
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - ./loki/config.yaml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    ports:
      - "3100:3100"
    networks:
      - observability-network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  promtail:
    image: grafana/promtail:2.9.2
    container_name: psychsync-promtail
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - ./promtail/config.yml:/etc/promtail/config.yml:ro
      - ./logs:/var/log/psychsync:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - promtail-positions:/tmp/positions
    networks:
      - observability-network
    depends_on:
      - loki

  grafana:
    image: grafana/grafana:10.2.2
    container_name: psychsync-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    ports:
      - "3000:3000"
    networks:
      - observability-network
    depends_on:
      - loki
      - prometheus
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  prometheus:
    image: prom/prometheus:v2.47.2
    container_name: psychsync-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - observability-network
    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:9090/-/healthy || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: psychsync-alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    ports:
      - "9093:9093"
    networks:
      - observability-network
    restart: always

volumes:
  loki-data:
    driver: local
  promtail-positions:
    driver: local
  grafana-data:
    driver: local
  prometheus-data:
    driver: local
  alertmanager-data:
    driver: local

networks:
  observability-network:
    driver: bridge
```

---

## LogQL Query Examples

### Basic Queries

```logql
# All errors in last hour
{level="ERROR"} | line_format "{{.message}}"

# All security events
{event_type=~".*"}

# Failed login attempts
{event_type="auth_login_failure"}

# Slow requests (>1000ms)
{duration_ms>1000}

# Errors from specific user
{level="ERROR"} | user_id="user123"

# Logs with correlation ID
{correlation_id="550e8400-e29b-41d4-a716-446655440000"}
```

### Aggregation Queries

```logql
# Count errors by level
count_over_time({level=~".*"} [1h])

# Average response time by endpoint
avg_over_time({path=~".*"} | unwrap() [5m])

# Top 10 slowest endpoints
topk(10, avg_over_time({path=~".*"} | unwrap() [1h]))

# Count log events per minute
count_over_time({} [1m])

# Rate of errors per second
rate({level="ERROR"}[1m])

# Percentage of error requests
100 * (sum(rate({level="ERROR"}[5m])) / sum(rate({}[5m])))
```

### Advanced Queries

```logql
# Errors with high severity
{level="ERROR"} | severity="HIGH" or severity="CRITICAL"

# Login failures from same IP in 5 minutes
count_over_time({event_type="auth_login_failure"} [5m]) by (actor_ip_address) > 5

# Requests with response time P99
quantile_over_time(0.99, {duration_ms!=""} | unwrap() [1h])

# Pattern matching - SQL injection attempts
{message=~".*union.*select.*"} | severity="CRITICAL"

# Correlate related events using correlation ID
{correlation_id="123"} | logfmt

# Time series of unique users
count_over_time({user_id!=""} [5m])
```

---

## Implementation Roadmap

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Deploy Grafana + Loki stack using Docker Compose
- [ ] Configure Loki storage (S3 or local)
- [ ] Set up Grafana authentication
- [ ] Configure Promtail log shipping
- [ ] Test log ingestion

### Phase 2: Dashboard Creation (Week 2)
- [ ] Create System Health dashboard
- [ ] Create Security Events dashboard
- [ ] Create Database Performance dashboard
- [ ] Create API Performance dashboard
- [ ] Set up dashboard provisioning

### Phase 3: Alert Configuration (Week 3)
- [ ] Configure error rate alerts
- [ ] Configure security event alerts
- [ ] Configure performance degradation alerts
- [ ] Set up notification channels (Slack, Email, PagerDuty)
- [ ] Test alert delivery

### Phase 4: Optimization (Week 4)
- [ ] Fine-tune alert thresholds
- [ ] Optimize Loki retention policies
- [ ] Set up dashboard permissions
- [ ] Create runbooks for common alerts
- [ ] Train team on dashboard usage

### Phase 5: Advanced Features (Week 5-6)
- [ ] Implement correlation ID tracing
- [ ] Add geographic IP visualization
- [ ] Create anomaly detection panels
- [ ] Set up automated incident response
- [ ] Integrate with incident management tools

---

## Performance Tuning

### Loki Optimization

**Query Parallelization:**
```yaml
frontend_worker:
  concurrency: 10
```

**Index Optimizations:**
```yaml
schema_config:
  configs:
    - from: 2024-01-01
      index:
        prefix: loki_index_
        period: 24h
```

**Storage Optimization:**
```yaml
compactor:
  retention_enabled: true
  delete_interval: 2h
  retention_delete_delay: 168h
```

### Promtail Tuning

**Batches:**
```yaml
client:
  batchwait: 1s
  batchsize: 1048576
  timeout: 10s
```

**Rate Limiting:**
```yaml
limits_config:
  per_stream_rate_limit: 10MB
  per_stream_rate_limit_burst: 20MB
```

---

## Security Considerations

1. **Authentication**
   - Grafana OAuth integration (SSO)
   - Role-based access control
   - Dashboard-level permissions

2. **Data Encryption**
   - TLS for log transport
   - Encrypted S3 storage
   - Sensitive data redaction in Promtail

3. **Audit Logging**
   - Enable Grafana audit logs
   - Track dashboard access
   - Monitor query history

4. **Network Security**
   - VPN access to Grafana
   - Firewall rules
   - Rate limiting

---

## Cost Estimate

| Component | Monthly Cost (AWS) | Notes |
|-----------|---------------------|-------|
| Loki (2 instances) | $80 | m5.large instances |
| Grafana (1 instance) | $40 | m5.medium instance |
| Prometheus (1 instance) | $40 | m5.medium instance |
| S3 Storage (500GB) | $15 | Standard storage |
| Data Transfer | $10 | 50GB outbound |
| **Total** | **$185/month** | Production estimate |

---

## Troubleshooting Guide

### Common Issues

1. **Logs not appearing in Grafana**
   ```bash
   # Check Promtail is running
   docker logs psychsync-promtail

   # Verify Loki is receiving logs
   curl http://loki:3100/ready

   # Check Promtail positions
   cat /tmp/positions.yaml
   ```

2. **Slow queries in Grafana**
   - Reduce time range
   - Use more specific label selectors
   - Enable query parallelization
   - Add label filters

3. **High Loki memory usage**
   - Increase compactor frequency
   - Reduce retention period
   - Add more Loki nodes
   - Tune chunk store settings

---

## Conclusion

Implementing a real-time log analytics dashboard using Grafana + Loki provides PsychSync with:

- ✅ **Sub-second log visibility** with live streaming
- ✅ **Cost-effective** storage compared to Elasticsearch
- ✅ **Powerful querying** with LogQL
- ✅ **Beautiful dashboards** with extensive customization
- ✅ **Flexible alerting** with multiple notification channels
- ✅ **Scalable architecture** for growing log volumes

The estimated implementation time is **6 weeks** with a monthly operational cost of **$185** for a medium-volume production environment.

---

**Next Steps:**
1. Review architecture with engineering team
2. Select cloud provider (AWS, GCP, or on-premise)
3. Begin Phase 1: Infrastructure Setup
4. Create implementation tickets in project management system
