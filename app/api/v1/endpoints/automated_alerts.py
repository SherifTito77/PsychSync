"""
Automated Clinical Alerts API Endpoints

Queries ClinicalAlert and WellnessAlert tables for real alert data.
Supports acknowledge/resolve workflows.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.clinical_screening import ClinicalAlert
from app.db.models.employee_safety import AlertLevel, WellnessAlert
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/automated-alerts", tags=["automated-alerts"])


async def _user_org_ids(db: AsyncSession, user_id) -> list[str]:
    """Get organization IDs the user belongs to via team membership."""
    result = await db.execute(
        select(Team.organization_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .distinct()
    )
    return [str(r[0]) for r in result.all()]


def _serialize_clinical_alert(alert) -> dict[str, Any]:
    return {
        "id": str(alert.id),
        "source": "clinical",
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.alert_message,
        "status": alert.resolution_status or "pending",
        "acknowledged": alert.acknowledged or False,
        "acknowledged_at": (
            alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        ),
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "escalated": alert.escalated or False,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


def _serialize_wellness_alert(alert) -> dict[str, Any]:
    severity_map = {
        "normal": "low",
        "elevated": "medium",
        "high": "high",
        "critical": "critical",
    }
    sev = alert.severity.value if alert.severity else "medium"
    return {
        "id": str(alert.id),
        "source": "wellness",
        "alert_type": alert.alert_type,
        "severity": severity_map.get(sev, sev),
        "message": alert.title,
        "status": alert.status or "active",
        "acknowledged": alert.acknowledged_date is not None,
        "acknowledged_at": (
            alert.acknowledged_date.isoformat() if alert.acknowledged_date else None
        ),
        "resolved_at": alert.resolved_date.isoformat() if alert.resolved_date else None,
        "escalated": False,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.get("/unresolved")
async def get_unresolved_alerts(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get all unresolved alerts across clinical and wellness sources."""
    org_ids = await _user_org_ids(db, current_user.id)

    alerts: list[dict] = []

    # Clinical alerts — unresolved
    if org_ids:
        clinical_result = await db.execute(
            select(ClinicalAlert)
            .where(
                and_(
                    ClinicalAlert.org_id.in_(org_ids),
                    or_(
                        ClinicalAlert.resolution_status.is_(None),
                        ClinicalAlert.resolution_status.in_(["pending", "in_progress"]),
                    ),
                )
            )
            .order_by(ClinicalAlert.created_at.desc())
            .limit(limit)
        )
        for a in clinical_result.scalars().all():
            alerts.append(_serialize_clinical_alert(a))

    # Wellness alerts — active/unresolved
    wellness_result = await db.execute(
        select(WellnessAlert)
        .where(
            and_(
                WellnessAlert.status.in_(["active", "acknowledged"]),
            )
        )
        .order_by(WellnessAlert.created_at.desc())
        .limit(limit)
    )
    for a in wellness_result.scalars().all():
        alerts.append(_serialize_wellness_alert(a))

    # Sort by created_at descending
    alerts.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    alerts = alerts[:limit]

    return {
        "alerts": alerts,
        "total_count": len(alerts),
        "unresolved_count": len(alerts),
    }


