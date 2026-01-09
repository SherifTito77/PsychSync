# app/core/background_jobs.py
"""
Background Job Processing System
- Redis-based task queue
- Job scheduling and retry logic
- Job status tracking
- Worker management
- Failed job handling and alerts
"""

import asyncio
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import json
import logging
import time
from typing import Any
import uuid

from redis.asyncio import Redis

from app.core.config import settings
from app.core.enhanced_cache import get_cache_manager
from app.monitoring.apm import get_custom_metrics

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class JobPriority(Enum):
    """Job priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Job:
    """Background job definition"""

    id: str
    task_name: str
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout_seconds: int = 300  # 5 minutes default
    error: str | None = None
    result: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary"""
        data = asdict(self)
        data["status"] = self.status.value
        data["priority"] = self.priority.value
        # Convert datetime to ISO string
        for field_name, field_value in data.items():
            if isinstance(field_value, datetime):
                data[field_name] = field_value.isoformat()
            elif field_value is None:
                data[field_name] = None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """Create job from dictionary"""
        # Handle datetime conversion
        date_fields = ["created_at", "scheduled_at", "started_at", "completed_at"]
        for field_name in date_fields:
            if data.get(field_name):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except (ValueError, TypeError):
                    data[field_name] = None

        # Handle enum conversion
        data["status"] = JobStatus(data.get("status", JobStatus.PENDING.value))
        data["priority"] = JobPriority(data.get("priority", JobPriority.NORMAL.value))

        return cls(**data)


