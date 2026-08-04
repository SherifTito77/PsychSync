# app/api/v1/endpoints/build_analysis.py
"""
API endpoints for Build Failure Analysis Agent
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.crud_build_analysis import (
    build_analysis_report,
    build_failure,
    build_pattern,
    root_cause_analysis,
)
from app.schemas.build_analysis import (
    BuildAnalysisReport,
    BuildFailure,
    BuildFailureCreate,
    BuildFailureSummary,
    BuildFailureUpdate,
    BuildPattern,
    BuildPatternCreate,
    RootCauseAnalysis,
    RootCauseAnalysisCreate,
)

router = APIRouter(prefix="/build_analysis", tags=["build_analysis"])


@router.get(
    "/failures/summary",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildFailureSummary,
)
async def get_failure_summary(db: AsyncSession = Depends(get_db)):
    """
    Get summary of build failures

    Returns overall statistics including health grade, failure counts, and common issues.
    """
    # Get all failures
    all_failures = await build_failure.get_recent(db, skip=0, limit=1000)
    unresolved = await build_failure.get_unresolved(db, skip=0, limit=1000)

    total_failures = len(all_failures)
    unresolved_failures = len(unresolved)
    critical_failures = len([f for f in unresolved if f.priority == "critical"])
    high_priority_failures = len([f for f in unresolved if f.priority == "high"])

    # Calculate average resolution time
    resolved_failures = [f for f in all_failures if f.is_resolved]
    avg_resolution_time = (
        sum([f.resolution_time_minutes or 0 for f in resolved_failures])
        / len(resolved_failures)
        if resolved_failures
        else 0.0
    )

    # Find most common failure type
    failure_types = {}
    for f in all_failures:
        failure_types[f.failure_type] = failure_types.get(f.failure_type, 0) + 1
    most_common_failure_type = (
        max(failure_types, key=failure_types.get) if failure_types else "unknown"
    )

    # Count flaky tests
    flaky_test_count = len(
        [
            f
            for f in all_failures
            if f.failure_type == "test_failure"
            and "flaky" in (f.ai_suggested_fix or "").lower()
        ]
    )

    # Find top contributing factor
    root_causes = {}
    for f in all_failures:
        root_causes[f.root_cause_category] = (
            root_causes.get(f.root_cause_category, 0) + 1
        )
    top_contributing_factor = (
        max(root_causes, key=root_causes.get) if root_causes else "unknown"
    )

    # Calculate health grade
    crud_instance = build_failure
    health_grade = crud_instance.calculate_health_grade(
        total_failures=total_failures,
        unresolved_failures=unresolved_failures,
        critical_failures=critical_failures,
        avg_resolution_time=avg_resolution_time,
    )

    return BuildFailureSummary(
        total_failures=total_failures,
        unresolved_failures=unresolved_failures,
        critical_failures=critical_failures,
        high_priority_failures=high_priority_failures,
        overall_health_grade=health_grade,
        average_resolution_time_minutes=round(avg_resolution_time, 2),
        most_common_failure_type=most_common_failure_type,
        flaky_test_count=flaky_test_count,
        top_contributing_factor=top_contributing_factor,
    )


@router.get(
    "/failures",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=list[BuildFailure],
)
async def get_build_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    failure_type: str | None = None,
    priority: str | None = None,
    developer: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of build failures with optional filtering

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **failure_type**: Filter by failure type (e.g., test_failure, compilation_error)
    - **priority**: Filter by priority (critical, high, medium, low)
    - **developer**: Filter by developer name
    """
    if failure_type:
        return await build_failure.get_by_failure_type(
            db, failure_type=failure_type, skip=skip, limit=limit
        )
    elif priority:
        return await build_failure.get_by_priority(
            db, priority=priority, skip=skip, limit=limit
        )
    elif developer:
        return await build_failure.get_by_developer(
            db, developer_name=developer, skip=skip, limit=limit
        )
    else:
        return await build_failure.get_recent(db, skip=skip, limit=limit)


