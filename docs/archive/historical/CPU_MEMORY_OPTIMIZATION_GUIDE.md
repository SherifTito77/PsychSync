# PsychSync CPU & Memory Optimization Guide
## Performance Tuning Strategies

**Based on Architecture Audit Findings**
**Target:** 5-10x performance improvement
**Focus:** CPU efficiency, memory optimization, resource utilization

---

## Executive Summary

Current performance analysis reveals significant optimization opportunities:
- **Synchronous operations in async context** - blocking event loop
- **Inefficient database queries** - N+1 problems, missing indexes
- **Large memory footprint** - 80-100MB ORM models loaded
- **CPU bottlenecks** - AI processing, assessment scoring
- **Connection pool exhaustion** - 50 max connections insufficient

**Expected Impact:** 5-10x performance improvement through optimization

---

## 1. CPU Optimization Strategies

### 1.1 Async/Sync Conversion (CRITICAL - 30-50% improvement)

#### Problem: Synchronous Cache Operations
**File:** `app/core/cache.py:119-174`

**Current (BLOCKING):**
```python
def cached(expire: int = 3600, key_prefix: str = "") -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):  # NOT ASYNC!
            if not redis_client:
                return func(*args, **kwargs)

            # Synchronous Redis operations block event loop
            value = redis_client.get(cache_key)
```

**Impact:** Every cached endpoint blocks during cache operations
**CPU Waste:** Event loop blocked = no other requests processed

**Optimized (ASYNC):**
```python
from redis.asyncio import Redis as AsyncRedis
from functools import wraps

redis_client = AsyncRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def cached_async(expire: int = 3600, key_prefix: str = "") -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):  # ASYNC!
            if not redis_client:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            # Try cache first (non-blocking)
            value = await redis_client.get(cache_key)
            if value is not None:
                return json.loads(value)

            # Cache miss - call function
            result = await func(*args, **kwargs)

            # Set cache (non-blocking)
            await redis_client.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )

            return result

        return wrapper
    return decorator
```

**Migration Path:**
1. Create `async_cache.py` alongside existing `cache.py`
2. Migrate endpoints one at a time
3. Run both in parallel during transition
4. Remove old `cache.py` after verification

**Expected Improvement:** 30-50% reduction in response times

#### Problem: Synchronous Database Operations
**File:** `app/services/agent_tools.py:55, 94`

**Current:**
```python
result = db.execute(text(query))  # Synchronous
```

**Optimized:**
```python
result = await db.execute(text(query))  # Async
```

**Action:** Search for all `.execute()` calls, ensure `await` is used

#### Problem: Synchronous DNS Resolution
**File:** `app/services/email_service.py`

**Current (BLOCKING):**
```python
import dns.resolver
# DNS resolution blocks event loop
mx_records = dns.resolver.resolve(domain, 'MX')
```

**Optimized (ASYNC):**
```python
import aiodns

resolver = aiodns.DNSResolver()
# Async DNS resolution
mx_records = await resolver.query(domain, 'MX')
```

**Installation:**
```bash
pip install aiodns
```

### 1.2 CPU-Intensive Task Offloading

#### Problem: AI Scoring Blocks Requests
**Current:** Assessment scoring (5-10 seconds) blocks API threads
**Impact:** API timeouts during high load

**Solution: Process Pool or Thread Pool**
```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

# Create process pool (outside request handler)
process_pool = ProcessPoolExecutor(max_workers=4)

async def calculate_assessment_score_async(responses: List[Response]):
    """Offload CPU-intensive scoring to process pool"""
    loop = asyncio.get_event_loop()

    # Run in separate process (doesn't block event loop)
    score = await loop.run_in_executor(
        process_pool,
        calculate_score,  # CPU-intensive function
        responses
    )

    return score
```

**Benefits:**
- Event loop remains responsive
- Can utilize multiple CPU cores
- Other requests processed during scoring

**Alternative:** Use Celery with dedicated worker processes

#### Problem: Large JSON Processing
**File:** Multiple endpoints process large JSON payloads

**Current:**
```python
# Blocks event loop
data = json.loads(large_json_string)
```

