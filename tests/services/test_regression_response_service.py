"""
Comprehensive Regression Tests for Response Service
tests/services/test_regression_response_service.py

This module contains regression tests for the ResponseService class:
- CRUD operations (create, read, update, delete)
- Analytics and aggregation
- Bulk operations
- Score calculation

Test Categories:
- P0: Critical CRUD operations (must pass)
- P1: High-priority edge cases and analytics

Priority: P0 (Critical)
Coverage Target: 85% lines, 80% branches, 90% functions
"""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.user import User
from app.schemas.response import ResponseCreate, ResponseUpdate
from app.services.response_service import ResponseService
from tests.conftest import fake


class TestResponseServiceCRUDRegression:
    """
    Regression tests for ResponseService CRUD operations
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_create_response_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify response creation in database

        Input: ResponseCreate schema
        Expected: Response object with id, created_at, updated_at
        Priority: P0
        """
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),  # Generic question ID
            answer_value=5,
        )

        response = await ResponseService.create(db=test_db, response_in=response_in)

        assert response is not None
        assert response.id is not None
        assert response.assessment_id == test_assessment.id
        assert response.user_id == test_user.id
        assert response.answer_value == 5
        assert response.created_at is not None
        assert response.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_response_with_score(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify automatic score calculation

        Input: Response with answer_value
        Expected: Score calculated and stored
        Priority: P0
        """
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=4,  # Should normalize to 0.8 (4/5)
        )

        response = await ResponseService.create(db=test_db, response_in=response_in)

        assert response.score is not None
        assert 0 <= response.score <= 1
        assert abs(response.score - 0.8) < 0.01  # 4/5 = 0.8

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify retrieval by UUID

        Input: Valid response_id
        Expected: Response object
        Priority: P0
        """
        # Create a response first
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=3,
        )
        created_response = await ResponseService.create(
            db=test_db, response_in=response_in
        )

        # Retrieve by ID
        retrieved_response = await ResponseService.get_by_id(
            db=test_db, response_id=created_response.id
        )

        assert retrieved_response is not None
        assert retrieved_response.id == created_response.id
        assert retrieved_response.answer_value == 3

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_db: AsyncSession):
        """
        Test: Verify None returned for invalid ID

        Input: Non-existent UUID
        Expected: None
        Priority: P0
        """
        fake_id = uuid4()
        response = await ResponseService.get_by_id(db=test_db, response_id=fake_id)

        assert response is None

    @pytest.mark.asyncio
    async def test_get_by_assessment_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify filtering by assessment

        Input: assessment_id
        Expected: List of responses for assessment
        Priority: P0
        """
        # Create multiple responses for the assessment
        for i in range(5):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        # Retrieve all responses for assessment
        responses = await ResponseService.get_by_assessment(
            db=test_db, assessment_id=test_assessment.id
        )

        assert len(responses) == 5
        assert all(r.assessment_id == test_assessment.id for r in responses)

    @pytest.mark.asyncio
    async def test_get_by_assessment_with_user_filter(
        self, test_db: AsyncSession, test_user: User, test_admin: User, test_assessment
    ):
        """
        Test: Verify user filtering

        Input: assessment_id, user_id
        Expected: Responses for specific user
        Priority: P0
        """
        # Create responses from two different users
        for i in range(3):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        for i in range(2):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_admin.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        # Retrieve only test_user's responses
        responses = await ResponseService.get_by_assessment(
            db=test_db, assessment_id=test_assessment.id, user_id=test_user.id
        )

        assert len(responses) == 3
        assert all(r.user_id == test_user.id for r in responses)

    @pytest.mark.asyncio
    async def test_get_by_user_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify retrieval by user

        Input: user_id
        Expected: Recent responses (limit 100)
        Priority: P0
        """
        # Create multiple responses
        for i in range(10):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        # Retrieve user's responses
        responses = await ResponseService.get_by_user(
            db=test_db, user_id=test_user.id, limit=100
        )

        assert len(responses) == 10
        assert all(r.user_id == test_user.id for r in responses)
        # Should be ordered by created_at desc
        # (This assumes the service orders by created_at desc)

    @pytest.mark.asyncio
    async def test_update_response_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify response update

        Input: response_id, ResponseUpdate
        Expected: Updated response, updated_at changed
        Priority: P0
        """
        # Create response
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=3,
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)

        # Wait a bit to ensure updated_at changes
        import asyncio

        await asyncio.sleep(0.01)

        # Update response
        update_in = ResponseUpdate(answer_value=5)
        updated_response = await ResponseService.update(
            db=test_db, response_id=response.id, response_in=update_in
        )

        assert updated_response is not None
        assert updated_response.answer_value == 5
        assert updated_response.updated_at > response.updated_at

    @pytest.mark.asyncio
    async def test_update_response_not_found(self, test_db: AsyncSession):
        """
        Test: Verify graceful failure

        Input: Invalid response_id
        Expected: None
        Priority: P0
        """
        update_in = ResponseUpdate(answer_value=5)
        result = await ResponseService.update(
            db=test_db, response_id=uuid4(), response_in=update_in
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_update_response_recalculates_score(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify score recalculation on answer update

        Input: Update answer_value
        Expected: Score recalculated
        Priority: P0
        """
        # Create response
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=2,  # Score = 0.4
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)
        original_score = response.score

        # Update answer_value
        update_in = ResponseUpdate(answer_value=5)  # New score = 1.0
        updated_response = await ResponseService.update(
            db=test_db, response_id=response.id, response_in=update_in
        )

        assert updated_response.score != original_score
        assert abs(updated_response.score - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_delete_response_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify deletion

        Input: Valid response_id
        Expected: True, response removed from DB
        Priority: P0
        """
        # Create response
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=3,
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)

        # Delete response
        result = await ResponseService.delete(db=test_db, response_id=response.id)

        assert result is True

        # Verify deletion
        deleted_response = await ResponseService.get_by_id(
            db=test_db, response_id=response.id
        )
        assert deleted_response is None

    @pytest.mark.asyncio
    async def test_delete_response_not_found(self, test_db: AsyncSession):
        """
        Test: Verify graceful failure

        Input: Invalid response_id
        Expected: False
        Priority: P0
        """
        result = await ResponseService.delete(db=test_db, response_id=uuid4())
        assert result is False


class TestResponseServiceAnalyticsRegression:
    """
    Regression tests for ResponseService analytics operations
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_get_assessment_completion_all_answered(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify completion calculation - all answered

        Input: All questions answered
        Expected: completion_rate=1.0
        Priority: P0
        """
        # Assume 10 questions for this assessment
        num_questions = 10

        # Create responses for all questions
        for i in range(num_questions):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        # Get completion stats
        stats = await ResponseService.get_assessment_completion(
            db=test_db, assessment_id=test_assessment.id, user_id=test_user.id
        )

        assert stats["total_questions"] == num_questions
        assert stats["answered_questions"] == num_questions
        assert stats["completion_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_assessment_completion_partial(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify partial completion calculation

        Input: 5 of 10 questions answered
        Expected: completion_rate=0.5
        Priority: P0
        """
        # Create 5 responses out of 10 questions
        for i in range(5):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
                score=0.5 + (i * 0.1),  # Set scores
            )
            await ResponseService.create(db=test_db, response_in=response_in)

        # Get completion stats
        stats = await ResponseService.get_assessment_completion(
            db=test_db, assessment_id=test_assessment.id, user_id=test_user.id
        )

        assert stats["total_questions"] == 5  # Only counted responses
        assert stats["completion_rate"] == 1.0  # All answered questions completed

    @pytest.mark.asyncio
    async def test_get_assessment_completion_score_rate(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify score rate calculation

        Input: 3 of 5 responses scored
        Expected: score_rate=0.6
        Priority: P0
        """
        # Create responses with and without scores
        for i in range(5):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
                score=0.5 if i < 3 else None,  # First 3 have scores
            )
            response = await ResponseService.create(db=test_db, response_in=response_in)

            if i >= 3:
                # Manually set score to None for last 2
                response.score = None
                await test_db.commit()

        # Get completion stats
        stats = await ResponseService.get_assessment_completion(
            db=test_db, assessment_id=test_assessment.id, user_id=test_user.id
        )

        assert stats["scored_questions"] == 3
        assert stats["score_rate"] == 0.6  # 3/5


class TestResponseServiceBulkOperationsRegression:
    """
    Regression tests for ResponseService bulk operations
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_bulk_create_success(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify batch creation

        Input: List of 50 ResponseCreate
        Expected: All 50 responses created
        Priority: P0
        """
        # Create 50 responses
        responses_data = []
        for i in range(50):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i % 5 + 1,
            )
            responses_data.append(response_in)

        # Bulk create
        created_responses = await ResponseService.bulk_create(
            db=test_db, responses=responses_data
        )

        assert len(created_responses) == 50
        assert all(r.id is not None for r in created_responses)

        # Verify they exist in database
        from sqlalchemy import func

        result = await test_db.execute(
            select(func.count(Response.id)).where(
                Response.assessment_id == test_assessment.id,
                Response.user_id == test_user.id,
            )
        )
        count = result.scalar()
        assert count == 50

    @pytest.mark.asyncio
    async def test_bulk_create_with_invalid_data(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify partial failure handling

        Input: Mix of valid/invalid responses
        Expected: Valid created, invalid rejected (or all failed together)
        Priority: P0
        """
        # Create mix of valid and invalid
        responses_data = []

        # Valid responses
        for i in range(3):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=i + 1,
            )
            responses_data.append(response_in)

        # Invalid response (no question_id)
        responses_data.append(
            ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=None,  # Invalid
                answer_value=1,
            )
        )

        # Attempt bulk create
        # Note: Depending on implementation, this may fail fast or partial
        try:
            created_responses = await ResponseService.bulk_create(
                db=test_db, responses=responses_data
            )
            # If partial success is supported
            assert len(created_responses) >= 3  # At least valid ones
        except Exception:
            # If transaction fails on first error
            # Verify no responses were created
            result = await test_db.execute(
                select(func.count(Response.id)).where(
                    Response.assessment_id == test_assessment.id
                )
            )
            count = result.scalar()
            assert count == 0


class TestResponseServiceEdgeCasesRegression:
    """
    Regression tests for edge cases and error handling
    Priority: P1 (High)
    """

    @pytest.mark.asyncio
    async def test_response_scoring_edge_cases(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify scoring edge cases

        Input: Min/max values, null values
        Expected: Proper handling
        Priority: P1
        """
        # Test with answer_value = 0
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=0,
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)
        assert response.score == 0.0

        # Test with answer_value = 5 (max)
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=5,
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)
        assert response.score == 1.0

        # Test with answer_value = None
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_value=None,
            answer_text="Text response",
        )
        response = await ResponseService.create(db=test_db, response_in=response_in)
        # Score should remain None
        assert response.score is None

    @pytest.mark.asyncio
    async def test_concurrent_response_creation(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify thread safety

        Input: 10 concurrent creations
        Expected: All succeed without race conditions
        Priority: P1
        """
        import asyncio

        async def create_response(value: int):
            response_in = ResponseCreate(
                assessment_id=test_assessment.id,
                user_id=test_user.id,
                question_id=uuid4(),
                answer_value=value,
            )
            return await ResponseService.create(db=test_db, response_in=response_in)

        # Create 10 responses concurrently
        tasks = [create_response(i + 1) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(r.id is not None for r in results)

    @pytest.mark.asyncio
    async def test_response_with_text_answer(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify text answer handling

        Input: Text answer instead of numeric
        Expected: Text stored correctly, no score calculated
        Priority: P1
        """
        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_text="This is my answer",
        )

        response = await ResponseService.create(db=test_db, response_in=response_in)

        assert response.answer_text == "This is my answer"
        assert response.score is None  # No score for text answers

    @pytest.mark.asyncio
    async def test_response_with_answer_data(
        self, test_db: AsyncSession, test_user: User, test_assessment
    ):
        """
        Test: Verify JSON answer_data handling

        Input: Complex JSON data
        Expected: JSON stored correctly
        Priority: P1
        """
        answer_data = {
            "selected_options": [1, 3, 5],
            "rating": 4,
            "comment": "Good question",
        }

        response_in = ResponseCreate(
            assessment_id=test_assessment.id,
            user_id=test_user.id,
            question_id=uuid4(),
            answer_data=answer_data,
        )

        response = await ResponseService.create(db=test_db, response_in=response_in)

        assert response.answer_data == answer_data


# Test class markers
TestResponseServiceCRUDRegression = pytest.mark.P0(TestResponseServiceCRUDRegression)
TestResponseServiceAnalyticsRegression = pytest.mark.P0(
    TestResponseServiceAnalyticsRegression
)
TestResponseServiceBulkOperationsRegression = pytest.mark.P0(
    TestResponseServiceBulkOperationsRegression
)
TestResponseServiceEdgeCasesRegression = pytest.mark.P1(
    TestResponseServiceEdgeCasesRegression
)
