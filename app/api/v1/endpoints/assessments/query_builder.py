"""
Assessment Query Builder - Refactored

This module provides a clean, composable way to build filtered queries
for assessments, eliminating repetitive filter code in endpoints.

Before: 65 lines of repetitive if/where blocks
After: 15 lines with composable filter specifications
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from app.db.models.assessment import Assessment


class FilterSpecification(ABC):
    """
    Base class for filter specifications.

    Each filter knows how to apply itself to a query.
    This follows the Single Responsibility Principle.
    """

    @abstractmethod
    def is_applicable(self, **kwargs) -> bool:
        """Check if this filter should be applied"""
        pass

    @abstractmethod
    def apply(self, query: Select, **kwargs) -> Select:
        """Apply this filter to the query"""
        pass


class SearchFilter(FilterSpecification):
    """Filter by search term (title or description)"""

    def is_applicable(self, search: Optional[str] = None, **kwargs) -> bool:
        return search is not None and search.strip()

    def apply(self, query: Select, search: str, **kwargs) -> Select:
        from app.db.models.assessment import Assessment
        return query.where(
            Assessment.title.ilike(f"%{search}%") |
            Assessment.description.ilike(f"%{search}%")
        )


class CategoryFilter(FilterSpecification):
    """Filter by category"""

    def is_applicable(self, category: Optional[str] = None, **kwargs) -> bool:
        return category is not None

    def apply(self, query: Select, category: str, **kwargs) -> Select:
        from app.db.models.assessment import Assessment
        return query.where(Assessment.category == category)


class StatusFilter(FilterSpecification):
    """Filter by status"""

    def is_applicable(self, status: Optional[str] = None, **kwargs) -> bool:
        return status is not None

    def apply(self, query: Select, status: str, **kwargs) -> Select:
        from app.db.models.assessment import Assessment
        return query.where(Assessment.status == status)


class CreatedByFilter(FilterSpecification):
    """Filter by creator ID"""

    def is_applicable(self, created_by: Optional[int] = None, **kwargs) -> bool:
        return created_by is not None

    def apply(self, query: Select, created_by: int, **kwargs) -> Select:
        from app.db.models.assessment import Assessment
        return query.where(Assessment.created_by_id == created_by)


class DateRangeFilter(FilterSpecification):
    """Filter by date range (created_after, created_before)"""

    def is_applicable(
        self,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        **kwargs
    ) -> bool:
        return created_after is not None or created_before is not None

    def apply(
        self,
        query: Select,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        **kwargs
    ) -> Select:
        from app.db.models.assessment import Assessment

        if created_after:
            query = query.where(Assessment.created_at >= created_after)

        if created_before:
            query = query.where(Assessment.created_at <= created_before)

        return query


class AssessmentFilters:
    """
    Encapsulates all assessment filter parameters.

    This groups all filter parameters into a single object,
    making the endpoint signature cleaner.
    """

    def __init__(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
    ):
        self.search = search
        self.category = category
        self.status = status
        self.created_by = created_by
        self.created_after = created_after
        self.created_before = created_before

    def to_dict(self) -> dict:
        """Convert to dictionary for tracking"""
        filters = {}
        if self.search:
            filters["search"] = self.search
        if self.category:
            filters["category"] = self.category
        if self.status:
            filters["status"] = self.status
        if self.created_by:
            filters["created_by"] = self.created_by
        if self.created_after:
            filters["created_after"] = self.created_after
        if self.created_before:
            filters["created_before"] = self.created_before
        return filters


class AssessmentQueryBuilder:
    """
    Builder for filtered assessment queries.

    Uses a chain of responsibility pattern to apply filters.

    Before (repetitive code in endpoint):
    ```python
    query = select(Assessment)
    if search:
        query = query.where(Assessment.title.ilike(f"%{search}%"))
    if category:
        query = query.where(Assessment.category == category)
    if status:
        query = query.where(Assessment.status == status)
    # ... 6+ more if blocks
    ```

    After (clean and composable):
    ```python
    query = builder.build(filters=filters, user=current_user)
    ```

    Complexity reduced from 65 lines to ~15 lines.
    """

    # Default filter chain - applied in order
    DEFAULT_FILTERS = [
        SearchFilter(),
        CategoryFilter(),
        StatusFilter(),
        CreatedByFilter(),
        DateRangeFilter(),
    ]

    def __init__(self, filters: Optional[list[FilterSpecification]] = None):
        """
        Initialize query builder.

        Args:
            filters: Custom filter chain (defaults to DEFAULT_FILTERS)
        """
        self.filters = filters or self.DEFAULT_FILTERS

    def build(
        self,
        user: "User",
        filters: Optional[AssessmentFilters] = None,
        eager_load: bool = True
    ) -> Select:
        """
        Build a filtered query for assessments.

        Args:
            user: Current user for access control
            filters: Filter parameters
            eager_load: Whether to eager load sections

        Returns:
            Select query with all applicable filters applied
        """
        from app.db.models.assessment import Assessment

        # Start with base query
        query = select(Assessment)

        # Eager load sections if requested
        if eager_load:
            query = query.options(selectinload(Assessment.sections))

        # Apply access control (user can only see their own or public assessments)
        query = query.where(
            (Assessment.created_by_id == user.id) | (Assessment.is_public == True)
        )

        # Apply filter chain
        if filters:
            filter_kwargs = {
                "search": filters.search,
                "category": filters.category,
                "status": filters.status,
                "created_by": filters.created_by,
                "created_after": filters.created_after,
                "created_before": filters.created_before,
            }

            for filter_spec in self.filters:
                if filter_spec.is_applicable(**filter_kwargs):
                    query = filter_spec.apply(query, **filter_kwargs)

        return query

    def build_with_custom_filters(
        self,
        user: "User",
        custom_filters: list[FilterSpecification],
        **filter_kwargs
    ) -> Select:
        """
        Build query with custom filter chain.

        Useful for specialized queries that need non-standard filters.

        Args:
            user: Current user
            custom_filters: List of filter specifications
            **filter_kwargs: Filter parameters

        Returns:
            Select query with custom filters applied
        """
        from app.db.models.assessment import Assessment

        query = select(Assessment).options(selectinload(Assessment.sections))
        query = query.where(
            (Assessment.created_by_id == user.id) | (Assessment.is_public == True)
        )

        for filter_spec in custom_filters:
            if filter_spec.is_applicable(**filter_kwargs):
                query = filter_spec.apply(query, **filter_kwargs)

        return query
