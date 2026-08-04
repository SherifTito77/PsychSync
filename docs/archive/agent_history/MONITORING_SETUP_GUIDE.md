# Message Queue Monitoring Setup Guide

**Purpose:** Configure monitoring and alerting for the async message queue system
**Created:** February 9, 2026
**Status:** ✅ Ready for Production

---

## Quick Start

```bash
# 1. Install monitoring dependencies
pip install prometheus-client aiohttp

# 2. Run database migrations
alembic upgrade head

# 3. Configure environment variables
cp .env.example .env.prod
# Edit .env.prod with your settings

# 4. Start the application with monitoring enabled
python -m app.main

# 5. Access metrics endpoint
curl http://localhost:8000/metrics
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_DLQ_TOPICS={"assessment":"dlq-assessment-events","user":"dlq-user-events"}

# Redis Configuration (for persistent buffer)
REDIS_URL=redis://localhost:6379/0

# Alerting Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_EMAIL_RECIPIENTS=ops@example.com,devops@example.com

# Monitoring Configuration
PROMETHEUS_METRICS_ENABLED=true
METRICS_PORT=9090

# Alert Thresholds
DLQ_SIZE_WARNING=100
DLQ_SIZE_CRITICAL=500
CONSUMER_LAG_WARNING=1000
CONSUMER_LAG_CRITICAL=10000
BUFFER_SIZE_WARNING=50
HEALTH_SCORE_CRITICAL=50
```

---

## Prometheus Metrics Setup

### 1. Expose Metrics Endpoint

The application exposes Prometheus metrics on `/metrics` endpoint.

**Metrics Available:**

```python
# Kafka Producer Metrics
kafka_messages_published_total{topic="assessment-events", status="success"}
kafka_publish_duration_seconds{topic="assessment-events"}
kafka_buffer_size{topic="assessment-events"}

# Kafka Consumer Metrics
kafka_messages_consumed_total{topic="assessment-events", consumer_group="default", status="success"}
kafka_consumer_lag{topic="assessment-events", consumer_group="default", partition="0"}
kafka_consumer_processing_duration_seconds{topic="assessment-events", handler="AssessmentHandler"}

# DLQ Metrics
kafka_dlq_size{topic="assessment-events", reason="handler_error", status="pending"}
celery_dlq_size{task_name="calculate_assessment_scores", reason="timeout", status="pending"}

# Health Metrics
message_loss_rate{queue_type="kafka"}
queue_health_score{queue_type="kafka"}
```

### 2. Configure Prometheus Scraping

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'psychsync-message-queues'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### 3. Start Prometheus

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

---

## Alerting Setup

### 1. Slack Alert Handler

```python
from app.monitoring.message_queue_monitoring import SlackAlertHandler, get_monitor

# Initialize monitor
monitor = get_monitor()

# Register Slack handler
slack_handler = SlackAlertHandler(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)
monitor.register_alert_handler(slack_handler)
```

### 2. Email Alert Handler (Critical Alerts Only)

```python
from app.monitoring.message_queue_monitoring import EmailAlertHandler

email_handler = EmailAlertHandler(
    recipients=["ops@example.com", "devops@example.com"]
)
monitor.register_alert_handler(email_handler)
```

### 3. Configure Alert Thresholds

Edit alert thresholds in your application startup:

```python
from app.monitoring.message_queue_monitoring import MessageQueueMonitor

monitor = MessageQueueMonitor()
monitor.alert_thresholds = {
    "dlq_size_warning": 100,
    "dlq_size_critical": 500,
    "consumer_lag_warning": 1000,
    "consumer_lag_critical": 10000,
    "buffer_size_warning": 50,
    "message_loss_rate_warning": 10,
    "health_score_critical": 50,
}
```

---

## Health Check Endpoints

### Queue Health Endpoint

```bash
curl http://localhost:8000/api/v1/health/queues
```

**Response:**

