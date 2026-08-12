"""
Organizational Network Analysis API

Exposes ONA insights: influencers, isolated employees, bridges,
cross-team collaboration, and manager dependency analysis.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
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
    """Full ONA for an organization: nodes, edges, influencers, isolated, bridges."""
    return await _service.analyze_organization(db, organization_id, lookback_days)
