# app/core/config/application.py

"""
ENTERPRISE-GRADE APPLICATION CONFIGURATION
Core application settings and environment configuration

FEATURES:
- Multi-environment support
- Application metadata
- Feature flags
- Monitoring configuration
- Debug settings
- API versioning

Author: Security Team
Version: 2.0 Enterprise Security
"""

import logging
from typing import Any

from pydantic import Field, validator

# Initialize application configuration logger
app_config_logger = logging.getLogger("app.config.application")


class ApplicationConfig:
    """
    Enterprise-grade application configuration with comprehensive settings
    """

    # Environment settings
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    TESTING: bool = Field(default=False, env="TESTING")

    # Application metadata
    PROJECT_NAME: str = Field(default="PsychSync AI", env="PROJECT_NAME")
    APP_VERSION: str = Field(default="2.0.0", env="APP_VERSION")
    API_V1_STR: str = "/api/v1"
    APP_DESCRIPTION: str = Field(
        default="Enterprise Psychological Assessment Platform", env="APP_DESCRIPTION"
    )

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=1, env="WORKERS")
    RELOAD: bool = Field(default=False, env="RELOAD")

    # Frontend settings
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    ADMIN_FRONTEND_URL: str = Field(
        default="http://localhost:5174", env="ADMIN_FRONTEND_URL"
    )

    # Feature flags
    ENABLE_REGISTRATION: bool = Field(default=True, env="ENABLE_REGISTRATION")
    ENABLE_EMAIL_VERIFICATION: bool = Field(
        default=False, env="ENABLE_EMAIL_VERIFICATION"
    )
    ENABLE_PASSWORD_RESET: bool = Field(default=True, env="ENABLE_PASSWORD_RESET")
    ENABLE_SOCIAL_LOGIN: bool = Field(default=False, env="ENABLE_SOCIAL_LOGIN")
    ENABLE_MULTI_TENANT: bool = Field(default=True, env="ENABLE_MULTI_TENANT")

    # Monitoring and logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    ENABLE_HEALTH_CHECKS: bool = Field(default=True, env="ENABLE_HEALTH_CHECKS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # API settings
    API_DOCS_ENABLED: bool = Field(default=True, env="API_DOCS_ENABLED")
    API_DOCS_URL: str = Field(default="/docs", env="API_DOCS_URL")
    API_REDOC_URL: str = Field(default="/redoc", env="API_REDOC_URL")
    API_TITLE: str = Field(default="PsychSync AI API", env="API_TITLE")

    # Performance settings
    MAX_REQUEST_SIZE: int = Field(
        default=16 * 1024 * 1024,  # 16MB
        env="MAX_REQUEST_SIZE",
    )
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_UPLOAD_SIZE",
    )
    REQUEST_TIMEOUT_SECONDS: int = Field(default=60, env="REQUEST_TIMEOUT_SECONDS")

    # Cache settings
    CACHE_ENABLED: bool = Field(default=True, env="CACHE_ENABLED")
    CACHE_TTL_SECONDS: int = Field(
        default=300,  # 5 minutes
        env="CACHE_TTL_SECONDS",
    )
    CACHE_MAX_SIZE: int = Field(default=1000, env="CACHE_MAX_SIZE")

    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """Validate environment setting"""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of: {allowed_envs}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {allowed_levels}")
        return v.upper()

    @validator("PROJECT_NAME", "APP_VERSION", "API_TITLE")
    def validate_required_strings(cls, v):
        """Validate required string fields"""
        if not v or not v.strip():
            raise ValueError("This field cannot be empty")
        return v.strip()

    @validator("PORT", "METRICS_PORT", "WORKERS")
    def validate_positive_integers(cls, v):
        """Validate positive integer fields"""
        if v <= 0:
            raise ValueError("This field must be a positive integer")
        return v

    @validator("DEBUG")
    def validate_debug_setting(cls, v, values):
        """Validate debug setting consistency"""
        env = values.get("ENVIRONMENT", "development")
        if env == "production" and v:
            raise ValueError("DEBUG cannot be True in production environment")
        if env == "development" and not v:
            # Set debug automatically for development
            v = True
        return v

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.TESTING or self.ENVIRONMENT == "testing"

    def get_api_info(self) -> dict[str, Any]:
        """
        Get API information for documentation

        Returns:
            API information dictionary
        """
        return {
            "title": self.API_TITLE,
            "description": self.APP_DESCRIPTION,
            "version": self.APP_VERSION,
            "docs_url": self.API_DOCS_URL if self.API_DOCS_ENABLED else None,
            "redoc_url": self.API_REDOC_URL if self.API_DOCS_ENABLED else None,
            "openapi_url": "/openapi.json" if self.API_DOCS_ENABLED else None,
        }

    def get_feature_flags(self) -> dict[str, bool]:
        """
        Get all feature flags

        Returns:
            Feature flags dictionary
        """
        return {
            "registration": self.ENABLE_REGISTRATION,
            "email_verification": self.ENABLE_EMAIL_VERIFICATION,
            "password_reset": self.ENABLE_PASSWORD_RESET,
            "social_login": self.ENABLE_SOCIAL_LOGIN,
            "multi_tenant": self.ENABLE_MULTI_TENANT,
            "metrics": self.ENABLE_METRICS,
            "health_checks": self.ENABLE_HEALTH_CHECKS,
            "api_docs": self.API_DOCS_ENABLED,
            "cache": self.CACHE_ENABLED,
        }

    def get_server_config(self) -> dict[str, Any]:
        """
        Get server configuration

        Returns:
            Server configuration dictionary
        """
        return {
            "host": self.HOST,
            "port": self.PORT,
            "workers": self.WORKERS,
            "reload": self.RELOAD,
            "log_level": self.LOG_LEVEL,
        }

    def get_performance_config(self) -> dict[str, Any]:
        """
        Get performance configuration

        Returns:
            Performance configuration dictionary
        """
        return {
            "max_request_size": self.MAX_REQUEST_SIZE,
            "max_upload_size": self.MAX_UPLOAD_SIZE,
            "request_timeout": self.REQUEST_TIMEOUT_SECONDS,
            "cache_enabled": self.CACHE_ENABLED,
            "cache_ttl": self.CACHE_TTL_SECONDS,
            "cache_max_size": self.CACHE_MAX_SIZE,
        }

    def get_frontend_urls(self) -> dict[str, str]:
        """
        Get frontend URLs

        Returns:
            Frontend URLs dictionary
        """
        return {
            "main": self.FRONTEND_URL,
            "admin": self.ADMIN_FRONTEND_URL,
        }

    def validate_application_configuration(self) -> None:
        """
        Validate overall application configuration

        Raises:
            RuntimeError: If configuration is invalid
        """
        # Environment-specific validations
        if self.is_production():
            if self.DEBUG:
                raise RuntimeError("DEBUG mode is not allowed in production")

            if self.API_DOCS_ENABLED:
                app_config_logger.warning(
                    "API docs enabled in production - consider disabling"
                )

            if self.RELOAD:
                raise RuntimeError("Auto-reload is not allowed in production")

        # Port conflict check
        if self.PORT == self.METRICS_PORT:
            raise RuntimeError("Application port and metrics port cannot be the same")

        # Feature flag consistency
        if self.ENABLE_SOCIAL_LOGIN and not self.ENABLE_REGISTRATION:
            raise RuntimeError("Social login requires registration to be enabled")

        # Log configuration
        app_config_logger.info(
            "Application configuration validated",
            extra={
                "environment": self.ENVIRONMENT,
                "version": self.APP_VERSION,
                "debug": self.DEBUG,
                "workers": self.WORKERS,
                "api_docs": self.API_DOCS_ENABLED,
                "metrics": self.ENABLE_METRICS,
            },
        )

    def __init__(self, **data):
        """Initialize application configuration with validation"""
        super().__init__(**data)
        self.validate_application_configuration()

        app_config_logger.info(
            "Application configuration initialized",
            extra={
                "name": self.PROJECT_NAME,
                "version": self.APP_VERSION,
                "environment": self.ENVIRONMENT,
                "port": self.PORT,
            },
        )
