# Database Monitoring Configuration Guide

## Quick Start

### 1. Configure Environment Variables

Add to your `.env` file:

```bash
# Basic configuration
DB_ERROR_ALERT_THRESHOLD=10
DB_ERROR_REPORT_INTERVAL=60
DB_ERROR_ALERTS_ENABLED=true
```

### 2. View Monitoring Statistics

```bash
# View last 5 minutes
python scripts/view_db_monitoring_stats.py

# View last 15 minutes
python scripts/view_db_monitoring_stats.py --minutes 15

# Full report
python scripts/view_db_monitoring_stats.py --full-report

# Watch mode (auto-refresh every 10 seconds)
python scripts/view_db_monitoring_stats.py --watch
```

### 3. Start Standalone Monitoring (Optional)

```bash
# Run as background service
python scripts/start_db_monitoring.py

# Or run with nohup for production
nohup python scripts/start_db_monitoring.py > /var/log/db_monitoring.log 2>&1 &
```

---

## Configuration Options

### DB_ERROR_ALERT_THRESHOLD

**Description:** Alert when errors per minute exceed this value

**Default:** `10` (alert if >10 errors/minute)

**Examples:**
- Development: `5` (more sensitive)
- Staging: `10` (moderate)
- Production: `20` (less sensitive)
- Critical systems: `5` (very sensitive)

**How to Set:**
```bash
# In .env file
DB_ERROR_ALERT_THRESHOLD=10

# Or export directly
export DB_ERROR_ALERT_THRESHOLD=10
```

### DB_ERROR_REPORT_INTERVAL

**Description:** How often to generate monitoring reports (in minutes)

**Default:** `60` (every hour)

**Examples:**
- Development: `30` (frequent reports)
- Staging: `60` (standard)
- Production: `60` (standard)

**How to Set:**
```bash
DB_ERROR_REPORT_INTERVAL=60
```

### DB_ERROR_ALERTS_ENABLED

**Description:** Enable or disable automated alerts

**Default:** `true`

**How to Set:**
```bash
DB_ERROR_ALERTS_ENABLED=true
```

---

## Understanding Monitoring Output

### Health Score

The monitoring system calculates a health score from 0-100:

- **90-100**: ✅ EXCELLENT - No errors detected
- **75-89**: ✅ GOOD - Minimal errors
- **50-74**: ⚠️ FAIR - Moderate error rate
- **25-49**: 🟡 DEGRADED - High error rate
- **0-24**: 🔴 CRITICAL - Excessive errors

### Error Rate Classification

| Errors/Minute | Status | Action Required |
|---------------|--------|-----------------|
| 0 | ✅ Perfect | None |
| < 1 | ✅ Normal | None |
| 1-5 | ⚠️ Elevated | Monitor closely |
| 5-10 | 🟡 Warning | Investigate soon |
| > 10 | 🔴 Critical | Immediate action |

### Top Error Types

The system tracks which error types occur most frequently:

- **IntegrityError**: Constraint violations (duplicates, foreign keys)
- **OperationalError**: Connection issues, timeouts
- **ProgrammingError**: SQL syntax errors
- **TimeoutError**: Query timeouts

### Top Services

Identifies which services have the most errors, helping you prioritize fixes.

---

## Recommended Actions by Scenario

### Scenario 1: High IntegrityError Count

**Symptoms:** Many `IntegrityError` exceptions

**Likely Causes:**
- Race conditions in check-then-act patterns
- Missing unique constraints
- Concurrent updates to same records

**Actions:**
1. Review services with high IntegrityError counts
2. Add row-level locking (`.with_for_update()`)
3. Ensure database unique constraints exist
4. Use `safe_create`/`safe_update` utilities

### Scenario 2: High OperationalError Count

**Symptoms:** Many `OperationalError` exceptions

**Likely Causes:**
- Database connection issues
- Network problems
- Database server overload

**Actions:**
1. Check database connectivity
2. Review database server health
3. Check connection pool size
4. Verify network stability

### Scenario 3: Single Service with High Error Rate

**Symptoms:** One service has >50% of all errors

**Likely Causes:**
- Bug in specific service
- Missing error handling
- Resource contention

**Actions:**
1. Review logs for that specific service
2. Check recent deployments
3. Add `@monitor_db_errors` decorator
4. Use safe operations utilities

---

## Integration with Application

The monitoring system is automatically integrated into the application:

### Automatic Startup

When FastAPI starts, monitoring automatically begins:

```python
# app/main.py - lifespan function
async def lifespan(app: FastAPI):
    # ...
    # Database error monitoring starts automatically
    asyncio.create_task(
        start_database_error_monitoring(
            report_interval_minutes=60,
            alert_on_patterns=True,
        )
    )
    # ...
```

### Manual Monitoring

You can also manually check stats:

```python
from app.monitoring.database_error_monitor import db_monitor

# Get statistics
stats = db_monitor.get_error_stats(minutes=5)
print(f"Errors per minute: {stats['errors_per_minute']}")

# Generate report
report = db_monitor.generate_report()
print(report)
```

---

## Troubleshooting

### No Monitoring Data Available

**Problem:** `python scripts/view_db_monitoring_stats.py` shows no data

**Solution:**
1. Ensure the application is running
2. Check that monitoring started in application logs
3. Wait for some database operations to occur

### Alerts Not Triggering

**Problem:** Error rate exceeds threshold but no alerts

**Solution:**
1. Check `DB_ERROR_ALERT_THRESHOLD` setting
2. Verify `DB_ERROR_ALERTS_ENABLED=true`
3. Check alert cooldown (5 minutes between alerts)

### High Memory Usage

**Problem:** Monitor using too much memory

**Solution:**
1. Reduce `DB_ERROR_HISTORY_SIZE`
2. Decrease report interval
3. Clear history: `db_monitor.clear_history()`

---

## Best Practices

### 1. Development Environment

```bash
DB_ERROR_ALERT_THRESHOLD=5
DB_ERROR_REPORT_INTERVAL=30
```

More sensitive to catch issues early.

### 2. Staging Environment

```bash
DB_ERROR_ALERT_THRESHOLD=10
DB_ERROR_REPORT_INTERVAL=60
```

Balanced sensitivity and reporting.

### 3. Production Environment

```bash
DB_ERROR_ALERT_THRESHOLD=20
DB_ERROR_REPORT_INTERVAL=60
```

Less sensitive to avoid alert fatigue, but still catches critical issues.

### 4. Monitoring Critical Services

For critical services (authentication, payments):
- Add `@monitor_db_errors` decorator
- Use safe operations (`safe_create`, `safe_update`)
- Set lower alert thresholds
- Review stats frequently

---

## Advanced Configuration

### Custom Alert Handlers

To add custom alert handlers (Slack, email, etc.):

```python
# app/monitoring/database_error_monitor.py
async def _send_external_alert(self, message: str, error_summary: Dict[str, int]):
    """Send alert to external monitoring systems."""
    # TODO: Add Slack webhook
    # TODO: Add email notification
    # TODO: Add PagerDuty integration
    pass
```

### Custom Metrics

To add custom metric tracking:

```python
from app.monitoring.database_error_monitor import db_monitor

# Log custom error with context
db_monitor.log_error(
    service="my_service",
    operation="my_operation",
    error=exception,
    context={
        "user_id": user_id,
        "request_id": request_id,
        "custom_field": custom_value
    }
)
```

---

## Support

For issues or questions:
1. Check logs: Database errors are logged with full context
2. Review reports: Auto-generated every 60 minutes
3. Run stats viewer: `python scripts/view_db_monitoring_stats.py`

---

**Last Updated:** 2026-01-18
