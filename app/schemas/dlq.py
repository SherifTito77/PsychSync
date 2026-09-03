"""
Dead Letter Queue Schemas

Pydantic schemas for DLQ API requests and responses.

Author: Infrastructure Team
Version: 1.0.0
Date: February 9, 2026
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# =============================================================================
# DLQ Entry Schemas
# =============================================================================


class DLQEntryBase(BaseModel):
    """Base DLQ entry schema with common fields"""

    task_id: str = Field(..., description="Original Celery task ID")
    task_name: str = Field(..., description="Full task module path")
    reason: str = Field(
        ..., description="DLQ reason (e.g., max_retries_exceeded, timeout)"
    )
    status: str = Field(
        ..., description="DLQ status (e.g., pending, retryable, permanent)"
    )
    is_transient: bool = Field(
        default=True, description="Whether error is transient/retryable"
    )
    exception: Optional[str] = Field(None, description="Exception message")
    exception_type: Optional[str] = Field(None, description="Exception class name")
    worker: Optional[str] = Field(None, description="Worker hostname")
    queue: Optional[str] = Field(None, description="Queue task was routed to")


class DLQEntryCreate(BaseModel):
    """Schema for creating a DLQ entry (typically internal use)"""

    task_id: str
    task_name: str
    reason: str
    exception: Optional[str] = None
    traceback: Optional[str] = None
    exception_type: Optional[str] = None
    args: Optional[str] = None
    kwargs: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    worker: Optional[str] = None
    queue: Optional[str] = None
    task_metadata: Optional[dict[str, Any]] = None


class DLQEntryUpdate(BaseModel):
    """Schema for updating a DLQ entry"""

    status: Optional[str] = None
    is_transient: Optional[bool] = None
    error_category: Optional[str] = None
    confidence_score: Optional[float] = None
    next_retry_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class DLQEntry(DLQEntryBase):
    """Complete DLQ entry with all fields"""

    id: UUID = Field(..., description="DLQ entry UUID")
    args: Optional[str] = Field(None, description="Serialized task arguments")
    kwargs: Optional[str] = Field(None, description="Serialized task keyword arguments")
    traceback: Optional[str] = Field(None, description="Full exception traceback")

    # Retry tracking
    retry_count: int = Field(..., description="Original task retry count")
    retry_attempts: int = Field(..., description="Number of DLQ retry attempts")
    max_retries: int = Field(..., description="Maximum DLQ retry attempts")

    # Timestamps
    created_at: datetime = Field(..., description="When task was sent to DLQ")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processed_at: Optional[datetime] = Field(
        None, description="When DLQ entry was analyzed"
    )
    last_retry_at: Optional[datetime] = Field(
        None, description="Last DLQ retry timestamp"
    )
    next_retry_at: Optional[datetime] = Field(
        None, description="Scheduled next retry time"
    )
    resolved_at: Optional[datetime] = Field(
        None, description="When task was resolved or discarded"
    )

    # Analysis metadata
    error_category: Optional[str] = Field(None, description="Categorized error type")
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="ML confidence in classification"
    )

    can_retry: bool = Field(..., description="Whether this task can be retried")
    should_auto_retry: bool = Field(
        ..., description="Whether this task should be auto-retried"
    )

    task_metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional task context"
    )

    class Config:
        from_attributes = True


class DLQEntrySummary(BaseModel):
    """Simplified DLQ entry for list views"""

    id: UUID
    task_name: str
    reason: str
    status: str
    is_transient: bool
    created_at: datetime
    retry_attempts: int
    can_retry: bool


class DLQEntryListResponse(BaseModel):
    """Response schema for DLQ list endpoint"""

    total: int = Field(..., description="Total number of DLQ entries matching filters")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: list[DLQEntrySummary] = Field(..., description="List of DLQ entries")


# =============================================================================
# DLQ Action Schemas
# =============================================================================


class DLQRetryRequest(BaseModel):
    """Request schema for retrying a DLQ entry"""

    delay_seconds: Optional[int] = Field(
        None, ge=0, le=3600, description="Delay before retry (0=immediate)"
    )
    force: bool = Field(
        default=False, description="Force retry even if can_retry=False"
    )


class DLQRetryResponse(BaseModel):
    """Response schema for DLQ retry action"""

    success: bool = Field(..., description="Whether retry was initiated")
    dlq_id: UUID = Field(..., description="DLQ entry ID")
    message: str = Field(..., description="Status message")
    task_id: Optional[str] = Field(None, description="Celery task ID for retry")
    scheduled_for: Optional[datetime] = Field(
        None, description="When retry is scheduled"
    )


class DLQBatchActionRequest(BaseModel):
    """Request schema for batch DLQ actions"""

    dlq_ids: list[UUID] = Field(..., min_items=1, max_items=100)
    action: str = Field(
        ..., description="Action to perform: 'retry', 'discard', 'mark_permanent'"
    )
    delay_seconds: Optional[int] = Field(
        None, ge=0, le=3600, description="Delay for retry action"
    )


class DLQBatchActionResponse(BaseModel):
    """Response schema for batch DLQ actions"""

    total: int = Field(..., description="Total items in batch")
    succeeded: int = Field(..., description="Number of successful actions")
    failed: int = Field(..., description="Number of failed actions")
    results: list[dict[str, Any]] = Field(
        ..., description="Individual results for each item"
    )


# =============================================================================
# DLQ Analytics Schemas
# =============================================================================


class DLQErrorDistribution(BaseModel):
    """Error type distribution"""

    reason: str = Field(..., description="DLQ reason")
    count: int = Field(..., description="Number of occurrences")
    percentage: float = Field(..., description="Percentage of total")


class DLQTopFailingTask(BaseModel):
    """Top failing tasks"""

    task_name: str = Field(..., description="Task name")
    count: int = Field(..., description="Number of failures")
    percentage: float = Field(..., description="Percentage of total")
    last_failure: datetime = Field(..., description="Last failure timestamp")


class DLQAnalyticsResponse(BaseModel):
    """DLQ analytics response"""

    period_days: int = Field(..., description="Analysis period in days")
    total_dlq_entries: int = Field(..., description="Total DLQ entries in period")

    # Status breakdown
    by_status: dict[str, int] = Field(..., description="Count of entries by status")

    # Error distribution
    error_distribution: list[DLQErrorDistribution] = Field(
        ..., description="Breakdown by error type"
    )

    # Top failing tasks
    top_failing_tasks: list[DLQTopFailingTask] = Field(
        ..., description="Tasks with most failures"
    )

    # Key metrics
    transient_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of transient errors"
    )
    auto_retry_success_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Success rate of auto-retries"
    )
    mean_retry_count: float = Field(..., description="Average retry attempts")
    mean_resolution_time_hours: float = Field(
        ..., description="Average time to resolution (hours)"
    )

    # Trends
    daily_trend: list[dict[str, Any]] = Field(
        ..., description="Daily DLQ creation trend"
    )


class DLQHealthCheckResponse(BaseModel):
    """DLQ system health check response"""

    status: str = Field(..., description="System status: healthy, warning, critical")
    timestamp: datetime = Field(..., description="Check timestamp")

    # Metrics
    pending_count: int = Field(..., description="Number of pending DLQ entries")
    retryable_count: int = Field(..., description="Number of retryable entries")
    permanent_count: int = Field(..., description="Number of permanent failures")

    # Health indicators
    creation_rate_per_hour: float = Field(
        ..., description="DLQ creation rate (last hour)"
    )
    resolution_rate_per_hour: float = Field(
        ..., description="DLQ resolution rate (last hour)"
    )

    # Alerts
    alerts: list[str] = Field(..., description="Active alerts")


# =============================================================================
# Query Parameters
# =============================================================================


class DLQQueryParams(BaseModel):
    """Query parameters for DLQ filtering"""

    status: Optional[str] = Field(None, description="Filter by status")
    reason: Optional[str] = Field(None, description="Filter by reason")
    task_name: Optional[str] = Field(
        None, description="Filter by task name (partial match)"
    )
    is_transient: Optional[bool] = Field(None, description="Filter by transient flag")
    worker: Optional[str] = Field(None, description="Filter by worker hostname")
    queue: Optional[str] = Field(None, description="Filter by queue name")

    # Date range filters
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )

    # Sorting
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")
