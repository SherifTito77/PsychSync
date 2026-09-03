"""
Input Sanitizer Service - Security Input Validation

Single Responsibility: Handle ALL input sanitization and validation
- XSS prevention via HTML escaping
- SQL injection prevention
- Email validation
- CSRF token generation and validation
- General input sanitization

This service follows SOLID principles:
- SRP: Only handles input sanitization
- OCP: Pluggable sanitization strategies
- DIP: No dependencies on external systems

Author: Security Team
Version: 1.0 (Extracted from security.py)
"""

import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class SanitizationResult:
    """Result of input sanitization"""

    original: str
    sanitized: str
    was_modified: bool
    patterns_removed: List[str]
    is_safe: bool


@dataclass
class ValidationResult:
    """Result of input validation"""

    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class CSRFToken:
    """CSRF token with metadata"""

    token: str
    created_at: datetime
    max_age: int


# =============================================================================
# Input Sanitizer Service
# =============================================================================


class InputSanitizerService:
    """
    Enterprise-grade input sanitization service.

    Responsibilities:
    - Sanitize user input to prevent injection attacks
    - Escape HTML to prevent XSS
    - Validate email format
    - Generate and validate CSRF tokens

    Usage:
        service = InputSanitizerService()

        # Sanitize input
        result = service.sanitize_input(user_input)

        # Escape HTML
        safe_html = service.escape_html(user_input)

        # Validate email
        is_valid = service.validate_email("user@example.com")

        # Generate CSRF token
        csrf_token = service.generate_csrf_token()
    """

    def __init__(
        self,
        enable_sql_injection_prevention: bool = True,
        enable_xss_prevention: bool = True,
        enable_html_escaping: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize input sanitizer service.

        Args:
            enable_sql_injection_prevention: Enable SQL injection prevention
            enable_xss_prevention: Enable XSS prevention
            enable_html_escaping: Enable HTML entity escaping
            strict_mode: If True, reject any suspicious input (don't sanitize)
        """
        self.enable_sql_injection_prevention = enable_sql_injection_prevention
        self.enable_xss_prevention = enable_xss_prevention
        self.enable_html_escaping = enable_html_escaping
        self.strict_mode = strict_mode

        self._logger = logging.getLogger("app.security.sanitization")

        # SQL injection patterns to detect/remove
        self._sql_patterns = [
            r"'(?!\s*[$a-zA-Z_])",  # Single quotes (except in valid contexts)
            r";\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)",  # SQL commands after semicolon
            r"--.*$",  # SQL comments
            r"/\*.*?\*/",  # SQL block comments
            r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b",  # SQL keywords
        ]

        # XSS patterns to detect
        self._xss_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript protocol
            r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
            r"<iframe[^>]*>",  # Iframe tags
            r"<embed[^>]*>",  # Embed tags
            r"<object[^>]*>",  # Object tags
        ]

        # HTML escape map
        self._html_escape_map = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }

    # =========================================================================
    # Input Sanitization
    # =========================================================================

    def sanitize_input(
        self, input_str: str, aggressive: bool = False
    ) -> SanitizationResult:
        """
        Sanitize user input to prevent injection attacks.

        Args:
            input_str: Raw user input
            aggressive: If True, use more aggressive sanitization

        Returns:
            SanitizationResult with sanitized input and details

        Security Features:
            - Removes SQL injection patterns
            - Removes XSS patterns
            - Normalizes whitespace
            - Logs sanitization events
        """
        if not input_str:
            return SanitizationResult(
                original="",
                sanitized="",
                was_modified=False,
                patterns_removed=[],
                is_safe=True,
            )

        original = input_str
        sanitized = input_str
        patterns_removed = []

        # SQL injection prevention
        if self.enable_sql_injection_prevention:
            for pattern in self._sql_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    if aggressive or self.strict_mode:
                        # In strict mode, reject suspicious input
                        self._logger.warning(
                            f"SQL injection pattern detected in input: {input_str[:50]}...",
                            extra={"event_type": "sql_injection_attempt"},
                        )
                        return SanitizationResult(
                            original=original,
                            sanitized="",
                            was_modified=True,
                            patterns_removed=["SQL_INJECTION"],
                            is_safe=False,
                        )
                    else:
                        # Sanitize mode: remove patterns
                        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
                        patterns_removed.append("SQL_PATTERN")

        # XSS prevention
        if self.enable_xss_prevention:
            for pattern in self._xss_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    if self.strict_mode:
                        self._logger.warning(
                            f"XSS pattern detected in input: {input_str[:50]}...",
                            extra={"event_type": "xss_attempt"},
                        )
                        return SanitizationResult(
                            original=original,
                            sanitized="",
                            was_modified=True,
                            patterns_removed=["XSS_PATTERN"],
                            is_safe=False,
                        )
                    else:
                        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
                        patterns_removed.append("XSS_PATTERN")

        # Remove excessive whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        was_modified = sanitized != original
        is_safe = not patterns_removed or not was_modified

        if was_modified:
            self._logger.info(
                f"Input sanitized: {len(patterns_removed)} patterns removed",
                extra={
                    "patterns_removed": patterns_removed,
                    "original_length": len(original),
                    "sanitized_length": len(sanitized),
                    "event_type": "input_sanitized",
                },
            )

        return SanitizationResult(
            original=original,
            sanitized=sanitized,
            was_modified=was_modified,
            patterns_removed=patterns_removed,
            is_safe=is_safe,
        )

    def escape_html(self, input_str: str) -> str:
        """
        Escape HTML entities to prevent XSS attacks.

        Args:
            input_str: Raw user input

        Returns:
            HTML-escaped string

        Examples:
            >>> service.escape_html("<script>alert('XSS')</script>")
            "&lt;script&gt;alert('XSS')&lt;/script&gt;"
        """
        if not input_str:
            return ""

        if not self.enable_html_escaping:
            return input_str

        escaped = input_str
        for char, entity in self._html_escape_map.items():
            escaped = escaped.replace(char, entity)

        return escaped

    def sanitize_json(self, json_str: str) -> str:
        """
        Sanitize JSON input to prevent injection attacks.

        Args:
            json_str: JSON string to sanitize

        Returns:
            Sanitized JSON string
        """
        if not json_str:
            return ""

        # Remove control characters except whitespace
        sanitized = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", json_str)

        # Remove SQL injection patterns from JSON values
        result = self.sanitize_input(sanitized, aggressive=False)

        return result.sanitized

    # =========================================================================
    # Validation
    # =========================================================================

    def validate_email(self, email: str) -> ValidationResult:
        """
        Validate email format using comprehensive regex.

        Args:
            email: Email address to validate

        Returns:
            ValidationResult with validity status

        Validation Checks:
            - Format validation (regex)
            - Length constraints
            - Allowed characters
        """
        errors = []
        warnings = []

        if not email or not isinstance(email, str):
            return ValidationResult(
                is_valid=False,
                errors=["Email is required and must be a string"],
                warnings=[],
            )

        email = email.strip()

        # Check length
        if len(email) > 254:  # RFC 5321
            errors.append("Email is too long (max 254 characters)")

        # Check for multiple @ symbols
        if email.count("@") != 1:
            errors.append("Email must contain exactly one @ symbol")

        # Comprehensive email validation regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            errors.append("Email format is invalid")

        # Check for suspicious patterns
        suspicious_patterns = [
            "..",  # Double dots
            ".@",  # Dot before @
            "@.",  # At sign followed immediately by dot
            "+@",  # Plus sign immediately before @ (common in spam)
        ]

        for pattern in suspicious_patterns:
            if pattern in email:
                warnings.append(f"Email contains suspicious pattern: {pattern}")

        # Check domain
        if "@" in email:
            local_part, domain = email.rsplit("@", 1)
            if "." not in domain:
                errors.append("Email domain is invalid")

            if len(local_part) > 64:  # RFC 5321
                warnings.append("Email local part is unusually long")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate URL format.

        Args:
            url: URL to validate

        Returns:
            ValidationResult with validity status
        """
        errors = []
        warnings = []

        if not url or not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                errors=["URL is required and must be a string"],
                warnings=[],
            )

        url = url.strip()

        # Basic URL pattern
        url_pattern = r"^https?://[a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})?(/.*)?$"

        if not re.match(url_pattern, url):
            errors.append("URL format is invalid")

        # Check for suspicious patterns
        if "javascript:" in url.lower():
            errors.append("URL contains javascript: protocol (XSS risk)")

        if "../" in url:
            warnings.append("URL contains path traversal sequence")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_username(self, username: str) -> ValidationResult:
        """
        Validate username format.

        Args:
            username: Username to validate

        Returns:
            ValidationResult with validity status
        """
        errors = []
        warnings = []

        if not username or not isinstance(username, str):
            return ValidationResult(
                is_valid=False,
                errors=["Username is required and must be a string"],
                warnings=[],
            )

        username = username.strip()

        # Length constraints
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif len(username) > 50:
            errors.append("Username must be no more than 50 characters long")

        # Allowed characters (alphanumeric, underscore, hyphen)
        username_pattern = r"^[a-zA-Z0-9_-]+$"

        if not re.match(username_pattern, username):
            errors.append(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )

        # Cannot start/end with special characters
        if username.startswith(("_", "-")):
            errors.append("Username cannot start with underscore or hyphen")

        if username.endswith(("_", "-")):
            errors.append("Username cannot end with underscore or hyphen")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # =========================================================================
    # CSRF Protection
    # =========================================================================

    def generate_csrf_token(self, length: int = 32) -> CSRFToken:
        """
        Generate CSRF token for state-changing operations.

        Args:
            length: Token length in bytes (default: 32)

        Returns:
            CSRFToken with token and metadata

        Note:
            CSRF tokens should be:
            - Generated server-side
            - Stored in user session
            - Included in forms
            - Verified on form submission
        """
        token = secrets.token_urlsafe(length)

        return CSRFToken(
            token=token,
            created_at=datetime.utcnow(),
            max_age=3600,  # 1 hour default
        )

    def validate_csrf_token(
        self,
        token: str,
        expected_token: str,
        max_age: int = 3600,
        created_at: datetime | None = None,
    ) -> bool:
        """
        Validate CSRF token.

        Args:
            token: Token from form submission
            expected_token: Token stored in session
            max_age: Maximum age of token in seconds (default: 3600)
            created_at: When token was created (optional)

        Returns:
            True if token is valid, False otherwise

        Validation:
            - Tokens must match exactly
            - Token must not be expired
        """
        if not token or not expected_token:
            return False

        # Use timing-safe comparison to prevent timing attacks
        import hmac

        if not hmac.compare_digest(token, expected_token):
            self._logger.warning(
                "CSRF token mismatch",
                extra={"event_type": "csrf_validation_failed"},
            )
            return False

        # Check token age if created_at provided
        if created_at:
            age = (datetime.utcnow() - created_at).total_seconds()
            if age > max_age:
                self._logger.warning(
                    f"CSRF token expired (age: {age}s, max: {max_age}s)",
                    extra={"event_type": "csrf_token_expired"},
                )
                return False

        return True


# =============================================================================
# Default Instance (Backward Compatibility)
# =============================================================================

_default_service: InputSanitizerService | None = None


def get_input_sanitizer_service() -> InputSanitizerService:
    """Get default input sanitizer service instance (singleton pattern)."""
    global _default_service
    if _default_service is None:
        _default_service = InputSanitizerService()
    return _default_service


# =============================================================================
# Convenience Functions (Backward Compatibility)
# =============================================================================


def sanitize_input(input_str: str) -> str:
    """Sanitize input using default service."""
    result = get_input_sanitizer_service().sanitize_input(input_str)
    return result.sanitized


def escape_html(input_str: str) -> str:
    """Escape HTML using default service."""
    return get_input_sanitizer_service().escape_html(input_str)


def validate_email(email: str) -> bool:
    """Validate email using default service."""
    result = get_input_sanitizer_service().validate_email(email)
    return result.is_valid


def generate_csrf_token(length: int = 32) -> str:
    """Generate CSRF token using default service."""
    csrf_token = get_input_sanitizer_service().generate_csrf_token(length)
    return csrf_token.token


def validate_csrf_token(token: str, expected_token: str, max_age: int = 3600) -> bool:
    """Validate CSRF token using default service."""
    return get_input_sanitizer_service().validate_csrf_token(
        token, expected_token, max_age
    )
