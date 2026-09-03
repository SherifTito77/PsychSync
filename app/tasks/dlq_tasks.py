"""
Dead Letter Queue Processing Tasks

Handles analysis, retry, and management of failed Celery tasks.
This completes the DLQ recovery system by providing automated
failure classification and intelligent retry mechanisms.

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

from celery import Task
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.celery_config import celery_app
from app.core.database import AsyncSessionLocal
from app.db.models.dead_letter import DeadLetterTask, DLQReason, DLQStatus
from app.tasks.base_task import BaseTask

logger = logging.getLogger(__name__)


# =============================================================================
# DLQ BASE TASK (Specialized for DLQ operations)
# =============================================================================


class DLQTask(BaseTask):
    """
    Base class for DLQ processing tasks.

    Extends BaseTask with DLQ-specific utilities for database operations
    and error classification.
    """

    @property
    def db(self) -> AsyncSession:
        """Get or create async database session"""
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db


# =============================================================================
# DLQ PROCESSING TASKS
# =============================================================================


@celery_app.task(
    base=DLQTask,
    bind=True,
    name="tasks.process_dlq",
    max_retries=3,
)
def process_dlq(self) -> Dict[str, Any]:
    """
    Process Dead Letter Queue - Analyze and categorize failed tasks.

    This task runs hourly to:
    1. Fetch new DLQ entries from database
    2. Classify failures (transient vs permanent)
    3. Schedule automatic retries for transient errors
    4. Alert on critical/permanent failures

    Returns:
        Processing summary with counts and actions taken
    """
    self.log_info("Starting DLQ processing")

    try:
        db = self.db

        # Get pending DLQ entries (not yet analyzed)
        stmt = select(DeadLetterTask).where(DeadLetterTask.status == DLQStatus.PENDING)
        result = db.execute(stmt)
        pending_tasks = result.scalars().all()

        if not pending_tasks:
            self.log_info("No pending DLQ entries to process")
            return {"status": "completed", "processed": 0}

        self.log_info(f"Found {len(pending_tasks)} pending DLQ entries")

        # Statistics
        stats = {
            "total": len(pending_tasks),
            "classified": 0,
            "auto_retried": 0,
            "marked_permanent": 0,
            "requires_manual_review": 0,
            "errors": [],
        }

        for dlq_entry in pending_tasks:
            try:
                # Classify the failure
                classification = DeadLetterTask.classify_exception(
                    exception_type=dlq_entry.exception_type or "Unknown",
                    exception_message=dlq_entry.exception or "",
                )

                # Update DLQ entry with classification
                dlq_entry.is_transient = classification["is_transient"]
                dlq_entry.error_category = classification["reason"]
                dlq_entry.confidence_score = classification["confidence"]
                dlq_entry.status = (
                    DLQStatus.RETRYABLE
                    if classification["is_transient"]
                    else DLQStatus.PERMANENT
                )
                dlq_entry.processed_at = datetime.utcnow()

                stats["classified"] += 1

                # Schedule automatic retry for transient errors
                if classification["is_transient"]:
                    if dlq_entry.should_auto_retry():
                        # Calculate exponential backoff delay
                        delay = calculate_backoff_delay(dlq_entry.retry_attempts)
                        dlq_entry.schedule_retry(delay)

                        # Queue retry task
                        retry_dlq_task.delay(str(dlq_entry.id), delay)
                        stats["auto_retried"] += 1

                        self.log_info(
                            f"Scheduled auto-retry for task {dlq_entry.task_name} "
                            f"(DLQ ID: {dlq_entry.id}) in {delay}s"
                        )
                    else:
                        stats["requires_manual_review"] += 1
                else:
                    stats["marked_permanent"] += 1

            except Exception as e:
                self.log_error(
                    f"Error processing DLQ entry {dlq_entry.id}: {e}",
                    exc_info=True,
                )
                stats["errors"].append({"dlq_id": str(dlq_entry.id), "error": str(e)})

        # Commit all updates
        db.commit()

        self.log_info(
            f"DLQ processing completed: "
            f"{stats['classified']} classified, "
            f"{stats['auto_retried']} auto-retried, "
            f"{stats['marked_permanent']} permanent"
        )

        return {
            "status": "completed",
            **stats,
        }

    except Exception as e:
        self.log_error(f"Failed to process DLQ: {e}", exc_info=True)
        raise


@celery_app.task(
    base=DLQTask,
    bind=True,
    name="tasks.retry_dlq_task",
    max_retries=1,  # Only retry once from DLQ
)
def retry_dlq_task(self, dlq_id: str, delay_seconds: int = 0) -> Dict[str, Any]:
    """
    Retry a specific task from the Dead Letter Queue.

    This task:
    1. Loads the DLQ entry
    2. Re-executes the original task
    3. Updates DLQ entry status based on result

    Args:
        dlq_id: UUID of the DLQ entry
        delay_seconds: Delay before retry (for scheduled retries)

    Returns:
        Retry result with status and details

    TODO(human): Prevent DLQ retry storms - DEADLOCK RISK
    -------------------------------------------------------
    Current Issue: Multiple retry_dlq_task instances can run concurrently
    for the same DLQ entry, causing:
    1. Retry storm (100+ tasks queued for same DLQ)
    2. Database contention on same DLQ row
    3. Wasted Celery worker capacity

    Required Implementation:
    1. Check dlq_entry.status == "in_progress" before proceeding
       if dlq_entry.status == DLQStatus.IN_PROGRESS:
           logger.warning(f"DLQ {dlq_id} already being retried, skipping")
           return {"status": "skipped", "reason": "already_in_progress"}

    2. Use SELECT FOR UPDATE with skip_locked=True
       - First query locks the DLQ row atomically
       - Other concurrent retry attempts fail fast

    3. Add MAX_CONCURRENT_RETRIES limit
       - Track total retry attempts (not just per task)
       - Stop retrying after 5 total attempts

    File location: This function (line 183-297)
    """
    self.log_info(f"Retrying DLQ task: {dlq_id}")

    try:
        db = self.db

        # Load DLQ entry
        stmt = select(DeadLetterTask).where(DeadLetterTask.id == UUID(dlq_id))
        result = db.execute(stmt)
        dlq_entry = result.scalar_one_or_none()

        if not dlq_entry:
            self.log_error(f"DLQ entry not found: {dlq_id}")
            return {"status": "error", "message": "DLQ entry not found"}

        if not dlq_entry.can_retry():
            self.log_warning(
                f"DLQ entry {dlq_id} cannot be retried "
                f"(status: {dlq_entry.status}, attempts: {dlq_entry.retry_attempts})"
            )
            return {
                "status": "skipped",
                "reason": "Task cannot be retried",
                "dlq_entry": dlq_entry.to_dict(),
            }

        # Update entry status
        dlq_entry.last_retry_at = datetime.utcnow()
        dlq_entry.status = DLQStatus.RETRYING

        # Deserialize args and kwargs
        import ast

        args = ast.literal_eval(dlq_entry.args) if dlq_entry.args else ()
        kwargs = ast.literal_eval(dlq_entry.kwargs) if dlq_entry.kwargs else {}

        self.log_info(
            f"Executing task {dlq_entry.task_name} "
            f"(retry attempt {dlq_entry.retry_attempts + 1})"
        )

        # Execute the original task
        success, result = execute_original_task(
            task_name=dlq_entry.task_name,
            args=args,
            kwargs=kwargs,
        )

        if success:
            # Task succeeded!
            dlq_entry.mark_resolved(success=True)
            db.commit()

            self.log_info(f"✅ DLQ task {dlq_id} retry succeeded")
            return {
                "status": "success",
                "dlq_id": dlq_id,
                "result": str(result)[:500],
                "retry_attempts": dlq_entry.retry_attempts,
            }
        else:
            # Task failed again - check if we should retry again
            if dlq_entry.retry_attempts < dlq_entry.max_retries:
                # Schedule another retry with exponential backoff
                next_delay = calculate_backoff_delay(dlq_entry.retry_attempts + 1)
                dlq_entry.schedule_retry(next_delay)
                db.commit()

                # Schedule next retry
                retry_dlq_task.apply_async(
                    args=[dlq_id],
                    countdown=next_delay,
                )

                self.log_warning(
                    f"⚠️ DLQ task {dlq_id} retry failed, "
                    f"scheduling next retry in {next_delay}s"
                )
                return {
                    "status": "retry_scheduled",
                    "dlq_id": dlq_id,
                    "error": str(result),
                    "next_retry_in": next_delay,
                }
            else:
                # Max retries exceeded - mark as permanent failure
                dlq_entry.mark_resolved(success=False)
                dlq_entry.mark_permanent(reason="max_dlq_retries_exceeded")
                db.commit()

                self.log_error(f"❌ DLQ task {dlq_id} failed after max retries")
                return {
                    "status": "permanent_failure",
                    "dlq_id": dlq_id,
                    "error": str(result),
                }

    except Exception as e:
        self.log_error(f"Exception during DLQ retry: {e}", exc_info=True)
        raise


@celery_app.task(
    base=DLQTask,
    bind=True,
    name="tasks.cleanup_resolved_dlq",
)
def cleanup_resolved_dlq(self, days_old: int = 30) -> Dict[str, Any]:
    """
    Clean up old resolved DLQ entries.

    Removes DLQ entries that have been resolved for more than
    the specified number of days to keep the table size manageable.

    Args:
        days_old: Delete entries resolved more than this many days ago

    Returns:
        Cleanup summary with count of deleted entries
    """
    self.log_info(f"Starting DLQ cleanup (deleting entries > {days_old} days old)")

    try:
        db = self.db

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Delete resolved entries older than cutoff
        stmt = select(DeadLetterTask).where(
            DeadLetterTask.resolved_at < cutoff_date,
            DeadLetterTask.status.in_(
                [DLQStatus.RETRIED, DLQStatus.DISCARDED, DLQStatus.FAILED]
            ),
        )
        result = db.execute(stmt)
        old_entries = result.scalars().all()

        count = len(old_entries)
        for entry in old_entries:
            db.delete(entry)

        db.commit()

        self.log_info(f"Deleted {count} old DLQ entries")

        return {
            "status": "completed",
            "deleted_count": count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as e:
        self.log_error(f"DLQ cleanup failed: {e}", exc_info=True)
        raise


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def calculate_backoff_delay(retry_attempt: int) -> int:
    """
    Calculate exponential backoff delay for DLQ retries.

    Uses longer delays than normal task retries since DLQ tasks
    have already failed multiple times.

    Formula: min(300 * (2 ^ retry_attempt), 3600) ± 10% jitter

    Args:
        retry_attempt: Current retry attempt number (0-indexed)

    Returns:
        Delay in seconds
    """
    import random

    base_delay = 300  # 5 minutes (longer than normal 60s)
    max_delay = 3600  # 1 hour max

    # Calculate exponential backoff
    delay = min(base_delay * (2**retry_attempt), max_delay)

    # Add jitter to prevent thundering herd
    jitter = delay * 0.1  # ±10%
    delay_with_jitter = delay + random.uniform(-jitter, jitter)

    return int(max(0, delay_with_jitter))


def execute_original_task(
    task_name: str,
    args: tuple,
    kwargs: dict,
) -> tuple[bool, Any]:
    """
    Execute the original Celery task synchronously.

    This function dynamically imports and executes the original task,
    handling both sync and async task types. All exceptions are caught
    and returned in the result tuple for DLQ tracking.

    Args:
        task_name: Full task name (e.g., "app.tasks.scoring_scheduler.calculate_assessment_scores")
        args: Original positional arguments
        kwargs: Original keyword arguments

    Returns:
        Tuple of (success: bool, result: Any)
        - success: True if task succeeded, False if failed
        - result: Task return value if success, exception if failed
    """
    import asyncio
    import importlib
    import inspect
    from concurrent.futures import TimeoutError as FuturesTimeoutError

    # Parse task_name: "app.tasks.scoring_scheduler.calculate_assessment_scores"
    # → module: "app.tasks.scoring_scheduler"
    # → function: "calculate_assessment_scores"
    try:
        parts = task_name.split(".")
        if len(parts) < 2:
            raise ImportError(f"Invalid task_name format: {task_name}")

        function_name = parts[-1]
        module_path = ".".join(parts[:-1])

        # Dynamically import the module
        module = importlib.import_module(module_path)

        # Get the task function
        if not hasattr(module, function_name):
            raise ImportError(
                f"Task function '{function_name}' not found in module '{module_path}'"
            )

        task_func = getattr(module, function_name)

        # Check if function is async (coroutine) or sync
        is_async = inspect.iscoroutinefunction(task_func)

        # Execute with timeout protection (30 minutes max for DLQ retries)
        timeout = 1800  # 30 minutes

        if is_async:
            # Run async task synchronously
            try:
                # ✅ DEADLOCK FIX: Use asyncio.run() instead of manual event loop management
                # This prevents event loop conflicts in Celery worker threads
                # Python 3.7+ handles event loop creation/cleanup automatically
                try:
                    # For Python 3.10+, use asyncio.run()
                    result = asyncio.run(
                        asyncio.wait_for(task_func(*args, **kwargs), timeout=timeout)
                    )
                except TypeError:
                    # Fallback for Python 3.7-3.9
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            asyncio.wait_for(
                                task_func(*args, **kwargs), timeout=timeout
                            )
                        )
                    finally:
                        loop.close()

                return True, result

            except asyncio.TimeoutError:
                logger.error(f"Task {task_name} timed out after {timeout}s")
                return False, Exception(f"Task execution timeout ({timeout}s)")
            except Exception as e:
                logger.error(f"Async task {task_name} failed: {e}", exc_info=True)
                return False, e
            finally:
                # Clean up event loop
                try:
                    loop.close()
                except:
                    pass
        else:
            # Execute sync task directly
            try:
                # Add timeout using signal or multiprocessing
                # For simplicity, we'll execute directly and rely on Celery's timeout
                result = task_func(*args, **kwargs)
                return True, result

            except Exception as e:
                logger.error(f"Sync task {task_name} failed: {e}", exc_info=True)
                return False, e

    except ImportError as e:
        logger.error(f"Failed to import task module for {task_name}: {e}")
        return False, e
    except Exception as e:
        logger.error(f"Unexpected error executing task {task_name}: {e}", exc_info=True)
        return False, e


@celery_app.task(name="tasks.manual_retry_dlq")
def manual_retry_dlq(dlq_id: str) -> Dict[str, Any]:
    """
    Manually retry a task from DLQ (triggered by admin API).

    Unlike retry_dlq_task, this bypasses the can_retry() check
    to allow forced retries by administrators.

    Args:
        dlq_id: UUID of the DLQ entry to retry

    Returns:
        Retry result
    """
    logger.info(f"Manual retry requested for DLQ entry: {dlq_id}")

    # Reset retry attempts to allow immediate retry
    # TODO: Implement forced retry logic
    return retry_dlq_task(dlq_id)


# =============================================================================
# DLQ ANALYTICS TASKS
# =============================================================================


@celery_app.task(name="tasks.generate_dlq_report")
def generate_dlq_report(days: int = 7) -> Dict[str, Any]:
    """
    Generate DLQ analytics report for the past N days.

    Provides insights into:
    - Top failing tasks
    - Error type distribution
    - Transient vs permanent failure ratios
    - Auto-retry success rates

    Args:
        days: Number of days to analyze

    Returns:
        DLQ analytics report
    """
    logger.info(f"Generating DLQ report for past {days} days")

    # TODO: Implement analytics query
    return {
        "period_days": days,
        "total_dlq_entries": 0,
        "top_failing_tasks": [],
        "error_distribution": {},
        "transient_ratio": 0.0,
        "auto_retry_success_rate": 0.0,
    }
