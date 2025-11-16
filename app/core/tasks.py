# app/core/tasks.py
"""
Advanced Celery background task system for PsychSync
Includes task scheduling, retry logic, and performance monitoring
"""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from celery import Celery, Task
from celery.result import AsyncResult
from celery.exceptions import Retry, WorkerLostError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_async_db
from app.core.constants import AIProcessing, Email

logger = logging.getLogger(__name__)

# Initialize Celery with advanced configuration
celery_app = Celery(
    "psychsync_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.email_tasks',
        'app.tasks.ai_processing_tasks',
        'app.tasks.analytics_tasks',
        'app.tasks.maintenance_tasks'
    ]
)

# Advanced Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'app.tasks.email_tasks.*': {'queue': 'email'},
        'app.tasks.ai_processing_tasks.*': {'queue': 'ai_processing'},
        'app.tasks.analytics_tasks.*': {'queue': 'analytics'},
        'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
        'app.tasks.critical_tasks.*': {'queue': 'critical'},
    },

    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,

    # Task execution
    task_always_eager=False,  # Don't run tasks synchronously
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,

    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_acks_late=True,
    worker_send_task_events=True,

    # Result backend
    result_expires=3600,       # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },

    # Retry configuration
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    # Monitoring and events
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Beat scheduler (for periodic tasks)
    beat_schedule={
        'cleanup-expired-tokens': {
            'task': 'app.tasks.maintenance_tasks.cleanup_expired_tokens',
            'schedule': 3600.0,  # Every hour
        },
        'update-user-statistics': {
            'task': 'app.tasks.analytics_tasks.update_user_statistics',
            'schedule': 1800.0,  # Every 30 minutes
        },
        'cache-warmup': {
            'task': 'app.tasks.maintenance_tasks.cache_warmup',
            'schedule': 900.0,   # Every 15 minutes
        },
        'health-check': {
            'task': 'app.tasks.maintenance_tasks.health_check',
            'schedule': 300.0,   # Every 5 minutes
        },
    },
    timezone='UTC',
)

@dataclass
class TaskMetadata:
    """Metadata for tracking tasks"""
    task_id: str
    task_name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    worker_id: Optional[str] = None
    runtime: Optional[float] = None

