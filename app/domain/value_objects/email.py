# app/domain/value_objects/email.py
"""
Email Value Object

Encapsulates email validation and business rules.
Part of the Domain Layer's value objects.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """
    Email value object with validation.

    This is a value object - it's immutable and defined by its value.
    Two Email objects with the same email address are considered equal.

    Attributes:
        value: The email address string

    Raises:
        ValueError: If email is invalid

    Example:
        >>> email = Email("user@example.com")
        >>> print(email.domain)
        'example.com'
        >>> email2 = Email("USER@EXAMPLE.COM")
        >>> email.normalized == email2.normalized
        True
    """

    value: str

    # Email regex pattern (RFC 5322 compliant simplified)
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __post_init__(self):
        """Validate email on initialization"""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Email must be a non-empty string")

        if not self.EMAIL_PATTERN.match(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    # ========================================================================
    # BUSINESS LOGIC
    # ========================================================================

    @property
    def normalized(self) -> str:
        """
        Get normalized (lowercase) email.

        Returns:
            Lowercase email address

        Example:
            >>> email = Email("User@Example.com")
            >>> email.normalized
            'user@example.com'
        """
        return self.value.lower()

    @property
    def domain(self) -> str:
        """
        Extract domain from email.

        Returns:
            Domain part of email

        Example:
            >>> email = Email("user@example.com")
            >>> email.domain
            'example.com'
        """
        return self.value.split("@")[1].lower()

    @property
    def local_part(self) -> str:
        """
        Extract local part from email (before @).

        Returns:
            Local part of email

        Example:
            >>> email = Email("user@example.com")
            >>> email.local_part
            'user'
        """
        return self.value.split("@")[0]

    def is_from_domain(self, domain: str) -> bool:
        """
        Check if email is from specific domain.

        Args:
            domain: Domain to check (case-insensitive)

        Returns:
            True if email matches domain

        Example:
            >>> email = Email("user@example.com")
            >>> email.is_from_domain("example.com")
            True
            >>> email.is_from_domain("other.com")
            False
        """
        return self.domain == domain.lower()

    def is_corporate(self) -> bool:
        """
        Check if email appears to be corporate (not free provider).

        Returns:
            True if not from common free email providers

        Example:
            >>> email = Email("user@company.com")
            >>> email.is_corporate()
            True
            >>> email2 = Email("user@gmail.com")
            >>> email2.is_corporate()
            False
        """
        free_providers = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "protonmail.com",
            "mail.com",
        }
        return self.domain not in free_providers

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def __str__(self) -> str:
        """String representation (normalized)"""
        return self.normalized

    def __eq__(self, other) -> bool:
        """Email comparison (case-insensitive)"""
        if not isinstance(other, Email):
            return False
        return self.normalized == other.normalized

    def __hash__(self) -> int:
        """Hash for use in sets/dicts"""
        return hash(self.normalized)