```json
{
  "timestamp": "2026-02-09T15:00:00.000Z",
  "overall_score": 85,
  "components": {
    "buffer": {
      "score": 90,
      "buffer_size": 5,
      "stats": {
        "retried": 100,
        "succeeded": 98,
        "failed": 2,
        "remaining": 5
      },
      "alerts": []
    },
    "consumer_lag": {
      "score": 95,
      "lag": 150,
      "alerts": []
    },
    "dlq": {
      "score": 70,
      "celery_dlq_size": 45,
      "kafka_dlq_size": 20,
      "total_dlq_size": 65,
      "alerts": [
        {
          "severity": "warning",
          "message": "DLQ size elevated: 65 entries",
          "metric": "dlq_size",
          "value": 65
        }
      ]
    }
  },
  "alerts": [
    {
      "severity": "warning",
      "message": "DLQ size elevated: 65 entries (Celery: 45, Kafka: 20)",
      "metric": "dlq_size",
      "value": 65
    }
  ]
}
```

---

## Periodic Health Checks

### Run Health Checks Every Minute

Add to your application startup:

```python
from app.monitoring.message_queue_monitoring import run_periodic_health_checks, get_monitor

# Start background task
import asyncio

async def start_monitoring():
    monitor = get_monitor()
    asyncio.create_task(
        run_periodic_health_checks(
            monitor=monitor,
            interval_seconds=60  # Check every minute
        )
    )

# Call in app startup
@app.on_event("startup")
async def startup_event():
    await start_monitoring()
```

---

## Grafana Dashboard Setup

### 1. Import Dashboard

Create `grafana-dashboard.json`:

```json
{
  "dashboard": {
    "title": "Message Queue Health",
    "panels": [
      {
        "title": "Queue Health Score",
        "targets": [
          {
            "expr": "queue_health_score{queue_type=\"kafka\"}"
          }
        ]
      },
      {
        "title": "DLQ Size",
        "targets": [
          {
            "expr": "kafka_dlq_size"
          },
          {
            "expr": "celery_dlq_size"
          }
        ]
      },
      {
        "title": "Consumer Lag",
        "targets": [
          {
            "expr": "kafka_consumer_lag"
          }
        ]
      },
      {
        "title": "Message Publish Rate",
        "targets": [
          {
            "expr": "rate(kafka_messages_published_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### 2. Access Dashboard

```bash
# Start Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Access at http://localhost:3000
# Default credentials: admin/admin
```

---

## Monitoring Tasks

### Daily Monitoring Checklist

- [ ] Check overall queue health score (should be > 80)
- [ ] Review DLQ size (should be < warning threshold)
- [ ] Check consumer lag (should be < 1000)
- [ ] Review failed messages in buffer
- [ ] Check for alert escalation

### Weekly Maintenance

```bash
# 1. Review DLQ entries
SELECT COUNT(*), reason, status
FROM kafka_dead_letter_tasks
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY reason, status;

# 2. Clean up old resolved entries
-- This is automated via cleanup_old_dlq_entries()
-- But you can run manually if needed

# 3. Review buffer size
redis-cli --scan --pattern "kafka:buffer:*" | wc -l

# 4. Check consumer lag metrics
curl http://localhost:8000/metrics | grep kafka_consumer_lag
```

---

## Troubleshooting

### High DLQ Size

**Symptoms:**
- DLQ size > warning threshold
- Alerts firing for dlq_size

**Investigation:**

```sql
-- Check top failure reasons
SELECT reason, COUNT(*) as count
FROM kafka_dead_letter_tasks
WHERE status = 'pending'
GROUP BY reason
ORDER BY count DESC
LIMIT 10;

-- Check by task/event type
SELECT event_type, COUNT(*) as count
FROM kafka_dead_letter_tasks
WHERE status = 'pending'
GROUP BY event_type
ORDER BY count DESC
LIMIT 10;
```

**Resolution:**

1. Check if errors are transient (network, timeout)
2. Review recent deployments for breaking changes
3. Run DLQ retry manually:
   ```python
   from app.events.producer import KafkaEventProducer

   producer = KafkaEventProducer()
   await producer.start()
   stats = await producer.retry_from_buffer()
   ```

### High Consumer Lag

**Symptoms:**
- Consumer lag > warning threshold
- Messages not being processed fast enough

**Investigation:**

```bash
# Check consumer processing duration
curl http://localhost:8000/metrics | grep kafka_consumer_processing_duration_seconds

