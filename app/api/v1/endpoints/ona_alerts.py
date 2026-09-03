# app/api/v1/endpoints/ona_alerts.py
"""
ONA Alert Endpoints

Trigger ONA alert checks and query network health alerts.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.communication_alerts import (
    AlertStatus,
    CommunicationAlert,
)
from app.services.ona_alert_monitor import ona_alert_monitor
from app.services.security import get_current_user

router = APIRouter(prefix="/ona-alerts", tags=["ona-alerts"])


@router.post("/{organization_id}/check", response_model=dict[str, Any])
async def trigger_ona_alert_check(
    organization_id: UUID,
    lookback_days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run ONA alert checks for an organization.
    Compares recent network snapshots and creates alerts for threshold breaches.
    """
    alerts = await ona_alert_monitor.check_organization(
        db, organization_id, lookback_days
    )
    return {
        "organization_id": str(organization_id),
        "alerts_created": len(alerts),
        "alerts": alerts,
    }


@router.get("/{organization_id}", response_model=dict[str, Any])
async def get_ona_alerts(
    organization_id: UUID,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get ONA-generated alerts for an organization.
    Filters to alerts created by the ona_alert_monitor.
    """
    conditions = [
        CommunicationAlert.organization_id == organization_id,
        CommunicationAlert.detection_source == "ona_alert_monitor",
    ]
    if status:
        conditions.append(CommunicationAlert.status == status)

    result = await db.execute(
        select(CommunicationAlert)
        .where(and_(*conditions))
        .order_by(desc(CommunicationAlert.created_at))
        .limit(limit)
    )
    alerts = result.scalars().all()

    return {
        "organization_id": str(organization_id),
        "count": len(alerts),
        "alerts": [
            {
                "id": str(a.id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "summary": a.summary,
                "status": a.status,
                "detection_confidence": (
                    float(a.detection_confidence) if a.detection_confidence else None
                ),
                "threshold_breached": a.threshold_breached,
                "supporting_metrics": a.supporting_metrics,
                "recommended_actions": a.recommended_actions,
                "requires_immediate_attention": a.requires_immediate_attention,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "acknowledged_at": (
                    a.acknowledged_at.isoformat() if a.acknowledged_at else None
                ),
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ],
    }


@router.patch("/{alert_id}/acknowledge", response_model=dict[str, Any])
async def acknowledge_ona_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Acknowledge an ONA alert."""
    result = await db.execute(
        select(CommunicationAlert).where(CommunicationAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    from datetime import datetime, timezone

    alert.status = AlertStatus.ACKNOWLEDGED.value
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()

    return {"id": str(alert_id), "status": "acknowledged"}


@router.patch("/{alert_id}/resolve", response_model=dict[str, Any])
async def resolve_ona_alert(
    alert_id: UUID,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Resolve an ONA alert with optional notes."""
    result = await db.execute(
        select(CommunicationAlert).where(CommunicationAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    from datetime import datetime, timezone

    alert.status = AlertStatus.RESOLVED.value
    alert.resolved_at = datetime.now(timezone.utc)
    if resolution_notes:
        alert.resolution_notes = resolution_notes
    await db.commit()

    return {"id": str(alert_id), "status": "resolved"}
