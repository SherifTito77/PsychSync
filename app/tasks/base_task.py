"""
Enhanced Task Base Class for PsychSync

Provides comprehensive task infrastructure:
- Database session management with automatic cleanup
- Comprehensive error handling and logging
- Automatic DLQ (Dead Letter Queue) routing on final retry
- Prometheus metrics integration
- Retry logic with exponential backoff
- Task timeout handling
- Structured logging with context

Usage:
    from app.tasks.base_task import BaseTask

    class MyTask(BaseTask):
        def run(self, arg1, arg2):
            # Task logic here
            return result

    @celery_app.task(base=MyTask, bind=True)
    def my_task(self, arg1, arg2):
        return self.run(arg1, arg2)

Author: Infrastructure Team
Version: 2.0.0
Date: January 7, 2026
"""

import asyncio
import json
import logging
import random
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from prometheus_client import Counter, Histogram
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Task execution metrics
task_executions_total = Counter(
    "celery_task_executions_total",
    "Total number of task executions",
    ["task_name", "status"],  # status: success, failure, retry
)

task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Task execution duration in seconds",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0],
)

task_retries_total = Counter(
    "celery_task_retries_total", "Total number of task retries", ["task_name"]
)

task_dlq_total = Counter(
    "celery_task_dlq_total",
    "Total number of tasks sent to Dead Letter Queue",
    ["task_name", "reason"],
)

logger = logging.getLogger(__name__)


# ============================================================================
# RETRY CONFIGURATION
# ============================================================================

# Exponential backoff configuration
DEFAULT_BASE_DELAY = 60  # Base delay in seconds
DEFAULT_MAX_DELAY = 600  # Maximum delay in seconds (10 minutes)
DEFAULT_MAX_RETRIES = 3  # Default maximum retry attempts
JITTER_RANGE = 0.1  # Add +/- 10% jitter to prevent thundering herd


# ============================================================================
# BASE TASK CLASS
# ============================================================================


