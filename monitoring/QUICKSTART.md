# PsychSync Monitoring Stack - Quick Start Guide

**Date:** February 10, 2026
**Status:** ✅ Ready for Deployment

---

## Overview

This monitoring stack provides comprehensive visibility into message queue health, alerting, and performance metrics for the PsychSync application.

**Components:**
- **Prometheus** (port 9091): Metrics collection and storage
- **Grafana** (port 3001): Visualization dashboards
- **AlertManager** (port 9093): Alert routing and notification

---

## Quick Start

### 1. Start the Monitoring Stack

```bash
# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access the Monitoring Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Prometheus** | http://localhost:9091 | None |
| **Grafana** | http://localhost:3001 | admin / admin |
| **AlertManager** | http://localhost:9093 | None |

### 3. View the Message Queue Dashboard

1. Open Grafana: http://localhost:3001
2. Login with `admin / admin`
3. Navigate to **Dashboards** → **PsychSync Message Queue Monitoring**

---

## Configuration

### Environment Variables

Update `.env` with your configuration:

```bash
# Slack Webhook for Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Email for Critical Alerts
ALERT_EMAIL_RECIPIENTS=ops@psychsync.io,devops@psychsync.io

# Prometheus Metrics
ENABLE_METRICS=true
METRICS_PORT=9090
```

### AlertManager Configuration

Edit `monitoring/alertmanager/config.yml`:

```yaml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@psychsync.io'
```

---

## Key Metrics

### Queue Health Score
- **0-50**: Critical (alerting)
- **50-80**: Warning (monitor)
- **80-100**: Healthy ✅

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| DLQ Size | 100 | 500 |
| Consumer Lag | 1,000 | 10,000 |
| Buffer Size | 50 | 250 |
| Message Loss Rate | 1/min | 10/min |
| Health Score | < 75 | < 50 |

---

## Dashboards

### 1. Message Queue Monitoring
- Overall health score
- DLQ size trends
- Consumer lag
- Publish/consume rates
- Buffer utilization
- Failure reason breakdown

### 2. Available Panels
- **Health Score Gauge**: Color-coded status indicator
- **DLQ Size Graph**: Time-series of Kafka + Celery DLQ
- **Consumer Lag**: Total lag across all partitions
- **Message Rates**: Real-time publish/consume throughput
- **Buffer Size**: Persistent buffer utilization
- **Failure Pie Chart**: DLQ entries by reason
- **DLQ Table**: Detailed breakdown by topic/reason

---

## Alerting

### Alert Channels

| Severity | Slack Channel | Email |
|----------|--------------|-------|
| **Critical** | #psychsync-critical | ✅ Yes |
| **Warning** | #psychsync-alerts | ❌ No |
| **DLQ** | #psychsync-dlq | ❌ No |
| **Operations** | #psychsync-ops | ❌ No |

### Alert Rules

See `monitoring/message_queue_alerts.yml` for complete rule definitions.

Key alerts:
- `KafkaDLQSizeCritical` - DLQ > 500 entries
- `MessageLossRateCritical` - Loss rate > 10/min
- `QueueHealthScoreCritical` - Health score < 50
- `KafkaConsumerLagCritical` - Lag > 10,000 messages

---

## Maintenance

### Daily Checks

- [ ] Review queue health score (should be > 80)
- [ ] Check DLQ size (should be < 100)
- [ ] Verify consumer lag (< 1,000)
- [ ] Review alert notifications

### Weekly Tasks

```bash
# Review DLQ entries by reason
SELECT reason, COUNT(*) as count
FROM kafka_dead_letter_tasks
WHERE status = 'pending'
GROUP BY reason
ORDER BY count DESC;

# Clean up old resolved entries (automated, but can be manual)
-- DELETE FROM kafka_dead_letter_tasks
-- WHERE status = 'resolved' AND created_at < NOW() - INTERVAL '30 days';
```

---

## Troubleshooting

### Dashboard Not Showing Data

1. Check Prometheus is scraping:
   ```bash
   curl http://localhost:9091/api/v1/targets
   ```

2. Verify metrics endpoint:
   ```bash
   curl http://localhost:9090/metrics
   ```

3. Check application logs:
   ```bash
   tail -f logs/app.log | grep -i monitoring
   ```

### Alerts Not Firing

1. Check AlertManager is running:
   ```bash
   docker-compose -f docker-compose.monitoring.yml logs alertmanager
   ```

2. Verify Slack webhook is configured in AlertManager config

3. Test alert rules in Prometheus UI:
   - Go to http://localhost:9091
   - Navigate to **Alerts** tab
   - Check rule evaluation status

### High DLQ Size

**Investigation:**
```sql
-- Check top failure reasons
SELECT reason, COUNT(*) as count
FROM kafka_dead_letter_tasks
WHERE status = 'pending'
GROUP BY reason
ORDER BY count DESC
LIMIT 10;
```

**Resolution:**
1. Check if errors are transient (network, timeout)
2. Review recent deployments for breaking changes
3. Run DLQ retry manually (see `MONITORING_SETUP_GUIDE.md`)

---

## Stopping the Monitoring Stack

```bash
# Stop all services
docker-compose -f docker-compose.monitoring.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.monitoring.yml down -v
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Update AlertManager configuration with production Slack webhook
- [ ] Set correct email addresses for alerts
- [ ] Adjust alert thresholds based on traffic patterns
- [ ] Configure persistent storage for Prometheus data
- [ ] Set up log rotation for monitoring logs
- [ ] Configure backup for Grafana dashboards

### Deployment Steps

1. **Update configurations** for production environment
2. **Deploy monitoring stack** to production servers
3. **Verify data collection** (check Prometheus targets)
4. **Test alerting** (trigger test alert)
5. **Import dashboards** to production Grafana
6. **Document runbooks** for common issues

---

## Support

For issues or questions:
- 📧 Email: ops@psychsync.io
- 💬 Slack: #psychsync-ops
- 📚 Docs: See `MONITORING_SETUP_GUIDE.md`

---

**Generated:** 2026-02-10
**Version:** 1.0.0