class TaskQueue:
    """Redis-based task queue manager"""

    def __init__(self, redis_client: Redis = None, queue_name: str = "default"):
        self.redis = redis_client or get_cache_manager().redis if get_cache_manager() else None
        self.queue_name = queue_name
        self.processing_queue = f"{queue_name}:processing"
        self.failed_queue = f"{queue_name}:failed"
        self.delayed_queue = f"{queue_name}:delayed"
        self.max_retries = 3
        self.visibility_timeout = 30  # seconds
        self.blocking_timeout = 10  # seconds

    async def enqueue(self, job: Job, delay_seconds: int = 0) -> str:
        """Enqueue a job"""
        try:
            job_data = job.to_dict()

            if delay_seconds > 0:
                # Add to delayed queue
                job.scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
                await self.redis.zadd(
                    self.delayed_queue, {json.dumps(job_data): job.created_at.timestamp()}
                )
                logger.info(
                    f"Enqueued delayed job {job.id} for {job.task_name} (delay: {delay_seconds}s)"
                )
            else:
                # Add to main queue
                job.scheduled_at = datetime.utcnow()
                await self.redis.lpush(self.queue_name, json.dumps(job_data))
                logger.info(f"Enqueued job {job.id} for {job.task_name}")

            return job.id

        except Exception as e:
            logger.error(f"Failed to enqueue job {job.id}: {e!s}")
            raise

    async def dequeue(self, timeout_seconds: int = 10) -> Job | None:
        """Dequeue a job"""
        try:
            # First, move any delayed jobs whose time has come
            await self._move_delayed_jobs()

            # Try to get a job from the main queue
            job_data = await self.redis.brpop(
                self.queue_name, self.processing_queue, timeout=timeout_seconds
            )

            if job_data:
                # Move job to processing queue with visibility timeout
                await self.redis.zadd(
                    self.processing_queue, {job_data: time.time()}, xx=self.visibility_timeout
                )

                job = Job.from_dict(json.loads(job_data))
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()

                logger.info(f"Dequeued job {job.id} for {job.task_name}")
                return job

            return None

        except Exception as e:
            logger.error(f"Failed to dequeue job: {e!s}")
            return None

    async def _move_delayed_jobs(self):
        """Move delayed jobs whose time has come to the main queue"""
        try:
            current_time = time.time()
            ready_jobs = await self.redis.zrangebyscore(
                self.delayed_queue, 0, current_time, withscores=True
            )

            if ready_jobs:
                # Remove from delayed queue
                await self.redis.zremrangebyscore(self.delayed_queue, 0, current_time)

                # Add to main queue in priority order
                for job_data, score in ready_jobs:
                    job = Job.from_dict(json.loads(job_data))
                    await self.redis.lpush(self.queue_name, job_data)

                logger.info(f"Moved {len(ready_jobs)} delayed jobs to main queue")

        except Exception as e:
            logger.error(f"Failed to move delayed jobs: {e!s}")

    async def complete_job(self, job: Job, result: Any = None):
        """Mark a job as completed"""
        try:
            # Remove from processing queue
            await self.redis.zrem(self.processing_queue, json.dumps(job.to_dict()))

            # Update job status
            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.utcnow()
            job.result = result
            job.error = None

            # Store completion info (optional - for audit trail)
            completion_key = f"job:{job.id}:completion"
            completion_data = {
                "job_id": job.id,
                "status": job.status.value,
                "completed_at": job.completed_at.isoformat(),
                "duration_ms": (job.completed_at - job.started_at).total_seconds() * 1000
                if job.started_at
                else 0,
                "result": str(result)[:1000] if result else None,
            }

            await self.redis.setex(
                completion_key, 3600, json.dumps(completion_data)
            )  # Keep for 1 hour

            logger.info(f"Completed job {job.id} for {job.task_name}")

            # Record metric
            await get_custom_metrics().increment_counter(
                "job_completed", tags={"task_name": job.task_name, "priority": job.priority.name}
            )

        except Exception as e:
            logger.error(f"Failed to complete job {job.id}: {e!s}")

    async def fail_job(self, job: Job, error: Exception):
        """Mark a job as failed and handle retries"""
        try:
            # Remove from processing queue
            await self.redis.zrem(self.processing_queue, json.dumps(job.to_dict()))

            # Update job status and error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error = str(error)
            job.retry_count += 1

            # Check if job should be retried
            if job.retry_count < job.max_retries:
                job.status = JobStatus.RETRY
                # Calculate exponential backoff delay
                delay_seconds = min(300, 60 * (2**job.retry_count))
                retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)

                # Add to delayed queue for retry
                job.scheduled_at = retry_at
                await self.redis.zadd(
                    self.delayed_queue,
                    {json.dumps(job.to_dict()): retry_at.timestamp()},
                    xx=self.visibility_timeout * job.retry_count,
                )

                logger.warning(
                    f"Retrying job {job.id} (attempt {job.retry_count}/{job.max_retries}) for {job.task_name} in {delay_seconds}s"
                )
            else:
                # Max retries exceeded, move to failed queue
                await self.redis.lpush(self.failed_queue, json.dumps(job.to_dict()))
                logger.error(
                    f"Job {job.id} failed permanently after {job.max_retries} attempts for {job.task_name}"
                )

            # Record error metric
            await get_custom_metrics().increment_counter(
                "job_failed",
                tags={
                    "task_name": job.task_name,
                    "error_type": type(error).__name__,
                    "retry_count": job.retry_count,
                },
            )

        except Exception as e:
            logger.error(f"Failed to handle job failure for {job.id}: {e!s}")

    async def get_job_status(self, job_id: str) -> Job | None:
        """Get current status of a job"""
        try:
            # Check completion info first
            completion_key = f"job:{job_id}:completion"
            completion_data = await self.redis.get(completion_key)
            if completion_data:
                data = json.loads(completion_data)
                job = Job.from_dict(json.loads(await self.redis.get(f"job:{job_id}") or "{}"))
                if job:
                    job.status = JobStatus[data["status"]]
                    job.completed_at = datetime.fromisoformat(data["completed_at"])
                    job.result = data.get("result")
                return job

            # Check processing queue
            processing_jobs = await self.redis.zrange(self.processing_queue, 0, -1, withscores=True)
            for job_data, score in processing_jobs:
                job = Job.from_dict(json.loads(job_data))
                if job.id == job_id:
                    job.status = JobStatus.RUNNING
                    return job

            # Check failed queue
            failed_jobs = await self.redis.lrange(self.failed_queue, 0, -1)
            for job_data in failed_jobs:
                job = Job.from_dict(json.loads(job_data))
                if job.id == job_id:
                    job.status = JobStatus.FAILED
                    return job

            # Check delayed queue
            delayed_jobs = await self.redis.zrange(self.delayed_queue, 0, -1, withscores=True)
            for job_data, score in delayed_jobs:
                job = Job.from_dict(json.loads(job_data))
                if job.id == job_id:
                    job.status = JobStatus.PENDING
                    return job

            return None

        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e!s}")
            return None

    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        try:
            stats = {
                "queue_name": self.queue_name,
                "pending_jobs": await self.redis.llen(self.queue_name),
                "processing_jobs": await self.redis.zcard(self.processing_queue),
                "delayed_jobs": await self.redis.zcard(self.delayed_queue),
                "failed_jobs": await self.redis.llen(self.failed_queue),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Get job counts by status
            all_jobs = []

            # Count jobs by task name
            task_counts = {}

            # Get recent completed jobs (from completion keys)
            pattern = "job:*:completion"
            completion_keys = await self.redis.keys(pattern)
            for key in completion_keys[:100]:  # Limit to recent jobs
                try:
                    completion_data = await self.redis.get(key)
                    if completion_data:
                        data = json.loads(completion_data)
                        task_name = data.get("task_name", "unknown")
                        task_counts[task_name] = task_counts.get(task_name, 0) + 1
                except:
                    pass

            stats["task_counts"] = task_counts
            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats: {e!s}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


class BackgroundWorker:
    """Background job worker"""

    def __init__(
        self,
        worker_id: str,
        task_queue: TaskQueue,
        max_concurrent_jobs: int = 1,
        poll_interval: float = 1.0,
        shutdown_timeout: float = 30.0,
    ):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.max_concurrent_jobs = max_concurrent_jobs
        self.poll_interval = poll_interval
        self.shutdown_timeout = shutdown_timeout
        self.running = False
        self.current_jobs: dict[str, Job] = {}
        self.registered_tasks: dict[str, Callable] = {}
        self.job_semaphore = asyncio.Semaphore(max_concurrent_jobs)

    def register_task(self, task_name: str, task_func: Callable):
        """Register a task function"""
        self.registered_tasks[task_name] = task_func
        logger.info(f"Worker {self.worker_id} registered task: {task_name}")

    async def start(self):
        """Start the worker"""
        self.running = True
        logger.info(f"Starting background worker {self.worker_id}")

        try:
            while self.running:
                async with self.job_semaphore:
                    if not self.running:
                        break

                    # Get next job
                    job = await self.task_queue.dequeue(timeout_seconds=self.poll_interval)

                    if job and job.task_name in self.registered_tasks:
                        await self._process_job(job)
                    elif job:
                        logger.warning(f"Unknown task: {job.task_name}")
                        await self.task_queue.fail_job(
                            job, ValueError(f"Task {job.task_name} not registered")
                        )

        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e!s}")
        finally:
            logger.info(f"Worker {self.worker_id} stopped")

    async def stop(self):
        """Stop the worker gracefully"""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False

        # Wait for current jobs to complete
        if self.current_jobs:
            logger.info(f"Waiting for {len(self.current_jobs)} jobs to complete...")
            await asyncio.sleep(self.shutdown_timeout)

        # Cancel remaining jobs
        for job_id, job in self.current_jobs.items():
            await self.task_queue.fail_job(job, asyncio.CancelledError("Worker shutdown"))

        logger.info(f"Worker {self.worker_id} stopped")

    async def _process_job(self, job: Job):
        """Process a single job"""
        self.current_jobs[job.id] = job
        start_time = time.time()

        try:
            logger.info(f"Worker {self.worker_id} processing job {job.id}: {job.task_name}")

            # Execute the task
            task_func = self.registered_tasks[job.task_name]

            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*job.args, **job.kwargs)
            else:
                result = task_func(*job.args, **job.kwargs)

            # Complete the job
            await self.task_queue.complete_job(job, result)

            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Worker {self.worker_id} completed job {job.id} in {execution_time:.2f}ms")

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"Worker {self.worker_id} failed job {job.id} in {execution_time:.2f}ms: {e!s}"
            )

            # Record the failure
            await self.task_queue.fail_job(job, e)

        finally:
            # Remove from current jobs
            self.current_jobs.pop(job.id, None)


