"""
Organizational Digital Twin API

Exposes the living organizational model: current state, temporal
evolution, and what-if scenario simulation.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.org_digital_twin_service import OrganizationalDigitalTwinService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/org-digital-twin",
    tags=["Organizational Digital Twin"],
)

_service = OrganizationalDigitalTwinService()


@router.get("/{organization_id}")
async def get_digital_twin(
    organization_id: str,
    force_recompute: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get the current organizational digital twin state.
    Returns cached snapshot if fresh (<1 hour), otherwise recomputes.
    Use force_recompute=true to force fresh computation.
    """
    return await _service.get_current_twin(db, organization_id, force_recompute)


@router.get("/{organization_id}/evolution")
async def get_evolution(
    organization_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Temporal evolution: recent twin snapshots for trend visualization.
    """
    return await _service.get_temporal_evolution(db, organization_id, limit)


class SimulationRequest(BaseModel):
    type: str = Field(
        ...,
        description=(
            "Scenario type: key_person_departure, team_merge, "
            "engagement_shift, or rapid_growth"
        ),
    )
    role: str | None = Field(
        None, description="For departure: manager, influencer, bridge, or member"
    )
    shift_pct: float | None = Field(
        None, description="For engagement_shift: percentage change (e.g. -15)"
    )
    growth_pct: float | None = Field(
        None, description="For rapid_growth: growth percentage (e.g. 30)"
    )


@router.post("/{organization_id}/simulate")
async def simulate_scenario(
    organization_id: str,
    scenario: SimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Run a what-if scenario against the current twin state.
    Returns baseline vs predicted scores with impact narrative.
    """
    return await _service.simulate_scenario(
        db, organization_id, scenario.model_dump(exclude_none=True)
    )
