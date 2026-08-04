# ELK Stack Log Aggregation Design
## Centralized Log Management for PsychSync

**Date:** 2026-03-10
**Version:** 1.0.0
**Priority:** P1 (High Priority Enhancement)

---

## Executive Summary

This document provides a comprehensive design for implementing an **ELK (Elasticsearch, Logstash, Kibana) stack** to provide centralized log aggregation, advanced querying, and real-time log analytics for PsychSync's production environment.

### Key Objectives

1. **Centralized Log Collection** - Aggregate logs from all services in one location
2. **Real-Time Indexing** - Sub-second log ingestion and search availability
3. **Advanced Querying** - KQL and Lucene query support for complex searches
4. **Log-Based Alerting** - Automated alerts on error rates, security events, and anomalies
5. **Scalability** - Horizontal scaling for growing log volumes
6. **Data Retention** - Configurable retention policies for compliance

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
│                  │ Filebeat/    │                                │
│                  │ Logstash     │                                │
│                  └──────┬───────┘                                │
└─────────────────────────┼────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Log Processing Layer                            │
│                    ┌────────────────────┐                           │
│                    │    Logstash       │                           │
│                    │  - Parsing       │                           │
│                    │  - Enrichment    │                           │
│                    │  - Filtering     │                           │
│                    │  - Redaction     │                           │
│                    └────────┬──────────┘                           │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Storage & Index Layer                             │
│                     ┌─────────────┐                                │
│                     │Elasticsearch│                                │
│                     │ Cluster    │                                │
│                     │            │                                │
│                     │  - Indices │                                │
│                     │  - Shards  │                                │
│                     │  - Replicas│                                │
│                     └─────┬───────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Visualization & Analysis                           │
│                    ┌─────────────┐                                │
│                    │   Kibana    │                                │
│                    │            │                                │
│                    │ - Dashboards│                                │
│                    │ - Discover   │                                │
│                    │ - Visualize  │                                │
│                    │ - Alerting   │                                │
│                    └─────────────┘                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Filebeat Configuration

**Purpose:** Lightweight log shipper that monitors log files and ships to Logstash

**Configuration:** `filebeat.yml`

```yaml
filebeat.inputs:
  # Application logs
  - type: log
    enabled: true
    paths:
      - /var/log/psychsync/app.log
      - /var/log/psychsync/errors.log
    fields:
      service: psychsync-api
      environment: ${ENVIRONMENT}
    fields_under_root: true
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after

  # Security logs
  - type: log
    enabled: true
    paths:
      - /var/log/psychsync/security.log
    fields:
      service: security-logger
      environment: ${ENVIRONMENT}
    fields_under_root: true

  # Audit logs
  - type: log
    enabled: true
    paths:
      - /var/log/psychsync/audit.log
    fields:
      service: audit-logger
      environment: ${ENVIRONMENT}
    fields_under_root: true

# Logstash output
output.logstash:
  hosts: ["logstash:5044"]
  loadbalance: true
  compression_level: 3

# Processing
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - add_cloud_metadata: ~
  - add_docker_metadata: ~

# Queue settings (for backpressure handling)
queue.mem:
  events: 4096
  flush.min_events: 512
  flush.timeout: 1s
```

### 2. Logstash Pipeline

**Purpose:** Central log processing with parsing, enrichment, and filtering

**Configuration:** `logstash/pipeline.conf`

