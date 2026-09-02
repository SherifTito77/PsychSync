"""
Employee Lifecycle Analytics API

Endpoints for organizational lifecycle intelligence: turnover, promotion
equity, departure clustering, flight risk, and team stability — all
derived from HRIS structural data, not individual sentiment.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.employee_lifecycle_service import employee_lifecycle_service
from app.services.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/employee-lifecycle",
    tags=["Employee Lifecycle Analytics"],
)


@router.get("/{org_id}/analysis")
async def get_lifecycle_analysis(
    org_id: str,
    period_days: int = Query(default=365, ge=30, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full lifecycle analysis: turnover, promotion, mobility, tenure, risk patterns."""
    analysis = await employee_lifecycle_service.analyze_lifecycle(
        db=db,
        org_id=org_id,
        period_days=period_days,
    )
    return {
        "org_id": analysis.org_id,
        "analysis_period_days": analysis.analysis_period_days,
        "turnover": {
            "total_rate": analysis.turnover_rate,
            "voluntary_rate": analysis.voluntary_turnover_rate,
            "involuntary_rate": analysis.involuntary_turnover_rate,
            "regrettable_rate": analysis.regrettable_turnover_rate,
        },
        "promotion_rate": analysis.promotion_rate,
        "internal_mobility_rate": analysis.internal_mobility_rate,
        "avg_tenure_months": analysis.avg_tenure_months,
        "tenure_distribution": analysis.tenure_distribution,
        "manager_change_frequency": analysis.manager_change_frequency,
        "new_hire_90day_retention": analysis.new_hire_90day_retention,
        "tenure_cliff_month": analysis.tenure_cliff,
        "departure_clustering": analysis.departure_clustering,
        "promotion_equity": analysis.promotion_equity,
        "flight_risk_indicators": analysis.flight_risk_indicators,
    }


@router.get("/{org_id}/team/{team_id}")
async def get_team_stability(
    org_id: str,
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Team-level stability: tenure distribution, recent changes, manager stability."""
    return await employee_lifecycle_service.get_team_stability(
        db=db,
        org_id=org_id,
        team_id=team_id,
    )


@router.get("/{org_id}/departure-clusters")
async def get_departure_clusters(
    org_id: str,
    period_days: int = Query(default=365, ge=30, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Teams/departments with statistically abnormal departure rates."""
    events = await employee_lifecycle_service._load_events(
        db=db, org_id=org_id, period_days=period_days
    )
    clusters = await employee_lifecycle_service.detect_departure_clusters(events)
    return {
        "org_id": org_id,
        "period_days": period_days,
        "clusters": clusters,
        "total_clusters": len(clusters),
    }


@router.get("/{org_id}/flight-risk")
async def get_flight_risk(
    org_id: str,
    period_days: int = Query(default=365, ge=30, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Org-wide flight risk signals by team/department."""
    analysis = await employee_lifecycle_service.analyze_lifecycle(
        db=db,
        org_id=org_id,
        period_days=period_days,
    )
    return {
        "org_id": org_id,
        "period_days": period_days,
        "flight_risk_indicators": analysis.flight_risk_indicators,
        "tenure_cliff_month": analysis.tenure_cliff,
        "regrettable_turnover_rate": analysis.regrettable_turnover_rate,
    }
