# app/core/password_validator.py
"""
Enterprise-grade password validation module.

Features:
- Entropy calculation and scoring
- Common password detection
- Sequential pattern detection
- Repeated character detection
- Comprehensive strength assessment
"""

import math
import re
import string
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PasswordStrengthResult:
    """Result of password strength assessment."""
    score: int  # 0-100
    strength: str  # weak, fair, good, strong, excellent
    feedback: List[str]
    entropy_bits: float
    is_valid: bool


class EnterprisePasswordValidator:
    """
    Enterprise-grade password validator.

    Requirements:
    - Minimum 12 characters
    - Contains uppercase, lowercase, digit, special character
    - Entropy score >= 60 bits
    - Not in common password list
    - No sequential or repeated patterns
    """

    # Top 500 common passwords (truncated for brevity - expand in production)
    COMMON_PASSWORDS = {
        'password', 'password123', 'password1', '123456', '12345678',
        '123456789', 'qwerty', 'qwerty123', 'abc123', 'letmein',
        'monkey', 'dragon', 'master', 'hello', 'login', 'welcome',
        'admin', 'administrator', 'root', 'pass', 'test', 'guest',
        'user', 'player', 'football', 'baseball', 'superman',
        'batman', 'trustno1', 'iloveyou', 'starwars', 'michael',
        'jennifer', 'jordan', 'charlie', 'andrew', 'matthew',
        'password1234', 'password!', 'Password1', 'Welcome1',
        'Admin123', 'Root123', 'Test123', 'User123', 'Login123',
    }

    # Sequential patterns to detect
    SEQUENTIAL_PATTERNS = [
        'abcdefghijklmnopqrstuvwxyz',
        'qwertyuiop',
        'asdfghjkl',
        'zxcvbnm',
        '0123456789',
    ]

    def __init__(self, min_length: int = 12, min_entropy: float = 60.0):
        """
        Initialize password validator.

        Args:
            min_length: Minimum password length (default: 12)
            min_entropy: Minimum entropy in bits (default: 60)
        """
        self.min_length = min_length
        self.min_entropy = min_entropy

    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password against enterprise requirements.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Length requirement
        if len(password) < self.min_length:
            errors.append(
                f'Password must be at least {self.min_length} characters long. '
                f'Current length: {len(password)}'
            )

        # Character variety
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)

        if not has_upper:
            errors.append('Password must contain at least one uppercase letter')
        if not has_lower:
            errors.append('Password must contain at least one lowercase letter')
        if not has_digit:
            errors.append('Password must contain at least one digit')
        if not has_special:
            errors.append('Password must contain at least one special character')

        # Entropy check
        entropy = self._calculate_entropy(password)
        if entropy < self.min_entropy:
            errors.append(
                f'Password is too predictable (entropy: {entropy:.1f} bits, '
                f'required: {self.min_entropy} bits). '
                f'Use a more complex combination of characters.'
            )

        # Common password check
        if self._is_common_password(password):
            errors.append(
                'This password is too common. '
                'Please choose a unique password that is not easily guessable.'
            )

        # Pattern detection
        if self._has_sequential_pattern(password):
            errors.append(
                'Password contains sequential patterns (e.g., "abc", "123", "qwerty"). '
                'Avoid using consecutive characters.'
            )

        if self._has_repeated_pattern(password):
            errors.append(
                'Password contains repeated characters (e.g., "aaa", "111"). '
                'Avoid using the same character multiple times in a row.'
            )

        is_valid = len(errors) == 0
        return is_valid, errors

    def assess_strength(self, password: str) -> PasswordStrengthResult:
        """
        Assess password strength with detailed feedback.

        Args:
            password: Password to assess

        Returns:
            PasswordStrengthResult with score, strength level, and feedback
        """
        score = 0
        feedback = []

        # Length (40 points max)
        length_score = min(len(password) * 2, 40)
        score += length_score
        if len(password) < 12:
            feedback.append(f"Use at least 12 characters (currently: {len(password)})")

        # Character variety (30 points max)
        variety_score = 0
        if any(c.islower() for c in password):
            variety_score += 7.5
        else:
            feedback.append("Add lowercase letters")

        if any(c.isupper() for c in password):
            variety_score += 7.5
        else:
            feedback.append("Add uppercase letters")

        if any(c.isdigit() for c in password):
            variety_score += 7.5
        else:
            feedback.append("Add numbers")

        if any(c in string.punctuation for c in password):
            variety_score += 7.5
        else:
            feedback.append("Add special characters (!@#$%...)")

        score += variety_score

        # Entropy (15 points max)
        entropy = self._calculate_entropy(password)
        entropy_score = min(entropy / 4, 15)  # Max 15 points at 60 bits
        score += entropy_score
        if entropy < 60:
            feedback.append("Increase character variety for better randomness")

        # Complexity (15 points max)
        complexity_penalty = 0
        if self._is_common_password(password):
            complexity_penalty += 15
            feedback.append("Avoid common passwords")
        if self._has_sequential_pattern(password):
            complexity_penalty += 10
            feedback.append("Avoid sequential patterns (abc, 123, qwerty)")
        if self._has_repeated_pattern(password):
            complexity_penalty += 10
            feedback.append("Avoid repeated characters (aaa, 111)")

        score -= max(complexity_penalty, 0)

        # Determine strength level
        score = max(0, min(score, 100))  # Clamp to 0-100

        if score >= 90:
            strength = "excellent"
        elif score >= 75:
            strength = "strong"
        elif score >= 60:
            strength = "good"
        elif score >= 40:
            strength = "fair"
        else:
            strength = "weak"

        # Clear feedback if excellent
        if score >= 90 and not feedback:
            feedback.append("Excellent password!")

        # Validate
        is_valid, validation_errors = self.validate_password(password)

        return PasswordStrengthResult(
            score=int(score),
            strength=strength,
            feedback=feedback if score < 90 else ["Excellent password!"],
            entropy_bits=entropy,
            is_valid=is_valid
        )

    def _calculate_entropy(self, password: str) -> float:
        """
        Calculate password entropy in bits.

        Formula: E = L * log2(N)
        Where L = length, N = charset size
        """
        charset_size = 0

        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in string.punctuation for c in password):
            charset_size += 32

        if charset_size == 0:
            return 0.0

        entropy = len(password) * math.log2(charset_size)
        return entropy

    def _is_common_password(self, password: str) -> bool:
        """Check if password is in common password list."""
        return (
            password.lower() in self.COMMON_PASSWORDS or
            any(pattern in password.lower() for pattern in self.COMMON_PASSWORDS)
        )

    def _has_sequential_pattern(self, password: str) -> bool:
        """Detect sequential patterns (abcd, 1234, qwerty)."""
        password_lower = password.lower()

        # Check sequences
        for sequence in self.SEQUENTIAL_PATTERNS:
            for i in range(len(sequence) - 3):
                seq = sequence[i:i+4]
                if seq in password_lower or seq[::-1] in password_lower:
                    return True

        return False

    def _has_repeated_pattern(self, password: str) -> bool:
        """Detect repeated characters (aaaa, 1111)."""
        for char in set(password):
            if char * 4 in password.lower():
                return True
        return False


# Singleton instance for easy import
password_validator = EnterprisePasswordValidator()


def validate_password_strength(password: str) -> str:
    """
    Validate password strength (for backward compatibility).

    This function is maintained for backward compatibility with existing code.
    New code should use EnterprisePasswordValidator directly.

    Args:
        password: Password to validate

    Returns:
        Password if valid

    Raises:
        ValueError: If password doesn't meet requirements
    """
    is_valid, errors = password_validator.validate_password(password)

    if not is_valid:
        error_message = '; '.join(errors)
        raise ValueError(error_message)

    return password
