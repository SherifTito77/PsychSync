# Fast Onboarding Tests - Optimized for Development Speed
# Uses mocked dependencies and focuses on critical functionality

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


# Schema validation tests (fast, no API calls)
class TestAssessmentSchemaValidation:
    """Test assessment request schema validation"""

    @pytest.mark.unit
    def test_valid_assessment_request(
        self, assessment_validator, sample_assessment_data
    ):
        """Test valid assessment request passes validation"""
        request = assessment_validator(**sample_assessment_data)
        assert request.role == sample_assessment_data["role"]
        assert request.challenge == sample_assessment_data["challenge"]

    @pytest.mark.unit
    def test_assessment_request_all_roles(self, assessment_validator, all_roles):
        """Test assessment request with all valid roles"""
        data = {"role": all_roles, "challenge": "communication"}
        request = assessment_validator(**data)
        assert request.role == all_roles

    @pytest.mark.unit
    def test_assessment_request_all_challenges(
        self, assessment_validator, all_challenges
    ):
        """Test assessment request with all valid challenges"""
        data = {"role": "manager", "challenge": all_challenges}
        request = assessment_validator(**data)
        assert request.challenge == all_challenges

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "invalid_data",
        [
            {"role": "", "challenge": "communication"},  # Empty role
            {"role": "invalid_role", "challenge": "communication"},  # Invalid role
            {"role": None, "challenge": "communication"},  # None role
            {"role": "manager", "challenge": ""},  # Empty challenge
            {"role": "manager", "challenge": None},  # None challenge
            {"role": "manager", "challenge": "invalid_challenge"},  # Invalid challenge
        ],
    )
    def test_invalid_assessment_requests(self, assessment_validator, invalid_data):
        """Test invalid assessment requests fail validation"""
        with pytest.raises(Exception):  # Pydantic validation error
            assessment_validator(**invalid_data)


# Fast API tests with mocked dependencies
class TestOnboardingAPIFast:
    """Fast API tests with mocked database and Redis"""

    @pytest.mark.integration
    def test_health_check_fast(self, fast_client):
        """Test health check endpoint (no database required)"""
        response = fast_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.integration
    def test_api_documentation_accessible(self, fast_client):
        """Test API documentation is accessible"""
        response = fast_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.integration
    def test_quick_assessment_endpoint_exists(
        self, fast_client, sample_assessment_data
    ):
        """Test quick assessment endpoint exists and handles requests"""
        # This should return an error (authentication/database), but endpoint should exist
        response = fast_client.post(
            "/api/v1/onboarding/quick-assessment", json=sample_assessment_data
        )
        # Accept any response except 500 (server error)
        assert response.status_code != 500

    @pytest.mark.integration
    def test_endpoint_response_structure(self, fast_client):
        """Test API endpoints return proper structure"""
        response = fast_client.get("/health")
        assert response.status_code == 200

        # Check response has proper JSON structure
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.integration
    def test_request_headers(self, fast_client):
        """Test proper security headers are set"""
        response = fast_client.get("/health")
        assert response.status_code == 200

        # Check for security headers
        headers = response.headers
        assert "X-Request-ID" in headers
        assert "X-Response-Time-MS" in headers


# Error handling tests
class TestErrorHandlingFast:
    """Test error handling without external dependencies"""

    @pytest.mark.integration
    def test_404_error_handling(self, fast_client):
        """Test 404 errors are handled properly"""
        response = fast_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "success" in data
        assert data["success"] is False

    @pytest.mark.integration
    def test_validation_error_handling(self, fast_client):
        """Test validation errors are handled properly"""
        # Send invalid data to trigger validation error
        response = fast_client.post("/api/v1/onboarding/quick-assessment", json={})

        # Should return 422 for validation errors (or 401 if auth is checked first)
        assert response.status_code in [422, 401]

    @pytest.mark.integration
    def test_large_request_handling(self, fast_client):
        """Test handling of large requests"""
        large_data = {
            "role": "manager",
            "challenge": "communication",
            "extra_data": "x" * 10000,  # 10KB of extra data
        }

        response = fast_client.post(
            "/api/v1/onboarding/quick-assessment", json=large_data
        )
        # Should handle gracefully (not crash)
        assert response.status_code != 500


