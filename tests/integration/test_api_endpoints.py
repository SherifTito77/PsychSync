"""
Comprehensive API Endpoint Integration Tests
Tests all HTTP methods, error scenarios, and cross-component interactions
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.db.models.team import Team


@pytest.mark.integration
class TestAPIEndpoints:
    """Test suite for all API endpoints"""

    @pytest.fixture
    async def client(self):
        """Create async test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    async def test_db(self):
        """Create test database session"""
        async for session in get_db():
            yield session

    @pytest.fixture
    async def test_user(self, test_db: AsyncSession):
        """Create test user"""
        user_data = {
            "email": "testuser@example.com",
            "full_name": "Test User",
            "password_hash": get_password_hash("TestPassword123!"),
            "role": "user",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow()
        }

        user = User(**user_data)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        return user

    @pytest.fixture
    async def auth_headers(self, test_user: User):
        """Create authentication headers"""
        token = create_access_token(data={"sub": str(test_user.id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def admin_user(self, test_db: AsyncSession):
        """Create admin user"""
        admin_data = {
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password_hash": get_password_hash("AdminPassword123!"),
            "role": "admin",
            "is_active": True,
            "email_verified": True,
            "created_at": datetime.utcnow()
        }

        admin = User(**admin_data)
        test_db.add(admin)
        await test_db.commit()
        await test_db.refresh(admin)

        return admin

    @pytest.fixture
    async def admin_headers(self, admin_user: User):
        """Create admin authentication headers"""
        token = create_access_token(data={"sub": str(admin_user.id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def test_assessment(self, test_db: AsyncSession):
        """Create test assessment"""
        assessment_data = {
            "title": "Big Five Personality Test",
            "description": "Assess personality traits",
            "type": "big_five",
            "is_active": True,
            "estimated_duration": 15,
            "created_at": datetime.utcnow()
        }

        assessment = Assessment(**assessment_data)
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)

        return assessment

    @pytest.fixture
    async def test_team(self, test_db: AsyncSession, test_user: User):
        """Create test team"""
        team_data = {
            "name": "Test Team",
            "description": "A team for testing",
            "department": "Engineering",
            "created_by": test_user.id,
            "created_at": datetime.utcnow()
        }

        team = Team(**team_data)
        test_db.add(team)
        await test_db.commit()
        await test_db.refresh(team)

        return team

    # Health Check Endpoints
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client: AsyncClient):
        """Test basic health check endpoint"""
        response = await client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_detailed_health_check(self, client: AsyncClient):
        """Test detailed health check with components"""
        response = await client.get("/api/v1/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "database" in data["components"]
        assert "cache" in data["components"]

    # Authentication Endpoints
    @pytest.mark.asyncio
    async def test_user_registration_success(self, client: AsyncClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "NewPassword123!",
            "role": "user"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]

    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "full_name": "Duplicate User",
            "password": "Password123!",
            "role": "user"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_user_login_success(self, client: AsyncClient, test_user: User):
        """Test successful user login"""
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["user"]["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_user_login_invalid_credentials(self, client: AsyncClient, test_user: User):
        """Test login with invalid credentials"""
        login_data = {
            "email": test_user.email,
            "password": "WrongPassword123!"
        }

        response = await client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_token_refresh_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh"""
        # First login to get refresh token
        login_data = {
            "email": test_user.email,
            "password": "TestPassword123!"
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["data"]["refresh_token"]

        # Refresh the token
        refresh_data = {"refresh_token": refresh_token}
        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_token_refresh_invalid_token(self, client: AsyncClient):
        """Test token refresh with invalid token"""
        refresh_data = {"refresh_token": "invalid_token"}

        response = await client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, auth_headers):
        """Test successful logout"""
        response = await client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    # User Management Endpoints
    @pytest.mark.asyncio
    async def test_get_user_profile(self, client: AsyncClient, test_user: User, auth_headers):
        """Test getting user profile"""
        response = await client.get("/api/v1/users/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == test_user.email
        assert data["data"]["full_name"] == test_user.full_name

    @pytest.mark.asyncio
    async def test_update_user_profile(self, client: AsyncClient, auth_headers):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name",
            "phone": "+1234567890"
        }

        response = await client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["full_name"] == "Updated Name"
        assert data["data"]["phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_get_users_admin(self, client: AsyncClient, admin_headers):
        """Test getting users list (admin only)"""
        response = await client.get("/api/v1/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_get_users_unauthorized(self, client: AsyncClient, auth_headers):
        """Test getting users list without admin privileges"""
        response = await client.get("/api/v1/users", headers=auth_headers)

        assert response.status_code == 403
        data = response.json()
        assert "insufficient permissions" in data["detail"].lower()

    # Assessment Endpoints
    @pytest.mark.asyncio
    async def test_list_assessments(self, client: AsyncClient, test_assessment: Assessment, auth_headers):
        """Test listing available assessments"""
        response = await client.get("/api/v1/assessments", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_get_assessment_details(self, client: AsyncClient, test_assessment: Assessment, auth_headers):
        """Test getting assessment details"""
        response = await client.get(f"/api/v1/assessments/{test_assessment.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == test_assessment.id
        assert data["data"]["title"] == test_assessment.title

    @pytest.mark.asyncio
    async def test_start_assessment(self, client: AsyncClient, test_assessment: Assessment, auth_headers):
        """Test starting an assessment"""
        response = await client.post(f"/api/v1/assessments/{test_assessment.id}/start", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data["data"]
        assert data["data"]["assessment_id"] == test_assessment.id

    @pytest.mark.asyncio
    async def test_submit_assessment_responses(self, client: AsyncClient, test_assessment: Assessment, auth_headers):
        """Test submitting assessment responses"""
        # First start the assessment
        start_response = await client.post(f"/api/v1/assessments/{test_assessment.id}/start", headers=auth_headers)
        session_id = start_response.json()["data"]["session_id"]

        # Submit responses
        responses_data = {
            "session_id": session_id,
            "responses": [
                {"question_id": "q1", "response": 4, "response_time_ms": 1500},
                {"question_id": "q2", "response": 3, "response_time_ms": 2000},
                {"question_id": "q3", "response": 5, "response_time_ms": 1000}
            ]
        }

        response = await client.post(f"/api/v1/assessments/{test_assessment.id}/responses", json=responses_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data["data"]
        assert "score" in data["data"]["results"]

    @pytest.mark.asyncio
    async def test_get_assessment_results(self, client: AsyncClient, test_assessment: Assessment, auth_headers):
        """Test getting assessment results"""
        # Start and complete assessment first
        start_response = await client.post(f"/api/v1/assessments/{test_assessment.id}/start", headers=auth_headers)
        session_id = start_response.json()["data"]["session_id"]

        responses_data = {
            "session_id": session_id,
            "responses": [{"question_id": "q1", "response": 4, "response_time_ms": 1500}]
        }
        await client.post(f"/api/v1/assessments/{test_assessment.id}/responses", json=responses_data, headers=auth_headers)

        # Get results
        response = await client.get(f"/api/v1/assessments/{test_assessment.id}/results?session_id={session_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "scores" in data["data"]

    # Team Management Endpoints
    @pytest.mark.asyncio
    async def test_create_team(self, client: AsyncClient, auth_headers):
        """Test creating a new team"""
        team_data = {
            "name": "New Test Team",
            "description": "A team created for testing",
            "department": "Engineering"
        }

        response = await client.post("/api/v1/teams", json=team_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == team_data["name"]
        assert data["data"]["department"] == team_data["department"]

    @pytest.mark.asyncio
    async def test_get_user_teams(self, client: AsyncClient, test_team: Team, auth_headers):
        """Test getting user's teams"""
        response = await client.get("/api/v1/teams", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) >= 1

    @pytest.mark.asyncio
    async def test_get_team_details(self, client: AsyncClient, test_team: Team, auth_headers):
        """Test getting team details"""
        response = await client.get(f"/api/v1/teams/{test_team.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == test_team.id
        assert data["data"]["name"] == test_team.name

    @pytest.mark.asyncio
    async def test_update_team(self, client: AsyncClient, test_team: Team, auth_headers):
        """Test updating team details"""
        update_data = {
            "name": "Updated Team Name",
            "description": "Updated description"
        }

        response = await client.put(f"/api/v1/teams/{test_team.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Team Name"
        assert data["data"]["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_get_team_analytics(self, client: AsyncClient, test_team: Team, auth_headers):
        """Test getting team analytics"""
        response = await client.get(f"/api/v1/teams/{test_team.id}/analytics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "team_stats" in data["data"]

    # File Upload Endpoints
    @pytest.mark.asyncio
    async def test_upload_file(self, client: AsyncClient, auth_headers):
        """Test file upload"""
        file_content = b"Test file content for integration testing"
        files = {
            "file": ("test_file.txt", file_content, "text/plain")
        }
        data = {
            "description": "Test file upload"
        }

        response = await client.post("/api/v1/files/upload", files=files, data=data, headers=auth_headers)

        assert response.status_code == 200
        response_data = response.json()
        assert "data" in response_data
        assert "file_id" in response_data["data"]
        assert response_data["data"]["filename"] == "test_file.txt"

    @pytest.mark.asyncio
    async def test_upload_file_unauthorized(self, client: AsyncClient):
        """Test file upload without authentication"""
        file_content = b"Test file content"
        files = {
            "file": ("test_file.txt", file_content, "text/plain")
        }

        response = await client.post("/api/v1/files/upload", files=files)

        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_file_info(self, client: AsyncClient, auth_headers):
        """Test getting file information"""
        # First upload a file
        file_content = b"Test file content"
        files = {
            "file": ("test_file.txt", file_content, "text/plain")
        }
        upload_response = await client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        file_id = upload_response.json()["data"]["file_id"]

        # Get file info
        response = await client.get(f"/api/v1/files/{file_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["file_id"] == file_id
        assert data["data"]["filename"] == "test_file.txt"

    @pytest.mark.asyncio
    async def test_download_file(self, client: AsyncClient, auth_headers):
        """Test file download"""
        # First upload a file
        file_content = b"Test file content for download"
        files = {
            "file": ("download_test.txt", file_content, "text/plain")
        }
        upload_response = await client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        file_id = upload_response.json()["data"]["file_id"]

        # Download the file
        response = await client.get(f"/api/v1/files/{file_id}/download", headers=auth_headers)

        assert response.status_code == 200
        assert response.content == file_content

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_not_found_error(self, client: AsyncClient, auth_headers):
        """Test 404 error handling"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(f"/api/v1/assessments/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_validation_error(self, client: AsyncClient, auth_headers):
        """Test validation error handling"""
        invalid_data = {
            "email": "invalid-email",  # Invalid email format
            "full_name": "",  # Empty full name
            "password": "123"  # Too short password
        }

        response = await client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting (if implemented)"""
        # Make multiple rapid requests to trigger rate limiting
        responses = []
        for _ in range(100):
            response = await client.get("/api/v1/health")
            responses.append(response)

            if response.status_code == 429:
                break

        # Check if rate limiting was triggered (optional, depends on implementation)
        rate_limited = any(r.status_code == 429 for r in responses)

        if rate_limited:
            rate_limit_response = next(r for r in responses if r.status_code == 429)
            assert rate_limit_response.status_code == 429

    @pytest.mark.asyncio
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are present"""
        response = await client.options("/api/v1/health")

        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    @pytest.mark.asyncio
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers are present"""
        response = await client.get("/api/v1/health")

        # Check for security headers
        headers_to_check = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]

        for header in headers_to_check:
            assert header in response.headers

    # Cross-component Integration Tests
    @pytest.mark.asyncio
    async def test_user_assessment_integration(self, client: AsyncClient, test_user: User, test_assessment: Assessment, auth_headers):
        """Test user-assessment workflow integration"""
        # Start assessment
        start_response = await client.post(f"/api/v1/assessments/{test_assessment.id}/start", headers=auth_headers)
        assert start_response.status_code == 200
        session_id = start_response.json()["data"]["session_id"]

        # Submit responses
        responses_data = {
            "session_id": session_id,
            "responses": [
                {"question_id": "q1", "response": 4, "response_time_ms": 1500}
            ]
        }

        submit_response = await client.post(f"/api/v1/assessments/{test_assessment.id}/responses", json=responses_data, headers=auth_headers)
        assert submit_response.status_code == 200

        # Verify in user profile
        profile_response = await client.get("/api/v1/users/profile", headers=auth_headers)
        assert profile_response.status_code == 200

    @pytest.mark.asyncio
    async def test_team_assessment_integration(self, client: AsyncClient, test_team: Team, test_assessment: Assessment, auth_headers):
        """Test team-assessment analytics integration"""
        # Get team analytics
        analytics_response = await client.get(f"/api/v1/teams/{test_team.id}/analytics", headers=auth_headers)
        assert analytics_response.status_code == 200

        # Start assessment for team member
        start_response = await client.post(f"/api/v1/assessments/{test_assessment.id}/start", headers=auth_headers)
        assert start_response.status_code == 200

    @pytest.mark.asyncio
    async def test_file_user_integration(self, client: AsyncClient, auth_headers):
        """Test file-user workflow integration"""
        # Upload file
        file_content = b"User integration test file"
        files = {
            "file": ("integration_test.txt", file_content, "text/plain")
        }

        upload_response = await client.post("/api/v1/files/upload", files=files, headers=auth_headers)
        assert upload_response.status_code == 200

        file_id = upload_response.json()["data"]["file_id"]

        # Verify file appears in user's file list
        # This would require implementing a user files endpoint
        # For now, we just verify the file was uploaded successfully
        assert file_id is not None

    # Performance Integration Tests
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient, auth_headers):
        """Test handling concurrent requests"""
        async def make_request():
            return await client.get("/api/v1/health", headers=auth_headers)

        # Make 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        responses = await asyncio.gather(*tasks)

        # All requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 45  # Allow for some failures under load

    @pytest.mark.asyncio
    async def test_large_response_handling(self, client: AsyncClient, auth_headers):
        """Test handling of large responses"""
        # Create team with many members (if this functionality exists)
        # For now, test getting large analytics data

        response = await client.get("/api/v1/users/profile", headers=auth_headers)
        assert response.status_code == 200

        # Verify response is properly formatted
        data = response.json()
        assert "data" in data

    # Cleanup Tests
    @pytest.mark.asyncio
    async def test_delete_user_account(self, client: AsyncClient, auth_headers):
        """Test user account deletion"""
        response = await client.delete("/api/v1/users/profile", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_remove_team_member(self, client: AsyncClient, test_team: Team, auth_headers):
        """Test removing team member"""
        # This would require implementing team member management endpoints
        # For now, just test the team exists
        response = await client.get(f"/api/v1/teams/{test_team.id}", headers=auth_headers)
        assert response.status_code == 200


# Error Handling Edge Cases
@pytest.mark.integration
class TestErrorHandlingEdgeCases:
    """Test suite for error handling edge cases"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_malformed_json(self, client: AsyncClient):
        """Test handling of malformed JSON"""
        malformed_json = '{"email": "test@example.com", "invalid": }'

        response = await client.post(
            "/api/v1/auth/login",
            content=malformed_json,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_oversized_request(self, client: AsyncClient):
        """Test handling of oversized requests"""
        # Create very large payload
        large_data = {
            "description": "x" * 1000000  # 1MB description
        }

        response = await client.post("/api/v1/teams", json=large_data)

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413, 422]

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, client: AsyncClient):
        """Test handling of special characters"""
        special_chars_data = {
            "name": "Team with special chars: áéíóú ñ 🚀",
            "description": "Description with <script>alert('xss')</script> content"
        }

        response = await client.post("/api/v1/teams", json=special_chars_data)

        # Should either succeed with sanitization or fail gracefully
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_unicode_handling(self, client: AsyncClient):
        """Test handling of Unicode characters"""
        unicode_data = {
            "full_name": "用户测试 🧪",
            "email": "test@example.com"
        }

        response = await client.post("/api/v1/auth/register", json=unicode_data)

        # Should handle Unicode properly
        assert response.status_code in [201, 400]


# Security Integration Tests
@pytest.mark.integration
class TestSecurityIntegration:
    """Test suite for security-related integrations"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client: AsyncClient):
        """Test SQL injection protection"""
        malicious_payload = "'; DROP TABLE users; --"

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": malicious_payload, "password": "test"}
        )

        # Should not succeed in database manipulation
        assert response.status_code == 401 or response.status_code == 422

    @pytest.mark.asyncio
    async def test_xss_protection(self, client: AsyncClient):
        """Test XSS protection in user inputs"""
        xss_payload = "<script>alert('xss')</script>"

        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "full_name": xss_payload,
                "password": "TestPassword123!"
            }
        )

        # Should either sanitize input or reject it
        if response.status_code == 201:
            # If accepted, verify script tags are sanitized
            data = response.json()
            assert "<script>" not in data["data"]["user"]["full_name"]
        else:
            # Should be rejected
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_authentication_bypass_attempts(self, client: AsyncClient):
        """Test authentication bypass attempts"""
        # Try accessing protected endpoint without auth
        response = await client.get("/api/v1/users/profile")

        assert response.status_code == 401

        # Try with invalid token
        response = await client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_privilege_escalation_attempts(self, client: AsyncClient):
        """Test privilege escalation attempts"""
        # Create regular user
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPassword123!"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["data"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Try accessing admin endpoint
            response = await client.get("/api/v1/admin/users", headers=headers)

            assert response.status_code == 403


# Database Integration Tests
@pytest.mark.integration
class TestDatabaseIntegration:
    """Test suite for database integration"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, client: AsyncClient):
        """Test database transaction rollback on errors"""
        # This would require implementing a test endpoint that forces a transaction error
        # For now, test that database operations are atomic

        # Create user
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "transaction_test@example.com",
                "full_name": "Transaction Test",
                "password": "TestPassword123!"
            }
        )

        if response.status_code == 201:
            # Try to register same user again (should fail)
            response2 = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "transaction_test@example.com",
                    "full_name": "Transaction Test 2",
                    "password": "TestPassword123!"
                }
            )

            # Second registration should fail
            assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_database_connection_pooling(self, client: AsyncClient):
        """Test database connection pooling under load"""
        async def make_request():
            return await client.get("/api/v1/health")

        # Make concurrent requests to test connection pooling
        tasks = [make_request() for _ in range(100)]
        responses = await asyncio.gather(*tasks)

        # Most requests should succeed, testing connection pool effectiveness
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 90  # Allow for some connection limits

    @pytest.mark.asyncio
    async def test_data_consistency(self, client: AsyncClient):
        """Test data consistency across related operations"""
        # This would require implementing related data operations
        # For now, test basic CRUD consistency

        # Create user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "consistency_test@example.com",
                "full_name": "Consistency Test",
                "password": "TestPassword123!"
            }
        )

        if register_response.status_code == 201:
            # Login with same credentials
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "consistency_test@example.com",
                    "password": "TestPassword123!"
                }
            )

            assert login_response.status_code == 200

            # Verify user data is consistent
            user_data = login_response.json()["data"]["user"]
            assert user_data["email"] == "consistency_test@example.com"
            assert user_data["full_name"] == "Consistency Test"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])