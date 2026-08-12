"""
Employee Safety API Endpoints

Queries SafetyIncident, WellnessAssessment, and WellnessAlert tables
for real incident data and wellness metrics. Creates incidents and
assessments with proper persistence.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.employee_safety import (
    AlertLevel,
    IncidentSeverity,
    IncidentStatus,
    SafetyIncident,
    SafetyIncidentType,
    WellnessAlert,
    WellnessAssessment,
)
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/safety", tags=["employee-safety"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _user_org_ids(db: AsyncSession, user_id) -> list[str]:
    """Get organization IDs the user belongs to via team membership."""
    result = await db.execute(
        select(Team.organization_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id)
        .distinct()
    )
    return [str(r[0]) for r in result.all()]


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------


class IncidentReportRequest(BaseModel):
    incident_type: str = Field(..., description="Type of safety incident")
    severity: str = Field(..., description="Incident severity level")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    location: Optional[str] = None
    date_occurred: Optional[datetime] = None
    witnesses: Optional[List[Dict[str, Any]]] = None
    evidence_files: Optional[List[str]] = None
    immediate_actions: Optional[List[str]] = None
    affected_user_id: Optional[uuid.UUID] = None

    @validator("date_occurred")
    def validate_date_occurred(cls, v):
        if v and v > datetime.utcnow():
            raise ValueError("Date occurred cannot be in the future")
        return v


class IncidentUpdateRequest(BaseModel):
    status: str
    investigation_notes: Optional[str] = None
    root_cause: Optional[str] = None
    prevention_measures: Optional[List[str]] = None
    resolution_details: Optional[str] = None
    lessons_learned: Optional[str] = None


class WellnessAssessmentRequest(BaseModel):
    user_id: uuid.UUID
    team_id: Optional[uuid.UUID] = None
    assessment_type: str = Field(
        default="scheduled", pattern="^(scheduled|incident_triggered|self_reported)$"
    )
    stress_level: Optional[float] = Field(None, ge=1, le=10)
    burnout_risk: Optional[float] = Field(None, ge=0, le=1)
    work_life_balance: Optional[float] = Field(None, ge=1, le=10)
    mental_health_score: Optional[float] = Field(None, ge=1, le=10)
    physical_wellness: Optional[float] = Field(None, ge=1, le=10)
    sleep_quality: Optional[float] = Field(None, ge=1, le=10)
    social_connection: Optional[float] = Field(None, ge=1, le=10)
    job_satisfaction: Optional[float] = Field(None, ge=1, le=10)
    engagement_level: Optional[float] = Field(None, ge=1, le=10)
    work_hours_per_week: Optional[float] = Field(None, ge=0)
    overtime_hours: Optional[float] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Incident Endpoints
# ---------------------------------------------------------------------------


@router.post("/incidents")
async def report_incident(
    incident_data: IncidentReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Report a new safety incident — persists to SafetyIncident table."""
    org_ids = await _user_org_ids(db, current_user.id)
    if not org_ids:
        raise HTTPException(
            status_code=400, detail="User has no organization membership"
        )

    # Map string to enum, fallback to OTHER
    try:
        inc_type = SafetyIncidentType(incident_data.incident_type)
    except ValueError:
        inc_type = SafetyIncidentType.OTHER
    try:
        severity = IncidentSeverity(incident_data.severity)
    except ValueError:
        severity = IncidentSeverity.MEDIUM

    incident = SafetyIncident(
        incident_type=inc_type,
        severity=severity,
        status=IncidentStatus.REPORTED,
        reporter_id=current_user.id,
        affected_user_id=incident_data.affected_user_id,
        organization_id=org_ids[0],
        title=incident_data.title,
        description=incident_data.description,
        location=incident_data.location,
        date_occurred=incident_data.date_occurred or datetime.utcnow(),
        date_reported=datetime.utcnow(),
        witnesses=incident_data.witnesses,
        evidence_files=incident_data.evidence_files,
        immediate_actions=incident_data.immediate_actions,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    return {
        "success": True,
        "incident_id": str(incident.id),
        "message": "Safety incident reported successfully",
        "title": incident.title,
        "severity": (
            incident.severity.value if incident.severity else incident_data.severity
        ),
        "reported_by": str(current_user.id),
        "reported_at": (
            incident.date_reported.isoformat()
            if incident.date_reported
            else datetime.utcnow().isoformat()
        ),
    }


@router.get("/incidents")
async def get_incidents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get safety incidents for the user's organizations."""
    org_ids = await _user_org_ids(db, current_user.id)
    if not org_ids:
        return {
            "incidents": [],
            "total_count": 0,
            "statistics": {
                "severity_breakdown": {},
                "type_breakdown": {},
                "status_breakdown": {},
            },
        }

    # Total count
    count_result = await db.execute(
        select(func.count(SafetyIncident.id)).where(
            SafetyIncident.organization_id.in_(org_ids)
        )
    )
    total = count_result.scalar() or 0

    # Fetch incidents
    result = await db.execute(
        select(SafetyIncident)
        .where(SafetyIncident.organization_id.in_(org_ids))
        .order_by(SafetyIncident.date_reported.desc())
        .limit(limit)
        .offset(offset)
    )
    incidents = result.scalars().all()

    # Statistics
    sev_result = await db.execute(
        select(SafetyIncident.severity, func.count(SafetyIncident.id))
        .where(SafetyIncident.organization_id.in_(org_ids))
        .group_by(SafetyIncident.severity)
    )
    severity_breakdown = {
        str(r[0].value) if r[0] else "unknown": r[1] for r in sev_result.all()
    }

    type_result = await db.execute(
        select(SafetyIncident.incident_type, func.count(SafetyIncident.id))
        .where(SafetyIncident.organization_id.in_(org_ids))
        .group_by(SafetyIncident.incident_type)
    )
    type_breakdown = {
        str(r[0].value) if r[0] else "unknown": r[1] for r in type_result.all()
    }

    status_result = await db.execute(
        select(SafetyIncident.status, func.count(SafetyIncident.id))
        .where(SafetyIncident.organization_id.in_(org_ids))
        .group_by(SafetyIncident.status)
    )
    status_breakdown = {
        str(r[0].value) if r[0] else "unknown": r[1] for r in status_result.all()
    }

    return {
        "incidents": [
            {
                "id": str(inc.id),
                "title": inc.title,
                "incident_type": inc.incident_type.value if inc.incident_type else None,
                "severity": inc.severity.value if inc.severity else None,
                "status": inc.status.value if inc.status else None,
                "location": inc.location,
                "date_occurred": (
                    inc.date_occurred.isoformat() if inc.date_occurred else None
                ),
                "date_reported": (
                    inc.date_reported.isoformat() if inc.date_reported else None
                ),
            }
            for inc in incidents
        ],
        "total_count": total,
        "statistics": {
            "severity_breakdown": severity_breakdown,
            "type_breakdown": type_breakdown,
            "status_breakdown": status_breakdown,
        },
    }


@router.get("/incidents/dashboard")
async def get_incidents_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    team_id: Optional[str] = None,
    days: int = 30,
):
    """Safety incidents dashboard with real aggregated data."""
    org_ids = await _user_org_ids(db, current_user.id)
    if not org_ids:
        return {
            "total_incidents": 0,
            "recent_incidents": 0,
            "critical_incidents": 0,
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "type_breakdown": {},
            "status_breakdown": {
                "open": 0,
                "investigating": 0,
                "resolved": 0,
                "closed": 0,
            },
            "incidents": [],
            "trends": {
                "period_days": days,
                "incidents_change": 0,
                "resolution_rate": 0,
            },
        }

    since = datetime.utcnow() - timedelta(days=days)
    base_filter = [SafetyIncident.organization_id.in_(org_ids)]
    if team_id:
        base_filter.append(SafetyIncident.team_id == team_id)

    # Total and recent
    total_result = await db.execute(
        select(func.count(SafetyIncident.id)).where(and_(*base_filter))
    )
    total = total_result.scalar() or 0

    recent_result = await db.execute(
        select(func.count(SafetyIncident.id)).where(
            and_(*base_filter, SafetyIncident.date_reported >= since)
        )
    )
    recent = recent_result.scalar() or 0

    critical_result = await db.execute(
        select(func.count(SafetyIncident.id)).where(
            and_(*base_filter, SafetyIncident.severity == IncidentSeverity.CRITICAL)
        )
    )
    critical = critical_result.scalar() or 0

    # Severity breakdown
    sev_result = await db.execute(
        select(SafetyIncident.severity, func.count(SafetyIncident.id))
        .where(and_(*base_filter))
        .group_by(SafetyIncident.severity)
    )
    sev_map = {str(r[0].value) if r[0] else "unknown": r[1] for r in sev_result.all()}
    severity_breakdown = {
        "critical": sev_map.get("critical", 0),
        "high": sev_map.get("high", 0),
        "medium": sev_map.get("medium", 0),
        "low": sev_map.get("low", 0),
    }

    # Type breakdown
    type_result = await db.execute(
        select(SafetyIncident.incident_type, func.count(SafetyIncident.id))
        .where(and_(*base_filter))
        .group_by(SafetyIncident.incident_type)
    )
    type_breakdown = {
        str(r[0].value) if r[0] else "unknown": r[1] for r in type_result.all()
    }

    # Status breakdown
    stat_result = await db.execute(
        select(SafetyIncident.status, func.count(SafetyIncident.id))
        .where(and_(*base_filter))
        .group_by(SafetyIncident.status)
    )
    stat_map = {str(r[0].value) if r[0] else "unknown": r[1] for r in stat_result.all()}
    status_breakdown = {
        "open": stat_map.get("reported", 0),
        "investigating": stat_map.get("investigating", 0),
        "resolved": stat_map.get("resolved", 0),
        "closed": stat_map.get("closed", 0),
    }

    # Recent incidents list
    inc_result = await db.execute(
        select(SafetyIncident)
        .where(and_(*base_filter, SafetyIncident.date_reported >= since))
        .order_by(SafetyIncident.date_reported.desc())
        .limit(10)
    )
    recent_incidents_list = [
        {
            "id": str(inc.id),
            "title": inc.title,
            "severity": inc.severity.value if inc.severity else None,
            "status": inc.status.value if inc.status else None,
            "date_reported": (
                inc.date_reported.isoformat() if inc.date_reported else None
            ),
        }
        for inc in inc_result.scalars().all()
    ]

    # Trends: compare current period to previous period
    prev_since = since - timedelta(days=days)
    prev_result = await db.execute(
        select(func.count(SafetyIncident.id)).where(
            and_(*base_filter, SafetyIncident.date_reported.between(prev_since, since))
        )
    )
    prev_count = prev_result.scalar() or 0
    incidents_change = recent - prev_count

    resolved_count = stat_map.get("resolved", 0) + stat_map.get("closed", 0)
    resolution_rate = round(resolved_count / max(total, 1) * 100, 1)

    return {
        "total_incidents": total,
        "recent_incidents": recent,
        "critical_incidents": critical,
        "severity_breakdown": severity_breakdown,
        "type_breakdown": type_breakdown,
        "status_breakdown": status_breakdown,
        "incidents": recent_incidents_list,
        "trends": {
            "period_days": days,
            "incidents_change": incidents_change,
            "resolution_rate": resolution_rate,
        },
    }


