# app/core/config.py - BACKWARD COMPATIBILITY LAYER
"""
ENTERPRISE-GRADE CONFIGURATION BACKWARD COMPATIBILITY
Provides backward compatibility for existing imports

This module ensures that existing code using the old import structure
continues to work while we migrate to the new modular configuration.

Author: Security Team
Version: 2.0 Enterprise Security
"""

# Import everything from the new modular configuration
from .config import Settings, get_settings, reload_settings, settings
from .config.application import *
from .config.database import *
from .config.security import *
from .config.settings import *

# Re-export for backward compatibility
__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "settings",
    # Add other commonly imported items as needed
]


# Maintain backward compatibility for direct attribute access
class CompatibilityWrapper:
    """Wrapper class to maintain backward compatibility"""

    def __init__(self, settings_instance):
        self._settings = settings_instance

    def __getattr__(self, name):
        """Delegate attribute access to settings instance"""
        try:
            return getattr(self._settings, name)
        except AttributeError:
            # Handle any renamed or moved attributes
            if name == "PASSWORD_MIN_LENGTH":
                return getattr(self._settings, "MIN_PASSWORD_LENGTH", None)
            raise


# Create compatibility wrapper
compat_settings = CompatibilityWrapper(settings)

# For even better backward compatibility, expose settings at module level
import sys

sys.modules["app.core.config"] = sys.modules[__name__]

print("✅ Configuration backward compatibility layer initialized")