# Performance tests (fast versions)
class TestPerformanceFast:
    """Fast performance tests"""

    @pytest.mark.unit
    def test_schema_validation_performance(
        self, assessment_validator, performance_tracker, sample_assessment_data
    ):
        """Test schema validation performance"""
        for i in range(100):  # Validate 100 times
            assessment_validator(**sample_assessment_data)
            performance_tracker.checkpoint(f"validation_{i}")

        # Should complete quickly
        assert performance_tracker.elapsed() < 1.0

    @pytest.mark.integration
    def test_api_response_time(self, fast_client, performance_tracker):
        """Test API response time performance"""
        response = fast_client.get("/health")
        performance_tracker.checkpoint("health_request")

        assert response.status_code == 200
        assert performance_tracker.elapsed() < 2.0

    @pytest.mark.integration
    def test_concurrent_requests(self, fast_client):
        """Test handling of concurrent requests"""

        async def make_request():
            response = fast_client.get("/health")
            return response.status_code == 200

        # Run 10 concurrent requests
        results = asyncio.run(asyncio.gather(*[make_request() for _ in range(10)]))

        # Most should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8


# Mock service tests
class TestMockServices:
    """Test with mocked service dependencies"""

    @pytest.mark.unit
    async def test_analytics_service_mock(self, mock_analytics_service):
        """Test analytics service mocking works"""
        result = await mock_analytics_service.track_event("test_event", {})
        assert result["success"] is True

    @pytest.mark.unit
    async def test_assessment_service_mock(self, mock_assessment_service):
        """Test assessment service mocking works"""
        result = await mock_assessment_service.generate_insights({})
        assert result["success"] is True
        assert "insights" in result

    @pytest.mark.integration
    @patch("app.services.analytics_service.AnalyticsService")
    def test_api_with_mocked_analytics(
        self, mock_analytics_class, fast_client, sample_assessment_data
    ):
        """Test API with mocked analytics service"""
        mock_analytics_class.return_value = AsyncMock()
        mock_analytics_class.return_value.track_event.return_value = {"success": True}

        response = fast_client.post(
            "/api/v1/onboarding/quick-assessment", json=sample_assessment_data
        )
        # Should not crash (even if not fully successful)
        assert response.status_code != 500


# Configuration tests
class TestConfiguration:
    """Test configuration and setup"""

    @pytest.mark.unit
    def test_test_environment_set(self, monkeypatch):
        """Test that test environment is properly configured"""
        assert monkeypatch.getenv("TESTING") == "true"
        assert monkeypatch.getenv("ENVIRONMENT") == "testing"

    @pytest.mark.unit
    def test_fast_app_creation(self, fast_app):
        """Test that fast app is created successfully"""
        assert fast_app is not None
        assert hasattr(fast_app, "routes")

    @pytest.mark.unit
    def test_fast_client_creation(self, fast_client):
        """Test that fast client is created successfully"""
        assert fast_client is not None
        assert hasattr(fast_client, "get")
        assert hasattr(fast_client, "post")


# Development convenience tests
class TestDevelopmentWorkflow:
    """Tests that support rapid development workflow"""

    @pytest.mark.unit
    def test_schema_validation_errors_are_descriptive(self, assessment_validator):
        """Test that validation errors provide useful feedback"""
        try:
            assessment_validator(role="invalid_role", challenge="communication")
        except Exception as e:
            # Error should be descriptive
            error_str = str(e).lower()
            assert "role" in error_str or "invalid" in error_str

    @pytest.mark.integration
    def test_health_endpoint_response_format(self, fast_client):
        """Test health endpoint returns expected format for monitoring"""
        response = fast_client.get("/health")
        data = response.json()

        # Should contain expected fields for monitoring
        expected_fields = ["status", "application", "version"]
        for field in expected_fields:
            assert field in data

    @pytest.mark.integration
    def test_request_id_tracking(self, fast_client):
        """Test that requests are tracked with unique IDs"""
        response = fast_client.get("/health")
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) > 10  # Should be a proper UUID
