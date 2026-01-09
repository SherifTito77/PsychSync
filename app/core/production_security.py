"""
Production Security Configuration
Provides security settings that can be toggled based on environment.
"""

import os
from typing import Literal

EnvironmentType = Literal["development", "staging", "production"]


class ProductionSecurityConfig:
    """Security configuration based on environment."""

    def __init__(self):
        self.environment: EnvironmentType = os.getenv("ENVIRONMENT", "development")
        self.debug_mode = os.getenv("DEBUG", "False").lower() == "true"

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.environment == "staging"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    def should_enable_feature(self, feature: str) -> bool:
        """
        Determine if a security feature should be enabled.

        Args:
            feature: Name of the feature ('docs', 'debug', 'captcha', etc.)

        Returns:
            True if feature should be enabled in current environment
        """
        # Features that are always disabled in production
        if self.is_production:
            if feature in ["docs", "debug", "auto_reload"]:
                return False
            if feature == "captcha" and os.getenv("CAPTCHA_ENABLED", "true").lower() == "true":
                return True
            return True

        # Features enabled in staging
        if self.is_staging:
            if feature in ["auto_reload"]:
                return False
            return True

        # All features enabled in development
        return True

    def get_security_headers(self) -> dict:
        """
        Get security headers for the current environment.

        Returns:
            Dictionary of security headers
        """
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
        }

        if not self.is_development:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return headers

    def should_hide_stack_traces(self) -> bool:
        """Determine if stack traces should be hidden."""
        return not self.is_development or not self.debug_mode

    def should_enable_rate_limiting(self) -> bool:
        """Determine if rate limiting should be enforced."""
        return not self.is_development

    def get_allowed_origins(self) -> list:
        """
        Get list of allowed CORS origins for current environment.

        Returns:
            List of allowed origins
        """
        if self.is_production:
            # In production, only allow specific domains
            return os.getenv("ALLOWED_ORIGINS", "").split(",")
        if self.is_staging:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:5174",
                os.getenv("STAGING_URL", ""),
            ]
        # Development: allow all local origins
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]


# Global config instance
security_config = ProductionSecurityConfig()


def require_production(feature: str = ""):
    """
    Decorator to require production environment for certain features.

    Args:
        feature: Feature name for error message

    Example:
        @require_production("admin")
        async def admin_panel():
            # Only runs in production
            pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not security_config.is_production:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=403,
                    detail=f"This feature ({feature}) is only available in production environment",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_production_or_staging(feature: str = ""):
    """
    Decorator to require production or staging environment.

    Args:
        feature: Feature name for error message
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not (security_config.is_production or security_config.is_staging):
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=403,
                    detail=f"This feature ({feature}) is only available in production or staging",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
