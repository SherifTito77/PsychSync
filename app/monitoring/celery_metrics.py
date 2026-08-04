"""
Celery Monitoring Integration

Provides comprehensive Celery metrics for Prometheus:
- Task execution counts (success, failure, retry)
- Task duration histograms
- Queue length gauges
- Worker health metrics
- Dead Letter Queue metrics

Exposes metrics at /metrics endpoint for Prometheus scraping.

Author: Infrastructure Team
Version: 2.0.0
Date: January 7, 2026
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from celery import Celery
from celery.signals import (
    Heartbeat,
    task_failure,
    task_postrun,
    task_prerun,
    task_received,
    task_retry,
    task_success,
    worker,
    worker_ready,
    worker_shutdown,
)
from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.requests import Request

from app.core.config.celery_config import celery_app

logger = logging.getLogger(__name__)


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Task execution metrics
task_executions_total = Counter(
    "celery_task_executions_total",
    "Total number of task executions",
    ["task_name", "status", "worker"],
    registry=CollectorRegistry(),
)

task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Task execution duration in seconds",
    ["task_name", "worker"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0),
    registry=CollectorRegistry(),
)

task_latency_seconds = Histogram(
    "celery_task_latency_seconds",
    "Time from task receipt to start in seconds",
    ["task_name", "worker"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0),
    registry=CollectorRegistry(),
)

# Queue metrics
queue_length = Gauge(
    "celery_queue_length",
    "Current number of tasks in queue",
    ["queue_name"],
    registry=CollectorRegistry(),
)

queue_dlq_length = Gauge(
    "celery_queue_dlq_length",
    "Current number of tasks in dead letter queue",
    registry=CollectorRegistry(),
)

# Worker metrics
worker_tasks_active = Gauge(
    "celery_worker_tasks_active",
    "Number of active tasks per worker",
    ["worker"],
    registry=CollectorRegistry(),
)

worker_status = Gauge(
    "celery_worker_status",
    "Worker status (1=online, 0=offline)",
    ["worker"],
    registry=CollectorRegistry(),
)

# Retry metrics
task_retries_total = Counter(
    "celery_task_retries_total",
    "Total number of task retries",
    ["task_name", "worker"],
    registry=CollectorRegistry(),
)

# DLQ metrics
task_dlq_total = Counter(
    "celery_task_dlq_total",
    "Total number of tasks sent to Dead Letter Queue",
    ["task_name", "reason", "worker"],
    registry=CollectorRegistry(),
)


# ============================================================================
# CELERY SIGNAL HANDLERS
# ============================================================================


@task_received.connect
def task_received_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **extras
):
    """Track task receipt (latency measurement start)"""
    task_name = task.name if task else "unknown"
    worker = sender.hostname if sender else "unknown"

    # Store receive time for latency calculation
    task._track_start = time.time()

    logger.debug(f"Task received: {task_name} (ID: {task_id})")


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **extras
):
    """Track task start (calculate latency)"""
    task_name = task.name if task else "unknown"
    worker = sender.hostname if sender else "unknown"

    # Calculate latency (time from receipt to start)
    if hasattr(task, "_track_start"):
        latency = time.time() - task._track_start
        task_latency_seconds.labels(task_name=task_name, worker=worker).observe(latency)

    # Track start time for duration calculation
    task._start_time = time.time()

    logger.debug(f"Task started: {task_name}")


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **extras,
):
    """Track task completion"""
    task_name = task.name if task else "unknown"
    worker = sender.hostname if sender else "worker"

    # Calculate duration
    if hasattr(task, "_start_time"):
        duration = time.time() - task._start_time
        task_duration_seconds.labels(task_name=task_name, worker=worker).observe(
            duration
        )

    # Track execution count
    status = "success" if state == "SUCCESS" else "failure"
    task_executions_total.labels(
        task_name=task_name, status=status, worker=worker
    ).inc()

    logger.debug(f"Task completed: {task_name} (status: {status})")


@task_success.connect
def task_success_handler(sender=None, task_id=None, result=None, **extras):
    """Track successful tasks"""
    task_name = sender.name if sender else "unknown"
    logger.debug(f"Task success: {task_name}")


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **extras,
):
    """Track failed tasks"""
    task_name = sender.name if sender else "unknown"
    worker = sender.hostname if sender else "unknown"

    # Check if this is a final failure (max retries exceeded)
    # If so, increment DLQ counter
    request = sender.request if sender else None
    if request and hasattr(request, "retries"):
        max_retries = getattr(sender, "max_retries", 3)
        if request.retries >= max_retries:
            task_dlq_total.labels(
                task_name=task_name, reason="max_retries_exceeded", worker=worker
            ).inc()

    logger.debug(f"Task failure: {task_name}")


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **extras):
    """Track task retries"""
    task_name = sender.name if sender else "unknown"
    worker = sender.hostname if sender else "worker"

    task_retries_total.labels(task_name=task_name, worker=worker).inc()

    logger.debug(f"Task retry: {task_name}")


@worker_ready.connect
def worker_ready_handler(sender=None, **extras):
    """Track worker coming online"""
    worker = sender.hostname if sender else "unknown"
    worker_status.labels(worker=worker).set(1)
    logger.info(f"Worker online: {worker}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **extras):
    """Track worker going offline"""
    worker = sender.hostname if sender else "unknown"
    worker_status.labels(worker=worker).set(0)
    logger.info(f"Worker offline: {worker}")


# ============================================================================
# QUEUE MONITORING
# ============================================================================


async def update_queue_metrics():
    """
    Update queue length metrics.

    Should be called periodically (e.g., every 30 seconds) from a scheduled task.
    """
    try:
        import redis.asyncio as aioredis

        from app.core.config import settings

        client = await aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )

        # Get queue lengths
        queue_names = [
            "default",
            "scoring",
            "reports",
            "notifications",
            "maintenance",
            "dlq",
        ]

        for queue in queue_names:
            key = f"celery:{queue}"
            length = await client.llen(key)
            if queue == "dlq":
                queue_dlq_length.set(length)
            else:
                queue_length.labels(queue_name=queue).set(length)

        await client.close()

        logger.debug("Queue metrics updated")

    except Exception as e:
        logger.error(f"Error updating queue metrics: {e}")


async def update_worker_metrics():
    """
    Update worker activity metrics.

    Should be called periodically (e.g., every 30 seconds) from a scheduled task.
    """
    try:
        inspect = celery_app.control.inspect()

        # Get active tasks
        active = inspect.active()
        if active:
            # Reset all gauges
            worker_tasks_active.clear()

            # Set current values
            for worker, tasks in active.items():
                worker_tasks_active.labels(worker=worker).set(len(tasks))

        logger.debug("Worker metrics updated")

    except Exception as e:
        logger.error(f"Error updating worker metrics: {e}")


# ============================================================================
# FASTAPI METRICS ENDPOINT
# ============================================================================


async def metrics_endpoint(request: Request) -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response with Prometheus metrics text format
    """
    # Update dynamic metrics
    await update_queue_metrics()
    await update_worker_metrics()

    # Generate metrics
    metrics = generate_latest()

    return Response(
        content=metrics,
        media_type=CONTENT_TYPE_LATEST,
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )


