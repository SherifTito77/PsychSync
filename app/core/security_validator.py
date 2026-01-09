# app/core/security_validator.py
"""
Comprehensive Security Validation Module
Provides enterprise-grade input validation and sanitization
"""

from dataclasses import dataclass
from enum import Enum
import html
import logging
import re
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security validation levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Validation result with security context"""

    is_valid: bool
    sanitized_value: Any
    security_issues: list[str]
    risk_level: SecurityLevel
    original_value: Any = None


class SecurityValidator:
    """Enterprise-grade security validation and sanitization"""

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+\'\w+\'\s*=\s*\'\w+\')",
        r"(;\s*(DROP|DELETE|UPDATE|INSERT)\b)",
        r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"expression\s*\(",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.[\\/]",
        r"[\\/]\.\.[\\/]",
        r"[\\/]\.\.[\\/]",
        r"\.\.[\\/]\.\.",
        r"%2e%2e[\\/]",
        r"..%2f",
        r"..%5c",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]]",
        r"\b(curl|wget|nc|netcat|ssh|ftp|telnet)\b",
        r"\b(rm|mv|cp|cat|ls|ps|kill|chmod|chown)\b",
        r"\b(python|perl|ruby|bash|sh|cmd|powershell)\b",
    ]

    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.max_text_length = 10000
        self.max_name_length = 100
        self.max_email_length = 254

        # Compile regex patterns for performance
        self.sql_injection_regex = re.compile(
            "|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        self.xss_regex = re.compile(
            "|".join(self.XSS_PATTERNS), re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        self.path_traversal_regex = re.compile(
            "|".join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE
        )
        self.command_injection_regex = re.compile(
            "|".join(self.COMMAND_INJECTION_PATTERNS), re.IGNORECASE
        )

        logger.info(f"SecurityValidator initialized with level: {security_level.value}")

    def validate_uuid(self, value: str | UUID, field_name: str = "id") -> ValidationResult:
        """Validate and sanitize UUID input"""
        try:
            if isinstance(value, UUID):
                return ValidationResult(
                    is_valid=True,
                    sanitized_value=str(value),
                    security_issues=[],
                    risk_level=SecurityLevel.LOW,
                    original_value=value,
                )

            if not isinstance(value, str):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"Invalid {field_name}: must be string or UUID"],
                    risk_level=SecurityLevel.HIGH,
                    original_value=value,
                )

            # Check for injection patterns in UUID string
            if self.sql_injection_regex.search(value) or self.xss_regex.search(value):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"Potentially malicious {field_name} detected"],
                    risk_level=SecurityLevel.CRITICAL,
                    original_value=value,
                )

            # Validate UUID format
            try:
                uuid_obj = UUID(value)
                return ValidationResult(
                    is_valid=True,
                    sanitized_value=str(uuid_obj),
                    security_issues=[],
                    risk_level=SecurityLevel.LOW,
                    original_value=value,
                )
            except ValueError:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"Invalid UUID format for {field_name}"],
                    risk_level=SecurityLevel.HIGH,
                    original_value=value,
                )

        except Exception as e:
            logger.error(f"UUID validation error: {e!s}")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"Validation error for {field_name}"],
                risk_level=SecurityLevel.HIGH,
                original_value=value,
            )

    def validate_email(self, email: str, field_name: str = "email") -> ValidationResult:
        """Validate and sanitize email address"""
        try:
            if not isinstance(email, str):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"{field_name} must be a string"],
                    risk_level=SecurityLevel.HIGH,
                    original_value=email,
                )

            # Length check
            if len(email) > self.max_email_length:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"{field_name} exceeds maximum length"],
                    risk_level=SecurityLevel.MEDIUM,
                    original_value=email,
                )

            # Check for injection patterns
            issues = []
            if self.sql_injection_regex.search(email):
                issues.append(f"SQL injection pattern detected in {field_name}")
            if self.xss_regex.search(email):
                issues.append(f"XSS pattern detected in {field_name}")

            if issues:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=issues,
                    risk_level=SecurityLevel.CRITICAL,
                    original_value=email,
                )

            # Basic email validation
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email.lower().strip()):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=["Invalid email format"],
                    risk_level=SecurityLevel.MEDIUM,
                    original_value=email,
                )

            # Sanitize email
            sanitized_email = email.lower().strip()

            return ValidationResult(
                is_valid=True,
                sanitized_value=sanitized_email,
                security_issues=[],
                risk_level=SecurityLevel.LOW,
                original_value=email,
            )

        except Exception as e:
            logger.error(f"Email validation error: {e!s}")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=["Email validation error"],
                risk_level=SecurityLevel.HIGH,
                original_value=email,
            )

    def validate_text_input(
        self,
        text: str,
        field_name: str = "text",
        max_length: int | None = None,
        allow_html: bool = False,
        min_length: int = 0,
    ) -> ValidationResult:
        """Validate and sanitize text input"""
        try:
            if not isinstance(text, str):
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"{field_name} must be a string"],
                    risk_level=SecurityLevel.HIGH,
                    original_value=text,
                )

            max_len = max_length or self.max_text_length

            # Length checks
            if len(text) > max_len:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"{field_name} exceeds maximum length of {max_len}"],
                    risk_level=SecurityLevel.MEDIUM,
                    original_value=text,
                )

            if len(text) < min_length:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    security_issues=[f"{field_name} below minimum length of {min_length}"],
                    risk_level=SecurityLevel.MEDIUM,
                    original_value=text,
                )

            # Security pattern checks
            issues = []
            sanitized_text = text

            # SQL injection check
            if self.sql_injection_regex.search(text):
                issues.append(f"SQL injection pattern detected in {field_name}")
                # Remove dangerous patterns
                sanitized_text = self.sql_injection_regex.sub("", sanitized_text)

            # XSS check (if HTML is not allowed)
            if not allow_html and self.xss_regex.search(text):
                issues.append(f"XSS pattern detected in {field_name}")
                # Remove dangerous patterns
                sanitized_text = self.xss_regex.sub("", sanitized_text)

            # Command injection check
            if self.command_injection_regex.search(text):
                issues.append(f"Command injection pattern detected in {field_name}")
                # Remove dangerous patterns
                sanitized_text = self.command_injection_regex.sub("", sanitized_text)

            # HTML sanitization if needed
            if not allow_html:
                sanitized_text = html.escape(sanitized_text)

            # Additional sanitization
            sanitized_text = sanitized_text.strip()

            risk_level = SecurityLevel.CRITICAL if issues else SecurityLevel.LOW

            return ValidationResult(
                is_valid=len(issues) == 0,
                sanitized_value=sanitized_text,
                security_issues=issues,
                risk_level=risk_level,
                original_value=text,
            )

        except Exception as e:
            logger.error(f"Text validation error: {e!s}")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} validation error"],
                risk_level=SecurityLevel.HIGH,
                original_value=text,
            )

    def validate_name_input(
        self, name: str, field_name: str = "name", max_length: int | None = None
    ) -> ValidationResult:
        """Validate names (more restrictive than general text)"""
        max_len = max_length or self.max_name_length

        if not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} must be a string"],
                risk_level=SecurityLevel.HIGH,
                original_value=name,
            )

        # Length check
        if len(name) > max_len:
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} exceeds maximum length of {max_len}"],
                risk_level=SecurityLevel.MEDIUM,
                original_value=name,
            )

        # Check for injection patterns
        issues = []
        if self.sql_injection_regex.search(name):
            issues.append(f"SQL injection pattern detected in {field_name}")
        if self.xss_regex.search(name):
            issues.append(f"XSS pattern detected in {field_name}")

        # Name-specific validation - allow only letters, numbers, spaces, hyphens, underscores
        name_pattern = r"^[a-zA-Z0-9\s\-_\.]+$"
        if not re.match(name_pattern, name.strip()):
            issues.append(f"{field_name} contains invalid characters")

        if issues:
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=issues,
                risk_level=SecurityLevel.CRITICAL,
                original_value=name,
            )

        # Sanitize name
        sanitized_name = html.escape(name.strip())

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_name,
            security_issues=[],
            risk_level=SecurityLevel.LOW,
            original_value=name,
        )

    def validate_search_query(self, query: str, field_name: str = "search") -> ValidationResult:
        """Validate search query parameters"""
        if not isinstance(query, str):
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} must be a string"],
                risk_level=SecurityLevel.HIGH,
                original_value=query,
            )

        # Length limit for search queries
        if len(query) > 500:
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} exceeds maximum length"],
                risk_level=SecurityLevel.MEDIUM,
                original_value=query,
            )

        # Security pattern checks
        issues = []
        if self.sql_injection_regex.search(query):
            issues.append(f"SQL injection pattern detected in {field_name}")
        if self.command_injection_regex.search(query):
            issues.append(f"Command injection pattern detected in {field_name}")

        # Sanitize search query
        sanitized_query = query.strip()
        # Remove potentially dangerous characters but keep search-friendly characters
        sanitized_query = re.sub(r'[<>"\'`;&|]', "", sanitized_query)

        if issues and self.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized_query,
                security_issues=issues,
                risk_level=SecurityLevel.HIGH,
                original_value=query,
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized_query,
            security_issues=issues,
            risk_level=SecurityLevel.LOW if not issues else SecurityLevel.MEDIUM,
            original_value=query,
        )

    def validate_pagination_params(
        self, skip: int = 0, limit: int = 100, max_limit: int = 1000
    ) -> ValidationResult:
        """Validate pagination parameters"""
        try:
            issues = []

            # Convert to int if needed
            if isinstance(skip, str):
                try:
                    skip = int(skip)
                except ValueError:
                    issues.append("Invalid skip parameter")
                    skip = 0

            if isinstance(limit, str):
                try:
                    limit = int(limit)
                except ValueError:
                    issues.append("Invalid limit parameter")
                    limit = 100

            # Validate ranges
            if skip < 0:
                issues.append("Skip parameter cannot be negative")
                skip = 0

            if limit < 1:
                issues.append("Limit parameter must be at least 1")
                limit = 100

            if limit > max_limit:
                issues.append(f"Limit parameter exceeds maximum of {max_limit}")
                limit = max_limit

            return ValidationResult(
                is_valid=len(issues) == 0,
                sanitized_value={"skip": skip, "limit": limit},
                security_issues=issues,
                risk_level=SecurityLevel.LOW if not issues else SecurityLevel.MEDIUM,
                original_value={"skip": skip, "limit": limit},
            )

        except Exception as e:
            logger.error(f"Pagination validation error: {e!s}")
            return ValidationResult(
                is_valid=False,
                sanitized_value={"skip": 0, "limit": 100},
                security_issues=["Pagination validation error"],
                risk_level=SecurityLevel.HIGH,
                original_value={"skip": skip, "limit": limit},
            )

    def sanitize_dict(
        self,
        data: dict[str, Any],
        text_fields: list[str],
        name_fields: list[str] = None,
        email_fields: list[str] = None,
    ) -> ValidationResult:
        """Sanitize dictionary of data"""
        try:
            sanitized_data = {}
            all_issues = []
            max_risk = SecurityLevel.LOW

            name_fields = name_fields or []
            email_fields = email_fields or []

            for key, value in data.items():
                if key in text_fields:
                    result = self.validate_text_input(str(value), key)
                elif key in name_fields:
                    result = self.validate_name_input(str(value), key)
                elif key in email_fields:
                    result = self.validate_email(str(value), key)
                elif isinstance(value, str):
                    # Basic string sanitization for other fields
                    result = self.validate_text_input(value, key, allow_html=False)
                else:
                    # Pass through non-string values as-is
                    result = ValidationResult(
                        is_valid=True,
                        sanitized_value=value,
                        security_issues=[],
                        risk_level=SecurityLevel.LOW,
                        original_value=value,
                    )

                sanitized_data[key] = result.sanitized_value
                all_issues.extend(result.security_issues)

                # Update risk level
                if result.risk_level.value > max_risk.value:
                    max_risk = result.risk_level

            return ValidationResult(
                is_valid=len(all_issues) == 0,
                sanitized_value=sanitized_data,
                security_issues=all_issues,
                risk_level=max_risk,
                original_value=data,
            )

        except Exception as e:
            logger.error(f"Dictionary sanitization error: {e!s}")
            return ValidationResult(
                is_valid=False,
                sanitized_value={},
                security_issues=["Data sanitization error"],
                risk_level=SecurityLevel.HIGH,
                original_value=data,
            )

    def validate_file_path(self, file_path: str, field_name: str = "file_path") -> ValidationResult:
        """Validate file paths against traversal attacks"""
        if not isinstance(file_path, str):
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=[f"{field_name} must be a string"],
                risk_level=SecurityLevel.HIGH,
                original_value=file_path,
            )

        issues = []

        # Check for path traversal patterns
        if self.path_traversal_regex.search(file_path):
            issues.append(f"Path traversal pattern detected in {field_name}")

        # Additional path validation
        normalized_path = file_path.replace("\\", "/")

        # Check for absolute paths (should be relative)
        if normalized_path.startswith("/"):
            issues.append(f"Absolute path not allowed in {field_name}")
            normalized_path = normalized_path.lstrip("/")

        # Check for dangerous file extensions
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".pif",
            ".scr",
            ".vbs",
            ".js",
            ".jar",
        ]
        file_ext = normalized_path.lower().split(".")[-1] if "." in normalized_path else ""

        if f".{file_ext}" in dangerous_extensions:
            issues.append(f"Dangerous file extension detected in {field_name}")

        if issues:
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                security_issues=issues,
                risk_level=SecurityLevel.CRITICAL,
                original_value=file_path,
            )

        return ValidationResult(
            is_valid=True,
            sanitized_value=normalized_path,
            security_issues=[],
            risk_level=SecurityLevel.LOW,
            original_value=file_path,
        )


# Global validator instance
security_validator = SecurityValidator(SecurityLevel.HIGH)
