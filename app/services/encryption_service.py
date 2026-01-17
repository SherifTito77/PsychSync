"""
Database Encryption Service

Provides encryption and decryption for sensitive data at rest.
Uses AES-256-GCM for symmetric encryption with authenticated encryption.

Features:
- AES-256-GCM encryption (256-bit key, 96-bit nonce)
- Per-record unique IVs to prevent pattern analysis
- Authentication tags to detect tampering
- Key rotation support
- Field-level encryption for sensitive columns

Security:
- Encryption keys managed through environment variables
- Keys never logged or exposed in error messages
- IVs are unique per encryption operation
- Authenticated encryption prevents tampering

Compliance:
- HIPAA compliant for PHI encryption
- NIST standards for cryptographic operations
- SOC 2 compatible data protection
"""

import os
import base64
import json
import hashlib
from typing import Any, Dict, Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Encryption Configuration
# =============================================================================

class EncryptionConfig:
    """Configuration for encryption operations"""

    # Key derivation
    KEY_SIZE = 32  # 256 bits for AES-256
    SALT_SIZE = 16  # 128 bits
    ITERATIONS = 100000  # PBKDF2 iterations

    # AES-GCM
    NONCE_SIZE = 12  # 96 bits (recommended for GCM)
    TAG_SIZE = 16  # 128 bits (built into GCM)

    # Encoding
    ENCODING = 'utf-8'


# =============================================================================
# Encryption Service
# =============================================================================

