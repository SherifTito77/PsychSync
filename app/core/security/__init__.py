from .auth import (
    create_access_token,
    get_current_active_user,
    get_current_user_async,
    get_password_hash,
    oauth2_scheme,
    verify_password,
    verify_token,
)

# Alias for backwards compatibility
get_current_user = get_current_user_async

from .monitoring import SecurityAlert, security_monitor
from .validators import (
    _contains_common_words,
    _get_strength_rating,
    sanitize_filename,
    sanitize_html,
    sanitize_string,
    validate_email,
    validate_password,
    validate_uuid,
)

__all__ = [
    "create_access_token",
    "get_current_active_user",
    "get_current_user",
    "get_current_user_async",
    "get_password_hash",
    "oauth2_scheme",
    "verify_password",
    "verify_token",
    "sanitize_filename",
    "sanitize_html",
    "sanitize_string",
    "validate_email",
    "validate_password",
    "validate_uuid",
    "SecurityAlert",
    "security_monitor",
    "_contains_common_words",
    "_get_strength_rating",
]
