"""
File Path: app/core/celery_worker.py
Celery configuration and worker setup
Handles asynchronous task processing and scheduling
"""
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue
import logging
import os

logger = logging.getLogger(__name__)


# =================================================================
# CELERY BROKER/BACKEND CONFIGURATION
# =================================================================

# Get broker URL from environment or use default
CELERY_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'redis://localhost:6379/0'
)

CELERY_RESULT_BACKEND = os.getenv(
    'CELERY_RESULT_BACKEND',
    'redis://localhost:6379/0'
)


# =================================================================
# CELERY APP INITIALIZATION
# =================================================================

celery_app = Celery(
    "psychsync",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.scoring_scheduler',
    ]
)


# =================================================================
# CELERY CONFIGURATION
# =================================================================

celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routes
    task_routes={
        'tasks.calculate_assessment_scores': {'queue': 'scoring'},
        'tasks.process_assessment_batch': {'queue': 'scoring'},
        'tasks.generate_assessment_report': {'queue': 'reports'},
        'tasks.send_assessment_notification': {'queue': 'notifications'},
        'tasks.cleanup_expired_assessments': {'queue': 'maintenance'},
        'tasks.generate_daily_reports': {'queue': 'reports'},
    },
    
    # Queue definitions
    task_queues=(
        Queue(
            'default',
            Exchange('default'),
            routing_key='default',
            queue_arguments={'x-max-priority': 10}
        ),
        Queue(
            'scoring',
            Exchange('scoring'),
            routing_key='scoring',
            queue_arguments={'x-max-priority': 10}
        ),
        Queue(
            'reports',
            Exchange('reports'),
            routing_key='reports',
            queue_arguments={'x-max-priority': 5}
        ),
        Queue(
            'notifications',
            Exchange('notifications'),
            routing_key='notifications',
            queue_arguments={'x-max-priority': 8}
        ),
        Queue(
            'maintenance',
            Exchange('maintenance'),
            routing_key='maintenance',
            queue_arguments={'x-max-priority': 3}
        ),
    ),
    
    # Default queue
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
)


# =================================================================
# CELERY BEAT SCHEDULE (PERIODIC TASKS)
# =================================================================

celery_app.conf.beat_schedule = {
    # Cleanup expired assessments daily at 2 AM
    'cleanup-expired-assessments': {
        'task': 'tasks.cleanup_expired_assessments',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'}
    },
    
    # Generate daily reports at 1 AM
    'generate-daily-reports': {
        'task': 'tasks.generate_daily_reports',
        'schedule': crontab(hour=1, minute=0),
        'options': {'queue': 'reports'}
    },
    
    # Health check every 5 minutes
    'health-check': {
        'task': 'tasks.health_check',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default'}
    },
    
    # Database health check every 10 minutes
    'database-health-check': {
        'task': 'tasks.database_health_check',
        'schedule': crontab(minute='*/10'),
        'options': {'queue': 'maintenance'}
    },
}


# =================================================================
# CELERY EVENTS AND LOGGING
# =================================================================

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    logger.info(f'Request: {self.request!r}')
    return {
        'status': 'success',
        'message': 'Debug task executed successfully',
        'request': str(self.request)
    }


# =================================================================
# CELERY SIGNALS
# =================================================================

from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    worker_ready,
    worker_shutdown
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, 
                        kwargs=None, **extra_kwargs):
    """Log when task starts"""
    logger.info(
        f"Task started: {task.name} (ID: {task_id})"
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None,
                         kwargs=None, retval=None, **extra_kwargs):
    """Log when task completes"""
    logger.info(
        f"Task completed: {task.name} (ID: {task_id})"
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, 
                        args=None, kwargs=None, traceback=None, 
                        einfo=None, **extra_kwargs):
    """Log task failures"""
    logger.error(
        f"Task failed: {sender.name} (ID: {task_id})\n"
        f"Exception: {exception}\n"
        f"Traceback: {traceback}"
    )


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log when worker is ready"""
    logger.info(f"Celery worker ready: {sender}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Log when worker shuts down"""
    logger.info(f"Celery worker shutting down: {sender}")


# =================================================================
# HELPER FUNCTIONS
# =================================================================

def get_task_status(task_id: str):
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
        'task_id': task_id,
        'status': result.state,
        'result': result.result if result.ready() else None,
        'traceback': result.traceback if result.failed() else None
    }


def revoke_task(task_id: str, terminate: bool = False):
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
        'task_id': task_id,
        'revoked': True,
        'terminated': terminate
    }


def get_active_tasks():
    """
    Get list of currently active tasks
    
    Returns:
        List of active tasks
    """
    inspect = celery_app.control.inspect()
    active = inspect.active()
    
    return active if active else {}


def get_worker_stats():
    """
    Get Celery worker statistics
    
    Returns:
        Worker statistics
    """
    inspect = celery_app.control.inspect()
    
    return {
        'stats': inspect.stats(),
        'active_queues': inspect.active_queues(),
        'registered_tasks': inspect.registered(),
        'scheduled_tasks': inspect.scheduled()
    }


# =================================================================
# WORKER STARTUP
# =================================================================

if __name__ == '__main__':
    # Start Celery worker
    celery_app.start()