@router.get("/wellness/dashboard")
async def get_wellness_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    team_id: Optional[str] = None,
):
    """Wellness dashboard with real assessment aggregation."""
    org_ids = await _user_org_ids(db, current_user.id)
    if not org_ids:
        return {
            "total_assessments": 0,
            "high_risk_employees": 0,
            "average_scores": {
                "stress_level": 0,
                "burnout_risk": 0,
                "work_life_balance": 0,
                "mental_health": 0,
                "physical_wellness": 0,
            },
            "alert_breakdown": {"critical": 0, "warning": 0, "watch": 0, "normal": 0},
            "weekly_trends": {},
            "recent_assessments": [],
        }

    base_filter = [WellnessAssessment.organization_id.in_(org_ids)]
    if team_id:
        base_filter.append(WellnessAssessment.team_id == team_id)

    # Total assessments
    total_result = await db.execute(
        select(func.count(WellnessAssessment.id)).where(and_(*base_filter))
    )
    total = total_result.scalar() or 0

    # Average scores
    avg_result = await db.execute(
        select(
            func.avg(WellnessAssessment.stress_level),
            func.avg(WellnessAssessment.burnout_risk),
            func.avg(WellnessAssessment.work_life_balance),
            func.avg(WellnessAssessment.mental_health_score),
            func.avg(WellnessAssessment.physical_wellness),
        ).where(and_(*base_filter))
    )
    avg_row = avg_result.one_or_none()

    average_scores = {
        "stress_level": round(float(avg_row[0] or 0), 1) if avg_row else 0,
        "burnout_risk": round(float(avg_row[1] or 0), 2) if avg_row else 0,
        "work_life_balance": round(float(avg_row[2] or 0), 1) if avg_row else 0,
        "mental_health": round(float(avg_row[3] or 0), 1) if avg_row else 0,
        "physical_wellness": round(float(avg_row[4] or 0), 1) if avg_row else 0,
    }

    # High-risk employees (burnout_risk > 0.7 or stress > 7)
    high_risk_result = await db.execute(
        select(func.count(func.distinct(WellnessAssessment.user_id))).where(
            and_(
                *base_filter,
                WellnessAssessment.alert_level.in_(
                    [AlertLevel.HIGH, AlertLevel.CRITICAL]
                ),
            )
        )
    )
    high_risk = high_risk_result.scalar() or 0

    # Alert level breakdown
    alert_result = await db.execute(
        select(WellnessAssessment.alert_level, func.count(WellnessAssessment.id))
        .where(and_(*base_filter))
        .group_by(WellnessAssessment.alert_level)
    )
    alert_map = {
        str(r[0].value) if r[0] else "normal": r[1] for r in alert_result.all()
    }
    alert_breakdown = {
        "critical": alert_map.get("critical", 0),
        "warning": alert_map.get("high", 0),
        "watch": alert_map.get("elevated", 0),
        "normal": alert_map.get("normal", 0),
    }

    # Weekly trends (last 4 weeks)
    weekly_trends = {}
    now = datetime.utcnow()
    for week in range(4):
        week_end = now - timedelta(weeks=week)
        week_start = week_end - timedelta(weeks=1)
        week_result = await db.execute(
            select(func.avg(WellnessAssessment.overall_wellness_score)).where(
                and_(
                    *base_filter,
                    WellnessAssessment.assessment_date.between(week_start, week_end),
                )
            )
        )
        score = week_result.scalar()
        weekly_trends[f"week_{week + 1}"] = round(float(score or 0), 1)

    # Recent assessments
    recent_result = await db.execute(
        select(WellnessAssessment)
        .where(and_(*base_filter))
        .order_by(WellnessAssessment.assessment_date.desc())
        .limit(10)
    )
    recent = [
        {
            "id": str(a.id),
            "user_id": str(a.user_id),
            "assessment_type": a.assessment_type,
            "overall_score": float(a.overall_wellness_score or 0),
            "alert_level": a.alert_level.value if a.alert_level else "normal",
            "assessment_date": (
                a.assessment_date.isoformat() if a.assessment_date else None
            ),
        }
        for a in recent_result.scalars().all()
    ]

    return {
        "total_assessments": total,
        "high_risk_employees": high_risk,
        "average_scores": average_scores,
        "alert_breakdown": alert_breakdown,
        "weekly_trends": weekly_trends,
        "recent_assessments": recent,
    }
