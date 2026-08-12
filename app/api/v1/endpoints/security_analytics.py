"""
Security Analytics Dashboard API

Queries AuditLog and SecurityIncident tables for real security event data,
authentication patterns, and threat indicators.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/security/analytics", tags=["Security Analytics"])


def _get_audit_model():
    """Lazy import to avoid circular imports."""
    from app.db.models.audit import AuditLog, SecurityIncident

    return AuditLog, SecurityIncident


@router.get("/status/overview")
async def get_system_security_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """System security status from audit logs."""
    AuditLog, SecurityIncident = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Total events
    total = (
        await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.timestamp >= since)
        )
    ).scalar() or 0

    # By severity
    sev_result = await db.execute(
        select(AuditLog.severity, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.severity)
    )
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for sev, cnt in sev_result.all():
        if sev in by_severity:
            by_severity[sev] = cnt

    # By type
    type_result = await db.execute(
        select(AuditLog.event_type, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.event_type)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
    )
    by_type = {r[0]: r[1] for r in type_result.all() if r[0]}

    # Active users and IPs
    active_users = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                AuditLog.timestamp >= since
            )
        )
    ).scalar() or 0

    active_ips = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.ip_address))).where(
                and_(AuditLog.timestamp >= since, AuditLog.ip_address.isnot(None))
            )
        )
    ).scalar() or 0

    # Security score: deduct for high/critical events
    high_count = by_severity.get("high", 0) + by_severity.get("critical", 0)
    score = max(0, 100 - high_count * 5)

    # Open security incidents
    open_incidents = (
        await db.execute(
            select(func.count(SecurityIncident.id)).where(
                SecurityIncident.status.in_(["open", "investigating"])
            )
        )
    ).scalar() or 0

    status = "healthy"
    if open_incidents > 0 or high_count > 5:
        status = "warning"
    if by_severity.get("critical", 0) > 0 or open_incidents > 3:
        status = "critical"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "security_score": score,
        "total_events": total,
        "active_users": max(active_users, 1),
        "active_ips": max(active_ips, 1),
        "events_by_severity": by_severity,
        "events_by_type": by_type,
        "open_incidents": open_incidents,
    }


@router.get("/metrics/overview")
async def get_security_metrics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Security metrics overview."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    # Events last hour
    last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
    hour_result = await db.execute(
        select(AuditLog.event_type, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= last_hour)
        .group_by(AuditLog.event_type)
    )
    events_last_hour = {r[0]: r[1] for r in hour_result.all() if r[0]}

    # Severity breakdown
    sev_result = await db.execute(
        select(AuditLog.severity, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.severity)
    )
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for sev, cnt in sev_result.all():
        if sev in by_severity:
            by_severity[sev] = cnt

    total = sum(by_severity.values())
    active_users = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                AuditLog.timestamp >= since
            )
        )
    ).scalar() or 0
    active_ips = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.ip_address))).where(
                and_(AuditLog.timestamp >= since, AuditLog.ip_address.isnot(None))
            )
        )
    ).scalar() or 0

    threat_indicators = by_severity.get("high", 0) + by_severity.get("critical", 0)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "events_last_hour": events_last_hour,
        "events_by_severity": by_severity,
        "active_users": max(active_users, 1),
        "active_ips": max(active_ips, 1),
        "total_events": total,
        "threat_indicators_active": threat_indicators,
        "users_with_recent_activity": max(active_users, 1),
        "ips_with_recent_activity": max(active_ips, 1),
    }


@router.get("/metrics/threats")
async def get_active_threats(
    hours: int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Active threats from high-severity audit events."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    filters = [AuditLog.timestamp >= since, AuditLog.severity.in_(["high", "critical"])]
    if severity:
        filters = [AuditLog.timestamp >= since, AuditLog.severity == severity]

    result = await db.execute(
        select(AuditLog)
        .where(and_(*filters))
        .order_by(AuditLog.timestamp.desc())
        .limit(50)
    )

    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "severity": log.severity,
            "ip_address": log.ip_address,
            "user_id": str(log.user_id) if log.user_id else None,
            "request_path": log.request_path,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "details": log.details,
        }
        for log in result.scalars().all()
    ]


@router.get("/metrics/events")
async def get_security_events(
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Security events with optional filters."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    filters = [AuditLog.timestamp >= since]
    if event_type:
        filters.append(AuditLog.event_type == event_type)
    if severity:
        filters.append(AuditLog.severity == severity)

    result = await db.execute(
        select(AuditLog)
        .where(and_(*filters))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )

    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "severity": log.severity,
            "ip_address": log.ip_address,
            "user_id": str(log.user_id) if log.user_id else None,
            "request_path": log.request_path,
            "request_method": log.request_method,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in result.scalars().all()
    ]


@router.get("/metrics/timeline")
async def get_security_timeline(
    hours: int = Query(default=24, ge=1, le=168),
    interval: str = Query(default="hour"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Security event timeline grouped by interval."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Group by hour
    result = await db.execute(
        select(
            func.date_trunc("hour", AuditLog.timestamp).label("bucket"),
            func.count(AuditLog.id),
        )
        .where(AuditLog.timestamp >= since)
        .group_by("bucket")
        .order_by("bucket")
    )

    data = {r[0].isoformat() if r[0] else "unknown": r[1] for r in result.all()}

    return {"interval": interval, "hours": hours, "data": data}


@router.get("/audit/logs")
async def get_audit_logs(
    event_type: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Audit log entries."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    filters = [AuditLog.timestamp >= since]
    if event_type:
        filters.append(AuditLog.event_type == event_type)
    if severity:
        filters.append(AuditLog.severity == severity)
    if user_id:
        filters.append(AuditLog.user_id == user_id)

    result = await db.execute(
        select(AuditLog)
        .where(and_(*filters))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )

    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "severity": log.severity,
            "user_id": str(log.user_id) if log.user_id else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_path": log.request_path,
            "request_method": log.request_method,
            "details": log.details,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in result.scalars().all()
    ]


@router.get("/audit/summary")
async def get_audit_summary(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Audit log summary statistics."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    total = (
        await db.execute(
            select(func.count(AuditLog.id)).where(AuditLog.timestamp >= since)
        )
    ).scalar() or 0

    type_result = await db.execute(
        select(AuditLog.event_type, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.event_type)
    )
    by_type = {r[0]: r[1] for r in type_result.all() if r[0]}

    sev_result = await db.execute(
        select(AuditLog.severity, func.count(AuditLog.id))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.severity)
    )
    by_severity = {r[0]: r[1] for r in sev_result.all() if r[0]}

    unique_users = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.user_id))).where(
                AuditLog.timestamp >= since
            )
        )
    ).scalar() or 0

    unique_ips = (
        await db.execute(
            select(func.count(func.distinct(AuditLog.ip_address))).where(
                and_(AuditLog.timestamp >= since, AuditLog.ip_address.isnot(None))
            )
        )
    ).scalar() or 0

    return {
        "hours": hours,
        "total_events": total,
        "by_type": by_type,
        "by_severity": by_severity,
        "unique_users": unique_users,
        "unique_ips": unique_ips,
    }


@router.get("/alerts/active")
async def get_active_alerts(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    """Active security incidents."""
    _, SecurityIncident = _get_audit_model()

    result = await db.execute(
        select(SecurityIncident)
        .where(SecurityIncident.status.in_(["open", "investigating"]))
        .order_by(SecurityIncident.created_at.desc())
        .limit(50)
    )

    return [
        {
            "id": str(inc.id),
            "incident_type": inc.incident_type,
            "severity": inc.severity,
            "status": inc.status,
            "title": inc.title if hasattr(inc, "title") else inc.incident_type,
            "created_at": inc.created_at.isoformat() if inc.created_at else None,
        }
        for inc in result.scalars().all()
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Acknowledge a security incident."""
    _, SecurityIncident = _get_audit_model()
    import uuid

    try:
        aid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    result = await db.execute(
        select(SecurityIncident).where(SecurityIncident.id == aid)
    )
    incident = result.scalar_one_or_none()
    if incident:
        incident.status = "investigating"
        await db.commit()

    return {"status": "acknowledged", "alert_id": alert_id}


@router.get("/risk/users/{user_id}")
async def get_user_risk_profile(
    user_id: str,
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """User risk profile from audit events."""
    AuditLog, _ = _get_audit_model()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    total = (
        await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(AuditLog.user_id == user_id, AuditLog.timestamp >= since)
            )
        )
    ).scalar() or 0

    threats = (
        await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since,
                    AuditLog.severity.in_(["high", "critical"]),
                )
            )
        )
    ).scalar() or 0

    high_sev = (
        await db.execute(
            select(func.count(AuditLog.id)).where(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.timestamp >= since,
                    AuditLog.severity == "critical",
                )
            )
        )
    ).scalar() or 0

    last_result = await db.execute(
        select(AuditLog.timestamp)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(1)
    )
    last_row = last_result.one_or_none()
    last_activity = last_row[0].isoformat() if last_row and last_row[0] else None

    risk = "low"
    if threats > 5 or high_sev > 0:
        risk = "high"
    elif threats > 0:
        risk = "medium"

    return {
        "user_id": user_id,
        "risk_level": risk,
        "analysis_period_hours": hours,
        "total_events": total,
        "threat_indicators_detected": threats,
        "high_severity_threats": high_sev,
        "last_activity": last_activity,
    }