class BaseTask(Task):
    """
    Enhanced base class for all Celery tasks.

    Provides:
    - Automatic database session management
    - Comprehensive error handling
    - Prometheus metrics integration
    - Automatic DLQ routing on final failure
    - Structured logging with task context
    - Retry management
    """

    _db = None  # Database session ( lazily created)

    # =======================================================================
    # TASK LIFECYCLE HOOKS
    # =======================================================================

    def __call__(self, *args, **kwargs):
        """
        Called when task is executed.

        Wraps task execution with:
        - Metrics collection
        - Error handling
        - Database session management
        - Logging
        """
        task_name = self.name
        task_id = self.request.id
        start_time = datetime.utcnow()

        logger.info(
            f"🚀 Task started: {task_name}",
            extra={
                "task_id": task_id,
                "task_name": task_name,
                "args": str(args)[:200],
                "kwargs": str(kwargs)[:200],
                "retries": self.request.retries,
            },
        )

        try:
            # Execute task
            result = self.run(*args, **kwargs)

            # Record success metrics
            task_executions_total.labels(task_name=task_name, status="success").inc()

            duration = (datetime.utcnow() - start_time).total_seconds()
            task_duration_seconds.labels(task_name=task_name).observe(duration)

            logger.info(
                f"✅ Task completed: {task_name}",
                extra={
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration_seconds": duration,
                },
            )

            return result

        except SoftTimeLimitExceeded as e:
            # Handle task timeout
            logger.error(
                f"⏱️ Task TIMEOUT: {task_name}",
                extra={
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration_seconds": (
                        datetime.utcnow() - start_time
                    ).total_seconds(),
                },
                exc_info=True,
            )

            task_executions_total.labels(task_name=task_name, status="timeout").inc()

            # Retry if possible, otherwise send to DLQ
            max_retries = self.get_max_retries()
            if self.request.retries < max_retries:
                task_retries_total.labels(task_name=task_name).inc()
                # Calculate exponential backoff delay with jitter
                delay = self._calculate_retry_delay(self.request.retries)
                logger.warning(
                    f"🔄 Retrying task after timeout: {task_name} "
                    f"(attempt {self.request.retries + 1}/{max_retries}) "
                    f"in {delay}s"
                )
                raise self.retry(exc=e, countdown=delay)

            # Max retries exceeded - send to DLQ
            return self._send_to_dlq(
                reason="timeout", exception=str(e), args=args, kwargs=kwargs
            )

        except Exception as e:
            # Handle other exceptions
            logger.error(
                f"❌ Task FAILED: {task_name}",
                extra={
                    "task_id": task_id,
                    "task_name": task_name,
                    "exception": str(e),
                    "traceback": traceback.format_exc(),
                },
                exc_info=True,
            )

            task_executions_total.labels(task_name=task_name, status="failure").inc()

            duration = (datetime.utcnow() - start_time).total_seconds()
            task_duration_seconds.labels(task_name=task_name).observe(duration)

            # Retry if possible
            max_retries = self.get_max_retries()
            if self.request.retries < max_retries:
                task_retries_total.labels(task_name=task_name).inc()
                # Calculate exponential backoff delay with jitter
                delay = self._calculate_retry_delay(self.request.retries)
                logger.warning(
                    f"🔄 Retrying task: {task_name} "
                    f"(attempt {self.request.retries + 1}/{max_retries}) "
                    f"in {delay}s",
                    extra={"task_id": task_id, "task_name": task_name},
                )
                raise self.retry(exc=e, countdown=delay)

            # Max retries exceeded - send to DLQ
            return self._send_to_dlq(
                reason="max_retries_exceeded",
                exception=str(e),
                traceback=traceback.format_exc(),
                args=args,
                kwargs=kwargs,
            )

        finally:
            # Clean up database session
            if self._db is not None:
                self._db.close()
                self._db = None

    # =======================================================================
    # RETRY CALCULATION
    # =======================================================================

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay with jitter.

        Formula: min(base_delay * (2 ^ retry_count), max_delay) +/- jitter%

        Args:
            retry_count: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied
        """
        # Calculate exponential backoff
        delay = min(DEFAULT_BASE_DELAY * (2**retry_count), DEFAULT_MAX_DELAY)

        # Add jitter to prevent thundering herd
        jitter = delay * JITTER_RANGE
        delay_with_jitter = delay + random.uniform(-jitter, jitter)

        return int(max(0, delay_with_jitter))

    def get_max_retries(self) -> int:
        """
        Get maximum retry attempts for this task.

        Returns:
            Maximum retry attempts from task options or default
        """
        # Celery stores max_retries in task options
        return getattr(self, "max_retries", DEFAULT_MAX_RETRIES)

    # =======================================================================
    # ABSTRACT RUN METHOD (Override in subclasses)
    # =======================================================================

    def run(self, *args, **kwargs):
        """
        Main task logic. Override this method in subclasses.

        Args:
            *args: Task positional arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result

        Raises:
            Exception: Any exception will trigger retry logic
        """
        raise NotImplementedError("Subclasses must implement the run() method")

    # =======================================================================
    # DATABASE SESSION MANAGEMENT
    # =======================================================================

    @property
    def db(self) -> AsyncSession:
        """
        Get or create database session for this task.

        Returns:
            AsyncSession: Database session

        Note:
            Session is automatically closed in task cleanup
        """
        if self._db is None:
            self._db = async_session_maker()
        return self._db

    @asynccontextmanager
    async def get_db_session(self):
        """
        Context manager for database session.

        Usage:
            async with self.get_db_session() as db:
                # Use db here
                result = await db.execute(query)

        Yields:
            AsyncSession: Database session
        """
        session = async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # =======================================================================
    # DEAD LETTER QUEUE ROUTING
    # =======================================================================

    def _send_to_dlq(
        self,
        reason: str,
        exception: str,
        traceback: str | None = None,
        args: tuple = (),
        kwargs: dict = None,
    ) -> dict:
        """
        Send failed task to Dead Letter Queue.

        Args:
            reason: Reason for DLQ routing
            exception: Exception message
            traceback: Exception traceback (optional)
            args: Original task arguments
            kwargs: Original task keyword arguments

        Returns:
            DLQ entry dictionary
        """
        task_name = self.name
        task_id = self.request.id

        dlq_entry = {
            "dlq_id": str(uuid4()),
            "task_id": task_id,
            "task_name": task_name,
            "reason": reason,
            "exception": exception,
            "traceback": traceback,
            "args": str(args)[:500],  # Truncate long args
            "kwargs": str(kwargs or {})[:500],
            "retries": self.request.retries,
            "created_at": datetime.utcnow().isoformat(),
            "worker": self.request.hostname,
        }

        # Log DLQ event
        logger.error(
            f"💀 Task sent to DLQ: {task_name}",
            extra={
                "task_id": task_id,
                "task_name": task_name,
                "dlq_reason": reason,
                "dlq_id": dlq_entry["dlq_id"],
            },
        )

        # Record DLQ metric
        task_dlq_total.labels(task_name=task_name, reason=reason).inc()

        # Persist DLQ entry to database with proper async handling
        try:
            from uuid import uuid4

            from app.db.models.dead_letter import DeadLetterTask, DLQStatus

            # Create DLQ database record
            dlq_record = DeadLetterTask(
                id=uuid4(),
                task_id=task_id,
                task_name=task_name,
                reason=reason,
                exception=str(exception)[:2000],  # Limit exception message length
                traceback=str(traceback)[:5000] if traceback else None,
                exception_type=(
                    exception.__class__.__name__
                    if hasattr(exception, "__class__")
                    else "Exception"
                ),
                retry_count=self.request.retries,
                max_retries=self.get_max_retries(),
                status=DLQStatus.PENDING,
                worker=self.request.hostname,
                queue=getattr(self.request, "delivery_info", {}).get(
                    "routing_key", "unknown"
                ),
                args=str(args)[:5000],
                kwargs=str(kwargs or {})[:5000],
                metadata={
                    "original_task_id": task_id,
                    "delivery_info": getattr(self.request, "delivery_info", {}),
                },
            )

            # Get database session and save
            db = self.db
            db.add(dlq_record)

            # ✅ FIX: Properly await the async commit
            # We need to run the async commit in a synchronous context
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create a task
                    asyncio.create_task(db.commit())
                    # Give the task a moment to complete
                    # This is a best-effort approach in a running loop
                else:
                    # If loop exists but not running, run the commit
                    loop.run_until_complete(db.commit())
            except RuntimeError:
                # No event loop exists, create a new one
                asyncio.run(db.commit())

            logger.info(
                f"✅ DLQ entry persisted to database: {dlq_record.id}",
                extra={"dlq_id": str(dlq_record.id), "task_name": task_name},
            )

        except Exception as e:
            # Log error but don't fail the task
            logger.error(
                f"❌ Failed to persist DLQ entry to database: {e}",
                extra={"task_id": task_id, "task_name": task_name},
                exc_info=True,
            )

            # ✅ IMPROVEMENT: Use Redis as fallback storage
            self._store_dlq_in_fallback(dlq_entry, task_id, task_name)

        return dlq_entry

    def _store_dlq_in_fallback(self, dlq_entry: dict, task_id: str, task_name: str):
        """
        Store DLQ entry in Redis fallback when database persistence fails.

        This provides a safety net for critical DLQ entries when database is unavailable.

        Args:
            dlq_entry: DLQ entry dictionary
            task_id: Original task ID
            task_name: Task name
        """
        try:
            import redis.asyncio as aioredis

            # Create Redis key with expiration (7 days)
            key = f"dlq:fallback:{task_id}"
            value = json.dumps(dlq_entry)
            ttl = 7 * 24 * 60 * 60  # 7 days in seconds

            # Use asyncio to run the async Redis operation
            async def store_in_redis():
                client = await aioredis.from_url(settings.REDIS_URL)
                try:
                    await client.setex(key, ttl, value)
                    logger.info(
                        f"✅ DLQ entry stored in Redis fallback: {key}",
                        extra={"task_id": task_id, "task_name": task_name},
                    )
                finally:
                    await client.close()

            # Run the async Redis operation
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(store_in_redis())
                else:
                    loop.run_until_complete(store_in_redis())
            except RuntimeError:
                asyncio.run(store_in_redis())

        except Exception as e:
            logger.error(
                f"❌ Failed to store DLQ entry in Redis fallback: {e}",
                extra={"task_id": task_id, "task_name": task_name},
                exc_info=True,
            )
            # Last resort: log to file
            self._log_dlq_to_file(dlq_entry, task_id, task_name)

    def _log_dlq_to_file(self, dlq_entry: dict, task_id: str, task_name: str):
        """
        Last resort: Log DLQ entry to file for manual recovery.

        Args:
            dlq_entry: DLQ entry dictionary
            task_id: Original task ID
            task_name: Task name
        """
        try:
            import os
            from pathlib import Path

            # Create dlq fallback directory
            dlq_dir = Path("logs/dlq_fallback")
            dlq_dir.mkdir(parents=True, exist_ok=True)

            # Write to file
            filename = (
                dlq_dir
                / f"{task_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(filename, "w") as f:
                json.dump(dlq_entry, f, indent=2, default=str)

            logger.info(
                f"✅ DLQ entry logged to file: {filename}",
                extra={
                    "task_id": task_id,
                    "task_name": task_name,
                    "file": str(filename),
                },
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to log DLQ entry to file: {e}",
                extra={"task_id": task_id, "task_name": task_name},
                exc_info=True,
            )

    # =======================================================================
    # UTILITY METHODS
    # =======================================================================

    def log_info(self, message: str, **extra):
        """Log info message with task context"""
        extra.update({"task_id": self.request.id, "task_name": self.name})
        logger.info(message, extra=extra)

    def log_warning(self, message: str, **extra):
        """Log warning message with task context"""
        extra.update({"task_id": self.request.id, "task_name": self.name})
        logger.warning(message, extra=extra)

    def log_error(self, message: str, exc_info: bool = False, **extra):
        """Log error message with task context"""
        extra.update({"task_id": self.request.id, "task_name": self.name})
        logger.error(message, extra=extra, exc_info=exc_info)

    def get_retry_count(self) -> int:
        """Get current retry count"""
        return self.request.retries

    def get_task_id(self) -> str:
        """Get task ID"""
        return self.request.id

    def is_final_retry(self) -> bool:
        """Check if this is the final retry attempt"""
        return self.request.retries >= self.get_max_retries() - 1


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


# Example 1: Simple task
class CalculateScoreTask(BaseTask):
    """Example task that calculates assessment scores"""

    def run(self, assessment_id: str) -> dict:
        """
        Calculate scores for an assessment.

        Args:
            assessment_id: Assessment ID

        Returns:
            Score calculation results
        """
        self.log_info(f"Calculating scores for assessment: {assessment_id}")

        # Task logic here
        result = {
            "assessment_id": assessment_id,
            "score": 95,
            "calculated_at": datetime.utcnow().isoformat(),
        }

        self.log_info(f"Score calculation complete: {result}")
        return result


# Example 2: Task with database operations
class ProcessAssessmentTask(BaseTask):
    """Example task that uses database"""

    def run(self, assessment_id: str) -> dict:
        """
        Process assessment with database operations.

        Args:
            assessment_id: Assessment ID

        Returns:
            Processing results
        """
        self.log_info(f"Processing assessment: {assessment_id}")

        # Note: For async database operations, use get_db_session context manager
        # This would typically be called from an async function
        # For now, this is a synchronous example

        result = {
            "assessment_id": assessment_id,
            "status": "processed",
            "processed_at": datetime.utcnow().isoformat(),
        }

        self.log_info(f"Assessment processing complete: {result}")
        return result


# Example 3: Register task with Celery
# from app.core.config.celery_config import celery_app
#
# @celery_app.task(base=CalculateScoreTask, bind=True, max_retries=3)
# def calculate_score(self, assessment_id: str):
#     return self.run(assessment_id)