class TaskRegistry:
    """Registry for tracking and managing tasks"""

    def __init__(self):
        self.active_tasks: Dict[str, TaskMetadata] = {}
        self.task_history: List[TaskMetadata] = []
        self.max_history = 10000

    def register_task(
        self,
        task_id: str,
        task_name: str,
        max_retries: int = 3
    ) -> TaskMetadata:
        """Register a new task"""
        metadata = TaskMetadata(
            task_id=task_id,
            task_name=task_name,
            status='PENDING',
            created_at=datetime.utcnow(),
            max_retries=max_retries
        )

        self.active_tasks[task_id] = metadata
        return metadata

    def update_task_status(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None,
        worker_id: Optional[str] = None
    ):
        """Update task status"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = status
            task.error = error
            task.worker_id = worker_id

            if status == 'STARTED' and not task.started_at:
                task.started_at = datetime.utcnow()
            elif status in ['SUCCESS', 'FAILURE', 'RETRY']:
                task.completed_at = datetime.utcnow()
                if task.started_at:
                    task.runtime = (task.completed_at - task.started_at).total_seconds()

                # Move to history
                self.task_history.append(task)
                del self.active_tasks[task_id]

                # Cleanup old history
                if len(self.task_history) > self.max_history:
                    self.task_history = self.task_history[-self.max_history:]

    def get_task_stats(self) -> Dict[str, Any]:
        """Get task statistics"""
        total_tasks = len(self.task_history) + len(self.active_tasks)
        completed_tasks = [t for t in self.task_history if t.status == 'SUCCESS']
        failed_tasks = [t for t in self.task_history if t.status == 'FAILURE']

        return {
            'total_tasks': total_tasks,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(completed_tasks),
            'failed_tasks': len(failed_tasks),
            'success_rate': (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0,
            'failure_rate': (len(failed_tasks) / total_tasks * 100) if total_tasks > 0 else 0,
            'avg_runtime': (
                sum(t.runtime for t in completed_tasks if t.runtime) /
                len(completed_tasks)
                if completed_tasks else 0
            )
        }

# Global task registry
task_registry = TaskRegistry()

class CustomTask(Task):
    """Custom task class with advanced features"""

    def on_success(self, retval, task_id, args, kwargs):
        """Task success handler"""
        task_registry.update_task_status(task_id, 'SUCCESS')
        logger.info(f"Task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Task failure handler"""
        error_message = str(exc)
        task_registry.update_task_status(task_id, 'FAILURE', error_message)
        logger.error(f"Task {task_id} failed: {error_message}")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Task retry handler"""
        task = task_registry.active_tasks.get(task_id)
        if task:
            task.retry_count += 1
            task_registry.update_task_status(task_id, 'RETRY')
        logger.warning(f"Task {task_id} retrying (attempt {task.retry_count if task else 1})")

    def on_apply(self, *args, **kwargs):
        """Task apply handler"""
        task_id = kwargs.get('task_id')
        if task_id:
            task_name = self.name
            max_retries = kwargs.get('max_retries', 3)
            task_registry.register_task(task_id, task_name, max_retries)
        return super().on_apply(*args, **kwargs)

# Set custom task class
celery_app.Task = CustomTask

class TaskManager:
    """Advanced task management system"""

    @staticmethod
    def send_task(
        task_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        queue: Optional[str] = None,
        eta: Optional[datetime] = None,
        countdown: Optional[int] = None,
        expires: Optional[datetime] = None,
        retry: bool = True,
        retry_policy: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        soft_time_limit: Optional[int] = None,
        time_limit: Optional[int] = None
    ) -> AsyncResult:
        """
        Send task with advanced options
        """
        kwargs = kwargs or {}
        retry_policy = retry_policy or {
            'max_retries': 3,
            'interval_start': 0,
            'interval_step': 0.2,
            'interval_max': 0.2,
            'jitter': True,
        }

        task_options = {
            'queue': queue,
            'eta': eta,
            'countdown': countdown,
            'expires': expires,
            'retry': retry,
            'retry_policy': retry_policy,
            'priority': priority,
            'soft_time_limit': soft_time_limit,
            'time_limit': time_limit,
        }

        # Remove None values
        task_options = {k: v for k, v in task_options.items() if v is not None}

        result = celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs,
            **task_options
        )

        logger.info(f"Task {task_name} sent: {result.id}")
        return result

    @staticmethod
    def get_task_result(task_id: str) -> Dict[str, Any]:
        """Get comprehensive task result"""
        result = AsyncResult(task_id, app=celery_app)

        response = {
            'task_id': task_id,
            'status': result.status,
            'result': None,
            'error': None,
            'traceback': None,
            'date_done': None,
        }

        if result.ready():
            if result.successful():
                response['result'] = result.result
            else:
                response['error'] = str(result.result)
                response['traceback'] = result.traceback

            response['date_done'] = result.date_done

        # Add metadata from registry
        if task_id in task_registry.active_tasks:
            response['metadata'] = asdict(task_registry.active_tasks[task_id])
        else:
            # Check in history
            for task in task_registry.task_history:
                if task.task_id == task_id:
                    response['metadata'] = asdict(task)
                    break

        return response

    @staticmethod
    def cancel_task(task_id: str, terminate: bool = False) -> bool:
        """Cancel or terminate a task"""
        try:
            celery_app.control.revoke(task_id, terminate=terminate)
            logger.info(f"Task {task_id} cancelled (terminate={terminate})")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False

    @staticmethod
    def get_worker_stats() -> Dict[str, Any]:
        """Get worker statistics"""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            active = inspect.active()
            scheduled = inspect.scheduled()
            reserved = inspect.reserved()

            return {
                'stats': stats or {},
                'active_tasks': active or {},
                'scheduled_tasks': scheduled or {},
                'reserved_tasks': reserved or {},
                'worker_count': len(stats) if stats else 0
            }
        except Exception as e:
            logger.error(f"Error getting worker stats: {str(e)}")
            return {}

    @staticmethod
    def purge_queue(queue_name: str) -> int:
        """Purge all tasks from a queue"""
        try:
            with celery_app.connection() as conn:
                channel = conn.channel()
                purged = channel.queue_purge(queue_name)
                logger.info(f"Purged {purged} tasks from queue: {queue_name}")
                return purged
        except Exception as e:
            logger.error(f"Error purging queue {queue_name}: {str(e)}")
            return 0

# Email tasks
def send_email_async(
    to_email: str,
    subject: str,
    template_name: str,
    template_data: Dict[str, Any],
    priority: int = 5,
    delay: Optional[int] = None
) -> AsyncResult:
    """Send email asynchronously"""
    return TaskManager.send_task(
        'app.tasks.email_tasks.send_email',
        kwargs={
            'to_email': to_email,
            'subject': subject,
            'template_name': template_name,
            'template_data': template_data
        },
        queue='email',
        priority=priority,
        countdown=delay
    )

def send_welcome_email(user_email: str, user_name: str) -> AsyncResult:
    """Send welcome email to new user"""
    return send_email_async(
        to_email=user_email,
        subject="Welcome to PsychSync!",
        template_name=Email.TEMPLATE_WELCOME,
        template_data={'user_name': user_name},
        priority=10  # High priority
    )

def send_password_reset_email(user_email: str, reset_token: str) -> AsyncResult:
    """Send password reset email"""
    return send_email_async(
        to_email=user_email,
        subject="Reset your PsychSync password",
        template_name=Email.TEMPLATE_PASSWORD_RESET,
        template_data={'reset_token': reset_token},
        priority=8  # High priority
    )

# AI Processing tasks
def process_assessment_results(
    assessment_id: str,
    user_id: str,
    framework: str,
    raw_data: Dict[str, Any]
) -> AsyncResult:
    """Process assessment results asynchronously"""
    return TaskManager.send_task(
        'app.tasks.ai_processing_tasks.process_assessment',
        kwargs={
            'assessment_id': assessment_id,
            'user_id': user_id,
            'framework': framework,
            'raw_data': raw_data
        },
        queue='ai_processing',
        time_limit=AIProcessing.LONG_PROCESSING_TIMEOUT,
        retry=True,
        retry_policy={
            'max_retries': 3,
            'interval_start': 60,  # Start with 1 minute delay
            'interval_step': 60,  # Add 1 minute each retry
            'interval_max': 300,  # Max 5 minutes between retries
        }
    )

def generate_user_insights(user_id: str) -> AsyncResult:
    """Generate user insights asynchronously"""
    return TaskManager.send_task(
        'app.tasks.ai_processing_tasks.generate_insights',
        kwargs={'user_id': user_id},
        queue='analytics',
        time_limit=600  # 10 minutes
    )

# Analytics tasks
def update_user_analytics(user_id: str) -> AsyncResult:
    """Update user analytics asynchronously"""
    return TaskManager.send_task(
        'app.tasks.analytics_tasks.update_user_analytics',
        kwargs={'user_id': user_id},
        queue='analytics'
    )

def generate_team_analytics(team_id: str) -> AsyncResult:
    """Generate team analytics asynchronously"""
    return TaskManager.send_task(
        'app.tasks.analytics_tasks.generate_team_analytics',
        kwargs={'team_id': team_id},
        queue='analytics',
        time_limit=300  # 5 minutes
    )

# Maintenance tasks
def schedule_cache_warmup(cache_patterns: List[str]) -> AsyncResult:
    """Schedule cache warmup for specific patterns"""
    return TaskManager.send_task(
        'app.tasks.maintenance_tasks.warm_cache',
        kwargs={'cache_patterns': cache_patterns},
        queue='maintenance',
        priority=2  # Low priority
    )

def cleanup_expired_data() -> AsyncResult:
    """Schedule cleanup of expired data"""
    return TaskManager.send_task(
        'app.tasks.maintenance_tasks.cleanup_expired_data',
        queue='maintenance',
        priority=1  # Lowest priority
    )

# Task monitoring utilities
async def get_task_health() -> Dict[str, Any]:
    """Get comprehensive task health information"""
    task_stats = task_registry.get_task_stats()
    worker_stats = TaskManager.get_worker_stats()

    # Get queue information
    try:
        inspect = celery_app.control.inspect()
        active_queues = inspect.active_queues()
    except Exception:
        active_queues = []

    return {
        'task_stats': task_stats,
        'worker_stats': worker_stats,
        'active_queues': active_queues or [],
        'timestamp': datetime.utcnow().isoformat()
    }

# Celery beat startup check
def ensure_celery_running():
    """Ensure Celery workers are running"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if not stats:
            logger.warning("No Celery workers are running!")
            return False
        logger.info(f"Celery workers running: {list(stats.keys())}")
        return True
    except Exception as e:
        logger.error(f"Error checking Celery status: {str(e)}")
        return False

