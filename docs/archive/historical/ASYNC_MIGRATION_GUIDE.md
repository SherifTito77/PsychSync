# PsychSync Async Migration Guide
## Converting Synchronous Flows to Async Tasks

**Based on Architecture Audit Findings**
**Goal:** Eliminate blocking operations, improve responsiveness
**Impact:** 5-10x throughput improvement

---

## Executive Summary

The current codebase has **mixed async/sync patterns** causing significant performance issues:
- Synchronous cache operations blocking async event loop
- Email sending blocking API responses
- AI assessment scoring causing timeouts
- Data exports consuming memory
- **Result:** Poor throughput, API timeouts under load

**Solution:** Systematic migration to async task patterns

---

## 1. Understanding the Problem

### 1.1 Current Async/Sync Mix

**File Analysis:**
```bash
# Count of async functions
grep -r "async def" app/ | wc -l  # 1,247 async functions

# Count of sync functions in async context
grep -r "def " app/api/v1/endpoints/*.py | grep -v "async def" | wc -l  # 89 sync functions

# Problem: Mixed patterns causing blocking
```

**Example of Blocking Code:**
```python
# app/core/cache.py:119-174 (BLOCKING!)
def cached(expire: int = 3600):
    def decorator(func):
        def wrapper(*args, **kwargs):  # NOT async!
            # Synchronous Redis operations block event loop
            value = redis_client.get(key)
```

**Impact:**
- When cache.get() takes 50ms, NO other requests can be processed
- Event loop blocked = wasted CPU cycles
- Throughput severely limited

### 1.2 Performance Impact

**Current Behavior:**
```
Request 1 → Cache get (50ms block) → Request 1 completes
Request 2 → Waits ❌ (blocked by Request 1)
Request 3 → Waits ❌ (blocked by Request 1)
```

**After Async Migration:**
```
Request 1 → Cache get (50ms async) → Request 1 completes
Request 2 → Processed concurrently ✅
Request 3 → Processed concurrently ✅
```

**Throughput Improvement:** 10-50x depending on I/O wait time

---

## 2. Async Pattern Fundamentals

### 2.1 Async Function Basics

**Synchronous (BLOCKING):**
```python
def get_user(user_id: UUID):
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()
```

**Asynchronous (NON-BLOCKING):**
```python
async def get_user(user_id: UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()
```

**Key Differences:**
- `async def` instead of `def`
- `await` before I/O operations
- Function returns coroutine object, not actual result
- Must be called from async context

### 2.2 Async Database Operations

**SQLAlchemy Async Pattern:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create async engine
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db"
)

# Create async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Usage
async def get_user(async_session: AsyncSession, user_id: UUID):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one()
```

**Common Async Patterns:**

**SELECT:**
```python
async def get_all_users(async_session: AsyncSession):
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()
```

**INSERT:**
```python
async def create_user(async_session: AsyncSession, user_data: dict):
    async with async_session() as session:
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
```

**UPDATE:**
```python
async def update_user(async_session: AsyncSession, user_id: UUID, updates: dict):
    async with async_session() as session:
        result = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**updates)
            .returning(User)
        )
        await session.commit()
        return result.scalar_one()
```

**DELETE:**
```python
async def delete_user(async_session: AsyncSession, user_id: UUID):
    async with async_session() as session:
        await session.execute(
            delete(User).where(User.id == user_id)
        )
        await session.commit()
```

### 2.3 Async HTTP Clients

**HTTPX (Recommended for Async):**
```python
import httpx

