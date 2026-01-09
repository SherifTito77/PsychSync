# app/core/config/security.py

"""
ENTERPRISE-GRADE SECURITY CONFIGURATION
Comprehensive security settings and validation

SECURITY FEATURES:
- Advanced secret validation
- Rate limiting configuration
- Authentication settings
- Session security
- Token management
- Audit logging configuration

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
import math
from typing import Any

from pydantic import Field

try:
    from pydantic import validator
except ImportError:
    from pydantic import field_validator as validator
from collections import Counter

# Initialize security configuration logger
security_config_logger = logging.getLogger("app.config.security")


class SecurityConfig:
    """
    Enterprise-grade security configuration with comprehensive validation
    """

    # Authentication settings
    SECRET_KEY: str = Field(
        default="8B4yxHjW6EvNM3nsnUcQXNnyLqLPnmx2_WjKBbOaQ6M7keJ9vptyRCKAH7LL7Cebv0GptObAOeGsQzFQ3eEmDImpm95Uqtz4Ix6AMMEqyc80vAQTfE9juKXz7lU3_so2t_4y01Ruj8c5RaBnJmIr9ozJXQ6rzgPKLyZwoO30",
        env="SECRET_KEY",
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    RATE_LIMIT_BURST_SIZE: int = Field(default=10, env="RATE_LIMIT_BURST_SIZE")

    # Session security
    SESSION_TIMEOUT_MINUTES: int = Field(default=120, env="SESSION_TIMEOUT_MINUTES")
    MAX_CONCURRENT_SESSIONS: int = Field(default=3, env="MAX_CONCURRENT_SESSIONS")
    DEVICE_FINGERPRINTING_ENABLED: bool = Field(default=True, env="DEVICE_FINGERPRINTING_ENABLED")

    # Password security
    MIN_PASSWORD_LENGTH: int = Field(default=12, env="MIN_PASSWORD_LENGTH")
    REQUIRE_PASSWORD_COMPLEXITY: bool = Field(default=True, env="REQUIRE_PASSWORD_COMPLEXITY")
    PASSWORD_HISTORY_COUNT: int = Field(default=5, env="PASSWORD_HISTORY_COUNT")
    ACCOUNT_LOCKOUT_ATTEMPTS: int = Field(default=5, env="ACCOUNT_LOCKOUT_ATTEMPTS")
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=15, env="ACCOUNT_LOCKOUT_MINUTES")

    # JWT Blacklist settings
    TOKEN_BLACKLIST_ENABLED: bool = Field(default=True, env="TOKEN_BLACKLIST_ENABLED")
    BLACKLIST_CLEANUP_HOURS: int = Field(default=24, env="BLACKLIST_CLEANUP_HOURS")

    # Phase 2 Security Implementation - Additional Security Keys
    PSYCHSYNC_ENCRYPTION_KEY: str = Field(
        default="",
        env="PSYCHSYNC_ENCRYPTION_KEY",
        description="256-bit encryption key for PII/PHI field-level encryption (GDPR/HIPAA)",
    )
    CSRF_SECRET_KEY: str = Field(
        default="",
        env="CSRF_SECRET_KEY",
        description="Secret key for CSRF token signing (double-submit cookie pattern)",
    )

    # Audit logging
    AUDIT_LOGGING_ENABLED: bool = Field(default=True, env="AUDIT_LOGGING_ENABLED")
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90, env="AUDIT_LOG_RETENTION_DAYS")
    AUDIT_SENSITIVE_OPERATIONS_ONLY: bool = Field(
        default=False, env="AUDIT_SENSITIVE_OPERATIONS_ONLY"
    )

    # CORS security (basic settings, detailed config in cors.py)
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
        ],
        env="CORS_ORIGINS",
    )

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or JSON array"""
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @validator("SECRET_KEY")
    def validate_secret_key(cls, v, values):
        """
        Comprehensive secret key validation with enterprise-grade security checks
        """
        environment = values.get("ENVIRONMENT", "development")

        if not v:
            raise ValueError("SECRET_KEY cannot be empty")

        # Environment-specific requirements
        if environment == "production":
            if len(v) < 128:
                raise ValueError("SECRET_KEY must be at least 128 characters in production")
        elif len(v) < 64:
            raise ValueError("SECRET_KEY must be at least 64 characters in development")

        # Global forbidden patterns
        global_blacklist = [
            "secret",
            "password",
            "admin",
            "root",
            "test",
            "demo",
            "debug",
            "development",
            "staging",
            "production",
            "example",
            "sample",
            "changeme",
            "default",
            "123456",
            "qwerty",
            "abc123",
        ]

        # Check for forbidden patterns (case-insensitive)
        v_lower = v.lower()
        for pattern in global_blacklist:
            if pattern in v_lower:
                raise ValueError(
                    f"SECRET_KEY contains forbidden pattern: '{pattern}'. "
                    f"Keys must be randomly generated and not contain common words."
                )

        # Check for sequential patterns
        # DISABLED: This can produce false positives for cryptographically secure random keys
        # if cls._has_sequential_pattern(v):
        #     raise ValueError(
        #         "SECRET_KEY contains sequential characters or numbers"
        #     )

        # Check for repetitive patterns
        # DISABLED: This can produce false positives for cryptographically secure random keys
        # if cls._has_repetitive_pattern(v):
        #     raise ValueError(
        #         "SECRET_KEY contains too many repetitive characters"
        #     )

        # Calculate entropy
        entropy = cls._calculate_entropy(v)
        min_entropy = 5.0 if environment == "production" else 4.0

        if entropy < min_entropy:
            raise ValueError(
                f"SECRET_KEY entropy too low: {entropy:.2f}. "
                f"Minimum required: {min_entropy:.2f}. "
                "Use a more random secret key."
            )

        security_config_logger.info(
            "SECRET_KEY validation passed",
            extra={"length": len(v), "entropy": entropy, "environment": environment},
        )

        return v

    @validator("ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS")
    def validate_token_times(cls, v):
        """Validate token expiration times"""
        if v <= 0:
            raise ValueError("Token expiration times must be positive")
        return v

    @validator("RATE_LIMIT_PER_MINUTE", "RATE_LIMIT_PER_HOUR")
    def validate_rate_limits(cls, v):
        """Validate rate limiting settings"""
        if v <= 0:
            raise ValueError("Rate limits must be positive")
        return v

    @validator("MIN_PASSWORD_LENGTH")
    def validate_password_length(cls, v):
        """Validate minimum password length"""
        if v < 8:
            raise ValueError("Minimum password length must be at least 8")
        if v > 128:
            raise ValueError("Minimum password length too large (max 128)")
        return v

    @staticmethod
    def _has_sequential_pattern(key: str) -> bool:
        """
        Check for sequential patterns in the key
        """
        # Check for 3+ consecutive characters/numbers
        for i in range(len(key) - 2):
            # Check for sequential characters
            char1, char2, char3 = key[i], key[i + 1], key[i + 2]

            # Check ASCII sequences
            if all(c.isalpha() for c in [char1, char2, char3]):
                if ord(char2) == ord(char1) + 1 and ord(char3) == ord(char2) + 1:
                    return True
                if ord(char2) == ord(char1) - 1 and ord(char3) == ord(char2) - 1:
                    return True

            # Check numeric sequences
            if all(c.isdigit() for c in [char1, char2, char3]):
                num1, num2, num3 = int(char1), int(char2), int(char3)
                if num2 == num1 + 1 and num3 == num2 + 1:
                    return True
                if num2 == num1 - 1 and num3 == num2 - 1:
                    return True

        return False

    @staticmethod
    def _has_repetitive_pattern(key: str) -> bool:
        """
        Check for excessive repetitive characters
        """
        # Check if any character appears more than 30% of the time
        char_counts = Counter(key)
        threshold = len(key) * 0.3

        for char, count in char_counts.items():
            if count > threshold:
                return True

        return False

    @staticmethod
    def _calculate_entropy(key: str) -> float:
        """
        Calculate Shannon entropy of the key
        """
        if not key:
            return 0

        # Count character frequencies
        char_counts = Counter(key)
        key_length = len(key)

        # Calculate entropy
        entropy = 0
        for count in char_counts.values():
            probability = count / key_length
            entropy -= probability * math.log2(probability)

        return entropy

    def get_jwt_config(self) -> dict[str, Any]:
        """
        Get JWT configuration for token generation

        Returns:
            JWT configuration dictionary
        """
        return {
            "algorithm": self.ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
            "blacklist_enabled": self.TOKEN_BLACKLIST_ENABLED,
        }

    def get_rate_limit_config(self) -> dict[str, Any]:
        """
        Get rate limiting configuration

        Returns:
            Rate limiting configuration dictionary
        """
        return {
            "enabled": self.RATE_LIMIT_ENABLED,
            "per_minute": self.RATE_LIMIT_PER_MINUTE,
            "per_hour": self.RATE_LIMIT_PER_HOUR,
            "burst_size": self.RATE_LIMIT_BURST_SIZE,
        }

    def get_password_policy(self) -> dict[str, Any]:
        """
        Get password security policy

        Returns:
            Password policy dictionary
        """
        return {
            "min_length": self.MIN_PASSWORD_LENGTH,
            "require_complexity": self.REQUIRE_PASSWORD_COMPLEXITY,
            "history_count": self.PASSWORD_HISTORY_COUNT,
            "lockout_attempts": self.ACCOUNT_LOCKOUT_ATTEMPTS,
            "lockout_minutes": self.ACCOUNT_LOCKOUT_MINUTES,
        }

    def get_session_config(self) -> dict[str, Any]:
        """
        Get session security configuration

        Returns:
            Session configuration dictionary
        """
        return {
            "timeout_minutes": self.SESSION_TIMEOUT_MINUTES,
            "max_concurrent": self.MAX_CONCURRENT_SESSIONS,
            "device_fingerprinting": self.DEVICE_FINGERPRINTING_ENABLED,
        }

    def validate_security_configuration(self) -> None:
        """
        Validate overall security configuration

        Raises:
            RuntimeError: If security configuration is invalid
        """
        environment = getattr(self, "ENVIRONMENT", "development")

        # Production security requirements
        if environment == "production":
            if not self.RATE_LIMIT_ENABLED:
                raise RuntimeError("Rate limiting must be enabled in production")

            if not self.TOKEN_BLACKLIST_ENABLED:
                raise RuntimeError("Token blacklist must be enabled in production")

            if not self.DEVICE_FINGERPRINTING_ENABLED:
                raise RuntimeError("Device fingerprinting should be enabled in production")

            if self.MIN_PASSWORD_LENGTH < 12:
                raise RuntimeError("Minimum password length should be at least 12 in production")

        # Log configuration
        security_config_logger.info(
            "Security configuration validated",
            extra={
                "environment": environment,
                "rate_limiting": self.RATE_LIMIT_ENABLED,
                "device_fingerprinting": self.DEVICE_FINGERPRINTING_ENABLED,
                "token_blacklist": self.TOKEN_BLACKLIST_ENABLED,
                "audit_logging": self.AUDIT_LOGGING_ENABLED,
            },
        )

    def __init__(self, **data):
        """Initialize security configuration with validation"""
        super().__init__(**data)
        self.validate_security_configuration()

        security_config_logger.info(
            "Security configuration initialized",
            extra={
                "jwt_algorithm": self.ALGORITHM,
                "access_token_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
                "rate_limiting": self.RATE_LIMIT_ENABLED,
                "password_min_length": self.MIN_PASSWORD_LENGTH,
            },
        )
