# app/domain/value_objects/password.py
"""
Password Value Object

Encapsulates password hashing and validation.
Part of the Domain Layer's value objects.
"""

import secrets
from dataclasses import dataclass

from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class Password:
    """
    Password value object with secure hashing.

    This value object handles password hashing and validation.
    Never store plaintext passwords - always use this value object.

    Attributes:
        hash_value: The bcrypt hash of the password

    Example:
        >>> # Create password from plaintext
        >>> password = Password.create("SecurePass123!")
        >>> # Verify password
        >>> password.verify("SecurePass123!")
        True
        >>> password.verify("WrongPassword")
        False
    """

    hash_value: str

    # ========================================================================
    # FACTORY METHODS
    # ========================================================================

    @classmethod
    def create(cls, plaintext: str) -> "Password":
        """
        Create password from plaintext (hashes automatically).

        Args:
            plaintext: Plaintext password

        Returns:
            Password value object with hashed password

        Raises:
            ValueError: If password doesn't meet requirements

        Example:
            >>> password = Password.create("SecurePass123!")
        """
        cls._validate_strength(plaintext)
        hash_value = pwd_context.hash(plaintext)
        return cls(hash_value=hash_value)

    @classmethod
    def from_hash(cls, hash_value: str) -> "Password":
        """
        Create password from existing hash (from database).

        Args:
            hash_value: Existing bcrypt hash

        Returns:
            Password value object

        Example:
            >>> password = Password.from_hash("$2b$12$...")
        """
        if not hash_value or not isinstance(hash_value, str):
            raise ValueError("Hash must be a non-empty string")
        return cls(hash_value=hash_value)

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    def verify(self, plaintext: str) -> bool:
        """
        Verify plaintext password against hash.

        Args:
            plaintext: Password to verify

        Returns:
            True if password matches hash

        Example:
            >>> password = Password.create("SecurePass123!")
            >>> password.verify("SecurePass123!")
            True
            >>> password.verify("WrongPassword")
            False
        """
        return pwd_context.verify(plaintext, self.hash_value)

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_strength(plaintext: str) -> None:
        """
        Validate password strength requirements.

        Args:
            plaintext: Password to validate

        Raises:
            ValueError: If password doesn't meet requirements

        Requirements:
            - Minimum 12 characters
            - Contains uppercase letter
            - Contains lowercase letter
            - Contains digit
            - Contains special character
        """
        if len(plaintext) < 12:
            raise ValueError("Password must be at least 12 characters long")

        if not any(c.isupper() for c in plaintext):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in plaintext):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in plaintext):
            raise ValueError("Password must contain at least one digit")

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in plaintext):
            raise ValueError("Password must contain at least one special character")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @staticmethod
    def generate(length: int = 16) -> str:
        """
        Generate secure random password.

        Args:
            length: Password length (default 16)

        Returns:
            Generated password string

        Example:
            >>> password = Password.generate()
            >>> len(password)
            16
        """
        alphabet = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            "!@#$%^&*()_+-=[]{}|;:,.<>?"
        )
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def __str__(self) -> str:
        """String representation (returns hash, not plaintext)"""
        return self.hash_value
