# app/api/v1/endpoints/breaking_changes.py
"""
API endpoints for Breaking Changes Detection Agent
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.crud_breaking_changes import breaking_change
from app.crud.crud_breaking_changes import breaking_change_report as report_crud
from app.crud.crud_breaking_changes import migration_guide
from app.schemas.breaking_changes import (
    BreakingChange,
    BreakingChangeCreate,
    BreakingChangeReport,
    BreakingChangesSummary,
    MigrationGuide,
    MigrationGuideCreate,
)

router = APIRouter(prefix="/breaking_changes", tags=["breaking_changes"])


@router.get(
    "/changes/summary",
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
    response_model=BreakingChangesSummary,
)
async def get_breaking_changes_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of breaking changes"""
    try:
        all_changes = await breaking_change.get_recent(db, skip=0, limit=1000)
    except Exception:
        return BreakingChangesSummary(
            total_changes=0,
            unresolved_changes=0,
            critical_changes=0,
            high_priority_changes=0,
            overall_risk_score=0.0,
            risk_grade="A",
            backwards_compatible_count=0,
            breaking_changes_count=0,
            most_common_change_type="none",
            most_affected_component="none",
        )

    total_changes = len(all_changes)
    unresolved = len([c for c in all_changes if not c.is_approved])
    critical = len(
        [c for c in all_changes if c.severity == "critical" and not c.is_approved]
    )
    high_priority = len(
        [c for c in all_changes if c.severity == "high" and not c.is_approved]
    )

    # Calculate risk score
    weights = {"critical": 40, "high": 30, "medium": 20, "low": 10}
    risk_score = (
        sum([weights.get(c.severity, 10) for c in all_changes if not c.is_approved])
        / unresolved
        if unresolved > 0
        else 0.0
    )

    # Get risk grade
    crud_instance = breaking_change
    risk_grade = crud_instance.calculate_risk_grade(risk_score)

    backwards_compatible = len([c for c in all_changes if c.backwards_compatible])
    breaking = len([c for c in all_changes if not c.backwards_compatible])

    # Most common change type
    change_types = {}
    for c in all_changes:
        change_types[c.change_type] = change_types.get(c.change_type, 0) + 1
    most_common = max(change_types, key=change_types.get) if change_types else "unknown"

    # Most affected component
    components = {}
    for c in all_changes:
        components[c.affected_component] = components.get(c.affected_component, 0) + 1
    most_affected = max(components, key=components.get) if components else "unknown"

    return BreakingChangesSummary(
        total_changes=total_changes,
        unresolved_changes=unresolved,
        critical_changes=critical,
        high_priority_changes=high_priority,
        overall_risk_score=round(risk_score, 2),
        risk_grade=risk_grade,
        backwards_compatible_count=backwards_compatible,
        breaking_changes_count=breaking,
        most_common_change_type=most_common,
        most_affected_component=most_affected,
    )


@router.get(
    "/changes",
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
    response_model=list[BreakingChange],
)
async def get_breaking_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: str | None = None,
    change_type: str | None = None,
    component: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get breaking changes with optional filtering"""
    try:
        if severity:
            return await breaking_change.get_by_severity(
                db, severity=severity, skip=skip, limit=limit
            )
        elif change_type:
            return await breaking_change.get_by_type(
                db, change_type=change_type, skip=skip, limit=limit
            )
        elif component:
            return await breaking_change.get_by_component(
                db, component=component, skip=skip, limit=limit
            )
        else:
            return await breaking_change.get_recent(db, skip=skip, limit=limit)
    except Exception:
        return []


@router.get(
    "/changes/unapproved",
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
    response_model=list[BreakingChange],
)
async def get_unapproved_changes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get unapproved breaking changes"""
    try:
        return await breaking_change.get_unapproved(db, skip=skip, limit=limit)
    except Exception:
        return []


@router.post(
    "/changes",
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
    response_model=BreakingChange,
)
async def create_breaking_change(
    change_data: BreakingChangeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new breaking change record"""
    return await breaking_change.create(db, obj_in=change_data)


@router.put(
    "/changes/{change_id}/approve",
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
    response_model=BreakingChange,
)
async def approve_breaking_change(
    change_id: UUID,
    approved_by: str,
    db: AsyncSession = Depends(get_db),
):
    """Approve a breaking change"""
    approved = await breaking_change.mark_as_approved(
        db, change_id=change_id, approved_by=approved_by
    )
    if not approved:
        raise HTTPException(status_code=404, detail="Breaking change not found")
    return approved


@router.get(
    "/migration-guides",
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
    response_model=list[MigrationGuide],
)
async def get_migration_guides(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get migration guides"""
    return await migration_guide.get_recent(db, skip=skip, limit=limit)


@router.post(
    "/migration-guides",
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
    response_model=MigrationGuide,
)
async def create_migration_guide(
    guide_data: MigrationGuideCreate,
    is_automated: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Create a new migration guide"""
    return await migration_guide.create(
        db, obj_in=guide_data, is_automated=is_automated
    )


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
    response_model=BreakingChangeReport,
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
    """Get latest breaking changes report"""
    report = await report_crud.get_latest(db)
    if not report:
        raise HTTPException(status_code=404, detail="No reports found")
    return report
