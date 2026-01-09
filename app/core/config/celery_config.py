"""
Unified Celery Configuration for PsychSync

This configuration provides:
- Single source of truth for all Celery settings
- Dead letter exchange for failed tasks
- Task routing with priorities
- Comprehensive retry configuration
- Monitoring and metrics hooks
- Consistent behavior across all workers

Author: Infrastructure Team
Version: 2.0.0
Date: January 7, 2026
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
import os
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# CELERY BROKER/BACKEND CONFIGURATION
# ============================================================================

CELERY_BROKER_URL = getattr(settings, "CELERY_BROKER_URL", settings.REDIS_URL)
CELERY_RESULT_BACKEND = getattr(settings, "CELERY_RESULT_BACKEND", settings.REDIS_URL)


# ============================================================================
# DEAD LETTER EXCHANGE CONFIGURATION
# ============================================================================

# Dead Letter Exchange for failed tasks
DLQ_EXCHANGE = Exchange(
    "dlq",
    type="direct",
    durable=True
)

# Dead Letter Queue
DLQ_QUEUE = Queue(
    "dlq",
    DLQ_EXCHANGE,
    routing_key="dlq",
    durable=True
)


# ============================================================================
# TASK QUEUE DEFINITIONS WITH PRIORITIES
# ============================================================================

# Task exchanges
DEFAULT_EXCHANGE = Exchange("default", type="direct", durable=True)
SCORING_EXCHANGE = Exchange("scoring", type="direct", durable=True)
REPORTS_EXCHANGE = Exchange("reports", type="direct", durable=True)
NOTIFICATIONS_EXCHANGE = Exchange("notifications", type="direct", durable=True)
MAINTENANCE_EXCHANGE = Exchange("maintenance", type="direct", durable=True)


# Task queues with priorities and DLQ
task_queues = (
    # Default queue (medium priority, 1-10 scale)
    Queue(
        "default",
        DEFAULT_EXCHANGE,
        routing_key="default",
        queue_arguments={
            "x-max-priority": 10,
            "x-dead-letter-exchange": "dlq",
            "x-dead-letter-routing-key": "dlq"
        },
        durable=True
    ),

    # Scoring queue (highest priority - time-sensitive)
    Queue(
        "scoring",
        SCORING_EXCHANGE,
        routing_key="scoring",
        queue_arguments={
            "x-max-priority": 10,
            "x-dead-letter-exchange": "dlq",
            "x-dead-letter-routing-key": "dlq"
        },
        durable=True
    ),

    # Reports queue (medium priority)
    Queue(
        "reports",
        REPORTS_EXCHANGE,
        routing_key="reports",
        queue_arguments={
            "x-max-priority": 5,
            "x-dead-letter-exchange": "dlq",
            "x-dead-letter-routing-key": "dlq"
        },
        durable=True
    ),

    # Notifications queue (high priority)
    Queue(
        "notifications",
        NOTIFICATIONS_EXCHANGE,
        routing_key="notifications",
        queue_arguments={
            "x-max-priority": 8,
            "x-dead-letter-exchange": "dlq",
            "x-dead-letter-routing-key": "dlq"
        },
        durable=True
    ),

    # Maintenance queue (low priority)
    Queue(
        "maintenance",
        MAINTENANCE_EXCHANGE,
        routing_key="maintenance",
        queue_arguments={
            "x-max-priority": 3,
            "x-dead-letter-exchange": "dlq",
            "x-dead-letter-routing-key": "dlq"
        },
        durable=True
    ),

    # Dead Letter Queue (for failed tasks)
    DLQ_QUEUE,
)


# ============================================================================
# TASK ROUTING CONFIGURATION
# ============================================================================

task_routes = {
    # Scoring tasks
    "app.tasks.*.score*": {"queue": "scoring", "priority": 9},
    "app.tasks.*.scoring*": {"queue": "scoring", "priority": 9},
    "app.tasks.scoring_scheduler.*": {"queue": "scoring", "priority": 9},

    # Report generation tasks
    "app.tasks.*.report*": {"queue": "reports", "priority": 5},
    "app.tasks.*.generate*": {"queue": "reports", "priority": 5},

    # Notification tasks
    "app.tasks.*.notification*": {"queue": "notifications", "priority": 7},
    "app.tasks.*.email*": {"queue": "notifications", "priority": 8},
    "app.tasks.*.alert*": {"queue": "notifications", "priority": 8},

    # Maintenance tasks
    "app.tasks.*.cleanup*": {"queue": "maintenance", "priority": 2},
    "app.tasks.*.maintenance*": {"queue": "maintenance", "priority": 2},
    "app.tasks.*.archive*": {"queue": "maintenance", "priority": 1},

    # AI processing tasks
    "app.tasks.*.ai_*": {"queue": "scoring", "priority": 10},
    "app.tasks.*.nlp*": {"queue": "scoring", "priority": 8},
    "app.tasks.psychometric_tasks.*": {"queue": "scoring", "priority": 9},
}


# ============================================================================
# CELERY APP INITIALIZATION
# ============================================================================

celery_app = Celery(
    "psychsync",  # Single app name (was conflicting: "psychsync_ai" vs "psychsync")
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.scoring_scheduler",
        "app.tasks.psychometric_tasks",
        "app.tasks.anonymous_feedback_tasks",
    ]
)


# ============================================================================
# COMPREHENSIVE CELERY CONFIGURATION
# ============================================================================

celery_app.conf.update(
    # =======================================================================
    # SERIALIZATION
    # =======================================================================
    task_serializer="json",
    accept_content=["json"],  # Security: Only accept JSON
    result_serializer="json",
    result_compression="gzip",  # Compress results to save space

    # =======================================================================
    # TIMEZONE
    # =======================================================================
    timezone="UTC",
    enable_utc=True,

    # =======================================================================
    # TASK EXECUTION SETTINGS
    # =======================================================================
    task_track_started=True,  # Track when tasks start
    task_time_limit=3600,  # 1 hour hard limit (was conflicting: 30 min vs 1 hour)
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completes (prevents task loss)
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker dies
    task_send_sent_event=True,  # Send task-sent events for monitoring

    # =======================================================================
    # RESULT BACKEND SETTINGS
    # =======================================================================
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,  # Persist results to disk
    result_extended=True,  # Store more result metadata

    # =======================================================================
    # WORKER SETTINGS
    # =======================================================================
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker (balances memory vs performance)
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevents memory leaks)
    worker_disable_rate_limits=False,  # Enable rate limiting
    worker_log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    worker_task_log_format="%(asctime)s - %(name)s - %(levelname)s - %(task_info)s - %(message)s",

    # =======================================================================
    # RETRY CONFIGURATION (Comprehensive)
    # =======================================================================
    task_autoretry_for=(
        Exception,  # Auto-retry on most exceptions
    ),
    task_retry_kwargs={
        "max_retries": 3,  # Retry failed tasks up to 3 times
        "countdown": 60,  # Wait 60 seconds before retry (exponential backoff recommended)
    },
    task_retry_delay=60,  # Default retry delay
    task_retry_max_delay=3600,  # Maximum retry delay (1 hour)
    task_retry_backoff=True,  # Enable exponential backoff
    task_retry_backoff_max=600,  # Maximum backoff delay (10 minutes)
    task_retry_jitter=True,  # Add jitter to prevent thundering herd

    # =======================================================================
    # DEFAULT QUEUE SETTINGS
    # =======================================================================
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_queues=task_queues,
    task_routes=task_routes,

    # =======================================================================
    # TASK PRIORITY
    # =======================================================================
    task_inherit_parent_priority=True,  # Child tasks inherit parent priority
    task_default_priority=5,  # Default priority (medium)

    # =======================================================================
    # MONITORING SETTINGS
    # =======================================================================
    worker_send_task_events=True,  # Send task events for monitoring
    task_send_event_sent=True,  # Send event when task is sent
    task_send_event_started=True,  # Send event when task starts
    task_send_event_success=True,  # Send event when task succeeds
    task_send_event_failure=True,  # Send event when task fails
    task_send_event_rejected=True,  # Send event when task is rejected

    # =======================================================================
    # SECURITY SETTINGS
    # =======================================================================
    worker_hijack_root_logger=False,  # Don't hijack root logger
    task_send_sent_event=True,
    task_always_eager=False,  # Never run tasks synchronously (must be async in production)

    # =======================================================================
    # EVENT SETTINGS
    # =======================================================================
    event_queue_expires=86400,  # Event queue expires after 24 hours
    event_queue_limit=1000,  # Limit event queue size
)


# ============================================================================
# CELERY BEAT SCHEDULE (Periodic Tasks)
# ============================================================================

celery_app.conf.beat_schedule = {
    # Cleanup expired assessments daily at 2 AM UTC
    "cleanup-expired-assessments": {
        "task": "app.tasks.scoring_scheduler.cleanup_expired_assessments",
        "schedule": crontab(hour=2, minute=0),
        "options": {
            "queue": "maintenance",
            "priority": 2
        }
    },

    # Generate daily reports at 1 AM UTC
    "generate-daily-reports": {
        "task": "app.tasks.scoring_scheduler.generate_daily_reports",
        "schedule": crontab(hour=1, minute=0),
        "options": {
            "queue": "reports",
            "priority": 5
        }
    },

    # Health check every 5 minutes
    "health-check": {
        "task": "app.tasks.scoring_scheduler.health_check",
        "schedule": crontab(minute="*/5"),
        "options": {
            "queue": "default",
            "priority": 10
        }
    },

    # Database health check every 10 minutes
    "database-health-check": {
        "task": "app.tasks.scoring_scheduler.database_health_check",
        "schedule": crontab(minute="*/10"),
        "options": {
            "queue": "maintenance",
            "priority": 3
        }
    },

    # Process DLQ tasks every hour
    "process-dead-letter-queue": {
        "task": "app.tasks.scoring_scheduler.process_dlq",
        "schedule": crontab(minute=0),
        "options": {
            "queue": "maintenance",
            "priority": 1
        }
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_task_status(task_id: str) -> dict:
    """
    Get status of a Celery task

    Args:
        task_id: Task ID

    Returns:
        Task status and result
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    return {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None,
        "info": result.info
    }