```conf
# Input from Filebeat
input {
  beats {
    port => 5044
    type => beats
  }
}

# Filter pipeline
filter {
  # Parse JSON logs
  if [message] =~ /^\{.*\}$/ {
    json {
      source => "message"
      target => "parsed"
    }
  }

  # Parse correlation ID
  if [parsed][correlation_id] {
    mutate {
      add_field => { "[@metadata][correlation_id]" => "%{[parsed][correlation_id]}" }
    }
  }

  # Add environment tag
  if [environment] {
    mutate {
      add_field => { "[@metadata][environment]" => "%{[environment]}" }
    }
  }

  # Parse log level
  if [parsed][level] {
    mutate {
      uppercase => [ "[parsed][level]" ]
      add_tag => [ "%{[parsed][level]}" ]
    }
  }

  # GeoIP enrichment for IP addresses
  if [parsed][ip_address] {
    geoip {
      source => "[parsed][ip_address]"
      target => "[parsed][geoip]"
      database => "/usr/share/GeoIP/GeoLite2-City.mmdb"
    }
  }

  # User agent parsing
  if [parsed][user_agent] {
    useragent {
      source => "[parsed][user_agent]"
      target => "[parsed][ua]"
    }
  }

  # Security event classification
  if [parsed][event] == "security_login_attempt" {
    mutate {
      add_tag => [ "security", "auth" ]
      add_field => { "[@metadata][alert_type]" => "auth_event" }
    }
  }

  # Error classification
  if [parsed][level] == "ERROR" {
    mutate {
      add_tag => [ "error" ]
    }

    # Rate limiting for error alerts (1 per minute per type)
    throttle {
      key => "%{[parsed][error_type]}-%{[parsed][path]}"
      period => 60
      max_age => 120
      add_tag => [ "throttled_error" ]
    }
  }

  # Sensitive data redaction (additional layer)
  mutate {
    gsub => [
      "message", "(?i)(password)[=:]\s*[^\s,\}]+", "\1=[REDACTED]",
      "message", "(?i)(token)[=:]\s*[^\s,\}]{20,}", "\1=[REDACTED]",
      "message", "\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}", "[REDACTED_CREDIT_CARD]"
    ]
  }

  # Add timestamp if missing
  if ![@timestamp] {
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }

  # Drop debug logs in production
  if [parsed][level] == "DEBUG" and [@metadata][environment] == "production" {
    drop { }
  }
}

# Elasticsearch output
output {
  # Main indices with daily rotation
  if [parsed][event] == "security_*" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "psychsync-security-%{+YYYY.MM.dd}"
      template_name => "psychsync-security"
      template => "/etc/logstash/templates/security-template.json"
    }
  } else if [parsed][level] == "ERROR" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "psychsync-errors-%{+YYYY.MM.dd}"
      template_name => "psychsync-errors"
    }
  } else {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "psychsync-logs-%{+YYYY.MM.dd}"
    }
  }
}
```

### 3. Elasticsearch Index Templates

**Purpose:** Define index mappings and settings for optimal performance

**Template:** `elasticsearch/templates/security-template.json`

```json
{
  "index_patterns": ["psychsync-security-*"],
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "refresh_interval": "5s",
      "index.lifecycle.name": "psychsync-security-policy",
      "index.lifecycle.rollover_alias": "psychsync-security"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "correlation_id": { "type": "keyword" },
        "event_type": { "type": "keyword" },
        "severity": { "type": "keyword" },
        "actor_user_id": { "type": "keyword" },
        "actor_ip_address": {
          "type": "ip",
          "fields": {
            "keyword": { "type": "keyword" }
          }
        },
        "parsed": {
          "properties": {
            "geoip": {
              "properties": {
                "location": { "type": "geo_point" },
                "city_name": { "type": "keyword" },
                "country_name": { "type": "keyword" }
              }
            },
            "ua": {
              "properties": {
                "name": { "type": "keyword" },
                "os": { "type": "keyword" },
                "device": { "type": "keyword" }
              }
            }
          }
        },
        "risk_score": { "type": "float" },
        "tags": { "type": "keyword" }
      }
    }
  }
}
```

**Index Lifecycle Management (ILM):**

```json
{
  "policy": "psychsync-security-policy",
  "phases": {
    "hot": {
      "min_age": "0ms",
      "actions": {
        "rollover": {
          "max_size": "50GB",
          "max_age": "1d"
        }
      }
    },
    "warm": {
      "min_age": "7d",
      "actions": {
        "shrink": { "number_of_shards": 1 },
        "force_merge": { "max_num_segments": 1 }
      }
    },
    "cold": {
      "min_age": "30d",
      "actions": {
        "freeze": {}
      }
    },
    "delete": {
      "min_age": "90d",
      "actions": {
        "delete": {}
      }
    }
  }
}
```