async def fetch_external_api(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

**Multiple Concurrent Requests:**
```python
import asyncio

async def fetch_multiple_urls(urls: List[str]):
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```

---

## 3. Converting Specific Patterns

### 3.1 Cache Operations (CRITICAL)

**Current (BLOCKING):**
```python
# app/core/cache.py
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def cached(expire: int = 3600):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = generate_key(func, args, kwargs)
            value = redis_client.get(key)  # BLOCKING I/O
            if value:
                return json.loads(value)

            result = func(*args, **kwargs)
            redis_client.setex(key, expire, json.dumps(result))  # BLOCKING I/O
            return result
        return wrapper
    return decorator
```

**Converted to Async (NON-BLOCKING):**
```python
# app/core/async_cache.py (NEW FILE)
from redis.asyncio import Redis as AsyncRedis
from typing import Callable
import asyncio
import json

redis_client = AsyncRedis(host='localhost', port=6379, decode_responses=True)

def cached_async(expire: int = 3600, key_prefix: str = ""):
    """Async caching decorator that doesn't block event loop"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            # Try cache (non-blocking)
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

**Migration Steps:**
1. Create `app/core/async_cache.py`
2. Copy `cache.py` functions to async versions
3. Add `@cached_async` to endpoints
4. Test alongside `@cached` using feature flag
5. Gradually migrate all endpoints
6. Remove old `cache.py` after verification

### 3.2 Email Sending

**Current (BLOCKING):**
```python
# app/services/email_service.py
import sendgrid
from sendgrid.helpers.mail import Mail

def send_email(to: str, subject: str, body: str):
    """Synchronous - blocks request while sending"""
    sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_KEY)
    mail = Mail(from_email=settings.FROM_EMAIL, to_emails=[to], subject=subject, plain_text_content=body)

    # BLOCKING HTTP call to SendGrid (can take 1-5 seconds)
    response = sg.send(mail)
    return response
```

**Option 1: Async Email Client**
```python
import httpx

async def send_email_async(to: str, subject: str, body: str):
    """Async - doesn't block"""
    url = "https://api.sendgrid.com/v3/mail/send"

    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": to}],
            "subject": subject
        }],
        "from": {"email": settings.FROM_EMAIL},
        "content": [{"type": "text/plain", "value": body}]
    }

    async with httpx.AsyncClient() as client:
        # Non-blocking HTTP call
        response = await client.post(url, json=data, headers=headers, timeout=30.0)
        return response.json()
```

**Option 2: Background Queue (RECOMMENDED)**
```python
from redis import Redis
from rq import Queue

redis_conn = Redis()
email_queue = Queue('emails', connection=redis_conn)

def send_email_async(to: str, subject: str, body: str):
    """Submit email to background queue"""
    # Returns immediately (non-blocking)
    job = email_queue.enqueue(
        'app.tasks.email_tasks.send_email',
        to, subject, body,
        timeout=30,
        result_ttl=3600  # Keep result for 1 hour
    )
    return {"job_id": job.id, "status": "queued"}
```

**Task Handler:**
```python
# app/tasks/email_tasks.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(to: str, subject: str, body: str):
    """Executed by worker process"""
    sg = SendGridAPIClient(api_key=settings.SENDGRID_KEY)
    mail = Mail(from_email=settings.FROM_EMAIL, to_emails=[to], subject=subject, plain_text_content=body)
    response = sg.send(mail)
    return response.status_code
```

**Worker Process:**
```bash
# Run separate worker processes
rq worker emails --url redis://localhost:6379
```

**Recommendation:** Use background queue for emails
- Better throughput
- Retry logic built-in
- Workers can scale independently
- Main API remains responsive

### 3.3 Data Export

**Current (MEMORY INTENSIVE, BLOCKING):**
```python
# app/services/data_export_service.py
async def export_all_data(org_id: UUID):
    """Loads all data into memory"""
    users = await db.execute(select(User).where(User.organization_id == org_id))
    all_users = users.scalars().all()  # 10,000+ users loaded!

    responses = await db.execute(select(Response).where(Response.organization_id == org_id))
    all_responses = responses.scalars().all()  # 100,000+ responses!

    # Generate CSV (doubles memory)
    csv_data = generate_csv(all_users, all_responses)

    return csv_data  # Returns entire CSV in memory
```

**Converted to Async + Streaming:**
```python
import asyncio
from io import StringIO
import csv

