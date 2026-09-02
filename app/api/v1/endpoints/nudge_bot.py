# app/api/v1/endpoints/nudge_bot.py
"""Nudge Bot API — Trigger proactive outbound nudges."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.user import User
from app.services.nudge_bot_service import nudge_bot_service
from app.services.security import get_current_user

router = APIRouter(
    prefix="/nudge-bot",
    tags=["Nudge Bot"],
)


@router.post("/{organization_id}/run-all")
async def run_all_nudges(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Run all nudge types for an organization. Typically called by cron."""
    return await nudge_bot_service.run_all_nudges(db, organization_id)


@router.post("/{organization_id}/pulse-reminders")
async def pulse_reminders(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Send pulse survey reminders to non-respondents."""
    return await nudge_bot_service.send_pulse_survey_reminders(db, organization_id)


@router.post("/{organization_id}/burnout-nudges")
async def burnout_nudges(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Send wellness nudges to users with elevated burnout signals."""
    return await nudge_bot_service.send_burnout_nudges(db, organization_id)


@router.post("/{organization_id}/action-plan-reminders")
async def action_plan_reminders(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Remind owners of overdue/upcoming action plans."""
    return await nudge_bot_service.send_action_plan_reminders(db, organization_id)


@router.post("/{organization_id}/recognition-prompts")
async def recognition_prompts(
    organization_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Prompt users who haven't given recognition recently."""
    return await nudge_bot_service.send_recognition_prompts(db, organization_id)