# Global task queue and workers
_task_queue: TaskQueue | None = None
_workers: list[BackgroundWorker] = []


def get_task_queue() -> TaskQueue:
    """Get global task queue instance"""
    global _task_queue
    if _task_queue is None:
        redis_client = get_cache_manager().redis if get_cache_manager() else None
        if redis_client:
            _task_queue = TaskQueue(redis_client)
    return _task_queue


def get_workers() -> list[BackgroundWorker]:
    """Get list of active workers"""
    return _workers


def create_worker(worker_id: str = None, max_concurrent_jobs: int = 1) -> BackgroundWorker:
    """Create a new background worker"""
    if worker_id is None:
        worker_id = f"worker_{uuid.uuid4().hex[:8]}"

    worker = BackgroundWorker(
        worker_id=worker_id, task_queue=get_task_queue(), max_concurrent_jobs=max_concurrent_jobs
    )
    _workers.append(worker)
    return worker


def task(task_name: str, **kwargs):
    """Decorator to register a task function"""

    def decorator(func):
        # Register the task with all workers
        for worker in get_workers():
            worker.register_task(task_name, func)

        @wraps(func)
        async def wrapper(*args, **func_kwargs):
            # This wrapper allows the function to be called directly
            return await func(*args, **func_kwargs)

        wrapper.task_name = task_name
        wrapper.original_func = func
        return wrapper

    return decorator


