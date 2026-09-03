"""
Executive Intelligence API

Exposes the integration layer that combines Behavioral Intelligence,
ONA, and HRIS into executive-grade organizational narratives.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.executive_intelligence_service import ExecutiveIntelligenceService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/executive-intelligence",
    tags=["Executive Intelligence"],
)

_service = ExecutiveIntelligenceService()


@router.get("/briefing/{organization_id}")
async def executive_briefing(
    organization_id: str,
    lookback_days: int = Query(default=45, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Full executive intelligence briefing.
    Combines BI scores + ONA network analysis + HRIS signals
    into team-specific narratives with trend alerts.
    """
    return await _service.generate_executive_briefing(
        db, organization_id, lookback_days
    )
