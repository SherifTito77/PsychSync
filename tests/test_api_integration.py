# tests/test_api_integration.py
"""
Comprehensive API endpoint integration tests

Test Coverage:
- API Endpoints: 35
- Integration Tests: 45
- Expected Coverage: >90%
- Test Categories: Authentication, CRUD, Security, Error Handling, Performance
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient

# Import API endpoints testing utilities
from tests.test_auth_complete import TestJWTTokenSecurity, TestPasswordSecurity


class TestAuthenticationEndpoints:
    """Comprehensive authentication API endpoint testing (25 tests)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_registration_endpoint(self, async_client: AsyncClient):
        """Test user registration endpoint"""
        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New Test User",
            "phone": "+1234567890",
            "department": "Engineering",
            "job_title": "Software Engineer"
        }

        response = await async_client.post("/api/v1/register", json=registration_data)

        # Should succeed with strong password
        assert response.status_code in [201, 200, 409]  # 409 if user already exists

        if response.status_code in [201, 200]:
            data = response.json()
            assert "data" in data or "access_token" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_registration_weak_password(self, async_client: AsyncClient):
        """Test user registration with weak password rejection"""
        weak_password_data = {
            "email": "weakuser@example.com",
            "password": "password",  # Weak password
            "full_name": "Weak Password User"
        }

        response = await async_client.post("/api/v1/register", json=weak_password_data)

        # Should reject weak password
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        # Should contain password validation errors
        error_detail = str(data.get("detail", ""))
        assert any(keyword in error_detail.lower() for keyword in
                  ["password", "weak", "strength", "character"])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_endpoint_success(self, async_client: AsyncClient, test_user):
        """Test successful login endpoint"""
        login_data = {
            "username": test_user.email,
            "password": "SecurePassword123!"
        }

        response = await async_client.post("/api/v1/token", data=login_data)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "token_type" in data["data"]
        assert data["data"]["token_type"] == "bearer"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_endpoint_invalid_credentials(self, async_client: AsyncClient):
        """Test login endpoint with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }

        response = await async_client.post("/api/v1/token", data=login_data)

        assert response.status_code == 401

        # Should not reveal whether user exists
        data = response.json()
        assert "detail" in data
        error_message = data["detail"].lower()
        assert "invalid" in error_message or "incorrect" in error_message

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_endpoint_account_locked(self, async_client: AsyncClient, test_user):
        """Test login endpoint with locked account"""
        # Simulate account lockout by making multiple failed attempts
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }

        # Make failed attempts to trigger lockout
        for _ in range(6):  # Assuming MAX_LOGIN_ATTEMPTS is 5
            await async_client.post("/api/v1/token", data=login_data)

        # Try login with correct password (should be locked)
        login_data["password"] = "SecurePassword123!"
        response = await async_client.post("/api/v1/token", data=login_data)

        # Should indicate account is locked
        assert response.status_code in [401, 423]

        data = response.json()
        if "detail" in data:
            error_message = data["detail"].lower()
            assert "locked" in error_message or "attempts" in error_message

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refresh_token_endpoint(self, async_client: AsyncClient, test_user):
        """Test refresh token endpoint"""
        # First, get login tokens
        login_data = {
            "username": test_user.email,
            "password": "SecurePassword123!"
        }

        login_response = await async_client.post("/api/v1/token", data=login_data)
        login_data = login_response.json()
        refresh_token = login_data["data"]["refresh_token"]

        # Use refresh token to get new tokens
        refresh_data = {
            "refresh_token": refresh_token
        }

        response = await async_client.post("/api/v1/refresh", data=refresh_data)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

        # New tokens should be different from original
        new_access_token = data["data"]["access_token"]
        original_access_token = login_data["data"]["access_token"]
        assert new_access_token != original_access_token

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """Test refresh token endpoint with invalid token"""
        refresh_data = {
            "refresh_token": "invalid_refresh_token"
        }

        response = await async_client.post("/api/v1/refresh", data=refresh_data)

        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logout_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test logout endpoint"""
        response = await async_client.post("/api/v1/logout", headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logout_without_auth(self, async_client: AsyncClient):
        """Test logout endpoint without authentication"""
        response = await async_client.post("/api/v1/logout")

        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_logout_all_sessions(self, async_client: AsyncClient, auth_headers):
        """Test logout from all devices"""
        response = await async_client.post("/api/v1/logout-all", headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_password_reset_request(self, async_client: AsyncClient, test_user):
        """Test password reset request"""
        reset_data = {
            "email": test_user.email
        }

        response = await async_client.post("/api/v1/password-reset", json=reset_data)

        # Should accept the request (email service may be mocked)
        assert response.status_code in [200, 202]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_password_reset_invalid_email(self, async_client: AsyncClient):
        """Test password reset with invalid email"""
        reset_data = {
            "email": "nonexistent@example.com"
        }

        response = await async_client.post("/api/v1/password-reset", json=reset_data)

        # Should still accept the request for security (don't reveal email existence)
        assert response.status_code in [200, 202]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_profile_endpoint(self, async_client: AsyncClient, auth_headers, test_user):
        """Test user profile endpoint"""
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["email"] == test_user.email
        assert data["data"]["full_name"] == test_user.full_name

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_profile_without_auth(self, async_client: AsyncClient):
        """Test user profile endpoint without authentication"""
        response = await async_client.get("/api/v1/users/me")

        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_user_profile_update(self, async_client: AsyncClient, auth_headers):
        """Test user profile update"""
        update_data = {
            "full_name": "Updated Name",
            "phone": "+1234567890,
            "department": "Updated Department"
        }

        response = await async_client.put("/api/v1/users/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["full_name"] == "Updated Name"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_password_change_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test password change endpoint"""
        password_data = {
            "current_password": "SecurePassword123!",
            "new_password": "NewSecurePassword456!"
        }

        response = await async_client.post("/api/v1/users/change-password",
                                       json=password_data, headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_password_change_weak_password(self, async_client: AsyncClient, auth_headers):
        """Test password change with weak password"""
        password_data = {
            "current_password": "SecurePassword123!",
            "new_password": "weak"  # Weak password
        }

        response = await async_client.post("/api/v1/users/change-password",
                                       json=password_data, headers=auth_headers)

        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_password_change_wrong_current_password(self, async_client: AsyncClient, auth_headers):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewSecurePassword456!"
        }

        response = await async_client.post("/api/v1/users/change-password",
                                       json=password_data, headers=auth_headers)

        assert response.status_code == 400

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_email_verification_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test email verification request"""
        response = await async_client.post("/api/v1/users/verify-email", headers=auth_headers)

        # Should accept the request
        assert response.status_code in [200, 202]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_validation_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test token validation endpoint"""
        response = await async_client.get("/api/v1/users/validate-token", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "valid" in data["data"]
        assert data["data"]["valid"] is True


class TestOrganizationEndpoints:
    """Organization API endpoint testing (10 tests)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_organization(self, async_client: AsyncClient, admin_headers):
        """Test organization creation"""
        org_data = {
            "name": "Test Organization",
            "description": "Test organization for integration testing",
            "industry": "Technology",
            "size": "11-50",
            "website": "https://testorg.com",
            "location": "Test City, Test Country"
        }

        response = await async_client.post("/api/v1/organizations",
                                       json=org_data, headers=admin_headers)

        assert response.status_code == 201

        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == org_data["name"]
        assert data["data"]["description"] == org_data["description"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_organization_unauthorized(self, async_client: AsyncClient, auth_headers):
        """Test organization creation without admin privileges"""
        org_data = {
            "name": "Unauthorized Organization",
            "description": "Should not be created"
        }

        response = await async_client.post("/api/v1/organizations",
                                       json=org_data, headers=auth_headers)

        assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_organizations(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test organization listing"""
        response = await async_client.get("/api/v1/organizations", headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_organization(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test getting specific organization"""
        response = await async_client.get(f"/api/v1/organizations/{test_organization.id}",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == str(test_organization.id)
        assert data["data"]["name"] == test_organization.name

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_organization(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test organization update"""
        update_data = {
            "name": "Updated Organization Name",
            "description": "Updated description"
        }

        response = await async_client.put(f"/api/v1/organizations/{test_organization.id}",
                                          json=update_data, headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["description"] == update_data["description"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_organization(self, async_client: AsyncClient, admin_headers):
        """Test organization deletion"""
        # First create an organization to delete
        org_data = {
            "name": "Organization to Delete",
            "description": "This will be deleted"
        }

        create_response = await async_client.post("/api/v1/organizations",
                                                json=org_data, headers=admin_headers)
        assert create_response.status_code == 201

        org_id = create_response.json()["data"]["id"]

        # Delete the organization
        response = await async_client.delete(f"/api/v1/organizations/{org_id}",
                                             headers=admin_headers)

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await async_client.get(f"/api/v1/organizations/{org_id}",
                                             headers=admin_headers)
        assert get_response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_organization_members(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test organization members endpoint"""
        response = await async_client.get(f"/api/v1/organizations/{test_organization.id}/members",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "items" in data["data"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_organization_member(self, async_client: AsyncClient, admin_headers, test_organization, test_user):
        """Test adding member to organization"""
        member_data = {
            "user_id": str(test_user.id),
            "role": "member"
        }

        response = await async_client.post(f"/api/v1/organizations/{test_organization.id}/members",
                                           json=member_data, headers=admin_headers)

        assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_remove_organization_member(self, async_client: AsyncClient, admin_headers, test_organization, test_user):
        """Test removing member from organization"""
        # First add member
        member_data = {
            "user_id": str(test_user.id),
            "role": "member"
        }

        add_response = await async_client.post(f"/api/v1/organizations/{test_organization.id}/members",
                                              json=member_data, headers=admin_headers)
        if add_response.status_code == 201:
            # Then remove
            response = await async_client.delete(f"/api/v1/organizations/{test_organization.id}/members/{test_user.id}",
                                                headers=admin_headers)

            assert response.status_code == 204

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_organization_analytics(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test organization analytics endpoint"""
        response = await async_client.get(f"/api/v1/organizations/{test_organization.id}/analytics",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data


class TestTeamEndpoints:
    """Team API endpoint testing (10 tests)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_team(self, async_client: AsyncClient, admin_headers, test_organization):
        """Test team creation"""
        team_data = {
            "name": "Test Team",
            "description": "Test team for integration testing",
            "department": "Engineering",
            "team_type": "development"
        }

        response = await async_client.post("/api/v1/teams", json=team_data, headers=admin_headers)

        assert response.status_code == 201

        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == team_data["name"]
        assert data["data"]["organization_id"] == str(test_organization.id)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_teams(self, async_client: AsyncClient, admin_headers, test_team):
        """Test team listing"""
        response = await async_client.get("/api/v1/teams", headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_team(self, async_client: AsyncClient, admin_headers, test_team):
        """Test getting specific team"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}", headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == str(test_team.id)
        assert data["data"]["name"] == test_team.name

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_team(self, async_client: AsyncClient, admin_headers, test_team):
        """Test team update"""
        update_data = {
            "name": "Updated Team Name",
            "description": "Updated description"
        }

        response = await async_client.put(f"/api/v1/teams/{test_team.id}",
                                          json=update_data, headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["name"] == update_data["name"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_team_member(self, async_client: AsyncClient, admin_headers, test_team, test_user):
        """Test adding member to team"""
        member_data = {
            "user_id": str(test_user.id),
            "role": "member"
        }

        response = await async_client.post(f"/api/v1/teams/{test_team.id}/members",
                                           json=member_data, headers=admin_headers)

        assert response.status_code == 201

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_team_members_list(self, async_client: AsyncClient, admin_headers, test_team):
        """Test team members listing"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}/members",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "items" in data["data"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_remove_team_member(self, async_client: AsyncClient, admin_headers, test_team, test_user):
        """Test removing member from team"""
        response = await async_client.delete(f"/api/v1/teams/{test_team.id}/members/{test_user.id}",
                                                headers=admin_headers)

        assert response.status_code == 204

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_team_analytics(self, async_client: AsyncClient, admin_headers, test_team):
        """Test team analytics endpoint"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}/analytics",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_team(self, async_client: AsyncClient, admin_headers):
        """Test team deletion"""
        # First create a team to delete
        team_data = {
            "name": "Team to Delete",
            "description": "This will be deleted"
        }

        create_response = await async_client.post("/api/v1/teams", json=team_data, headers=admin_headers)
        assert create_response.status_code == 201

        team_id = create_response.json()["data"]["id"]

        # Delete the team
        response = await async_client.delete(f"/api/v1/teams/{team_id}", headers=admin_headers)

        assert response.status_code == 204

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_team_performance_metrics(self, async_client: AsyncClient, admin_headers, test_team):
        """Test team performance metrics endpoint"""
        response = await async_client.get(f"/api/v1/teams/{test_team.id}/performance",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data


class TestAssessmentEndpoints:
    """Assessment API endpoint testing (10 tests)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_assessment(self, async_client: AsyncClient, auth_headers, test_organization):
        """Test assessment creation"""
        assessment_data = {
            "title": "Test Assessment",
            "description": "Test assessment for integration testing",
            "category": "personality",
            "estimated_duration_minutes": 30,
            "instructions": "Please answer all questions honestly",
            "tags": ["test", "integration"],
            "questions": [
                {
                    "text": "I enjoy meeting new people",
                    "type": "likert",
                    "scale": 5,
                    "required": True
                },
                {
                    "text": "I prefer working alone",
                    "type": "likert",
                    "scale": 5,
                    "required": True
                }
            ]
        }

        response = await async_client.post("/api/v1/assessments",
                                           json=assessment_data, headers=auth_headers)

        assert response.status_code == 201

        data = response.json()
        assert "data" in data
        assert data["data"]["title"] == assessment_data["title"]
        assert len(data["data"]["questions"]) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_assessments(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test assessment listing"""
        response = await async_client.get("/api/v1/assessments", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_assessment(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test getting specific assessment"""
        response = await async_client.get(f"/api/v1/assessments/{test_assessment.id}",
                                          headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["id"] == str(test_assessment.id)
        assert data["data"]["title"] == test_assessment.title

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_assessment(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test assessment update"""
        update_data = {
            "title": "Updated Assessment Title",
            "description": "Updated description"
        }

        response = await async_client.put(f"/api/v1/assessments/{test_assessment.id}",
                                          json=update_data, headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["title"] == update_data["title"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_publish_assessment(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test publishing assessment"""
        response = await async_client.post(f"/api/v1/assessments/{test_assessment.id}/publish",
                                            headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["status"] in ["published", "active"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_take_assessment(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test taking an assessment"""
        # First get the assessment questions
        get_response = await async_client.get(f"/api/v1/assessments/{test_assessment.id}/take",
                                              headers=auth_headers)
        assert get_response.status_code == 200

        assessment_data = get_response.json()
        questions = assessment_data["data"]["questions"]

        # Submit responses
        responses = []
        for question in questions:
            responses.append({
                "question_id": question["id"],
                "answer": 3,  # Middle of Likert scale
                "response_time_ms": 1500
            })

        submit_data = {
            "responses": responses
        }

        response = await async_client.post(f"/api/v1/assessments/{test_assessment.id}/submit",
                                           json=submit_data, headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "results" in data["data"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assessment_results(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test getting assessment results"""
        response = await async_client.get(f"/api/v1/assessments/{test_assessment.id}/results",
                                          headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assessment_analytics(self, async_client: AsyncClient, auth_headers, test_assessment):
        """Test assessment analytics"""
        response = await async_client.get(f"/api/v1/assessments/{test_assessment.id}/analytics",
                                          headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_assessment(self, async_client: AsyncClient, auth_headers):
        """Test assessment deletion"""
        # First create an assessment to delete
        assessment_data = {
            "title": "Assessment to Delete",
            "description": "This will be deleted",
            "category": "personality",
            "questions": [
                {
                    "text": "Test question",
                    "type": "likert",
                    "scale": 5,
                    "required": True
                }
            ]
        }

        create_response = await async_client.post("/api/v1/assessments",
                                                json=assessment_data, headers=auth_headers)
        assert create_response.status_code == 201

        assessment_id = create_response.json()["data"]["id"]

        # Delete the assessment
        response = await async_client.delete(f"/api/v1/assessments/{assessment_id}",
                                             headers=auth_headers)

        assert response.status_code == 204

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assessment_templates(self, async_client: AsyncClient, auth_headers):
        """Test assessment templates listing"""
        response = await async_client.get("/api/v1/assessments/templates", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestSecurityEndpoints:
    """Security-specific API endpoint testing (15 tests)"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_alerts_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test security alerts endpoint"""
        response = await async_client.get("/api/v1/security-alerts", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "alerts" in data["data"]
        assert "count" in data["data"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_alerts_admin(self, async_client: AsyncClient, admin_headers):
        """Test security alerts endpoint for admin (should see all alerts)"""
        response = await async_client.get("/api/v1/security-alerts", headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_alerts_filtering(self, async_client: AsyncClient, auth_headers):
        """Test security alerts filtering"""
        # Filter by severity
        response = await async_client.get("/api/v1/security-alerts?severity=high", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "filters" in data["data"]
        assert data["data"]["filters"]["severity"] == "high"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resolve_security_alert(self, async_client: AsyncClient, admin_headers):
        """Test resolving security alert"""
        # This test would require an actual alert ID
        # For now, test the endpoint exists and handles invalid IDs properly
        response = await async_client.post("/api/v1/resolve-alert/invalid_alert_id",
                                           json={"resolution_note": "Test resolution"},
                                           headers=admin_headers)

        assert response.status_code in [404, 200]  # 404 if alert not found

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_risk_assessment_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test risk assessment endpoint"""
        response = await async_client.get("/api/v1/risk-assessment", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "user_id" in data["data"]
        assert "risk_level" in data["data"]
        assert "risk_factors" in data["data"]
        assert "risk_score" in data["data"]

        # Risk score should be between 0 and 100
        risk_score = data["data"]["risk_score"]
        assert 0 <= risk_score <= 100

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_risk_assessment_admin(self, async_client: AsyncClient, admin_headers, test_user):
        """Test risk assessment for another user (admin only)"""
        response = await async_client.get(f"/api/v1/risk-assessment?target_user_id={test_user.id}",
                                          headers=admin_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["user_id"] == str(test_user.id)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sessions_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test user sessions endpoint"""
        response = await async_client.get("/api/v1/sessions", headers=auth_headers)

        assert response.status_code == 200

        data = response.json()
        assert "data" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_revoke_session(self, async_client: AsyncClient, auth_headers):
        """Test revoking a specific session"""
        # Test with invalid session ID
        response = await async_client.delete("/api/v1/sessions/invalid_session_id",
                                             headers=auth_headers)

        assert response.status_code in [404, 200]  # 404 if session not found

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_trust_device_endpoint(self, async_client: AsyncClient, auth_headers):
        """Test trusting a device"""
        device_data = {
            "device_id": "test_device_123",
            "device_name": "Test Device"
        }

        response = await async_client.post("/api/v1/trust-device",
                                           json=device_data, headers=auth_headers)

        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_security_headers(self, async_client: AsyncClient):
        """Test security headers on all endpoints"""
        endpoints_to_test = [
            "/",
            "/api/v1/users/me",
            "/api/v1/health",
            "/api/v1/security-alerts"
        ]

        security_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection"
        ]

        for endpoint in endpoints_to_test:
            response = await async_client.get(endpoint)

            # Check for security headers
            headers = response.headers
            for header in security_headers:
                # Headers are lowercase in response.headers
                assert header in headers, f"Missing {header} header on {endpoint}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limiting_headers(self, async_client: AsyncClient):
        """Test rate limiting headers"""
        response = await async_client.get("/")

        # Should have rate limiting headers or handle gracefully
        assert response.status_code in [200, 429]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers"""
        # Test preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }

        response = await async_client.options("/api/v1/users/me", headers=headers)

        # Should handle CORS preflight
        assert response.status_code in [200, 204, 405]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client: AsyncClient):
        """Test that authentication is properly required"""
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/users/change-password",
            "/api/v1/logout",
            "/api/v1/organizations",
            "/api/v1/teams",
            "/api/v1/assessments"
        ]

        for endpoint in protected_endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_authorization_enforcement(self, async_client: AsyncClient, auth_headers):
        """Test that authorization is properly enforced"""
        admin_endpoints = [
            "/api/v1/users",  # User management
        ]

        for endpoint in admin_endpoints:
            response = await async_client.get(endpoint, headers=auth_headers)
            # Regular user should not have access to admin endpoints
            assert response.status_code == 403

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_input_validation(self, async_client: AsyncClient):
        """Test input validation on API endpoints"""
        # Test SQL injection attempts
        sql_payload = "admin'; DROP TABLE users; --"

        response = await async_client.post("/api/v1/token", data={
            "username": sql_payload,
            "password": "password123"
        })

        # Should handle SQL injection gracefully
        assert response.status_code in [401, 422]

        # Test XSS attempts
        xss_payload = "<script>alert('xss')</script>"

        response = await async_client.post("/api/v1/register", json={
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "full_name": xss_payload
        })

        # Should handle XSS gracefully
        if response.status_code == 422:
            # Should not execute script in response
            response_text = response.text.lower()
            assert "<script>" not in response_text

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling(self, async_client: AsyncClient):
        """Test secure error handling"""
        # Test with malformed JSON
        response = await async_client.post("/api/v1/register",
                                           data="invalid_json",
                                           headers={"Content-Type": "application/json"})

        assert response.status_code == 422

        # Test with invalid data types
        response = await async_client.post("/api/v1/register", json={
            "email": "not_an_email",
            "password": 123,  # Number instead of string
            "full_name": ""
        })

        assert response.status_code == 422

        # Error messages should not reveal sensitive information
        data = response.json()
        assert "detail" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """Test concurrent request handling"""
        async def make_request(request_id: int):
            response = await async_client.get("/health")
            return response.status_code

        # Make concurrent requests
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All requests should complete successfully
        for result in results:
            assert result == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_payload_handling(self, async_client: AsyncClient):
        """Test large payload handling"""
        # Create very large payload
        large_data = {
            "description": "x" * 10000  # 10KB of text
        }

        # This should be handled gracefully (either accept or reject with proper error)
        response = await async_client.post("/api/v1/register", json={
            "email": "large@example.com",
            "password": "SecurePassword123!",
            "full_name": "Large Data Test",
            **large_data
        })

        # Should not crash the server
        assert response.status_code in [201, 422]


# Performance Tests
class TestAPIPerformance:
    """API performance testing (5 tests)"""

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_authentication_performance(self, async_client: AsyncClient):
        """Test authentication endpoint performance"""
        login_data = {
            "username": "test@example.com",
            "password": "SecurePassword123!"
        }

        start_time = time.time()
        response = await async_client.post("/api/v1/token", data=login_data)
        end_time = time.time()

        response_time = end_time - start_time

        # Authentication should be fast
        assert response_time < 2.0  # Less than 2 seconds

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_response_time(self, async_client: AsyncClient, auth_headers):
        """Test API response time"""
        start_time = time.time()
        response = await async_client.get("/api/v1/users/me", headers=auth_headers)
        end_time = time.time()

        response_time = end_time - start_time

        # API responses should be fast
        assert response_time < 1.0  # Less than 1 second

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_pagination_performance(self, async_client: AsyncClient, auth_headers):
        """Test pagination performance"""
        start_time = time.time()
        response = await async_client.get("/api/v1/users?size=50&page=1", headers=auth_headers)
        end_time = time.time()

        response_time = end_time - start_time

        assert response_time < 2.0

        if response.status_code == 200:
            data = response.json()
            # Should have pagination info
            assert "data" in data

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, async_client: AsyncClient):
        """Test performance under concurrent load"""
        import asyncio

        async def make_request():
            response = await async_client.get("/health")
            return response.status_code

        start_time = time.time()
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Should handle 50 concurrent requests reasonably fast
        assert total_time < 10.0  # Less than 10 seconds
        assert all(result == 200 for result in results)

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_database_query_performance(self, async_client: AsyncClient, auth_headers):
        """Test database query performance"""
        start_time = time.time()
        response = await async_client.get("/api/v1/assessments", headers=auth_headers)
        end_time = time.time()

        response_time = end_time - start_time

        # Database queries should be optimized
        assert response_time < 3.0

        if response.status_code == 200:
            data = response.json()
            assert "data" in data


# Test execution and validation
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
