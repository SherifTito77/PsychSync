# Rate Limiting Load Testing Suite

This directory contains comprehensive load testing tools to validate API rate limiting and throttling behavior under stress.

## Overview

The load testing suite validates:

- **User Tier-Based Rate Limiting** - Different limits for anonymous, basic, premium, and admin users
- **Per-Endpoint Rate Limiting** - Stricter limits for auth endpoints, lenient for health checks
- **Sliding Window Accuracy** - Proper rate limit resets and window management
- **IP-based vs User-based Limiting** - Correct handling of anonymous vs authenticated requests
- **Rate Limit Headers** - Accurate `X-RateLimit-*` headers in responses
- **Concurrent Load Handling** - Correct behavior under high concurrent request volumes
- **Redis Atomic Operations** - Distributed rate limiting across multiple app instances

## Rate Limit Configuration

### User Tier Limits (requests per minute)

| Tier      | Per Minute | Per Hour | Per Day |
|-----------|------------|----------|---------|
| ANONYMOUS | 50         | 200      | 1,000   |
| BASIC     | 200        | 1,000    | 10,000  |
| PREMIUM   | 500        | 2,500    | 50,000  |
| ENTERPRISE| 1,000      | 5,000    | 100,000 |
| ADMIN     | 2,000      | 10,000   | 200,000 |

### Endpoint Multipliers

- `POST:/api/v1/auth/token` - 0.5x (stricter)
- `POST:/api/v1/users` - 0.3x (very strict)
- `GET:/api/v1/health` - 2.0x (lenient)
- `GET:/api/v1/analytics` - 0.5x (stricter)

## Test Files

### 1. `test_rate_limiting_load.py`
Pytest-based load tests with precise control and assertions.

**Tests:**
- `test_rate_limit_basic_tier_under_load` - Validates 200/min limit for BASIC tier
- `test_rate_limit_auth_endpoints_stricter_limits` - Confirms auth endpoints have 0.5x multiplier
- `test_rate_limit_sliding_window_accuracy` - Tests window reset behavior
- `test_rate_limit_different_user_tiers` - Validates all tier limits
- `test_rate_limit_ip_based_vs_user_based` - Confirms proper separation
- `test_rate_limit_headers_accuracy` - Validates response headers

**Running:**
```bash
# Run all load tests
python -m pytest tests/load/test_rate_limiting_load.py -v -m load

# Run specific test
python -m pytest tests/load/test_rate_limiting_load.py::test_rate_limit_basic_tier_under_load -v

# Run with verbose output
python -m pytest tests/load/test_rate_limiting_load.py -v -s
```

### 2. `locustfile.py`
Locust-based load tests with realistic user behavior patterns.

**User Types:**
- `AnonymousUser` - Unauthenticated browsing (50/min limit)
- `BasicUser` - Regular authenticated user (200/min limit)
- `PremiumUser` - High-volume user (500/min limit)
- `AdminUser` - Administrative user (2000/min limit)
- `StresstestUser` - Maximum load testing (disabled by default)

**Running:**
```bash
# Interactive web UI (recommended for exploration)
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089

# Headless mode (automated testing)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=2m \
    --headless \
    --html=reports/locust_report.html

# Stress test (caution: very high load)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=1000 \
    --spawn-rate=100 \
    --run-time=5m \
    --headless
```

### 3. `run_load_tests.sh`
Convenience script to run all load tests.

```bash
# Make executable (first time only)
chmod +x tests/load/run_load_tests.sh

# Run all tests
./tests/load/run_load_tests.sh

# Run only pytest tests
./tests/load/run_load_tests.sh pytest

# Run only Locust tests
./tests/load/run_load_tests.sh locust

# Quick validation test
./tests/load/run_load_tests.sh quick

# Check if services are running
./tests/load/run_load_tests.sh check
```

## Quick Start

1. **Start required services:**
   ```bash
   # Terminal 1: Backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

   # Terminal 2: Redis
   redis-server
   # OR with Docker
   docker-compose up -d redis
   ```

2. **Run quick validation:**
   ```bash
   ./tests/load/run_load_tests.sh quick
   ```

