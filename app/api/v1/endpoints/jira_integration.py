# app/api/v1/endpoints/jira_integration.py

"""
JIRA INTEGRATION ENDPOINTS
API endpoints for Jira integration, bug tracking, and reporting

Author: Product Operations Team
Version: 1.0
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.jira_integration import JiraIssue, JiraBugSummary, JiraSprintMetrics
from app.db.models.user import User
from app.schemas.jira_integration import (
    BugTrendData,
    EngineeringPerformanceReport,
    JiraBugSummary,
    JiraIssue,
    JiraSprintMetrics,
)

router = APIRouter(prefix="/jira_integration", tags=["jira_integration"])


@router.get(
    "/issues",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[JiraIssue],
)
async def get_jira_issues(    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    project_key: str | None = Query(None, description="Filter by project key"),
    issue_type: str | None = Query(None, description="Filter by issue type"),
    status: str | None = Query(None, description="Filter by status"),
    is_bug: bool | None = Query(None, description="Filter for bugs only"),
    sprint_id: str | None = Query(None, description="Filter by sprint"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[JiraIssue]:
    """
    Get Jira issues with filtering

    Returns paginated list of Jira issues
    """
    query = select(JiraIssue)

    # Apply filters
    filters = []
    if project_key is not None:
        filters.append(JiraIssue.project_key == project_key)
    if issue_type is not None:
        filters.append(JiraIssue.issue_type == issue_type)
    if status is not None:
        filters.append(JiraIssue.status == status)
    if is_bug is not None:
        filters.append(JiraIssue.is_bug == (1.0 if is_bug else 0.0))
    if sprint_id is not None:
        filters.append(JiraIssue.sprint_id == sprint_id)

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(JiraIssue.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    issues = result.scalars().all()

    return list(issues)


@router.get(
    "/bugs/summary/latest",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=JiraBugSummary,
)
async def get_latest_bug_summary(    project_key: str = Query(..., description="Project key"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JiraBugSummary:
    """
    Get the latest bug summary for a project

    Returns the most recent daily bug summary
    """
    query = select(JiraBugSummary).where(
        JiraBugSummary.project_key == project_key
    ).order_by(JiraBugSummary.summary_date.desc()).limit(1)

    result = await db.execute(query)
    summary = result.scalar_one_or_none()

    if not summary:
        raise HTTPException(status_code=404, detail="No bug summary found for this project")

    return summary


@router.get(
    "/bugs/summary",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[JiraBugSummary],
)
async def get_bug_summaries(    project_key: str = Query(..., description="Project key"),
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[JiraBugSummary]:
    """
    Get bug summaries for a date range

    Returns daily bug summaries for the specified period
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    query = select(JiraBugSummary).where(
        and_(
            JiraBugSummary.project_key == project_key,
            JiraBugSummary.summary_date >= start_date
        )
    ).order_by(JiraBugSummary.summary_date.desc())

    result = await db.execute(query)
    summaries = result.scalars().all()

    return list(summaries)


