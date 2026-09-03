# app/core/pagination.py
"""
Comprehensive Pagination System
Supports cursor-based, offset-based, and page-based pagination
"""

from functools import wraps
from math import ceil
from typing import Any, Generic, TypeVar

from fastapi import HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    )

    @property
    def offset(self) -> int:
        """Calculate offset from page and size"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """Get limit"""
        return self.size


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination parameters"""

    cursor: str | None = Field(None, description="Cursor for pagination")
    size: int = Field(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    )
    direction: str = Field(
        "forward", regex="^(forward|backward)$", description="Pagination direction"
    )


class OffsetPaginationParams(BaseModel):
    """Offset-based pagination parameters"""

    offset: int = Field(0, ge=0, description="Number of items to skip")
    size: int = Field(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there's a next page")
    has_prev: bool = Field(description="Whether there's a previous page")
    next_page: int | None = Field(None, description="Next page number")
    prev_page: int | None = Field(None, description="Previous page number")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response from raw data"""
        pages = ceil(total / size) if size > 0 else 0
        has_next = page < pages
        has_prev = page > 1
        next_page = page + 1 if has_next else None
        prev_page = page - 1 if has_prev else None

        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=next_page,
            prev_page=prev_page,
        )


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Cursor-based paginated response"""

    items: list[T] = Field(description="List of items")
    next_cursor: str | None = Field(None, description="Next page cursor")
    prev_cursor: str | None = Field(None, description="Previous page cursor")
    has_next: bool = Field(description="Whether there are more items")
    has_prev: bool = Field(description="Whether there are previous items")
    size: int = Field(description="Items per page")


class OffsetPaginatedResponse(BaseModel, Generic[T]):
    """Offset-based paginated response"""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Current offset")
    size: int = Field(description="Items per page")
    has_next: bool = Field(description="Whether there are more items")
    next_offset: int | None = Field(None, description="Next offset")


class PaginationHelper:
    """Helper class for pagination operations"""

    @staticmethod
    async def paginate_query(
        db: AsyncSession, query, pagination: PaginationParams, count_query=None
    ) -> tuple[list[Any], int]:
        """
        Execute paginated query and return items and total count

        Args:
            db: Database session
            query: SQLAlchemy select query
            pagination: Pagination parameters
            count_query: Optional custom count query

        Returns:
            (items, total_count)
        """
        # Get total count
        if count_query is None:
            count_query = select(func.count()).select_from(query.subquery())

        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Apply pagination and get items
        paginated_query = query.offset(pagination.offset).limit(pagination.size)
        result = await db.execute(paginated_query)
        items = result.scalars().all()

        return items, total

    @staticmethod
    async def paginate_with_filters(
        db: AsyncSession,
        base_model,
        filters: dict[str, Any] = None,
        pagination: PaginationParams = None,
        eager_loads: list[str] = None,
        order_by=None,
    ) -> PaginatedResponse:
        """
        Paginate model with optional filters and eager loading

        Args:
            db: Database session
            base_model: SQLAlchemy model class
            filters: Dictionary of filters to apply
            pagination: Pagination parameters
            eager_loads: List of relationships to eager load
            order_by: SQLAlchemy order by clause

        Returns:
            PaginatedResponse
        """
        pagination = pagination or PaginationParams()
        filters = filters or {}

        # Build base query
        query = select(base_model)

        # Apply eager loads
        if eager_loads:
            for load in eager_loads:
                query = query.options(selectinload(getattr(base_model, load)))

        # Apply filters
        for field, value in filters.items():
            if hasattr(base_model, field) and value is not None:
                if isinstance(value, list):
                    query = query.where(getattr(base_model, field).in_(value))
                else:
                    query = query.where(getattr(base_model, field) == value)

        # Apply ordering
        if order_by:
            query = query.order_by(order_by)
        elif hasattr(base_model, "created_at"):
            query = query.order_by(base_model.created_at.desc())

        # Get paginated results
        items, total = await PaginationHelper.paginate_query(db, query, pagination)

        return PaginatedResponse.create(
            items=items, total=total, page=pagination.page, size=pagination.size
        )

    @staticmethod
    def generate_cursor(item: Any, sort_field: str = "created_at") -> str:
        """Generate cursor for item"""
        if hasattr(item, sort_field):
            value = getattr(item, sort_field)
            # Convert to string and encode
            cursor_value = str(value).encode("utf-8")
            # Create simple cursor (in production, use proper encoding)
            return cursor_value.hex()
        return ""

    @staticmethod
    def parse_cursor(cursor: str, sort_field: str = "created_at") -> Any:
        """Parse cursor back to value"""
        if not cursor:
            return None
        try:
            # Decode cursor (in production, use proper decoding)
            cursor_value = bytes.fromhex(cursor)
            return cursor_value.decode("utf-8")
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            return None


# FastAPI dependency for pagination
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    ),
) -> PaginationParams:
    """FastAPI dependency for pagination parameters"""
    return PaginationParams(page=page, size=size)


