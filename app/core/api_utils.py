# app/core/api_utils.py
"""
Common API utilities and decorators for consistent endpoint implementation
Includes pagination, filtering, caching, and error handling utilities
"""

from collections.abc import Callable
from datetime import datetime
from functools import wraps
import time
from typing import Any, TypeVar
import uuid

from fastapi import HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.core.response import (
    ErrorDetail,
    FilterMeta,
    ResponseStatus,
    create_error_response,
    create_paginated_response,
    create_success_response,
)

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""

    page: int = Query(1, ge=1, description="Page number (1-based)")
    size: int = Query(20, ge=1, le=1000, description="Items per page")


class SortParams(BaseModel):
    """Standard sorting parameters"""

    sort_by: str | None = Query(None, description="Field to sort by")
    sort_order: str | None = Query("asc", regex="^(asc|desc)$", description="Sort order")


class FilterParams(BaseModel):
    """Base filter parameters"""

    created_after: datetime | None = Query(None, description="Filter items created after this date")
    created_before: datetime | None = Query(
        None, description="Filter items created before this date"
    )
    search: str | None = Query(None, description="Search term")
    status: str | None = Query(None, description="Status filter")


def get_pagination_params(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=1000)
) -> PaginationParams:
    """Get pagination parameters with validation"""
    return PaginationParams(page=page, size=size)


def get_sort_params(sort_by: str | None = None, sort_order: str | None = "asc") -> SortParams:
    """Get sorting parameters with validation"""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


def create_filter_meta(
    applied_filters: dict[str, Any], available_filters: dict[str, Any], sort_params: SortParams
) -> FilterMeta:
    """Create filter metadata"""
    return FilterMeta(
        applied_filters=applied_filters,
        available_filters=available_filters,
        sort_by=sort_params.sort_by,
        sort_order=sort_params.sort_order,
    )


def cache_response(
    expire_seconds: int = 300, key_prefix: str = "api", vary_on: list[str] | None = None
):
    """Decorator for caching API responses"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"

            # Add variation parameters to cache key
            if vary_on:
                for param in vary_on:
                    if param in kwargs:
                        cache_key += f":{param}:{kwargs[param]}"

            # Try to get from cache
            cached_result = cache_get(cache_key)
            if cached_result:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache the result
            cache_set(cache_key, result, expire_seconds)

            return result

        return wrapper

    return decorator


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure and log API performance"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # Add performance metadata if response supports it
            if hasattr(result, "meta"):
                result.meta.performance = {
                    "execution_time_ms": round(execution_time, 2),
                    "request_id": request_id,
                }
                result.meta.request_id = request_id

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            # Log performance even for errors
            print(f"Request {request_id} failed after {execution_time:.2f}ms: {e}")
            raise

    return wrapper


def handle_api_errors(func: Callable) -> Callable:
    """Decorator for consistent error handling"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except PermissionError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied") from e
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
            ) from e

    return wrapper


async def apply_pagination(
    query: Any, db: AsyncSession, pagination: PaginationParams
) -> tuple[list[Any], int]:
    """Apply pagination to a SQLAlchemy query"""
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (pagination.page - 1) * pagination.size
    paginated_query = query.offset(offset).limit(pagination.size)

    result = await db.execute(paginated_query)
    items = result.scalars().all()

    return list(items), total


def apply_filters(query: Any, filter_params: dict[str, Any]) -> Any:
    """Apply common filters to a SQLAlchemy query"""
    # Date range filters
    if filter_params.get("created_after"):
        query = query.filter(
            query.column_descriptions[0]["type"].created_at >= filter_params["created_after"]
        )

    if filter_params.get("created_before"):
        query = query.filter(
            query.column_descriptions[0]["type"].created_at <= filter_params["created_before"]
        )

    # Status filter
    if filter_params.get("status"):
        if hasattr(query.column_descriptions[0]["type"], "status"):
            query = query.filter(
                query.column_descriptions[0]["type"].status == filter_params["status"]
            )

    # Search filter (basic implementation)
    if filter_params.get("search"):
        search_term = f"%{filter_params['search']}%"
        if hasattr(query.column_descriptions[0]["type"], "name"):
            query = query.filter(query.column_descriptions[0]["type"].name.ilike(search_term))

    return query


def apply_sorting(query: Any, sort_params: SortParams) -> Any:
    """Apply sorting to a SQLAlchemy query"""
    if sort_params.sort_by and hasattr(query.column_descriptions[0]["type"], sort_params.sort_by):
        sort_field = getattr(query.column_descriptions[0]["type"], sort_params.sort_by)

        if sort_params.sort_order == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
    # Default sorting
    elif hasattr(query.column_descriptions[0]["type"], "created_at"):
        query = query.order_by(query.column_descriptions[0]["type"].created_at.desc())
    else:
        query = query.order_by(query.column_descriptions[0]["type"].id.desc())

    return query


async def create_paginated_list_response(
    query: Any,
    db: AsyncSession,
    pagination: PaginationParams,
    sort_params: SortParams,
    filter_params: dict[str, Any] = None,
    message: str = "Items retrieved successfully",
):
    """Create a paginated response from a SQLAlchemy query"""
    filter_params = filter_params or {}

    # Apply filters, sorting, and pagination
    query = apply_filters(query, filter_params)
    query = apply_sorting(query, sort_params)
    items, total = await apply_pagination(query, db, pagination)

    # Create metadata
    pagination_meta = create_filter_meta(
        applied_filters=filter_params, available_filters={}, sort_params=sort_params
    )

    return create_paginated_response(
        data=items,
        page=pagination.page,
        size=pagination.size,
        total=total,
        message=message,
        filters=pagination_meta,
    )


def validate_permissions(required_permissions: list[str]):
    """Decorator to validate user permissions"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (typically injected by Depends)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
                )

            # Check permissions (simplified - implement based on your auth system)
            user_permissions = getattr(current_user, "permissions", [])

            for permission in required_permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission '{permission}' required",
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Request validation utilities
def validate_request_id(request: Request) -> str:
    """Extract or generate request ID"""
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    return request_id


# Rate limiting utilities
def create_rate_limit_response(retry_after: int = 60) -> JSONResponse:
    """Create a standardized rate limit exceeded response"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=create_error_response(
            message="Rate limit exceeded",
            status=ResponseStatus.RATE_LIMITED,
            error_code="RATE_LIMIT_EXCEEDED",
        ).dict(),
        headers={"Retry-After": str(retry_after)},
    )


# Response formatting utilities
def format_datetime(dt: datetime) -> str:
    """Format datetime for API responses"""
    return dt.isoformat()


def serialize_model(model_instance: Any) -> dict[str, Any]:
    """Serialize a SQLAlchemy model instance"""
    if hasattr(model_instance, "dict"):
        return model_instance.dict()
    # Fallback for models without dict method
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, datetime):
            value = format_datetime(value)
        result[column.name] = value
    return result


# Bulk operation utilities
def create_bulk_response(
    operation: str,
    total_items: int,
    successful_items: int,
    failed_items: int,
    errors: list[ErrorDetail] = None,
) -> dict[str, Any]:
    """Create response for bulk operations"""
    success_rate = (successful_items / total_items * 100) if total_items > 0 else 0

    return create_success_response(
        data={
            "operation": operation,
            "total_items": total_items,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "success_rate": round(success_rate, 2),
            "errors": errors or [],
        },
        message=f"{operation} completed with {success_rate:.1f}% success rate",
    )