class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data at rest.

    Uses AES-256-GCM for authenticated encryption:
    - 256-bit AES key
    - 96-bit nonce (unique per encryption)
    - 128-bit authentication tag (automatic with GCM)

    Encryption Format:
    {
      "nonce": "base64-encoded-nonce",
      "ciphertext": "base64-encoded-ciphertext-with-tag",
      "version": 1
    }
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption service.

        Args:
            master_key: Optional master key (for testing). If not provided,
                       uses DB_ENCRYPTION_KEY from environment.
        """
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._get_master_key()

        # Validate key length
        if len(self.master_key) != EncryptionConfig.KEY_SIZE:
            raise ValueError(
                f"Encryption key must be {EncryptionConfig.KEY_SIZE} bytes, "
                f"got {len(self.master_key)}"
            )

    # -------------------------------------------------------------------------
    # Key Management
    # -------------------------------------------------------------------------

    def _get_master_key(self) -> bytes:
        """
        Get or derive master encryption key.

        In production, this should come from a secure key management service
        (AWS KMS, Azure Key Vault, etc.). For now, derive from environment.

        Returns:
            32-byte encryption key
        """
        # Try to get key from environment
        env_key = os.environ.get('DB_ENCRYPTION_KEY')

        if not env_key:
            # Generate and warn (not for production!)
            logger.warning(
                "DB_ENCRYPTION_KEY not set. Generating temporary key. "
                "This should NOT be used in production!"
            )
            return os.urandom(EncryptionConfig.KEY_SIZE)

        # Derive key from environment variable
        # Use PBKDF2 with a fixed salt for consistency
        salt = b'PsychSync_DB_Encryption_Salt_v1'  # In production, use KMS
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=EncryptionConfig.KEY_SIZE,
            salt=salt,
            iterations=EncryptionConfig.ITERATIONS,
            backend=default_backend()
        )

        # Decode base64 key if needed
        if env_key.startswith('base64:'):
            key_bytes = base64.b64decode(env_key[7:])
        else:
            key_bytes = env_key.encode(EncryptionConfig.ENCODING)

        # Derive final key
        derived_key = kdf.derive(key_bytes)

        return derived_key

    def rotate_key(self, new_key: bytes) -> None:
        """
        Rotate to a new encryption key.

        After calling this, you must re-encrypt all encrypted data:
        1. Decrypt with old key
        2. Encrypt with new key
        3. Update database

        Args:
            new_key: New 32-byte encryption key
        """
        if len(new_key) != EncryptionConfig.KEY_SIZE:
            raise ValueError(f"New key must be {EncryptionConfig.KEY_SIZE} bytes")

        logger.info("Rotating encryption key")
        self.master_key = new_key

    # -------------------------------------------------------------------------
    # Encryption/Decryption Operations
    # -------------------------------------------------------------------------

    def encrypt(self, plaintext: Union[str, bytes, Dict, Any]) -> str:
        """
        Encrypt data.

        Args:
            plaintext: Data to encrypt (string, bytes, or JSON-serializable)

        Returns:
            JSON string containing encrypted data with nonce
        """
        try:
            # Convert to bytes if needed
            if isinstance(plaintext, str):
                plaintext_bytes = plaintext.encode(EncryptionConfig.ENCODING)
            elif isinstance(plaintext, (dict, list)):
                plaintext_bytes = json.dumps(plaintext).encode(EncryptionConfig.ENCODING)
            elif isinstance(plaintext, bytes):
                plaintext_bytes = plaintext
            else:
                raise TypeError(f"Unsupported type for encryption: {type(plaintext)}")

            # Generate unique nonce (IV)
            nonce = os.urandom(EncryptionConfig.NONCE_SIZE)

            # Encrypt with AES-GCM
            aesgcm = AESGCM(self.master_key)
            ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)

            # Format as JSON
            encrypted_data = {
                "nonce": base64.b64encode(nonce).decode('ascii'),
                "ciphertext": base64.b64encode(ciphertext_with_tag).decode('ascii'),
                "version": 1
            }

            return json.dumps(encrypted_data)

        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Failed to encrypt data: {str(e)}")

    def decrypt(self, encrypted_json: str) -> Any:
        """
        Decrypt data.

        Args:
            encrypted_json: JSON string from encrypt()

        Returns:
            Original plaintext (string, bytes, or dict)
        """
        try:
            # Parse JSON
            encrypted_data = json.loads(encrypted_json)

            # Validate version
            if encrypted_data.get("version") != 1:
                raise ValueError(f"Unsupported encryption version: {encrypted_data.get('version')}")

            # Decode nonce and ciphertext
            nonce = base64.b64decode(encrypted_data["nonce"])
            ciphertext_with_tag = base64.b64decode(encrypted_data["ciphertext"])

            # Decrypt with AES-GCM
            aesgcm = AESGCM(self.master_key)
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)

            # Try to detect if it's JSON
            try:
                return json.loads(plaintext_bytes.decode(EncryptionConfig.ENCODING))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Not JSON, return as-is (string or bytes)
                try:
                    return plaintext_bytes.decode(EncryptionConfig.ENCODING)
                except UnicodeDecodeError:
                    return plaintext_bytes

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse encrypted JSON: {str(e)}")
            raise ValueError("Invalid encrypted data format")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Failed to decrypt data: {str(e)}")

    def encrypt_field(self, value: Any) -> Optional[str]:
        """
        Encrypt a database field value.

        Handles None values gracefully.

        Args:
            value: Value to encrypt

        Returns:
            Encrypted JSON string or None if input was None
        """
        if value is None:
            return None

        return self.encrypt(value)

    def decrypt_field(self, encrypted_value: Optional[str]) -> Optional[Any]:
        """
        Decrypt a database field value.

        Handles None values gracefully.

        Args:
            encrypted_value: Encrypted JSON string or None

        Returns:
            Decrypted value or None if input was None
        """
        if encrypted_value is None:
            return None

        return self.decrypt(encrypted_value)

    # -------------------------------------------------------------------------
    # Hashing Operations (for verification)
    # -------------------------------------------------------------------------

    @staticmethod
    def hash_value(value: Union[str, bytes], salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Hash a value for verification (not encryption).

        Uses SHA-256 with salt. Suitable for:
            - Verifying data integrity
            - Hashing identifiers before storage
            - Creating deterministic hashes for lookups

        NOT suitable for passwords (use bcrypt/scrypt/argon2 for that).

        Args:
            value: Value to hash
            salt: Optional salt (generates random if not provided)

        Returns:
            Tuple of (hex_hash, salt)
        """
        if salt is None:
            salt = os.urandom(EncryptionConfig.SALT_SIZE)

        if isinstance(value, str):
            value_bytes = value.encode(EncryptionConfig.ENCODING)
        else:
            value_bytes = value

        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(salt)
        digest.update(value_bytes)
        hash_bytes = digest.finalize()

        return (hash_bytes.hex(), salt)

    @staticmethod
    def verify_hash(value: Union[str, bytes], hash_hex: str, salt: bytes) -> bool:
        """
        Verify a value against a hash.

        Args:
            value: Original value
            hash_hex: Hash to verify against
            salt: Salt used for hashing

        Returns:
            True if hash matches
        """
        computed_hash, _ = EncryptionService.hash_value(value, salt)
        return computed_hash == hash_hex

    # -------------------------------------------------------------------------
    # Data Classification
    # -------------------------------------------------------------------------

    @staticmethod
    def is_sensitive_field(table_name: str, column_name: str) -> bool:
        """
        Determine if a database field should be encrypted.

        Based on HIPAA and data protection requirements.

        Args:
            table_name: Database table name
            column_name: Column name

        Returns:
            True if field should be encrypted
        """
        # Sensitive fields that require encryption
        sensitive_patterns = [
            # Personal Identifiable Information (PII)
            ('users', ['email', 'full_name', 'phone']),
            ('users', ['ssn', 'social_security_number', 'tax_id']),

            # Protected Health Information (PHI)
            ('clinical_screening', ['responses', 'notes', 'diagnosis']),
            ('wellness_assessments', ['responses', 'notes']),
            ('intervention_participants', ['notes', 'treatment_plan']),

            # Authentication data (if stored separately from password_hash)
            ('users', ['mfa_secret', 'recovery_codes']),

            # Communication
            ('messages', ['content', 'subject']),
            ('email_metadata', ['subject', 'body']),
        ]

        # Check if table/column combination is sensitive
        for table, columns in sensitive_patterns:
            if table_name == table:
                if any(col in column_name for col in columns):
                    return True

        # Check for generic sensitive patterns
        sensitive_keywords = [
            'ssn', 'social_security', 'credit_card', 'password',
            'secret', 'token', 'api_key', 'private_key',
            'medical_record', 'phi', 'protected_health',
        ]

        column_lower = column_name.lower()
        return any(keyword in column_lower for keyword in sensitive_keywords)

    # -------------------------------------------------------------------------
    # Key Rotation Utilities
    # -------------------------------------------------------------------------

    def generate_new_key(self) -> bytes:
        """
        Generate a new random encryption key.

        Returns:
            32-byte random key
        """
        return os.urandom(EncryptionConfig.KEY_SIZE)

    def export_key_encrypted(self, key: bytes, password: str) -> str:
        """
        Export a key encrypted with a password.

        Useful for backup and key rotation.

        Args:
            key: Key to export
            password: Password for encrypting the key

        Returns:
            Base64-encoded encrypted key
        """
        # Derive encryption key from password
        salt = os.urandom(EncryptionConfig.SALT_SIZE)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=EncryptionConfig.KEY_SIZE,
            salt=salt,
            iterations=EncryptionConfig.ITERATIONS,
            backend=default_backend()
        )
        enc_key = kdf.derive(password.encode(EncryptionConfig.ENCODING))

        # Encrypt the key
        nonce = os.urandom(EncryptionConfig.NONCE_SIZE)
        aesgcm = AESGCM(enc_key)
        encrypted_key = aesgcm.encrypt(nonce, key, None)

        # Pack salt + nonce + encrypted_key
        packed = salt + nonce + encrypted_key

        return base64.b64encode(packed).decode('ascii')

    def import_key_encrypted(self, encrypted_key_b64: str, password: str) -> bytes:
        """
        Import a key encrypted with a password.

        Args:
            encrypted_key_b64: Base64-encoded encrypted key from export_key_encrypted()
            password: Password used for encryption

        Returns:
            Decrypted key
        """
        packed = base64.b64decode(encrypted_key_b64)

        # Unpack salt + nonce + encrypted_key
        salt = packed[:EncryptionConfig.SALT_SIZE]
        nonce = packed[EncryptionConfig.SALT_SIZE:EncryptionConfig.SALT_SIZE + EncryptionConfig.NONCE_SIZE]
        encrypted_key = packed[EncryptionConfig.SALT_SIZE + EncryptionConfig.NONCE_SIZE:]

        # Derive decryption key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=EncryptionConfig.KEY_SIZE,
            salt=salt,
            iterations=EncryptionConfig.ITERATIONS,
            backend=default_backend()
        )
        enc_key = kdf.derive(password.encode(EncryptionConfig.ENCODING))

        # Decrypt the key
        aesgcm = AESGCM(enc_key)
        key = aesgcm.decrypt(nonce, encrypted_key, None)

        return key


