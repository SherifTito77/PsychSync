# app/api/v1/endpoints/pulse_survey.py
"""
Pulse Survey API — Direct employee voice for BI calibration.

Endpoints for submitting pulse responses, viewing aggregated trends,
and comparing reported vs inferred scores (validation layer).
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.pulse_survey_service import pulse_survey_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/pulse-survey",
    tags=["Pulse Survey"],
)


class PulseResponseSubmission(BaseModel):
    team_health_perception: Optional[float] = Field(None, ge=1, le=10)
    collaboration_effectiveness: Optional[float] = Field(None, ge=1, le=10)
    manager_support: Optional[float] = Field(None, ge=1, le=10)
    psychological_safety: Optional[float] = Field(None, ge=1, le=10)
    workload_balance: Optional[float] = Field(None, ge=1, le=10)
    engagement_level: Optional[float] = Field(None, ge=1, le=10)
    burnout_felt: Optional[float] = Field(None, ge=1, le=10)
    change_readiness: Optional[float] = Field(None, ge=1, le=10)
    biggest_challenge: Optional[str] = Field(None, max_length=200)
    response_time_seconds: Optional[int] = None


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=255)
    frequency: str = Field(default="biweekly")
    question_set: str = Field(default="standard")


@router.post("/{organization_id}/respond")
async def submit_pulse_response(
    organization_id: str,
    submission: PulseResponseSubmission,
    team_id: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Submit a pulse survey response. One per user per survey round."""
    return await pulse_survey_service.submit_response(
        db,
        organization_id,
        str(current_user.id),
        submission.model_dump(exclude_none=True),
        team_id=team_id,
    )


@router.post("/{organization_id}/campaign")
async def create_campaign(
    organization_id: str,
    campaign: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a pulse survey campaign for the organization."""
    return await pulse_survey_service.create_campaign(
        db,
        organization_id,
        campaign.name,
        campaign.frequency,
        str(current_user.id),
        campaign.question_set,
    )


@router.get("/{organization_id}/summary")
async def get_pulse_summary(
    organization_id: str,
    team_id: Optional[str] = Query(default=None),
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Aggregated pulse survey results per team."""
    return await pulse_survey_service.get_team_pulse_summary(
        db, organization_id, team_id, lookback_days
    )


@router.get("/{organization_id}/trends")
async def get_pulse_trends(
    organization_id: str,
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Weekly pulse trends for charting."""
    return await pulse_survey_service.get_pulse_trends(db, organization_id, days)


@router.get("/{organization_id}/validation")
async def validate_scores(
    organization_id: str,
    lookback_days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Compare pulse survey results with inferred BI scores.

    Returns divergences where reported and inferred scores differ
    by more than 25 points — indicating the inference may be wrong.
    """
    from app.services.behavioral_intelligence_service import (
        BehavioralIntelligenceService,
    )
    from app.services.data_source_aggregator import data_source_aggregator

    bi_service = BehavioralIntelligenceService()
    enrichment = await data_source_aggregator.gather_bi_enrichment(organization_id)
    dashboard = await bi_service.get_organization_dashboard(
        db, organization_id, lookback_days, enrichment=enrichment or None
    )

    org_scores = dashboard.get("scores", {})
    divergences = await pulse_survey_service.validate_against_inferred(
        db, organization_id, org_scores, lookback_days
    )

    return {
        "organization_id": organization_id,
        "divergences": divergences,
        "divergence_count": len(divergences),
        "confidence": ("high" if not divergences else "uncertain"),
        "pulse_response_count": (
            await pulse_survey_service.get_org_pulse_summary(
                db, organization_id, lookback_days
            )
        ).get("response_count", 0),
    }
