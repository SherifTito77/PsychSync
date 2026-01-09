# app/core/config.py

"""
LEGACY CONFIGURATION MODULE
This module provides backward compatibility while delegating to the new modular configuration.

For new code, please import directly from app.core.config.settings

DEPRECATION NOTICE:
This module is deprecated and will be removed in a future version.
Please update imports to use: from app.core.config import settings

Author: Security Team
Version: 2.0 Enterprise Security (Deprecated)
"""

import logging

from .config.settings import get_settings, reload_settings, settings

# Initialize compatibility logger
compat_logger = logging.getLogger("app.config.compatibility")


class LegacyCompatibilityWrapper:
    """
    Enhanced wrapper that provides backward compatibility for all configuration attributes
    """

    def __init__(self, settings_instance):
        self._settings = settings_instance

    def __getattr__(self, name):
        """Delegate all attribute access to settings with fallback handling"""
        try:
            return getattr(self._settings, name)
        except AttributeError:
            # Handle commonly renamed/moved attributes
            if name == "PASSWORD_MIN_LENGTH":
                return getattr(self._settings, "MIN_PASSWORD_LENGTH", 12)
            if name == "DATABASE_CONFIG":
                return self._settings.get_database_url()
            if name == "JWT_CONFIG":
                return self._settings.get_jwt_config()
            if name == "RATE_LIMIT_CONFIG":
                return self._settings.get_rate_limit_config()
            compat_logger.debug(f"Legacy config attribute '{name}' not found")
            raise

    def __getitem__(self, name):
        """Support dictionary-style access"""
        return getattr(self, name)

    def get(self, name, default=None):
        """Support dictionary-style get method"""
        try:
            return getattr(self, name)
        except AttributeError:
            return default


# Create compatibility wrapper
legacy_wrapper = LegacyCompatibilityWrapper(settings)

# Provide direct access to commonly used configuration values
# This allows imports like: from app.core.config import DATABASE_URL
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ENVIRONMENT = settings.ENVIRONMENT
DEBUG = settings.DEBUG
TESTING = getattr(settings, "TESTING", False)

# Additional commonly used values
CORS_ORIGINS = getattr(settings, "CORS_ORIGINS", [])
REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379")
RATE_LIMIT_ENABLED = getattr(settings, "RATE_LIMIT_ENABLED", True)
MIN_PASSWORD_LENGTH = getattr(settings, "MIN_PASSWORD_LENGTH", 12)
DATABASE_POOL_SIZE = getattr(settings, "DATABASE_POOL_SIZE", 40)

# Conditional deprecation warning - only warn in non-test environments
if not getattr(settings, "TESTING", False):
    compat_logger.info("Legacy config module loaded with deprecation warning enabled")

# Export everything needed for backward compatibility
__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "ALGORITHM",
    "CORS_ORIGINS",
    "DATABASE_POOL_SIZE",
    "DATABASE_URL",
    "DEBUG",
    "ENVIRONMENT",
    "MIN_PASSWORD_LENGTH",
    "RATE_LIMIT_ENABLED",
    "REDIS_URL",
    "SECRET_KEY",
    "TESTING",
    "get_settings",
    "legacy_wrapper",
    "reload_settings",
    "settings",
]
