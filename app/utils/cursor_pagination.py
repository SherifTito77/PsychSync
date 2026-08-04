"""
Cursor-Based Pagination Utility

Provides scalable pagination that performs consistently regardless of page number,
unlike offset-based pagination which degrades linearly with page count.

Benefits over Offset Pagination:
- O(1) performance regardless of page number (uses indexed WHERE clauses)
- Consistent response times even at page 1,000,000
- No duplicate/missing results when data changes during pagination
- Memory efficient (doesn't require scanning all previous rows)

Usage Example:
    # In your endpoint or service:
    from app.utils.cursor_pagination import paginate, CursorPaginationParams

    pagination_params = CursorPaginationParams(
        cursor=request.query_params.get("cursor"),
        limit=min(int(request.query_params.get("limit", 50)), 100)
    )

    result = paginate(
        db.query(Response).filter(Response.user_id == user_id),
        pagination_params,
        ordering_column=Response.created_at,
        ordering_direction="desc"
    )

    return {
        "items": result.items,
        "next_cursor": result.next_cursor,
        "has_more": result.has_more,
        "total_count": result.total_count
    }

Author: Scalability Team
Created: 2025-02-10
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from sqlalchemy import Column, asc, desc, func, select
from sqlalchemy.orm import Query
from sqlalchemy.sql import Select

T = TypeVar("T")


@dataclass
class CursorPaginationParams:
    """
    Pagination parameters for cursor-based pagination.

    Attributes:
        cursor: Opaque cursor string from previous page (None for first page)
        limit: Number of items per page (default: 50, max: 100)
    """

    cursor: Optional[str] = None
    limit: int = 50

    def __post_init__(self):
        """Validate and clamp limit values"""
        if self.limit < 1:
            raise ValueError("limit must be at least 1")
        if self.limit > 100:
            # Prevent unbounded result sets
            self.limit = 100


@dataclass
class CursorPaginationResult(Generic[T]):
    """
    Result of cursor-based pagination.

    Attributes:
        items: List of items for current page
        next_cursor: Cursor for next page (None if no more pages)
        has_more: Whether there are more items after this page
        total_count: Total number of items (optional, requires separate count query)
    """

    items: List[T]
    next_cursor: Optional[str]
    has_more: bool
    total_count: Optional[int] = None


def paginate(
    query: Query | Select,
    params: CursorPaginationParams,
    ordering_column: Column,
    ordering_direction: str = "desc",
) -> CursorPaginationResult:
    """
    Apply cursor-based pagination to a SQLAlchemy query.

    Args:
        query: SQLAlchemy Query or Select statement
        params: Pagination parameters (cursor, limit)
        ordering_column: Column to order by (must be indexed for performance!)
        ordering_direction: "asc" or "desc" (default: "desc")

    Returns:
        CursorPaginationResult with items and metadata

    Example:
        # Get user's responses, newest first
        result = paginate(
            db.query(Response).filter(Response.user_id == user_id),
            CursorPaginationParams(cursor=cursor, limit=20),
            ordering_column=Response.created_at,
            ordering_direction="desc"
        )
    """
    if params.cursor:
        # Decode cursor and filter to items after cursor
        cursor_value = _decode_cursor(params.cursor)

        # Build WHERE clause based on ordering direction
        if ordering_direction == "desc":
            # For descending: get items with value < cursor_value
            query = query.filter(ordering_column < cursor_value)
        else:
            # For ascending: get items with value > cursor_value
            query = query.filter(ordering_column > cursor_value)

    # Apply ordering
    order_func = desc if ordering_direction == "desc" else asc
    query = query.order_by(order_func(ordering_column))

    # Fetch one extra item to determine if there are more results
    items = query.limit(params.limit + 1).all()

    # Determine if there are more items
    has_more = len(items) > params.limit
    if has_more:
        items = items[: params.limit]  # Remove extra item
        next_cursor = _encode_cursor(getattr(items[-1], ordering_column.key))
    else:
        next_cursor = None

    return CursorPaginationResult(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )


def paginate_with_count(
    query: Query | Select,
    params: CursorPaginationParams,
    ordering_column: Column,
    ordering_direction: str = "desc",
    db_session=None,
) -> CursorPaginationResult:
    """
    Apply cursor-based pagination with total count.

    WARNING: Counting can be slow on large tables. Use only when needed.
    Consider using estimated counts or cached counts for better performance.

    Args:
        query: SQLAlchemy Query or Select statement
        params: Pagination parameters
        ordering_column: Column to order by
        ordering_direction: "asc" or "desc"
        db_session: Database session (required for count query)

    Returns:
        CursorPaginationResult with items, metadata, and total count
    """
    if db_session is None:
        raise ValueError("db_session is required for count queries")

    # Get paginated result
    result = paginate(query, params, ordering_column, ordering_direction)

    # Get total count (separate query - can be slow!)
    try:
        if hasattr(query, "statement"):
            # SQLAlchemy Query object
            count_query = select(func.count()).select_from(query.statement.froms[0])
            # Apply same filters
            if query.whereclause is not None:
                count_query = count_query.where(query.whereclause)
            total_count = db_session.execute(count_query).scalar()
        else:
            # Select statement
            # For count queries on Select statements, we need to wrap it
            count_query = select(func.count()).select_from(query.subquery())
            total_count = db_session.execute(count_query).scalar()

        result.total_count = total_count
    except Exception as e:
        # Log error but don't fail pagination
        import logging

        logging.warning(f"Failed to get total count for pagination: {e}")
        result.total_count = None

    return result


def _encode_cursor(value: Any) -> str:
    """
    Encode a column value into an opaque cursor string.

    The cursor is base64-encoded JSON containing the value and type.
    This makes the cursor opaque to clients while allowing us to
    deserialize it safely.

    Args:
        value: Column value to encode

    Returns:
        Base64-encoded cursor string
    """
    import base64
    import json

    # Handle different types
    if isinstance(value, UUID):
        value_str = str(value)
        value_type = "uuid"
    elif isinstance(value, datetime):
        value_str = value.isoformat()
        value_type = "datetime"
    elif isinstance(value, int):
        value_str = str(value)
        value_type = "int"
    elif isinstance(value, str):
        value_str = value
        value_type = "str"
    else:
        value_str = str(value)
        value_type = "other"

    cursor_data = {"v": value_str, "t": value_type}
    json_str = json.dumps(cursor_data)
    return base64.b64encode(json_str.encode()).decode()


def _decode_cursor(cursor: str) -> Any:
    """
    Decode an opaque cursor string back into a column value.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Original column value

    Raises:
        ValueError: If cursor is invalid or malformed
    """
    import base64
    import json

    try:
        json_str = base64.b64decode(cursor.encode()).decode()
        cursor_data = json.loads(json_str)

        value_str = cursor_data["v"]
        value_type = cursor_data.get("t", "other")

        # Convert back to original type
        if value_type == "uuid":
            return UUID(value_str)
        elif value_type == "datetime":
            return datetime.fromisoformat(value_str)
        elif value_type == "int":
            return int(value_str)
        elif value_type == "str":
            return value_str
        else:
            return value_str

    except Exception as e:
        raise ValueError(f"Invalid cursor: {e}") from e


class CursorPaginator:
    """
    High-level paginator for common use cases.

    Example:
        paginator = CursorPaginator(Response, Response.created_at, "desc")

        # First page
        page1 = paginator.paginate(
            db,
            filters=[Response.user_id == user_id],
            limit=20
        )

        # Second page
        page2 = paginator.paginate(
            db,
            filters=[Response.user_id == user_id],
            cursor=page1.next_cursor,
            limit=20
        )
    """

    def __init__(
        self,
        model_class: type,
        ordering_column: Column,
        ordering_direction: str = "desc",
    ):
        """
        Initialize paginator for a specific model.

        Args:
            model_class: SQLAlchemy model class
            ordering_column: Column to order by
            ordering_direction: "asc" or "desc"
        """
        self.model_class = model_class
        self.ordering_column = ordering_column
        self.ordering_direction = ordering_direction

    def paginate(
        self,
        db,
        filters: Optional[List] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
        include_count: bool = False,
    ) -> CursorPaginationResult:
        """
        Paginate a query for this model.

        Args:
            db: Database session
            filters: Optional list of WHERE conditions
            cursor: Cursor from previous page
            limit: Items per page
            include_count: Whether to include total count (slower!)

        Returns:
            CursorPaginationResult
        """
        # Build base query
        query = db.query(self.model_class)

        # Apply filters
        if filters:
            for filter_condition in filters:
                query = query.filter(filter_condition)

        # Create pagination params
        params = CursorPaginationParams(cursor=cursor, limit=limit)

        # Paginate
        if include_count:
            return paginate_with_count(
                query,
                params,
                self.ordering_column,
                self.ordering_direction,
                db_session=db,
            )
        else:
            return paginate(
                query, params, self.ordering_column, self.ordering_direction
            )


# Convenience functions for common patterns


def paginate_by_id(
    query: Query,
    params: CursorPaginationParams,
    descending: bool = True,
) -> CursorPaginationResult:
    """
    Convenience function for pagination by ID (most common case).

    IDs are always indexed, so this is always performant.

    Example:
        result = paginate_by_id(
            db.query(User).filter(User.is_active == True),
            CursorPaginationParams(cursor=cursor, limit=20),
            descending=True
        )
    """
    from app.db.models.user import User

    direction = "desc" if descending else "asc"
    return paginate(query, params, User.id, direction)


def paginate_by_created_at(
    query: Query,
    params: CursorPaginationParams,
    descending: bool = True,
) -> CursorPaginationResult:
    """
    Convenience function for pagination by created_at timestamp.

    Assumes created_at column exists and is indexed.

    Example:
        result = paginate_by_created_at(
            db.query(Response).filter(Response.user_id == user_id),
            CursorPaginationParams(cursor=cursor, limit=20),
            descending=True
        )
    """
    from app.db.models.response import Response

    direction = "desc" if descending else "asc"
    return paginate(query, params, Response.created_at, direction)