# Initialize Celery
def init_celery():
    """Initialize Celery application"""
    if not settings.CELERY_BROKER_URL:
        logger.warning("Celery broker URL not configured")
        return

    # Auto-discover tasks
    celery_app.autodiscover_tasks(['app'])

    # Configure error handling
    @celery_app.task(bind=True)
    def debug_task(self):
        """Debug task for testing"""
        print(f'Request: {self.request!r}')

    logger.info("Celery initialized successfully")

# Task execution monitoring
class TaskMonitor:
    """Monitor task execution in real-time"""

    def __init__(self):
        self.start_time = time.time()
        self.task_counts = {}
        self.error_counts = {}

    def monitor_task(self, task_name: str, success: bool, duration: float):
        """Monitor task execution"""
        self.task_counts[task_name] = self.task_counts.get(task_name, 0) + 1

        if not success:
            self.error_counts[task_name] = self.error_counts.get(task_name, 0) + 1

        # Log slow tasks
        if duration > 10:  # Tasks taking more than 10 seconds
            logger.warning(f"Slow task detected: {task_name} took {duration:.2f}s")

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        uptime = time.time() - self.start_time
        total_tasks = sum(self.task_counts.values())
        total_errors = sum(self.error_counts.values())

        return {
            'uptime_seconds': uptime,
            'total_tasks': total_tasks,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_tasks * 100) if total_tasks > 0 else 0,
            'tasks_per_minute': (total_tasks / (uptime / 60)) if uptime > 0 else 0,
            'task_counts': self.task_counts,
            'error_counts': self.error_counts
        }

# Global task monitor
task_monitor = TaskMonitor()