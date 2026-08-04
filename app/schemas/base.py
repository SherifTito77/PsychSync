# app/schemas/base.py
"""
Base Schema Classes for PsychSync

Provides consistent base classes for all Pydantic schemas.
Follows Pydantic v2 patterns and conventions.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# STANDARD BASE SCHEMAS
# ============================================================================


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.

    All schemas should inherit from this for consistent behavior.
    """

    model_config = ConfigDict(
        from_attributes=True,  # Allow from ORM models
        populate_by_name=True,  # Allow both aliases and field names
        use_enum_values=True,  # Use enum values instead of enum objects
    )


class EntitySchema(BaseSchema):
    """
    Base schema for entities with standard fields.

    All response schemas for database entities should inherit from this.
    """

    id: UUID = Field(description="Unique entity identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TimestampedSchema(BaseSchema):
    """
    Base schema for entities with timestamps but no ID.
    """

    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


# ============================================================================
# SCHEMA MIXINS
# ============================================================================


class SoftDeleteMixin(BaseSchema):
    """
    Mixin for entities that support soft deletes.
    """

    deleted_at: datetime | None = Field(
        default=None, description="Deletion timestamp (null if not deleted)"
    )
    is_deleted: bool = Field(
        default=False, description="Whether the entity is soft-deleted"
    )


class OwnershipMixin(BaseSchema):
    """
    Mixin for entities with ownership tracking.
    """

    created_by_id: UUID = Field(description="ID of user who created this entity")
    updated_by_id: UUID | None = Field(
        default=None, description="ID of user who last updated this entity"
    )


class PaginationMixin:
    total: int = Field(description="Total number of items")
    page: int | None = Field(default=1, description="Current page number")
    page_size: int | None = Field(default=100, description="Items per page")


# ============================================================================
# STANDARD RESPONSE SCHEMAS
# ============================================================================


class MessageResponse(BaseSchema):
    """
    Standard message response.
    """

    message: str = Field(description="Response message")
    detail: str | None = Field(default=None, description="Additional details")


class ErrorResponse(BaseSchema):
    """
    Standard error response.
    """

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional error details")
    code: str | None = Field(
        default=None, description="Application-specific error code"
    )


class ValidationErrorResponse(BaseSchema):
    """
    Validation error response.
    """

    error: str = Field(default="validation_error", description="Error type")
    message: str = Field(default="Validation failed", description="Error message")
    detail: list[dict[str, Any]] = Field(
        description="List of validation errors",
        examples=[
            {
                "loc": ["body", "email"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ],
    )


# ============================================================================
# GENERIC RESPONSE WRAPPERS
# ============================================================================


class ListResponse(BaseSchema, PaginationMixin):
    """
    Generic list response with pagination.

    Type parameter:
        T: The type of items in the list

    Example:
        class UserListResponse(ListResponse[User]):
            items: list[User]
    """


class SingleResponse(BaseSchema):
    """
    Generic single item response.

    Type parameter:
        T: The type of item

    Example:
        class UserResponse(SingleResponse[User]):
            data: User
    """


# ============================================================================
# COMMON FIELD DEFINITIONS
# ============================================================================


class CommonFields:
    """
    Common field definitions for reuse across schemas.

    Usage:
        class MySchema(BaseSchema):
            email: EmailStr = CommonFields.email()
            description: str = CommonFields.description(required=False)
    """

    @staticmethod
    def uuid_field(description: str) -> Field:
        """Standard UUID field"""
        return Field(description=description)

    @staticmethod
    def email(required: bool = True) -> Field:
        """Email field"""
        return Field(description="Email address", min_length=5, max_length=255)

    @staticmethod
    def name(required: bool = True) -> Field:
        """Name field"""
        return Field(description="Name", min_length=1, max_length=255)

    @staticmethod
    def description(required: bool = False) -> Field:
        """Description field"""
        return Field(default=None, description="Description", max_length=5000)

    @staticmethod
    def timestamp() -> Field:
        """Timestamp field"""
        return Field(description="Timestamp")

    @staticmethod
    def status() -> Field:
        """Status field"""
        return Field(
            description="Status", pattern="^(active|inactive|pending|archived)$"
        )


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


class ValidationRules:
    """
    Common validation rules for use in Field() validators.

    Usage:
        class MySchema(BaseSchema):
            email: EmailStr = Field(**ValidationRules.email())
    """

    @staticmethod
    def email() -> dict[str, Any]:
        """Email validation rules"""
        return {"min_length": 5, "max_length": 255, "description": "Email address"}

    @staticmethod
    def password() -> dict[str, Any]:
        """Password validation rules"""
        return {
            "min_length": 12,
            "max_length": 128,
            "description": "Password (min 12 characters, must include uppercase, lowercase, digit, and special character)",
        }

    @staticmethod
    def name() -> dict[str, Any]:
        """Name validation rules"""
        return {"min_length": 1, "max_length": 255, "description": "Name"}

    @staticmethod
    def description() -> dict[str, Any]:
        """Description validation rules"""
        return {"max_length": 5000, "default": None, "description": "Description"}

    @staticmethod
    def url() -> dict[str, Any]:
        """URL validation rules"""
        return {"max_length": 2048, "description": "URL"}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Base schemas
    "BaseSchema",
    "EntitySchema",
    "TimestampedSchema",
    # Mixins
    "SoftDeleteMixin",
    "OwnershipMixin",
    "PaginationMixin",
    # Standard responses
    "MessageResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    # Generic wrappers
    "ListResponse",
    "SingleResponse",
    # Field helpers
    "CommonFields",
    "ValidationRules",
]
