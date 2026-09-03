"""
Encrypted Database Field Types

SQLAlchemy custom types for automatic field-level encryption.
These types encrypt data on write and decrypt on read transparently.

Usage:
    class User(Base):
        __tablename__ = 'users'
        email = Column(EncryptedString(255))
        ssn = Column(EncryptedString)
        metadata = Column(EncryptedJSON)
"""

import json
from typing import Any, Optional

from sqlalchemy import String, TypeDecorator
from sqlalchemy.types import TEXT, LargeBinary

from app.services.encryption_service import encryption_service


class EncryptedString(TypeDecorator):
    """
    String field that automatically encrypts/decrypts values.

    Usage:
        email = Column(EncryptedString(255))
        secret = Column(EncryptedString)
    """

    impl = TEXT
    cache_ok = True

    def __init__(self, length: Optional[int] = None, **kwargs):
        """
        Initialize encrypted string type.

        Args:
            length: Optional maximum length (for documentation)
        """
        super().__init__(**kwargs)
        self.length = length

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt before writing to database"""
        if value is None:
            return None

        # Return encrypted JSON string
        return encryption_service.encrypt_field(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt after reading from database"""
        if value is None:
            return None

        try:
            decrypted = encryption_service.decrypt_field(value)

            # Ensure we return a string
            if isinstance(decrypted, str):
                return decrypted
            elif decrypted is None:
                return None
            else:
                return str(decrypted)

        except Exception as e:
            # Log error but don't crash
            from app.core.logger import logger

            logger.error(f"Failed to decrypt encrypted string: {e}")
            return None


class EncryptedJSON(TypeDecorator):
    """
    JSON field that automatically encrypts/decrypts values.

    Usage:
        metadata = Column(EncryptedJSON)
        preferences = Column(EncryptedJSON)
    """

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        """Encrypt before writing to database"""
        if value is None:
            return None

        # Return encrypted JSON string
        return encryption_service.encrypt_field(value)

    def process_result_value(self, value: Optional[str], dialect) -> Any:
        """Decrypt after reading from database"""
        if value is None:
            return None

        try:
            decrypted = encryption_service.decrypt_field(value)

            # Should already be a dict/list from JSON parsing
            return decrypted

        except Exception as e:
            # Log error but don't crash
            from app.core.logger import logger

            logger.error(f"Failed to decrypt encrypted JSON: {e}")
            return None


class EncryptedText(TypeDecorator):
    """
    Large text field that automatically encrypts/decrypts values.

    Suitable for long-form content like notes, messages, etc.

    Usage:
        notes = Column(EncryptedText)
        message_body = Column(EncryptedText)
    """

    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt before writing to database"""
        if value is None:
            return None

        return encryption_service.encrypt_field(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt after reading from database"""
        if value is None:
            return None

        try:
            decrypted = encryption_service.decrypt_field(value)

            if isinstance(decrypted, str):
                return decrypted
            elif decrypted is None:
                return None
            else:
                return str(decrypted)

        except Exception as e:
            from app.core.logger import logger

            logger.error(f"Failed to decrypt encrypted text: {e}")
            return None


class HashedString(TypeDecorator):
    """
    String field that stores a one-way hash (for verification only).

    Suitable for:
    - Email lookup without storing plaintext
    - Identifiable but not readable data
    - Deterministic comparisons

    WARNING: Cannot be decrypted! Only use for verification/lookup.

    Usage:
        email_hash = Column(HashedString)
        external_id = Column(HashedString)
    """

    impl = String(128)
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Hash before writing to database"""
        if value is None:
            return None

        # Use lookup hash format (hash:salt)
        return hash_for_lookup(value)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Return hash as-is (cannot be reversed)"""
        return value


# =============================================================================
# Convenience Functions
# =============================================================================


def encrypt_on_write(column_type: TypeDecorator) -> TypeDecorator:
    """
    Decorator to add encryption to any column type.

    Usage:
        class MyModel(Base):
            custom_field = Column(encrypt_on_write(String(255)))
    """

    class EncryptedColumn(TypeDecorator):
        impl = column_type
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            return encryption_service.encrypt_field(value)

        def process_result_value(self, value, dialect):
            if value is None:
                return None
            try:
                return encryption_service.decrypt_field(value)
            except Exception:
                return None

    return EncryptedColumn


# Import helper functions at module level for convenience
from app.services.encryption_service import hash_for_lookup, verify_lookup_hash
