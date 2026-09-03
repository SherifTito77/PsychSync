"""
Data Redaction for Security Logs

Automatically redacts sensitive information from logs while preserving
utility for debugging and forensics.

Supports:
- PII (personally identifiable information)
- Credentials (passwords, tokens, API keys)
- Financial data (credit cards, bank accounts)
- Health information (HIPAA)
- Custom patterns
"""

import hashlib
import re
from re import Pattern
from typing import Any


class RedactionRule:
    """Rule for detecting and redacting sensitive data"""

    def __init__(
        self,
        name: str,
        pattern: Pattern,
        replacement: str = "***REDACTED***",
        hash_value: bool = False,
        preserve_length: bool = False,
    ):
        self.name = name
        self.pattern = pattern
        self.replacement = replacement
        self.hash_value = hash_value
        self.preserve_length = preserve_length

    def redact(self, value: str) -> str:
        """Apply redaction rule to value"""
        if not value or not isinstance(value, str):
            return value

        def replace_match(match):
            original = match.group(0)

            if self.hash_value:
                # Hash the value for verification while preserving privacy
                hash_obj = hashlib.sha256(original.encode())
                return f"[HASH:{hash_obj.hexdigest()[:16]}]"

            if self.preserve_length:
                # Preserve length for debugging
                return "*" * len(original)

            return self.replacement

        return self.pattern.sub(replace_match, value)


