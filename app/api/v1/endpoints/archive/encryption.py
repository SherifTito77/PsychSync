"""
Database Encryption Management API Endpoints

Provides endpoints for managing encryption keys and testing encryption.
Admin-only access for security.

Access: Administrators only
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.db.models.user import User
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/encryption", tags=["encryption-management"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is admin"""
    if current_user.is_superuser:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required"
    )


# =============================================================================
# Pydantic Schemas
# =============================================================================


class EncryptRequest(BaseModel):
    """Request schema for encryption test"""

    plaintext: str = Field(..., description="Data to encrypt")


class EncryptResponse(BaseModel):
    """Response schema for encryption result"""

    success: bool
    encrypted_data: str
    message: str


class DecryptRequest(BaseModel):
    """Request schema for decryption test"""

    encrypted_data: str = Field(..., description="Encrypted JSON string")


class DecryptResponse(BaseModel):
    """Response schema for decryption result"""

    success: bool
    decrypted_data: str
    message: str


class KeyRotationRequest(BaseModel):
    """Request schema for key rotation"""

    current_password: str = Field(..., description="Password to protect new key")
    new_key_password: str = Field(..., description="Password for new key export")


class KeyStatusResponse(BaseModel):
    """Response schema for key status"""

    encryption_enabled: bool
    key_type: str
    key_size: int
    can_rotate: bool


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/test/encrypt", response_model=EncryptResponse)
async def test_encryption(
    request: EncryptRequest,
    admin_user: User = Depends(get_admin_user),
):
    """
    Test encryption on a string.

    **Admin Only**

    Useful for verifying encryption is working correctly.

    **Request Body:**
    ```json
    {
      "plaintext": "sensitive data to encrypt"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "encrypted_data": "{\"nonce\":\"...\",\"ciphertext\":\"...\",\"version\":1}",
      "message": "Data encrypted successfully"
    }
    ```
    """

    try:
        encrypted = encryption_service.encrypt(request.plaintext)

        return EncryptResponse(
            success=True,
            encrypted_data=encrypted,
            message="Data encrypted successfully",
        )

    except Exception as e:
        logger.error(f"Encryption test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption failed: {str(e)}",
        )


@router.post("/test/decrypt", response_model=DecryptResponse)
async def test_decryption(
    request: DecryptRequest,
    admin_user: User = Depends(get_admin_user),
):
    """
    Test decryption on an encrypted string.

    **Admin Only**

    Useful for verifying encrypted data can be decrypted.

    **Request Body:**
    ```json
    {
      "encrypted_data": "{\"nonce\":\"...\",\"ciphertext\":\"...\",\"version\":1}"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "decrypted_data": "original plaintext",
      "message": "Data decrypted successfully"
    }
    ```
    """

    try:
        decrypted = encryption_service.decrypt(request.encrypted_data)

        # Convert to string if needed
        if isinstance(decrypted, str):
            decrypted_str = decrypted
        elif isinstance(decrypted, dict):
            decrypted_str = str(decrypted)
        else:
            decrypted_str = str(decrypted)

        return DecryptResponse(
            success=True,
            decrypted_data=decrypted_str,
            message="Data decrypted successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decryption failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Decryption test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}",
        )


@router.get("/status", response_model=KeyStatusResponse)
async def get_encryption_status(
    admin_user: User = Depends(get_admin_user),
):
    """
    Get encryption system status.

    **Admin Only**

    Returns information about the encryption configuration.

    **Response:**
    ```json
    {
      "encryption_enabled": true,
      "key_type": "AES-256-GCM",
      "key_size": 256,
      "can_rotate": true
    }
    ```
    """

    try:
        # Check if encryption is properly configured
        has_key = encryption_service.master_key is not None
        key_size = len(encryption_service.master_key) * 8 if has_key else 0  # bits

        return KeyStatusResponse(
            encryption_enabled=has_key,
            key_type="AES-256-GCM",
            key_size=key_size,
            can_rotate=has_key,
        )

    except Exception as e:
        logger.error(f"Failed to get encryption status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}",
        )


@router.post("/key/export")
async def export_encryption_key(
    password: str,
    admin_user: User = Depends(get_admin_user),
):
    """
    Export the current encryption key (password-protected).

    **Admin Only**

    Exports the encryption key encrypted with a password.
    Store this securely for backup purposes.

    **Query Parameters:**
    - password: Password to protect the exported key

    **Response:**
    ```json
    {
      "success": true,
      "encrypted_key": "base64-encoded-encrypted-key",
      "message": "Key exported successfully. Store this securely."
    }
    ```
    """

    try:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required"
            )

        # Export key encrypted with password
        encrypted_key = encryption_service.export_key_encrypted(
            encryption_service.master_key, password
        )

        return {
            "success": True,
            "encrypted_key": encrypted_key,
            "message": "Key exported successfully. Store this securely.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export key: {str(e)}",
        )


