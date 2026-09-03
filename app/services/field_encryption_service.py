"""
Field-Level Encryption Service

Provides granular, field-by-field encryption for sensitive data:
- Different encryption keys per field type
- Field-level access controls
- Automatic encryption/decryption at ORM level
- Audit logging of access to encrypted fields

SECURITY PRINCIPLES:
- Encrypt at field level, not just database level
- Use different keys for different sensitivity levels
- Log all access to encrypted fields
- Support for searchable encryption (where needed)

Author: Security Team
Version: 1.0
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.services.data_encryption_service import DataEncryptionService, EncryptionResult

logger = logging.getLogger(__name__)


class FieldSensitivity(Enum):
    """Field sensitivity levels for encryption key selection"""

    PUBLIC = "public"  # No encryption needed
    INTERNAL = "internal"  # Basic encryption
    CONFIDENTIAL = "confidential"  # Standard encryption
    RESTRICTED = "restricted"  # Enhanced encryption
    CRITICAL = "critical"  # Maximum encryption


@dataclass
class FieldEncryptionMetadata:
    """Metadata for encrypted field"""

    field_name: str
    sensitivity: FieldSensitivity
    encrypted_value: str
    key_id: str
    algorithm: str
    encrypted_at: datetime
    access_count: int = 0
    last_accessed: datetime | None = None


class FieldLevelEncryptionService:
    """
    Field-level encryption service

    Manages encryption at the field level with:
    - Different keys per sensitivity level
    - Access tracking and audit logging
    - Automatic key rotation support
    """

    def __init__(self, base_encryption_service: DataEncryptionService):
        """
        Initialize field-level encryption service

        Args:
            base_encryption_service: Base encryption service
        """
        self.encryption_service = base_encryption_service
        self.field_access_log: dict[str, list[dict]] = {}

        # Define which fields should be encrypted for each model
        self.encryption_rules = {
            # User model fields
            "User": {
                "email": FieldSensitivity.CONFIDENTIAL,
                "password_hash": FieldSensitivity.CRITICAL,
                "full_name": FieldSensitivity.INTERNAL,
                "phone": FieldSensitivity.CONFIDENTIAL,
                "ssn": FieldSensitivity.RESTRICTED,  # If added
                "preferences": FieldSensitivity.INTERNAL,
            },
            # Organization model fields
            "Organization": {
                "name": FieldSensitivity.INTERNAL,
                "billing_info": FieldSensitivity.RESTRICTED,
                "api_key": FieldSensitivity.CRITICAL,
            },
            # Team model fields
            "Team": {
                "name": FieldSensitivity.INTERNAL,
                "description": FieldSensitivity.INTERNAL,
            },
            # Assessment model fields
            "Assessment": {
                "title": FieldSensitivity.INTERNAL,
                "questions": FieldSensitivity.CONFIDENTIAL,
                "scoring_algorithm": FieldSensitivity.INTERNAL,
            },
            # Response model fields
            "Response": {
                "answers": FieldSensitivity.CONFIDENTIAL,
                "scores": FieldSensitivity.CONFIDENTIAL,
                "notes": FieldSensitivity.INTERNAL,
            },
        }

    def should_encrypt(self, model_name: str, field_name: str) -> bool:
        """
        Check if field should be encrypted

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            True if field should be encrypted
        """
        if model_name not in self.encryption_rules:
            return False

        return field_name in self.encryption_rules[model_name]

    def get_field_sensitivity(
        self, model_name: str, field_name: str
    ) -> FieldSensitivity | None:
        """
        Get sensitivity level for a field

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            FieldSensitivity if field should be encrypted, None otherwise
        """
        if not self.should_encrypt(model_name, field_name):
            return None

        return self.encryption_rules[model_name][field_name]

    def encrypt_field(
        self, model_name: str, field_name: str, value: Any, user_id: str | None = None
    ) -> str:
        """
        Encrypt a field value

        Args:
            model_name: Name of the model
            field_name: Name of the field
            value: Value to encrypt
            user_id: User performing encryption (for audit)

        Returns:
            Encrypted value (JSON string with metadata)

        Raises:
            ValueError: If field should not be encrypted
        """
        if not self.should_encrypt(model_name, field_name):
            raise ValueError(
                f"Field {model_name}.{field_name} is not configured for encryption"
            )

        sensitivity = self.get_field_sensitivity(model_name, field_name)

        # Convert value to string if needed
        if not isinstance(value, (str, int, float, bool)):
            value = json.dumps(value)
        else:
            value = str(value)

        # Select key based on sensitivity
        key_id = self._get_key_for_sensitivity(sensitivity)

        # Encrypt the value
        try:
            result: EncryptionResult = self.encryption_service.encrypt_pii(
                value, key_id=key_id
            )

            # Create metadata
            metadata = {
                "encrypted": result.encrypted_data,
                "key_id": result.key_id,
                "algorithm": result.algorithm,
                "nonce": result.nonce,
                "sensitivity": sensitivity.value,
                "encrypted_at": result.timestamp.isoformat(),
            }

            # Log encryption event
            logger.info(
                f"Encrypted field: {model_name}.{field_name}",
                extra={
                    "model": model_name,
                    "field": field_name,
                    "sensitivity": sensitivity.value,
                    "user_id": user_id,
                },
            )

            return json.dumps(metadata)

        except Exception as e:
            logger.error(f"Field encryption failed: {e!s}")
            raise

    def decrypt_field(
        self,
        model_name: str,
        field_name: str,
        encrypted_value: str,
        user_id: str | None = None,
    ) -> Any:
        """
        Decrypt a field value

        Args:
            model_name: Name of the model
            field_name: Name of the field
            encrypted_value: Encrypted value (JSON string with metadata)
            user_id: User requesting decryption (for audit)

        Returns:
            Decrypted value

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Parse metadata
            metadata = json.loads(encrypted_value)
            encrypted_data = metadata["encrypted"]
            key_id = metadata["key_id"]

            # Decrypt the value
            decrypted = self.encryption_service.decrypt_pii(
                encrypted_data, key_id=key_id
            )

            # Log access
            self._log_field_access(
                model_name, field_name, user_id, metadata.get("sensitivity", "unknown")
            )

            return decrypted

        except Exception as e:
            logger.error(f"Field decryption failed: {e!s}")
            raise ValueError(f"Decryption failed: {e!s}")

    def _get_key_for_sensitivity(self, sensitivity: FieldSensitivity) -> str:
        """
        Get appropriate encryption key for sensitivity level

        Args:
            sensitivity: Field sensitivity level

        Returns:
            Key ID to use
        """
        key_mapping = {
            FieldSensitivity.INTERNAL: "internal_key_v1",
            FieldSensitivity.CONFIDENTIAL: "confidential_key_v1",
            FieldSensitivity.RESTRICTED: "restricted_key_v1",
            FieldSensitivity.CRITICAL: "critical_key_v1",
        }

        return key_mapping.get(sensitivity, "internal_key_v1")

    def _log_field_access(
        self, model_name: str, field_name: str, user_id: str | None, sensitivity: str
    ) -> None:
        """
        Log field access for audit trail

        Args:
            model_name: Name of the model
            field_name: Name of the field
            user_id: User accessing the field
            sensitivity: Sensitivity level
        """
        field_key = f"{model_name}.{field_name}"

        if field_key not in self.field_access_log:
            self.field_access_log[field_key] = []

        access_record = {
            "user_id": user_id,
            "accessed_at": datetime.utcnow().isoformat(),
            "sensitivity": sensitivity,
        }

        self.field_access_log[field_key].append(access_record)

        # Limit log size
        if len(self.field_access_log[field_key]) > 1000:
            self.field_access_log[field_key] = self.field_access_log[field_key][-1000:]

        logger.info(
            f"Encrypted field accessed: {field_key}",
            extra={
                "model": model_name,
                "field": field_name,
                "user_id": user_id,
                "sensitivity": sensitivity,
            },
        )

    def get_field_access_log(
        self, model_name: str, field_name: str, limit: int = 100
    ) -> list[dict]:
        """
        Get access log for a field

        Args:
            model_name: Name of the model
            field_name: Name of the field
            limit: Maximum number of records

        Returns:
            List of access records
        """
        field_key = f"{model_name}.{field_name}"
        return self.field_access_log.get(field_key, [])[-limit:]

    def rotate_field_encryption(
        self,
        model_name: str,
        field_name: str,
        encrypted_value: str,
        new_key_id: str | None = None,
    ) -> str:
        """
        Rotate encryption for a field (decrypt with old key, encrypt with new)

        Args:
            model_name: Name of the model
            field_name: Name of the field
            encrypted_value: Current encrypted value
            new_key_id: New key ID (optional, auto-selected by sensitivity)

        Returns:
            New encrypted value
        """
        try:
            # Decrypt with current key
            decrypted = self.decrypt_field(model_name, field_name, encrypted_value)

            # Get sensitivity
            sensitivity = self.get_field_sensitivity(model_name, field_name)

            # Select new key
            if new_key_id is None:
                new_key_id = self._get_key_for_sensitivity(sensitivity)

            # Encrypt with new key
            result: EncryptionResult = self.encryption_service.encrypt_pii(
                decrypted, key_id=new_key_id
            )

            # Create new metadata
            metadata = {
                "encrypted": result.encrypted_data,
                "key_id": result.key_id,
                "algorithm": result.algorithm,
                "nonce": result.nonce,
                "sensitivity": sensitivity.value,
                "encrypted_at": result.timestamp.isoformat(),
                "rotated": True,
            }

            logger.info(
                f"Rotated encryption for field: {model_name}.{field_name}",
                extra={
                    "model": model_name,
                    "field": field_name,
                    "old_key_id": json.loads(encrypted_value).get("key_id"),
                    "new_key_id": new_key_id,
                },
            )

            return json.dumps(metadata)

        except Exception as e:
            logger.error(f"Field rotation failed: {e!s}")
            raise

    def bulk_encrypt_fields(
        self, model_name: str, data: dict[str, Any], user_id: str | None = None
    ) -> dict[str, str]:
        """
        Encrypt multiple fields in a record

        Args:
            model_name: Name of the model
            data: Dictionary of field names to values
            user_id: User performing encryption

        Returns:
            Dictionary of encrypted field values
        """
        encrypted_fields = {}

        for field_name, value in data.items():
            if self.should_encrypt(model_name, field_name):
                try:
                    encrypted_fields[field_name] = self.encrypt_field(
                        model_name, field_name, value, user_id
                    )
                except Exception as e:
                    logger.error(f"Failed to encrypt {field_name}: {e!s}")

        return encrypted_fields

    def bulk_decrypt_fields(
        self,
        model_name: str,
        encrypted_data: dict[str, str],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Decrypt multiple fields in a record

        Args:
            model_name: Name of the model
            encrypted_data: Dictionary of field names to encrypted values
            user_id: User requesting decryption

        Returns:
            Dictionary of decrypted field values
        """
        decrypted_fields = {}

        for field_name, encrypted_value in encrypted_data.items():
            if self.should_encrypt(model_name, field_name):
                try:
                    decrypted_fields[field_name] = self.decrypt_field(
                        model_name, field_name, encrypted_value, user_id
                    )
                except Exception as e:
                    logger.error(f"Failed to decrypt {field_name}: {e!s}")
                    decrypted_fields[field_name] = "[DECRYPTION FAILED]"

        return decrypted_fields


# Singleton instance (initialized in main app)
field_encryption_service: FieldLevelEncryptionService | None = None


def get_field_encryption_service() -> FieldLevelEncryptionService:
    """Get field encryption service singleton"""
    global field_encryption_service
    if field_encryption_service is None:
        from app.main import encryption_service

        field_encryption_service = FieldLevelEncryptionService(encryption_service)
    return field_encryption_service
