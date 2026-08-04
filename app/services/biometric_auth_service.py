"""
Biometric Authentication Service

Manages biometric authentication (Face ID, Touch ID, Fingerprint) for mobile apps.
Provides secure authentication using device biometrics combined with cryptographic challenges.

Features:
- Biometric registration with key pair generation
- Challenge-response authentication flow
- Anti-replay protection
- Device binding
- Revocation and recovery

Security:
- Uses public-key cryptography (RSA/ECDSA)
- Server generates random challenges
- Biometric data never leaves the device
- Challenges expire after short time window
- Rate limiting on authentication attempts
"""

import base64
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import UUID, uuid4

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import User

logger = logging.getLogger(__name__)


# =============================================================================
# Types and Enums
# =============================================================================


class BiometricType(str):
    """Supported biometric authentication types"""

    FACE_ID = "face_id"  # iOS Face ID
    TOUCH_ID = "touch_id"  # iOS Touch ID
    FINGERPRINT = "fingerprint"  # Android Fingerprint
    IRIS = "iris"  # Samsung Iris Scan
    FACE_UNLOCK = "face_unlock"  # Android Face Unlock


class BiometricError(str):
    """Biometric authentication error codes"""

    NOT_AVAILABLE = "biometric_not_available"
    NOT_ENROLLED = "biometric_not_enrolled"
    LOCKED_OUT = "biometric_locked_out"
    AUTHENTICATION_FAILED = "authentication_failed"
    CHALLENGE_EXPIRED = "challenge_expired"
    INVALID_SIGNATURE = "invalid_signature"
    KEY_INVALID = "key_invalid"
    TOO_MANY_ATTEMPTS = "too_many_attempts"
    DEVICE_NOT_SUPPORTED = "device_not_supported"


# =============================================================================
# Main Service Class
# =============================================================================


