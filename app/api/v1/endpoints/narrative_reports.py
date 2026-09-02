# app/api/v1/endpoints/narrative_reports.py
"""
Narrative Intelligence Endpoints

Generate executive storytelling reports from organizational data.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.narrative_intelligence_service import narrative_intelligence_service
from app.services.security import get_current_user

router = APIRouter(prefix="/narrative-reports", tags=["narrative-reports"])


@router.get("/{organization_id}", response_model=dict[str, Any])
async def generate_narrative_report(
    organization_id: UUID,
    period: str = Query(default="weekly", regex="^(weekly|monthly|quarterly)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate a narrative intelligence report for an organization.

    Sections: executive summary, improvements, declines, team spotlight,
    risk outlook, recommended actions.
    """
    return await narrative_intelligence_service.generate_report(
        db, organization_id, period
    )
