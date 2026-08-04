# app/api/v1/endpoints/metrics.py
"""
Metrics Summary Endpoints
API endpoints for application metrics and summaries
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.assessment import Assessment
from app.db.models.organization import Organization
from app.db.models.response import Response
from app.db.models.team import Team
from app.db.models.user import User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/summary",
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
)
async def get_metrics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get application metrics summary

    Returns high-level metrics about the application state
    """
    # Get total counts
    users_count_result = await db.execute(select(func.count(User.id)))
    users_count = users_count_result.scalar() or 0

    organizations_count_result = await db.execute(select(func.count(Organization.id)))
    organizations_count = organizations_count_result.scalar() or 0

    teams_count_result = await db.execute(select(func.count(Team.id)))
    teams_count = teams_count_result.scalar() or 0

    assessments_count_result = await db.execute(select(func.count(Assessment.id)))
    assessments_count = assessments_count_result.scalar() or 0

    responses_count_result = await db.execute(select(func.count(Response.id)))
    responses_count = responses_count_result.scalar() or 0

    # Get active users in last 30 days (based on creation date)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    )
    active_users_count = active_users_result.scalar() or 0

    return {
        "users": {
            "total": users_count,
            "active_30_days": active_users_count,
        },
        "organizations": {
            "total": organizations_count,
        },
        "teams": {
            "total": teams_count,
        },
        "assessments": {
            "total": assessments_count,
        },
        "responses": {
            "total": responses_count,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check metrics service health",
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "metrics",
                    }
                }
            },
        }
    },
)
async def health_check(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Health check endpoint for metrics service"""
    return {
        "status": "healthy",
        "service": "metrics",
        "version": "1.0.0",
    }
