"""
Security Services Package

Enterprise-grade security services extracted from security.py
following Single Responsibility Principle (SRP).

Modules:
    - password_service: Password hashing, verification, validation
    - token_service: JWT token creation, verification, revocation
    - authorization_service: Role checking, permissions, access control
    - input_sanitizer_service: XSS prevention, SQL injection protection

Usage:
    from app.services.security import (
        get_password_service,
        get_token_service,
        get_authorization_service,
        get_input_sanitizer_service,
    )

    password_svc = get_password_service()
    hashed = password_svc.hash_password("my_password")

Author: Security Team
Version: 1.0
"""

from app.services.security.password_service import (
    PasswordService,
    get_password_service,
    get_password_hash,
    verify_password,
    validate_password,
    generate_password_requirements,
)

from app.services.security.token_service import (
    TokenService,
    get_token_service,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    verify_token,
    decode_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_email_verification_token,
    verify_email_verification_token,
)

from app.services.security.authorization_service import (
    AuthorizationService,
    get_authorization_service,
    has_role,
    is_owner,
    is_team_member,
)

from app.services.security.input_sanitizer_service import (
    InputSanitizerService,
    get_input_sanitizer_service,
    sanitize_input,
    escape_html,
    validate_email,
    generate_csrf_token,
    validate_csrf_token,
)

__all__ = [
    # Password Service
    "PasswordService",
    "get_password_service",
    "get_password_hash",
    "verify_password",
    "validate_password",
    "generate_password_requirements",
    # Token Service
    "TokenService",
    "get_token_service",
    "create_access_token",
    "create_refresh_token",
    "create_token_pair",
    "verify_token",
    "decode_token",
    "create_password_reset_token",
    "verify_password_reset_token",
    "create_email_verification_token",
    "verify_email_verification_token",
    # Authorization Service
    "AuthorizationService",
    "get_authorization_service",
    "has_role",
    "is_owner",
    "is_team_member",
    # Input Sanitizer Service
    "InputSanitizerService",
    "get_input_sanitizer_service",
    "sanitize_input",
    "escape_html",
    "validate_email",
    "generate_csrf_token",
    "validate_csrf_token",
]