@router.post("/key/rotate")
async def rotate_encryption_key(
    request: KeyRotationRequest,
    admin_user: User = Depends(get_admin_user),
):
    """
    Rotate to a new encryption key.

    **Admin Only**

    ⚠️ **WARNING**: After rotating the key, you must re-encrypt all
    encrypted data in the database. This is a complex operation that
    should be done during a maintenance window.

    Steps after key rotation:
    1. Export old key (backup)
    2. Generate new key
    3. Decrypt all encrypted data with old key
    4. Encrypt all data with new key
    5. Update database records
    6. Verify data integrity
    7. Test decryption with new key

    **Request Body:**
    ```json
    {
      "current_password": "password-for-backup",
      "new_key_password": "password-for-new-key"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "old_key_export": "base64-encoded-old-key",
      "new_key_export": "base64-encoded-new-key",
      "message": "Key rotated successfully. Re-encrypt all data now."
    }
    ```
    """

    try:
        # Export old key for backup
        old_key_export = encryption_service.export_key_encrypted(
            encryption_service.master_key, request.current_password
        )

        # Generate new key
        new_key = encryption_service.generate_new_key()

        # Export new key
        new_key_export = encryption_service.export_key_encrypted(
            new_key, request.new_key_password
        )

        # Rotate to new key
        encryption_service.rotate_key(new_key)

        logger.warning(f"Encryption key rotated by admin {admin_user.id}")

        return {
            "success": True,
            "old_key_export": old_key_export,
            "new_key_export": new_key_export,
            "message": "Key rotated successfully. You must now re-encrypt all encrypted data. See documentation for procedure.",
        }

    except Exception as e:
        logger.error(f"Failed to rotate key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate key: {str(e)}",
        )


@router.get("/fields/sensitive")
async def list_sensitive_fields(
    admin_user: User = Depends(get_admin_user),
):
    """
    List all database fields that should be encrypted.

    **Admin Only**

    Returns a comprehensive list of sensitive fields based on
    HIPAA requirements and data classification.

    **Response:**
    ```json
    {
      "sensitive_fields": [
        {
          "table": "users",
          "column": "email",
          "reason": "PII - Personal Identifiable Information",
          "priority": "high"
        },
        ...
      ],
      "total_fields": 42
    }
    ```
    """

    try:
        # Import here to avoid circular imports
        pass

        # Define sensitive fields manually for clarity
        sensitive_fields = [
            # PII (Personally Identifiable Information)
            {
                "table": "users",
                "column": "email",
                "reason": "PII - Email address",
                "priority": "high",
            },
            {
                "table": "users",
                "column": "full_name",
                "reason": "PII - Full name",
                "priority": "high",
            },
            {
                "table": "users",
                "column": "two_factor_secret",
                "reason": "Authentication data - MFA secret",
                "priority": "critical",
            },
            {
                "table": "users",
                "column": "two_factor_recovery_codes",
                "reason": "Authentication data - Recovery codes",
                "priority": "critical",
            },
            # PHI (Protected Health Information)
            {
                "table": "clinical_screening",
                "column": "responses",
                "reason": "PHI - Assessment responses",
                "priority": "critical",
            },
            {
                "table": "clinical_screening",
                "column": "notes",
                "reason": "PHI - Clinical notes",
                "priority": "critical",
            },
            {
                "table": "clinical_screening",
                "column": "diagnosis",
                "reason": "PHI - Diagnosis information",
                "priority": "critical",
            },
            # Additional sensitive fields
            {
                "table": "biometric_keys",
                "column": "public_key",
                "reason": "Security - Cryptographic key material",
                "priority": "high",
            },
        ]

        return {
            "sensitive_fields": sensitive_fields,
            "total_fields": len(sensitive_fields),
        }

    except Exception as e:
        logger.error(f"Failed to list sensitive fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list fields: {str(e)}",
        )


@router.post("/data/re-encrypt")
async def re_encrypt_data(
    table_name: str,
    column_name: str,
    batch_size: int = 100,
    admin_user: User = Depends(get_admin_user),
):
    """
    Re-encrypt all data in a specific table/column.

    **Admin Only**

    ⚠️ **DANGER ZONE**: This operation will decrypt and re-encrypt
    all data in the specified column. Use with extreme caution
    and always backup first!

    This is typically used after key rotation.

    **Query Parameters:**
    - table_name: Name of the table
    - column_name: Name of the column to re-encrypt
    - batch_size: Number of records to process per batch (default: 100)

    **Response:**
    ```json
    {
      "success": true,
      "records_processed": 1234,
      "records_failed": 0,
      "message": "Re-encryption complete"
    }
    ```
    """

    try:
        # TODO: Implement batch re-encryption
        # This would:
        # 1. Query records in batches
        # 2. Decrypt each value with old key
        # 3. Encrypt each value with new key
        # 4. Update record
        # 5. Continue until all records processed

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Re-encryption not yet implemented. Use manual migration.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to re-encrypt data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Re-encryption failed: {str(e)}",
        )
