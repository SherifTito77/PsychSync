"""
Behavioral Intelligence Engine API

Exposes the 6 core organizational health scores + org-wide dashboard.
Each score aggregates real assessment data, team structure, and behavioral
signals rather than returning hardcoded stubs.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.behavioral_intelligence_service import BehavioralIntelligenceService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/behavioral-intelligence",
    tags=["Behavioral Intelligence"],
)

_service = BehavioralIntelligenceService()


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


@router.get("/team/{team_id}/all")
async def team_all_scores(
    team_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """All six scores for a single team in one call."""
    th = await _service.calculate_team_health(db, team_id, lookback_days)
    co = await _service.calculate_collaboration_score(db, team_id, lookback_days)
    mh = await _service.calculate_manager_health(db, team_id, lookback_days)
    ps = await _service.calculate_psychological_safety(db, team_id, lookback_days)
    cr = await _service.calculate_change_readiness(db, team_id, lookback_days)
    fi = await _service.calculate_friction_index(db, team_id, lookback_days)

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
        },
    }


@router.get("/organization/{organization_id}/dashboard")
async def organization_dashboard(
    organization_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full behavioral intelligence dashboard for an organization."""
    return await _service.get_organization_dashboard(db, organization_id, lookback_days)