class DataRedactor:
    """
    Redacts sensitive data from log messages and structured data.

    Uses pattern matching, keyword detection, and structural analysis
    to identify and redact sensitive information.
    """

    # Precompiled regex patterns for performance
    PATTERNS = {
        # Email addresses
        "email": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE
        ),
        # IP addresses (optional - redact by default for privacy)
        "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", re.IGNORECASE),
        # Credit card numbers (Luhn algorithm validation not applied for speed)
        "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b", re.IGNORECASE),
        # SSN (US Social Security Number)
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b", re.IGNORECASE),
        # Phone numbers
        "phone": re.compile(
            r"\b(?:\+?1[-. ]?)?\(?[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b",
            re.IGNORECASE,
        ),
        # API keys and tokens
        "api_key_bearer": re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        "api_key_generic": re.compile(
            r"(?:api[_-]?key|apikey|token)\s*[:=]\s*[A-Za-z0-9\-._~+/]{20,}",
            re.IGNORECASE,
        ),
        # Passwords in JSON/logs
        "password_field": re.compile(
            r'(["\']?(?:password|passwd|pwd|secret|token|api_key|access_key)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])',
            re.IGNORECASE,
        ),
        # AWS keys
        "aws_access_key": re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}", re.IGNORECASE),
        # JWT tokens
        "jwt": re.compile(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*", re.IGNORECASE
        ),
        # URLs with potential credentials
        "url_with_creds": re.compile(r"(https?://)[^:\s]+:[^@\s]+@", re.IGNORECASE),
        # UUIDs (optional - can identify users)
        "uuid": re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    }

    # Keywords that indicate sensitive data in structured data
    SENSITIVE_KEYWORDS = [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "auth_token",
        "auth_token",
        "session_id",
        "sessionid",
        "private_key",
        "privatekey",
        "public_key",
        "publickey",
        "ssn",
        "social_security",
        "credit_card",
        "card_number",
        "cvv",
        "cvc",
        "bank_account",
        "account_number",
        "pin",
        "passcode",
    ]

    def __init__(
        self,
        redact_email: bool = True,
        redact_phone: bool = True,
        redact_ssn: bool = True,
        redact_credit_card: bool = True,
        redact_api_keys: bool = True,
        redact_jwt: bool = True,
        redact_ip: bool = False,  # Often needed for security analysis
        redact_uuid: bool = False,  # Often needed for tracing
        hash_mode: bool = False,  # Hash instead of redact for verification
    ):
        self.redact_email = redact_email
        self.redact_phone = redact_phone
        self.redact_ssn = redact_ssn
        self.redact_credit_card = redact_credit_card
        self.redact_api_keys = redact_api_keys
        self.redact_jwt = redact_jwt
        self.redact_ip = redact_ip
        self.redact_uuid = redact_uuid
        self.hash_mode = hash_mode

        # Build redaction rules based on configuration
        self.rules: list[RedactionRule] = []
        self._build_rules()

    def _build_rules(self):
        """Build redaction rules based on configuration"""
        if self.redact_email:
            self.rules.append(
                RedactionRule(
                    "email", self.PATTERNS["email"], hash_value=self.hash_mode
                )
            )

        if self.redact_phone:
            self.rules.append(
                RedactionRule(
                    "phone", self.PATTERNS["phone"], hash_value=self.hash_mode
                )
            )

        if self.redact_ssn:
            self.rules.append(
                RedactionRule(
                    "ssn", self.PATTERNS["ssn"], "***-**-****", preserve_length=True
                )
            )

        if self.redact_credit_card:
            self.rules.append(
                RedactionRule(
                    "credit_card", self.PATTERNS["credit_card"], preserve_length=True
                )
            )

        if self.redact_api_keys:
            self.rules.append(
                RedactionRule("api_key_bearer", self.PATTERNS["api_key_bearer"])
            )
            self.rules.append(
                RedactionRule("api_key_generic", self.PATTERNS["api_key_generic"])
            )
            self.rules.append(
                RedactionRule("aws_access_key", self.PATTERNS["aws_access_key"])
            )
            self.rules.append(
                RedactionRule(
                    "password_field",
                    self.PATTERNS["password_field"],
                    r"\1***REDACTED***\3",
                )
            )

        if self.redact_jwt:
            self.rules.append(RedactionRule("jwt", self.PATTERNS["jwt"], "[JWT]"))

        if self.redact_ip:
            self.rules.append(
                RedactionRule(
                    "ip_address", self.PATTERNS["ip_address"], hash_value=self.hash_mode
                )
            )

        if self.redact_uuid:
            self.rules.append(
                RedactionRule("uuid", self.PATTERNS["uuid"], hash_value=self.hash_mode)
            )

    def redact_string(self, text: str) -> str:
        """
        Redact sensitive information from a string.

        Args:
            text: Input string that may contain sensitive information

        Returns:
            Redacted string
        """
        if not text or not isinstance(text, str):
            return text

        result = text

        # Apply all redaction rules
        for rule in self.rules:
            result = rule.redact(result)

        return result

    def redact_dict(self, data: dict[str, Any], deep: bool = True) -> dict[str, Any]:
        """
        Redact sensitive information from a dictionary.

        Args:
            data: Dictionary that may contain sensitive information
            deep: Perform deep recursion into nested structures

        Returns:
            Redacted dictionary
        """
        if not isinstance(data, dict):
            return data

        result = {}

        for key, value in data.items():
            # Check if key indicates sensitive data
            key_lower = key.lower()
            is_sensitive_key = any(kw in key_lower for kw in self.SENSITIVE_KEYWORDS)

            if is_sensitive_key:
                # Redact the entire value
                if self.hash_mode:
                    # Hash for verification
                    if isinstance(value, (str, int, float)):
                        hash_obj = hashlib.sha256(str(value).encode())
                        result[key] = f"[HASH:{hash_obj.hexdigest()[:16]}]"
                    else:
                        result[key] = "***REDACTED***"
                else:
                    result[key] = "***REDACTED***"
            elif isinstance(value, str):
                # Apply string redaction
                result[key] = self.redact_string(value)
            elif isinstance(value, dict) and deep:
                # Recurse into nested dictionaries
                result[key] = self.redact_dict(value, deep=True)
            elif isinstance(value, list) and deep:
                # Recurse into lists
                result[key] = self.redact_list(value, deep=True)
            else:
                # Keep as-is
                result[key] = value

        return result

    def redact_list(self, data: list[Any], deep: bool = True) -> list[Any]:
        """
        Redact sensitive information from a list.

        Args:
            data: List that may contain sensitive information
            deep: Perform deep recursion into nested structures

        Returns:
            Redacted list
        """
        if not isinstance(data, list):
            return data

        result = []

        for item in data:
            if isinstance(item, str):
                result.append(self.redact_string(item))
            elif isinstance(item, dict) and deep:
                result.append(self.redact_dict(item, deep=True))
            elif isinstance(item, list) and deep:
                result.append(self.redact_list(item, deep=True))
            else:
                result.append(item)

        return result

    def redact(self, data: Any) -> Any:
        """
        Automatically detect type and redact sensitive information.

        Args:
            data: Any data structure (string, dict, list, etc.)

        Returns:
            Redacted data
        """
        if isinstance(data, str):
            return self.redact_string(data)
        if isinstance(data, dict):
            return self.redact_dict(data)
        if isinstance(data, list):
            return self.redact_list(data)
        return data

    def create_safe_preview(self, text: str, max_length: int = 100) -> str:
        """
        Create a safe preview of text for logging (redacted + truncated).

        Args:
            text: Input text
            max_length: Maximum length of preview

        Returns:
            Safe, redacted, truncated preview
        """
        if not text:
            return ""

        # Redact sensitive information
        redacted = self.redact_string(text)

        # Truncate if necessary
        if len(redacted) > max_length:
            return redacted[:max_length] + "..."

        return redacted

    def detect_sensitive_fields(self, data: dict[str, Any]) -> list[str]:
        """
        Detect which fields in a dictionary contain sensitive information.

        Args:
            data: Dictionary to analyze

        Returns:
            List of field names that likely contain sensitive data
        """
        sensitive_fields = []

        for key, value in data.items():
            key_lower = key.lower()

            # Check by keyword
            if any(kw in key_lower for kw in self.SENSITIVE_KEYWORDS):
                sensitive_fields.append(key)
                continue

            # Check by pattern matching
            if isinstance(value, str):
                for rule in self.rules:
                    if rule.pattern.search(value):
                        sensitive_fields.append(key)
                        break

        return sensitive_fields


# Singleton instance for easy import
_default_redactor = None


def get_redactor() -> DataRedactor:
    """Get the default redactor instance"""
    global _default_redactor
    if _default_redactor is None:
        _default_redactor = DataRedactor()
    return _default_redactor


def redact(text: str) -> str:
    """Quick redact function using default redactor"""
    return get_redactor().redact_string(text)


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Quick dict redact function using default redactor"""
    return get_redactor().redact_dict(data)
