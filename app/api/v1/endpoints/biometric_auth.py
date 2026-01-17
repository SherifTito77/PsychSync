"""
Biometric Authentication API Endpoints

Provides endpoints for biometric authentication (Face ID, Touch ID, Fingerprint).
Uses public-key cryptography for secure authentication without storing biometric data.

Access: Authenticated users
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.v1.endpoints.users import get_async_db, get_current_user
from app.db.models.user import User
from app.services.biometric_auth_service import (
    biometric_auth_service,
    BiometricType,
    BiometricError,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/biometric-auth", tags=["biometric-auth"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class InitiateRegistrationRequest(BaseModel):
    """Request schema for initiating biometric registration"""

    device_id: str = Field(..., description="Unique device identifier")
    biometric_type: str = Field(..., description="Type of biometric (face_id, touch_id, fingerprint)")
    device_info: Optional[Dict] = Field(default_factory=dict, description="Device information")


class CompleteRegistrationRequest(BaseModel):
    """Request schema for completing biometric registration"""

    device_id: str = Field(..., description="Unique device identifier")
    public_key: str = Field(..., description="PEM-encoded public key")
    challenge_signature: str = Field(..., description="Signature of registration challenge")
    key_id: Optional[str] = Field(None, description="Optional key identifier from device")


class InitiateAuthRequest(BaseModel):
    """Request schema for initiating biometric authentication"""

    device_id: str = Field(..., description="Unique device identifier")


class VerifyAuthRequest(BaseModel):
    """Request schema for verifying biometric authentication"""

    device_id: str = Field(..., description="Unique device identifier")
    challenge_id: str = Field(..., description="Challenge UUID")
    signature: str = Field(..., description="Signature of the challenge")


class RevokeBiometricRequest(BaseModel):
    """Request schema for revoking biometric authentication"""

    device_id: str = Field(..., description="Unique device identifier")


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/register/initiate")
async def initiate_biometric_registration(
    request: InitiateRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate biometric registration.

    This endpoint generates a registration challenge that the device must sign.
    The device should:
    1. Generate an RSA/ECDSA key pair
    2. Store private key in Secure Enclave/Keystore
    3. Sign the registration challenge with private key
    4. Send public key and signature to complete registration

    **Request Body:**
    ```json
    {
      "device_id": "unique-device-id",
      "biometric_type": "face_id",
      "device_info": {
        "platform": "ios",
        "model": "iPhone 14"
      }
    }
    ```
    """

    try:
        result = await biometric_auth_service.initiate_registration(
            db=db,
            user_id=current_user.id,
            device_id=request.device_id,
            biometric_type=request.biometric_type,
            device_info=request.device_info,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to initiate biometric registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate registration: {str(e)}")


@router.post("/register/complete")
async def complete_biometric_registration(
    request: CompleteRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Complete biometric registration.

    This endpoint verifies the challenge signature and stores the public key.
    After successful registration, the user can authenticate using biometrics.

    **Request Body:**
    ```json
    {
      "device_id": "unique-device-id",
      "public_key": "PEM-encoded public key",
      "challenge_signature": "base64-encoded signature",
      "key_id": "optional-key-id"
    }
    ```
    """

    try:
        result = await biometric_auth_service.complete_registration(
            db=db,
            user_id=current_user.id,
            device_id=request.device_id,
            public_key=request.public_key,
            challenge_signature=request.challenge_signature,
            key_id=request.key_id,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete biometric registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete registration: {str(e)}")


@router.post("/authenticate/initiate")
async def initiate_biometric_authentication(
    request: InitiateAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate biometric authentication.

    This endpoint generates a challenge that the device must sign using
    the registered private key.

    **Request Body:**
    ```json
    {
      "device_id": "unique-device-id"
    }
    ```

    **Response:**
    ```json
    {
      "challenge": "random-challenge-string",
      "challenge_id": "uuid",
      "expires_in": 60,
      "key_id": "key-identifier"
    }
    ```
    """

    try:
        result = await biometric_auth_service.generate_challenge(
            db=db,
            user_id=current_user.id,
            device_id=request.device_id,
        )

        return result

    except ValueError as e:
        error_msg = str(e)

        # Map specific errors to appropriate status codes
        if error_msg == BiometricError.NOT_ENROLLED:
            raise HTTPException(
                status_code=404,
                detail="Biometric not registered on this device. Please register first."
            )

        if error_msg == BiometricError.LOCKED_OUT:
            raise HTTPException(
                status_code=429,
                detail="Too many failed attempts. Please try again later."
            )

        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        logger.error(f"Failed to initiate biometric authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate authentication: {str(e)}")


@router.post("/authenticate/verify")
async def verify_biometric_authentication(
    request: VerifyAuthRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Verify biometric authentication.

    This endpoint verifies the signature of the challenge.
    If valid, it returns an authentication token.

    **Request Body:**
    ```json
    {
      "device_id": "unique-device-id",
      "challenge_id": "challenge-uuid",
      "signature": "base64-encoded signature"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "authenticated": true,
      "auth_token": "jwt-token",
      "token_type": "Bearer",
      "expires_in": 3600,
      "message": "Biometric authentication successful"
    }
    ```
    """

    try:
        result = await biometric_auth_service.verify_challenge_response(
            db=db,
            user_id=current_user.id,
            device_id=request.device_id,
            challenge_id=request.challenge_id,
            signature=request.signature,
        )

        return result

    except ValueError as e:
        error_msg = str(e)

        # Map specific errors to appropriate status codes
        if error_msg == BiometricError.CHALLENGE_EXPIRED:
            raise HTTPException(
                status_code=400,
                detail="Challenge expired. Please initiate authentication again."
            )

        if error_msg == BiometricError.AUTHENTICATION_FAILED:
            raise HTTPException(
                status_code=401,
                detail="Biometric authentication failed. Please try again."
            )

        if error_msg == BiometricError.INVALID_SIGNATURE:
            raise HTTPException(
                status_code=401,
                detail="Invalid signature. Authentication failed."
            )

        raise HTTPException(status_code=400, detail=error_msg)

    except Exception as e:
        logger.error(f"Failed to verify biometric authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify authentication: {str(e)}")


@router.post("/revoke")
async def revoke_biometric_authentication(
    request: RevokeBiometricRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revoke biometric authentication for a device.

    Call this when the user disables biometric authentication or
    when the device is lost/stolen.

    **Request Body:**
    ```json
    {
      "device_id": "unique-device-id"
    }
    ```
    """

    try:
        success = await biometric_auth_service.revoke_biometric(
            db=db,
            user_id=current_user.id,
            device_id=request.device_id,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Biometric authentication not found")

        return {
            "success": True,
            "message": "Biometric authentication revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke biometric authentication: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke: {str(e)}")


@router.get("/devices")
async def get_registered_biometric_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all devices with biometric authentication registered.

    Returns a list of devices where biometric authentication has been set up.

    **Response:**
    ```json
    [
      {
        "device_id": "unique-device-id",
        "key_id": "key-identifier",
        "biometric_type": "face_id",
        "registered_at": "2024-01-17T10:00:00Z",
        "last_used_at": "2024-01-17T12:00:00Z"
      }
    ]
    ```
    """

    try:
        devices = await biometric_auth_service.get_registered_devices(
            db=db,
            user_id=current_user.id,
        )

        return {
            "devices": devices,
            "total": len(devices),
        }

    except Exception as e:
        logger.error(f"Failed to get registered devices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve devices: {str(e)}")


@router.get("/status")
async def get_biometric_status(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get biometric authentication status for a device.

    Query parameters:
    - device_id: Unique device identifier

    **Response:**
    ```json
    {
      "enabled": true,
      "biometric_type": "face_id",
      "registered_at": "2024-01-17T10:00:00Z",
      "last_used_at": "2024-01-17T12:00:00Z"
    }
    ```
    """

    try:
        from app.db.models.biometric import BiometricKey
        from sqlalchemy import select, and_

        query = select(BiometricKey).where(
            and_(
                BiometricKey.user_id == current_user.id,
                BiometricKey.device_id == device_id,
                BiometricKey.is_active == True,
            )
        ).order_by(BiometricKey.created_at.desc())

        result = await db.execute(query)
        biometric_key = result.scalar_one_or_none()

        if not biometric_key:
            return {
                "enabled": False,
                "message": "Biometric authentication not enabled on this device"
            }

        return {
            "enabled": True,
            "biometric_type": biometric_key.biometric_type,
            "registered_at": biometric_key.created_at.isoformat(),
            "last_used_at": biometric_key.last_used_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get biometric status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")


@router.get("/types")
async def list_supported_biometric_types():
    """
    List all supported biometric authentication types.

    Returns information about available biometric types and their
    compatibility with different platforms.
    """

    return {
        "biometric_types": [
            {
                "type": BiometricType.FACE_ID,
                "name": "Face ID",
                "platform": "ios",
                "description": "3D facial recognition on iPhone X and later",
                "min_version": "iOS 11.0",
            },
            {
                "type": BiometricType.TOUCH_ID,
                "name": "Touch ID",
                "platform": "ios",
                "description": "Fingerprint authentication on iPhone 5s and later",
                "min_version": "iOS 8.0",
            },
            {
                "type": BiometricType.FINGERPRINT,
                "name": "Fingerprint",
                "platform": "android",
                "description": "Fingerprint authentication on Android devices",
                "min_version": "Android 6.0 (API 23)",
            },
            {
                "type": BiometricType.IRIS,
                "name": "Iris Scan",
                "platform": "android",
                "description": "Iris recognition on Samsung devices",
                "min_version": "Samsung-specific",
            },
            {
                "type": BiometricType.FACE_UNLOCK,
                "name": "Face Unlock",
                "platform": "android",
                "description": "Facial recognition on Android devices",
                "min_version": "Android 10.0 (API 29)",
            },
        ],
        "total_types": 5,
    }
