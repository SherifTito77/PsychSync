# Retry Logic Enhancement - Usage Guide

## Overview

This document shows how to use the enhanced retry logic system with:
- ✅ Prometheus metrics integration
- ✅ Circuit breaker protection
- ✅ Environment-based configuration
- ✅ Dead Letter Queue (DLQ) for failed operations

---

## Quick Start

### 1. Using the `@with_retry` Decorator

```python
from app.core.retry_wrapper import with_retry
from app.core.retry_config import get_retry_config

@with_retry(component="database", operation="create_user")
async def create_user(db, user_data):
    """Create user with automatic retry"""
    return await db.execute(insert(User).values(**user_data))
```

### 2. Using the Functional Form

```python
from app.core.retry_wrapper import retry_async

async def get_user(db, user_id):
    """Fetch user with automatic retry"""
    result = await retry_async(
        "database",
        "fetch_user",
        db.execute,
        select(User).where(User.id == user_id)
    )
    return result
```

---

## Environment Configuration

### Global Retry Settings

```bash
# .env or environment variables
RETRY_MAX_RETRIES=3
RETRY_BASE_DELAY=1.0
RETRY_MAX_DELAY=30.0
RETRY_JITTER_ENABLED=true
RETRY_JITTER_PERCENTAGE=0.25
RETRY_CIRCUIT_BREAKER_ENABLED=true
RETRY_METRICS_ENABLED=true
RETRY_METRICS_TYPE=prometheus
```

### Component-Specific Overrides

```bash
# Database - more aggressive retries
DATABASE_RETRY_MAX_RETRIES=5
DATABASE_RETRY_BASE_DELAY=0.5
DATABASE_RETRY_MAX_DELAY=5.0

# Webhooks - longer delays
WEBHOOK_RETRY_MAX_RETRIES=3
WEBHOOK_RETRY_BASE_DELAY=2.0
WEBHOOK_RETRY_MAX_DELAY=60.0

# Email - standard settings
EMAIL_SMTP_RETRY_MAX_RETRIES=3
EMAIL_SMTP_RETRY_BASE_DELAY=1.0

# HRIS API - longer max delay
HRIS_API_RETRY_MAX_DELAY=60.0
```

---

## Migration Examples

### Example 1: Database Operations

**Before:**
```python
async def create_user(db, user_data):
    try:
        return await db.execute(insert(User).values(**user_data))
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise
```

**After:**
```python
from app.core.retry_wrapper import with_retry

@with_retry(component="database", operation="create_user")
async def create_user(db, user_data):
    return await db.execute(insert(User).values(**user_data))
```

### Example 2: External API Calls

**Before:**
```python
async def send_webhook(url, payload):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
```

**After:**
```python
from app.core.retry_wrapper import with_retry

@with_retry(component="webhook", operation="send")
async def send_webhook(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()
```

### Example 3: Email Sending

**Before:**
```python
async def send_email(to, subject, body):
    for attempt in range(3):
        try:
            with smtplib.SMTP(server, port) as smtp:
                smtp.send_message(msg)
                return
        except smtplib.SMTPException:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            raise
```

**After:**
```python
from app.core.retry_wrapper import with_retry

@with_retry(component="email_smtp", operation="send")
async def send_email(to, subject, body):
    with smtplib.SMTP(server, port) as smtp:
        smtp.send_message(msg)
        return
```

---

## Monitoring & Observability

### 1. Prometheus Metrics

Access metrics at: `GET /api/v1/admin/retry/metrics`

**Metrics Available:**
- `retry_attempts_total{component="..."}` - Total retry attempts
- `retry_success_total{component="..."}` - Successful operations
- `retry_failure_total{component="..."}` - Failed operations
- `retry_rate_percentage{component="..."}` - Retry rate
- `retry_avg_duration_ms{component="..."}` - Average duration
- `retry_dlq_size` - Dead Letter Queue size
- `retry_overall_rate` - System-wide retry rate

### 2. Dead Letter Queue

