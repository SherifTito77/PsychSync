"""
Refactored Assessment Endpoints

This file demonstrates the refactored endpoint using the Query Builder.

Before: 65 lines of repetitive filter logic mixed with endpoint logic
After: 15 lines - clean, readable endpoint
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.api.v1.endpoints.assessments.query_builder import (
    AssessmentFilters,
    AssessmentQueryBuilder,
)
from app.core.api_utils import (
    PaginationParams,
    SortParams,
    create_paginated_list_response,
)
from app.db.models.assessment import Assessment
from app.db.models.user import User

router = APIRouter()


@router.get("/")
async def list_assessments_refactored(
    # Clean parameter grouping using AssessmentFilters
    filters: AssessmentFilters = Depends(),
    # Standard pagination and sorting
    pagination: PaginationParams = Depends(),
    sort_params: SortParams = Depends(),
    # Dependencies
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of assessments with filtering and sorting.

    REFACTORED: Using Query Builder pattern

    Before (65 lines of repetitive logic):
    ```python
    query = select(Assessment).options(selectinload(Assessment.sections))
    filter_params = {}

    if search:
        filter_params["search"] = search
        query = query.where(
            Assessment.title.ilike(f"%{search}%") |
            Assessment.description.ilike(f"%{search}%")
        )
    if category:
        filter_params["category"] = category
        query = query.where(Assessment.category == category)
    if status:
        filter_params["status"] = status
        query = query.where(Assessment.status == status)
    # ... 4+ more repetitive if blocks
    ```

    After (15 lines, clean separation):
    ```python
    builder = AssessmentQueryBuilder()
    query = builder.build(filters=filters, user=current_user)
    return await create_paginated_list_response(...)
    ```

    Complexity Reduction:
    - Lines of code: 65 → 15 (77% reduction)
    - Responsibilities: Mixed → Single (endpoint orchestration only)
    - Testability: Hard → Easy (can mock builder)
    - Maintainability: Low → High (add filters without touching endpoint)

    Enhanced Features:
    - Standardized pagination with metadata
    - Advanced filtering (search, category, status, creator, dates)
    - Configurable sorting
    - Access control (user's own + public assessments)
    """
    # Build query with all filters applied
    builder = AssessmentQueryBuilder()
    query = builder.build(filters=filters, user=current_user)

    # Return paginated response
    return await create_paginated_list_response(
        query=query,
        db=db,
        pagination=pagination,
        sort_params=sort_params,
        filter_params=filters.to_dict(),
        message="Assessments retrieved successfully",
    )


@router.get("/featured")
async def list_featured_assessments(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get featured/public assessments.

    Demonstrates using custom filters with the builder.
    """
    from app.api.v1.endpoints.assessments.query_builder import FilterSpecification
    from app.db.models.assessment import Assessment

    # Custom filter: only public assessments
    class PublicOnlyFilter(FilterSpecification):
        def is_applicable(self, **kwargs):
            return True

        def apply(self, query, **kwargs):
            return query.where(Assessment.is_public == True)

    # Build query with custom filter
    builder = AssessmentQueryBuilder()
    query = builder.build_with_custom_filters(
        user=current_user,
        custom_filters=[PublicOnlyFilter()],
    )

    return await create_paginated_list_response(
        query=query,
        db=db,
        pagination=pagination,
        sort_params=None,
        filter_params={"featured": True},
        message="Featured assessments retrieved successfully",
    )


@router.get("/my-assessments")
async def list_my_assessments(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get assessments created by the current user.

    Demonstrates pre-filling filters for common use cases.
    """
    # Pre-fill created_by filter with current user
    filters = AssessmentFilters(created_by=current_user.id)

    builder = AssessmentQueryBuilder()
    query = builder.build(filters=filters, user=current_user)

    return await create_paginated_list_response(
        query=query,
        db=db,
        pagination=pagination,
        sort_params=None,
        filter_params=filters.to_dict(),
        message="Your assessments retrieved successfully",
    )