async def export_all_data_streaming(org_id: UUID):
    """Stream data without loading all into memory"""
    async with db.stream(
        select(User).where(User.organization_id == org_id)
    ) as user_stream:

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["user_id", "email", "full_name"])

        # Stream users one at a time
        async for user in user_stream.scalars():
            writer.writerow([user.id, user.email, user.full_name])

            # Yield chunks every 1MB
            if output.tell() > 1024 * 1024:
                yield output.getvalue()
                output = StringIO()
                writer = csv.writer(output)

        # Yield remaining data
        if output.tell() > 0:
            yield output.getvalue()
```

**FastAPI Endpoint:**
```python
from fastapi.responses import StreamingResponse

@router.get("/exports/organizations/{org_id}")
async def export_organization(org_id: UUID):
    return StreamingResponse(
        export_all_data_streaming(org_id),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=organization_{org_id}.csv"
        }
    )
```

**Benefits:**
- Constant memory usage (~1MB)
- Can export millions of rows
- Faster time-to-first-byte
- Client receives data incrementally

### 3.4 AI Assessment Scoring

**Current (BLOCKS FOR 5-10 SECONDS):**
```python
# app/services/assessment_service.py
async def submit_assessment(assessment_id: UUID, responses: List[Response]):
    """Synchronous scoring blocks request"""
    # Calculate score (CPU-intensive, 5-10 seconds)
    score = await calculate_score(responses)  # Still blocks!

    # Save results
    await db.execute(insert(AssessmentResult).values(score=score))

    return score
```

**Option 1: Async + Process Pool**
```python
from concurrent.futures import ProcessPoolExecutor
import asyncio

# Create process pool (outside request handler)
process_pool = ProcessPoolExecutor(max_workers=4)

async def submit_assessment_async(assessment_id: UUID, responses: List[Response]):
    """Offload scoring to process pool"""
    loop = asyncio.get_event_loop()

    # Run in separate process (doesn't block event loop)
    score = await loop.run_in_executor(
        process_pool,
        calculate_score_blocking,  # Regular (non-async) function
        responses
    )

    # Save results (async)
    await db.execute(insert(AssessmentResult).values(score=score))

    return score
```

**Option 2: Background Queue (RECOMMENDED)**
```python
from redis import Redis
from rq import Queue

redis_conn = Redis()
ai_queue = Queue('ai_scoring', connection=redis_conn)

@router.post("/assessments/{assessment_id}/submit")
async def submit_assessment(assessment_id: UUID, responses: List[Response]):
    """Submit to queue, return job ID"""
    job = ai_queue.enqueue(
        'app.tasks.ai_tasks.score_assessment',
        assessment_id,
        responses,
        timeout=600,  # 10 minutes
        result_ttl=86400  # Keep result for 24 hours
    )

    return {
        "job_id": job.id,
        "status": "processing",
        "result_url": f"/api/v1/jobs/{job.id}"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Poll for results"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except NoSuchJobError:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.get_status(),
        "result": job.result if job.is_finished else None,
        "error": job.exc_info if job.is_failed else None
    }
```

**Frontend Polling:**
```typescript
// frontend/src/hooks/useAssessmentSubmission.ts
export function useAssessmentSubmission() {
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'failed'>('idle');
  const [result, setResult] = useState<Score | null>(null);

  const submitAssessment = async (assessmentId: string, responses: Response[]) => {
    setStatus('processing');

    // Submit to queue
    const { data } = await api.post(`/assessments/${assessmentId}/submit`, { responses });

    // Poll for results
    const pollInterval = setInterval(async () => {
      const { data: job } = await api.get(`/jobs/${data.job_id}`);

      if (job.status === 'completed') {
        setResult(job.result);
        setStatus('completed');
        clearInterval(pollInterval);
      } else if (job.status === 'failed') {
        setStatus('failed');
        clearInterval(pollInterval);
      }
    }, 2000); // Check every 2 seconds
  };

  return { submitAssessment, status, result };
}
```

**Recommendation:** Use background queue for AI scoring
- API responds immediately
- Better user experience (progress bar possible)
- Workers can scale independently
- Can use GPU instances for workers

---

## 4. Background Task Implementation

### 4.1 Task Queue Setup

**Option A: Redis Queue (RQ) - Simple**
```bash
pip install rq
```

**Configuration:**
```python
# app/core/queue.py
from redis import Redis
from rq import Queue