@router.get("/stats/overview")
async def get_alert_stats_overview(
    days_back: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Alert statistics overview from both clinical and wellness alert tables."""
    org_ids = await _user_org_ids(db, current_user.id)
    since = datetime.utcnow() - timedelta(days=days_back)

    # Clinical alert stats
    clinical_total = 0
    clinical_resolved = 0
    clinical_acknowledged = 0
    clinical_by_severity: dict[str, int] = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    if org_ids:
        ct_result = await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                and_(
                    ClinicalAlert.org_id.in_(org_ids), ClinicalAlert.created_at >= since
                )
            )
        )
        clinical_total = ct_result.scalar() or 0

        cr_result = await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                and_(
                    ClinicalAlert.org_id.in_(org_ids),
                    ClinicalAlert.created_at >= since,
                    ClinicalAlert.resolution_status == "resolved",
                )
            )
        )
        clinical_resolved = cr_result.scalar() or 0

        ca_result = await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                and_(
                    ClinicalAlert.org_id.in_(org_ids),
                    ClinicalAlert.created_at >= since,
                    ClinicalAlert.acknowledged == True,
                )
            )
        )
        clinical_acknowledged = ca_result.scalar() or 0

        sev_result = await db.execute(
            select(ClinicalAlert.severity, func.count(ClinicalAlert.id))
            .where(
                and_(
                    ClinicalAlert.org_id.in_(org_ids), ClinicalAlert.created_at >= since
                )
            )
            .group_by(ClinicalAlert.severity)
        )
        for sev, cnt in sev_result.all():
            if sev in clinical_by_severity:
                clinical_by_severity[sev] = cnt

    # Wellness alert stats
    wt_result = await db.execute(
        select(func.count(WellnessAlert.id)).where(WellnessAlert.created_at >= since)
    )
    wellness_total = wt_result.scalar() or 0

    wr_result = await db.execute(
        select(func.count(WellnessAlert.id)).where(
            and_(WellnessAlert.created_at >= since, WellnessAlert.status == "resolved")
        )
    )
    wellness_resolved = wr_result.scalar() or 0

    wa_result = await db.execute(
        select(func.count(WellnessAlert.id)).where(
            and_(
                WellnessAlert.created_at >= since,
                WellnessAlert.acknowledged_date.isnot(None),
            )
        )
    )
    wellness_acknowledged = wa_result.scalar() or 0

    wsev_result = await db.execute(
        select(WellnessAlert.severity, func.count(WellnessAlert.id))
        .where(WellnessAlert.created_at >= since)
        .group_by(WellnessAlert.severity)
    )
    wellness_sev_map = {
        "normal": "low",
        "elevated": "medium",
        "high": "high",
        "critical": "critical",
    }
    for sev, cnt in wsev_result.all():
        mapped = wellness_sev_map.get(sev.value if sev else "normal", "medium")
        clinical_by_severity[mapped] = clinical_by_severity.get(mapped, 0) + cnt

    total = clinical_total + wellness_total
    resolved = clinical_resolved + wellness_resolved
    acknowledged = clinical_acknowledged + wellness_acknowledged
    unresolved = total - resolved

    # Average resolution time (from clinical alerts that have resolved_at)
    avg_time_result = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", ClinicalAlert.resolved_at)
                    - func.extract("epoch", ClinicalAlert.created_at)
                )
            ).where(
                and_(
                    ClinicalAlert.resolved_at.isnot(None),
                    ClinicalAlert.created_at >= since,
                )
            )
        )
        if org_ids
        else None
    )
    avg_seconds = (avg_time_result.scalar() or 0) if avg_time_result else 0
    avg_hours = round(avg_seconds / 3600, 1) if avg_seconds else 0

    return {
        "days_back": days_back,
        "total_alerts": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "acknowledged": acknowledged,
        "by_severity": clinical_by_severity,
        "avg_resolution_time_hours": avg_hours,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/history")
async def get_alert_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get full alert history (all statuses) with pagination."""
    org_ids = await _user_org_ids(db, current_user.id)

    alerts: list[dict] = []

    if org_ids:
        clinical_result = await db.execute(
            select(ClinicalAlert)
            .where(ClinicalAlert.org_id.in_(org_ids))
            .order_by(ClinicalAlert.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        for a in clinical_result.scalars().all():
            alerts.append(_serialize_clinical_alert(a))

    wellness_result = await db.execute(
        select(WellnessAlert)
        .order_by(WellnessAlert.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    for a in wellness_result.scalars().all():
        alerts.append(_serialize_wellness_alert(a))

    alerts.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    alerts = alerts[offset : offset + limit]

    # Total count
    total = 0
    if org_ids:
        ct = await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                ClinicalAlert.org_id.in_(org_ids)
            )
        )
        total += ct.scalar() or 0
    wt = await db.execute(select(func.count(WellnessAlert.id)))
    total += wt.scalar() or 0

    return {
        "alerts": alerts,
        "total_count": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{alert_id}")
async def get_alert_detail(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get detail for a specific alert (checks both clinical and wellness tables)."""
    import uuid as _uuid

    try:
        aid = _uuid.UUID(alert_id)
    except ValueError:
        return {"alert_id": alert_id, "status": "not_found"}

    # Try clinical first
    result = await db.execute(select(ClinicalAlert).where(ClinicalAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        return _serialize_clinical_alert(alert)

    # Try wellness
    result = await db.execute(select(WellnessAlert).where(WellnessAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        return _serialize_wellness_alert(alert)

    return {"alert_id": alert_id, "status": "not_found"}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Acknowledge an alert in either clinical or wellness table."""
    import uuid as _uuid

    try:
        aid = _uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    now = datetime.utcnow()

    # Try clinical
    result = await db.execute(select(ClinicalAlert).where(ClinicalAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        alert.acknowledged = True
        alert.acknowledged_by = current_user.id
        alert.acknowledged_at = now
        if not alert.resolution_status or alert.resolution_status == "pending":
            alert.resolution_status = "in_progress"
        await db.commit()
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_at": now.isoformat(),
        }

    # Try wellness
    result = await db.execute(select(WellnessAlert).where(WellnessAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        alert.acknowledged_by_id = current_user.id
        alert.acknowledged_date = now
        alert.status = "acknowledged"
        await db.commit()
        return {
            "alert_id": alert_id,
            "status": "acknowledged",
            "acknowledged_at": now.isoformat(),
        }

    raise HTTPException(status_code=404, detail="Alert not found")


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve an alert in either clinical or wellness table."""
    import uuid as _uuid

    try:
        aid = _uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    now = datetime.utcnow()

    # Try clinical
    result = await db.execute(select(ClinicalAlert).where(ClinicalAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        alert.resolution_status = "resolved"
        alert.resolved_by = current_user.id
        alert.resolved_at = now
        await db.commit()
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_at": now.isoformat(),
        }

    # Try wellness
    result = await db.execute(select(WellnessAlert).where(WellnessAlert.id == aid))
    alert = result.scalar_one_or_none()
    if alert:
        alert.status = "resolved"
        alert.resolved_date = now
        alert.resolution_notes = f"Resolved by {current_user.email}"
        await db.commit()
        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_at": now.isoformat(),
        }

    raise HTTPException(status_code=404, detail="Alert not found")
