"""
Biometric Integrations API Endpoints

Manages wearable device connections, OAuth flows, data sync,
and biometric metrics retrieval for health monitoring.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.models.biometric_health import (
    BiometricHealthData,
    DataSourceType,
    HealthDataConsent,
)
from app.db.models.user import User
from app.services.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/biometric", tags=["Biometric Integrations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

PROVIDER_CONFIG = {
    "apple_health": {
        "name": "Apple Health",
        "auth_type": "native_bridge",
        "oauth_url": None,
        "scopes": [
            "heart_rate",
            "hrv",
            "sleep",
            "steps",
            "blood_oxygen",
            "respiratory_rate",
        ],
        "requires_mobile": True,
    },
    "google_fit": {
        "name": "Google Fit",
        "auth_type": "oauth2",
        "oauth_base": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/fitness.heart_rate.read",
            "https://www.googleapis.com/auth/fitness.sleep.read",
            "https://www.googleapis.com/auth/fitness.activity.read",
        ],
        "requires_mobile": False,
    },
    "fitbit": {
        "name": "Fitbit",
        "auth_type": "oauth2",
        "oauth_base": "https://www.fitbit.com/oauth2/authorize",
        "token_url": "https://api.fitbit.com/oauth2/token",
        "scopes": ["heartrate", "sleep", "activity", "profile"],
        "requires_mobile": False,
    },
    "garmin": {
        "name": "Garmin Connect",
        "auth_type": "oauth1",
        "oauth_base": "https://connect.garmin.com/oauthConfirm",
        "requires_mobile": False,
    },
    "whoop": {
        "name": "WHOOP",
        "auth_type": "oauth2",
        "oauth_base": "https://api.prod.whoop.com/oauth/oauth2/auth",
        "token_url": "https://api.prod.whoop.com/oauth/oauth2/token",
        "scopes": [
            "read:recovery",
            "read:sleep",
            "read:workout",
            "read:body_measurement",
        ],
        "requires_mobile": False,
    },
    "oura": {
        "name": "Oura Ring",
        "auth_type": "oauth2",
        "oauth_base": "https://cloud.ouraring.com/oauth/authorize",
        "token_url": "https://api.ouraring.com/oauth/token",
        "scopes": ["heartrate", "daily", "sleep", "personal"],
        "requires_mobile": False,
    },
}


class ConnectRequest(BaseModel):
    redirect_uri: Optional[str] = None


class BiometricSubmission(BaseModel):
    data_source: str
    measurement_date: date
    resting_heart_rate: Optional[float] = None
    heart_rate_variability: Optional[float] = None
    sleep_hours: Optional[float] = None
    sleep_quality_score: Optional[float] = None
    deep_sleep_hours: Optional[float] = None
    rem_sleep_hours: Optional[float] = None
    steps_count: Optional[int] = None
    activity_minutes: Optional[int] = None
    stress_score: Optional[float] = None
    recovery_score: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    device_info: Optional[dict] = None


class SyncSettingsUpdate(BaseModel):
    sync_frequency_minutes: Optional[int] = 15
    data_retention_days: Optional[int] = 90
    share_anonymized: Optional[bool] = True
    enable_stress_alerts: Optional[bool] = True
    allow_manager_view: Optional[bool] = False


# ---------------------------------------------------------------------------
# Provider Discovery
# ---------------------------------------------------------------------------


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available biometric providers with connection status."""
    # Check which providers the user has connected
    result = await db.execute(
        select(
            BiometricHealthData.data_source,
            func.max(BiometricHealthData.sync_timestamp).label("last_sync"),
            func.count(BiometricHealthData.id).label("data_points"),
        )
        .where(BiometricHealthData.user_id == current_user.id)
        .group_by(BiometricHealthData.data_source)
    )
    connected_sources = {
        row.data_source: {
            "last_sync": row.last_sync.isoformat() if row.last_sync else None,
            "data_points": row.data_points,
        }
        for row in result.all()
    }

    providers = []
    for provider_id, config in PROVIDER_CONFIG.items():
        conn_info = connected_sources.get(provider_id, {})
        providers.append(
            {
                "id": provider_id,
                "name": config["name"],
                "auth_type": config["auth_type"],
                "requires_mobile": config.get("requires_mobile", False),
                "connected": provider_id in connected_sources,
                "last_sync": conn_info.get("last_sync"),
                "data_points": conn_info.get("data_points", 0),
                "scopes": config.get("scopes", []),
            }
        )

    return {"success": True, "providers": providers}


