# 📊 Setting Up Async Cache Monitoring

**Date:** December 27, 2025
**Purpose:** Monitor async cache performance with Grafana + Prometheus
**Status:** ✅ Configuration files created

---

## 🎯 Overview

This guide walks through setting up monitoring for the async cache implementation using Prometheus and Grafana. The monitoring stack will track:

- **Cache hit rate** (target: >70%)
- **Cache hits vs misses** (operations per second)
- **Memory usage** (Redis memory consumption)
- **Response times** (P50, P95, P99 latency)
- **Connected clients** (active connections)
- **Expired keys** (cache evictions)

---

## 📋 Prerequisites

1. **Redis Exporter** - Exposes Redis metrics in Prometheus format
2. **Prometheus** - Scrapes and stores metrics
3. **Grafana** - Visualizes metrics with dashboards

---

## 🚀 Quick Start

### Step 1: Install Redis Exporter

```bash
# Download Redis Exporter
curl -LO https://github.com/oliver006/redis_exporter/releases/download/v1.52.0/redis_exporter-v1.52.0.darwin.amd64.tar.gz
tar xvfz redis_exporter-v1.52.0.darwin.amd64.tar.gz
mv redis_exporter-v1.52.0.darwin-amd64/redis_exporter /usr/local/bin/

# Start Redis Exporter
redis_exporter --redis.addr=localhost:6379 &
```

### Step 2: Start Prometheus

```bash
# Start Prometheus with configuration
prometheus --config.file=deploy/prometheus/prometheus.yml \
  --storage.tsdb.path=./prometheus_data &
```

Verify: http://localhost:9090

### Step 3: Start Grafana

```bash
# Start Grafana
grafana-server --config=deploy/grafana/grafana.ini --homepath=/usr/local/opt/grafana &
```

Verify: http://localhost:3000 (default: admin/admin)

### Step 4: Import Dashboard

1. Open Grafana: http://localhost:3000
2. Navigate to Dashboards → Import
3. Upload: `deploy/grafana/dashboards/redis-cache-dashboard.json`
4. Select Prometheus data source

---

## 📊 Dashboard Configuration

The dashboard includes the following panels:

### 1. Cache Hit Rate (Primary Metric)
**Query:**
```
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100
```
**Target:** >70%
**Alert:** Triggers when hit rate drops below 70% for 5 minutes

### 2. Cache Hits vs Misses
**Queries:**
```
rate(redis_keyspace_hits_total[5m])  # Hits per second
rate(redis_keyspace_misses_total[5m]) # Misses per second
```
**Purpose:** Compare cache effectiveness

### 3. Total Commands Processed
**Query:**
```
rate(redis_commands_processed_total[5m])
```
**Purpose:** Overall Redis throughput

### 4. Connected Clients
**Query:**
```
redis_connected_clients
```
**Purpose:** Monitor connection count

### 5. Memory Usage
**Queries:**
```
redis_memory_used_bytes   # Current memory usage
redis_memory_max_bytes    # Max memory limit (if set)
```
**Purpose:** Track memory consumption

### 6. Cache Key Count
**Query:**
```
redis_db_keys
```
**Purpose:** Monitor number of cached items

### 7. Expired Keys
**Query:**
```
rate(redis_expired_keys_total[5m])
```
**Purpose:** Track cache evictions

### 8. Response Time (P95)
**Query:**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```
**Target:** <500ms
**Purpose:** Monitor API response times

---

## ⚠️ Alerting Rules

### Alert 1: Low Cache Hit Rate
```yaml
- alert: CacheHitRateLow
  expr: |
    rate(redis_keyspace_hits_total[5m])
    / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
    < 0.7
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 70%"
    description: "Hit rate is {{ $value | humanizePercentage }}"
```

### Alert 2: High Memory Usage
```yaml
- alert: RedisHighMemoryUsage
  expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Redis memory usage above 90%"
    description: "Memory usage is {{ $value | humanizePercentage }}"
```

### Alert 3: High P95 Latency
```yaml
- alert: HighP95Latency
  expr: |
    histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
    > 0.5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "P95 latency above 500ms"
    description: "P95 latency is {{ $value }}s"
```

---

## 🔍 Verifying Setup

### Check Redis Exporter

```bash
curl http://localhost:9121/metrics | grep redis_keyspace
```

Expected output:
```
redis_keyspace_hits_total 6240
redis_keyspace_misses_total 854
```

### Check Prometheus Targets

```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

Expected:
```json
{"job": "redis_exporter", "health": "up"}
{"job": "psychsync_api", "health": "up"}
```

### Check Grafana Dashboard

1. Open Grafana: http://localhost:3000
2. Navigate to Dashboards → PsychSync - Async Cache Performance
3. Verify panels are showing data

---

## 📈 Interpreting Metrics

### Cache Hit Rate

| Range | Status | Action |
|-------|--------|--------|
| >90% | ✅ Excellent | No action needed |
| 70-90% | ✅ Good | Monitor for trends |
| 50-70% | ⚠️ Fair | Investigate cache key design |
| <50% | ❌ Poor | Review caching strategy |

### Memory Usage

| Range | Status | Action |
|-------|--------|--------|
| <50% | ✅ Good | No action needed |
| 50-80% | ⚠️ Monitor | Plan for expansion |
| 80-90% | ⚠️ Warning | Consider increasing memory or TTL |
| >90% | ❌ Critical | Immediate action required |

### P95 Latency

| Range | Status | Action |
|-------|--------|--------|
| <200ms | ✅ Excellent | No action needed |
| 200-500ms | ✅ Good | Within target |
| 500-1000ms | ⚠️ Warning | Investigate slow queries |
| >1000ms | ❌ Critical | Optimize or scale |

---

## 🛠️ Troubleshooting

### Issue: No metrics in Grafana

**Solution:**
1. Check Prometheus is scraping:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```
2. Verify Redis Exporter is running:
   ```bash
   ps aux | grep redis_exporter
   ```
3. Check Redis Exporter metrics:
   ```bash
   curl http://localhost:9121/metrics
   ```

### Issue: Cache hit rate low (<50%)

**Solution:**
1. Check TTL values - may be too short
2. Review cache key design - may be too specific
3. Verify cache is being used - check logs
4. Consider cache warming for frequently accessed data

### Issue: High memory usage (>80%)

**Solution:**
1. Reduce TTL values
2. Implement cache eviction policies
3. Monitor memory growth trends
4. Consider increasing Redis memory limit

---

## 📚 Additional Resources

- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Documentation:** https://grafana.com/docs/
- **Redis Exporter:** https://github.com/oliver006/redis_exporter
- **Async Cache Guide:** `ASYNC_CACHE_MIGRATION_GUIDE.md`
- **Migration Demo:** `ASYNC_CACHE_MIGRATION_COMPLETE.md`

---

## ✅ Setup Checklist

- [ ] Redis Exporter installed and running (port 9121)
- [ ] Prometheus configured and running (port 9090)
- [ ] Grafana installed and running (port 3000)
- [ ] Dashboard imported into Grafana
- [ ] Prometheus data source configured in Grafana
- [ ] Alerts configured in Prometheus
- [ ] Verification queries executed successfully
- [ ] Dashboard panels showing data

---

**Setup Complete:** Once all checklist items are complete, your async cache monitoring is ready!

**Next Steps:**
1. Monitor cache hit rate for 24 hours
2. Identify patterns and optimize TTL values
3. Set up alert notifications (email, Slack, PagerDuty)
4. Create additional dashboards for specific endpoints

---

**Created:** December 27, 2025
**Author:** Claude Code (Architecture Audit & Execution)
**Version:** 1.0
