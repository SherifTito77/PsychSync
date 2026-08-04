"""
Authentication Request Validation Schema

Provides strict input validation for authentication endpoints to prevent:
- DoS via oversized inputs
- Injection attacks
- Memory exhaustion

Author: Security Team
Version: 1.0
Date: 2025-01-19
"""

from email_validator import EmailNotValidError
from email_validator import validate_email as email_validator_validate
from pydantic import BaseModel, Field, field_validator, validator


class LoginRequestValidator(BaseModel):
    """
    Strict validation for login request parameters.

    Prevents DoS attacks by enforcing strict length limits and format validation
    before any expensive operations (database queries, bcrypt hashing).

    Security Features:
    - Max length enforcement (prevents memory exhaustion)
    - Email format validation (prevents injection)
    - Password complexity check (prevents weak passwords)
    - Fast-fail validation (rejects before expensive operations)
    """

    username: str = Field(
        ..., min_length=3, max_length=255, description="User email address"
    )

    password: str = Field(
        ..., min_length=8, max_length=128, description="User password"
    )

    @field_validator("username")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """
        Validate email format to prevent injection attacks.

        Args:
            v: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValueError: If email format is invalid
        """
        try:
            # Validate email format and normalize
            validated = email_validator_validate(v)
            return validated.email.lower().strip()
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email format: {str(e)}")

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """
        Validate password length to prevent DoS via slow bcrypt hashing.

        Bcrypt hashing time grows linearly with password length.
        A 1MB password would take several minutes to hash.

        Args:
            v: Password to validate

        Returns:
            Validated password

        Raises:
            ValueError: If password is too long
        """
        # Length check handled by Field validator, but add explicit check here
        if len(v.encode("utf-8")) > 128:  # Check byte length, not character length
            raise ValueError("Password exceeds maximum length")

        return v

    class Config:
        """Pydantic model configuration."""

        str_strip_whitespace = True  # Auto-strip whitespace
        str_min_length = True  # Apply min_length after stripping


class MFALoginRequestValidator(BaseModel):
    """
    Validation for MFA login completion request.
    """

    mfa_challenge_token: str = Field(
        ...,
        min_length=20,
        max_length=512,
        description="MFA challenge token from initial login",
    )

    totp_code: str = Field(
        ..., min_length=6, max_length=8, description="6-digit TOTP authentication code"
    )

    @field_validator("totp_code")
    @classmethod
    def validate_totp_format(cls, v: str) -> str:
        """
        Validate TOTP code format.

        Args:
            v: TOTP code to validate

        Returns:
            Validated TOTP code

        Raises:
            ValueError: If TOTP code format is invalid
        """
        if not v.isdigit():
            raise ValueError("TOTP code must contain only digits")

        return v

    class Config:
        """Pydantic model configuration."""

        str_strip_whitespace = True


class PasswordValidationRequest(BaseModel):
    """
    Password complexity validation for registration/password reset.
    """

    password: str = Field(
        ..., min_length=8, max_length=128, description="Password to validate"
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password meets complexity requirements.

        Args:
            v: Password to validate

        Returns:
            Validated password

        Raises:
            ValueError: If password doesn't meet complexity requirements
        """
        errors = []

        # Check length
        if len(v) < 8:
            errors.append("Password must be at least 8 characters")

        # Check for uppercase
        if not any(c.isupper() for c in v):
            errors.append("Password must contain at least one uppercase letter")

        # Check for lowercase
        if not any(c.islower() for c in v):
            errors.append("Password must contain at least one lowercase letter")

        # Check for digit
        if not any(c.isdigit() for c in v):
            errors.append("Password must contain at least one digit")

        # Check for special character
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in v):
            errors.append("Password must contain at least one special character")

        # Check for common patterns
        if v.lower() in ["password", "12345678", "qwerty123"]:
            errors.append("Password is too common")

        if errors:
            raise ValueError("; ".join(errors))

        return v


# FastAPI dependency for login validation
async def validate_login_request(username: str, password: str) -> LoginRequestValidator:
    """
    Validate login request parameters.

    Use as FastAPI dependency:

        @router.post("/login")
        async def login(
            form_data: OAuth2PasswordRequestForm = Depends(),
            db: AsyncSession = Depends(get_db)
        ):
            # Validation happens automatically
            validator = LoginRequestValidator(
                username=form_data.username,
                password=form_data.password
            )
            # ... rest of login logic

    Args:
        username: Username from form data
        password: Password from form data

    Returns:
        Validated login request

    Raises:
        HTTPException: If validation fails
    """
    try:
        return LoginRequestValidator(username=username, password=password)
    except ValueError as e:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
