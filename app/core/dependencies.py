"""
Dependency adapter to point to the correct locations.
"""

from app.api.v1.deps import (
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    get_db,
)

__all__ = [
    "get_current_user",
    "get_db",
    "get_current_active_user",
    "get_current_admin_user",
]
