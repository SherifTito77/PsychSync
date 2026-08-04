from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User

router = APIRouter()


@router.get("")
async def get_settings(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user settings
    """
    # Placeholder implementation until real backend logic is ready
    return {
        "profile": {
            "name": current_user.full_name or "",
            "email": current_user.email or "",
            "company": "PsychSync",
            "title": "User",
            "bio": "",
            "avatar": "",
        },
        "preferences": {
            "emailNotifications": True,
            "weeklyReports": True,
            "teamUpdates": True,
            "assessmentReminders": True,
            "theme": "light",
            "language": "en",
            "timezone": "UTC",
        },
        "privacy": {
            "profileVisibility": "team",
            "shareAssessmentResults": True,
            "dataSharing": False,
            "twoFactorEnabled": False,
        },
        "billing": {
            "plan": "free",
            "billingEmail": current_user.email or "",
            "cancelAtPeriodEnd": False,
        },
    }


@router.put("")
async def update_settings(
    settings_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update user settings
    """
    # Placeholder implementation
    return {"message": "Settings updated successfully"}


@router.post("/avatar")
async def upload_avatar(current_user: User = Depends(get_current_user)) -> Any:
    """
    Placeholder for avatar upload
    """
    return {
        "avatarUrl": "https://ui-avatars.com/api/?name=User&background=3B82F6&color=fff"
    }
