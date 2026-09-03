"""
Executive Burnout Analytics API Endpoints

Provides REST API endpoints for CEO-level dashboards:
- Organization-level summaries
- Department heatmaps
- 14-day forecasts
- Cost-benefit analysis
- ROI tracking

Author: PsychSync Engineering Team
Version: 2.0
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.organization import Organization

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Pydantic Schemas
# =============================================================================


class ExecutiveSummaryResponse(BaseModel):
    """Response schema for executive summary"""

    organization_id: str
    time_range: str

    overall_risk_score: float
    risk_trend: str  # 'improving', 'stable', 'worsening'
    high_risk_employees: int
    high_risk_percentage: float
    predicted_turnover_risk_30d: float
    estimated_cost_of_burnout: Dict[str, float]
    intervention_roi: Dict[str, float]


class DepartmentHeatmapResponse(BaseModel):
    """Response schema for department heatmap"""

    organization_id: str
    departments: List[Dict[str, Any]]


class ForecastResponse(BaseModel):
    """Response schema for 14-day forecast"""

    organization_id: str
    horizon_days: int
    forecast_data: List[Dict[str, Any]]
    intervention_scenarios: List[Dict[str, Any]]


class CostBenefitResponse(BaseModel):
    """Response schema for cost-benefit analysis"""

    organization_id: str
    analysis: Dict[str, Any]


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/executive/burnout/summary", response_model=Dict[str, Any])
async def get_executive_summary(
    org_id: str,
    range: str = Query("90d", description="Time range: 30d, 90d, or 180d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get organization-level burnout summary for executive dashboard

    Returns:
        Executive summary with overall risk, trends, and ROI
    """
    try:
        logger.info(f"Fetching executive summary for org {org_id}, range {range}")

        # Parse time range
        days_map = {"30d": 30, "90d": 90, "180d": 180}
        days = days_map.get(range, 90)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Validate organization exists
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        organization = org_result.scalar_one_or_none()

        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        # TODO(human): Implement organization membership authorization check
        # Context: Users should only access burnout data for organizations they belong to
        # Your task: Implement the check_user_organization_access() function below
        #
        # Guidance:
        # 1. Check if current_user.organization_id matches the requested org_id
        # 2. Consider role-based access (superusers should access all orgs)
        # 3. Decide error handling: 403 Forbidden for no access vs 404 Not Found to hide existence
        # 4. You may want to check for specific roles like 'admin', 'hr', or 'manager'
        # 5. Consider team membership - should managers see their team's data?
        #
        # Example structure:
        # def check_user_organization_access(current_user: User, org_id: str) -> bool:
        #     # Superusers can access all organizations
        #     if current_user.is_superuser:
        #         return True
        #
        #     # Regular users can only access their own organization
        #     # TODO(human): Add your business logic here
        #     pass
        #
        # Then call it here:
        # if not check_user_organization_access(current_user, org_id):
        #     raise HTTPException(status_code=403, detail="You don't have access to this organization's data")

        # Calculate executive summary (mock data for now)
        summary = await _calculate_executive_summary(db, org_id, cutoff_date)

        return {"organization_id": org_id, "time_range": range, "summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching executive summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch summary: {str(e)}"
        )


