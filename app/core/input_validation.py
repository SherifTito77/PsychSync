# app/core/input_validation.py
"""
Comprehensive input validation utilities for PsychSync API
"""

import logging
import re
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class InputValidator:
    """Comprehensive input validation utilities"""

    # Pre-compiled regex patterns for performance
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE
    )
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    SAFE_STRING_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_.,!?@#$%^&*()+=\[\]{}|;:<>]+$")

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"document\.",
        r"window\.",
        r"alert\s*\(",
        r"prompt\s*\(",
        r"confirm\s*\(",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
        r"Function\s*\(",
        r"RegExp\s*\(",
        r"\\x[0-9a-f]{2}",
        r"\\u[0-9a-f]{4}",
    ]

    @classmethod
    def validate_uuid(cls, value: str | uuid.UUID, field_name: str = "ID") -> str:
        """Validate UUID format"""
        if isinstance(value, uuid.UUID):
            return str(value)

        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string or UUID")

        if not cls.UUID_PATTERN.match(value):
            raise ValueError(f"Invalid {field_name} format. Must be a valid UUID")

        return value

    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email format"""
        if not isinstance(email, str):
            raise ValueError("Email must be a string")

        email = email.strip().lower()
        if not cls.EMAIL_PATTERN.match(email):
            raise ValueError("Invalid email format")

        # Additional length checks
        if len(email) > 254:
            raise ValueError("Email address too long")

        if len(email.split("@")[0]) > 64:
            raise ValueError("Email local part too long")

        return email

    @classmethod
    def validate_safe_string(
        cls, value: str, field_name: str = "Input", min_length: int = 1, max_length: int = 1000
    ) -> str:
        """Validate string for safe usage"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")

        # Length validation
        if len(value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters")

        if len(value) > max_length:
            raise ValueError(f"{field_name} must not exceed {max_length} characters")

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Blocked dangerous pattern in {field_name}: {pattern}")
                raise ValueError(f"{field_name} contains unsafe content")

        # Remove or replace potentially problematic characters
        # Allow basic alphanumeric and common punctuation
        clean_value = re.sub(r"[^\w\s\-_.,!?@#$%^&*()+=\[\]{}|;:<>]", "", value)

        return clean_value.strip()

    @classmethod
    def validate_pagination_params(
        cls, skip: int = 0, limit: int = 100, max_limit: int = 1000
    ) -> tuple[int, int]:
        """Validate pagination parameters"""
        if not isinstance(skip, int) or skip < 0:
            skip = 0

        if not isinstance(limit, int) or limit < 1:
            limit = 100

        limit = min(limit, max_limit)

        return skip, limit

    @classmethod
    def validate_sort_params(cls, sort_by: str, allowed_fields: list[str]) -> str:
        """Validate sort parameters against allowed fields"""
        if not isinstance(sort_by, str):
            raise ValueError("Sort field must be a string")

        # Remove any potential SQL injection
        clean_sort = re.sub(r"[^a-zA-Z0-9_\-]", "", sort_by)

        if clean_sort not in allowed_fields:
            raise ValueError(f"Invalid sort field. Allowed fields: {', '.join(allowed_fields)}")

        return clean_sort

    @classmethod
    def validate_json_data(cls, data: Any, max_size: int = 10000) -> dict:
        """Validate JSON data structure and size"""
        if isinstance(data, str):
            # Try to parse JSON string
            try:
                import json

                data = json.loads(data)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format") from None

        if not isinstance(data, dict):
            raise ValueError("Data must be a JSON object")

        # Size check
        if len(str(data)) > max_size:
            raise ValueError(f"JSON data too large. Maximum size: {max_size} characters")

        return data

    @classmethod
    def sanitize_search_term(cls, term: str) -> str:
        """Sanitize search term for safe database querying"""
        if not isinstance(term, str):
            return ""

        # Remove potentially dangerous characters
        sanitized = re.sub(r"[^\w\s\-_]", "", term)

        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized.strip()

    @classmethod
    def validate_file_upload(
        cls, filename: str, allowed_extensions: list[str] = None, max_size_mb: int = 10
    ) -> dict:
        """Validate file upload parameters"""
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        # Basic filename validation
        if not filename or len(filename) > 255:
            raise ValueError("Invalid filename")

        # Block dangerous characters
        dangerous_chars = ["..", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in dangerous_chars:
            if char in filename:
                raise ValueError(f"Filename contains invalid character: {char}")

        # Check extension if provided
        if allowed_extensions:
            file_ext = filename.lower().split(".")[-1] if "." in filename else ""
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                raise ValueError(
                    f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
                )

        return {
            "filename": filename,
            "safe_name": re.sub(r"[^a-zA-Z0-9._-]", "_", filename),
            "max_size_bytes": max_size_mb * 1024 * 1024,
        }

    @classmethod
    def validate_api_key(cls, api_key: str) -> str:
        """Validate API key format"""
        if not isinstance(api_key, str):
            raise ValueError("API key must be a string")

        # Remove whitespace
        api_key = api_key.strip()

        # Basic format validation (adjust as needed)
        if len(api_key) < 16 or len(api_key) > 128:
            raise ValueError("API key must be between 16 and 128 characters")

        # Only allow alphanumeric and specific characters
        if not re.match(r"^[a-zA-Z0-9\-_\.]+$", api_key):
            raise ValueError("API key contains invalid characters")

        return api_key


# Pydantic validators for use in schemas
def validate_uuid_field(value: str | uuid.UUID) -> str:
    """Pydantic validator for UUID fields"""
    return InputValidator.validate_uuid(value)


def validate_email_field(value: str) -> str:
    """Pydantic validator for email fields"""
    return InputValidator.validate_email(value)


def validate_safe_string_field(value: str) -> str:
    """Pydantic validator for safe string fields"""
    return InputValidator.validate_safe_string(value)


# Decorator for input validation
def validate_input(validators: dict):
    """Decorator for function input validation"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            for param_name, validator_func in validators.items():
                if param_name in kwargs:
                    try:
                        kwargs[param_name] = validator_func(kwargs[param_name])
                    except ValueError as e:
                        raise ValueError(f"Invalid {param_name}: {e!s}") from e
            return func(*args, **kwargs)

        return wrapper

    return decorator
