# app/api/v1/endpoints/okr_health.py
"""
OKR Health Monitor Endpoints

Cross-references OKR objectives with team BI scores to flag
health risks that could undermine achievement.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.okr_health_monitor import okr_health_monitor
from app.services.security import get_current_user

router = APIRouter(prefix="/okr-health", tags=["okr-health"])


@router.post("/{organization_id}/check", response_model=dict[str, Any])
async def check_okr_health(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Run OKR health check for an organization.
    Evaluates all active objectives against their team's BI scores
    and flags health risks (burnout, low collaboration, friction, etc.).
    """
    result = await okr_health_monitor.check_organization(db, organization_id)

    # Dispatch webhook events for critical flags
    try:
        from app.services.intelligence_events import intelligence_events

        await intelligence_events.dispatch_okr_health_events(
            str(organization_id), result
        )
    except Exception:
        pass

    return result


@router.get("/{organization_id}/flagged", response_model=dict[str, Any])
async def get_flagged_objectives(
    organization_id: UUID,
    min_severity: str = Query(default="caution", regex="^(caution|warning|critical)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get OKR objectives currently flagged with health risks.
    Filter by minimum severity level.
    """
    from sqlalchemy import and_, select
    from app.db.models.okr import Objective, OKRStatus

    severity_order = {"caution": 1, "warning": 2, "critical": 3}
    min_level = severity_order.get(min_severity, 1)

    result = await db.execute(
        select(Objective).where(
            and_(
                Objective.organization_id == organization_id,
                Objective.status == OKRStatus.ACTIVE,
                Objective.health_risk_flag.isnot(None),
                Objective.health_risk_flag != "none",
            )
        )
    )
    objectives = result.scalars().all()

    flagged = []
    for obj in objectives:
        obj_level = severity_order.get(obj.health_risk_flag, 0)
        if obj_level >= min_level:
            flagged.append(
                {
                    "objective_id": str(obj.id),
                    "title": obj.title,
                    "team": obj.team,
                    "progress": round(obj.progress_percentage, 1),
                    "status": obj.status.value,
                    "health_risk_flag": obj.health_risk_flag,
                    "health_risk_signals": obj.health_risk_signals or [],
                    "checked_at": (
                        obj.health_risk_checked_at.isoformat()
                        if obj.health_risk_checked_at
                        else None
                    ),
                }
            )

    flagged.sort(
        key=lambda x: severity_order.get(x["health_risk_flag"], 0), reverse=True
    )

    return {
        "organization_id": str(organization_id),
        "flagged_count": len(flagged),
        "objectives": flagged,
    }