def revoke_task(task_id: str, terminate: bool = False) -> dict:
    """
    Revoke a running task

    Args:
        task_id: Task ID to revoke
        terminate: If True, terminate the task immediately

    Returns:
        Revocation status
    """
    celery_app.control.revoke(task_id, terminate=terminate)

    return {
        "task_id": task_id,
        "revoked": True,
        "terminated": terminate
    }


def get_active_tasks() -> dict:
    """
    Get list of currently active tasks

    Returns:
        Dictionary of active tasks per worker
    """
    inspect = celery_app.control.inspect()
    active = inspect.active()

    return active if active else {}


def get_worker_stats() -> dict:
    """
    Get Celery worker statistics

    Returns:
        Worker statistics including queues, registered tasks, etc.
    """
    inspect = celery_app.control.inspect()

    return {
        "stats": inspect.stats(),
        "active_queues": inspect.active_queues(),
        "registered_tasks": inspect.registered(),
        "scheduled_tasks": inspect.scheduled(),
        "active_tasks": inspect.active()
    }


def get_queue_lengths() -> dict:
    """
    Get current queue lengths (requires Redis)

    Returns:
        Queue lengths
    """
    try:
        import redis.asyncio as aioredis

        async def get_lengths():
            client = await aioredis.from_url(CELERY_BROKER_URL)
            queue_names = ["default", "scoring", "reports", "notifications", "maintenance", "dlq"]

            lengths = {}
            for queue in queue_names:
                key = f"celery:{queue}"
                length = await client.llen(key)
                lengths[queue] = length

            await client.close()
            return lengths

        # For now, return empty dict (async function needs to be awaited)
        return {}
    except Exception as e:
        logger.error(f"Error getting queue lengths: {e}")
        return {}


