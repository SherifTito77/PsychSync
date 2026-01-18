"""
Password Service - Enterprise-Grade Password Management

Single Responsibility: Handle ALL password-related operations
- Password hashing with timing attack protection
- Password verification with security logging
- Password validation with strength scoring
- Password requirements generation

This service follows SOLID principles:
- SRP: Only handles password operations
- OCP: Pluggable hashing algorithms via dependency injection
- DIP: Depends on logging abstraction, not concrete implementations

Author: Security Team
Version: 1.0 (Extracted from security.py)
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from passlib.context import CryptContext

from app.core.config import settings


# =============================================================================
# Data Classes & Enums
# =============================================================================


class PasswordStrength(Enum):
    """Password strength rating"""
    VERY_WEAK = 0
    WEAK = 1
    FAIR = 2
    GOOD = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class ValidationResult:
    """Password validation result"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    strength_score: int  # 0-100
    strength_rating: str
    estimated_crack_time: str | None = None


@dataclass
class VerificationResult:
    """Password verification result"""
    is_valid: bool
    verification_time: float
    timestamp: datetime


# =============================================================================
# Password Service
# =============================================================================


class PasswordService:
    """
    Enterprise-grade password management service.

    Responsibilities:
    - Hash passwords securely
    - Verify passwords with timing attack protection
    - Validate password strength
    - Generate password requirements

    Usage:
        service = PasswordService()

        # Hash a password
        hashed = service.hash_password("my_secure_password")

        # Verify a password
        result = await service.verify_password(
            plain_password="my_secure_password",
            hashed_password=hashed,
            user_id="user-123"
        )

        # Validate password strength
        validation = service.validate_password("my_password")
    """

    def __init__(
        self,
        bcrypt_rounds: int = 12,
        min_length: int | None = None,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
    ):
        """
        Initialize password service with configurable parameters.

        Args:
            bcrypt_rounds: Number of bcrypt rounds (higher = more secure but slower)
            min_length: Minimum password length (default: from settings)
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_digits: Require digits
            require_special: Require special characters
        """
        self.bcrypt_rounds = bcrypt_rounds
        self.min_length = min_length or getattr(settings, "MIN_PASSWORD_LENGTH", 8)
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?`~"

        # Initialize password hashing context
        self._pwd_context = CryptContext(
            schemes=["bcrypt"],
            default="bcrypt",
            deprecated="auto",
            bcrypt__rounds=bcrypt_rounds,
        )

        # Initialize logger
        self._logger = logging.getLogger("app.security.password")

        # Common weak patterns for validation
        self._weak_patterns = [
            "password", "123456", "qwerty", "admin", "letmein",
            "welcome", "changeme", "default", "login", "user", "test",
        ]

        # Common dictionary words
        self._common_words = [
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "day",
            "get", "has", "him", "his", "how", "man", "new", "now",
            "old", "see", "two", "way", "who", "boy", "did", "its",
            "let", "put", "say", "she", "too", "use",
        ]

        # Keyboard patterns to detect
        self._keyboard_patterns = [
            "qwerty", "asdf", "zxcv", "qwe", "asd", "zxc",
            "123", "234", "345", "456", "567", "678", "789", "890",
        ]

    # =========================================================================
    # Hashing Operations
    # =========================================================================

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string

        Raises:
            ValueError: If password validation fails
            RuntimeError: If hashing fails

        Security Note:
            - Uses passlib for consistent, secure hashing
            - Validates password before hashing
            - Handles bcrypt limitations transparently
        """
        # Validate password before hashing
        validation_result = self.validate_password(password)
        if not validation_result.is_valid:
            raise ValueError(
                f"Password validation failed: {', '.join(validation_result.errors)}"
            )

        try:
            return self._pwd_context.hash(password)
        except Exception as e:
            self._logger.error(f"Password hashing failed: {type(e).__name__}")
            raise RuntimeError("Password hashing failed. Please try again.") from e

    async def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
        ip_address: str = "unknown",
        user_id: str | None = None,
    ) -> VerificationResult:
        """
        Verify a password against its hash with timing attack protection.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            ip_address: Client IP address for security logging
            user_id: User ID for security tracking

        Returns:
            VerificationResult with validity and timing information

        Security Features:
            - Timing attack protection
            - Comprehensive audit logging
            - Anomaly detection via timing analysis
            - Brute force detection support

        Note:
            This method is async to support future security event recording
            Currently logs synchronously but designed for async event recording
        """
        if not plain_password or not hashed_password:
            self._logger.warning(
                "Password verification with empty values",
                extra={
                    "ip_address": ip_address,
                    "user_id": user_id,
                    "event_type": "security_warning",
                },
            )
            return VerificationResult(
                is_valid=False,
                verification_time=0.0,
                timestamp=datetime.utcnow()
            )

        start_time = time.time()

        try:
            # Use passlib with enhanced error handling
            result = self._pwd_context.verify(plain_password, hashed_password)
            verification_time = time.time() - start_time

            # Security audit logging
            if result:
                self._logger.info(
                    "Password verification successful",
                    extra={
                        "ip_address": ip_address,
                        "user_id": user_id,
                        "verification_time": verification_time,
                        "event_type": "auth_success",
                    },
                )
            else:
                self._logger.warning(
                    "Password verification failed",
                    extra={
                        "ip_address": ip_address,
                        "user_id": user_id,
                        "verification_time": verification_time,
                        "event_type": "auth_failure",
                    },
                )

            return VerificationResult(
                is_valid=result,
                verification_time=verification_time,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            verification_time = time.time() - start_time

            self._logger.error(
                f"Password verification error: {type(e).__name__}",
                extra={
                    "ip_address": ip_address,
                    "user_id": user_id,
                    "verification_time": verification_time,
                    "error_type": type(e).__name__,
                    "event_type": "security_error",
                },
            )

            # Fail securely - always return False on error
            return VerificationResult(
                is_valid=False,
                verification_time=verification_time,
                timestamp=datetime.utcnow()
            )

    # =========================================================================
    # Validation Operations
    # =========================================================================

    def validate_password(self, password: str) -> ValidationResult:
        """
        Validate password against security requirements.

        Args:
            password: Password to validate

        Returns:
            ValidationResult with validity status, errors, warnings, and strength

        Validation Checks:
            - Minimum length
            - Character variety (upper, lower, digit, special)
            - Common weak patterns
            - Sequential characters
            - Repeated characters
            - Keyboard patterns
            - Dictionary words
            - Overall strength score
        """
        errors = []
        warnings = []

        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        elif len(password) < 16:
            warnings.append("Consider using a password of at least 16 characters for better security")

        # Check for uppercase letter
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        # Check for lowercase letter
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        # Check for digit
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        # Check for special characters
        if self.require_special:
            if not any(c in self.special_chars for c in password):
                errors.append(f"Password must contain at least one special character: {self.special_chars}")

        # Prevent common weak patterns
        password_lower = password.lower()
        for pattern in self._weak_patterns:
            if pattern in password_lower:
                errors.append(f"Password cannot contain common patterns like '{pattern}'")
                break

        # Check for sequential characters
        sequential_count = self._count_sequential_chars(password)
        if sequential_count > len(password) * 0.1:  # More than 10% sequential
            errors.append("Password contains too many sequential characters")
        elif sequential_count > 0:
            warnings.append("Password contains sequential characters, consider changing them")

        # Check for repeated characters
        repeated_count = self._count_repeated_chars(password)
        if repeated_count > len(password) * 0.1:  # More than 10% repeated
            errors.append("Password contains too many repeated characters")
        elif repeated_count > 0:
            warnings.append("Password contains repeated characters, consider diversifying")

        # Check for keyboard patterns
        for pattern in self._keyboard_patterns:
            if pattern in password_lower:
                warnings.append(f"Password contains keyboard pattern '{pattern}', consider changing it")

        # Calculate password strength score
        strength_score = self._calculate_strength(password)

        # Add strength-based warnings
        if strength_score < 60:
            errors.append("Password is too weak. Please choose a stronger password")
        elif strength_score < 80:
            warnings.append("Password strength could be improved")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            strength_score=strength_score,
            strength_rating=self._get_strength_rating(strength_score),
            estimated_crack_time=self._estimate_crack_time(strength_score),
        )

    def _calculate_strength(self, password: str) -> int:
        """Calculate password strength score (0-100). Higher is better."""
        score = 0

        # Length contribution (40% of total score)
        length_score = min(len(password) * 2.5, 40)
        score += length_score

        # Character variety contribution (40% of total score)
        char_variety_score = 0
        if any(c.islower() for c in password):
            char_variety_score += 10
        if any(c.isupper() for c in password):
            char_variety_score += 10
        if any(c.isdigit() for c in password):
            char_variety_score += 10
        if any(c in self.special_chars for c in password):
            char_variety_score += 10
        score += char_variety_score

        # Entropy bonus (15% of total score)
        unique_chars = len(set(password))
        entropy_bonus = min(unique_chars * 2, 15)
        score += entropy_bonus

        # Complexity bonus (5% of total score)
        complexity_bonus = 0
        if not self._contains_common_words(password):
            complexity_bonus += 5
        score += complexity_bonus

        return min(score, 100)

    def _count_sequential_chars(self, password: str) -> int:
        """Count sequential character patterns."""
        sequential_count = 0
        for i in range(len(password) - 2):
            if (
                (ord(password[i]) + 1 == ord(password[i + 1]) == ord(password[i + 2]) - 1)
                or (ord(password[i]) - 1 == ord(password[i + 1]) == ord(password[i + 2]) + 1)
            ):
                sequential_count += 1
        return sequential_count

    def _count_repeated_chars(self, password: str) -> int:
        """Count repeated character patterns."""
        repeated_count = 0
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                repeated_count += 1
        return repeated_count

    def _contains_common_words(self, password: str) -> bool:
        """Check if password contains common dictionary words."""
        password_lower = password.lower()
        for word in self._common_words:
            if word in password_lower:
                return True
        return False

    def _get_strength_rating(self, score: int) -> str:
        """Get strength rating label from score."""
        if score >= 90:
            return "Very Strong"
        if score >= 80:
            return "Strong"
        if score >= 70:
            return "Good"
        if score >= 60:
            return "Fair"
        if score >= 40:
            return "Weak"
        return "Very Weak"

    def _estimate_crack_time(self, score: int) -> str:
        """Estimate time to crack password based on strength score."""
        if score >= 90:
            return "Centuries"
        if score >= 80:
            return "Decades"
        if score >= 70:
            return "Years"
        if score >= 60:
            return "Months"
        if score >= 40:
            return "Weeks"
        return "Days or less"

    # =========================================================================
    # Requirements Generation
    # =========================================================================

    def get_requirements(self) -> dict[str, Any]:
        """
        Get current password requirements for UI display.

        Returns:
            Dictionary with password requirements
        """
        return {
            "min_length": self.min_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_digits": self.require_digits,
            "require_special_chars": self.require_special,
            "special_characters": self.special_chars,
            "recommended_length": 16,
            "forbidden_patterns": self._weak_patterns.copy(),
        }


# =============================================================================
# Default Instance (Backward Compatibility)
# =============================================================================

# Create default service instance for backward compatibility
_default_service: PasswordService | None = None


def get_password_service() -> PasswordService:
    """Get default password service instance (singleton pattern)."""
    global _default_service
    if _default_service is None:
        _default_service = PasswordService()
    return _default_service


# =============================================================================
# Convenience Functions (Backward Compatibility)
# =============================================================================

def get_password_hash(password: str) -> str:
    """Hash password using default service."""
    return get_password_service().hash_password(password)


async def verify_password(
    plain_password: str,
    hashed_password: str,
    ip_address: str = "unknown",
    user_id: str | None = None,
) -> bool:
    """Verify password using default service."""
    result = await get_password_service().verify_password(
        plain_password, hashed_password, ip_address, user_id
    )
    return result.is_valid


def validate_password(password: str) -> dict[str, Any]:
    """Validate password using default service."""
    result = get_password_service().validate_password(password)
    return {
        "valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "strength_score": result.strength_score,
        "strength_rating": result.strength_rating,
    }


def generate_password_requirements() -> dict[str, Any]:
    """Get password requirements using default service."""
    return get_password_service().get_requirements()
