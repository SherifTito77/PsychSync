# Re-export from canonical source to eliminate duplication.
# app/core/deps.py is the single source of truth for auth dependencies.
from app.core.deps import (  # noqa: F401
    check_team_admin,
    check_team_member,
    get_admin_user_with_mfa,
    get_current_active_user,
    get_current_admin_user,
    get_current_user,
    get_current_user_optional,
    get_current_user_with_mfa,
    get_db,
    get_team_or_404,
    oauth2_scheme,
)
