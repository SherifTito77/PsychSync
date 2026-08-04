# Distributed Rate Limiting Test

## Overview

This test validates that **Redis-backed distributed rate limiting** works correctly across multiple application instances. This is critical for production environments where you have multiple app instances behind a load balancer.

## Why This Matters

### The Problem
Without distributed rate limiting, each app instance maintains its own in-memory rate limit counter. A malicious user could:

```
Instance 1: [User] → 30 requests (throttled) ✗
Instance 2: [User] → 30 requests (throttled) ✗
Instance 3: [User] → 30 requests (throttled) ✗
Total: 90 requests allowed instead of 30! ✗✗✗
```

### The Solution
With Redis-backed rate limiting, all instances share the same counter:

```
Instance 1: [User] → 30 requests (throttled) ✓
Instance 2: [User] → Already throttled ✓
Instance 3: [User] → Already throttled ✓
Total: 30 requests allowed globally ✓✓✓
```

## Test Architecture

```
                    ┌─────────────────┐
                    │   Nginx LB      │
                    │   (Port 8080)   │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼─────┐┌───▼─────┐┌───▼─────┐
         │  Backend 1  ││Backend 2││Backend 3│
         │  (Port 8001)││(8002)   ││(8003)   │
         └──────┬─────┘└───┬─────┘└───┬─────┘
                │            │            │
                └────────────┼────────────┘
                             │
                    ┌────────▼────────┐
                    │  Shared Redis    │
                    │  (Port 6379)     │
                    └─────────────────┘
```

## Test Phases

### Phase 1: Load Balancer Test
- Sends 50 requests through the load balancer
- Verifies rate limiting is enforced (~30 successful, ~20 throttled)
- Validates that requests are distributed across instances

### Phase 2: Direct Instance Test
- Sends 20 requests directly to each instance
- Verifies all instances show throttling (shared Redis state)
- Confirms users can't bypass limits by hitting different instances

### Phase 3: Rate Limit Reset Test
- Waits 65 seconds for rate limit window to reset
- Verifies requests are accepted again
- Confirms reset is synchronized across all instances

## Quick Start

### Automated Test (Recommended)

```bash
# Run everything with one script
cd /path/to/psychsync
./tests/load/run_distributed_test.sh
```

This script will:
1. Stop any existing test containers
2. Start 3 backend instances + Redis + Nginx
3. Wait for services to be healthy
4. Run the distributed test
5. Display results and logs

### Manual Test

```bash
# 1. Start the distributed test environment
docker-compose -f docker-compose.distributed-test.yml up -d --build

# 2. Wait for services to be healthy (check with: docker-compose ps)
# Wait about 20-30 seconds for all backends to initialize

# 3. Run the test
python tests/load/test_rate_limiting_load.py --distributed

# 4. View logs if needed
docker-compose -f docker-compose.distributed-test.yml logs -f backend-1

# 5. Stop the environment when done
docker-compose -f docker-compose.distributed-test.yml down
```

## Configuration

### Environment Variables

The distributed test uses these settings in `docker-compose.distributed-test.yml`:

```yaml
environment:
  - REDIS_URL=redis://redis:6379/2  # Shared Redis for rate limiting
  - DATABASE_URL=postgresql+...      # Shared database
```

### Rate Limiting Settings

Current configuration in `app/middleware/simple_rate_limit.py`:

```python
RATE_LIMITED_PATHS = [
    "/api/v1/health",  # 30 requests per minute
    "/api/v1/auth/",   # 30 requests per minute
]
```

**Note**: For distributed testing, you need to update the rate limiter to use Redis instead of in-memory storage.

## Expected Results

### ✅ Pass Criteria

1. **Load Balancer Test**: ~30 successful, ~20 throttled
2. **Instance Test**: All 3 instances show throttling
3. **Reset Test**: Requests accepted after 65s wait

### ❌ Fail Indicators

1. All requests succeed (no rate limiting)
2. Different instances allow different amounts
3. Rate limit doesn't reset properly

## Troubleshooting

### Issue: "Connection refused" errors

**Cause**: Services not fully started yet

**Solution**:
```bash
# Check service status
docker-compose -f docker-compose.distributed-test.yml ps

# View logs for a specific service
docker-compose -f docker-compose.distributed-test.yml logs backend-1

# Wait a bit longer and retry
```

### Issue: "All requests succeed" (no throttling)

**Cause**: Rate limiter might be using in-memory storage instead of Redis

**Solution**:
1. Check that `REDIS_URL` is set correctly
2. Verify the rate limiter imports and uses Redis backend
3. Check if `app/middleware/simple_rate_limit.py` is using Redis

### Issue: "Different instances allow different amounts"

**Cause**: Instances not connecting to the same Redis

**Solution**:
```bash
# Check Redis connection
docker-compose -f docker-compose.distributed-test.yml logs backend-1 | grep redis

# Verify all instances use same REDIS_URL
docker-compose -f docker-compose.distributed-test.yml config | grep REDIS_URL
```

## Next Steps for Production

### 1. Upgrade to Redis-Backed Rate Limiting

The current implementation uses in-memory storage. For production:

```python
# In app/middleware/simple_rate_limit.py
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379/2")

async def check_rate_limit_redis(request, limit=30, window=60):
    """Redis-backed rate limiting"""
    key = f"ratelimit:{client_ip}:{path}"

    # Use Redis pipeline for atomic operations
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    results = await pipe.execute()

    count = results[0]

    if count > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### 2. Add User-Based Rate Limiting

For authenticated endpoints:

```python
# Use user_id instead of IP for authenticated requests
if user_id := get_current_user_id(request):
    key = f"ratelimit:user:{user_id}:{path}"
else:
    key = f"ratelimit:ip:{client_ip}:{path}"
```

### 3. Configure Different Limits per Endpoint

```python
RATE_LIMITS = {
    "/api/v1/health": {"limit": 30, "window": 60},
    "/api/v1/auth/login": {"limit": 10, "window": 60},
    "/api/v1/admin/*": {"limit": 50, "window": 60},
}
```

## Files Modified

1. `docker-compose.distributed-test.yml` - Multi-instance setup
2. `tests/load/nginx-test.conf` - Load balancer configuration
3. `tests/load/test_rate_limiting_load.py` - Added distributed test
4. `tests/load/run_distributed_test.sh` - Automated test script

## Credits

Implementation by: Human (TODO(human) section completed)
Date: 2025-01-20
Test validates: Distributed rate limiting architecture
