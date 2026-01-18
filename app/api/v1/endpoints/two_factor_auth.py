"""
Two-Factor Authentication API Endpoints
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.api.deps import get_async_db, get_current_active_user
from app.db.models.user import User
from app.services.two_factor_service import two_factor_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================


class TwoFactorEnableResponse(BaseModel):
    """Response when enabling 2FA"""

    secret: str = Field(..., description="TOTP secret key")
    qr_code: str = Field(..., description="QR code data URL")
    recovery_codes: list[str] = Field(..., description="Recovery codes (store securely!)")
    message: str


class TwoFactorVerifyRequest(BaseModel):
    """Request to verify 2FA setup"""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class TwoFactorDisableRequest(BaseModel):
    """Request to disable 2FA"""

    password: str = Field(..., description="Current password for verification")


class TwoFactorLoginRequest(BaseModel):
    """Request for 2FA code during login"""

    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP or recovery code")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/enable", response_model=TwoFactorEnableResponse)
async def enable_two_factor(
    current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
    """
    Enable 2FA for the current user

    Returns TOTP secret, QR code, and recovery codes.
    User must verify the setup with the TOTP code before 2FA becomes active.
    """
    # Check if already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled. Disable first to re-setup.",
        )

    try:
        result = two_factor_service.enable_2fa_for_user(current_user, db)
        logger.info(f"2FA enabled for user: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"Error enabling 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to enable 2FA"
        ) from e


@router.post("/verify")
async def verify_two_factor_setup(
    request: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """
    Verify 2FA setup with TOTP code

    Call this after /enable to confirm 2FA is working correctly.
    """
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not setup. Call /enable first."
        )

    # Verify code
    if not two_factor_service.verify_totp_code(current_user.two_factor_secret, request.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    logger.info(f"2FA verified for user: {current_user.email}")
    return {"message": "2FA setup verified successfully", "enabled": True}


@router.post("/disable")
async def disable_two_factor(
    request: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """
    Disable 2FA for the current user

    Requires current password for verification.
    """
    # Verify password
    if not current_user.verify_password(request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    try:
        result = two_factor_service.disable_2fa_for_user(current_user, db)
        logger.info(f"2FA disabled for user: {current_user.email}")
        return result
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disable 2FA"
        ) from e


@router.get("/status")
async def get_two_factor_status(current_user: User = Depends(get_current_active_user)) -> dict[str, Any]:
    """
    Get 2FA status for current user
    """
    remaining_codes = two_factor_service.check_remaining_recovery_codes(current_user)

    return {
        "enabled": current_user.two_factor_enabled,
        "has_secret": bool(current_user.two_factor_secret),
        "remaining_recovery_codes": remaining_codes,
        "recommendation": "Generate new recovery codes" if remaining_codes < 3 else None,
    }


@router.post("/recovery-codes/regenerate")
async def regenerate_recovery_codes(
    password: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_async_db)
) -> dict[str, Any]:
    """
    Regenerate recovery codes

    Requires current password for verification.
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")

    # Verify password
    if not current_user.verify_password(password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    # Generate new codes
    recovery_codes = two_factor_service.generate_recovery_codes()
    hashed_recovery_codes = [two_factor_service.hash_recovery_code(code) for code in recovery_codes]

    current_user.two_factor_recovery_codes = hashed_recovery_codes
    db.commit()

    logger.info(f"Recovery codes regenerated for user: {current_user.email}")

    return {
        "recovery_codes": recovery_codes,
        "message": "New recovery codes generated. Store securely!",
    }