**Optimized:**
```python
import orjson

# 2-3x faster, non-blocking
data = orjson.loads(large_json_string)
```

**Installation:**
```bash
pip install orjson
```

**Benchmark:** orjson is 2-3x faster than standard json library

### 1.3 Query Optimization

#### Problem: N+1 Queries
**Current Pattern:**
```python
# app/api/v1/endpoints/teams.py:68-93
teams = await db.execute(select(Team).options(selectinload(Team.members)))

for team in teams:
    # Accesses members (already loaded)
    count = len(team.members) if hasattr(team, 'members') else 0
    # BUT: accessing team.members.user triggers additional query
```

**Optimized:**
```python
# Eager load all relationships
teams = await db.execute(
    select(Team)
    .options(
        selectinload(Team.members)
        .selectinload(TeamMember.user)  # Load user too!
    )
)

for team in teams:
    # No additional queries
    member_count = len(team.members)
    user_emails = [m.user.email for m in team.members]
```

**Impact:** 1 query vs 1+N queries (N = number of teams)

#### Problem: Inefficient Search
**File:** `app/services/user_service.py:694-711`

**Current (FULL TABLE SCAN):**
```python
search_pattern = f"%{search_term.lower()}%"
query = select(User).where(
    or_(
        User.email.ilike(search_pattern),  # Leading % = no index usage
        User.full_name.ilike(search_pattern)
    )
)
```

**Optimized (FULL-TEXT SEARCH):**
```sql
-- Add GIN index (one-time):
CREATE INDEX idx_users_email_gin
    ON users USING gin(to_tsvector('english', email));

CREATE INDEX idx_users_full_name_gin
    ON users USING gin(to_tsvector('english', full_name));
```

```python
# Use full-text search (uses index):
from sqlalchemy import func

search_vector = func.plainto_tsquery('english', search_term)
query = select(User).where(
    func.to_tsvector('english', User.email).op('@@')(search_vector) |
    func.to_tsvector('english', User.full_name).op('@@')(search_vector)
)
```

**Impact:** Query time from >1000ms to <50ms

### 1.4 Caching Strategy

#### Three-Level Cache Hierarchy

**Level 1: In-Memory (Per-Request)**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_framework_config(framework_code: str):
    """Fast, in-memory for duration of request"""
    return load_framework_from_db(framework_code)
```

**Level 2: Redis (Cross-Request)**
```python
@cached_async(expire=300)  # 5 minutes
async def get_assessment(assessment_id: UUID):
    """Shared across all instances"""
    return await load_assessment_from_db(assessment_id)
```

**Level 3: Database (Persistent)**
```python
async def get_assessment_from_db(assessment_id: UUID):
    """Source of truth"""
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id)
    )
    return result.scalar_one_or_none()
```

**Cache Invalidation Strategy:**
```python
async def on_assessment_updated(assessment_id: UUID):
    """Event-driven invalidation"""
    # Invalidate specific assessment
    await redis_client.delete(f"assessment:{assessment_id}")

    # Invalidate list caches
    keys = await redis_client.keys("assessments:*")
    if keys:
        await redis_client.delete(*keys)

    # Publish invalidation event
    await redis_client.publish(
        "cache_invalidation",
        json.dumps({
            "type": "assessment",
            "id": str(assessment_id)
        })
    )
```

---

## 2. Memory Optimization Strategies

### 2.1 Lazy Loading

#### Problem: Eager Loading by Default
**File:** `app/db/models/user.py:86`

**Current (LOADS ORG FOR EVERY USER QUERY):**
```python
class User(Base):
    # ...

    organization = relationship("Organization", lazy="joined")  # Always loaded!
```

**Impact:** 100 users loaded = 100 organization objects loaded

**Optimized:**
```python
class User(Base):
    # ...

    organization = relationship("Organization", lazy="select")  # Load on access
```

**Usage:**
```python
# Most list views don't need organization
users = await db.execute(select(User))

