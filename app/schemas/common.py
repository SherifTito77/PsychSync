# app/schemas/common.py
"""
Common Schema Components

Shared schema components used across multiple schema modules.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema

# ============================================================================
# ENUMS
# ============================================================================


class Status(str, Enum):
    """Common status values"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"
    DELETED = "deleted"


class UserRole(str, Enum):
    """User roles"""

    ADMIN = "ADMIN"
    USER = "USER"
    TEAM_LEAD = "TEAM_LEAD"


class AssessmentStatus(str, Enum):
    """Assessment statuses"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ResponseStatus(str, Enum):
    """Response statuses"""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


# ============================================================================
# COMMON SCHEMAS
# ============================================================================


class OwnerInfo(BaseSchema):
    """
    Owner/user information commonly embedded in responses.
    """

    id: UUID = Field(description="User ID")
    email: str = Field(description="User email")
    full_name: str | None = Field(default=None, description="User's full name")


class TimestampsMixin(BaseSchema):
    """
    Mixin providing timestamp fields.
    """

    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    deleted_at: datetime | None = Field(
        default=None, description="Deletion timestamp (if soft-deleted)"
    )


class MetadataMixin(BaseSchema):
    """
    Mixin for additional metadata.
    """

    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata as key-value pairs"
    )


# ============================================================================
# FILTER AND SORT SCHEMAS
# ============================================================================


class SortOrder(str, Enum):
    """Sort order"""

    ASC = "asc"
    DESC = "desc"


class SortField(BaseSchema):
    """
    Sort field specification.
    """

    field: str = Field(description="Field to sort by")
    order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


class FilterOptions(BaseSchema):
    """
    Base filter options.
    """

    search: str | None = Field(default=None, description="Search query")
    status: Status | None = Field(default=None, description="Filter by status")
    created_after: datetime | None = Field(
        default=None, description="Filter by creation date (after)"
    )
    created_before: datetime | None = Field(
        default=None, description="Filter by creation date (before)"
    )


class PaginationParams(BaseSchema):
    """
    Pagination parameters.
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=100, ge=1, le=1000, description="Items per page")

    @property
    def skip(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.page_size


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "Status",
    "UserRole",
    "AssessmentStatus",
    "ResponseStatus",
    "SortOrder",
    # Common schemas
    "OwnerInfo",
    "TimestampsMixin",
    "MetadataMixin",
    # Filter/sort
    "SortField",
    "FilterOptions",
    "PaginationParams",
]