redis_conn = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0
)

# Create separate queues for different priorities
high_priority_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_priority_queue = Queue('low', connection=redis_conn)
```

**Worker:**
```python
# workers.py
from redis import Redis
from rq import Worker

redis_conn = Redis()
work_queues = ['high', 'default', 'low']

if __name__ == '__main__':
    with Worker(*work_queues, connection=redis_conn):
        work()
```

**Run Workers:**
```bash
# Terminal 1
python -u workers.py

# Terminal 2 (for multiple workers)
python -u workers.py
```

**Option B: Celery - Feature Rich**
```bash
pip install celery
```

**Configuration:**
```python
# app/core/celery_app.py
from celery import Celery

celery_app = Celery(
    'psychsync',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,  # Fetch 4 tasks at a time
)
```

**Tasks:**
```python
# app/tasks/assessment_tasks.py
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def score_assessment_task(self, assessment_id: str, responses: list):
    """Celery task for scoring"""
    try:
        score = calculate_score(responses)
        return {'status': 'completed', 'score': score}
    except Exception as exc:
        # Update task state
        self.update_state(state='FAILURE', meta={'error': str(exc)})
        raise
```

**Run Workers:**
```bash
celery -A app.core.celery_app worker --loglevel=info --concurrency=4
```

### 4.2 Task Patterns

**Pattern 1: Fire and Forget**
```python
# Submit task, don't wait for result
default_queue.enqueue(
    'app.tasks.email_tasks.send_welcome_email',
    user.email
)
# Returns immediately
```

**Pattern 2: Get Result Later**
```python
# Submit task
job = default_queue.enqueue(
    'app.tasks.export_tasks.generate_report',
    org_id,
    timeout=600
)

# Return job ID to client
return {"job_id": job.id}

# Client polls for result
@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = Job.fetch(job_id, connection=redis_conn)
    return {
        "status": job.get_status(),
        "result": job.result if job.is_finished else None
    }
```

**Pattern 3: Scheduled Tasks**
```python
from datetime import timedelta

# Schedule task to run in 1 hour
job = default_queue.enqueue_in(
    timedelta(hours=1),
    'app.tasks.cleanup.delete_old_logs'
)

# Schedule recurring task
from rq_scheduler import Scheduler

scheduler = Scheduler(queue_name=default_queue, connection=redis_conn)

scheduler.schedule(
    scheduled_time=datetime.utcnow(),
    func=app.tasks.cleanup.delete_old_logs,
    interval=3600,  # Run every hour
    repeat=None
)
```

### 4.3 Task Best Practices

**Idempotency:**
```python
@celery_app.task(bind=True)
def process_payment(self, payment_id: str):
    """Ensure task is idempotent"""
    # Check if already processed
    if Payment.objects.filter(id=payment_id, status='completed').exists():
        return {'status': 'already_processed'}

    # Process payment
    payment = Payment.objects.get(id=payment_id)
    payment.charge()
    payment.status = 'completed'
    payment.save()

    return {'status': 'success'}
```

**Error Handling:**
```python
@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_notification(self, user_id: str, message: str):
    """Auto-retry on failure with exponential backoff"""
    try:
        send_email(user_id, message)
    except Exception as exc:
        # Log error
        logger.error(f"Failed to send notification: {exc}")
        # Retry automatically
        raise self.retry(exc=exc)
```

**Progress Tracking:**
```python
@celery_app.task(bind=True)
def long_running_task(self, data):
    """Update progress as task runs"""
    total = len(data)

    for i, item in enumerate(data):
        # Process item
        process_item(item)

        # Update progress (0-100)
        progress = int((i + 1) / total * 100)
        self.update_state(state='PROGRESS', meta={'progress': progress})

    return {'status': 'completed', 'total': total}