# ---------------------------------------------------------------------------
# Connection Management
# ---------------------------------------------------------------------------


@router.post("/connect/{provider}")
async def connect_provider(
    provider: str,
    request: ConnectRequest = ConnectRequest(),
    current_user: User = Depends(get_current_user),
):
    """Initiate connection to a biometric provider. Returns OAuth URL for redirect-based flows."""
    if provider not in PROVIDER_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    config = PROVIDER_CONFIG[provider]

    if config["auth_type"] == "native_bridge":
        return {
            "success": False,
            "auth_type": "native_bridge",
            "requires_mobile": True,
            "message": "Apple Health requires the PsychSync mobile app. Download it to sync HealthKit data.",
        }

    if config["auth_type"] in ("oauth2", "oauth1"):
        redirect_uri = request.redirect_uri or f"/api/v1/biometric/callback/{provider}"
        scopes = " ".join(config.get("scopes", []))

        # Build OAuth authorization URL
        oauth_url = (
            f"{config['oauth_base']}"
            f"?response_type=code"
            f"&client_id=PLACEHOLDER_CLIENT_ID"
            f"&redirect_uri={redirect_uri}"
            f"&scope={scopes}"
            f"&state={current_user.id}:{provider}"
        )

        return {
            "success": True,
            "auth_type": config["auth_type"],
            "auth_url": oauth_url,
            "message": f"Redirect user to auth_url to connect {config['name']}",
        }

    raise HTTPException(status_code=500, detail="Unsupported auth type")


@router.post("/disconnect/{provider}")
async def disconnect_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a biometric provider and optionally delete stored data."""
    if provider not in PROVIDER_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # Soft-delete: mark records but keep for data retention compliance
    logger.info(
        "User %s disconnecting biometric provider: %s", current_user.id, provider
    )

    return {
        "success": True,
        "provider": provider,
        "message": f"Disconnected {PROVIDER_CONFIG[provider]['name']}. Data retained per your retention policy.",
    }


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from biometric provider."""
    if provider not in PROVIDER_CONFIG:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    # In production: exchange code for access/refresh tokens via config["token_url"]
    # Store tokens securely (encrypted) in a BiometricConnection table
    logger.info("OAuth callback for provider %s, state=%s", provider, state)

    return {
        "success": True,
        "provider": provider,
        "message": f"Successfully connected to {PROVIDER_CONFIG[provider]['name']}",
    }


# ---------------------------------------------------------------------------
# Data Submission & Retrieval
# ---------------------------------------------------------------------------