def get_cursor_pagination_params(
    cursor: str | None = Query(None, description="Cursor for pagination"),
    size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    ),
    direction: str = Query(
        "forward", regex="^(forward|backward)$", description="Pagination direction"
    ),
) -> CursorPaginationParams:
    """FastAPI dependency for cursor pagination parameters"""
    return CursorPaginationParams(cursor=cursor, size=size, direction=direction)


def get_offset_pagination_params(
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (1-{settings.MAX_PAGE_SIZE})",
    ),
) -> OffsetPaginationParams:
    """FastAPI dependency for offset pagination parameters"""
    return OffsetPaginationParams(offset=offset, size=size)


# Pagination decorators for endpoint functions
def paginated_response(
    default_size: int | None = None,
    max_size: int | None = None,
    pagination_type: str = "page",  # "page", "cursor", "offset"
):
    """
    Decorator for paginated endpoints

    Args:
        default_size: Default page size
        max_size: Maximum page size
        pagination_type: Type of pagination
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract pagination params from kwargs
            if pagination_type == "page":
                pagination = kwargs.get("pagination")
                if not pagination:
                    pagination = PaginationParams(
                        page=kwargs.get("page", 1),
                        size=kwargs.get(
                            "size", default_size or settings.DEFAULT_PAGE_SIZE
                        ),
                    )
            elif pagination_type == "cursor":
                pagination = kwargs.get("cursor_pagination")
                if not pagination:
                    pagination = CursorPaginationParams(
                        cursor=kwargs.get("cursor"),
                        size=kwargs.get(
                            "size", default_size or settings.DEFAULT_PAGE_SIZE
                        ),
                        direction=kwargs.get("direction", "forward"),
                    )
            else:  # offset
                pagination = kwargs.get("offset_pagination")
                if not pagination:
                    pagination = OffsetPaginationParams(
                        offset=kwargs.get("offset", 0),
                        size=kwargs.get(
                            "size", default_size or settings.DEFAULT_PAGE_SIZE
                        ),
                    )

            # Validate size
            if max_size and pagination.size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Page size cannot exceed {max_size}",
                )

            # Add pagination to kwargs
            kwargs["_pagination"] = pagination

            # Call the function
            result = await func(*args, **kwargs)

            return result

        return wrapper

    return decorator


# Search and filter helper
class SearchFilterHelper:
    """Helper for search and filtering in pagination"""

    @staticmethod
    def apply_search_filter(query, model, search_term: str, search_fields: list[str]):
        """Apply text search to query"""
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(model, field):
                    search_conditions.append(
                        getattr(model, field).ilike(f"%{search_term}%")
                    )

            if search_conditions:
                query = query.where(or_(*search_conditions))

        return query

    @staticmethod
    def apply_date_filter(
        query, model, start_date=None, end_date=None, date_field="created_at"
    ):
        """Apply date range filter to query"""
        if hasattr(model, date_field):
            if start_date:
                query = query.where(getattr(model, date_field) >= start_date)
            if end_date:
                query = query.where(getattr(model, date_field) <= end_date)

        return query

    @staticmethod
    def apply_status_filter(
        query, model, status_values: list[str], status_field="status"
    ):
        """Apply status filter to query"""
        if status_values and hasattr(model, status_field):
            query = query.where(getattr(model, status_field).in_(status_values))

        return query