**View DLQ entries:**
```bash
GET /api/v1/admin/retry/dlq
```

**View DLQ statistics:**
```bash
GET /api/v1/admin/retry/dlq/stats
```

**Clear DLQ entries:**
```bash
POST /api/v1/admin/retry/dlq/clear?component=webhook
```

### 3. Health Check

**Check retry system health:**
```bash
GET /api/v1/admin/retry/health
```

**Get high retry rate components:**
```bash
GET /api/v1/admin/retry/components/high-retry-rate?threshold=20.0
```

---

## Component Configuration Reference

| Component | Default Max Retries | Base Delay | Max Delay | Use Case |
|-----------|---------------------|------------|-----------|----------|
| `database` | 3 | 0.5s | 5.0s | SQL operations with serialization errors |
| `webhook` | 3 | 1.0s | 30.0s | External webhook delivery |
| `email_smtp` | 3 | 1.0s | 30.0s | Email sending via SMTP |
| `email_imap` | 3 | 1.0s | 30.0s | Email fetching via IMAP |
| `hris_api` | 3 | 1.0s | 30.0s | HRIS API calls |
| `hris_db` | 3 | 0.5s | 5.0s | HRIS database access |
| `default` | 3 | 1.0s | 30.0s | General purpose |

---

## Integration with Existing Code

### Option 1: Gradual Migration (Recommended)

Add the decorator to new critical paths first:

```python
# New code uses @with_retry
@with_retry(component="database", operation="critical_operation")
async def critical_operation(db):
    return await db.execute(critical_query)

# Existing code continues to work
async def legacy_operation(db):
    return await db.execute(legacy_query)
```

### Option 2: Update Central Functions

Update shared utility functions:

```python
# In app/db/base.py
from app.core.retry_wrapper import with_retry

@with_retry(component="database", operation="db_execute")
async def execute_with_retry(db, query, params=None):
    return await db.execute(query, params)
```

### Option 3: Middleware Integration

Add retry at the API layer:

```python
# In app/api/deps.py
from app.core.retry_wrapper import retry_async

async def get_user_with_retry(user_id: int):
    return await retry_async(
        "database",
        "get_user_by_id",
        db.execute,
        select(User).where(User.id == user_id)
    )
```

---

## Grafana Dashboard Queries

### Retry Rate by Component
```promql
rate(retry_attempts_total[5m]) * 100
```

### Failure Rate
```promql
sum(rate(retry_failure_total[5m])) / sum(rate(retry_attempts_total[5m])) * 100
```

### DLQ Size Alert
```promql
retry_dlq_size > 100
```

### High Retry Rate Components
```promql
topk(5, retry_rate_percentage)
```

---

## Troubleshooting

### High Retry Rate?

1. **Check metrics:**
   ```bash
   curl http://localhost:8000/api/v1/admin/retry/summary
   ```

2. **View alerts:**
   ```bash
   curl http://localhost:8000/api/v1/admin/retry/alerts
   ```

3. **Inspect DLQ:**
   ```bash
   curl http://localhost:8000/api/v1/admin/retry/dlq?component=webhook
   ```

### Need to Tune Retry Settings?

Update environment variables and restart:
```bash
# Increase retries for database
export DATABASE_RETRY_MAX_RETRIES=5
export DATABASE_RETRY_BASE_DELAY=0.5

# Restart service
systemctl restart psychsync-backend
```

### Circuit Breaker Tripping?

Circuit breakers open after 5 failures by default. Adjust:
```bash
export RETRY_CIRCUIT_BREAKER_THRESHOLD=10  # More failures before opening
```

---

## Production Checklist

- [ ] Configure environment variables for retry settings
- [ ] Add Prometheus scraping endpoint to monitoring
- [ ] Set up Grafana dashboards for retry metrics
- [ ] Configure alerts for high retry/failure rates
- [ ] Set up DLQ monitoring and alerting
- [ ] Test circuit breaker behavior
- [ ] Document component-specific retry requirements
- [ ] Train team on DLQ inspection and replay procedures