### 4. Kibana Dashboard Configuration

**Dashboard 1: Security Events Overview**

```json
{
  "title": "PsychSync Security Events",
  "description": "Real-time security event monitoring",
  "panels": [
    {
      "type": "metric",
      "title": "Total Security Events (24h)",
      "grid": { "x": 0, "y": 0, "w": 6, "h": 4 },
      "metrics": [
        { "id": "1", "type": "count" }
      ]
    },
    {
      "type": "pie",
      "title": "Events by Severity",
      "grid": { "x": 6, "y": 0, "w": 6, "h": 4 },
      "dimensions": { "splitRow": "terms", "field": "severity.keyword" }
    },
    {
      "type": "map",
      "title": "Login Locations",
      "grid": { "x": 12, "y": 0, "w": 12, "h": 4 },
      "map": {
        "mapStyle": "Dark Matter",
        "layer": "road",
        "field": "parsed.geoip.location"
      }
    },
    {
      "type": "line",
      "title": "Security Events Timeline",
      "grid": { "x": 0, "y": 4, "w": 24, "h": 8 },
      "axis": { "x": { "field": "@timestamp" } },
      "series": [
        { "id": "1", "split_by_mode": "terms", "split_by_field": "event_type.keyword" }
      ]
    },
    {
      "type": "data-table",
      "title": "Recent Security Events",
      "grid": { "x": 0, "y": 12, "w": 24, "h": 8 },
      "columns": [
        "@timestamp", "event_type.keyword", "severity.keyword",
        "actor_user_id.keyword", "actor_ip_address", "message"
      ],
      "sort": [["@timestamp", "desc"]]
    }
  ]
}
```

**Dashboard 2: Application Performance**

```json
{
  "title": "Application Performance Metrics",
  "panels": [
    {
      "type": "metric",
      "title": "Avg Response Time (ms)",
      "grid": { "x": 0, "y": 0, "w": 4, "h": 3 },
      "metrics": [
        {
          "type": "avg",
          "field": "duration_ms"
        }
      ]
    },
    {
      "type": "metric",
      "title": "Requests/sec",
      "grid": { "x": 4, "y": 0, "w": 4, "h": 3 },
      "metrics": [
        { "type": "count", "id": "1" },
        { "type": "bucket_script", "id": "2", "buckets_path": { "count": "1" },
          "script": "params.count / 60" }
      ]
    },
    {
      "type": "metric",
      "title": "Error Rate (%)",
      "grid": { "x": 8, "y": 0, "w": 4, "h": 3 },
      "metrics": [
        { "type": "count", "id": "errors", "filter": "level: ERROR" },
        { "type": "count", "id": "total" },
        {
          "type": "bucket_script",
          "script": "params.errors / params.total * 100"
        }
      ]
    },
    {
      "type": "histogram",
      "title": "Response Time Distribution",
      "grid": { "x": 0, "y": 3, "w": 12, "h": 6 },
      "params": { "field": "duration_ms", "interval": 100 }
    },
    {
      "type": "bar",
      "title": "Slowest Endpoints",
      "grid": { "x": 12, "y": 3, "w": 12, "h": 6 },
      "series": [
        {
          "id": "1",
          "split_by_mode": "terms",
          "split_by_field": "path.keyword",
          "metrics": [
            { "type": "avg", "field": "duration_ms" }
          ],
          "top": 10
        }
      ]
    }
  ]
}
```

### 5. Alert Configuration

**Alert Rule 1: High Error Rate**

