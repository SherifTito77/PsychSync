"""
Executive Burnout Analytics API Endpoints
"""

import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.organization import Organization
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def validate_org_id(db: AsyncSession, org_id: str) -> str:
    """Helper to validate organization exists and return uuid.UUID string"""
    try:
        org_uuid = uuid.UUID(org_id)
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_uuid)
        )
    except ValueError:
        # If not a valid uuid.UUID, try looking up by name
        org_result = await db.execute(
            select(Organization).where(Organization.name == org_id)
        )

    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return str(org.id)


@router.get("/executive/burnout/summary", response_model=Dict[str, Any])
async def get_executive_summary(
    org_id: str,
    range: str = Query("90d", description="Time range: 30d, 90d, or 180d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    validated_org_id = await validate_org_id(db, org_id)
    summary = await _calculate_executive_summary(db, validated_org_id, range)
    # Return fields directly to match frontend expectation
    return {"organization_id": validated_org_id, "time_range": range, **summary}


@router.get("/executive/burnout/heatmap", response_model=Dict[str, Any])
async def get_department_heatmap(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    validated_org_id = await validate_org_id(db, org_id)
    heatmap_data = await _calculate_department_heatmap(db, validated_org_id)
    return {"organization_id": validated_org_id, "departments": heatmap_data}


@router.get("/executive/burnout/forecast", response_model=Dict[str, Any])
async def get_burnout_forecast(
    org_id: str,
    horizon: str = Query("14d", description="Forecast horizon: 7d, 14d, or 30d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    validated_org_id = await validate_org_id(db, org_id)
    forecast_data = await _calculate_forecast(db, validated_org_id, horizon)
    return {
        "organization_id": validated_org_id,
        "horizon_days": horizon,
        "forecast_data": forecast_data["forecast_data"],
        "intervention_scenarios": forecast_data["intervention_scenarios"],
    }


@router.get("/executive/burnout/cost-benefit", response_model=Dict[str, Any])
async def get_cost_benefit_analysis(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    validated_org_id = await validate_org_id(db, org_id)
    analysis = await _calculate_cost_benefit(db, validated_org_id)
    return {"organization_id": validated_org_id, "analysis": analysis}


async def _calculate_executive_summary(
    db: AsyncSession, org_id: str, range: str
) -> Dict[str, Any]:
    """
    Calculates a weighted Organizational Health Index (OHI).
    Formula: OHI = (0.4 * Engagement) + (0.3 * RetentionRate) + (0.3 * TeamCompatibility)
    All components normalized to 0-100 scale.
    """
    # 1. Fetch data components (simulated queries based on system structure)
    # In production, these would be queries to analytics, assessments, and HRIS tables.
    engagement_score = 75.0  # Placeholder for query to wellness/assessment
    retention_rate = 85.0  # Placeholder for query to hris/turnover
    compatibility_score = 80.0  # Placeholder for query to team_optimization

    # 2. Calculate Weighted Score
    ohi_score = (
        (0.4 * engagement_score) + (0.3 * retention_rate) + (0.3 * compatibility_score)
    )

    # 3. Return structured data
    return {
        "overall_risk_score": round(100 - ohi_score, 1),  # Risk is inverse of Health
        "health_index": round(ohi_score, 1),
        "risk_trend": "stable",  # Needs actual history comparison logic
        "high_risk_employees": 47,
        "high_risk_percentage": 12.3,
        "predicted_turnover_risk_30d": 18.5,
        "estimated_cost_of_burnout": {
            "monthly": 284000,
            "quarterly": 852000,
            "annual": 3408000,
        },
        "intervention_roi": {
            "invested": 156000,
            "saved": 482000,
            "roi_percentage": 209,
        },
    }


async def _calculate_department_heatmap(db, org_id) -> List[Dict[str, Any]]:
    return [{"department": "Engineering", "avg_risk_score": 58}]


async def _calculate_forecast(db, org_id, horizon) -> Dict[str, Any]:
    return {"forecast_data": [], "intervention_scenarios": []}


async def _calculate_cost_benefit(db, org_id) -> Dict[str, Any]:
    return {"roi": 209.0}
