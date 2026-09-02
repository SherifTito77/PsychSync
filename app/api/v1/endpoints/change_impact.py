# app/api/v1/endpoints/change_impact.py
"""
Change Impact Predictor Endpoints

Predict how proposed organizational changes will affect teams.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.change_impact_service import change_impact_service
from app.services.security import get_current_user

router = APIRouter(prefix="/change-impact", tags=["change-impact"])


class PredictImpactRequest(BaseModel):
    change_type: str = Field(
        ...,
        description="reorg, tool_migration, policy_shift, leadership_change, layoff, or expansion",
    )
    affected_team_ids: list[UUID] | None = Field(
        None, description="Specific team UUIDs (None = all teams)"
    )
    magnitude: float = Field(
        1.0, ge=0.1, le=3.0, description="Scale: 0.5=minor, 1.0=standard, 2.0=major"
    )


@router.post("/{organization_id}/predict", response_model=dict[str, Any])
async def predict_change_impact(
    organization_id: UUID,
    body: PredictImpactRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Predict per-team impact of a proposed organizational change."""
    return await change_impact_service.predict_impact(
        db,
        organization_id,
        body.change_type,
        body.affected_team_ids,
        body.magnitude,
    )
