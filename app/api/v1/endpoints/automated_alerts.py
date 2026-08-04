"""
Automated Clinical Alerts API Endpoints

Provides endpoints for:
- Managing clinical alerts (acknowledge, resolve)
- Retrieving unresolved alerts
- Alert history and details
- Triggering scheduled alert checks

Access: Clinicians and Administrators only
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db as get_async_db, get_current_user
from app.db.models.clinical_screening import ClinicalAlert
from app.db.models.notification import NotificationPreference
from app.db.models.organizations import Organization
from app.db.models.user import User
from app.services.clinical.automated_alert_service import (
    AlertSeverity,
    AlertType,
    AutomatedAlertService,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/automated-alerts", tags=["automated-alerts"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class AlertTriggerRequest(BaseModel):
    """Request schema for manually triggering an alert"""

    user_id: UUID = Field(..., description="User ID who triggered the alert")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(
        ..., description="Severity level (critical, high, moderate, low)"
    )
    message: str = Field(
        ..., min_length=10, max_length=2000, description="Alert message"
    )
    metadata: Optional[Dict] = Field(
        default_factory=dict, description="Additional alert data"
    )


class AcknowledgeAlertRequest(BaseModel):
    """Request schema for acknowledging an alert"""

    notes: Optional[str] = Field(
        None, max_length=1000, description="Acknowledgment notes"
    )


class ResolveAlertRequest(BaseModel):
    """Request schema for resolving an alert"""

    resolution_notes: str = Field(
        ..., min_length=10, max_length=2000, description="Resolution details"
    )
    resolution_status: str = Field(
        default="resolved", description="Final status (resolved, escalated, etc.)"
    )


class AlertResponse(BaseModel):
    """Response schema for alert data"""

    id: UUID
    user_id: UUID
    org_id: UUID
    alert_type: str
    severity: str
    alert_message: str
    acknowledged: bool
    acknowledged_by: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    resolution_status: str
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    escalated: bool
    escalation_level: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict] = None

    class Config:
        from_attributes = True


class UnresolvedAlertsResponse(BaseModel):
    """Response schema for unresolved alerts list"""

    alerts: List[AlertResponse]
    total_count: int
    critical_count: int
    high_count: int
    moderate_count: int


class AlertHistoryResponse(BaseModel):
    """Response schema for alert history"""

    alerts: List[AlertResponse]
    total_count: int
    resolved_count: int
    escalated_count: int
    date_range: Dict[str, datetime]


class AlertCheckResponse(BaseModel):
    """Response schema for alert check trigger"""

    success: bool
    alerts_triggered: int
    breakdown: Dict[str, int] = Field(
        default_factory=dict, description="Alerts by type"
    )
    message: str


# =============================================================================
# Helper Functions
# =============================================================================


async def verify_clinician_or_admin(current_user: User) -> None:
    """Verify user has clinician or admin role"""

    if current_user.role not in ["clinician", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Automated alert management requires clinician or admin role",
        )


def get_alert_service() -> AutomatedAlertService:
    """Get alert service instance"""

    return AutomatedAlertService()


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/unresolved", response_model=UnresolvedAlertsResponse)
async def get_unresolved_alerts(
    severity: Optional[str] = Query(
        None, description="Filter by severity (critical, high, moderate, low)"
    ),
    limit: int = Query(
        50, ge=1, le=200, description="Maximum number of alerts to return"
    ),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all unresolved clinical alerts

    Returns alerts sorted by severity (critical first) and creation time (newest first).
    Used by clinicians to see which users require attention.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Get unresolved alerts
        alerts = await alert_service.get_unresolved_alerts(
            org_id=str(current_user.org_id) if current_user.org_id else None,
            severity=severity,
            limit=limit,
        )

        # Convert to response format
        alert_responses = [AlertResponse(**alert) for alert in alerts]

        # Count by severity
        critical_count = sum(1 for a in alert_responses if a.severity == "critical")
        high_count = sum(1 for a in alert_responses if a.severity == "high")
        moderate_count = sum(1 for a in alert_responses if a.severity == "moderate")

        logger.info(
            f"Retrieved {len(alert_responses)} unresolved alerts for {current_user.email}"
        )

        return UnresolvedAlertsResponse(
            alerts=alert_responses,
            total_count=len(alert_responses),
            critical_count=critical_count,
            high_count=high_count,
            moderate_count=moderate_count,
        )

    except Exception as e:
        logger.error(f"Error retrieving unresolved alerts: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alerts: {str(e)}"
        )


@router.get("/history", response_model=AlertHistoryResponse)
async def get_alert_history(
    user_id: Optional[UUID] = Query(None, description="Filter by specific user"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=200, description="Maximum alerts to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get alert history for the organization or specific user

    Useful for reviewing past alerts, identifying patterns, and quality improvement.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Build query
        query = select(ClinicalAlert).where(
            ClinicalAlert.created_at >= start_date, ClinicalAlert.created_at <= end_date
        )

        # Filter by organization
        if current_user.org_id:
            query = query.where(ClinicalAlert.org_id == current_user.org_id)

        # Filter by specific user
        if user_id:
            query = query.where(ClinicalAlert.user_id == user_id)

        # Order by creation time (newest first)
        query = query.order_by(ClinicalAlert.created_at.desc()).limit(limit)

        # Execute query
        result = await db.execute(query)
        alerts = result.scalars().all()

        # Convert to response format
        alert_responses = [AlertResponse.model_validate(alert) for alert in alerts]

        # Count statistics
        resolved_count = sum(
            1 for a in alert_responses if a.resolution_status == "resolved"
        )
        escalated_count = sum(1 for a in alert_responses if a.escalated)

        logger.info(
            f"Retrieved {len(alert_responses)} historical alerts for {current_user.email} "
            f"({days_back} days)"
        )

        return AlertHistoryResponse(
            alerts=alert_responses,
            total_count=len(alert_responses),
            resolved_count=resolved_count,
            escalated_count=escalated_count,
            date_range={"start": start_date, "end": end_date},
        )

    except Exception as e:
        logger.error(f"Error retrieving alert history: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert history: {str(e)}"
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_details(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get detailed information about a specific alert

    Includes full alert message, metadata, acknowledgment/resolution details.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    try:
        # Get alert
        query = select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        # Verify access (same organization)
        if current_user.org_id and alert.org_id != current_user.org_id:
            raise HTTPException(status_code=403, detail="Access denied to this alert")

        logger.info(f"Retrieved details for alert {alert_id} by {current_user.email}")

        return AlertResponse.model_validate(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert details: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert details: {str(e)}"
        )


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    request: AcknowledgeAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Acknowledge a clinical alert

    Marks the alert as acknowledged by the current clinician.
    This indicates the clinician has seen the alert and is taking action.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Acknowledge alert
        success = await alert_service.acknowledge_alert(
            alert_id=str(alert_id),
            clinician_id=str(current_user.id),
            notes=request.notes,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Alert not found or already acknowledged"
            )

        # Get updated alert
        query = select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one()

        logger.info(
            f"Alert {alert_id} acknowledged by {current_user.email}"
            + (f" with notes: {request.notes}" if request.notes else "")
        )

        return AlertResponse.model_validate(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    request: ResolveAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Resolve a clinical alert

    Marks the alert as resolved with resolution notes.
    This indicates the clinician has addressed the issue.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Resolve alert
        success = await alert_service.resolve_alert(
            alert_id=str(alert_id),
            clinician_id=str(current_user.id),
            resolution_notes=request.resolution_notes,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Alert not found or already resolved"
            )

        # Get updated alert
        query = select(ClinicalAlert).where(ClinicalAlert.id == alert_id)
        result = await db.execute(query)
        alert = result.scalar_one()

        logger.info(
            f"Alert {alert_id} resolved by {current_user.email}: {request.resolution_notes[:100]}..."
        )

        return AlertResponse.model_validate(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve alert: {str(e)}"
        )


@router.post("/check-predictions", response_model=AlertCheckResponse)
async def trigger_prediction_checks(
    prediction_types: Optional[List[str]] = Query(
        None, description="Specific prediction types to check"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger ML prediction-based alert checks

    Runs the ML risk prediction models and generates alerts for high-risk users.
    Can be called manually or by scheduled background jobs.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Run ML prediction alerts
        triggers = await alert_service.run_ml_prediction_alerts(
            org_id=str(current_user.org_id) if current_user.org_id else None,
            prediction_types=prediction_types,
        )

        # Count by type
        breakdown = {}
        for trigger in triggers:
            breakdown[trigger.trigger_type] = breakdown.get(trigger.trigger_type, 0) + 1

        logger.info(
            f"ML prediction check triggered by {current_user.email}: "
            f"{len(triggers)} alerts generated"
        )

        return AlertCheckResponse(
            success=True,
            alerts_triggered=len(triggers),
            breakdown=breakdown,
            message=f"Checked {len(triggers)} users for ML-based risks",
        )

    except Exception as e:
        logger.error(f"Error running prediction checks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run prediction checks: {str(e)}"
        )


@router.post("/check-trends", response_model=AlertCheckResponse)
async def trigger_trend_checks(
    current_user: User = Depends(get_current_user),
):
    """
    Trigger trend-based alert checks

    Analyzes user assessment trends and generates alerts for worsening patterns.
    Can be called manually or by scheduled background jobs.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Run trend alerts
        triggers = await alert_service.check_trending_alerts(
            org_id=str(current_user.org_id) if current_user.org_id else None
        )

        # Count by type
        breakdown = {}
        for trigger in triggers:
            breakdown[trigger.trigger_type] = breakdown.get(trigger.trigger_type, 0) + 1

        logger.info(
            f"Trend check triggered by {current_user.email}: {len(triggers)} alerts generated"
        )

        return AlertCheckResponse(
            success=True,
            alerts_triggered=len(triggers),
            breakdown=breakdown,
            message=f"Analyzed user trends and generated {len(triggers)} alerts",
        )

    except Exception as e:
        logger.error(f"Error running trend checks: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to run trend checks: {str(e)}"
        )