# ============================================================================
# BACKGROUND METRICS COLLECTION
# ============================================================================


@celery_app.task
def collect_celery_metrics():
    """
    Background task to collect Celery metrics periodically.

    This task should be scheduled in Celery Beat to run every 30 seconds:
    "collect-celery-metrics": {
        "task": "app.monitoring.celery_metrics.collect_celery_metrics",
        "schedule": crontab(second="*/30"),
        "options": {"queue": "maintenance"}
    }
    """
    import asyncio

    # Run async update functions
    asyncio.run(update_queue_metrics())
    asyncio.run(update_worker_metrics())

    logger.debug("Celery metrics collected")


# ============================================================================
# CONTEXT MANAGER FOR CUSTOM TASK TRACKING
# ============================================================================


@contextmanager
def track_task_execution(task_name: str, worker: str = "unknown"):
    """
    Context manager for manual task tracking.

    Usage:
        with track_task_execution("my_task", "worker1"):
            # Do work
            result = do_work()

    Args:
        task_name: Name of the task
        worker: Worker name
    """
    start_time = time.time()
    try:
        yield
        # Task succeeded
        task_executions_total.labels(
            task_name=task_name, status="success", worker=worker
        ).inc()
    except Exception as e:
        # Task failed
        task_executions_total.labels(
            task_name=task_name, status="failure", worker=worker
        ).inc()
        raise
    finally:
        # Record duration
        duration = time.time() - start_time
        task_duration_seconds.labels(task_name=task_name, worker=worker).observe(
            duration
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_task_metrics_summary() -> dict:
    """
    Get summary of all task metrics.

    Returns:
        Dictionary with metrics summary
    """
    return {
        "task_executions": {
            "total": task_executions_total._value.sum,
            "by_task": {
                (labels[0], labels[1]): metric._value.get()
                for metric, labels in task_executions_total._metrics.items()
            },
        },
        "avg_task_duration": (
            task_duration_seconds._sum.get() / task_duration_seconds._count.get()
            if task_duration_seconds._count.get() > 0
            else 0
        ),
        "queue_lengths": {
            queue: metric._value.get()
            for queue, metric in queue_length._metrics.items()
        },
        "dlq_length": queue_dlq_length._value.get(),
        "active_tasks": sum(
            metric._value.get() for metric in worker_tasks_active._metrics.values()
        ),
        "online_workers": sum(
            1 for metric in worker_status._metrics.values() if metric._value.get() > 0
        ),
        "total_retries": task_retries_total._value.sum,
        "total_dlq": task_dlq_total._value.sum,
    }


def reset_all_metrics():
    """
    Reset all metrics (use with caution).

    This is primarily useful for testing.
    """
    task_executions_total.clear()
    task_duration_seconds.clear()
    task_latency_seconds.clear()
    queue_length.clear()
    queue_dlq_length.clear()
    worker_tasks_active.clear()
    worker_status.clear()
    task_retries_total.clear()
    task_dlq_total.clear()

    logger.warning("All Celery metrics reset")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "metrics_endpoint",
    "collect_celery_metrics",
    "track_task_execution",
    "get_task_metrics_summary",
    "reset_all_metrics",
    # Metrics (for direct access if needed)
    "task_executions_total",
    "task_duration_seconds",
    "task_latency_seconds",
    "queue_length",
    "queue_dlq_length",
    "worker_tasks_active",
    "worker_status",
    "task_retries_total",
    "task_dlq_total",
]
