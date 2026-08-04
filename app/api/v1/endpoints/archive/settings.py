"""
User Settings API Endpoints
Manages user profile, preferences, privacy, and billing settings
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["settings"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ProfileSettings(BaseModel):
    """User profile settings"""

    name: str
    email: str
    company: str = ""
    title: str = ""
    bio: str = ""
    avatar: str = ""


class PreferencesSettings(BaseModel):
    """User preferences"""

    emailNotifications: bool = True
    weeklyReports: bool = True
    teamUpdates: bool = True
    assessmentReminders: bool = True
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"


class PrivacySettings(BaseModel):
    """Privacy settings"""

    profileVisibility: str = "team"
    shareAssessmentResults: bool = True
    dataSharing: bool = False
    twoFactorEnabled: bool = False


class BillingSettings(BaseModel):
    """Billing information"""

    plan: str = "free"
    billingEmail: str = ""
    nextBillingDate: str | None = None
    cancelAtPeriodEnd: bool = False


class SettingsResponse(BaseModel):
    """Complete user settings"""

    profile: ProfileSettings
    preferences: PreferencesSettings
    privacy: PrivacySettings
    billing: BillingSettings


class SettingsUpdate(BaseModel):
    """Settings update request"""

    profile: ProfileSettings | None = None
    preferences: PreferencesSettings | None = None
    privacy: PrivacySettings | None = None
    billing: BillingSettings | None = None


# ============================================================================
# Mock Data Store (In production, this would be in the database)
# ============================================================================

# Mock user settings - in production, fetch from database based on user_id
_mock_settings = {
    "profile": {
        "name": "Demo User",
        "email": "demo@psychsync.com",
        "company": "PsychSync",
        "title": "Team Member",
        "bio": "Psychology and wellness enthusiast",
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
        "billingEmail": "demo@psychsync.com",
        "nextBillingDate": (datetime.now() + timedelta(days=30)).isoformat(),
        "cancelAtPeriodEnd": False,
    },
}


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    """
    Get user settings

    **Returns:**
    Complete user settings including profile, preferences, privacy, and billing
    """
    # In production, fetch from database using current user ID from auth token
    return SettingsResponse(**_mock_settings)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate) -> SettingsResponse:
    """
    Update user settings

    **Args:**
        update: Settings update with any combination of profile, preferences, privacy, or billing

    **Returns:**
    Updated complete settings
    """
    # In production, update in database and validate changes

    # Update mock settings
    if update.profile:
        _mock_settings["profile"].update(update.profile.model_dump(exclude_unset=True))
    if update.preferences:
        _mock_settings["preferences"].update(
            update.preferences.model_dump(exclude_unset=True)
        )
    if update.privacy:
        _mock_settings["privacy"].update(update.privacy.model_dump(exclude_unset=True))
    if update.billing:
        billing_data = update.billing.model_dump(exclude_unset=True)
        _mock_settings["billing"].update(billing_data)

    return SettingsResponse(**_mock_settings)


@router.get("/settings/health")
async def health_check():
    """Health check for settings service"""
    return {
        "status": "healthy",
        "service": "Settings Service",
        "timestamp": datetime.utcnow().isoformat(),
    }