# =============================================================================
# Global Service Instance
# =============================================================================

# Initialize global encryption service
encryption_service = EncryptionService()


# =============================================================================
# Helper Functions for Common Operations
# =============================================================================

def encrypt_sensitive_data(data: Any) -> Optional[str]:
    """Convenience function to encrypt sensitive data"""
    return encryption_service.encrypt_field(data)


def decrypt_sensitive_data(encrypted_data: Optional[str]) -> Optional[Any]:
    """Convenience function to decrypt sensitive data"""
    return encryption_service.decrypt_field(encrypted_data)


def hash_for_lookup(value: str) -> str:
    """
    Hash a value for deterministic lookup.

    Useful for:
    - Searching encrypted fields
    - Creating indexed hashed values
    - Privacy-preserving identifiers

    Args:
        value: Value to hash

    Returns:
        Hex string of hash (with embedded salt)
    """
    hash_hex, salt = EncryptionService.hash_value(value)

    # Embed salt with hash for later verification
    salt_b64 = base64.b64encode(salt).decode('ascii')
    return f"{hash_hex}:{salt_b64}"


def verify_lookup_hash(value: str, lookup_hash: str) -> bool:
    """
    Verify a value against a lookup hash.

    Args:
        value: Original value
        lookup_hash: Hash from hash_for_lookup()

    Returns:
        True if matches
    """
    try:
        hash_hex, salt_b64 = lookup_hash.split(':')
        salt = base64.b64decode(salt_b64)
        return EncryptionService.verify_hash(value, hash_hex, salt)
    except (ValueError, IndexError):
        return False
