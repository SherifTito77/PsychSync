# app/domain/exceptions/__init__.py
"""
Domain Exceptions

Custom exceptions for domain-specific errors.
These are business logic errors, not technical errors.
"""


class DomainError(Exception):
    """Base exception for domain errors"""


class ValidationError(DomainError):
    """
    Raised when validation fails.

    Example:
        >>> raise ValidationError("Email is required")
    """


class NotFoundError(DomainError):
    """
    Raised when a requested entity is not found.

    Example:
        >>> raise NotFoundError(f"User {id} not found")
    """


class AuthenticationError(DomainError):
    """
    Raised when authentication fails.

    Example:
        >>> raise AuthenticationError("Invalid credentials")
    """


class AuthorizationError(DomainError):
    """
    Raised when user lacks permission for an action.

    Example:
        >>> raise AuthorizationError("User not authorized")
    """


class BusinessRuleError(DomainError):
    """
    Raised when a business rule is violated.

    Example:
        >>> raise BusinessRuleError("Cannot delete user with active assessments")
    """
