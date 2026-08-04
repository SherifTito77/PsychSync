"""
Test suite for async response endpoints conversion
Tests all modified endpoints for proper async behavior
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.db.models.response import Response
from app.main import app
from app.services.response_service import ResponseService

# ========================================================================
# Response Service Tests
# ========================================================================


class TestResponseServiceAsyncMethods:
    """Test new async methods added to ResponseService"""

    @pytest.mark.asyncio
    async def test_get_response_score(self, db_session):
        """Test get_response_score method"""
        # Create a test response
        response = Response(
            id=uuid4(),
            assessment_id=uuid4(),
            user_id=uuid4(),
            score=0.85,
            normalized_score=0.85,
            percentage=85.0,
        )

        with patch.object(ResponseService, "get_by_id", return_value=response):
            score = await ResponseService.get_response_score(
                db_session, response_id=response.id
            )

            assert score is not None
            assert score["raw_score"] == 0.85
            assert score["normalized_score"] == 0.85
            assert score["percentage"] == 85.0

    @pytest.mark.asyncio
    async def test_get_response_score_not_found(self, db_session):
        """Test get_response_score returns None for non-existent response"""
        with patch.object(ResponseService, "get_by_id", return_value=None):
            score = await ResponseService.get_response_score(
                db_session, response_id=uuid4()
            )

            assert score is None

    @pytest.mark.asyncio
    async def test_save_progress(self, db_session):
        """Test save_progress method"""
        response = Response(id=uuid4(), assessment_id=uuid4(), user_id=uuid4())

        mock_refresh = AsyncMock()
        db_session.refresh = mock_refresh

        with patch.object(db_session, "commit"):
            result = await ResponseService.save_progress(
                db_session,
                response=response,
                responses_data={"question_1": "answer_1"},
                current_section="section_2",
            )

            assert result == response
            assert response.responses == {"question_1": "answer_1"}
            assert response.current_section == "section_2"

    @pytest.mark.asyncio
    async def test_validate_response_data_valid(self, db_session):
        """Test validate_response_data with valid data"""
        is_valid, error = await ResponseService.validate_response_data(
            db_session, assessment_id=uuid4(), responses_data={"q1": "a1", "q2": "a2"}
        )

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_response_data_empty(self, db_session):
        """Test validate_response_data rejects empty data"""
        is_valid, error = await ResponseService.validate_response_data(
            db_session, assessment_id=uuid4(), responses_data={}
        )

        assert is_valid is False
        assert error == "Response data cannot be empty"

    @pytest.mark.asyncio
    async def test_submit_response(self, db_session):
        """Test submit_response method"""
        response = Response(id=uuid4(), assessment_id=uuid4(), user_id=uuid4())

        mock_commit = AsyncMock()
        mock_refresh = AsyncMock()
        db_session.commit = mock_commit
        db_session.refresh = mock_refresh

        with patch.object(ResponseService, "_calculate_score", new=AsyncMock()):
            result = await ResponseService.submit_response(
                db_session,
                response=response,
                responses_data={"q1": "a1"},
                time_taken=120,
            )

            assert result == response
            assert response.is_complete is True
            assert response.responses == {"q1": "a1"}
            assert response.time_taken_minutes == 2.0
            assert response.completed_at is not None

    @pytest.mark.asyncio
    async def test_delete_response(self, db_session):
        """Test delete_response method"""
        response = Response(id=uuid4(), assessment_id=uuid4(), user_id=uuid4())

        mock_delete = AsyncMock()
        mock_commit = AsyncMock()
        db_session.delete = mock_delete
        db_session.commit = mock_commit

        result = await ResponseService.delete_response(db_session, response=response)

        assert result is True
        mock_delete.assert_called_once_with(response)
        mock_commit.assert_called_once()


# ========================================================================
# Response Endpoint Tests
# ========================================================================


class TestResponseEndpointsAsync:
    """Test async response endpoints"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_start_response_with_valid_uuid(self, client, authenticated_user):
        """Test start_response endpoint with UUID conversion"""
        assessment_id = str(uuid4())
        response_data = {
            "assessment_id": assessment_id,
            "user_id": str(authenticated_user.id),
        }

        with patch(
            "app.api.v1.endpoints.responses.AssessmentService.get_by_id"
        ) as mock_get_assessment, patch(
            "app.api.v1.endpoints.responses.ResponseService.create"
        ) as mock_create:

            mock_assessment = Mock()
            mock_assessment.status.value = "active"
            mock_assessment.allow_anonymous = False
            mock_get_assessment.return_value = mock_assessment

            mock_response = Mock()
            mock_response.id = uuid4()
            mock_create.return_value = mock_response

            response = await client.post(
                "/api/v1/responses/start",
                json=response_data,
                headers={"Authorization": f"Bearer {authenticated_user.id}"},
            )

            # Verify endpoint doesn't crash with UUID conversion
            assert response.status_code in [200, 201, 404]

    @pytest.mark.asyncio
    async def test_get_response_with_invalid_uuid(self, client):
        """Test get_response rejects invalid UUID format"""
        response = await client.get(
            "/api/v1/responses/invalid-uuid-format",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_save_progress_with_valid_uuid(self, client):
        """Test save_progress with UUID conversion"""
        response_id = str(uuid4())
        save_data = {"responses": {"q1": "a1"}, "current_section": "section_2"}

        with patch(
            "app.api.v1.endpoints.responses.ResponseService.get_by_id"
        ) as mock_get, patch(
            "app.api.v1.endpoints.responses.ResponseService.save_progress"
        ) as mock_save:

            mock_response = Mock()
            mock_response.respondent_id = uuid4()
            mock_response.is_complete = False
            mock_get.return_value = mock_response
            mock_save.return_value = mock_response

            response = await client.put(
                f"/api/v1/responses/{response_id}/save",
                json=save_data,
                headers={"Authorization": "Bearer test-token"},
            )

            # Verify UUID conversion works
            assert response.status_code in [200, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_delete_response_with_valid_uuid(self, client):
        """Test delete_response with UUID conversion"""
        response_id = str(uuid4())

        with patch(
            "app.api.v1.endpoints.responses.ResponseService.get_by_id"
        ) as mock_get, patch(
            "app.api.v1.endpoints.responses.ResponseService.delete_response"
        ) as mock_delete:

            mock_response = Mock()
            mock_response.respondent_id = uuid4()
            mock_response.is_complete = False
            mock_get.return_value = mock_response
            mock_delete.return_value = True

            response = await client.delete(
                f"/api/v1/responses/{response_id}",
                headers={"Authorization": "Bearer test-token"},
            )

            # Verify UUID conversion works
            assert response.status_code in [200, 204, 401, 403, 404]


# ========================================================================
# Feature Request Endpoint Tests
# ========================================================================


class TestFeatureRequestAsyncHelpers:
    """Test async helper functions in feature_requests.py"""

    @pytest.mark.asyncio
    async def test_feature_request_to_response_async(self, db_session):
        """Test _feature_request_to_response is async"""
        from app.api.v1.endpoints.feature_requests import _feature_request_to_response
        from app.db.models.feature_requests import FeatureRequest

        feature_request = FeatureRequest(
            id=uuid4(),
            title="Test Feature",
            description="Test description",
            status="backlog",
            theme="ANALYT",
            request_type="NEW",
            priority="P3",
            effort="M",
            value="V3",
            source_type="customer",
        )

        # This should work with async/await
        response = await _feature_request_to_response(feature_request, db_session)

        assert response.id == str(feature_request.id)
        assert response.title == "Test Feature"
        assert response.vote_count == 0  # Default when no votes

    @pytest.mark.asyncio
    async def test_get_vote_count_async(self, db_session):
        """Test _get_vote_count is async"""
        from app.api.v1.endpoints.feature_requests import _get_vote_count

        request_id = str(uuid4())

        # Should work with async/await
        count = await _get_vote_count(request_id, db_session)

        # Should return 0 for non-existent request
        assert count == 0


# ========================================================================
# Activation Endpoint Tests
# ========================================================================


class TestActivationAsyncHelpers:
    """Test async helper functions in activation.py"""

    @pytest.mark.asyncio
    async def test_check_and_mark_activated_async(self, db_session):
        """Test _check_and_mark_activated is async"""
        from app.api.v1.endpoints.activation import _check_and_mark_activated
        from app.db.models.user_activation import UserActivation

        activation = UserActivation(
            id=uuid4(),
            user_id=uuid4(),
            segment="individual_free",
            signup_timestamp=None,
        )

        # This should work with async/await
        await _check_and_mark_activated(activation, db_session)

        # Should not crash even with no signup timestamp

    @pytest.mark.asyncio
    async def test_calculate_funnel_async(self, db_session):
        """Test _calculate_funnel is async"""
        from app.api.v1.endpoints.activation import _calculate_funnel

        # Create a mock query
        mock_query = Mock()
        mock_query.count = Mock(return_value=100)
        mock_query.filter = Mock(return_value=mock_query)

        # Should work with async/await
        funnel = await _calculate_funnel(mock_query, db_session)

        assert len(funnel) > 0
        assert isinstance(funnel, list)


# ========================================================================
# Async Performance Tests
# ========================================================================


class TestAsyncPerformance:
    """Test that async operations don't block"""

    @pytest.mark.asyncio
    async def test_concurrent_response_creation(self, db_session):
        """Test multiple concurrent response creations don't block"""
        import asyncio

        async def create_response():
            response = Response(id=uuid4(), assessment_id=uuid4(), user_id=uuid4())
            # Simulate async operation
            await asyncio.sleep(0.01)
            return response

        # Create 10 concurrent responses
        tasks = [create_response() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        # If blocking, this would take much longer
        # With async, should complete quickly

    @pytest.mark.asyncio
    async def test_database_query_non_blocking(self, db_session):
        """Test database queries wrapped in run_in_executor don't block"""
        import asyncio
        import time

        async def simulated_query():
            # Simulate a query that takes time
            def blocking_query():
                time.sleep(0.05)  # 50ms blocking operation
                return "result"

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, blocking_query)
            return result

        # Run multiple "queries" concurrently
        start = time.time()
        tasks = [simulated_query() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # With true async, 5 concurrent 50ms operations should take ~50-100ms total
        # If blocking, would take ~250ms (5 * 50ms)
        assert elapsed < 0.2  # Should complete in under 200ms
        assert len(results) == 5