@router.get(
    "/failures/unresolved",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=list[BuildFailure],
)
async def get_unresolved_failures(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get unresolved build failures ordered by recency"""
    return await build_failure.get_unresolved(db, skip=skip, limit=limit)


@router.post(
    "/failures",
    responses={
        201: {
            "description": "Resource created successfully",
            "content": {
                "application/json": {
                    "example": {"id": 1, "created_at": "2025-01-13T10:00:00Z"}
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildFailure,
)
async def create_build_failure(
    failure_data: BuildFailureCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new build failure record

    Use this endpoint when a build fails to track and analyze the failure.
    """
    return await build_failure.create(db, obj_in=failure_data)


@router.put(
    "/failures/{failure_id}/resolve",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildFailure,
)
async def resolve_build_failure(
    failure_id: UUID,
    resolution_notes: str,
    fix_commit_hash: str,
    resolution_time_minutes: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a build failure as resolved

    - **resolution_notes**: Notes on how the failure was resolved
    - **fix_commit_hash**: Git commit hash that contains the fix
    - **resolution_time_minutes**: Time taken to resolve in minutes
    """
    resolved = await build_failure.mark_as_resolved(
        db,
        failure_id=failure_id,
        resolution_notes=resolution_notes,
        fix_commit_hash=fix_commit_hash,
        resolution_time_minutes=resolution_time_minutes,
    )

    if not resolved:
        raise HTTPException(status_code=404, detail="Build failure not found")

    return resolved


@router.get(
    "/patterns",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=list[BuildPattern],
)
async def get_build_patterns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    pattern_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detected build patterns

    Returns recurring patterns in build failures (e.g., flaky tests, slow builds).
    """
    if pattern_type:
        return await build_pattern.get_by_pattern_type(
            db, pattern_type=pattern_type, skip=skip, limit=limit
        )
    else:
        return await build_pattern.get_unresolved(db, skip=skip, limit=limit)


@router.post(
    "/patterns",
    responses={
        201: {
            "description": "Resource created successfully",
            "content": {
                "application/json": {
                    "example": {"id": 1, "created_at": "2025-01-13T10:00:00Z"}
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildPattern,
)
async def create_build_pattern(
    pattern_data: BuildPatternCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new build pattern record

    Use this to track recurring build issues.
    """
    return await build_pattern.create(db, obj_in=pattern_data)


@router.get(
    "/reports/latest",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildAnalysisReport,
)
async def get_latest_report(db: AsyncSession = Depends(get_db)):
    """Retrieve resource(s).

    Args:
        db: Database session
        **kwargs: Filter criteria

    Returns:
        Resource object or list of resources

    Raises:
        NotFoundError: If resource doesn't exist
    """
    """
    Get the latest build analysis report

    Contains comprehensive analytics including success rates, common failure types, and AI insights.
    """
    report = await build_analysis_report.get_latest(db)
    if not report:
        raise HTTPException(status_code=404, detail="No analysis reports found")
    return report


@router.get(
    "/reports",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=list[BuildAnalysisReport],
)
async def get_reports(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recent build analysis reports"""
    return await build_analysis_report.get_recent(db, limit=limit)


@router.post(
    "/reports/generate",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=BuildAnalysisReport,
)
async def generate_report(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a build analysis report for the specified time period

    - **days**: Number of days to include in the analysis (default: 7)
    """
    from sqlalchemy import func, select

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    # Get failures in period
    result = await db.execute(
        select(BuildFailure)
        .where(BuildFailure.created_at >= period_start)
        .where(BuildFailure.created_at <= period_end)
    )
    failures = result.scalars().all()

    # Calculate statistics
    total_builds = len(failures)
    failed_builds = len([f for f in failures if not f.is_resolved])
    successful_builds = total_builds - failed_builds
    flaky_builds = len([f for f in failures if f.failure_type == "test_failure"])

    # Calculate average build time (mock)
    average_build_time_minutes = 15.5
    average_recovery_time_minutes = 45.2

    # Get top failure types
    failure_types = {}
    for f in failures:
        failure_types[f.failure_type] = failure_types.get(f.failure_type, 0) + 1
    top_failure_types = dict(
        sorted(failure_types.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    # Get top failing branches
    branches = {}
    for f in failures:
        branches[f.branch_name] = branches.get(f.branch_name, 0) + 1
    top_failing_branches = dict(
        sorted(branches.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    # Get top failing developers
    developers = {}
    for f in failures:
        developers[f.developer_name] = developers.get(f.developer_name, 0) + 1
    top_failing_developers = dict(
        sorted(developers.items(), key=lambda x: x[1], reverse=True)[:5]
    )

    # Generate AI content
    success_rate = (successful_builds / total_builds * 100) if total_builds > 0 else 0

    ai_summary = f"""
    Build health analysis for the past {days} days shows{' good' if success_rate > 80 else ' concerning'} trends.
    Success rate of {success_rate:.1f}% with {failed_builds} failed builds out of {total_builds} total builds.
    Top failure type is '{top_failure_types[0] if top_failure_types else 'unknown'}' affecting build stability.
    """

    ai_insights = {
        "highlights": [
            (
                f"{successful_builds} builds succeeded"
                if successful_builds > 0
                else "No successful builds"
            ),
            f"Top failure type: {list(top_failure_types.keys())[0] if top_failure_types else 'N/A'}",
        ],
        "concerns": [
            (
                f"{failed_builds} build failures detected"
                if failed_builds > 0
                else "No build failures"
            ),
        ],
        "recommendations": [
            "Focus on fixing most common failure types",
            "Implement automated testing for flaky tests",
            "Review CI/CD pipeline configuration",
        ],
    }

    recommendations = [
        f"Address {list(top_failure_types.keys())[0] if top_failure_types else 'build'} failures first",
        "Increase test coverage for critical paths",
        "Set up alerts for repeated failures",
    ]

    # Create report
    report = await build_analysis_report.create_report(
        db,
        report_date=datetime.utcnow(),
        period_start=period_start,
        period_end=period_end,
        total_builds=total_builds,
        successful_builds=successful_builds,
        failed_builds=failed_builds,
        flaky_builds=flaky_builds,
        average_build_time_minutes=average_build_time_minutes,
        average_recovery_time_minutes=average_recovery_time_minutes,
        top_failure_types=top_failure_types,
        top_failing_branches=top_failing_branches,
        top_failing_developers=top_failing_developers,
        ai_summary=ai_summary,
        ai_insights=ai_insights,
        recommendations=recommendations,
    )

    return report