@router.post("/trigger", response_model=AlertCheckResponse)
async def trigger_manual_alert(
    request: AlertTriggerRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a clinical alert

    Allows clinicians to manually create alerts for users requiring attention.
    Useful for situations not caught by automated systems.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    alert_service = get_alert_service()

    try:
        # Import AlertTrigger and create trigger
        from app.services.clinical.automated_alert_service import AlertTrigger

        trigger = AlertTrigger(
            trigger_type=AlertType(request.alert_type),
            severity=AlertSeverity(request.severity),
            user_id=str(request.user_id),
            org_id=str(current_user.org_id) if current_user.org_id else None,
            message=request.message,
            metadata=request.metadata,
        )

        # Process alert
        await alert_service._process_alerts([trigger])

        logger.info(
            f"Manual alert triggered by {current_user.email} for user {request.user_id}: "
            f"{request.alert_type}"
        )

        return AlertCheckResponse(
            success=True,
            alerts_triggered=1,
            breakdown={request.alert_type: 1},
            message="Manual alert created successfully",
        )

    except Exception as e:
        logger.error(f"Error triggering manual alert: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger alert: {str(e)}"
        )


@router.get("/stats/overview")
async def get_alert_statistics(
    days_back: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get alert statistics and overview metrics

    Useful for dashboards and quality improvement reporting.

    Requires: Clinician or Admin role
    """

    await verify_clinician_or_admin(current_user)

    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Build base query
        base_query = select(ClinicalAlert).where(
            ClinicalAlert.created_at >= start_date, ClinicalAlert.created_at <= end_date
        )

        # Filter by organization
        if current_user.org_id:
            base_query = base_query.where(ClinicalAlert.org_id == current_user.org_id)

        # Total alerts
        result = await db.execute(select(ClinicalAlert).where(base_query.whereclause))
        total_count = len(result.scalars().all())

        # Unresolved alerts
        unresolved_query = base_query.where(
            ClinicalAlert.resolution_status == "pending"
        )
        result = await db.execute(unresolved_query)
        unresolved_count = len(result.scalars().all())

        # By severity
        critical_query = base_query.where(ClinicalAlert.severity == "critical")
        result = await db.execute(critical_query)
        critical_count = len(result.scalars().all())

        high_query = base_query.where(ClinicalAlert.severity == "high")
        result = await db.execute(high_query)
        high_count = len(result.scalars().all())

        # By type
        crisis_query = base_query.where(
            ClinicalAlert.alert_type.in_(
                ["crisis_suicide", "crisis_self_harm", "crisis_severe"]
            )
        )
        result = await db.execute(crisis_query)
        crisis_count = len(result.scalars().all())

        # Acknowledgment rate
        acknowledged_query = base_query.where(ClinicalAlert.acknowledged == True)
        result = await db.execute(acknowledged_query)
        acknowledged_count = len(result.scalars().all())

        acknowledgment_rate = (
            (acknowledged_count / total_count * 100) if total_count > 0 else 0
        )

        # Resolution rate
        resolved_query = base_query.where(ClinicalAlert.resolution_status == "resolved")
        result = await db.execute(resolved_query)
        resolved_count = len(result.scalars().all())

        resolution_rate = (resolved_count / total_count * 100) if total_count > 0 else 0

        # Average resolution time (for resolved alerts)
        resolved_with_time_query = base_query.where(
            ClinicalAlert.resolution_status == "resolved",
            ClinicalAlert.resolved_at.isnot(None),
        )
        result = await db.execute(resolved_with_time_query)
        resolved_alerts = result.scalars().all()

        if resolved_alerts:
            resolution_times = [
                (a.resolved_at - a.created_at).total_seconds() for a in resolved_alerts
            ]
            avg_resolution_hours = sum(resolution_times) / len(resolution_times) / 3600
        else:
            avg_resolution_hours = 0

        logger.info(
            f"Alert statistics retrieved for {current_user.email}: {days_back} days"
        )

        return {
            "period_days": days_back,
            "total_alerts": total_count,
            "unresolved_count": unresolved_count,
            "by_severity": {
                "critical": critical_count,
                "high": high_count,
                "moderate": total_count - critical_count - high_count,
            },
            "crisis_alerts": crisis_count,
            "acknowledgment_rate": round(acknowledgment_rate, 1),
            "resolution_rate": round(resolution_rate, 1),
            "avg_resolution_hours": round(avg_resolution_hours, 1),
        }

    except Exception as e:
        logger.error(f"Error retrieving alert statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve alert statistics: {str(e)}"
        )