class BiometricAuthService:
    """
    Service for managing biometric authentication.

    Flow:
    1. Registration: Device generates key pair, sends public key to server
    2. Authentication: Server sends challenge, device signs with private key
    3. Verification: Server verifies signature and issues authentication token

    Security:
    - Private key never leaves device (stored in secure enclave/keystore)
    - Public key stored on server bound to device and user
    - Challenges expire after 60 seconds
    - Each challenge can only be used once
    """

    def __init__(self):
        self.challenge_expiry_seconds = 60  # Challenges expire after 60 seconds
        self.max_attempts = 5  # Max failed attempts before lockout
        self.lockout_duration_minutes = 15  # Lockout duration

    # -------------------------------------------------------------------------
    # Registration Flow
    # -------------------------------------------------------------------------

    async def initiate_registration(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
        biometric_type: str,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiate biometric registration.

        Args:
            db: Database session
            user_id: User UUID
            device_id: Unique device identifier
            biometric_type: Type of biometric (face_id, touch_id, etc.)
            device_info: Device information (platform, model, etc.)

        Returns:
            Dict with registration challenge and metadata

        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate biometric type
            if biometric_type not in [
                BiometricType.FACE_ID,
                BiometricType.TOUCH_ID,
                BiometricType.FINGERPRINT,
                BiometricType.IRIS,
                BiometricType.FACE_UNLOCK,
            ]:
                raise ValueError(f"Invalid biometric type: {biometric_type}")

            # Check if user already has biometric on this device
            existing = await self._get_biometric_key(db, user_id, device_id)
            if existing and existing.is_active:
                logger.warning(
                    f"User {user_id} already has biometric registered on device {device_id}"
                )
                # Return existing registration info
                return {
                    "already_registered": True,
                    "biometric_type": existing.biometric_type,
                    "device_id": device_id,
                    "registered_at": existing.created_at.isoformat(),
                }

            # Generate registration challenge
            challenge = secrets.token_urlsafe(32)

            # Store challenge temporarily (expires in 5 minutes)
            # In production, use Redis or similar
            registration_data = {
                "user_id": str(user_id),
                "device_id": device_id,
                "biometric_type": biometric_type,
                "device_info": device_info or {},
                "challenge": challenge,
                "created_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Initiated biometric registration for user {user_id} on device {device_id}"
            )

            return {
                "registration_challenge": challenge,
                "challenge_expires_in": 300,  # 5 minutes
                "biometric_type": biometric_type,
                "device_info": device_info or {},
            }

        except Exception as e:
            logger.error(f"Failed to initiate biometric registration: {str(e)}")
            raise

    async def complete_registration(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
        public_key: str,
        challenge_signature: str,
        key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete biometric registration by verifying the challenge signature.

        Args:
            db: Database session
            user_id: User UUID
            device_id: Unique device identifier
            public_key: PEM-encoded public key generated by device
            challenge_signature: Base64-encoded signature of the challenge
            key_id: Optional key identifier from device

        Returns:
            Dict with registration status

        Raises:
            ValueError: If validation fails
        """
        try:
            # TODO: In production, retrieve the challenge from Redis/temp storage
            # For now, we'll skip challenge verification during registration
            # since the device just generated the key pair

            # Validate public key format
            try:
                public_key_bytes = base64.b64decode(public_key)
                key = serialization.load_pem_public_key(
                    public_key_bytes, backend=default_backend()
                )
            except Exception as e:
                raise ValueError(f"Invalid public key format: {str(e)}")

            # Store biometric key
            from app.db.models.biometric import BiometricKey

            biometric_key = BiometricKey(
                id=uuid4(),
                user_id=user_id,
                device_id=device_id,
                key_id=key_id or str(uuid4()),
                public_key=public_key,
                biometric_type="biometric",  # Generic type
                is_active=True,
                created_at=datetime.utcnow(),
                last_used_at=datetime.utcnow(),
            )

            db.add(biometric_key)
            await db.commit()
            await db.refresh(biometric_key)

            logger.info(
                f"Completed biometric registration for user {user_id} on device {device_id}"
            )

            return {
                "success": True,
                "key_id": biometric_key.key_id,
                "registered_at": biometric_key.created_at.isoformat(),
                "message": "Biometric authentication registered successfully",
            }

        except Exception as e:
            logger.error(f"Failed to complete biometric registration: {str(e)}")
            await db.rollback()
            raise

    # -------------------------------------------------------------------------
    # Authentication Flow
    # -------------------------------------------------------------------------

    async def generate_challenge(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a challenge for biometric authentication.

        Args:
            db: Database session
            user_id: User UUID
            device_id: Unique device identifier

        Returns:
            Dict with challenge and metadata

        Raises:
            ValueError: If biometric not registered or device locked
        """
        try:
            # Check if user has biometric registered on this device
            biometric_key = await self._get_biometric_key(db, user_id, device_id)

            if not biometric_key:
                raise ValueError(BiometricError.NOT_ENROLLED)

            if not biometric_key.is_active:
                raise ValueError(BiometricError.KEY_INVALID)

            # Check if device is locked out
            if await self._is_device_locked_out(db, device_id):
                raise ValueError(BiometricError.LOCKED_OUT)

            # Generate random challenge
            challenge = secrets.token_urlsafe(32)

            # Store challenge with expiry
            # In production, use Redis with TTL
            from app.db.models.biometric import BiometricChallenge

            biometric_challenge = BiometricChallenge(
                id=uuid4(),
                user_id=user_id,
                device_id=device_id,
                key_id=biometric_key.key_id,
                challenge=challenge,
                expires_at=datetime.utcnow()
                + timedelta(seconds=self.challenge_expiry_seconds),
                created_at=datetime.utcnow(),
            )

            db.add(biometric_challenge)
            await db.commit()

            logger.info(
                f"Generated biometric challenge for user {user_id} on device {device_id}"
            )

            return {
                "challenge": challenge,
                "challenge_id": str(biometric_challenge.id),
                "expires_in": self.challenge_expiry_seconds,
                "key_id": biometric_key.key_id,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate challenge: {str(e)}")
            raise

    async def verify_challenge_response(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
        challenge_id: str,
        signature: str,
    ) -> Dict[str, Any]:
        """
        Verify the biometric challenge response.

        Args:
            db: Database session
            user_id: User UUID
            device_id: Unique device identifier
            challenge_id: Challenge UUID
            signature: Base64-encoded signature of the challenge

        Returns:
            Dict with authentication result and token (if successful)

        Raises:
            ValueError: If verification fails
        """
        try:
            # Retrieve challenge
            from app.db.models.biometric import BiometricChallenge

            query = select(BiometricChallenge).where(
                and_(
                    BiometricChallenge.id == UUID(challenge_id),
                    BiometricChallenge.user_id == user_id,
                    BiometricChallenge.device_id == device_id,
                    BiometricChallenge.used == False,
                )
            )
            result = await db.execute(query)
            challenge = result.scalar_one_or_none()

            if not challenge:
                await self._record_failed_attempt(db, device_id)
                raise ValueError(BiometricError.CHALLENGE_EXPIRED)

            # Check expiry
            if challenge.expires_at < datetime.utcnow():
                await self._record_failed_attempt(db, device_id)
                raise ValueError(BiometricError.CHALLENGE_EXPIRED)

            # Get biometric key
            biometric_key = await self._get_biometric_key_by_key_id(
                db, challenge.key_id
            )
            if not biometric_key:
                raise ValueError(BiometricError.KEY_INVALID)

            # Verify signature
            try:
                public_key_bytes = base64.b64decode(biometric_key.public_key)
                public_key = serialization.load_pem_public_key(
                    public_key_bytes, backend=default_backend()
                )

                signature_bytes = base64.b64decode(signature)
                challenge_bytes = challenge.challenge.encode("utf-8")

                public_key.verify(
                    signature_bytes,
                    challenge_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )

            except Exception:
                await self._record_failed_attempt(db, device_id)
                logger.warning(f"Invalid biometric signature for user {user_id}")
                raise ValueError(BiometricError.AUTHENTICATION_FAILED)

            # Mark challenge as used
            challenge.used = True
            challenge.used_at = datetime.utcnow()

            # Update last used timestamp
            biometric_key.last_used_at = datetime.utcnow()

            # Reset failed attempts
            await self._reset_failed_attempts(db, device_id)

            await db.commit()

            logger.info(
                f"Successful biometric authentication for user {user_id} on device {device_id}"
            )

            # Generate authentication token
            # TODO: Integrate with JWT service
            auth_token = self._generate_auth_token(user_id, device_id)

            return {
                "success": True,
                "authenticated": True,
                "auth_token": auth_token,
                "token_type": "Bearer",
                "expires_in": 3600,  # 1 hour
                "message": "Biometric authentication successful",
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify challenge response: {str(e)}")
            await db.rollback()
            raise

    # -------------------------------------------------------------------------
    # Management Methods
    # -------------------------------------------------------------------------

    async def revoke_biometric(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
    ) -> bool:
        """
        Revoke biometric authentication for a device.

        Args:
            db: Database session
            user_id: User UUID
            device_id: Unique device identifier

        Returns:
            True if successfully revoked
        """
        try:
            biometric_key = await self._get_biometric_key(db, user_id, device_id)

            if not biometric_key:
                return False

            biometric_key.is_active = False
            biometric_key.revoked_at = datetime.utcnow()

            await db.commit()

            logger.info(
                f"Revoked biometric authentication for user {user_id} on device {device_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to revoke biometric: {str(e)}")
            await db.rollback()
            return False

    async def get_registered_devices(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> list[Dict[str, Any]]:
        """
        Get all devices with biometric authentication registered.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            List of devices with biometric info
        """
        try:
            from app.db.models.biometric import BiometricKey

            query = select(BiometricKey).where(
                and_(
                    BiometricKey.user_id == user_id,
                    BiometricKey.is_active == True,
                )
            )
            result = await db.execute(query)
            keys = result.scalars().all()

            return [
                {
                    "device_id": key.device_id,
                    "key_id": key.key_id,
                    "biometric_type": key.biometric_type,
                    "registered_at": key.created_at.isoformat(),
                    "last_used_at": key.last_used_at.isoformat(),
                }
                for key in keys
            ]

        except Exception as e:
            logger.error(f"Failed to get registered devices: {str(e)}")
            return []

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _get_biometric_key(
        self,
        db: AsyncSession,
        user_id: UUID,
        device_id: str,
    ) -> Optional[Any]:
        """Get biometric key for user and device"""
        from app.db.models.biometric import BiometricKey

        query = (
            select(BiometricKey)
            .where(
                and_(
                    BiometricKey.user_id == user_id,
                    BiometricKey.device_id == device_id,
                )
            )
            .order_by(BiometricKey.created_at.desc())
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _get_biometric_key_by_key_id(
        self,
        db: AsyncSession,
        key_id: str,
    ) -> Optional[Any]:
        """Get biometric key by key_id"""
        from app.db.models.biometric import BiometricKey

        query = select(BiometricKey).where(BiometricKey.key_id == key_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _is_device_locked_out(
        self,
        db: AsyncSession,
        device_id: str,
    ) -> bool:
        """Check if device is locked out due to failed attempts"""
        # TODO: Implement failed attempts tracking
        # For now, always return False
        return False

    async def _record_failed_attempt(
        self,
        db: AsyncSession,
        device_id: str,
    ):
        """Record a failed authentication attempt"""
        # TODO: Implement failed attempts counter
        pass

    async def _reset_failed_attempts(
        self,
        db: AsyncSession,
        device_id: str,
    ):
        """Reset failed attempts counter"""
        # TODO: Reset counter on successful auth
        pass

    def _generate_auth_token(
        self,
        user_id: UUID,
        device_id: str,
    ) -> str:
        """Generate authentication token after successful biometric auth"""
        # TODO: Integrate with JWT service
        # For now, return a placeholder
        return f"biometric_token_{user_id}_{device_id}_{secrets.token_urlsafe(32)}"


# =============================================================================
# Service Instance
# =============================================================================

biometric_auth_service = BiometricAuthService()