```json
{
  "name": "High Error Rate Alert",
  "type": "threshold",
  "throttle_period": "5m",
  "params": {
    "index": "psychsync-errors-*",
    "timeWindowSize": "5m",
    "timeUnit": "m",
    "thresholdComparator": "between",
    "threshold": [10, 10000],
    "thresholdDocCount": 1
  },
  "actions": [
    {
      "id": "email_notification",
      "type": "email",
      "email": "ops-team@psychsync.com"
    },
    {
      "id": "slack_notification",
      "type": "slack",
      "webhook_url": "${SLACK_WEBHOOK_URL}"
    }
  ]
}
```

**Alert Rule 2: Failed Login Attempts**

```json
{
  "name": "Failed Login Attempts Alert",
  "type": "threshold",
  "throttle_period": "15m",
  "params": {
    "index": "psychsync-security-*",
    "timeWindowSize": "10m",
    "timeUnit": "m",
    "filter": "event_type:auth_login_failure AND success:false",
    "thresholdComparator": ">",
    "threshold": 5
  }
}
```

**Alert Rule 3: Suspicious IP Activity**

```json
{
  "name": "Suspicious IP Activity",
  "type": "threshold",
  "throttle_period": "1h",
  "params": {
    "index": "psychsync-security-*",
    "timeWindowSize": "30m",
    "timeUnit": "m",
    "groupBy": "actor_ip_address",
    "thresholdComparator": ">",
    "threshold": 100
  }
}
```

---

## Docker Compose Configuration

**File:** `docker-compose.elk.yml`

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: psychsync-elasticsearch
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
      - "ELASTIC_PASSWORD=${ELASTIC_PASSWORD}"
      - xpack.security.enabled=true
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
      - ./elasticsearch/templates:/usr/share/elasticsearch/templates
    ports:
      - "9200:9200"
      - "9300:9300"
    networks:
      - elk-network
    healthcheck:
      test: ["CMD-SHELL", "curl -u elastic:${ELASTIC_PASSWORD} -s http://localhost:9200/_cluster/health | grep -q 'green'"]
      interval: 30s
      timeout: 10s
      retries: 5

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: psychsync-logstash
    volumes:
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./logstash/templates:/etc/logstash/templates
    ports:
      - "5044:5044"
      - "9600:9600"
    networks:
      - elk-network
    depends_on:
      - elasticsearch
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9600/_node/stats | grep -q 'status:green'"]
      interval: 30s
      timeout: 10s
      retries: 5

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: psychsync-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=elastic
      - "ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}"
      - SERVER_NAME=psychsync-kibana
    volumes:
      - ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml
    ports:
      - "5601:5601"
    networks:
      - elk-network
    depends_on:
      - elasticsearch
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:5601/api/status | grep -q 'green'"]
      interval: 30s
      timeout: 10s
      retries: 5

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: psychsync-filebeat
    user: root
    volumes:
      - ./filebeat/config/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/psychsync:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - elk-network
    depends_on:
      - logstash

volumes:
  elasticsearch-data:
    driver: local

networks:
  elk-network:
    driver: bridge
