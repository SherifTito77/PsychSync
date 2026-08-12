"""
Clinical Analytics API Endpoints

Queries ClinicalScreening, ClinicalAlert, and ClinicalReferral tables
for real clinical analytics data.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.clinical_screening import ClinicalAlert, ClinicalScreening
from app.db.models.team import Team, TeamMember
from app.db.models.user import User
from app.services.security import get_current_user

router = APIRouter(prefix="/analytics/clinical", tags=["clinical-analytics"])


async def _user_org_ids(db: AsyncSession, user_id) -> list[str]:
    result = await db.execute(
        select(Team.organization_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .distinct()
    )
    return [str(r[0]) for r in result.all()]


@router.get("/population")
async def get_population_analytics(
    period: Optional[str] = Query(default="30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Population-level clinical analytics from screening data."""
    org_ids = await _user_org_ids(db, current_user.id)
    days = int(period.rstrip("d")) if period and period.endswith("d") else 30
    since = datetime.utcnow() - timedelta(days=days)

    base_filter = []
    if org_ids:
        base_filter.append(ClinicalScreening.org_id.in_(org_ids))

    # Total assessments and users
    total_result = await db.execute(
        select(
            func.count(ClinicalScreening.id),
            func.count(func.distinct(ClinicalScreening.user_id)),
        ).where(and_(*base_filter))
        if base_filter
        else select(
            func.count(ClinicalScreening.id),
            func.count(func.distinct(ClinicalScreening.user_id)),
        )
    )
    row = total_result.one_or_none()
    total_assessments = row[0] or 0 if row else 0
    total_users = row[1] or 0 if row else 0

    # Recent screenings
    recent_filter = [ClinicalScreening.created_at >= since]
    if org_ids:
        recent_filter.append(ClinicalScreening.org_id.in_(org_ids))

    recent_result = await db.execute(
        select(func.count(ClinicalScreening.id)).where(and_(*recent_filter))
    )
    total_screenings = recent_result.scalar() or 0

    # Completed
    completed_filter = recent_filter + [ClinicalScreening.completed_at.isnot(None)]
    completed_result = await db.execute(
        select(func.count(ClinicalScreening.id)).where(and_(*completed_filter))
    )
    completed = completed_result.scalar() or 0
    completion_rate = round(completed / max(total_screenings, 1) * 100, 1)

    # Risk distribution
    risk_filter = recent_filter.copy()
    risk_result = await db.execute(
        select(ClinicalScreening.risk_level, func.count(ClinicalScreening.id))
        .where(and_(*risk_filter))
        .group_by(ClinicalScreening.risk_level)
    )
    risk_map = {r[0]: r[1] for r in risk_result.all() if r[0]}
    risk_distribution = {
        "low": risk_map.get("low", 0),
        "moderate": risk_map.get("moderate", 0),
        "high": risk_map.get("high", 0),
        "critical": risk_map.get("critical", 0),
    }

    # Assessment counts by type
    type_result = await db.execute(
        select(ClinicalScreening.screening_type, func.count(ClinicalScreening.id))
        .where(and_(*recent_filter))
        .group_by(ClinicalScreening.screening_type)
    )
    assessment_counts = {r[0]: r[1] for r in type_result.all() if r[0]}

    # Crisis alerts
    alert_filter = [ClinicalAlert.created_at >= since]
    if org_ids:
        alert_filter.append(ClinicalAlert.org_id.in_(org_ids))

    crisis_total = (
        await db.execute(
            select(func.count(ClinicalAlert.id)).where(and_(*alert_filter))
        )
    ).scalar() or 0

    crisis_resolved = (
        await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                and_(*alert_filter, ClinicalAlert.resolution_status == "resolved")
            )
        )
    ).scalar() or 0

    # Avg response time for acknowledged alerts
    avg_resp = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", ClinicalAlert.acknowledged_at)
                    - func.extract("epoch", ClinicalAlert.created_at)
                )
            ).where(and_(*alert_filter, ClinicalAlert.acknowledged_at.isnot(None)))
        )
    ).scalar()
    avg_response_minutes = round(float(avg_resp or 0) / 60, 1)

    # High risk users
    high_risk_result = await db.execute(
        select(ClinicalScreening.user_id, func.max(ClinicalScreening.risk_level))
        .where(
            and_(*recent_filter, ClinicalScreening.risk_level.in_(["high", "critical"]))
        )
        .group_by(ClinicalScreening.user_id)
        .limit(10)
    )
    high_risk_users = [
        {"user_id": str(r[0]), "risk_level": r[1]} for r in high_risk_result.all()
    ]

    return {
        "period": period,
        "summary": {
            "total_assessments": total_assessments,
            "total_users": total_users,
            "crisis_alerts_triggered": crisis_total,
            "crisis_alerts_resolved": crisis_resolved,
            "avg_response_time_minutes": avg_response_minutes,
        },
        "riskDistribution": risk_distribution,
        "assessmentCounts": assessment_counts,
        "trends": [],
        "highRiskUsers": high_risk_users,
        "total_screenings": total_screenings,
        "completion_rate": completion_rate,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/completion-stats")
async def get_completion_statistics(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Completion rates by screening tool."""
    filters = []
    if start_date:
        filters.append(ClinicalScreening.created_at >= start_date)
    if end_date:
        filters.append(ClinicalScreening.created_at <= end_date)

    started_result = await db.execute(
        select(func.count(ClinicalScreening.id)).where(and_(*filters))
        if filters
        else select(func.count(ClinicalScreening.id))
    )
    total_started = started_result.scalar() or 0

    completed_filters = filters + [ClinicalScreening.completed_at.isnot(None)]
    completed_result = await db.execute(
        select(func.count(ClinicalScreening.id)).where(and_(*completed_filters))
    )
    total_completed = completed_result.scalar() or 0

    # By tool
    tool_result = await db.execute(
        select(
            ClinicalScreening.screening_type,
            func.count(ClinicalScreening.id),
            func.count(ClinicalScreening.completed_at),
        ).where(and_(*filters))
        if filters
        else select(
            ClinicalScreening.screening_type,
            func.count(ClinicalScreening.id),
            func.count(ClinicalScreening.completed_at),
        )
    )
    # Need group_by
    tool_result = await db.execute(
        select(
            ClinicalScreening.screening_type,
            func.count(ClinicalScreening.id).label("started"),
            func.sum(
                func.cast(
                    ClinicalScreening.completed_at.isnot(None), type_=func.integer_type
                )
                if hasattr(func, "integer_type")
                else 1
            ).label("completed"),
        ).group_by(ClinicalScreening.screening_type)
    )
    by_tool = {}
    # Simpler approach
    type_list_result = await db.execute(
        select(ClinicalScreening.screening_type).distinct()
    )
    for (stype,) in type_list_result.all():
        if not stype:
            continue
        s = (
            await db.execute(
                select(func.count(ClinicalScreening.id)).where(
                    ClinicalScreening.screening_type == stype
                )
            )
        ).scalar() or 0
        c = (
            await db.execute(
                select(func.count(ClinicalScreening.id)).where(
                    and_(
                        ClinicalScreening.screening_type == stype,
                        ClinicalScreening.completed_at.isnot(None),
                    )
                )
            )
        ).scalar() or 0
        by_tool[stype] = {
            "started": s,
            "completed": c,
            "rate": round(c / max(s, 1) * 100, 1),
        }

    return {
        "total_started": total_started,
        "total_completed": total_completed,
        "completion_rate": round(total_completed / max(total_started, 1) * 100, 1),
        "by_tool": by_tool,
    }


@router.get("/severity-distribution")
async def get_severity_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Severity distribution across all screenings."""
    result = await db.execute(
        select(ClinicalScreening.severity_level, func.count(ClinicalScreening.id))
        .where(ClinicalScreening.severity_level.isnot(None))
        .group_by(ClinicalScreening.severity_level)
    )
    dist = {r[0]: r[1] for r in result.all()}
    total = sum(dist.values())

    return {
        "distribution": {
            "minimal": dist.get("minimal", 0),
            "mild": dist.get("mild", 0),
            "moderate": dist.get("moderate", 0),
            "severe": dist.get("severe", 0),
        },
        "total": total,
    }


@router.get("/crisis-metrics")
async def get_crisis_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Crisis alert metrics."""
    since = datetime.utcnow() - timedelta(days=30)

    active = (
        await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                ClinicalAlert.resolution_status.in_(["pending", "in_progress", None])
            )
        )
    ).scalar() or 0

    resolved = (
        await db.execute(
            select(func.count(ClinicalAlert.id)).where(
                and_(
                    ClinicalAlert.created_at >= since,
                    ClinicalAlert.resolution_status == "resolved",
                )
            )
        )
    ).scalar() or 0

    avg_resp = (
        await db.execute(
            select(
                func.avg(
                    func.extract("epoch", ClinicalAlert.acknowledged_at)
                    - func.extract("epoch", ClinicalAlert.created_at)
                )
            ).where(ClinicalAlert.acknowledged_at.isnot(None))
        )
    ).scalar()
    avg_minutes = round(float(avg_resp or 0) / 60, 1)

    return {
        "active_crises": active,
        "resolved_last_30d": resolved,
        "avg_response_time_minutes": avg_minutes,
    }


@router.get("/population-health")
async def get_population_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Population health summary."""
    since = datetime.utcnow() - timedelta(days=30)

    total_patients = (
        await db.execute(select(func.count(func.distinct(ClinicalScreening.user_id))))
    ).scalar() or 0

    screened_30d = (
        await db.execute(
            select(func.count(func.distinct(ClinicalScreening.user_id))).where(
                ClinicalScreening.created_at >= since
            )
        )
    ).scalar() or 0

    high_risk = (
        await db.execute(
            select(func.count(func.distinct(ClinicalScreening.user_id))).where(
                ClinicalScreening.risk_level.in_(["high", "critical"])
            )
        )
    ).scalar() or 0

    return {
        "total_patients": total_patients,
        "screened_last_30d": screened_30d,
        "high_risk_count": high_risk,
        "trends": [],
    }


@router.get("/clinician-workload")
async def get_clinician_workload(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Clinician workload based on validated screenings."""
    # Clinicians = users who have validated screenings
    result = await db.execute(
        select(
            ClinicalScreening.validated_by,
            func.count(ClinicalScreening.id),
        )
        .where(ClinicalScreening.validated_by.isnot(None))
        .group_by(ClinicalScreening.validated_by)
    )
    rows = result.all()
    total_clinicians = len(rows)
    caseloads = [r[1] for r in rows]
    avg_caseload = round(sum(caseloads) / max(total_clinicians, 1), 1)

    distribution = {}
    for uid, count in rows:
        if count <= 10:
            distribution["light"] = distribution.get("light", 0) + 1
        elif count <= 30:
            distribution["moderate"] = distribution.get("moderate", 0) + 1
        else:
            distribution["heavy"] = distribution.get("heavy", 0) + 1

    return {
        "total_clinicians": total_clinicians,
        "avg_caseload": avg_caseload,
        "workload_distribution": distribution,
    }
