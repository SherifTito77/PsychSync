# Redis Memory Monitoring Guide

This guide explains how to monitor Redis memory usage and verify that cache entries are properly expiring.

## Quick Start

### Prerequisites

```bash
# Install redis-py
pip install redis

# Ensure Redis is running
redis-cli ping
# Should return: PONG
```

### Basic Monitoring (10 minutes)

```bash
# Run a quick 10-minute monitoring session
python scripts/redis-memory-monitor.py --duration 10 --interval 10
```

### Full Monitoring (2 hours)

```bash
# Run comprehensive 2-hour monitoring
python scripts/redis-memory-monitor.py --duration 120 --interval 30
```

## Understanding the Output

### Sample Output

```
======================================================================
📊 Redis Metrics - Check #5
======================================================================
⏱️  Elapsed Time: 30.5 minutes

💾 Memory Usage:
   Used: 45.2M
   Peak: 48.1M
   Max: 0B
   Policy: allkeys-lru

📦 Cache Statistics:
   Total Keys: 1523
   Keys with TTL: 1450/1000 sampled
   TTL Coverage: 87.5%

🔑 Key Patterns:
   cache:user:*: 523
   cache:assessment:*: 342
   session:*: 298
   lock:*: 156
   other: 204
```

### Key Metrics Explained

#### Memory Usage
- **Used**: Current memory consumption
- **Peak**: Maximum memory used since Redis started
- **Max**: Configured memory limit (0 = unlimited)
- **Policy**: Eviction policy when memory limit is reached

**Healthy Range**:
- ✅ Growth < 50MB over 2 hours
- ⚠️  Growth 50-100MB - monitor closely
- 🚨 Growth > 100MB - investigate missing TTLs

#### Cache Statistics
- **Total Keys**: Number of keys in Redis
- **Keys with TTL**: Percentage of keys that will expire
- **TTL Coverage**: Critical metric - should be > 80%

**Healthy Range**:
- ✅ TTL Coverage > 80%
- ⚠️  TTL Coverage 60-80%
- 🚨 TTL Coverage < 60%

#### Key Patterns
Shows distribution of keys by pattern. Watch for:
- `cache:*` - Should have TTL (default 3600s)
- `session:*` - Should have TTL
- `lock:*` - Should expire (default 10s)
- `other` - Investigate unknown patterns

## Common Issues and Solutions

### Issue 1: Memory Keeps Growing

**Symptom**: Used memory increases linearly over time

**Diagnosis**:
```bash
# Check TTL coverage
redis-cli
> INFO keyspace
> SCAN 0 COUNT 1000
```

**Solution**: Verify all cache.set() calls have TTL:
```python
# ❌ Wrong - no TTL
await cache.set("key", value)

# ✅ Correct - with TTL
await cache.set("key", value, expire=3600)
```

### Issue 2: High Key Count, Low TTL Coverage

**Symptom**: Thousands of keys, but < 50% have TTL

**Diagnosis**:
```python
# Find keys without TTL
import redis
r = redis.Redis()
cursor = 0
keys_no_ttl = 0
while True:
    cursor, keys = r.scan(cursor, count=100)
    for key in keys:
        if r.ttl(key) == -1:  # -1 means no expiration
            keys_no_ttl += 1
            print(f"No TTL: {key}")
    if cursor == 0:
        break
```

**Solution**: Add default TTL to EnhancedCacheService:
```python
# In enhanced_cache_service.py
async def set(self, key, value, expire=None):
    if expire is None:
        expire = self.DEFAULT_TTL  # ✅ Uses default
    # ... rest of code
```

### Issue 3: Lock Keys Accumulating

**Symptom**: Many `lock:*` keys building up

**Diagnosis**:
```bash
redis-cli
> KEYS lock:*
> TTL lock:some-key  # Should return remaining seconds, not -1
```

**Solution**: Ensure locks are released:
```python
try:
    # ... do work
finally:
    await cache.delete(f"lock:{key}")
```

## Manual Redis Commands

### Check Memory Usage

```bash
# Current memory info
redis-cli INFO memory

# Get human-readable format
redis-cli --latency-history | grep used_memory

# Monitor in real-time
redis-cli --stat
```

### Find Large Keys

```bash
# Find keys > 1KB
redis-cli --bigkeys

# Find specific patterns
redis-cli --scan --pattern "cache:*" | head -20
```

### Check TTL Distribution

```bash
# Sample 1000 keys and check TTL
for i in {1..1000}; do
  key=$(redis-cli RANDOMKEY)
  ttl=$(redis-cli TTL "$key")
  echo "$key: $ttl"
done
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Redis Memory Monitor

on:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install redis

      - name: Start backend services
        run: |
          python -m uvicorn app.main:app &
          sleep 10

      - name: Generate cache load
        run: |
          python tests/generate_cache_load.py &
          LOAD_PID=$!

      - name: Run Redis monitor
        run: |
          python scripts/redis-memory-monitor.py \
            --duration 10 \
            --interval 5 \
            --output redis-results.json

      - name: Check results
        run: |
          python scripts/check-redis-results.py redis-results.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: redis-monitor-results
          path: redis-results.json
```

## Performance Tuning

### Redis Configuration

Edit `redis.conf`:

```conf
# Set maximum memory (e.g., 1GB)
maxmemory 1gb

# Eviction policy
maxmemory-policy allkeys-lru

# Save memory
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
```

### Backend Cache Configuration

In `app/core/config.py`:

```python
# Cache TTL values
CACHE_TTL_SHORT = 300      # 5 minutes
CACHE_TTL_MEDIUM = 1800    # 30 minutes
CACHE_TTL_LONG = 3600      # 1 hour
CACHE_TTL_EXTENDED = 7200  # 2 hours

# Maximum cache size
REDIS_MAX_MEMORY = 1024 * 1024 * 1024  # 1GB
```

## Troubleshooting

### "Connection Refused"

**Problem**: Can't connect to Redis

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# Or using Docker
docker-compose up -d redis
```

### "ImportError: No module named 'redis'"

**Problem**: redis-py not installed

**Solution**:
```bash
pip install redis

# Or using poetry
poetry add redis

# Or using pipenv
pipenv install redis
```

### Script Runs But Shows No Data

**Problem**: Redis is empty

**Solution**:
```bash
# Verify cache is being used
redis-cli
> DBSIZE  # Should show > 0
> KEYS *  # Should show some keys

# Generate some cache entries
curl http://localhost:8000/api/v1/health
```

## Best Practices

1. **Always set TTL**: Never set a cache key without expiration
2. **Use appropriate TTL**:
   - User session: 1 hour
   - API responses: 5-15 minutes
   - Computed results: 1-2 hours
   - Locks: 10 seconds

3. **Monitor regularly**: Run monitoring script weekly

4. **Set alerts**: Configure monitoring tools to alert on:
   - Memory growth > 100MB/hour
   - TTL coverage < 70%
   - Total keys > 100,000

5. **Review patterns**: Monthly review of key patterns to identify:
   - Unused prefixes
   - Accumulating locks
   - Zombie sessions

## Additional Resources

- [Redis Memory Optimization](https://redis.io/topics/memory-optimization)
- [Redis Eviction Policies](https://redis.io/topics/lru-cache)
- [EnhancedCacheService Documentation](../app/services/enhanced_cache_service.py)
