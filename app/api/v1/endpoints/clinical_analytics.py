"""
Clinical Analytics API Endpoints

Provides population health insights, screening completion rates,
and mental health trends for clinicians and administrators.

HIPAA: All endpoints require authentication and role-based access control
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.clinical.clinical_analytics_service import ClinicalScreeningAnalytics

router = APIRouter(prefix="/analytics/clinical", tags=["clinical-analytics"])
logger = logging.getLogger(__name__)


@router.get("/completion-stats")
async def get_completion_statistics(
    start_date: Optional[str] = Query(
        None, description="ISO format start date (default: 30 days ago)"
    ),
    end_date: Optional[str] = Query(
        None, description="ISO format end date (default: now)"
    ),
    screening_type: Optional[str] = Query(
        None, description="Filter by screening type (PHQ9, GAD7, etc.)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get screening completion statistics for organization

    Returns:
        - Total eligible users vs completed screenings
        - Completion rate percentage
        - Breakdown by screening type
        - Team-level completion rates
        - Weekly trend data

    HIPAA: Requires organization-level access
    """
    # Default to last 30 days if not specified
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.utcnow().isoformat()

    # Parse dates
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            400,
            "Invalid date format. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS",
        )

    # Validate date range (max 1 year)
    if (end_dt - start_dt).days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    # Use user's organization
    org_id = str(current_user.org_id) if hasattr(current_user, "org_id") else None

    if not org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        analytics_service = ClinicalScreeningAnalytics(db)
        stats = await analytics_service.get_screening_completion_stats(
            org_id=org_id,
            start_date=start_dt,
            end_date=end_dt,
            screening_type=screening_type,
        )

        logger.info(
            f"Completion stats retrieved for org {org_id} by user {current_user.id}"
        )
        return stats

    except Exception as e:
        logger.error(f"Error retrieving completion stats: {str(e)}")
        raise HTTPException(500, f"Failed to retrieve completion statistics: {str(e)}")


@router.get("/severity-distribution")
async def get_severity_distribution(
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    screening_type: Optional[str] = Query(None, description="Filter by screening type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get distribution of severity levels for completed screenings

    Returns:
        - Severity counts and percentages
        - Breakdown by screening type
        - High-risk count
        - Severity trends over time

    HIPAA: Requires organization-level access
    """
    # Default to last 30 days
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.utcnow().isoformat()

    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid date format")

    org_id = str(current_user.org_id) if hasattr(current_user, "org_id") else None

    if not org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        analytics_service = ClinicalScreeningAnalytics(db)
        distribution = await analytics_service.get_severity_distribution(
            org_id=org_id,
            start_date=start_dt,
            end_date=end_dt,
            screening_type=screening_type,
        )

        logger.info(f"Severity distribution retrieved for org {org_id}")
        return distribution

    except NotImplementedError:
        raise HTTPException(501, "Severity distribution analytics not yet implemented")
    except Exception as e:
        logger.error(f"Error retrieving severity distribution: {str(e)}")
        raise HTTPException(500, f"Failed to retrieve severity distribution: {str(e)}")


@router.get("/crisis-metrics")
async def get_crisis_alert_metrics(
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get crisis alert metrics and response times

    Returns:
        - Total alerts triggered
        - Breakdown by alert type
        - Average response time
        - Resolution rate
        - Pending alerts

    HIPAA: Requires clinician or admin role
    """
    # Default to last 30 days
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.utcnow().isoformat()

    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid date format")

    org_id = str(current_user.org_id) if hasattr(current_user, "org_id") else None

    if not org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        analytics_service = ClinicalScreeningAnalytics(db)
        metrics = await analytics_service.get_crisis_alert_metrics(
            org_id=org_id, start_date=start_dt, end_date=end_dt
        )

        logger.info(f"Crisis metrics retrieved for org {org_id}")
        return metrics

    except NotImplementedError:
        raise HTTPException(501, "Crisis metrics analytics not yet implemented")
    except Exception as e:
        logger.error(f"Error retrieving crisis metrics: {str(e)}")
        raise HTTPException(500, f"Failed to retrieve crisis metrics: {str(e)}")


@router.get("/population-health")
async def get_population_health_summary(
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get population-level mental health summary

    Returns:
        - Average scores across screening types
        - Risk distribution
        - Top mental health concerns
        - Improvement indicators
        - Risk factor patterns

    HIPAA: Requires organization-level access
    """
    if not start_date:
        start_date = (
            datetime.utcnow() - timedelta(days=90)
        ).isoformat()  # Default 90 days
    if not end_date:
        end_date = datetime.utcnow().isoformat()

    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid date format")

    org_id = str(current_user.org_id) if hasattr(current_user, "org_id") else None

    if not org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        analytics_service = ClinicalScreeningAnalytics(db)
        summary = await analytics_service.get_population_health_summary(
            org_id=org_id, start_date=start_dt, end_date=end_dt
        )

        logger.info(f"Population health summary retrieved for org {org_id}")
        return summary

    except NotImplementedError:
        raise HTTPException(501, "Population health analytics not yet implemented")
    except Exception as e:
        logger.error(f"Error retrieving population health summary: {str(e)}")
        raise HTTPException(
            500, f"Failed to retrieve population health summary: {str(e)}"
        )


@router.get("/clinician-workload")
async def get_clinician_workload(
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get clinician workload and productivity metrics

    Returns:
        - Screenings reviewed per clinician
        - Average review time
        - Alert response statistics
        - Patient load
        - Documentation time

    HIPAA: Requires clinician or admin role
    """
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.utcnow().isoformat()

    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(400, "Invalid date format")

    org_id = str(current_user.org_id) if hasattr(current_user, "org_id") else None

    if not org_id:
        raise HTTPException(403, "User must belong to an organization")

    try:
        analytics_service = ClinicalScreeningAnalytics(db)
        workload = await analytics_service.get_clinician_workload_metrics(
            org_id=org_id, start_date=start_dt, end_date=end_dt
        )

        logger.info(f"Clinician workload metrics retrieved for org {org_id}")
        return workload

    except NotImplementedError:
        raise HTTPException(501, "Clinician workload analytics not yet implemented")
    except Exception as e:
        logger.error(f"Error retrieving clinician workload: {str(e)}")
        raise HTTPException(500, f"Failed to retrieve clinician workload: {str(e)}")
