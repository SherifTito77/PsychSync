"""
Enhanced Clinical Analytics API Endpoints

Integration of enhanced analytics service with FastAPI
Provides comprehensive analytics for clinical screening data
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.clinical.enhanced_analytics import (
    EnhancedClinicalAnalytics,
    generate_analytics_report,
)

router = APIRouter(prefix="/analytics", tags=["enhanced-analytics"])


@router.get("/user/{user_id}/summary")
async def get_user_analytics_summary(
    user_id: str,
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get comprehensive analytics summary for user

    Includes:
    - Trends for all screening types
    - Comparative metrics
    - Outcome measurements
    - Population health context
    """
    # Verify authorization (user can only access own data unless clinician/admin)
    if current_user.id != user_id and current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's analytics",
        )

    try:
        report = await generate_analytics_report(db, user_id, org_id)
        return {
            "status": "success",
            "data": report,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}",
        )


@router.get("/user/{user_id}/trends/{screening_type}")
async def get_user_trends(
    user_id: str,
    screening_type: str,
    weeks: int = 12,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get longitudinal trend analysis for specific screening

    Returns:
    - Trend direction (improving, stable, declining)
    - Change percentage
    - Statistical confidence
    - Clinical recommendations
    """
    if current_user.id != user_id and current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    analytics = EnhancedClinicalAnalytics(db)
    trends = await analytics.get_user_trends(user_id, screening_type, weeks)

    if not trends:
        return {
            "status": "insufficient_data",
            "message": "Not enough data points for trend analysis",
            "data": None,
        }

    return {
        "status": "success",
        "screening_type": screening_type,
        "analysis_period": f"{weeks} weeks",
        "data": {
            "direction": trends.direction.value,
            "change_percentage": trends.change_percentage,
            "confidence": trends.confidence,
            "slope": trends.slope,
            "r_squared": trends.r_squared,
            "recommendation": trends.recommendation,
        },
    }


@router.get("/user/{user_id}/comparison/{screening_type}")
async def get_comparative_metrics(
    user_id: str,
    screening_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Compare user's scores to population

    Returns:
    - User's average score
    - Population average
    - Percentile rank
    - Z-score
    - Interpretation
    """
    if current_user.id != user_id and current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    analytics = EnhancedClinicalAnalytics(db)
    comparative = await analytics.get_comparative_metrics(user_id, screening_type)

    if not comparative:
        return {
            "status": "no_data",
            "message": "No screening data available for comparison",
        }

    return {
        "status": "success",
        "screening_type": screening_type,
        "data": {
            "user_average": comparative.user_average,
            "population_average": comparative.population_average,
            "percentile_rank": comparative.percentile_rank,
            "z_score": comparative.z_score,
            "interpretation": comparative.interpretation,
        },
    }


@router.get("/user/{user_id}/outcomes/{screening_type}")
async def get_outcome_metrics(
    user_id: str,
    screening_type: str,
    baseline_days: int = 30,
    follow_up_days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Measure clinical outcomes over time

    Returns:
    - Baseline score
    - Current score
    - Change amount
    - Clinical significance
    - Achievement status
    """
    if current_user.id != user_id and current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    analytics = EnhancedClinicalAnalytics(db)
    outcomes = await analytics.get_outcome_metrics(
        user_id, screening_type, baseline_days, follow_up_days
    )

    if not outcomes:
        return {
            "status": "insufficient_data",
            "message": "Need both baseline and follow-up data",
            "data": None,
        }

    return {
        "status": "success",
        "screening_type": screening_type,
        "baseline_period_days": baseline_days,
        "follow_up_period_days": follow_up_days,
        "data": {
            "baseline_score": outcomes.baseline_score,
            "current_score": outcomes.current_score,
            "change": outcomes.change,
            "clinically_significant": outcomes.clinically_significant,
            "minimal_important_change": outcomes.minimal_important_change,
            "achieved": outcomes.achieved,
        },
    }


@router.get("/organization/{org_id}/population-health")
async def get_population_health(
    org_id: str,
    screening_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get population health metrics for organization

    Returns:
    - Completion rates
    - Risk distribution
    - Crisis alerts
    - Organization-level insights
    """
    # Verify user belongs to organization
    if current_user.org_id != org_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this organization's data",
        )

    analytics = EnhancedClinicalAnalytics(db)
    metrics = await analytics.get_population_health_metrics(org_id, screening_type)

    return {
        "status": "success",
        "organization_id": org_id,
        "screening_type": screening_type or "all",
        "data": metrics,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/organization/{org_id}/dashboard")
async def get_analytics_dashboard(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get complete analytics dashboard for organization

    Combines:
    - Population health metrics
    - Top trends across organization
    - Risk distribution
    - Completion rates
    - Recent activity
    """
    if current_user.org_id != org_id and current_user.role not in [
        "clinician",
        "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    analytics = EnhancedClinicalAnalytics(db)

    # Get population health
    population_health = await analytics.get_population_health_metrics(org_id)

    return {
        "status": "success",
        "organization_id": org_id,
        "dashboard": {
            "population_health": population_health,
            "summary": {
                "total_screenings": population_health.get("total_screenings", 0),
                "completion_rate": population_health.get("completion_rate", 0),
                "high_risk_count": population_health.get("high_risk_count", 0),
                "crisis_alerts_last_30_days": population_health.get(
                    "crisis_alerts_last_30_days", 0
                ),
            },
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