```

---

## Implementation Roadmap

### Phase 1: Infrastructure Setup (Week 1-2)
- [ ] Deploy ELK stack using Docker Compose
- [ ] Configure Elasticsearch cluster with security
- [ ] Set up Kibana with authentication
- [ ] Configure Logstash pipeline
- [ ] Deploy Filebeat on application servers

### Phase 2: Integration (Week 3)
- [ ] Update application logging to structured JSON
- [ ] Configure Filebeat to ship logs
- [ ] Test log ingestion and parsing
- [ ] Set up index templates and ILM policies

### Phase 3: Visualization (Week 4)
- [ ] Create security events dashboard
- [ ] Create application performance dashboard
- [ ] Create error analysis dashboard
- [ ] Set up saved queries

### Phase 4: Alerting (Week 5)
- [ ] Configure alert rules
- [ ] Set up notification channels (email, Slack, PagerDuty)
- [ ] Test alert delivery
- [ ] Configure alert escalation

### Phase 5: Optimization (Week 6)
- [ ] Performance tuning for Elasticsearch
- [ ] Configure log retention policies
- [ ] Set up backup and recovery
- [ ] Document operational procedures

---

## Performance Considerations

### Elasticsearch Sizing

| Log Volume | Nodes | RAM per Node | Storage | Shards |
|------------|--------|--------------|----------|---------|
| < 10 GB/day | 1 | 4GB | 100GB | 1 |
| 10-50 GB/day | 3 | 8GB | 500GB | 3 |
| 50-200 GB/day | 3+ | 16GB | 2TB | 5-10 |
| > 200 GB/day | 5+ | 32GB | 10TB+ | 10+ |

### Logstash Performance

- **Workers:** 2 × number of CPU cores
- **Batch Size:** 125-500 events per batch
- **Pipeline Batch Size:** 125-500
- **Queue Type:** persisted (for durability)

### Filebeat Configuration

- **Prospectors:** 10-20 (max 50)
- **Scan Frequency:** 10s (default)
- **Harvester Buffer:** 16KB (default)
- **Spool Size:** 2048 messages

---

## Security Considerations

1. **Transport Layer Security (TLS)**
   - Enable TLS for all node communications
   - Use certificate-based authentication

2. **Authentication**
   - Elasticsearch Native Realm or SAML
   - Kibana authentication via Elasticsearch

3. **Authorization**
   - Role-based access control (RBAC)
   - Index-level permissions
   - Field-level security for sensitive data

4. **Data Encryption**
   - Encrypt sensitive fields at rest
   - Use encrypted backups

5. **Audit Logging**
   - Enable Elasticsearch security audit logs
   - Monitor access to sensitive indices

---

## Cost Estimate

| Component | Monthly Cost (AWS) | Notes |
|-----------|---------------------|-------|
| Elasticsearch (3 nodes, 8GB) | $150 | m5.large instances |
| Logstash (2 nodes, 4GB) | $60 | m5.medium instances |
| Kibana (1 node, 4GB) | $30 | m5.medium instance |
| EBS Storage (1TB) | $80 | gp2 storage |
| Data Transfer | $20 | 100GB outbound |
| **Total** | **$340/month** | Production estimate |

---

## Monitoring the ELK Stack

### Key Metrics to Monitor

**Elasticsearch:**
- Cluster health status
- JVM heap usage
- Indexing rate
- Search latency
- Disk usage

**Logstash:**
- Pipeline throughput
- Queue size
- Worker utilization
- Filter execution time

**Filebeat:**
- Log shipping rate
- Registry file size
- Spooler queue size
- Network errors

### Monitoring Tools

- **Elastic Stack Monitoring:** Built-in Kibana monitoring
- **Prometheus:** Export metrics to Prometheus
- **CloudWatch:** AWS-native monitoring
- **PagerDuty:** Alert escalation

---

## Troubleshooting Guide

### Common Issues

1. **Logs not appearing in Kibana**
   - Check Filebeat is running: `systemctl status filebeat`
   - Verify Logstash pipeline: `curl localhost:9600/_node/stats/pipelines`
   - Check Elasticsearch index: `curl localhost:9200/_cat/indices`

2. **High CPU usage on Elasticsearch**
   - Reduce refresh interval
   - Increase shard count
   - Check for expensive queries

3. **Memory pressure on Logstash**
   - Increase pipeline workers
   - Reduce batch size
   - Filter logs before processing

---

## Conclusion

Implementing an ELK stack will provide PsychSync with enterprise-grade log aggregation and analytics capabilities. The solution is:

- ✅ Scalable for growing log volumes
- ✅ Real-time with sub-second indexing
- ✅ Secure with encryption and RBAC
- ✅ Cost-effective with proper sizing
- ✅ Maintainable with Docker deployment

The estimated implementation time is **6 weeks** with a monthly operational cost of **$340** for a medium-volume production environment.

---

**Next Steps:**
1. Review architecture with operations team
2. Obtain approval for infrastructure costs
3. Begin Phase 1: Infrastructure Setup
4. Create JIRA tickets for implementation tasks
