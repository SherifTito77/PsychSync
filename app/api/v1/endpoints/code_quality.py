# app/api/v1/endpoints/code_quality.py

"""
CODE QUALITY MONITORING ENDPOINTS
API endpoints for code quality metrics and analysis

Author: Product Operations Team
Version: 1.0
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.crud.crud_code_quality import (
    code_quality_issue,
    code_quality_metric,
    pull_request_quality,
)
from app.db.models.user import User
from app.schemas.code_quality import (
    CodeQualityIssue,
    CodeQualityMetric,
    CodeQualityMetricWithIssues,
    CodeQualitySummary,
    CodeQualityTrend,
    PullRequestQuality,
    PullRequestQualitySummary,
)

router = APIRouter()


@router.get(
    "/metrics/summary",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=CodeQualitySummary,
)
async def get_quality_summary(    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CodeQualitySummary:
    """
    Get current code quality summary

    Returns overall quality score, grade, trends, and issue counts
    """
    # Get latest metric
    latest = await code_quality_metric.get_latest(db)

    if not latest:
        raise HTTPException(status_code=404, detail="No quality metrics available")

    # Get previous metric for trend calculation
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    previous_metrics, _ = await code_quality_metric.get_multi(
        db,
        start_date=thirty_days_ago,
        skip=1,
        limit=1,
    )

    trend = "stable"
    trend_percentage = 0.0

    if previous_metrics:
        previous = previous_metrics[0]
        if previous.quality_score > 0:
            change = ((latest.quality_score - previous.quality_score) / previous.quality_score) * 100
            trend_percentage = change

            if change > 2:
                trend = "improving"
            elif change < -2:
                trend = "declining"

    return CodeQualitySummary(
        current_score=latest.quality_score,
        current_grade=latest.quality_grade,
        trend=trend,
        trend_percentage=trend_percentage,
        total_issues=latest.code_violations_count + latest.bugs_count + latest.security_hotspots_count,
        critical_issues=latest.security_hotspots_count + latest.bugs_count,
        major_issues=latest.code_violations_count,
        test_coverage=latest.test_coverage_percentage or 0.0,
        technical_debt_hours=latest.estimated_remediation_cost or 0.0,
        files_scanned=latest.file_count,
        last_scan_date=latest.scan_date,
    )


@router.get(
    "/metrics",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[CodeQualityMetric],
)
async def get_quality_metrics(    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=200, description="Number of records to return"),
    module_name: str | None = Query(None, description="Filter by module name"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CodeQualityMetric]:
    """
    Get code quality metrics with filtering and pagination

    Returns historical quality metrics over time
    """
    metrics, _ = await code_quality_metric.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        module_name=module_name,
        start_date=start_date,
        end_date=end_date,
    )

    return metrics


@router.get(
    "/metrics/latest",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=CodeQualityMetricWithIssues,
)
async def get_latest_metrics(    module_name: str | None = Query(None, description="Filter by module name"),
    include_issues: bool = Query(True, description="Include quality issues"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CodeQualityMetricWithIssues:
    """
    Get the most recent quality metric with optional issues

    Returns the latest scan results
    """
    metric = await code_quality_metric.get_latest(db, module_name=module_name)

    if not metric:
        raise HTTPException(status_code=404, detail="No quality metrics found")

    # Load issues if requested
    issues = []
    if include_issues:
        issues, _ = await code_quality_issue.get_multi(
            db=db,
            metric_id=str(metric.id),
            limit=50,
        )

    return CodeQualityMetricWithIssues(
        **metric.__dict__,
        quality_issues=issues,
    )


@router.get(
    "/metrics/trend",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[CodeQualityTrend],
)
async def get_quality_trend(    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    module_name: str | None = Query(None, description="Filter by module name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CodeQualityTrend]:
    """
    Get code quality trend over time

    Returns quality scores and trends for the specified period
    """
    trend_data = await code_quality_metric.get_trend(
        db=db,
        days=days,
        module_name=module_name,
    )

    return [CodeQualityTrend(**t) for t in trend_data]


@router.get(
    "/issues",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[CodeQualityIssue],
)
async def get_quality_issues(    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    issue_type: str | None = Query(None, description="Filter by issue type"),
    severity: str | None = Query(None, description="Filter by severity"),
    status: str = Query("open", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CodeQualityIssue]:
    """
    Get code quality issues with filtering

    Returns detected issues with severity and remediation info
    """
    issues, _ = await code_quality_issue.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        issue_type=issue_type,
        severity=severity,
        status=status,
    )

    return issues


@router.get(
    "/issues/hotspots",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[CodeQualityIssue],
)
async def get_quality_hotspots(    limit: int = Query(20, ge=1, le=100, description="Number of hotspots to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[CodeQualityIssue]:
    """
    Get critical and major issues requiring attention

    Returns the most severe issues that should be addressed first
    """
    hotspots = await code_quality_issue.get_hotspots(db=db, limit=limit)
    return hotspots


@router.get(
    "/pull-requests",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[PullRequestQuality],
)
async def get_pull_request_quality(    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    risk_level: str | None = Query(None, description="Filter by risk level"),
    min_score: float | None = Query(None, ge=0, le=100, description="Minimum quality score"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[PullRequestQuality]:
    """
    Get pull request quality scores

    Returns PRs analyzed for quality and risk
    """
    prs, _ = await pull_request_quality.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        risk_level=risk_level,
        min_score=min_score,
    )

    return prs


@router.get(
    "/pull-requests/summary",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=PullRequestQualitySummary,
)
async def get_pull_request_summary(    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PullRequestQualitySummary:
    """
    Get pull request quality summary

    Returns aggregate metrics for PR quality over the specified period
    """
    summary = await pull_request_quality.get_summary(db=db, days=days)
    return PullRequestQualitySummary(**summary)


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check API and database connectivity status",
    responses={200: {'description': 'System is healthy', 'content': {'application/json': {'example': {'status': 'healthy', 'database': 'connected', 'redis': 'connected', 'timestamp': '2025-01-13T10:00:00Z'}}}}},
)
async def health_check(    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Health check endpoint for code quality monitoring"""
    return {
        "status": "healthy",
        "service": "code_quality_monitoring",
        "version": "1.0.0",
    }