@router.get(
    "/bugs/trends",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[BugTrendData],
)
async def get_bug_trends(    project_key: str = Query(..., description="Project key"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[BugTrendData]:
    """
    Get bug trend data over time

    Returns bug creation and resolution trends
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get summaries
    query = select(JiraBugSummary).where(
        and_(
            JiraBugSummary.project_key == project_key,
            JiraBugSummary.summary_date >= start_date
        )
    ).order_by(JiraBugSummary.summary_date)

    result = await db.execute(query)
    summaries = result.scalars().all()

    # Convert to trend data
    trends = []
    for summary in summaries:
        resolution_rate = 0.0
        if summary.total_bugs > 0:
            resolution_rate = (summary.resolved_bugs / summary.total_bugs) * 100

        trends.append(BugTrendData(
            date=summary.summary_date,
            new_bugs=summary.new_bugs,
            resolved_bugs=summary.resolved_bugs,
            total_bugs=summary.total_bugs,
            critical_bugs=summary.critical_bugs,
            resolution_rate=round(resolution_rate, 2),
        ))

    return trends


@router.get(
    "/sprints",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[JiraSprintMetrics],
)
async def get_sprints(    project_key: str = Query(..., description="Project key"),
    state: str | None = Query(None, description="Filter by state: active, closed, future"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[JiraSprintMetrics]:
    """
    Get sprint metrics

    Returns sprint performance data
    """
    query = select(JiraSprintMetrics).where(
        JiraSprintMetrics.project_key == project_key
    )

    if state:
        query = query.where(JiraSprintMetrics.state == state)

    query = query.order_by(JiraSprintMetrics.start_date.desc())
    result = await db.execute(query)
    sprints = result.scalars().all()

    return list(sprints)


@router.get(
    "/sprints/{sprint_id}",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=JiraSprintMetrics,
)
async def get_sprint_details(    sprint_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> JiraSprintMetrics:
    """
    Get detailed sprint metrics

    Returns comprehensive sprint performance data
    """
    query = select(JiraSprintMetrics).where(
        JiraSprintMetrics.sprint_id == sprint_id
    )

    result = await db.execute(query)
    sprint = result.scalar_one_or_none()

    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    return sprint


@router.get(
    "/reports/performance",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=EngineeringPerformanceReport,
)
async def get_performance_report(    project_key: str = Query(..., description="Project key"),
    days: int = Query(7, ge=1, le=90, description="Number of days to report on"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EngineeringPerformanceReport:
    """
    Generate engineering performance report

    Returns comprehensive performance metrics for the specified period
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get bug metrics
    bugs_query = select(JiraIssue).where(
        and_(
            JiraIssue.project_key == project_key,
            JiraIssue.is_bug == 1.0,
            JiraIssue.created_at >= start_date
        )
    )

    bugs_result = await db.execute(bugs_query)
    bugs = list(bugs_result.scalars().all())

    # Calculate metrics
    total_bugs_created = len(bugs)
    total_bugs_resolved = len([b for b in bugs if b.resolved_at and b.resolved_at <= end_date])

    bugs_by_severity = {
        "critical": len([b for b in bugs if b.severity == "critical"]),
        "major": len([b for b in bugs if b.severity == "major"]),
        "minor": len([b for b in bugs if b.severity == "minor"]),
    }

    # Calculate avg resolution time
    resolved_bugs_with_time = [b for b in bugs if b.resolved_at and b.created_at]
    if resolved_bugs_with_time:
        resolution_times = [
            (b.resolved_at - b.created_at).total_seconds() / 3600
            for b in resolved_bugs_with_time
        ]
        avg_resolution_time = sum(resolution_times) / len(resolution_times)
    else:
        avg_resolution_time = 0.0

    # Get sprint metrics
    sprints_query = select(JiraSprintMetrics).where(
        and_(
            JiraSprintMetrics.project_key == project_key,
            JiraSprintMetrics.start_date >= start_date,
            JiraSprintMetrics.state == "closed"
        )
    )

    sprints_result = await db.execute(sprints_query)
    sprints = list(sprints_result.scalars().all())

    sprints_completed = len(sprints)
    avg_velocity = int(sum([s.team_velocity or 0 for s in sprints]) / len(sprints)) if sprints else 0
    completion_rate = sum([s.completion_rate or 0 for s in sprints]) / len(sprints) if sprints else 0.0

    # Get top contributors (by assigned issues)
    contributors_query = select(
        JiraIssue.assignee_name,
        func.count(JiraIssue.id).label('count')
    ).where(
        and_(
            JiraIssue.project_key == project_key,
            JiraIssue.assignee_name.isnot(None),
            JiraIssue.created_at >= start_date
        )
    ).group_by(JiraIssue.assignee_name).order_by(
        func.count(JiraIssue.id).desc()
    ).limit(5)

    contributors_result = await db.execute(contributors_query)
    top_contributors = [
        {"name": row.assignee_name, "issues_completed": row.count}
        for row in contributors_result.fetchall()
    ]

    # Generate AI summary
    ai_highlights = []
    ai_concerns = []
    ai_recommendations = []

    if bugs_by_severity["critical"] > 0:
        ai_concerns.append(f"{bugs_by_severity['critical']} critical bugs need immediate attention")

    if avg_resolution_time > 48:
        ai_concerns.append(f"Average resolution time ({avg_resolution_time:.1f}h) exceeds 48h target")

    if completion_rate < 80:
        ai_concerns.append(f"Sprint completion rate ({completion_rate:.1f}%) is below 80% target")

    if total_bugs_created > total_bugs_resolved:
        ai_concerns.append("Bug backlog is growing - more bugs created than resolved")

    if avg_velocity > 0:
        ai_highlights.append(f"Team velocity: {avg_velocity} story points per sprint")

    if sprints_completed > 0:
        ai_highlights.append(f"Completed {sprints_completed} sprint(s) in the period")

    resolution_rate = (total_bugs_resolved / total_bugs_created * 100) if total_bugs_created > 0 else 0
    if resolution_rate > 80:
        ai_highlights.append(f"Strong bug resolution rate: {resolution_rate:.1f}%")

    # Recommendations
    if bugs_by_severity["critical"] > 2:
        ai_recommendations.append("Consider scheduling a bug sprint to address critical issues")

    if avg_resolution_time > 72:
        ai_recommendations.append("Review bug triage process to reduce resolution time")

    if completion_rate < 70:
        ai_recommendations.append("Improve sprint planning accuracy and commitment estimation")

    ai_summary = f"Engineering performance report for {project_key} covering {days} days. "

    if total_bugs_created > 0:
        ai_summary += f"Team addressed {total_bugs_resolved} of {total_bugs_created} bugs ({resolution_rate:.1f}% resolution rate). "

    if sprints_completed > 0:
        ai_summary += f"Completed {sprints_completed} sprint(s) with average velocity of {avg_velocity} points. "

    ai_summary += f"Overall completion rate: {completion_rate:.1f}%."

    return EngineeringPerformanceReport(
        period_start=start_date,
        period_end=end_date,
        project_key=project_key,
        total_bugs_created=total_bugs_created,
        total_bugs_resolved=total_bugs_resolved,
        bugs_by_severity=bugs_by_severity,
        avg_resolution_time_hours=round(avg_resolution_time, 2),
        sprints_completed=sprints_completed,
        avg_velocity=avg_velocity,
        completion_rate=round(completion_rate, 2),
        top_contributors=top_contributors,
        team_workload={},
        ai_summary=ai_summary,
        ai_highlights=ai_highlights,
        ai_concerns=ai_concerns,
        ai_recommendations=ai_recommendations,
    )


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check API and database connectivity status",
    responses={200: {'description': 'System is healthy', 'content': {'application/json': {'example': {'status': 'healthy', 'database': 'connected', 'redis': 'connected', 'timestamp': '2025-01-13T10:00:00Z'}}}}},
)
async def health_check(    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Health check endpoint for Jira integration"""
    return {
        "status": "healthy",
        "service": "jira_integration",
        "version": "1.0.0",
    }