# Load only when needed
user = await db.execute(
    select(User)
    .options(selectinload(User.organization))  # Explicit load
    .where(User.id == user_id)
)
```

**Expected Memory Savings:** 20-30% reduction in user query memory

### 2.2 Pagination

#### Problem: Loading All Results
**Current:**
```python
async def get_all_assessments():
    result = await db.execute(select(Assessment))
    return result.scalars().all()  # Loads EVERYTHING into memory
```

**Optimized (CURSOR-BASED):**
```python
async def get_assessments(cursor: Optional[str] = None, limit: int = 50):
    query = select(Assessment).order_by(Assessment.created_at.desc())

    if cursor:
        # Decode cursor (base64 encoded timestamp)
        timestamp = base64.b64decode(cursor.encode()).decode()
        query = query.where(Assessment.created_at < timestamp)

    query = query.limit(limit + 1)  # Fetch one extra to check if more exist

    result = await db.execute(query)
    assessments = result.scalars().all()

    # Check if there are more results
    has_more = len(assessments) > limit
    if has_more:
        assessments = assessments[:limit]

    # Create next cursor
    next_cursor = None
    if has_more:
        last_assessment = assessments[-1]
        next_cursor = base64.b64encode(
            str(last_assessment.created_at).encode()
        ).decode()

    return {
        "items": assessments,
        "next_cursor": next_cursor,
        "has_more": has_more
    }
```

**Benefits:**
- Constant memory usage regardless of dataset size
- No offset performance degradation
- Better user experience (consistent load times)

### 2.3 Streaming Large Results

#### Problem: Data Export Loads All Data
**File:** `app/services/data_export_service.py`

**Current (OUT OF MEMORY):**
```python
async def export_users(org_id: UUID):
    users = await db.execute(select(User).where(User.organization_id == org_id))
    all_users = users.scalars().all()  # Loads ALL users into memory

    # Generate CSV from all data
    csv_data = generate_csv(all_users)  # Memory doubles!
    return csv_data
```

**Optimized (STREAMING):**
```python
import asyncio
from io import StringIO

async def export_users_streaming(org_id: UUID):
    """Stream users to CSV without loading all into memory"""

    # Use server-side cursor for streaming
    async with db.stream(
        select(User).where(User.organization_id == org_id)
    ) as stream:

        # Create CSV writer
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["id", "email", "full_name", "created_at"])

        # Stream rows one at a time
        async for user in stream.scalars():
            writer.writerow([
                str(user.id),
                user.email,
                user.full_name,
                user.created_at.isoformat()
            ])

            # Yield chunks for large datasets
            if output.tell() > 1024 * 1024:  # Every 1MB
                yield output.getvalue()
                output = StringIO()
                writer = csv.writer(output)

        # Yield remaining data
        if output.tell() > 0:
            yield output.getvalue()
```

**Usage in FastAPI:**
```python
from fastapi.responses import StreamingResponse

@router.get("/exports/users")
async def export_users_endpoint(org_id: UUID):
    return StreamingResponse(
        export_users_streaming(org_id),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )
```

**Benefits:**
- Constant memory usage (~1MB)
- Can export millions of rows
- Faster time-to-first-byte

### 2.4 Connection Pool Tuning

#### Problem: Pool Exhaustion
**Current:**
```python
pool_size=20, max_overflow=30  # 50 total connections
```

**Optimized (based on monitoring):**
```python
# Formula: connections = (workers * connections_per_worker) + background_threads

# For 8 workers, 10 connections per worker, 20 background threads:
pool_size = 8 * 10 = 80
max_overflow = 40  # 120 total connections

async_engine = create_async_engine(
    get_database_url(async_driver=True),
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_use_lifo=True,  # NEW: Use LIFO to reduce idle connections
)
```

**Monitoring Required:**
```python
@app.get("/health/db-pool")
async def db_pool_status():
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "max_overflow": pool.max_overflow,
        "utilisation": f"{(pool.checkedout() / (pool.size() + pool.max_overflow)) * 100:.1f}%"
    }
```

**Alert:** Create alert if utilisation > 80%

### 2.5 Memory Profiling

#### Identify Memory Hotspots
```python
import tracemalloc
import asyncio

