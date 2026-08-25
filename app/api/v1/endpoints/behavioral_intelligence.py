"""
Behavioral Intelligence Engine API

Exposes the 7 core organizational health scores + org-wide dashboard.
Each score aggregates real assessment data, team structure, and behavioral
signals rather than returning hardcoded stubs.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.behavioral_intelligence_service import BehavioralIntelligenceService
from app.services.data_source_aggregator import data_source_aggregator
from app.services.privacy_guard import PrivacyContext, PrivacyGuard
from app.services.security import get_current_user

router = APIRouter(
    prefix="/behavioral-intelligence",
    tags=["Behavioral Intelligence"],
)

_service = BehavioralIntelligenceService()
_privacy = PrivacyGuard()


@router.get("/team/{team_id}/health")
async def team_health(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_team_health(db, team_id, lookback_days)


@router.get("/team/{team_id}/collaboration")
async def team_collaboration(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_collaboration_score(db, team_id, lookback_days)


@router.get("/team/{team_id}/manager-health")
async def team_manager_health(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_manager_health(db, team_id, lookback_days)


@router.get("/team/{team_id}/psychological-safety")
async def team_psychological_safety(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_psychological_safety(db, team_id, lookback_days)


@router.get("/team/{team_id}/change-readiness")
async def team_change_readiness(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_change_readiness(db, team_id, lookback_days)


@router.get("/team/{team_id}/friction-index")
async def team_friction_index(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_friction_index(db, team_id, lookback_days)


@router.get("/team/{team_id}/burnout-risk")
async def team_burnout_risk(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return await _service.calculate_burnout_risk(db, team_id, lookback_days)


@router.get("/team/{team_id}/all")
async def team_all_scores(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """All seven scores for a single team in one call."""
    th = await _service.calculate_team_health(db, team_id, lookback_days)
    co = await _service.calculate_collaboration_score(db, team_id, lookback_days)
    mh = await _service.calculate_manager_health(db, team_id, lookback_days)
    ps = await _service.calculate_psychological_safety(db, team_id, lookback_days)
    cr = await _service.calculate_change_readiness(db, team_id, lookback_days)
    fi = await _service.calculate_friction_index(db, team_id, lookback_days)
    br = await _service.calculate_burnout_risk(db, team_id, lookback_days)

    return {
        "team_id": team_id,
        "lookback_days": lookback_days,
        "scores": {
            "team_health": th,
            "collaboration": co,
            "manager_health": mh,
            "psychological_safety": ps,
            "change_readiness": cr,
            "friction_index": fi,
            "burnout_risk": br,
        },
    }


@router.get("/organization/{organization_id}/dashboard")
async def organization_dashboard(
    organization_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full behavioral intelligence dashboard for an organization.

    Gathers enrichment from all connected data sources (HRIS, Calendar,
    Work Systems) and applies k-anonymity privacy guard before returning.
    """
    enrichment = await data_source_aggregator.gather_bi_enrichment(organization_id)
    dashboard = await _service.get_organization_dashboard(
        db,
        organization_id,
        lookback_days,
        enrichment=enrichment or None,
    )

    ctx = PrivacyContext(organization_id=organization_id)
    dashboard = _privacy.guard_dashboard(dashboard, ctx)
    dashboard["data_sources"] = data_source_aggregator.get_data_source_status()
    return dashboard
