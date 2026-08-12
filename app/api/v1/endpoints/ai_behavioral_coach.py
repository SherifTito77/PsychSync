"""
AI Behavioral Coach & Digital Twin API

Personalized coaching, digital twin profiles, and team fit simulations.
"""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.ai_behavioral_coach_service import AIBehavioralCoachService
from app.services.security import get_current_user

router = APIRouter(
    prefix="/ai-coach",
    tags=["AI Behavioral Coach"],
)

_service = AIBehavioralCoachService()


@router.get("/profile/{user_id}")
async def coaching_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get personalized coaching profile for a user."""
    return await _service.get_coaching_profile(db, user_id)


@router.get("/me")
async def my_coaching_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get coaching profile for the current user."""
    return await _service.get_coaching_profile(db, str(current_user.id))


@router.get("/digital-twin/{user_id}")
async def digital_twin(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get Digital Twin behavioral profile."""
    return await _service.get_digital_twin(db, user_id)


@router.get("/digital-twin/me")
async def my_digital_twin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Get Digital Twin for the current user."""
    return await _service.get_digital_twin(db, str(current_user.id))


@router.get("/team-fit/{user_id}/{team_id}")
async def simulate_team_fit(
    user_id: str,
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Simulate how a user would fit into a specific team."""
    return await _service.simulate_team_fit(db, user_id, team_id)
