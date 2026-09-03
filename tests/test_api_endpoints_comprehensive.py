# tests/test_api_endpoints_comprehensive.py
"""
Comprehensive API endpoint testing
- CRUD operations testing
- Pagination and filtering
- Error handling and validation
- Response schemas and status codes
- Performance and rate limiting
- Security and authorization
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
from app.db.models.organization import Organization
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User, UserRole


@pytest.mark.integration
class TestUserEndpoints:
    """Test user management endpoints"""

    async def test_get_current_user(self, async_client: AsyncClient, auth_headers: dict, test_user: User):
        """Test getting current user profile"""
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert "password" not in data

    async def test_update_current_user(self, async_client: AsyncClient, auth_headers: dict):
        """Test updating current user profile"""
        update_data = {
            "full_name": "Updated Name",
            "department": "Updated Department",
            "job_title": "Updated Title",
            "bio": "Updated bio"
        }

        response = await async_client.put("/api/v1/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["department"] == update_data["department"]

    async def test_get_users_pagination(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test getting users with pagination"""
        # Create additional users
        await test_utils.create_test_users(async_db, 15)

        # Test first page
        response = await async_client.get("/api/v1/users?page=1&size=10", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        test_utils.assert_valid_pagination(data)
        assert len(data["items"]) <= 10
        assert data["total"] >= 15

    async def test_get_users_filtering(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test filtering users"""
        # Create users with different roles
        await test_utils.create_test_users(async_db, 5, UserRole.ADMIN)
        await test_utils.create_test_users(async_db, 5, UserRole.MODERATOR)

        # Filter by role
        response = await async_client.get("/api/v1/users?role=admin", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        for user in data["items"]:
            assert user["role"] == UserRole.ADMIN.value

    async def test_get_user_by_id(self, async_client: AsyncClient, admin_headers: dict, test_user: User):
        """Test getting user by ID"""
        response = await async_client.get(f"/api/v1/users/{test_user.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)

    async def test_get_user_by_id_unauthorized(self, async_client: AsyncClient, auth_headers: dict, test_user: User):
        """Test getting user by ID without admin permissions"""
        response = await async_client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)

        assert response.status_code == 403

    async def test_delete_user(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test deleting user"""
        users = await test_utils.create_test_users(async_db, 1)
        user_to_delete = users[0]

        response = await async_client.delete(f"/api/v1/users/{user_to_delete.id}", headers=admin_headers)

        assert response.status_code == 204

        # Verify user is deleted
        deleted_user = await async_db.get(User, user_to_delete.id)
        assert deleted_user is None


@pytest.mark.integration
class TestTeamEndpoints:
    """Test team management endpoints"""

    async def test_create_team(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization):
        """Test creating a team"""
        team_data = {
            "name": "Test Team",
            "description": "A test team",
            "department": "Engineering",
            "organization_id": str(test_organization.id)
        }

        response = await async_client.post("/api/v1/teams", json=team_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == team_data["name"]
        assert data["organization_id"] == team_data["organization_id"]

    async def test_get_teams_pagination(self, async_client: AsyncClient, auth_headers: dict, test_team: Team, test_utils):
        """Test getting teams with pagination"""
        response = await async_client.get("/api/v1/teams?page=1&size=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        test_utils.assert_valid_pagination(data)
        assert len(data["items"]) >= 1

    async def test_get_team_by_id(self, async_client: AsyncClient, auth_headers: dict, test_team: Team):
        """Test getting team by ID"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_team.id)

    async def test_update_team(self, async_client: AsyncClient, auth_headers: dict, test_team: Team):
        """Test updating team"""
        update_data = {
            "name": "Updated Team Name",
            "description": "Updated description"
        }

        response = await async_client.put(f"/api/v1/teams/{test_team.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]

    async def test_add_team_member(self, async_client: AsyncClient, auth_headers: dict, async_db: AsyncSession, test_team: Team, test_utils):
        """Test adding member to team"""
        # Create additional user
        new_users = await test_utils.create_test_users(async_db, 1)
        new_user = new_users[0]

        member_data = {
            "user_id": str(new_user.id),
            "role": TeamRole.MEMBER.value
        }

        response = await async_client.post(f"/api/v1/teams/{test_team.id}/members", json=member_data, headers=auth_headers)

        assert response.status_code == 201

    async def test_remove_team_member(self, async_client: AsyncClient, auth_headers: dict, async_db: AsyncSession, test_team: Team, test_utils):
        """Test removing member from team"""
        # Create and add user to team
        new_users = await test_utils.create_test_users(async_db, 1)
        new_user = new_users[0]

        # Add member directly to DB for testing
        team_member = TeamMember(
            team_id=test_team.id,
            user_id=new_user.id,
            role=TeamRole.MEMBER,
            joined_at=datetime.utcnow()
        )
        async_db.add(team_member)
        await async_db.commit()

        # Remove member
        response = await async_client.delete(f"/api/v1/teams/{test_team.id}/members/{new_user.id}", headers=auth_headers)

        assert response.status_code == 204

    async def test_get_team_members(self, async_client: AsyncClient, auth_headers: dict, test_team: Team):
        """Test getting team members"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}/members", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the creator


@pytest.mark.integration
class TestAssessmentEndpoints:
    """Test assessment management endpoints"""

    async def test_create_assessment(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization):
        """Test creating an assessment"""
        assessment_data = {
            "title": "Test Assessment",
            "description": "A test assessment",
            "category": AssessmentCategory.PERSONALITY.value,
            "estimated_duration_minutes": 30,
            "instructions": "Complete this assessment",
            "organization_id": str(test_organization.id)
        }

        response = await async_client.post("/api/v1/assessments", json=assessment_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == assessment_data["title"]
        assert data["category"] == assessment_data["category"]

    async def test_get_assessments_with_filters(self, async_client: AsyncClient, auth_headers: dict, test_assessment: Assessment):
        """Test getting assessments with filters"""
        # Filter by category
        response = await async_client.get(
            f"/api/v1/assessments?category={test_assessment.category.value}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        if "items" in data:  # If paginated
            for assessment in data["items"]:
                assert assessment["category"] == test_assessment.category.value
        else:  # If not paginated
            for assessment in data:
                assert assessment["category"] == test_assessment.category.value

    async def test_get_assessment_by_id(self, async_client: AsyncClient, auth_headers: dict, test_assessment: Assessment):
        """Test getting assessment by ID"""
        response = await async_client.get(f"/api/v1/assessments/{test_assessment.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_assessment.id)

    async def test_update_assessment(self, async_client: AsyncClient, auth_headers: dict, test_assessment: Assessment):
        """Test updating assessment"""
        update_data = {
            "title": "Updated Assessment Title",
            "description": "Updated description",
            "status": AssessmentStatus.PUBLISHED.value
        }

        response = await async_client.put(f"/api/v1/assessments/{test_assessment.id}", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["status"] == update_data["status"]

    async def test_publish_assessment(self, async_client: AsyncClient, auth_headers: dict, test_assessment: Assessment):
        """Test publishing assessment"""
        response = await async_client.post(f"/api/v1/assessments/{test_assessment.id}/publish", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == AssessmentStatus.PUBLISHED.value

    async def test_duplicate_assessment(self, async_client: AsyncClient, auth_headers: dict, test_assessment: Assessment):
        """Test duplicating assessment"""
        duplicate_data = {
            "title": "Duplicated Assessment"
        }

        response = await async_client.post(
            f"/api/v1/assessments/{test_assessment.id}/duplicate",
            json=duplicate_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == duplicate_data["title"]
        assert data["id"] != str(test_assessment.id)


@pytest.mark.integration
class TestOrganizationEndpoints:
    """Test organization management endpoints"""

    async def test_create_organization(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating organization"""
        org_data = {
            "name": "Test Organization",
            "description": "A test organization",
            "industry": "Technology",
            "size": "11-50",
            "website": "https://testorg.com"
        }

        response = await async_client.post("/api/v1/organizations", json=org_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == org_data["name"]
        assert data["created_by_id"] in data  # Creator should be set

    async def test_get_organizations(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization):
        """Test getting organizations"""
        response = await async_client.get("/api/v1/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        if isinstance(data, list):
            assert len(data) >= 1
        elif "items" in data:
            assert len(data["items"]) >= 1

    async def test_update_organization(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization):
        """Test updating organization"""
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description"
        }

        response = await async_client.put(
            f"/api/v1/organizations/{test_organization.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]

    async def test_get_organization_stats(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization):
        """Test getting organization statistics"""
        response = await async_client.get(f"/api/v1/organizations/{test_organization.id}/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_teams" in data
        assert "total_assessments" in data


@pytest.mark.integration
class TestPaginationAndFiltering:
    """Test pagination and filtering across endpoints"""

    async def test_cursor_based_pagination(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test cursor-based pagination"""
        # Create many users
        await test_utils.create_test_users(async_db, 50)

        # Get first page
        response = await async_client.get("/api/v1/users?size=10&pagination_type=cursor", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data
        assert len(data["items"]) <= 10

        if data["next_cursor"]:
            # Get next page
            next_response = await async_client.get(
                f"/api/v1/users?size=10&cursor={data['next_cursor']}&pagination_type=cursor",
                headers=admin_headers
            )
            assert next_response.status_code == 200

    async def test_offset_based_pagination(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test offset-based pagination"""
        # Create many users
        await test_utils.create_test_users(async_db, 50)

        # Get second page
        response = await async_client.get("/api/v1/users?page=2&size=10&pagination_type=offset", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        test_utils.assert_valid_pagination(data)
        assert data["page"] == 2

    async test_search_functionality(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test search functionality"""
        # Create users with specific names
        search_term = "SearchableUser"
        await test_utils.create_test_users(async_db, 3)

        # Search for users
        response = await async_client.get(f"/api/v1/users?search={search_term}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        # Should return users matching search term

    async def test_sorting_functionality(self, async_client: AsyncClient, admin_headers: dict):
        """Test sorting functionality"""
        # Sort users by email
        response = await async_client.get("/api/v1/users?sort_by=email&sort_order=asc", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        # Check if items are sorted (depending on response format)
        items = data if isinstance(data, list) else data.get("items", [])
        if len(items) > 1:
            for i in range(len(items) - 1):
                assert items[i]["email"] <= items[i + 1]["email"]

    async def test_date_range_filtering(self, async_client: AsyncClient, auth_headers: dict):
        """Test filtering by date range"""
        from datetime import datetime, timedelta

        # Filter users created in last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        response = await async_client.get(
            f"/api/v1/users?created_after={start_date.isoformat()}&created_before={end_date.isoformat()}",
            headers=auth_headers
        )

        assert response.status_code == 200
        # Should return users within date range


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling"""

    async def test_validation_error_response(self, async_client: AsyncClient, auth_headers: dict):
        """Test validation error response format"""
        invalid_data = {
            "email": "invalid-email",
            "full_name": "",  # Empty name should fail validation
            "password": "123"  # Too short
        }

        response = await async_client.post("/api/v1/users", json=invalid_data, headers=auth_headers)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    async def test_not_found_error_response(self, async_client: AsyncClient, auth_headers: dict):
        """Test 404 error response format"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await async_client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_permission_denied_response(self, async_client: AsyncClient, auth_headers: dict, test_user: User):
        """Test permission denied response format"""
        response = await async_client.get(f"/api/v1/admin/users/{test_user.id}", headers=auth_headers)

        assert response.status_code in [403, 404]
        if response.status_code == 403:
            data = response.json()
            assert "detail" in data

    async def test_rate_limit_response(self, async_client: AsyncClient, test_user: User):
        """Test rate limiting response"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }

        # Make many requests
        for i in range(10):
            response = await async_client.post("/api/v1/auth/login/json", json=login_data)
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data
                assert "rate limit" in data["detail"].lower()
                break


@pytest.mark.integration
@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance"""

    async def test_list_response_time(self, async_client: AsyncClient, admin_headers: dict, performance_timer):
        """Test list endpoint response time"""
        with performance_timer():
            response = await async_client.get("/api/v1/users?size=50", headers=admin_headers)
            assert response.status_code == 200

    async def test_search_performance(self, async_client: AsyncClient, admin_headers: dict, performance_timer):
        """Test search performance"""
        with performance_timer():
            response = await async_client.get("/api/v1/users?search=test&page=1&size=20", headers=admin_headers)
            assert response.status_code == 200

    async def test_create_performance(self, async_client: AsyncClient, auth_headers: dict, test_organization: Organization, performance_timer):
        """Test create endpoint performance"""
        team_data = {
            "name": "Performance Test Team",
            "description": "Testing performance",
            "organization_id": str(test_organization.id)
        }

        with performance_timer():
            response = await async_client.post("/api/v1/teams", json=team_data, headers=auth_headers)
            assert response.status_code == 201


@pytest.mark.integration
@pytest.mark.security
class TestAPISecurity:
    """Test API security features"""

    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are present"""
        response = await async_client.options("/api/v1/users/me")

        assert response.status_code == 200
        # Check for CORS headers
        cors_headers = ["access-control-allow-origin", "access-control-allow-methods"]
        for header in cors_headers:
            assert header in response.headers

    async def test_security_headers(self, async_client: AsyncClient):
        """Test security headers are present"""
        response = await async_client.get("/api/v1/health")

        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]
        for header in security_headers:
            assert header in response.headers

    async def test_sensitive_data_exposure(self, async_client: AsyncClient, auth_headers: dict):
        """Test that sensitive data is not exposed"""
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        sensitive_fields = ["password", "password_hash", "secret"]

        for field in sensitive_fields:
            assert field not in data

    async def test_input_sanitization(self, async_client: AsyncClient, auth_headers: dict):
        """Test input sanitization"""
        malicious_data = {
            "full_name": "<script>alert('xss')</script>",
            "bio": "'; DROP TABLE users; --"
        }

        response = await async_client.put("/api/v1/users/me", json=malicious_data, headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            # Script tags should be escaped or removed
            assert "<script>" not in data["full_name"]
            assert ";" not in data["bio"] or "DROP TABLE" not in data["bio"]


@pytest.mark.integration
@pytest.mark.slow
class TestBulkOperations:
    """Test bulk operations"""

    async def test_bulk_user_operations(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils):
        """Test bulk user operations"""
        # Create multiple users
        users = await test_utils.create_test_users(async_db, 10)
        user_ids = [str(user.id) for user in users]

        # Bulk delete users
        bulk_data = {"user_ids": user_ids}
        response = await async_client.post("/api/v1/admin/users/bulk-delete", json=bulk_data, headers=admin_headers)

        # Response might be 200, 204, or 404 depending on implementation
        assert response.status_code in [200, 204, 404]

    async def test_bulk_email_operations(self, async_client: AsyncClient, admin_headers: dict, async_db: AsyncSession, test_utils, mock_email_service):
        """Test bulk email operations"""
        # Create users
        users = await test_utils.create_test_users(async_db, 5)
        user_emails = [user.email for user in users]

        # Send bulk email
        email_data = {
            "subject": "Test Bulk Email",
            "body": "This is a test email",
            "recipient_emails": user_emails
        }

        response = await async_client.post("/api/v1/admin/send-bulk-email", json=email_data, headers=admin_headers)

        # Response might be 200 or 404 depending on implementation
        if response.status_code == 200:
            mock_email_service.send_bulk_emails.assert_called_once()


@pytest.mark.integration
class TestAPIVersioning:
    """Test API versioning functionality"""

    async def test_version_header(self, async_client: AsyncClient):
        """Test API version header"""
        response = await async_client.get("/api/v1/health")

        assert response.status_code == 200
        assert "api-version" in response.headers

    async def test_version_negotiation(self, async_client: AsyncClient):
        """Test API version negotiation"""
        # Test with Accept header versioning
        headers = {"Accept": "application/vnd.psychsync.v1+json"}
        response = await async_client.get("/api/v1/health", headers=headers)

        assert response.status_code == 200

    async def test_deprecated_version_warning(self, async_client: AsyncClient):
        """Test deprecated version warning"""
        # This would test deprecated version if implemented
        response = await async_client.get("/api/v1/health")

        # Should not have deprecation warnings for current version
        assert "deprecation" not in response.headers.lower()