async def enqueue_job(
    task_name: str,
    args: list[Any] = None,
    kwargs: dict[str, Any] = None,
    priority: JobPriority = JobPriority.NORMAL,
    max_retries: int = 3,
    delay_seconds: int = 0,
    timeout_seconds: int = 300,
    metadata: dict[str, Any] = None,
) -> str:
    """Enqueue a background job"""
    job_id = str(uuid.uuid4())

    job = Job(
        id=job_id,
        task_name=task_name,
        args=args or [],
        kwargs=kwargs or {},
        priority=priority,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        metadata=metadata or {},
    )

    queue = get_task_queue()
    if queue:
        return await queue.enqueue(job, delay_seconds)
    raise RuntimeError("Task queue not available")


# Example task functions
@task("send_email")
async def send_email_task(to_email: str, subject: str, body: str, template_id: str = None):
    """Example: Send email task"""
    # Implement email sending logic here
    logger.info(f"Sending email to {to_email}: {subject}")
    await asyncio.sleep(1)  # Simulate email sending
    return {"status": "sent", "to": to_email, "subject": subject}


@task("generate_report")
async def generate_report_task(user_id: str, report_type: str, filters: dict[str, Any] = None):
    """Example: Generate report task"""
    # Implement report generation logic here
    logger.info(f"Generating {report_type} report for user {user_id}")
    await asyncio.sleep(2)  # Simulate report generation
    return {"report_id": str(uuid.uuid4()), "type": report_type, "user_id": user_id}


@task("cleanup_temp_files")
async def cleanup_temp_files():
    """Example: Cleanup temporary files"""
    # Implement cleanup logic here
    logger.info("Cleaning up temporary files")
    # Add actual cleanup logic
    return {"cleaned_files": 0}


# Global worker instance for convenience
_background_worker = None


async def get_background_worker() -> BackgroundWorker:
    """Get or create the global background worker instance"""
    global _background_worker
    if _background_worker is None:
        # Create default task queue and worker
        task_queue = TaskQueue("default", redis=Redis.from_url(settings.REDIS_URL))
        _background_worker = BackgroundWorker("default_worker", task_queue)
        await _background_worker.start()
    return _background_worker
