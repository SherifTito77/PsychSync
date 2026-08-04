# app/core/config/__init__.py

"""
ENTERPRISE-GRADE CONFIGURATION MODULE
Comprehensive configuration management for PsychSync

This package provides modular, secure, and validated configuration
management for the PsychSync application.

MODULE STRUCTURE:
- settings.py: Main unified settings class
- application.py: Application and environment configuration
- security.py: Security and authentication configuration
- database.py: Database connection and pool configuration
- ../cors.py: CORS configuration (separated for security)

Author: Security Team
Version: 2.0 Enterprise Security
"""

from .settings import Settings, get_settings, reload_settings, settings


def get_database_url(async_driver: bool = True, test_mode: bool = False) -> str:
    """Get database URL from settings."""
    return settings.get_database_url(async_driver=async_driver, test_mode=test_mode)


__all__ = [
    "Settings",
    "get_database_url",
    "get_settings",
    "reload_settings",
    "settings",
]

# Module information
__version__ = "2.0.0"
__author__ = "Security Team"
__description__ = "Enterprise-grade configuration management"
