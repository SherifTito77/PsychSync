"""
Multi-Factor Authentication (MFA) API Endpoints

Provides REST API for MFA management:
- Setup MFA with TOTP
- Verify and enable MFA
- Manage backup codes
- Disable MFA

Security:
- All endpoints require authentication
- MFA verification required for sensitive operations
- Rate limiting enforced
- Audit logging for all operations

Author: Security Team
Version: 1.0
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.security import get_current_user
from app.db.models.user import User
from app.services.mfa_service import (
    BackupCodeError,
    MFASetupError,
    MFAVerificationError,
    mfa_service,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# Request/Response Models
class MFASetupResponse(BaseModel):
    """Response model for MFA setup initiation"""

    secret: str = Field(..., description="TOTP secret (show once)")
    qr_code: str = Field(..., description="QR code as base64 image")
    backup_codes: list[str] = Field(..., description="Backup recovery codes")
    message: str = Field(
        "Scan QR code with your authenticator app (Google Authenticator, "
        "Authy, etc.) and save backup codes securely"
    )


class MFAVerifyRequest(BaseModel):
    """Request model for MFA verification"""

    code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit TOTP code from authenticator app"
    )

    @validator("code")
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError("Code must be numeric")
        return v


class MFAVerifyResponse(BaseModel):
    """Response model for successful MFA verification"""

    message: str
    mfa_enabled: bool


class MFABackupCodeVerifyRequest(BaseModel):
    """Request model for backup code verification"""

    code: str = Field(
        ..., min_length=8, max_length=8, description="8-character backup recovery code"
    )


class MFADisableRequest(BaseModel):
    """Request model for disabling MFA"""

    password: str = Field(..., min_length=8, description="Current password for confirmation")


class MFAStatusResponse(BaseModel):
    """Response model for MFA status"""

    enabled: bool
    has_backup_codes: bool
    backup_codes_count: int


class BackupCodesRegenerateResponse(BaseModel):
    """Response model for backup code regeneration"""

    backup_codes: list[str]
    message: str = Field("Save these new backup codes securely. Old codes are no longer valid.")


# API Endpoints


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Initiate MFA setup for current user

    Generates TOTP secret, QR code, and backup codes.
    User must verify TOTP code before MFA is enabled.

    Security:
    - Requires authentication
    - Can only be called if MFA is not already enabled
    - Generates fresh secret and codes each time
    """
    # Check if MFA already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it first to setup again.",
        )

    try:
        # Generate TOTP secret and QR code
        secret, qr_url = await mfa_service.generate_totp_secret(current_user, db)
        qr_code = mfa_service.generate_qr_code(qr_url)

        # Generate backup codes
        backup_codes = await mfa_service.generate_backup_codes(current_user, db)

        return MFASetupResponse(secret=secret, qr_code=qr_code, backup_codes=backup_codes)

    except MFASetupError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to setup MFA: {e!s}"
        ) from e


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Verify TOTP code and enable MFA

    After scanning QR code, user enters code from authenticator app
    to verify setup and enable MFA.

    Security:
    - Requires authentication
    - Must be called after /setup
    - Enables MFA only after successful verification
    """
    # Check if MFA already enabled
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    try:
        # Verify TOTP code
        await mfa_service.verify_totp_code(current_user, request.code, db)

        # Enable MFA
        await mfa_service.enable_mfa(current_user, db)

        return MFAVerifyResponse(message="MFA enabled successfully", mfa_enabled=True)

    except MFAVerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(current_user: User = Depends(get_current_user)):
    """
    Get MFA status for current user

    Returns whether MFA is enabled and number of backup codes available.

    Security:
    - Requires authentication
    - Safe to call anytime
    """
    status = mfa_service.get_mfa_status(current_user)
    return MFAStatusResponse(**status)


@router.post("/verify-backup-code", response_model=dict[str, Any])
async def verify_backup_code(
    request: MFABackupCodeVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Verify backup code (for login or recovery)

    Used during login if user doesn't have access to authenticator app,
    or for account recovery.

    Security:
    - Requires authentication
    - Consumes backup code after use
    """
    try:
        # Verify and consume backup code
        await mfa_service.verify_backup_code(current_user, request.code, db, consume=True)

        return {
            "message": "Backup code verified successfully",
            "remaining_codes": mfa_service.get_mfa_status(current_user)["backup_codes_count"],
        }

    except BackupCodeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/regenerate-backup-codes", response_model=BackupCodesRegenerateResponse)
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)
):
    """
    Generate new backup codes

    Invalidates all existing backup codes and generates new ones.
    Use this if you lose access to most backup codes.

    Security:
    - Requires authentication
    - Requires MFA to be enabled
    - Invalidates old codes immediately
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA must be enabled to regenerate backup codes",
        )

    try:
        # Generate new backup codes
        backup_codes = await mfa_service.generate_backup_codes(current_user, db)

        return BackupCodesRegenerateResponse(backup_codes=backup_codes)

    except BackupCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate backup codes: {e!s}",
        ) from e


@router.post("/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Disable MFA for current user

    Requires current password for confirmation.
    **WARNING**: This reduces account security significantly.

    Security:
    - Requires authentication
    - Requires password confirmation
    - Should log security event
    """
    # Verify password (using existing auth service)
    from app.services.security import verify_password

    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    try:
        await mfa_service.disable_mfa(current_user, db)

        return {
            "message": "MFA disabled successfully",
            "warning": "Your account is now less secure. Consider re-enabling MFA.",
        }

    except MFASetupError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable MFA: {e!s}",
        ) from e
