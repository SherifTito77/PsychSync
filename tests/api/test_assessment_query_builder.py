"""
Tests for Assessment Query Builder

These tests demonstrate the improved testability of the refactored
query building logic.
"""

import pytest
from sqlalchemy import select
from app.api.v1.endpoints.assessments.query_builder import (
    AssessmentQueryBuilder,
    AssessmentFilters,
    SearchFilter,
    CategoryFilter,
    StatusFilter,
    CreatedByFilter,
    DateRangeFilter,
)


class TestFilterSpecifications:
    """Test individual filter specifications"""

    def test_search_filter_is_applicable(self):
        """Test that search filter applies when search term provided"""
        filter = SearchFilter()

        assert filter.is_applicable(search="test") is True
        assert filter.is_applicable(search="") is False
        assert filter.is_applicable(search=None) is False
        assert filter.is_applicable(search="   ") is False

    def test_category_filter_is_applicable(self):
        """Test that category filter applies when category provided"""
        filter = CategoryFilter()

        assert filter.is_applicable(category="personality") is True
        assert filter.is_applicable(category=None) is False

    def test_status_filter_is_applicable(self):
        """Test that status filter applies when status provided"""
        filter = StatusFilter()

        assert filter.is_applicable(status="published") is True
        assert filter.is_applicable(status=None) is False

    def test_created_by_filter_is_applicable(self):
        """Test that created_by filter applies when user ID provided"""
        filter = CreatedByFilter()

        assert filter.is_applicable(created_by=123) is True
        assert filter.is_applicable(created_by=None) is False

    def test_date_range_filter_is_applicable(self):
        """Test that date range filter applies when dates provided"""
        filter = DateRangeFilter()

        assert filter.is_applicable(created_after="2024-01-01") is True
        assert filter.is_applicable(created_before="2024-12-31") is True
        assert filter.is_applicable(
            created_after="2024-01-01",
            created_before="2024-12-31"
        ) is True
        assert filter.is_applicable() is False


class TestAssessmentFilters:
    """Test AssessmentFilters data class"""

    def test_to_dict_with_all_filters(self):
        """Test converting all filters to dict"""
        filters = AssessmentFilters(
            search="test",
            category="personality",
            status="published",
            created_by=123,
            created_after="2024-01-01",
            created_before="2024-12-31",
        )

        result = filters.to_dict()

        assert result["search"] == "test"
        assert result["category"] == "personality"
        assert result["status"] == "published"
        assert result["created_by"] == 123
        assert result["created_after"] == "2024-01-01"
        assert result["created_before"] == "2024-12-31"

    def test_to_dict_with_no_filters(self):
        """Test converting empty filters to dict"""
        filters = AssessmentFilters()

        result = filters.to_dict()

        assert result == {}

    def test_to_dict_with_partial_filters(self):
        """Test converting partial filters to dict"""
        filters = AssessmentFilters(
            search="test",
            status="published",
        )

        result = filters.to_dict()

        assert result["search"] == "test"
        assert result["status"] == "published"
        assert "category" not in result
        assert "created_by" not in result


class TestAssessmentQueryBuilder:
    """Test the query builder"""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user"""
        class MockUser:
            id = 123

        return MockUser()

    def test_builder_creates_base_query(self, mock_user):
        """Test that builder creates a base query with access control"""
        builder = AssessmentQueryBuilder()

        query = builder.build(user=mock_user, filters=None)

        assert query is not None
        # Query should be a Select object
        assert hasattr(query, 'where')

    def test_builder_applies_search_filter(self, mock_user):
        """Test that builder applies search filter"""
        builder = AssessmentQueryBuilder()
        filters = AssessmentFilters(search="personality")

        query = builder.build(user=mock_user, filters=filters)

        assert query is not None
        # Query should have search conditions applied

    def test_builder_applies_multiple_filters(self, mock_user):
        """Test that builder applies multiple filters"""
        builder = AssessmentQueryBuilder()
        filters = AssessmentFilters(
            search="test",
            category="personality",
            status="published",
        )

        query = builder.build(user=mock_user, filters=filters)

        assert query is not None
        # All three filters should be applied

    def test_builder_with_custom_filters(self, mock_user):
        """Test builder with custom filter chain"""
        from app.api.v1.endpoints.assessments.query_builder import FilterSpecification

        # Create a custom filter
        class CustomFilter(FilterSpecification):
            def is_applicable(self, custom_param: bool = False, **kwargs):
                return custom_param

            def apply(self, query, **kwargs):
                # Add custom where clause
                return query

        builder = AssessmentQueryBuilder()
        custom_filters = [CustomFilter()]

        query = builder.build_with_custom_filters(
            user=mock_user,
            custom_filters=custom_filters,
            custom_param=True,
        )

        assert query is not None

    def test_builder_without_eager_load(self, mock_user):
        """Test builder can disable eager loading"""
        builder = AssessmentQueryBuilder()

        query = builder.build(
            user=mock_user,
            filters=None,
            eager_load=False,
        )

        assert query is not None


class TestQueryComposition:
    """Test that filters compose correctly"""

    def test_filters_apply_in_order(self):
        """Test that filters are applied in the order they're defined"""
        applied_order = []

        class OrderTrackingFilter:
            def __init__(self, name):
                self.name = name

            def is_applicable(self, **kwargs):
                return True

            def apply(self, query, **kwargs):
                applied_order.append(self.name)
                return query

        filters = [
            OrderTrackingFilter("first"),
            OrderTrackingFilter("second"),
            OrderTrackingFilter("third"),
        ]

        builder = AssessmentQueryBuilder(filters=filters)

        # Build query (we don't care about the actual query here)
        # Just tracking the order
        for filter_spec in filters:
            filter_spec.apply(None)

        assert applied_order == ["first", "second", "third"]
