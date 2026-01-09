"""
Log Sanitization Module
Prevents sensitive data from being exposed in log files
"""

import json
import logging
import re
from typing import Any


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that removes sensitive data from log messages
    """

    # Patterns for sensitive data that should be redacted
    SENSITIVE_PATTERNS = {
        "password": [
            r'password[=:]\s*[^\s,}"]+',
            r'pwd[=:]\s*[^\s,}"]+',
            r'pass[=:]\s*[^\s,}"]+',
            r'(?:\{|["\'])password(?:\}|["\'])\s*:\s*"[^"]+"',
        ],
        "token": [
            r'token[=:]\s*[^\s,}"]{20,}',
            r'jwt[=:]\s*[^\s,}"]{20,}',
            r'auth[_-]?token[=:]\s*[^\s,}"]{20,}',
            r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        ],
        "api_key": [
            r'api[_-]?key[=:]\s*[^\s,}"]{16,}',
            r'apikey[=:]\s*[^\s,}"]{16,}',
            r'secret[_-]?key[=:]\s*[^\s,}"]{16,}',
            r'access[_-]?key[=:]\s*[^\s,}"]{16,}',
        ],
        "credit_card": [
            r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
            r"\d{16}",
        ],
        "ssn": [
            r"\d{3}[-\s]?\d{2}[-\s]?\d{4}",
        ],
        "email": [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ],
        "ip_address": [
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        ],
        "phone": [
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            r"\b\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",
        ],
        "pii": [
            r'(?:first|last|full)[_-]?name[=:]\s*[^\s,}"]{2,}',
            r'(?:address|street|city|state|zip)[=:]\s*[^\s,}"]{5,}',
            r'(?:dob|birth[_-]?date)[=:]\s*[^\s,}"]{8,}',
        ],
        "database_url": [
            r"(?:postgres|mysql|mongodb)://[^\s]+:[^\s]+@",
        ],
        "session_id": [
            r"session[_-]?id[=:]\s*[a-f0-9]{32,}",
        ],
    }

    # Fields to redact in JSON/dict data
    SENSITIVE_FIELDS = {
        "password",
        "passwd",
        "pwd",
        "token",
        "jwt",
        "auth_token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "secret_key",
        "secret",
        "credit_card",
        "cc_number",
        "card_number",
        "ssn",
        "social_security",
        "email_address",
        "email",
        "phone_number",
        "phone",
        "mobile",
        "address",
        "street_address",
        "date_of_birth",
        "dob",
        "birth_date",
        "database_url",
        "db_url",
        "connection_string",
        "session_id",
        "sessionid",
    }

    def __init__(self, redaction_string="[REDACTED]"):
        super().__init__()
        self.redaction_string = redaction_string
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_patterns = {}
        for data_type, patterns in self.SENSITIVE_PATTERNS.items():
            self.compiled_patterns[data_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def filter(self, record):
        """Filter sensitive data from log record"""
        # Sanitize the message
        record.msg = self.sanitize(record.msg)

        # Sanitize args if present
        if hasattr(record, "args") and record.args:
            record.args = tuple(
                self.sanitize(str(arg)) if isinstance(arg, (str, bytes)) else arg
                for arg in record.args
            )

        # Sanitize extra fields if present
        if hasattr(record, "extra"):
            record.extra = self.sanitize_dict(record.extra)

        return True

    def sanitize(self, text: str) -> str:
        """Remove sensitive data from text"""
        if not isinstance(text, str):
            text = str(text)

        # Apply each pattern
        for data_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                text = pattern.sub(self.redaction_string, text)

        return text

    def sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize dictionary data"""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            # Check if key is sensitive
            if key.lower() in self.SENSITIVE_FIELDS:
                sanitized[key] = self.redaction_string
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item)
                    if isinstance(item, dict)
                    else self.sanitize(str(item))
                    if isinstance(item, (str, bytes))
                    else item
                    for item in value
                ]
            elif isinstance(value, (str, bytes)):
                sanitized[key] = self.sanitize(str(value))
            else:
                sanitized[key] = value

        return sanitized


class SecureLogger:
    """
    Secure logging wrapper that automatically sanitizes sensitive data
    """

    @staticmethod
    def setup_logging(app_name: str = "psychsync", log_level: str = "INFO"):
        """Set up secure logging with sanitization"""
        # Create logger
        logger = logging.getLogger(app_name)
        logger.setLevel(getattr(logging, log_level.upper()))

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        # Add sensitive data filter
        sensitive_filter = SensitiveDataFilter()
        console_handler.addFilter(sensitive_filter)

        # Add handler to logger
        logger.addHandler(console_handler)

        return logger


# Convenience functions for secure logging
def secure_log(logger: logging.Logger, level: str, message: str, **kwargs):
    """
    Log a message with automatic sanitization of sensitive data

    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        **kwargs: Additional fields (will be sanitized)
    """
    # Sanitize message
    sanitizer = SensitiveDataFilter()
    safe_message = sanitizer.sanitize(message)

    # Sanitize kwargs
    safe_kwargs = sanitizer.sanitize_dict(kwargs)

    # Log the message
    log_func = getattr(logger, level.lower())
    log_func(safe_message, extra=safe_kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Test the sanitizer
    test_messages = [
        "User logged in with email: test@example.com",
        "Database connection: postgres://user:secret123@localhost/db",
        "API request with token: abc123def456ghi789jkl012mno345pqr",
        "Password reset for password=MySecretPassword123",
        "Credit card: 4512-3456-7890-1234",
        "SSN: 123-45-6789",
        "IP: 192.168.1.1",
    ]

    print("🔍 LOG SANITIZATION TEST")
    print("=" * 60)

    sanitizer = SensitiveDataFilter()

    for msg in test_messages:
        sanitized = sanitizer.sanitize(msg)
        print(f"Original:  {msg}")
        print(f"Sanitized: {sanitized}")
        print()

    # Test with dict data
    test_data = {
        "user": "john@example.com",
        "password": "SecretPass123",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "address": "123 Main St",
        "safe_field": "This is fine",
    }

    print("=" * 60)
    print("🔍 DICT SANITIZATION TEST")
    print("=" * 60)

    sanitized_data = sanitizer.sanitize_dict(test_data)
    print(json.dumps(sanitized_data, indent=2))
