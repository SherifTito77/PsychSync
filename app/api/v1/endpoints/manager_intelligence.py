"""
Manager Intelligence API

Dedicated dashboard endpoints for managers to view their team's
behavioral health, member risks, network insights, and action items.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.manager_intelligence_service import ManagerIntelligenceService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/manager-intelligence",
    tags=["Manager Intelligence"],
)

_service = ManagerIntelligenceService()


@router.get("/teams")
async def get_my_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List teams the current user is a member of (for team selector)."""
    return await _service.get_manager_teams(db, str(current_user.id))


@router.get("/team/{team_id}")
async def get_team_briefing(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Full manager intelligence briefing for a specific team.
    Combines BI scores, member risk profiles, ONA insights,
    action items, and coaching prompts.
    """
    briefing = await _service.get_manager_briefing(db, team_id, str(current_user.id))

    # Persist generated action items as trackable action plans
    action_items = briefing.get("action_items", [])
    if action_items and briefing.get("organization_id"):
        from uuid import UUID as _UUID

        from app.services.action_plan_service import action_plan_service

        plans = await action_plan_service.create_from_manager_actions(
            db,
            organization_id=_UUID(briefing["organization_id"]),
            owner_id=current_user.id,
            team_id=_UUID(team_id),
            action_items=action_items,
            bi_scores=briefing.get("bi_scores"),
        )
        briefing["action_plans_created"] = len(plans)
        await db.commit()

    return briefing
