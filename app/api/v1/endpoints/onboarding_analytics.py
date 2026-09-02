# app/api/v1/endpoints/onboarding_analytics.py
"""
Onboarding Analytics API — New hire health monitoring.
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.onboarding_analytics_service import onboarding_analytics_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/onboarding-analytics",
    tags=["Onboarding Analytics"],
)


@router.get("/{organization_id}")
async def onboarding_dashboard(
    organization_id: str,
    window_days: int = Query(default=90, ge=30, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Onboarding health dashboard: new hires, their integration scores, and at-risk flags."""
    return await onboarding_analytics_service.get_onboarding_dashboard(
        db, organization_id, window_days
    )