3. **Run full test suite:**
   ```bash
   ./tests/load/run_load_tests.sh pytest
   ```

## Interpreting Results

### Expected Behavior

✅ **Healthy Rate Limiting:**
- Requests within limits are accepted (HTTP 200)
- Requests exceeding limits are throttled (HTTP 429)
- Rate limit headers are accurate and decrement properly
- Response times remain acceptable (< 1s average, < 2s P95)
- Different tiers have appropriate different limits

❌ **Unhealthy Behavior:**
- Requests exceed defined limits (rate limiting not working)
- All requests are throttled (limit too strict)
- Response times degrade significantly (> 2s average)
- Rate limit headers missing or inaccurate
- Crashes or errors under load

### Example Output

```
✓ BASIC Tier Load Test Results:
  - Total requests: 300
  - Successful: 200 (limit: 200)
  - Throttled: 100
  - Throttle rate: 33.3%
  - Avg response time: 0.245s
  - P95 response time: 0.892s
```

## Performance Baselines

Based on the rate limiting configuration, these are expected performance characteristics:

### Concurrent Load Handling
- **100 concurrent users** - Should handle without significant throttling (for BASIC tier)
- **500 concurrent users** - Expect ~60% throttle rate for BASIC tier
- **1000 concurrent users** - Expect ~80% throttle rate for BASIC tier

### Response Time Targets
- **Average**: < 500ms
- **P95**: < 1000ms
- **P99**: < 2000ms

### Throughput Targets
- **Anonymous**: ~50 req/min sustained
- **Basic**: ~200 req/min sustained
- **Premium**: ~500 req/min sustained
- **Admin**: ~2000 req/min sustained

## Advanced Testing

### Testing Distributed Rate Limiting

To validate Redis-based rate limiting across multiple app instances:

```bash
# Terminal 1: Start first backend instance
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start second backend instance
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Run load tests against both instances
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=200 \
    --spawn-rate=20
```

Both instances should share the same Redis-based rate limits, meaning:
- Combined requests across both instances are rate limited
- User cannot exceed limits by hitting different instances

### Testing Sliding Window Reset

```bash
# Send burst of requests right at limit
for i in {1..200}; do
  curl -s http://localhost:8000/api/v1/health
done

# Wait for window to expire (~60 seconds)
sleep 65

# Should be able to send requests again
curl -s http://localhost:8000/api/v1/health
# Should return 200, not 429
```

## Troubleshooting

### Issue: All Requests Are Throttled

**Possible causes:**
- Redis is not running (fallback to in-memory may have issues)
- Rate limits configured too low
- Previous test run didn't clean up properly

**Solution:**
```bash
# Check Redis
redis-cli ping

# Clear rate limit keys
redis-cli FLUSHDB

# Restart backend
```

### Issue: No Requests Are Throttled

**Possible causes:**
- Rate limiting middleware not enabled
- Test user has admin tier
- Request rate too slow to hit limits

**Solution:**
```bash
# Check if rate limiting is enabled
curl -I http://localhost:8000/api/v1/health
# Look for X-RateLimit-* headers

# Increase request rate
locust -f tests/load/locustfile.py --users=1000 --spawn-rate=100
```

### Issue: High Response Times Under Load

**Possible causes:**
- Redis connection bottleneck
- Database connection pool exhausted
- Insufficient system resources

**Solution:**
```bash
# Check Redis connection pool
redis-cli --latency

# Check database connections
redis-cli CLIENT LIST | wc -l

# Monitor system resources
htop
```

## Reports

After running Locust tests, HTML reports are generated:

```bash
# View latest report
open reports/locust_rate_limit_report.html

# View stats CSV
cat reports/locust_rate_limit_stats_stats.csv
```

## TODO

See the code for a TODO(human) task for implementing distributed rate limiting tests across multiple app instances.

## References

- [Rate Limiting Implementation](../../app/core/rate_limiter_unified.py)
- [API Rate Limiter](../../app/core/api_rate_limiter.py)
- [Rate Limiting Middleware](../../app/middleware/rate_limiting.py)
- [Locust Documentation](https://docs.locust.io/)
