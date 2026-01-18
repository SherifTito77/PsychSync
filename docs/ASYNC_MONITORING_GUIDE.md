# Monitoring Configuration for Async Endpoints

**Purpose**: Monitor async endpoints for blocking operations, errors, and performance issues

---

## Prometheus Metrics Configuration

### Endpoint to add to `app/main.py`:

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Async endpoint monitoring metrics
async_endpoint_requests = Counter(
    'async_endpoint_requests_total',
    'Total async endpoint requests',
    ['endpoint', 'method', 'status']
)

async_endpoint_duration = Histogram(
    'async_endpoint_duration_seconds',
    'Async endpoint request duration',
    ['endpoint', 'method'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

async_endpoint_blocking = Counter(
    'async_endpoint_blocking_detected',
    'Blocking operations detected in async endpoints',
    ['endpoint', 'operation_type']
)

async_active_requests = Gauge(
    'async_active_requests',
    'Number of active async requests',
    ['endpoint']
)
```

### Middleware for Monitoring

Add to `app/middleware/async_monitoring.py`:

```python
import time
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram

class AsyncMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor async endpoints for blocking operations"""

    async def dispatch(self, request: Request, call_next):
        """Monitor request and detect blocking operations"""
        start_time = time.time()
        endpoint = request.url.path

        # Track active requests
        async_active_requests.labels(endpoint=endpoint).inc()

        try:
            # Set warning if request takes too long (possible blocking)
            response = await asyncio.wait_for(
                call_next(request),
                timeout=5.0  # Warn if > 5 seconds
            )

            # Record metrics
            duration = time.time() - start_time
            async_endpoint_requests.labels(
                endpoint=endpoint,
                method=request.method,
                status=response.status_code
            ).inc()

            async_endpoint_duration.labels(
                endpoint=endpoint,
                method=request.method
            ).observe(duration)

            # Alert on slow requests (possible blocking)
            if duration > 1.0:
                async_endpoint_blocking.labels(
                    endpoint=endpoint,
                    operation_type='slow_request'
                ).inc()

            return response

        except asyncio.TimeoutError:
            # Request blocked too long
            async_endpoint_blocking.labels(
                endpoint=endpoint,
                operation_type='timeout'
            ).inc()
            raise

        finally:
            async_active_requests.labels(endpoint=endpoint).dec()
```

---

## Grafana Dashboard Queries

### Dashboard: Async Endpoint Health

#### Panel 1: Request Rate by Endpoint
```promql
rate(async_endpoint_requests_total[5m])
```
**Format**: Graph
**Alert**: If rate drops suddenly, endpoints may be blocked

#### Panel 2: P95 Response Time
```promql
histogram_quantile(0.95, rate(async_endpoint_duration_seconds_bucket[5m]))
```
**Format**: Graph
**Warning threshold**: > 500ms
**Critical threshold**: > 1s

#### Panel 3: Blocking Detection
```promql
rate(async_endpoint_blocking_detected[5m])
```
**Format**: Stat
**Warning**: Any value > 0 indicates blocking

#### Panel 4: Active Concurrent Requests
```promql
async_active_requests
```
**Format**: Gauge
**Monitor**: Should scale with load, not stay constant

#### Panel 5: Error Rate by Endpoint
```promql
rate(async_endpoint_requests_total{status=~"5.."}[5m]) / rate(async_endpoint_requests_total[5m])
```
**Format**: Graph
**Warning threshold**: > 1%
**Critical threshold**: > 5%

---

## Alert Rules

### File: `alerting/async_endpoints.yml`

```yaml
groups:
  - name: async_endpoints
    interval: 30s
    rules:
      - alert: AsyncEndpointBlocking
        expr: rate(async_endpoint_blocking_detected[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Blocking operations detected in async endpoints"
          description: "Endpoint {{ $labels.endpoint }} has blocking operations"

      - alert: AsyncEndpointSlowResponse
        expr: histogram_quantile(0.95, rate(async_endpoint_duration_seconds_bucket[5m])) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Async endpoint slow responses"
          description: "P95 response time for {{ $labels.endpoint }} is {{ $value }}s"

      - alert: AsyncEndpointHighErrorRate
        expr: rate(async_endpoint_requests_total{status=~"5.."}[5m]) / rate(async_endpoint_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on async endpoints"
          description: "Error rate for {{ $labels.endpoint }} is {{ $value | humanizePercentage }}"

      - alert: AsyncEndpointTimeout
        expr: rate(async_endpoint_blocking_detected{operation_type="timeout"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Async endpoint timeouts detected"
          description: "Endpoint {{ $labels.endpoint }} is experiencing timeouts"
```

---

## Log Monitoring

### Critical Log Patterns to Monitor

#### 1. Blocking Operation Warnings
```python
# Add to your async endpoints
import time
import logging

logger = logging.getLogger(__name__)

async def some_async_operation():
    start = time.time()

    # Your operation here

    elapsed = time.time() - start
    if elapsed > 0.5:  # Log if > 500ms
        logger.warning(
            f"Slow async operation detected: {elapsed:.3f}s",
            extra={"operation": "some_async_operation", "duration": elapsed}
        )
```

#### 2. Event Loop Blocking
```python
# Monitor event loop health
import asyncio

async def check_event_loop_health():
    """Log if event loop is blocked"""
    try:
        await asyncio.wait_for(asyncio.sleep(0), timeout=0.1)
    except asyncio.TimeoutError:
        logger.error("Event loop is blocked!")
```

### ELK/Loki Queries

#### Find Slow Operations
```
{app="psychsync", level="warning"}
| json
| duration > 0.5
| group by operation
| avg(duration)
```

#### Find Blocking Operations
```
{app="psychsync"}
|~ "blocking|blocked|timeout"
| group by endpoint
| count
```

---

## Health Check Endpoints

### Add to Monitoring

```python
@router.get("/health/async")
async def async_health_check():
    """Check async endpoint health"""
    checks = {
        "event_loop": "healthy",
        "active_requests": 0,
        "blocking_detected": False
    }

    # Check event loop responsiveness
    try:
        start = time.time()
        await asyncio.wait_for(asyncio.sleep(0), timeout=0.1)
        if time.time() - start > 0.05:
            checks["event_loop"] = "slow"
    except asyncio.TimeoutError:
        checks["event_loop"] = "blocked"

    # Check active requests
    active = async_active_requests.labels(endpoint="/")._value.get()
    checks["active_requests"] = active

    # Check for blocking in last minute
    blocking = async_endpoint_blocking.labels(endpoint="/")._value.get()
    checks["blocking_detected"] = blocking > 0

    status_code = 200 if all([
        checks["event_loop"] == "healthy",
        checks["blocking_detected"] == False
    ]) else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if status_code == 200 else "unhealthy",
            "checks": checks,
            "timestamp": time.time()
        }
    )
```

---

## Performance Baselines

### Expected Performance Metrics

| Endpoint Type | P50 Latency | P95 Latency | P99 Latency | Max Throughput |
|---------------|-------------|-------------|-------------|----------------|
| Simple GET    | < 50ms      | < 100ms     | < 200ms     | 500+ RPS       |
| Complex GET   | < 100ms     | < 250ms     | < 500ms     | 200+ RPS       |
| POST/PUT      | < 150ms     | < 400ms     | < 750ms     | 100+ RPS       |
| DELETE        | < 100ms     | < 250ms     | < 500ms     | 200+ RPS       |

### Red Flags (Investigate Immediately)

- ⚠️ P95 latency > 1 second for any endpoint
- ⚠️ Error rate > 1% for any endpoint
- ⚠️ Request rate drops suddenly (possible blocking)
- ⚠️ Active requests count stays high (requests stuck)
- ⚠️ Timeout errors increasing
- ⚠️ Event loop blocked warnings in logs

---

## Incident Response

### If Blocking Detected

1. **Identify the endpoint**:
   ```bash
   curl -s http://localhost:9090/api/v1/query?query=async_endpoint_blocking_detected | jq .
   ```

2. **Check the code**:
   - Look for `db.query()` not wrapped in `run_in_executor()`
   - Look for long-running operations not using `await`
   - Check for CPU-intensive operations

3. **Quick fix**:
   - Wrap blocking operation in `run_in_executor()`
   - Or convert to true async operation

4. **Deploy fix**:
   ```bash
   ./scripts/deploy_async_fixes.sh
   ```

5. **Monitor**:
   - Watch for blocking counter to stop increasing
   - Verify P95 latency returns to baseline

---

## Rolling Back

If async conversion causes issues:

```bash
# 1. Stop the service
systemctl stop psychsync

# 2. Revert to previous commit
git revert <commit-hash>

# 3. Restart
systemctl start psychsync

# 4. Verify health
curl http://localhost:8000/api/v1/health/async
```

---

## Summary

**Monitoring Stack**:
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards
- ✅ AlertManager rules
- ✅ Log aggregation (Loki/ELK)
- ✅ Health check endpoints

**Key Metrics**:
- Request rate per endpoint
- P50/P95/P99 latency
- Blocking operation counter
- Active concurrent requests
- Error rate

**Alert Thresholds**:
- Warning: P95 > 500ms
- Critical: P95 > 1s
- Critical: Error rate > 5%
- Warning: Any blocking detected