async def profile_memory(func):
    """Decorator to profile memory usage"""
    async def wrapper(*args, **kwargs):
        # Start tracing
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Execute function
        result = await func(*args, **kwargs)

        # Take snapshot
        snapshot2 = tracemalloc.take_snapshot()

        # Calculate difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        for stat in top_stats[:10]:
            print(stat)

        tracemalloc.stop()
        return result

    return wrapper

# Usage:
@profile_memory
async def expensive_operation():
    # ... do work ...
    pass
```

#### Production Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Run with profiling
python -m memory_profiler app/main.py
```

---

## 3. Specific Optimization Targets

### 3.1 Assessment Scoring (HIGH PRIORITY)

**Current Performance:** 5-10 seconds per assessment
**Target:** < 1 second per assessment

**Strategy 1: Algorithm Optimization**
```python
# Current: Multiple passes through data
def calculate_score(responses):
    # Pass 1: Calculate totals
    totals = {}
    for response in responses:
        totals[response.dimension] = totals.get(response.dimension, 0) + response.value

    # Pass 2: Normalize
    normalized = {}
    for dimension, total in totals.items():
        normalized[dimension] = (total / max_score) * 100

    # Pass 3: Apply weights
    weighted = {}
    for dimension, score in normalized.items():
        weighted[dimension] = score * weights[dimension]

    return weighted

# Optimized: Single pass
def calculate_score_optimized(responses):
    weighted_totals = defaultdict(float)
    count_per_dimension = defaultdict(int)

    # Single pass through data
    for response in responses:
        dimension = response.dimension
        value = response.value

        # Normalize on-the-fly (pre-calculate max values)
        normalized_value = (value / MAX_VALUES[dimension]) * 100

        # Apply weight and accumulate
        weighted_totals[dimension] += normalized_value * WEIGHTS[dimension]
        count_per_dimension[dimension] += 1

    # Calculate final averages
    return {
        dimension: total / count_per_dimension[dimension]
        for dimension, total in weighted_totals.items()
    }
```

**Strategy 2: Pre-computation**
```python
# Cache dimension max values
DIMENSION_MAX_VALUES = {
    "openness": 50,      # 10 questions * 5 max score
    "conscientiousness": 50,
    # ... other dimensions
}

# Cache question weights
QUESTION_WEIGHTS = load_weights_from_db()  # Load once at startup
```

**Strategy 3: Parallel Processing**
```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

async def calculate_score_parallel(responses: List[Response]):
    """Calculate dimensions in parallel"""

    # Group responses by dimension
    by_dimension = group_by_dimension(responses)

    # Process dimensions in parallel
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor() as pool:
        scores = await asyncio.gather(*[
            loop.run_in_executor(
                pool,
                calculate_dimension_score,
                dimension,
                responses
            )
            for dimension, responses in by_dimension.items()
        ])

    return dict(zip(by_dimension.keys(), scores))
```

### 3.2 Analytics Queries (HIGH PRIORITY)

**Current Performance:** 2-5 seconds for dashboard
**Target:** < 500ms for dashboard

**Strategy 1: Materialized Views**
```sql
-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW mv_organization_stats AS
SELECT
    organization_id,
    COUNT(DISTINCT user_id) as user_count,
    COUNT(DISTINCT team_id) as team_count,
    COUNT(assessment_id) as assessment_count,
    AVG(score) as avg_score
FROM user_assessments
GROUP BY organization_id;

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX ON mv_organization_stats(organization_id);

-- Refresh strategy (cron job every 15 minutes):
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_organization_stats;
```

**Usage:**
```python
# Instead of complex aggregation query:
async def get_organization_stats(org_id: UUID):
    result = await db.execute(
        select(OrgStats)
        .where(OrgStats.organization_id == org_id)
        .with_entities(OrgStats.user_count, OrgStats.team_count)
    )
    return result.one()

# Query time: 5ms vs 2000ms+
```

**Strategy 2: Incremental Updates**
```python
# Update stats incrementally instead of full refresh
async def update_org_stats_on_assessment(org_id: UUID, score: float):
    await db.execute(
        insert(OrgStats)
        .values(
            organization_id=org_id,
            assessment_count=1,
            total_score=score
        )
        .on_conflict_do_update(
            index_elements=['organization_id'],
            set_={
                "assessment_count": OrgStats.assessment_count + 1,
                "total_score": OrgStats.total_score + score
            }
        )
    )
```