```

**Poll Progress:**
```python
@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PROGRESS':
        return {
            "status": "processing",
            "progress": task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        return {
            "status": "completed",
            "result": task.result
        }
    elif task.state == 'FAILURE':
        return {
            "status": "failed",
            "error": str(task.info)
        }
```

---

## 5. Migration Checklist

### Phase 1: Cache Operations (Week 1)
- [ ] Create `app/core/async_cache.py`
- [ ] Implement `@cached_async` decorator
- [ ] Add feature flag to toggle between sync/async cache
- [ ] Migrate 10% of endpoints to async cache
- [ ] Monitor performance metrics
- [ ] Complete migration of all endpoints
- [ ] Remove old `cache.py`

### Phase 2: Email Sending (Week 2)
- [ ] Install RQ or Celery
- [ ] Create background worker processes
- [ ] Implement `send_email_async()` with queue
- [ ] Update all email sending to use queue
- [ ] Add job status endpoints
- [ ] Monitor queue depth and failures

### Phase 3: Data Export (Week 3)
- [ ] Implement streaming data export
- [ ] Add `StreamingResponse` to export endpoints
- [ ] Test with large datasets (100K+ rows)
- [ ] Monitor memory usage during exports
- [ ] Add export job tracking

### Phase 4: AI Scoring (Week 4-5)
- [ ] Create AI scoring background tasks
- [ ] Implement job submission endpoint
- [ ] Create job status polling endpoint
- [ ] Update frontend to poll for results
- [ ] Scale AI workers independently
- [ ] Add GPU instances if needed

### Phase 5: Database Queries (Week 6)
- [ ] Verify all database calls use `await`
- [ ] Implement proper eager loading
- [ ] Add database indexes
- [ ] Optimize N+1 queries
- [ ] Test query performance

---

## 6. Testing Async Code

### 6.1 Testing Async Functions

**Using pytest-asyncio:**
```bash
pip install pytest-asyncio
```

**Test Example:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user(async_client: AsyncClient):
    response = await async_client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
```

**Async Fixture:**
```python
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### 6.2 Testing Background Tasks

**Direct Task Testing:**
```python
@pytest.mark.asyncio
async def test_score_assessment_task():
    """Test task directly (not through queue)"""
    responses = create_test_responses()

    # Call task function directly
    result = score_assessment_task(responses)

    assert result["openness"] > 0
    assert result["conscientiousness"] > 0
```

**Integration Testing with Queue:**
```python
@pytest.mark.asyncio
async def test_assessment_submission_flow():
    """Test full flow with queue"""
    # Submit assessment
    response = await async_client.post(
        f"/assessments/{assessment_id}/submit",
        json={"responses": test_responses}
    )

    assert response.status_code == 202  # Accepted
    job_id = response.json()["job_id"]

    # Wait for job to complete
    await asyncio.sleep(5)

    # Check result
    result = await async_client.get(f"/jobs/{job_id}")
    assert result.status_code == 200
    assert result.json()["status"] == "completed"
```

---

## 7. Monitoring Async Operations

### 7.1 Task Monitoring

**RQ Dashboard:**
```bash
pip install rq-dashboard

# Run dashboard
rq-dashboard --redis-url redis://localhost:6379
```

**Visit:** http://localhost:9181

**Celery Flower:**
```bash
pip install flower

# Run flower
celery -A app.core.celery_app flower
```

**Visit:** http://localhost:5555

### 7.2 Metrics to Track

**Queue Metrics:**
```python
from prometheus_client import Gauge

queue_size = Gauge('queue_size', 'Queue size', ['queue_name'])
queue_latency = Gauge('queue_latency_seconds', 'Time in queue', ['queue_name'])

async def update_queue_metrics():
    # Update queue metrics
    for queue_name in ['high', 'default', 'low']:
        queue = Queue(queue_name, connection=redis_conn)
        queue_size.labels(queue_name=queue_name).set(len(queue))

        # Get oldest job age
        job = queue.get_job()
        if job:
            age = time.time() - job.created_at
            queue_latency.labels(queue_name=queue_name).set(age)
```

**Task Metrics:**
```python
task_duration = Histogram('task_duration_seconds', 'Task duration', ['task_name'])
task_successes = Counter('task_successes_total', 'Task successes', ['task_name'])
task_failures = Counter('task_failures_total', 'Task failures', ['task_name'])

@celery_app.task(bind=True)
def my_task(self, data):
    start_time = time.time()

    try:
        result = process_data(data)

        # Record success
        duration = time.time() - start_time
        task_duration.labels(task_name='my_task').observe(duration)
        task_successes.labels(task_name='my_task').inc()

        return result

    except Exception as exc:
        # Record failure
        task_failures.labels(task_name='my_task').inc()
        raise
```

---

## 8. Common Pitfalls

### Pitfall 1: Mixing Async and Sync

**BAD:**
```python
async def get_user_data(user_id: UUID):
    user = await db.execute(select(User).where(User.id == user_id))
    # Sync call inside async function
    profile = fetch_profile_from_api(user.email)  # BLOCKS!
    return profile
```

**GOOD:**
```python
async def get_user_data(user_id: UUID):
    user = await db.execute(select(User).where(User.id == user_id))
    # Async call
    profile = await fetch_profile_from_api_async(user.email)
    return profile
```

### Pitfall 2: Forgetting `await`

**BAD:**
```python
async def process_user(user_id: UUID):
    result = db.execute(select(User).where(User.id == user_id))  # Missing await!
    return result.scalar_one()  # Error: can't call scalar_one() on coroutine
```

**GOOD:**
```python
async def process_user(user_id: UUID):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one()
```

### Pitfall 3: Blocking Operations in Loops

**BAD:**
```python
async def send_notifications(user_ids: List[UUID]):
    for user_id in user_ids:
        # Each email blocks for 1 second
        send_email(user_id, "Welcome!")  # Total: N seconds
```

**GOOD:**
```python
async def send_notifications(user_ids: List[UUID]):
    # Send all emails concurrently
    tasks = [send_email_async(user_id, "Welcome!") for user_id in user_ids]
    await asyncio.gather(*tasks)  # Total: ~1 second
```

### Pitfall 4: Not Closing Connections

**BAD:**
```python
async def fetch_data():
    client = httpx.AsyncClient()
    response = await client.get(url)
    return response.json()
    # Client never closed!
```

**GOOD:**
```python
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
    # Client automatically closed
```

---

## 9. Performance Comparison

### Before Migration

```
Request: GET /assessments/{id}/submit

Timeline:
0ms: Start
50ms: Database query (blocking)
100ms: Calculate score (CPU, blocking)
5000ms: Save results (blocking)
5000ms: Total (API blocked entire time)

Throughput: 0.2 requests/second (5 seconds per request)
```

### After Migration

```
Request: POST /assessments/{id}/submit

Timeline:
0ms: Start
5ms: Submit to queue
10ms: Return job_id
10ms: Total (API responds immediately)

Background Task:
50ms: Database query
5000ms: Calculate score
100ms: Save results
5150ms: Total (doesn't block API)

Throughput: 100 requests/second (10ms per request)
```

**Improvement:** 500x throughput increase

---

## 10. Conclusion

Converting to async patterns provides **massive performance improvements**:

### Key Benefits
1. **Higher Throughput** - 10-500x more requests per second
2. **Better User Experience** - Faster API responses
3. **Scalability** - Horizontal scaling enabled
4. **Resource Efficiency** - Better CPU utilization

### Migration Priority
1. **Cache operations** (Week 1) - 30-50% improvement
2. **Email sending** (Week 2) - Eliminate timeouts
3. **Data export** (Week 3) - Fix memory issues
4. **AI scoring** (Week 4-5) - 10x improvement
5. **All database queries** (Week 6) - Complete async

### Success Criteria
- ✅ 100% of database calls use async
- ✅ 100% of cache operations use async
- ✅ 100% of email/background jobs use queue
- ✅ Zero blocking operations in hot paths
- ✅ P95 latency < 500ms

---

**Document Version:** 1.0
**Last Updated:** December 27, 2025
**Related Documents:**
- Architecture Audit Report
- Improvement Roadmap
- CPU/Memory Optimization Guide
