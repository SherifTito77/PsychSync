"""
Organizational Network Analysis API

Exposes ONA insights: influencers, isolated employees, bridges,
cross-team collaboration, manager dependency analysis, community detection,
temporal network evolution, collaboration surveys, and personality overlays.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.schemas.network_analysis import (
    CollaborationSurveyResult,
    CollaborationSurveySubmit,
)
from app.services.organizational_network_service import OrganizationalNetworkService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/organizational-network",
    tags=["Organizational Network Analysis"],
)

_service = OrganizationalNetworkService()


@router.get("/analyze/{organization_id}")
async def analyze_network(
    organization_id: str,
    lookback_days: int = Query(default=60, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Full ONA with community detection: nodes, edges, communities, influencers, isolated, bridges."""
    return await _service.analyze_organization(db, organization_id, lookback_days)


@router.get("/temporal/{organization_id}")
async def get_temporal_evolution(
    organization_id: str,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Network snapshots over time for trend visualization."""
    return await _service.get_temporal_evolution(db, organization_id, days)


@router.post("/survey/{organization_id}")
async def submit_collaboration_survey(
    organization_id: str,
    survey: CollaborationSurveySubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CollaborationSurveyResult:
    """Submit collaboration survey nominations (advice, trust, energy, collaboration)."""
    result = await _service.submit_collaboration_survey(
        db,
        organization_id,
        str(current_user.id),
        [n.model_dump() for n in survey.nominations],
        survey.survey_round,
    )
    return CollaborationSurveyResult(**result)


@router.get("/survey/{organization_id}/results")
async def get_survey_network(
    organization_id: str,
    network_type: str | None = Query(default=None),
    survey_round: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """View survey-derived network (advice, trust, energy networks)."""
    return await _service.get_survey_network(
        db, organization_id, network_type, survey_round
    )


@router.get("/personality/{organization_id}")
async def get_personality_network_insights(
    organization_id: str,
    lookback_days: int = Query(default=60, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Personality x network overlay: quiet connectors, friction bridges, burnout risks."""
    return await _service.get_personality_network_insights(
        db, organization_id, lookback_days
    )
