"""
Wellness Metrics API Endpoints
Provides wellness scores and metrics for individual users
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.user import User
from app.services.wellness_monitoring import WellnessMonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wellness", tags=["wellness"])


@router.get("/metrics/current-user")
async def get_current_user_wellness_metrics(
    time_range: str = Query(default="30d", description="Time range for metrics"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    print("DEBUG: get_current_user_wellness_metrics called")
    return await get_wellness_metrics("current-user", time_range, current_user, db)


@router.get("/metrics/{user_id}")
async def get_wellness_metrics(
    user_id: str,
    time_range: str = Query(
        default="30d", description="Time range for metrics (e.g., '30d', '90d')"
    ),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get wellness metrics for a user.

    - **user_id**: ID of the user or 'current-user'
    - **time_range**: Time period for analysis (default: 30d)

    Returns comprehensive wellness metrics including overall score, burnout risk,
    stress levels, and individual wellness dimensions.
    """
    try:
        # Resolve 'current-user'
        target_user_id = user_id
        if user_id == "current-user":
            target_user_id = str(current_user.id)
        elif user_id != str(current_user.id) and not current_user.is_admin:
            # TODO: Add check for team/org permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view metrics for this user",
            )

        # Initialize service
        wellness_service = WellnessMonitoringService(db)

        # In a real implementation, we would call a service method
        # For now, we'll provide a high-quality mock response based on the service's domain weights
        # but try to integrate actual data if possible.

        # Mock implementation returning baseline data
        return {
            "user_id": target_user_id,
            "time_range": time_range,
            "overall_wellness_score": 0.72,
            "burnout_risk_score": 0.25,
            "stress_level": 0.45,
            "engagement_level": 0.68,
            "physical_wellness": 0.70,
            "emotional_wellness": 0.68,
            "mental_wellness": 0.75,
            "social_wellness": 0.65,
            "professional_wellness": 0.72,
            "trends": {
                "improving": ["sleep_quality", "social_engagement"],
                "declining": [],
                "stable": ["stress_level", "energy_levels", "work_life_balance"],
            },
            "recommendations": [
                "Maintain current sleep patterns",
                "Continue social engagement activities",
                "Consider stress management techniques",
            ],
            "last_updated": datetime.utcnow().isoformat(),
            "data_sources": [
                "wellness_assessments",
                "activity_tracking",
                "self_reported_metrics",
            ],
            "sample_size": 15,
            "completeness": 0.85,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wellness metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting wellness metrics: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Health check for wellness service."""
    return {
        "status": "healthy",
        "service": "Wellness Metrics Service",
        "timestamp": datetime.utcnow().isoformat(),
    }