@router.get("/executive/burnout/heatmap", response_model=Dict[str, Any])
async def get_department_heatmap(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get department risk heatmap for executive dashboard

    Returns:
        Department-level risk breakdown with costs
    """
    try:
        logger.info(f"Fetching department heatmap for org {org_id}")

        # Get departments (would query from teams/departments table)
        # For now, return mock data structure

        heatmap_data = await _calculate_department_heatmap(db, org_id)

        return {"organization_id": org_id, "departments": heatmap_data}

    except Exception as e:
        logger.error(f"Error fetching department heatmap: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch heatmap: {str(e)}"
        )


@router.get("/executive/burnout/forecast", response_model=Dict[str, Any])
async def get_burnout_forecast(
    org_id: str,
    horizon: str = Query("14d", description="Forecast horizon: 7d, 14d, or 30d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get 14-day burnout probability forecast

    Returns:
        Forecast with confidence bands and intervention scenarios
    """
    try:
        logger.info(f"Fetching burnout forecast for org {org_id}, horizon {horizon}")

        # Parse horizon
        horizon_map = {"7d": 7, "14d": 14, "30d": 30}
        horizon_days = horizon_map.get(horizon, 14)

        forecast_data = await _calculate_forecast(db, org_id, horizon_days)

        return {
            "organization_id": org_id,
            "horizon_days": horizon_days,
            "forecast_data": forecast_data["forecast_data"],
            "intervention_scenarios": forecast_data["intervention_scenarios"],
        }

    except Exception as e:
        logger.error(f"Error fetching burnout forecast: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch forecast: {str(e)}"
        )


@router.get("/executive/burnout/cost-benefit", response_model=Dict[str, Any])
async def get_cost_benefit_analysis(
    org_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost-benefit analysis of interventions vs inaction

    Returns:
        Detailed cost breakdown with ROI calculations
    """
    try:
        logger.info(f"Fetching cost-benefit analysis for org {org_id}")

        analysis = await _calculate_cost_benefit(db, org_id)

        return {"organization_id": org_id, "analysis": analysis}

    except Exception as e:
        logger.error(f"Error fetching cost-benefit analysis: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch analysis: {str(e)}"
        )


# =============================================================================
# Internal Helper Functions
# =============================================================================


async def _calculate_executive_summary(
    db: AsyncSession, org_id: str, cutoff_date: datetime
) -> Dict[str, Any]:
    """Calculate executive summary metrics"""

    # In production, this would query actual data
    # For now, return mock data based on typical patterns

    return {
        "overall_risk_score": 52.3,
        "risk_trend": "stable",
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
            "roi_percentage": 209.0,
        },
    }


async def _calculate_department_heatmap(
    db: AsyncSession, org_id: str
) -> List[Dict[str, Any]]:
    """Calculate department-level risk heatmap"""

    # Mock data - in production, would aggregate from predictions table
    departments = [
        {
            "department": "Engineering",
            "team_count": 120,
            "avg_risk_score": 58,
            "high_risk_count": 18,
            "critical_risk_count": 3,
            "risk_trend": "worsening",
            "predicted_burnouts_90d": 4,
            "estimated_cost_impact": 425000,
        },
        {
            "department": "Sales",
            "team_count": 85,
            "avg_risk_score": 63,
            "high_risk_count": 16,
            "critical_risk_count": 4,
            "risk_trend": "stable",
            "predicted_burnouts_90d": 5,
            "estimated_cost_impact": 512000,
        },
        {
            "department": "Marketing",
            "team_count": 45,
            "avg_risk_score": 42,
            "high_risk_count": 5,
            "critical_risk_count": 1,
            "risk_trend": "improving",
            "predicted_burnouts_90d": 1,
            "estimated_cost_impact": 98000,
        },
        {
            "department": "Operations",
            "team_count": 95,
            "avg_risk_score": 48,
            "high_risk_count": 8,
            "critical_risk_count": 2,
            "risk_trend": "stable",
            "predicted_burnouts_90d": 2,
            "estimated_cost_impact": 215000,
        },
    ]

    return departments


async def _calculate_forecast(
    db: AsyncSession, org_id: str, horizon_days: int
) -> Dict[str, Any]:
    """Calculate 14-day burnout probability forecast"""

    # Generate forecast data
    days = list(range(1, horizon_days + 1))
    forecast_data = []
    current_prob = 0.35

    for day in days:
        # Simulate slight increase over time
        day_prob = min(current_prob + (day * 0.015), 0.65)
        uncertainty = 0.08 + (day * 0.002)

        forecast_data.append(
            {
                "date": (datetime.utcnow() + timedelta(days=day)).strftime("%Y-%m-%d"),
                "org_burnout_probability": day_prob,
                "confidence_interval_lower": max(0, day_prob - 1.96 * uncertainty),
                "confidence_interval_upper": min(1.0, day_prob + 1.96 * uncertainty),
            }
        )

    # Intervention scenarios
    intervention_scenarios = [
        {
            "name": "No Action",
            "probability_at_day_14": forecast_data[-1]["org_burnout_probability"] * 100,
            "cost": 0,
        },
        {
            "name": "Light Intervention",
            "probability_at_day_14": forecast_data[-1]["org_burnout_probability"] * 80,
            "cost": 25000,
        },
        {
            "name": "Comprehensive Program",
            "probability_at_day_14": forecast_data[-1]["org_burnout_probability"] * 60,
            "cost": 75000,
        },
    ]

    return {
        "forecast_data": forecast_data,
        "intervention_scenarios": intervention_scenarios,
    }


async def _calculate_cost_benefit(db: AsyncSession, org_id: str) -> Dict[str, Any]:
    """Calculate cost-benefit analysis of interventions"""

    # Standard cost multipliers (would be configured per organization)
    avg_salary = 85000
    turnover_multiplier = 1.5  # Cost of turnover = 1.5x annual salary
    employee_count = 380

    # Calculate costs
    high_risk_count = 47
    predicted_burnouts = int(high_risk_count * 0.35)  # 35% of high-risk

    cost_of_inaction = {
        "current_month": {
            "turnover_replacement": 0,
            "productivity_loss": 0,
            "healthcare_costs": 0,
            "absenteeism": 0,
        },
        "next_quarter": {
            "turnover_replacement": predicted_burnouts
            * avg_salary
            * turnover_multiplier
            / 4,
            "productivity_loss": 136800,  # 20% productivity loss for affected employees
            "healthcare_costs": 52800,
            "absenteeism": 26400,
        },
        "next_year": {
            "turnover_replacement": predicted_burnouts
            * avg_salary
            * turnover_multiplier,
            "productivity_loss": 136800 * 4,
            "healthcare_costs": 52800 * 4,
            "absenteeism": 26400 * 4,
        },
        "breakdown": {
            "turnover_replacement": predicted_burnouts
            * avg_salary
            * turnover_multiplier,
            "productivity_loss": 136800 * 4,
            "healthcare_costs": 52800 * 4,
            "absenteeism": 26400 * 4,
        },
    }

    # Sum annual cost
    cost_of_inaction["current_month"] = (
        cost_of_inaction["breakdown"]["turnover_replacement"] / 12
        + cost_of_inaction["breakdown"]["productivity_loss"] / 12
        + cost_of_inaction["breakdown"]["healthcare_costs"] / 12
        + cost_of_inaction["breakdown"]["absenteeism"] / 12
    )
    cost_of_inaction["next_quarter"] = (
        cost_of_inaction["breakdown"]["turnover_replacement"] / 4
        + cost_of_inaction["breakdown"]["productivity_loss"] / 4
        + cost_of_inaction["breakdown"]["healthcare_costs"] / 4
        + cost_of_inaction["breakdown"]["absenteeism"] / 4
    )
    cost_of_inaction["next_year"] = (
        cost_of_inaction["breakdown"]["turnover_replacement"]
        + cost_of_inaction["breakdown"]["productivity_loss"]
        + cost_of_inaction["breakdown"]["healthcare_costs"]
        + cost_of_inaction["breakdown"]["absenteeism"]
    )

    # Intervention costs
    cost_of_intervention = {
        "program_costs": 180000,  # Wellness programs, EAP, etc.
        "implementation_costs": 45000,  # Training, setup, etc.
        "total": 225000,
    }

    # Projected savings (70% reduction in costs with intervention)
    savings_factor = 0.7
    projected_savings = {
        "turnover_avoided": cost_of_inaction["breakdown"]["turnover_replacement"]
        * savings_factor,
        "productivity_gained": cost_of_inaction["breakdown"]["productivity_loss"]
        * savings_factor,
        "healthcare_reduced": cost_of_inaction["breakdown"]["healthcare_costs"]
        * savings_factor,
        "total": sum(
            [
                cost_of_inaction["breakdown"]["turnover_replacement"],
                cost_of_inaction["breakdown"]["productivity_loss"],
                cost_of_inaction["breakdown"]["healthcare_costs"],
            ]
        )
        * savings_factor,
    }

    # Calculate ROI
    net_benefit = projected_savings["total"] - cost_of_intervention["total"]
    roi = (net_benefit / cost_of_intervention["total"]) * 100

    return {
        "cost_of_inaction": cost_of_inaction,
        "cost_of_intervention": cost_of_intervention,
        "projected_savings": projected_savings,
        "roi": roi,
    }