# Check for slow handlers
# Look for handlers with high p95/p99 durations
```

**Resolution:**

1. Scale consumer instances
2. Optimize slow handler functions
3. Check for database bottlenecks
4. Review batch processing configuration

### Message Loss Detected

**Symptoms:**
- `message_loss_rate` metric elevated
- Publish count >> consume count

**Investigation:**

```bash
# Check publish vs consume rates
curl http://localhost:8000/metrics | grep -E "(messages_published|messages_consumed)"

# Check buffer size (messages waiting to retry)
redis-cli --scan --pattern "kafka:buffer:*" | wc -l
```

**Resolution:**

1. Check Kafka broker health
2. Review network connectivity
3. Run buffer retry to flush persisted messages
4. Check for handler errors causing commits to fail

---

## Performance Tuning

### Optimize Retry Intervals

```python
# In app/events/producer.py, adjust backoff calculation:

def _calculate_backoff(self, attempt: int) -> float:
    base_delay = 0.5  # Reduce from 1.0 to 0.5
    max_delay = 30.0  # Reduce from 60.0 to 30.0
    # ... rest of function
```

### Adjust Buffer TTL

```python
# In app/events/producer.py, adjust buffer retention:

BUFFER_TTL_SECONDS = 3 * 24 * 60 * 60  # 3 days instead of 7
```

### Tune Consumer Batch Size

```python
# In app/events/consumer.py, adjust batch processing:

consumer = KafkaEventConsumer(
    topics=["assessment-events"],
    group_id="assessment-consumers",
    max_poll_records=50,  # Reduce from 100 to 50
)
```

---

## Emergency Procedures

### 1. Flush Persistent Buffer

If Kafka is back online after being down:

```python
from app.events.producer import KafkaEventProducer

producer = KafkaEventProducer()
await producer.start()

# Flush all buffered events
stats = await producer.retry_from_buffer()
print(f"Flushed: {stats['succeeded']}, Failed: {stats['failed']}, Remaining: {stats['remaining']}")
```

### 2. Pause Message Processing

If system is overloaded:

```bash
# Stop consumers
# Kubernetes:
kubectl scale deployment psychsync-consumer --replicas=0

# Docker:
docker stop psychsync-consumer

# Or scale consumers to 0 in your deployment platform
```

### 3. Clear DLQ (Emergency Only)

**WARNING:** This will permanently delete failed events!

```python
from app.events.kafka_dlq import cleanup_old_dlq_entries

# Delete ALL DLQ entries (use only in extreme emergency)
result = await cleanup_old_dlq_entries(days_old=0)
print(f"Deleted: {result['deleted_count']} entries")
```

---

## Monitoring Integration with CI/CD

### Pre-Deployment Health Check

Add to your deployment pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Check Queue Health
  run: |
    curl -f http://staging.example.com/api/v1/health/queues || exit 1

- name: Verify DLQ Size
  run: |
    SCORE=$(curl -s http://staging.example.com/api/v1/health/queues | jq '.overall_score')
    if [ "$SCORE" -lt 80 ]; then
      echo "Queue health score too low: $SCORE"
      exit 1
    fi
```

---

## Summary

This monitoring system provides:

✅ **Real-time visibility** into queue health
✅ **Automated alerting** for critical issues
✅ **Comprehensive metrics** for performance analysis
✅ **Graceful degradation** with persistent buffers
✅ **Emergency procedures** for crisis management

**Next Steps:**
1. Deploy to staging environment
2. Monitor for 24-48 hours
3. Tune alert thresholds based on observed metrics
4. Deploy to production with monitoring enabled

---

**Questions?** See `MESSAGE_QUEUE_DROPPED_MESSAGE_FIXES_COMPLETE.md` for detailed fix information.