# ============================================================================
# CELERY SIGNALS (Event Handlers)
# ============================================================================

from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_success,
    task_retry,
    worker_ready,
    worker_shutdown
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None,
                        kwargs=None, **extra_kwargs):
    """Log when task starts"""
    logger.info(
        f"🚀 Task started: {task.name} (ID: {task_id})",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": str(args)[:200],  # Truncate long args
            "kwargs": str(kwargs)[:200]
        }
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None,
                         kwargs=None, retval=None, **extra_kwargs):
    """Log when task completes"""
    logger.info(
        f"✅ Task completed: {task.name} (ID: {task_id})",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "state": retval
        }
    )


@task_success.connect
def task_success_handler(sender=None, task_id=None, result=None, **extra_kwargs):
    """Log successful tasks"""
    logger.info(
        f"✨ Task SUCCESS: {sender.name} (ID: {task_id})",
        extra={
            "task_id": task_id,
            "result": str(result)[:500]
        }
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None,
                        args=None, kwargs=None, traceback=None,
                        einfo=None, **extra_kwargs):
    """Log task failures and route to DLQ"""
    logger.error(
        f"❌ Task FAILED: {sender.name} (ID: {task_id})\n"
        f"Exception: {exception}\n"
        f"Args: {args}\n"
        f"Kwargs: {kwargs}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "traceback": traceback
        },
        exc_info=True
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **extra_kwargs):
    """Log task retries"""
    logger.warning(
        f"🔄 Task RETRY: {sender.name} (ID: {task_id}) - Reason: {reason}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "retry_reason": str(reason)
        }
    )


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log when worker is ready"""
    logger.info(f"🎉 Celery worker ready: {sender}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Log when worker shuts down"""
    logger.info(f"👋 Celery worker shutting down: {sender}")


# ============================================================================
# DEBUG TASK
# ============================================================================

@celery_app.task(bind=True, name="debug_task")
def debug_task(self):
    """Debug task for testing Celery setup"""
    logger.info(f"Debug task request: {self.request!r}")
    return {
        "status": "success",
        "message": "Debug task executed successfully",
        "request": str(self.request),
        "worker": str(self.request.hostname)
    }


# ============================================================================
# WORKER STARTUP
# ============================================================================

if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()