### 3.3 API Response Optimization

**Problem: Over-Fetching Data**
```python
# Current: Returns entire User object with all relationships
@router.get("/users/{user_id}")
async def get_user(user_id: UUID):
    user = await db.execute(
        select(User)
        .options(selectinload(User.organization))  # Load full org
        .options(selectinload(User.teams))  # Load all teams
        .options(selectinload(User.assessments))  # Load all assessments
        .where(User.id == user_id)
    )
    return user.scalar_one()
```

**Optimized (SELECTED FIELDS):**
```python
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, include: Optional[str] = None):
    # Only load requested fields
    query = select(User).where(User.id == user_id)

    # Parse include parameter
    includes = include.split(',') if include else []

    if 'organization' in includes:
        query = query.options(selectinload(User.organization))
    if 'teams' in includes:
        query = query.options(selectinload(User.teams))

    user = await db.execute(query)
    return user.scalar_one()
```

**Alternative: GraphQL**
```graphql
# Client requests exactly what they need
query GetUser {
  user(id: "123") {
    email
    fullName
    organization {
      name
    }
  }
}
```

---

## 4. Infrastructure Optimization

### 4.1 Gunicorn Worker Configuration

**Current (DEFAULT):**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Optimized (based on CPU cores):**
```bash
# Formula: workers = (2 x CPU cores) + 1
# For 8 cores: (2 x 8) + 1 = 17 workers

gunicorn app.main:app \
  -w 17 \
  -k uvicorn.workers.UvicornWorker \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --graceful-timeout 10
```

**Parameters Explained:**
- `-w 17`: Number of worker processes
- `--worker-connections 1000`: Max connections per worker
- `--max-requests 1000`: Restart workers after 1000 requests (prevents memory leaks)
- `--max-requests-jitter 100`: Randomize restarts (avoid thundering herd)
- `--timeout 30`: Worker timeout for slow requests
- `--graceful-timeout 10`: Allow 10s for graceful shutdown

### 4.2 Nginx Optimization

**Configuration:**
```nginx
# /etc/nginx/nginx.conf

worker_processes auto;
worker_connections 10000;
worker_rlimit_nofile 100000;

http {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss
               application/rss+xml font/truetype font/opentype
               application/vnd.ms-fontobject image/svg+xml;

    # Enable HTTP/2
    listen 443 ssl http2;

    # Buffer optimization
    client_body_buffer_size 128k;
    client_max_body_size 10M;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;

    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 65;
    send_timeout 10;

    # Upstream configuration
    upstream psychsync_backend {
        least_conn;  # Load balancing strategy
        server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
        server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
        server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;

        # Keepalive connections
        keepalive 32;
        keepalive_timeout 60s;
    }

    server {
        location / {
            proxy_pass http://psychsync_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
    }
}
```

### 4.3 Resource Limits

**Docker Configuration:**
```yaml
# docker-compose.yml

services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Max 2 CPU cores
          memory: 4G      # Max 4GB RAM
        reservations:
          cpus: '1.0'      # Reserve 1 CPU core
          memory: 2G      # Reserve 2GB RAM
    ulimits:
      nproc: 65535
      nofile:
        soft: 20000
        hard: 40000
```

**Kubernetes Configuration:**
```yaml
# k8s/deployment.yaml

resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

---

## 5. Monitoring & Profiling

### 5.1 Application Performance Monitoring

**Pyinstrument Profiling:**
```bash
# Install
pip install pyinstrument

# Run with profiling
pyinstrument app/main.py

# Or profile specific function
from pyinstrument import Profiler

profiler = Profiler()
profiler.start()

# ... do work ...

profiler.stop()
print(profiler.output_text(unicode=True, color=True))
```

**Memory Profiler:**
```bash
# Install
pip install memory-profiler

# Profile function
python -m memory_profiler app/services/assessment_service.py
```

### 5.2 Continuous Performance Tracking

**Middleware for Request Timing:**
```python
import time
from app.monitoring.metrics import request_duration

