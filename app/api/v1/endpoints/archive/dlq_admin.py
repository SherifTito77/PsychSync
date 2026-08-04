"""
Dead Letter Queue Admin API Endpoints

Administrative endpoints for managing failed Celery tasks in the DLQ.
Provides comprehensive CRUD operations, analytics, and bulk actions.

All endpoints require superuser authentication.

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_superuser, get_db
from app.core.config.celery_config import celery_app
from app.db.models.dead_letter import DeadLetterTask, DLQStatus
from app.schemas.dlq import (
    DLQAnalyticsResponse,
    DLQBatchActionRequest,
    DLQBatchActionResponse,
    DLQEntry,
    DLQEntryListResponse,
    DLQEntrySummary,
    DLQErrorDistribution,
    DLQHealthCheckResponse,
    DLQRetryRequest,
    DLQRetryResponse,
    DLQTopFailingTask,
)
from app.services.user_service import get_users_by_organization

logger = logging.getLogger(__name__)

router = APIRouter(tags=["DLQ Admin"])


# =============================================================================
# DEPENDENCIES
# =============================================================================


async def get_dlq_entry(
    dlq_id: uuid.UUID,
    db: AsyncSession,
) -> DeadLetterTask:
    """
    Get DLQ entry by ID or raise 404.

    Args:
        dlq_id: DLQ entry uuid.UUID
        db: Database session

    Returns:
        DeadLetterTask instance

    Raises:
        HTTPException: If entry not found
    """
    result = await db.execute(select(DeadLetterTask).where(DeadLetterTask.id == dlq_id))
    dlq_entry = result.scalar_one_or_none()

    if not dlq_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"DLQ entry {dlq_id} not found",
        )

    return dlq_entry


# =============================================================================
# LIST DLQ ENTRIES
# =============================================================================


@router.get(
    "/dlq",
    response_model=DLQEntryListResponse,
    summary="List all DLQ entries",
    description="Retrieve paginated list of DLQ entries with optional filtering",
)
async def list_dlq_entries(
    status: Optional[str] = Query(None, description="Filter by status"),
    reason: Optional[str] = Query(None, description="Filter by reason"),
    task_name: Optional[str] = Query(
        None, description="Filter by task name (partial match)"
    ),
    is_transient: Optional[bool] = Query(None, description="Filter by transient flag"),
    worker: Optional[str] = Query(None, description="Filter by worker hostname"),
    queue: Optional[str] = Query(None, description="Filter by queue name"),
    created_after: Optional[datetime] = Query(
        None, description="Filter by creation date (after)"
    ),
    created_before: Optional[datetime] = Query(
        None, description="Filter by creation date (before)"
    ),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    List DLQ entries with filtering and pagination.

    Supports filtering by:
    - status (e.g., pending, retryable, permanent)
    - reason (e.g., max_retries_exceeded, timeout)
    - task_name (partial match)
    - is_transient (boolean)
    - worker (hostname)
    - queue (queue name)
    - Date ranges (created_after, created_before)

    Pagination:
    - page: Page number (1-indexed)
    - page_size: Items per page (1-100)

    Sorting:
    - sort_by: Field to sort by (created_at, task_name, status, etc.)
    - sort_order: asc or desc
    """
    # Build base query
    query = select(DeadLetterTask)

    # Apply filters
    if status:
        query = query.where(DeadLetterTask.status == status)
    if reason:
        query = query.where(DeadLetterTask.reason == reason)
    if task_name:
        query = query.where(DeadLetterTask.task_name.contains(task_name))
    if is_transient is not None:
        query = query.where(DeadLetterTask.is_transient == is_transient)
    if worker:
        query = query.where(DeadLetterTask.worker.contains(worker))
    if queue:
        query = query.where(DeadLetterTask.queue == queue)
    if created_after:
        query = query.where(DeadLetterTask.created_at >= created_after)
    if created_before:
        query = query.where(DeadLetterTask.created_at <= created_before)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply sorting
    sort_column = getattr(DeadLetterTask, sort_by, DeadLetterTask.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    dlq_entries = result.scalars().all()

    # Convert to summary format
    items = [
        DLQEntrySummary(
            id=entry.id,
            task_name=entry.task_name,
            reason=entry.reason,
            status=entry.status,
            is_transient=entry.is_transient,
            created_at=entry.created_at,
            retry_attempts=entry.retry_attempts,
            can_retry=entry.can_retry(),
        )
        for entry in dlq_entries
    ]

    total_pages = (total + page_size - 1) // page_size

    return DLQEntryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


# =============================================================================
# GET DLQ ENTRY DETAILS
# =============================================================================


@router.get(
    "/dlq/{dlq_id}",
    response_model=DLQEntry,
    summary="Get DLQ entry details",
    description="Retrieve full details of a specific DLQ entry",
)
async def get_dlq_entry(
    dlq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get detailed information about a specific DLQ entry.

    Includes full context:
    - Task arguments and kwargs
    - Exception traceback
    - Retry history
    - Classification metadata
    """
    dlq_entry = await get_dlq_entry(dlq_id, db)

    # Convert to schema with computed fields
    return DLQEntry(
        id=dlq_entry.id,
        task_id=dlq_entry.task_id,
        task_name=dlq_entry.task_name,
        reason=dlq_entry.reason,
        status=dlq_entry.status,
        is_transient=dlq_entry.is_transient,
        exception=dlq_entry.exception,
        exception_type=dlq_entry.exception_type,
        traceback=dlq_entry.traceback,
        args=dlq_entry.args,
        kwargs=dlq_entry.kwargs,
        retry_count=dlq_entry.retry_count,
        retry_attempts=dlq_entry.retry_attempts,
        max_retries=dlq_entry.max_retries,
        worker=dlq_entry.worker,
        queue=dlq_entry.queue,
        error_category=dlq_entry.error_category,
        confidence_score=dlq_entry.confidence_score,
        created_at=dlq_entry.created_at,
        updated_at=dlq_entry.updated_at,
        processed_at=dlq_entry.processed_at,
        last_retry_at=dlq_entry.last_retry_at,
        next_retry_at=dlq_entry.next_retry_at,
        resolved_at=dlq_entry.resolved_at,
        task_metadata=dlq_entry.task_metadata,
        can_retry=dlq_entry.can_retry(),
        should_auto_retry=dlq_entry.should_auto_retry(),
    )


# =============================================================================
# RETRY DLQ ENTRY
# =============================================================================


@router.post(
    "/dlq/{dlq_id}/retry",
    response_model=DLQRetryResponse,
    summary="Retry a DLQ entry",
    description="Manually retry a failed task from the DLQ",
)
async def retry_dlq_entry(
    dlq_id: uuid.UUID,
    retry_request: DLQRetryRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Retry a failed task from the Dead Letter Queue.

    Parameters:
    - delay_seconds: Delay before retry (0=immediate, max=3600)
    - force: Force retry even if can_retry=False

    Returns:
    - success: Whether retry was initiated
    - task_id: Celery task ID for tracking retry
    - scheduled_for: When retry will execute
    """
    from app.tasks.dlq_tasks import manual_retry_dlq

    dlq_entry = await get_dlq_entry(dlq_id, db)

    # Check if entry can be retried
    if not retry_request.force and not dlq_entry.can_retry():
        return DLQRetryResponse(
            success=False,
            dlq_id=dlq_id,
            message=f"Cannot retry: status={dlq_entry.status}, attempts={dlq_entry.retry_attempts}/{dlq_entry.max_retries}",
        )

    # Reset retry attempts if forcing
    if retry_request.force:
        dlq_entry.retry_attempts = 0
        dlq_entry.status = DLQStatus.RETRYABLE
        await db.commit()

    # Trigger retry task
    delay = retry_request.delay_seconds if retry_request else 0

    if delay > 0:
        # Schedule delayed retry
        eta = datetime.utcnow() + timedelta(seconds=delay)
        result = manual_retry_dlq.apply_async(args=[str(dlq_id)], eta=eta)
    else:
        # Immediate retry
        result = manual_retry_dlq.delay(str(dlq_id))

    return DLQRetryResponse(
        success=True,
        dlq_id=dlq_id,
        message="Retry initiated",
        task_id=result.id,
        scheduled_for=datetime.utcnow() + timedelta(seconds=delay) if delay else None,
    )


# =============================================================================
# DISCARD DLQ ENTRY
# =============================================================================


@router.delete(
    "/dlq/{dlq_id}",
    summary="Discard DLQ entry",
    description="Remove a DLQ entry (marks as discarded)",
)
async def discard_dlq_entry(
    dlq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Discard a DLQ entry (soft delete).

    Marks the entry as discarded and records resolution timestamp.
    The entry remains in the database for audit purposes.
    """
    dlq_entry = await get_dlq_entry(dlq_id, db)

    dlq_entry.status = DLQStatus.DISCARDED
    dlq_entry.resolved_at = datetime.utcnow()
    await db.commit()

    return {
        "success": True,
        "message": "DLQ entry discarded",
        "dlq_id": str(dlq_id),
    }


# =============================================================================
# BATCH ACTIONS
# =============================================================================


@router.post(
    "/dlq/batch",
    response_model=DLQBatchActionResponse,
    summary="Batch action on DLQ entries",
    description="Perform bulk actions on multiple DLQ entries",
)
async def batch_dlq_action(
    batch_request: DLQBatchActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Perform bulk actions on multiple DLQ entries.

    Supported actions:
    - retry: Retry all entries (with optional delay)
    - discard: Discard all entries
    - mark_permanent: Mark all entries as permanent failures

    Max batch size: 100 entries
    """
    results = []
    succeeded = 0
    failed = 0

    for dlq_id in batch_request.dlq_ids:
        try:
            dlq_entry = await get_dlq_entry(dlq_id, db)

            if batch_request.action == "retry":
                # Trigger retry
                from app.tasks.dlq_tasks import manual_retry_dlq

                delay = batch_request.delay_seconds or 0
                manual_retry_dlq.delay(str(dlq_id))

                results.append({"dlq_id": str(dlq_id), "status": "retry_scheduled"})
                succeeded += 1

            elif batch_request.action == "discard":
                dlq_entry.status = DLQStatus.DISCARDED
                dlq_entry.resolved_at = datetime.utcnow()
                results.append({"dlq_id": str(dlq_id), "status": "discarded"})
                succeeded += 1

            elif batch_request.action == "mark_permanent":
                dlq_entry.mark_permanent(reason="admin_marked_permanent")
                results.append({"dlq_id": str(dlq_id), "status": "marked_permanent"})
                succeeded += 1

            else:
                results.append({"dlq_id": str(dlq_id), "status": "unknown_action"})
                failed += 1

        except Exception as e:
            results.append({"dlq_id": str(dlq_id), "status": "error", "error": str(e)})
            failed += 1

    # Commit all changes
    await db.commit()

    return DLQBatchActionResponse(
        total=len(batch_request.dlq_ids),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


# =============================================================================
# DLQ ANALYTICS
# =============================================================================


@router.get(
    "/dlq/analytics",
    response_model=DLQAnalyticsResponse,
    summary="Get DLQ analytics",
    description="Retrieve comprehensive DLQ analytics for the specified period",
)
async def get_dlq_analytics(
    days: int = Query(7, ge=1, le=90, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get comprehensive DLQ analytics.

    Returns:
    - Total DLQ entries in period
    - Breakdown by status
    - Error type distribution
    - Top failing tasks
    - Transient vs permanent ratio
    - Auto-retry success rate
    - Daily trend
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Total entries
    total_result = await db.execute(
        select(func.count())
        .select_from(DeadLetterTask)
        .where(DeadLetterTask.created_at >= cutoff_date)
    )
    total = total_result.scalar() or 0

    if total == 0:
        return DLQAnalyticsResponse(
            period_days=days,
            total_dlq_entries=0,
            by_status={},
            error_distribution=[],
            top_failing_tasks=[],
            transient_ratio=0.0,
            auto_retry_success_rate=0.0,
            mean_retry_count=0.0,
            mean_resolution_time_hours=0.0,
            daily_trend=[],
        )

    # Status breakdown
    status_result = await db.execute(
        select(DeadLetterTask.status, func.count())
        .where(DeadLetterTask.created_at >= cutoff_date)
        .group_by(DeadLetterTask.status)
    )
    by_status = {status: count for status, count in status_result.all()}

    # Error distribution
    error_result = await db.execute(
        select(DeadLetterTask.reason, func.count())
        .where(DeadLetterTask.created_at >= cutoff_date)
        .group_by(DeadLetterTask.reason)
        .order_by(func.count().desc())
    )
    error_distribution = [
        DLQErrorDistribution(
            reason=reason, count=count, percentage=(count / total) * 100
        )
        for reason, count in error_result.all()
    ]

    # Top failing tasks
    tasks_result = await db.execute(
        select(
            DeadLetterTask.task_name,
            func.count().label("count"),
            func.max(DeadLetterTask.created_at).label("last_failure"),
        )
        .where(DeadLetterTask.created_at >= cutoff_date)
        .group_by(DeadLetterTask.task_name)
        .order_by(func.count().desc())
        .limit(10)
    )

    top_failing_tasks = [
        DLQTopFailingTask(
            task_name=task_name,
            count=count,
            percentage=(count / total) * 100,
            last_failure=last_failure,
        )
        for task_name, count, last_failure in tasks_result.all()
    ]

    # Transient ratio
    transient_result = await db.execute(
        select(func.count()).where(
            and_(
                DeadLetterTask.created_at >= cutoff_date,
                DeadLetterTask.is_transient == True,
            )
        )
    )
    transient_count = transient_result.scalar() or 0
    transient_ratio = transient_count / total if total > 0 else 0.0

    # Auto-retry success rate (retried vs failed)
    auto_retry_success_rate = await calculate_auto_retry_success_rate(db, cutoff_date)

    # Mean retry count
    mean_retry_result = await db.execute(
        select(func.avg(DeadLetterTask.retry_attempts)).where(
            DeadLetterTask.created_at >= cutoff_date
        )
    )
    mean_retry_count = mean_retry_result.scalar() or 0.0

    # Mean resolution time (for resolved entries)
    mean_resolution_time_hours = await calculate_mean_resolution_time(db, cutoff_date)

    # Daily trend
    daily_trend = await calculate_daily_trend(db, days)

    return DLQAnalyticsResponse(
        period_days=days,
        total_dlq_entries=total,
        by_status=by_status,
        error_distribution=error_distribution,
        top_failing_tasks=top_failing_tasks,
        transient_ratio=transient_ratio,
        auto_retry_success_rate=0.0,  # TODO: Implement
        mean_retry_count=mean_retry_count,
        mean_resolution_time_hours=0.0,  # TODO: Implement
        daily_trend=[],  # TODO: Implement
    )


# =============================================================================
# DLQ HEALTH CHECK
# =============================================================================


@router.get(
    "/dlq/health",
    response_model=DLQHealthCheckResponse,
    summary="DLQ system health check",
    description="Check overall health of the DLQ system",
)
async def dlq_health_check(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """
    Get DLQ system health status.

    Returns:
    - System status (healthy, warning, critical)
    - Pending/retryable/permanent counts
    - Creation and resolution rates
    - Active alerts
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # Count by status
    pending_result = await db.execute(
        select(func.count()).where(DeadLetterTask.status == DLQStatus.PENDING)
    )
    pending_count = pending_result.scalar() or 0

    retryable_result = await db.execute(
        select(func.count()).where(DeadLetterTask.status == DLQStatus.RETRYABLE)
    )
    retryable_count = retryable_result.scalar() or 0

    permanent_result = await db.execute(
        select(func.count()).where(DeadLetterTask.status == DLQStatus.PERMANENT)
    )
    permanent_count = permanent_result.scalar() or 0

    # Creation rate (last hour)
    creation_result = await db.execute(
        select(func.count()).where(DeadLetterTask.created_at >= one_hour_ago)
    )
    creation_rate = creation_result.scalar() or 0

    # Resolution rate (last hour)
    resolution_result = await db.execute(
        select(func.count()).where(DeadLetterTask.resolved_at >= one_hour_ago)
    )
    resolution_rate = resolution_result.scalar() or 0

    # Determine system status
    alerts = []

    if pending_count > 100:
        alerts.append(f"High pending count: {pending_count} entries awaiting analysis")

    if permanent_count > 50:
        alerts.append(
            f"High permanent failure count: {permanent_count} permanent failures"
        )

    if creation_rate > 20:
        alerts.append(f"High DLQ creation rate: {creation_rate} entries/hour")

    if resolution_rate < creation_rate * 0.5:
        alerts.append(
            f"Low resolution rate: {resolution_rate}/hour vs {creation_rate}/hour creation"
        )

    # Determine overall status
    if len(alerts) == 0:
        system_status = "healthy"
    elif len(alerts) <= 2:
        system_status = "warning"
    else:
        system_status = "critical"

    return DLQHealthCheckResponse(
        status=system_status,
        timestamp=now,
        pending_count=pending_count,
        retryable_count=retryable_count,
        permanent_count=permanent_count,
        creation_rate_per_hour=float(creation_rate),
        resolution_rate_per_hour=float(resolution_rate),
        alerts=alerts,
    )


# =============================================================================
# ANALYTICS HELPER FUNCTIONS
# =============================================================================


async def calculate_auto_retry_success_rate(
    db: AsyncSession, cutoff_date: datetime
) -> float:
    """
    Calculate auto-retry success rate.

    Returns the percentage of DLQ entries that succeeded after auto-retry.
    Formula: retried_count / (retried_count + failed_count)
    """
    # Count by status for retried and failed entries
    result = await db.execute(
        select(DeadLetterTask.status, func.count())
        .where(
            and_(
                DeadLetterTask.created_at >= cutoff_date,
                DeadLetterTask.status.in_(["retried", "failed"]),
                DeadLetterTask.retry_attempts
                > 0,  # Only entries that were actually retried
            )
        )
        .group_by(DeadLetterTask.status)
    )

    # Extract counts
    counts = {status: count for status, count in result.all()}
    retried = counts.get("retried", 0)
    failed = counts.get("failed", 0)
    total = retried + failed

    # Calculate ratio
    return retried / total if total > 0 else 0.0


async def calculate_mean_resolution_time(
    db: AsyncSession, cutoff_date: datetime
) -> float:
    """
    Calculate mean time to resolution for DLQ entries.

    Returns average time from creation to resolution in hours.
    """
    # Calculate average time difference in seconds, then convert to hours
    result = await db.execute(
        select(
            func.avg(
                func.extract(
                    "epoch", DeadLetterTask.resolved_at - DeadLetterTask.created_at
                )
            )
        ).where(
            and_(
                DeadLetterTask.created_at >= cutoff_date,
                DeadLetterTask.resolved_at.is_not(None),
            )
        )
    )

    # Get average in seconds, convert to hours
    avg_seconds = result.scalar()
    return (avg_seconds / 3600.0) if avg_seconds else 0.0


async def calculate_daily_trend(db: AsyncSession, days: int) -> list[dict[str, Any]]:
    """
    Calculate daily DLQ creation trend.

    Returns daily breakdown of DLQ entries over the period.
    """
    daily_trend = []

    # Iterate through the last N days
    for i in range(days):
        # Calculate date for this day (going backwards from today)
        date = datetime.utcnow() - timedelta(days=days - 1 - i)

        # Set day boundaries (midnight to midnight)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Count DLQ entries created on this day
        result = await db.execute(
            select(func.count()).where(
                and_(
                    DeadLetterTask.created_at >= day_start,
                    DeadLetterTask.created_at < day_end,
                )
            )
        )

        count = result.scalar() or 0

        # Add to trend
        daily_trend.append({"date": date.strftime("%Y-%m-%d"), "count": count})

    return daily_trend