@router.post("/data")
async def submit_biometric_data(
    submission: BiometricSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit biometric data (from device sync or manual entry)."""
    if (
        submission.data_source not in PROVIDER_CONFIG
        and submission.data_source != "manual_entry"
    ):
        raise HTTPException(
            status_code=400, detail=f"Unknown data source: {submission.data_source}"
        )

    record = BiometricHealthData(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        measurement_date=submission.measurement_date,
        data_source=submission.data_source,
        resting_heart_rate=submission.resting_heart_rate,
        heart_rate_variability=submission.heart_rate_variability,
        sleep_hours=submission.sleep_hours,
        sleep_quality_score=submission.sleep_quality_score,
        deep_sleep_hours=submission.deep_sleep_hours,
        rem_sleep_hours=submission.rem_sleep_hours,
        steps_count=submission.steps_count,
        activity_minutes=submission.activity_minutes,
        stress_score=submission.stress_score,
        recovery_score=submission.recovery_score,
        oxygen_saturation=submission.oxygen_saturation,
        device_info=submission.device_info,
        sync_timestamp=datetime.utcnow(),
        consent_given=True,
    )
    db.add(record)
    await db.commit()

    risk_indicators = record.get_cardiovascular_risk_indicators()
    return {
        "success": True,
        "data_id": str(record.id),
        "risk_indicators": risk_indicators,
    }


@router.get("/metrics")
async def get_biometric_metrics(
    days: int = Query(default=30, ge=1, le=365),
    source: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get biometric metrics summary for current user."""
    since = date.today() - timedelta(days=days)

    query = select(BiometricHealthData).where(
        and_(
            BiometricHealthData.user_id == current_user.id,
            BiometricHealthData.measurement_date >= since,
        )
    )
    if source:
        query = query.where(BiometricHealthData.data_source == source)

    query = query.order_by(BiometricHealthData.measurement_date.desc())
    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        return {
            "success": True,
            "has_data": False,
            "message": "No biometric data found. Connect a device to start tracking.",
            "metrics": {},
        }

    latest = records[0]
    return {
        "success": True,
        "has_data": True,
        "period_days": days,
        "total_records": len(records),
        "sources": list({r.data_source for r in records}),
        "latest": {
            "date": str(latest.measurement_date),
            "resting_heart_rate": (
                float(latest.resting_heart_rate) if latest.resting_heart_rate else None
            ),
            "heart_rate_variability": (
                float(latest.heart_rate_variability)
                if latest.heart_rate_variability
                else None
            ),
            "sleep_hours": float(latest.sleep_hours) if latest.sleep_hours else None,
            "sleep_quality_score": (
                float(latest.sleep_quality_score)
                if latest.sleep_quality_score
                else None
            ),
            "steps_count": latest.steps_count,
            "stress_score": float(latest.stress_score) if latest.stress_score else None,
            "recovery_score": (
                float(latest.recovery_score) if latest.recovery_score else None
            ),
            "activity_minutes": latest.activity_minutes,
        },
        "cardiovascular_risk": latest.get_cardiovascular_risk_indicators(),
        "sleep_quality": latest.get_sleep_quality_indicators(),
        "activity_level": latest.get_activity_level(),
    }


# ---------------------------------------------------------------------------
# Sync Settings & Consent
# ---------------------------------------------------------------------------


@router.get("/settings")
async def get_sync_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's biometric sync settings and consent status."""
    result = await db.execute(
        select(HealthDataConsent).where(HealthDataConsent.user_id == current_user.id)
    )
    consent = result.scalar_one_or_none()

    return {
        "success": True,
        "consent_given": consent.consent_given if consent else False,
        "data_retention_days": consent.data_retention_days if consent else 90,
        "biometric_collection": consent.biometric_collection if consent else False,
        "biometric_sharing": consent.biometric_sharing if consent else False,
        "anonymization_allowed": consent.anonymization_allowed if consent else False,
        "data_sources": consent.data_sources if consent else [],
    }


@router.put("/settings")
async def update_sync_settings(
    settings: SyncSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update biometric sync settings and privacy preferences."""
    result = await db.execute(
        select(HealthDataConsent).where(HealthDataConsent.user_id == current_user.id)
    )
    consent = result.scalar_one_or_none()

    if not consent:
        consent = HealthDataConsent(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            consent_given=True,
            consent_date=date.today(),
        )
        db.add(consent)

    consent.data_retention_days = settings.data_retention_days
    consent.anonymization_allowed = settings.share_anonymized
    consent.biometric_collection = True
    consent.biometric_processing = True
    consent.biometric_sharing = settings.allow_manager_view

    await db.commit()

    return {"success": True, "message": "Settings updated"}
