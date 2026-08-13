"""
Population Health Analytics API Endpoints

Provides endpoints for:
- Population metrics and statistics
- High-risk user identification
- Treatment outcome tracking
- Time series trends
- Demographic breakdowns

Access restricted to clinicians and administrators.
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db as get_async_db, get_current_user
from app.core.logging_config import logger
from app.db.models.user import User
from app.services.clinical.population_health_service import (
    HighRiskUser,
    PopulationHealthService,
    PopulationMetrics,
    TimeSeriesData,
    TreatmentOutcome,
)

router = APIRouter(prefix="/population-health", tags=["population-health"])


# =============================================================================
# Request/Response Models
# =============================================================================


class PopulationMetricsResponse(BaseModel):
    """Response model for population metrics"""

    total_users: int
    active_assessments: int
    average_scores: dict[str, float]
    risk_distribution: dict[str, int]
    crisis_count: int
    high_risk_count: int
    moderate_risk_count: int
    low_risk_count: int


class HighRiskUserResponse(BaseModel):
    """Response model for high-risk user"""

    user_id: str
    risk_level: str
    prediction_type: str
    current_score: float
    trend: str
    last_assessment: str
    factors: dict[str, Any]


class TreatmentOutcomeResponse(BaseModel):
    """Response model for treatment outcome"""

    outcome_type: str
    count: int
    percentage: float
    avg_score_change: Optional[float] = None


class TimeSeriesResponse(BaseModel):
    """Response model for time series data"""

    period: str
    avg_score: float
    assessment_count: int
    high_risk_count: int
    crisis_count: int


class SummaryStatisticsResponse(BaseModel):
    """Response model for summary statistics"""

    population_metrics: PopulationMetricsResponse
    high_risk_users: dict[str, Any]
    treatment_outcomes: list[TreatmentOutcomeResponse]
    trend_direction: str
    crisis_rate: float
    high_risk_rate: float


# =============================================================================
# Population Metrics Endpoints
# =============================================================================


@router.get("/metrics", response_model=PopulationMetricsResponse)
async def get_population_metrics(
    assessment_types: Optional[str] = Query(
        None, description="Comma-separated assessment types (e.g., BDI2,BAI,GAD7)"
    ),
    days_back: int = Query(30, ge=7, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get aggregate population metrics

    Returns:
    - Total unique users
    - Active assessment count
    - Average scores by assessment type
    - Risk level distribution
    - Crisis and high-risk counts

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Population health data requires admin privileges",
            )

        # Parse assessment types
        types_list = assessment_types.split(",") if assessment_types else None

        # Initialize service
        service = PopulationHealthService(db)

        # Get metrics
        metrics = await service.get_population_metrics(
            assessment_types=types_list, days_back=days_back
        )

        logger.info(
            f"Population metrics retrieved by {current_user.email}: "
            f"{metrics.total_users} users, {metrics.active_assessments} assessments"
        )

        return PopulationMetricsResponse(**metrics.to_dict())

    except Exception as e:
        logger.error(f"Error retrieving population metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# High-Risk User Endpoints
# =============================================================================


@router.get("/high-risk-users", response_model=List[HighRiskUserResponse])
async def get_high_risk_users(
    assessment_types: Optional[str] = Query(
        None, description="Comma-separated assessment types"
    ),
    days_back: int = Query(30, ge=7, le=180, description="Lookback period in days"),
    min_assessments: int = Query(
        2, ge=1, le=10, description="Minimum assessments per user"
    ),
    limit: int = Query(50, ge=1, le=200, description="Maximum users to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Identify high-risk users requiring attention

    Criteria:
    - Crisis alerts in recent assessments
    - High or critical risk levels
    - Worsening trend (>5 point increase)
    - High scores (≥40 for BDI-II/BAI)

    Returns users sorted by:
    1. Risk level (critical > high > moderate > low)
    2. Current score (descending)

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="High-risk user data requires admin privileges",
            )

        # Parse assessment types
        types_list = assessment_types.split(",") if assessment_types else None

        # Initialize service
        service = PopulationHealthService(db)

        # Get high-risk users
        high_risk_users = await service.identify_high_risk_users(
            assessment_types=types_list,
            days_back=days_back,
            min_assessments=min_assessments,
            limit=limit,
        )

        logger.info(
            f"High-risk user list retrieved by {current_user.email}: "
            f"{len(high_risk_users)} users identified"
        )

        # Log warning if critical users found
        critical_count = sum(1 for u in high_risk_users if u.risk_level == "critical")
        if critical_count > 0:
            logger.warning(
                f"⚠️ {critical_count} critical-risk users identified for review by {current_user.email}"
            )

        return [HighRiskUserResponse(**u.to_dict()) for u in high_risk_users]

    except Exception as e:
        logger.error(f"Error retrieving high-risk users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Treatment Outcome Endpoints
# =============================================================================


@router.get("/treatment-outcomes", response_model=List[TreatmentOutcomeResponse])
async def get_treatment_outcomes(
    assessment_type: str = Query("BDI2", description="Assessment type to analyze"),
    days_back: int = Query(90, ge=30, le=365, description="Lookback period in days"),
    min_assessments: int = Query(
        4, ge=2, le=10, description="Minimum assessments per user"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Analyze treatment outcomes across population

    Outcome Classifications:
    - full_response: ≥50% score reduction
    - partial_response: 25-50% score reduction
    - non_response: <25% score reduction
    - deterioration: Score worsening (>10% increase)

    Includes:
    - Count of users in each outcome category
    - Percentage distribution
    - Average score change per category

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Treatment outcome data requires admin privileges",
            )

        # Initialize service
        service = PopulationHealthService(db)

        # Get treatment outcomes
        outcomes = await service.get_treatment_outcomes(
            assessment_type=assessment_type,
            days_back=days_back,
            min_assessments=min_assessments,
        )

        logger.info(
            f"Treatment outcomes retrieved by {current_user.email} for {assessment_type}: "
            f"{len(outcomes)} outcome categories"
        )

        return [TreatmentOutcomeResponse(**o.to_dict()) for o in outcomes]

    except Exception as e:
        logger.error(f"Error retrieving treatment outcomes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Time Series Trend Endpoints
# =============================================================================


@router.get("/trends", response_model=List[TimeSeriesResponse])
async def get_time_series_trends(
    assessment_type: str = Query("BDI2", description="Assessment type to analyze"),
    days_back: int = Query(90, ge=30, le=365, description="Total lookback period"),
    interval_days: int = Query(
        7, ge=1, le=30, description="Size of each time bucket (days)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get time series data for trend visualization

    Returns metrics for each time interval:
    - Period label (date range)
    - Average score
    - Assessment count
    - High-risk count
    - Crisis count

    Useful for:
    - Line charts showing score trends over time
    - Bar charts comparing periods
    - Identifying seasonal patterns
    - Monitoring intervention effectiveness

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Time series data requires admin privileges",
            )

        # Initialize service
        service = PopulationHealthService(db)

        # Get time series data
        trends = await service.get_time_series_trends(
            assessment_type=assessment_type,
            days_back=days_back,
            interval_days=interval_days,
        )

        logger.info(
            f"Time series trends retrieved by {current_user.email} for {assessment_type}: "
            f"{len(trends)} data points"
        )

        return [TimeSeriesResponse(**t.to_dict()) for t in trends]

    except Exception as e:
        logger.error(f"Error retrieving time series trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Demographic Breakdown Endpoints
# =============================================================================


@router.get("/demographic-breakdown")
async def get_demographic_breakdown(
    group_by: str = Query(
        "assessment_type",
        description="Field to group by (assessment_type, risk_level)",
    ),
    days_back: int = Query(30, ge=7, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get breakdown by demographic or assessment type

    Returns statistics for each group:
    - Count of assessments
    - Average score
    - Min/max scores
    - Crisis count and rate

    Group by options:
    - assessment_type: Statistics by assessment instrument
    - risk_level: Statistics by risk level

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Demographic breakdown requires admin privileges",
            )

        # Initialize service
        service = PopulationHealthService(db)

        # Get breakdown
        breakdown = await service.get_demographic_breakdown(
            group_by=group_by, days_back=days_back
        )

        logger.info(
            f"Demographic breakdown retrieved by {current_user.email}: "
            f"grouped by {group_by}, {len(breakdown)} groups"
        )

        return {
            "group_by": group_by,
            "days_back": days_back,
            "breakdown": breakdown,
            "total_groups": len(breakdown),
        }

    except Exception as e:
        logger.error(f"Error retrieving demographic breakdown: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Summary Statistics Endpoint
# =============================================================================


@router.get("/summary", response_model=SummaryStatisticsResponse)
async def get_summary_statistics(
    days_back: int = Query(30, ge=7, le=90, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get executive summary statistics for dashboard

    Comprehensive overview including:
    - Population metrics
    - Top 10 high-risk users
    - Treatment outcome distribution
    - Recent trend direction
    - Crisis and high-risk rates

    Perfect for:
    - Executive dashboards
    - Daily monitoring views
    - Quick overviews

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Summary statistics requires admin privileges",
            )

        # Initialize service
        service = PopulationHealthService(db)

        # Get summary
        summary = await service.get_summary_statistics(days_back=days_back)

        logger.info(
            f"Summary statistics retrieved by {current_user.email}: "
            f"trend={summary['trend_direction']}, "
            f"crisis_rate={summary['crisis_rate']}%, "
            f"high_risk_users={summary['high_risk_users']['count']}"
        )

        # Log warnings for concerning metrics
        if summary["crisis_rate"] > 5.0:
            logger.warning(
                f"⚠️ High crisis rate detected: {summary['crisis_rate']}% "
                f"(reviewed by {current_user.email})"
            )

        if summary["trend_direction"] == "worsening":
            logger.warning(
                f"⚠️ Worsening population trend detected "
                f"(reviewed by {current_user.email})"
            )

        return SummaryStatisticsResponse(**summary)

    except Exception as e:
        logger.error(f"Error retrieving summary statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Assessment Type Comparison
# =============================================================================


@router.get("/assessment-comparison")
async def compare_assessment_types(
    days_back: int = Query(30, ge=7, le=365, description="Lookback period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Compare metrics across different assessment types

    Returns side-by-side comparison of:
    - Assessment counts
    - Average scores
    - Risk distributions
    - Crisis rates

    Useful for:
    - Understanding which assessments show most concern
    - Resource allocation decisions
    - Program evaluation

    Access: Clinicians and Administrators only
    """
    try:
        # Verify authorization
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Assessment comparison requires admin privileges",
            )

        # Initialize service
        service = PopulationHealthService(db)

        # Get metrics for each major assessment type
        assessment_types = ["BDI2", "BAI", "GAD7", "PHQ9", "LSAS"]
        comparison = {}

        for assess_type in assessment_types:
            try:
                metrics = await service.get_population_metrics(
                    assessment_types=[assess_type], days_back=days_back
                )

                comparison[assess_type] = {
                    "name": _get_assessment_name(assess_type),
                    "active_assessments": metrics.active_assessments,
                    "average_score": metrics.average_scores.get(assess_type, 0),
                    "crisis_count": metrics.crisis_count,
                    "high_risk_count": metrics.high_risk_count,
                    "crisis_rate": round(
                        (
                            metrics.crisis_count / metrics.active_assessments * 100
                            if metrics.active_assessments > 0
                            else 0
                        ),
                        2,
                    ),
                }
            except Exception as e:
                logger.warning(f"Could not get metrics for {assess_type}: {e}")
                continue

        logger.info(
            f"Assessment comparison retrieved by {current_user.email}: "
            f"{len(comparison)} assessment types compared"
        )

        return {
            "assessment_types": comparison,
            "days_back": days_back,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error retrieving assessment comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Helper Functions
# =============================================================================


def _get_assessment_name(assessment_type: str) -> str:
    """Get full name for assessment type"""
    names = {
        "BDI2": "Beck Depression Inventory-II",
        "BAI": "Beck Anxiety Inventory",
        "GAD7": "Generalized Anxiety Disorder-7",
        "PHQ9": "Patient Health Questionnaire-9",
        "LSAS": "Liebowitz Social Anxiety Scale",
        "EAT26": "Eating Attitudes Test-26",
        "YBOCS": "Yale-Brown Obsessive Compulsive Scale",
    }
    return names.get(assessment_type, assessment_type)
