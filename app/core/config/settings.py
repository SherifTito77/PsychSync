# app/core/config/settings.py

"""
ENTERPRISE-GRADE SETTINGS MODULE
Consolidated settings using focused configuration modules

This module provides a unified interface to all configuration settings
while maintaining separation of concerns through focused modules.

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from typing import Any

from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

# Import focused configuration modules
from app.core.config.application import ApplicationConfig
from app.core.config.database import DatabaseConfig
from app.core.config.security import SecurityConfig

# Initialize settings logger
settings_logger = logging.getLogger("app.config.settings")


class Settings(BaseSettings, ApplicationConfig, SecurityConfig, DatabaseConfig):
    """
    Enterprise-grade unified settings class

    This class consolidates all configuration modules while maintaining
    clean separation of concerns through inheritance.
    """

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables (e.g., VITE_* from frontend)

    # API Settings
    API_V1_PREFIX: str = Field(default="/api/v1", env="API_V1_PREFIX")

    @property
    def api_prefix(self) -> str:
        """Get API prefix"""
        return self.API_V1_PREFIX

    # JWT Settings (alias for ALGORITHM)
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")

    @property
    def jwt_secret(self) -> str:
        """JWT secret key - maps to SECRET_KEY for compatibility"""
        return self.SECRET_KEY

    # Security Settings
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")

    # Encryption Settings (for PII field encryption)
    ENCRYPTION_KEY: str = Field(
        default="", env="ENCRYPTION_KEY", description="Fernet encryption key for PII data at rest"
    )

    # Master Encryption Key (for advanced encryption operations)
    ENCRYPTION_MASTER_KEY: str | None = Field(
        default=None,
        env="ENCRYPTION_MASTER_KEY",
        description="Master encryption key for advanced cryptographic operations",
    )

    # Host validation settings
    ALLOWED_HOSTS: str | None = Field(
        default="localhost,127.0.0.1,0.0.0.0",
        env="ALLOWED_HOSTS",
        description="Comma-separated list of allowed hosts for Host header validation",
    )

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Get ALLOWED_HOSTS as a list"""
        if self.ALLOWED_HOSTS:
            return [h.strip() for h in self.ALLOWED_HOSTS.split(",")]
        return []

    # Cache Settings
    # CACHE_ENABLED is inherited from ApplicationConfig
    CACHE_DEFAULT_EXPIRE: int = Field(default=3600, env="CACHE_DEFAULT_EXPIRE")
    CACHE_USER_EXPIRE: int = Field(default=1800, env="CACHE_USER_EXPIRE")
    CACHE_ASSESSMENT_EXPIRE: int = Field(default=3600, env="CACHE_ASSESSMENT_EXPIRE")
    CACHE_TEAM_EXPIRE: int = Field(default=1800, env="CACHE_TEAM_EXPIRE")

    # Monitoring Settings
    SENTRY_DSN: str | None = Field(default=None, env="SENTRY_DSN")

    # Email Service Settings
    GMAIL_CLIENT_ID: str | None = Field(default=None, env="GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: str | None = Field(default=None, env="GMAIL_CLIENT_SECRET")

    # Email settings
    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_PORT: int | None = Field(default=None, env="SMTP_PORT")
    SMTP_HOST: str | None = Field(default=None, env="SMTP_HOST")
    SMTP_USER: str | None = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: str | None = Field(default=None, env="SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: str | None = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: str | None = Field(default=None, env="EMAILS_FROM_NAME")
    EMAIL_TEMPLATES_DIR: str = Field(default="app/email_templates", env="EMAIL_TEMPLATES_DIR")

    # Email Processing Settings
    EMAIL_CALLBACK_URL: str = Field(
        default="http://localhost:8000/api/v1/email/callback", env="EMAIL_CALLBACK_URL"
    )

    # Redis settings (for caching and sessions)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_PASSWORD: str | None = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")

    # External services
    SLACK_BOT_TOKEN: str | None = Field(default=None, env="SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: str | None = Field(default=None, env="SLACK_SIGNING_SECRET")
    GOOGLE_CLIENT_ID: str | None = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    OUTLOOK_CLIENT_ID: str | None = Field(default=None, env="OUTLOOK_CLIENT_ID")
    OUTLOOK_CLIENT_SECRET: str | None = Field(default=None, env="OUTLOOK_CLIENT_SECRET")

    # SIEM (Security Information and Event Management) Settings
    SIEM_ENABLED: bool = Field(default=False, env="SIEM_ENABLED")
    SIEM_PLATFORM: str = Field(default="webhook", env="SIEM_PLATFORM")
    SIEM_ENDPOINT_URL: str | None = Field(default=None, env="SIEM_ENDPOINT_URL")
    SIEM_TOKEN: str | None = Field(default=None, env="SIEM_TOKEN")
    SIEM_INDEX: str | None = Field(default="psychsync-security", env="SIEM_INDEX")
    SIEM_SOURCE: str = Field(default="psychsync", env="SIEM_SOURCE")
    SIEM_VERIFY_SSL: bool = Field(default=True, env="SIEM_VERIFY_SSL")

    # Security Monitoring Settings
    SECURITY_MONITORING_ENABLED: bool = Field(default=True, env="SECURITY_MONITORING_ENABLED")
    ANOMALY_DETECTION_THRESHOLD: float = Field(default=0.7, env="ANOMALY_DETECTION_THRESHOLD")
    SECURITY_ALERT_RETENTION_DAYS: int = Field(default=90, env="SECURITY_ALERT_RETENTION_DAYS")
    BEHAVIOR_PROFILE_RETENTION_DAYS: int = Field(default=30, env="BEHAVIOR_PROFILE_RETENTION_DAYS")

    # Failed Login Settings
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, env="MAX_LOGIN_ATTEMPTS")
    LOCKOUT_DURATION_MINUTES: int = Field(default=15, env="LOCKOUT_DURATION_MINUTES")
    LOGIN_ATTEMPT_WINDOW_MINUTES: int = Field(default=15, env="LOGIN_ATTEMPT_WINDOW_MINUTES")

    # File upload settings
    UPLOAD_DIR: str = Field(default="uploads", env="UPLOAD_DIR")
    # MAX_UPLOAD_SIZE is inherited from ApplicationConfig
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"],
        env="ALLOWED_UPLOAD_EXTENSIONS",
    )

    # Retry Configuration for External Integrations
    RETRY_MAX_ATTEMPTS: int = Field(default=3, env="RETRY_MAX_ATTEMPTS")
    RETRY_TIMEOUT_SHORT: int = Field(default=10, env="RETRY_TIMEOUT_SHORT")
    RETRY_TIMEOUT_MEDIUM: int = Field(default=30, env="RETRY_TIMEOUT_MEDIUM")
    RETRY_TIMEOUT_LONG: int = Field(default=300, env="RETRY_TIMEOUT_LONG")
    RETRY_MULTIPLIER: float = Field(default=1.0, env="RETRY_MULTIPLIER")
    RETRY_MIN_WAIT: float = Field(default=1.0, env="RETRY_MIN_WAIT")
    RETRY_MAX_WAIT: float = Field(default=10.0, env="RETRY_MAX_WAIT")
    RETRY_BACKOFF_BASE: int = Field(default=2, env="RETRY_BACKOFF_BASE")

    def __init__(self, **data):
        """Initialize settings with comprehensive validation"""
        super().__init__(**data)

        # Additional cross-module validation
        self._validate_cross_module_settings()

        settings_logger.info(
            "Settings initialized successfully",
            extra={
                "environment": self.ENVIRONMENT,
                "version": self.APP_VERSION,
                "project": self.PROJECT_NAME,
            },
        )

    def _validate_cross_module_settings(self) -> None:
        """
        Validate settings that span multiple configuration modules
        """
        # Validate email settings if email features are enabled
        if self.ENABLE_EMAIL_VERIFICATION and not all([self.SMTP_HOST, self.SMTP_USER]):
            settings_logger.warning("Email verification enabled but SMTP configuration incomplete")

        # Validate Slack settings if Slack integration is configured
        if self.SLACK_BOT_TOKEN and not self.SLACK_SIGNING_SECRET:
            settings_logger.warning("Slack bot token configured but signing secret missing")

        # Validate Redis settings if cache is enabled
        if self.CACHE_ENABLED and not self.REDIS_URL:
            settings_logger.warning("Cache enabled but Redis URL not configured")

    def get_database_url(self, async_driver: bool = True, test_mode: bool = False) -> str:
        """
        Get database URL for specific use case

        Args:
            async_driver: Use async driver
            test_mode: Use test database

        Returns:
            Database URL string
        """
        return self.get_database_url_for_env(async_driver, test_mode)

    def get_cache_config(self) -> dict[str, Any]:
        """
        Get cache configuration

        Returns:
            Cache configuration dictionary
        """
        return {
            "enabled": self.CACHE_ENABLED,
            "url": self.REDIS_URL,
            "password": self.REDIS_PASSWORD,
            "db": self.REDIS_DB,
            "max_connections": self.REDIS_MAX_CONNECTIONS,
            "ttl": self.CACHE_TTL_SECONDS,
            "max_size": self.CACHE_MAX_SIZE,
        }

    def get_email_config(self) -> dict[str, Any]:
        """
        Get email configuration

        Returns:
            Email configuration dictionary
        """
        return {
            "enabled": bool(self.SMTP_HOST),
            "host": self.SMTP_HOST,
            "port": self.SMTP_PORT,
            "tls": self.SMTP_TLS,
            "user": self.SMTP_USER,
            "password": self.SMTP_PASSWORD,
            "from_email": self.EMAILS_FROM_EMAIL,
            "from_name": self.EMAILS_FROM_NAME,
            "templates_dir": self.EMAIL_TEMPLATES_DIR,
        }

    def get_slack_config(self) -> dict[str, Any]:
        """
        Get Slack integration configuration

        Returns:
            Slack configuration dictionary
        """
        return {
            "enabled": bool(self.SLACK_BOT_TOKEN),
            "bot_token": self.SLACK_BOT_TOKEN,
            "signing_secret": self.SLACK_SIGNING_SECRET,
        }

    def get_upload_config(self) -> dict[str, Any]:
        """
        Get file upload configuration

        Returns:
            Upload configuration dictionary
        """
        return {
            "upload_dir": self.UPLOAD_DIR,
            "max_size": self.MAX_UPLOAD_SIZE,
            "allowed_extensions": self.ALLOWED_UPLOAD_EXTENSIONS,
        }

    def get_monitoring_config(self) -> dict[str, Any]:
        """
        Get monitoring configuration

        Returns:
            Monitoring configuration dictionary
        """
        return {
            "enabled": self.ENABLE_METRICS,
            "port": self.METRICS_PORT,
            "health_checks": self.ENABLE_HEALTH_CHECKS,
            "log_level": self.LOG_LEVEL,
        }

    def get_external_services_config(self) -> dict[str, Any]:
        """
        Get external services configuration

        Returns:
            External services configuration dictionary
        """
        return {
            "slack": self.get_slack_config(),
            "google_oauth": {
                "enabled": bool(self.GOOGLE_CLIENT_ID),
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
            },
        }

    def get_retry_config(self) -> dict[str, Any]:
        """
        Get retry configuration for external integrations

        Returns:
            Retry configuration dictionary with timeout and backoff settings
        """
        return {
            "max_attempts": self.RETRY_MAX_ATTEMPTS,
            "timeout_short": self.RETRY_TIMEOUT_SHORT,
            "timeout_medium": self.RETRY_TIMEOUT_MEDIUM,
            "timeout_long": self.RETRY_TIMEOUT_LONG,
            "multiplier": self.RETRY_MULTIPLIER,
            "min_wait": self.RETRY_MIN_WAIT,
            "max_wait": self.RETRY_MAX_WAIT,
            "backoff_base": self.RETRY_BACKOFF_BASE,
        }

    def validate_production_readiness(self) -> list[str]:
        """
        Validate configuration for production deployment

        Returns:
            List of validation warnings/errors
        """
        issues = []

        if self.is_production():
            # Check critical production settings
            if self.DEBUG:
                issues.append("DEBUG mode is enabled in production")

            if self.API_DOCS_ENABLED:
                issues.append("API documentation is enabled in production")

            if not self.SECRET_KEY or len(self.SECRET_KEY) < 128:
                issues.append("SECRET_KEY is too short for production")

            if not self.RATE_LIMIT_ENABLED:
                issues.append("Rate limiting is disabled in production")

            if not self.CACHE_ENABLED:
                issues.append("Caching is disabled in production (recommended for performance)")

            # Check required production configurations
            required_configs = {
                "SMTP_HOST": self.SMTP_HOST,
                "REDIS_URL": self.REDIS_URL,
                "FRONTEND_URL": self.FRONTEND_URL,
            }

            for config_name, config_value in required_configs.items():
                if not config_value:
                    issues.append(f"{config_name} is not configured for production")

        return issues

    def get_configuration_summary(self) -> dict[str, Any]:
        """
        Get a comprehensive configuration summary

        Returns:
            Configuration summary dictionary
        """
        return {
            "application": {
                "name": self.PROJECT_NAME,
                "version": self.APP_VERSION,
                "environment": self.ENVIRONMENT,
                "debug": self.DEBUG,
                "testing": self.TESTING,
            },
            "security": self.get_jwt_config(),
            "database": {
                "pool_size": self.DATABASE_POOL_SIZE,
                "ssl_mode": self.DB_SSL_MODE,
                "echo": self.DB_ECHO,
            },
            "features": self.get_feature_flags(),
            "performance": self.get_performance_config(),
            "cache": self.get_cache_config(),
            "email": self.get_email_config(),
            "monitoring": self.get_monitoring_config(),
            "retry": self.get_retry_config(),
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance

    Returns:
        Settings instance
    """
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables

    Returns:
        New settings instance
    """
    global settings
    settings = Settings()
    return settings