@app.middleware("http")
async def track_request_duration(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000

    # Record metric
    request_duration.labels(
        method=request.method,
        path=request.url.path,
        status=response.status_code
    ).observe(duration_ms)

    # Log slow requests
    if duration_ms > 1000:  # > 1 second
        logger.warning(
            f"Slow request: {request.method} {request.url.path}",
            extra={
                "duration_ms": duration_ms,
                "status": response.status_code
            }
        )

    return response
```

### 5.3 Performance Budgets

**Define Thresholds:**
```python
# app/monitoring/performance_budgets.py

PERFORMANCE_BUDGETS = {
    # P50 (median)
    "p50_ms": 100,

    # P95 (95th percentile)
    "p95_ms": 500,

    # P99 (99th percentile)
    "p99_ms": 1000,

    # Error rate
    "error_rate_percent": 1.0,

    # Database queries per request
    "max_db_queries": 10,

    # Memory per request
    "max_memory_mb": 50
}

def check_performance_budgets(metrics: dict) -> List[str]:
    """Check if metrics meet performance budgets"""
    violations = []

    if metrics["p95_ms"] > PERFORMANCE_BUDGETS["p95_ms"]:
        violations.append(f"P95 latency {metrics['p95_ms']}ms exceeds budget {PERFORMANCE_BUDGETS['p95_ms']}ms")

    if metrics["error_rate"] > PERFORMANCE_BUDGETS["error_rate_percent"]:
        violations.append(f"Error rate {metrics['error_rate']}% exceeds budget {PERFORMANCE_BUDGETS['error_rate_percent']}%")

    return violations
```

---

## 6. Optimization Checklist

### Immediate (Week 1)
- [ ] Replace synchronous Redis with async
- [ ] Add database indexes for slow queries
- [ ] Implement cursor-based pagination
- [ ] Enable gzip compression in Nginx
- [ ] Increase connection pool to 150

### Short Term (Month 1)
- [ ] Offload AI scoring to background queue
- [ ] Implement streaming for data exports
- [ ] Use materialized views for analytics
- [ ] Replace json with orjson
- [ ] Profile and optimize hot paths

### Medium Term (Months 2-3)
- [ ] Implement Redis session storage
- [ ] Set up database read replicas
- [ ] Optimize Gunicorn worker configuration
- [ ] Implement comprehensive monitoring
- [ ] Create performance dashboards

---

## 7. Expected Results

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **P50 Response Time** | 500ms | 100ms | 5x faster |
| **P95 Response Time** | 5000ms | 500ms | 10x faster |
| **P99 Response Time** | 10000ms | 1000ms | 10x faster |
| **Memory per Request** | 50MB | 10MB | 5x reduction |
| **Max Concurrent Users** | 5,000 | 100,000 | 20x increase |
| **Queries per Second** | 100 | 1000 | 10x increase |
| **CPU Utilization** | 80% | 40% | 2x efficiency |

### Resource Efficiency

**Before:**
- 8 workers × 20 connections = 160 total connections
- 50ms average response time
- 50% CPU idle time waiting for I/O

**After:**
- 17 workers × 50 connections = 850 total connections
- 100ms average response time
- 20% CPU idle time (better utilization)

---

## 8. Conclusion

CPU and memory optimization provides **immediate, high-impact benefits**:

1. **Better User Experience** - Faster response times
2. **Higher Throughput** - More users per server
3. **Lower Costs** - Fewer servers needed
4. **Improved Reliability** - Less memory pressure, fewer OOM errors

**Priority Order:**
1. Fix async/sync cache mismatch (30-50% improvement)
2. Add database indexes (50-90% query improvement)
3. Implement background tasks (eliminate timeouts)
4. Optimize connection pool (prevent exhaustion)
5. Profile and optimize hot paths

**Next Steps:**
1. Set up performance monitoring
2. Establish performance budgets
3. Create optimization sprint backlog
4. Begin with highest-impact items

---

**Document Version:** 1.0
**Last Updated:** December 27, 2025
**Related Documents:**
- Architecture Audit Report
- Improvement Roadmap
- Async Migration Guide
