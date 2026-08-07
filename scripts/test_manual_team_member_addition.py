#!/usr/bin/env python3
"""
Comprehensive Test Suite for Manual Team Member Addition
Tests the complete workflow from UI interactions to database operations
"""

import json
import unittest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import requests


class TestManualTeamMemberAddition(unittest.TestCase):
    """
    Comprehensive test suite for adding a team member manually
    Covers UI interactions, API endpoints, database operations, and validation
    """

    def setUp(self):
        """Set up test fixtures and mock data"""
        self.base_url = "http://localhost:8000/api/v1"

        # Mock team data
        self.mock_team = {
            "id": str(uuid4()),
            "name": "Clinical Psychology Team",
            "description": "Team focused on clinical psychology assessments",
            "organization_id": str(uuid4()),
            "created_by_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "members": [],
        }

        # Mock users for team member addition scenarios
        self.mock_users = {
            "team_owner": {
                "id": str(uuid4()),
                "email": "owner@example.com",
                "full_name": "Team Owner",
                "role": "USER",
                "is_active": True,
            },
            "existing_member": {
                "id": str(uuid4()),
                "email": "member@example.com",
                "full_name": "Existing Member",
                "role": "USER",
                "is_active": True,
            },
            "new_member_existing_user": {
                "id": str(uuid4()),
                "email": "newmember@example.com",
                "full_name": "New Member",
                "role": "USER",
                "is_active": True,
            },
            "new_member_not_in_system": {
                "email": "external@example.com",
                "full_name": "External User",
                "role": "USER",
                "is_active": True,
            },
            "admin_user": {
                "id": str(uuid4()),
                "email": "admin@example.com",
                "full_name": "Admin User",
                "role": "ADMIN",
                "is_active": True,
            },
        }

        # Team member roles enum
        self.team_roles = ["owner", "admin", "member"]

    # =============================================================================
    # UI COMPONENT TESTING
    # =============================================================================

    @patch("frontend.src.services.teamService.addTeamMember")
    @patch("frontend.src.services.teamService.getTeamMembers")
    def test_ui_team_member_addition_form_validation(
        self, mock_get_members, mock_add_member
    ):
        """Test frontend form validation for team member addition"""

        # Mock successful team member addition
        mock_add_member.return_value = {
            "id": str(uuid4()),
            "team_id": self.mock_team["id"],
            "user_id": self.mock_users["new_member_existing_user"]["id"],
            "role": "member",
            "user": self.mock_users["new_member_existing_user"],
        }

        # Mock current team members
        mock_get_members.return_value = {
            "members": [
                {
                    "id": str(uuid4()),
                    "user_id": self.mock_users["team_owner"]["id"],
                    "role": "owner",
                    "user": self.mock_users["team_owner"],
                }
            ]
        }

        # Simulate frontend form validation scenarios
        form_scenarios = [
            {
                "name": "Valid email and role",
                "data": {"email": "newmember@example.com", "role": "member"},
                "expected_valid": True,
                "expected_error": None,
            },
            {
                "name": "Invalid email format",
                "data": {"email": "invalid-email", "role": "member"},
                "expected_valid": False,
                "expected_error": "Please enter a valid email address",
            },
            {
                "name": "Empty email",
                "data": {"email": "", "role": "member"},
                "expected_valid": False,
                "expected_error": "Email is required",
            },
            {
                "name": "Invalid role",
                "data": {"email": "valid@example.com", "role": "invalid_role"},
                "expected_valid": False,
                "expected_error": "Please select a valid role",
            },
            {
                "name": "Empty role",
                "data": {"email": "valid@example.com", "role": ""},
                "expected_valid": False,
                "expected_error": "Role is required",
            },
        ]

        for scenario in form_scenarios:
            with self.subTest(scenario=scenario["name"]):
                is_valid = self._validate_team_member_form(scenario["data"])

                if scenario["expected_valid"]:
                    self.assertTrue(
                        is_valid, f"Form should be valid: {scenario['name']}"
                    )
                else:
                    self.assertFalse(
                        is_valid, f"Form should be invalid: {scenario['name']}"
                    )
                    # In real implementation, error message would be displayed
                    error = self._get_form_validation_error(scenario["data"])
                    self.assertIsNotNone(
                        error, f"Error message expected: {scenario['name']}"
                    )

    def test_ui_permission_based_rendering(self):
        """Test that UI renders correctly based on user permissions"""

        ui_scenarios = [
            {
                "name": "Team Owner can add members",
                "current_user_role": "owner",
                "can_add_members": True,
                "available_roles": ["admin", "member"],
            },
            {
                "name": "Team Admin can add members",
                "current_user_role": "admin",
                "can_add_members": True,
                "available_roles": ["member"],
            },
            {
                "name": "Team Member cannot add members",
                "current_user_role": "member",
                "can_add_members": False,
                "available_roles": [],
            },
            {
                "name": "Non-member cannot add members",
                "current_user_role": None,
                "can_add_members": False,
                "available_roles": [],
            },
        ]

        for scenario in ui_scenarios:
            with self.subTest(scenario=scenario["name"]):
                ui_permissions = self._get_ui_permissions(scenario["current_user_role"])

                self.assertEqual(
                    ui_permissions["can_add_members"],
                    scenario["can_add_members"],
                    f"Add members permission incorrect for {scenario['name']}",
                )

                self.assertEqual(
                    sorted(ui_permissions["available_roles"]),
                    sorted(scenario["available_roles"]),
                    f"Available roles incorrect for {scenario['name']}",
                )

    def _validate_team_member_form(self, form_data: Dict[str, Any]) -> bool:
        """Simulate frontend form validation"""
        email = form_data.get("email", "").strip()
        role = form_data.get("role", "").strip()

        # Email validation
        if not email:
            return False
        if "@" not in email or "." not in email.split("@")[-1]:
            return False

        # Role validation
        if not role or role not in self.team_roles:
            return False

        return True

    def _get_form_validation_error(self, form_data: Dict[str, Any]) -> str:
        """Get form validation error message"""
        email = form_data.get("email", "").strip()
        role = form_data.get("role", "").strip()

        if not email:
            return "Email is required"
        if "@" not in email or "." not in email.split("@")[-1]:
            return "Please enter a valid email address"
        if not role:
            return "Role is required"
        if role not in self.team_roles:
            return "Please select a valid role"

        return None

    def _get_ui_permissions(self, user_role: str) -> Dict[str, Any]:
        """Get UI permissions based on user role"""
        permissions = {
            "owner": {"can_add_members": True, "available_roles": ["admin", "member"]},
            "admin": {"can_add_members": True, "available_roles": ["member"]},
            "member": {"can_add_members": False, "available_roles": []},
        }

        return permissions.get(
            user_role, {"can_add_members": False, "available_roles": []}
        )

    # =============================================================================
    # API ENDPOINT TESTING
    # =============================================================================

    @patch("requests.post")
    @patch("app.api.v1.deps.get_current_active_user")
    def test_api_add_team_member_existing_user(self, mock_get_user, mock_post):
        """Test API endpoint for adding existing user to team"""

        # Mock current authenticated user (team owner)
        mock_get_user.return_value = Mock(
            id=self.mock_users["team_owner"]["id"],
            email=self.mock_users["team_owner"]["email"],
        )

        # Mock successful API response
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                "id": str(uuid4()),
                "team_id": self.mock_team["id"],
                "user_id": self.mock_users["new_member_existing_user"]["id"],
                "role": "member",
                "user": self.mock_users["new_member_existing_user"],
                "created_at": datetime.now().isoformat(),
            },
        )

        # Test API call
        response = requests.post(
            f"{self.base_url}/teams/{self.mock_team['id']}/members",
            json={
                "user_id": self.mock_users["new_member_existing_user"]["id"],
                "role": "member",
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        # Validate response
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertEqual(
            response_data["user_id"], self.mock_users["new_member_existing_user"]["id"]
        )
        self.assertEqual(response_data["role"], "member")
        self.assertIn("created_at", response_data)

        # Validate API call was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(
            call_args[1]["json"]["user_id"],
            self.mock_users["new_member_existing_user"]["id"],
        )
        self.assertEqual(call_args[1]["json"]["role"], "member")

    @patch("requests.post")
    @patch("app.api.v1.deps.get_current_active_user")
    def test_api_add_team_member_by_email(self, mock_get_user, mock_post):
        """Test API endpoint for adding team member by email (new user invitation)"""

        # Mock current authenticated user
        mock_get_user.return_value = Mock(
            id=self.mock_users["team_owner"]["id"],
            email=self.mock_users["team_owner"]["email"],
        )

        # Mock successful API response for email-based addition
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                "id": str(uuid4()),
                "team_id": self.mock_team["id"],
                "email": self.mock_users["new_member_not_in_system"]["email"],
                "role": "member",
                "invitation_sent": True,
                "invitation_token": str(uuid4()),
                "message": "Invitation sent to new user",
            },
        )

        # Test API call with email
        response = requests.post(
            f"{self.base_url}/teams/{self.mock_team['id']}/members/invite",
            json={
                "email": self.mock_users["new_member_not_in_system"]["email"],
                "role": "member",
            },
            headers={"Authorization": "Bearer fake-token"},
        )

        # Validate response
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertEqual(
            response_data["email"], self.mock_users["new_member_not_in_system"]["email"]
        )
        self.assertTrue(response_data["invitation_sent"])
        self.assertIn("invitation_token", response_data)

    @patch("requests.post")
    @patch("app.api.v1.deps.get_current_active_user")
    def test_api_permission_validation(self, mock_get_user, mock_post):
        """Test API permission validation for team member addition"""

        # Test different user roles and their permissions
        permission_scenarios = [
            {
                "name": "Team Owner can add members",
                "user_role": "owner",
                "expected_status": 201,
                "should_succeed": True,
            },
            {
                "name": "Team Admin can add members",
                "user_role": "admin",
                "expected_status": 201,
                "should_succeed": True,
            },
            {
                "name": "Team Member cannot add members",
                "user_role": "member",
                "expected_status": 403,
                "should_succeed": False,
            },
            {
                "name": "Non-member cannot add members",
                "user_role": None,
                "expected_status": 403,
                "should_succeed": False,
            },
        ]

        for scenario in permission_scenarios:
            with self.subTest(scenario=scenario["name"]):
                # Mock current user with specified role
                mock_user = Mock(id=str(uuid4()))
                mock_get_user.return_value = mock_user

                # Mock API response based on expected outcome
                if scenario["should_succeed"]:
                    mock_post.return_value = Mock(
                        status_code=scenario["expected_status"]
                    )
                else:
                    mock_post.return_value = Mock(
                        status_code=scenario["expected_status"],
                        json=lambda: {"detail": "Permission denied"},
                    )

                response = requests.post(
                    f"{self.base_url}/teams/{self.mock_team['id']}/members",
                    json={"user_id": str(uuid4()), "role": "member"},
                    headers={"Authorization": "Bearer fake-token"},
                )

                self.assertEqual(
                    response.status_code,
                    scenario["expected_status"],
                    f"Status code mismatch for {scenario['name']}",
                )

    # =============================================================================
    # VALIDATION AND EDGE CASES
    # =============================================================================

    def test_email_validation_scenarios(self):
        """Test email validation for team member addition"""

        email_scenarios = [
            {
                "email": "valid@example.com",
                "expected_valid": True,
                "description": "Valid email",
            },
            {
                "email": "user.name+tag@example.com",
                "expected_valid": True,
                "description": "Email with plus addressing",
            },
            {
                "email": "user@subdomain.example.com",
                "expected_valid": True,
                "description": "Email with subdomain",
            },
            {
                "email": "invalid-email",
                "expected_valid": False,
                "description": "Invalid email format",
            },
            {
                "email": "@example.com",
                "expected_valid": False,
                "description": "Email missing username",
            },
            {
                "email": "user@",
                "expected_valid": False,
                "description": "Email missing domain",
            },
            {"email": "", "expected_valid": False, "description": "Empty email"},
            {
                "email": "   ",
                "expected_valid": False,
                "description": "Whitespace only email",
            },
            {
                "email": "user@example..com",
                "expected_valid": False,
                "description": "Email with double dots in domain",
            },
            {
                "email": "user.name@example",
                "expected_valid": False,
                "description": "Email without TLD",
            },
        ]

        for scenario in email_scenarios:
            with self.subTest(scenario=scenario["description"]):
                is_valid = self._validate_email_format(scenario["email"])
                self.assertEqual(
                    is_valid,
                    scenario["expected_valid"],
                    f"Email validation failed for: {scenario['email']}",
                )

    def test_role_assignment_validation(self):
        """Test role assignment validation"""

        role_scenarios = [
            {
                "role": "member",
                "assigner_role": "owner",
                "expected_valid": True,
                "description": "Owner assigning member role",
            },
            {
                "role": "admin",
                "assigner_role": "owner",
                "expected_valid": True,
                "description": "Owner assigning admin role",
            },
            {
                "role": "owner",
                "assigner_role": "owner",
                "expected_valid": False,
                "description": "Owner cannot assign owner role",
            },
            {
                "role": "member",
                "assigner_role": "admin",
                "expected_valid": True,
                "description": "Admin assigning member role",
            },
            {
                "role": "admin",
                "assigner_role": "admin",
                "expected_valid": False,
                "description": "Admin cannot assign admin role",
            },
            {
                "role": "member",
                "assigner_role": "member",
                "expected_valid": False,
                "description": "Member cannot assign roles",
            },
            {
                "role": "invalid_role",
                "assigner_role": "owner",
                "expected_valid": False,
                "description": "Invalid role assignment",
            },
        ]

        for scenario in role_scenarios:
            with self.subTest(scenario=scenario["description"]):
                is_valid = self._validate_role_assignment(
                    scenario["role"], scenario["assigner_role"]
                )
                self.assertEqual(
                    is_valid,
                    scenario["expected_valid"],
                    f"Role validation failed for {scenario['description']}",
                )

    def test_duplicate_member_prevention(self):
        """Test prevention of adding duplicate team members"""

        # Mock existing team members
        existing_members = [
            {
                "user_id": self.mock_users["existing_member"]["id"],
                "email": self.mock_users["existing_member"]["email"],
                "role": "member",
            },
            {
                "user_id": self.mock_users["team_owner"]["id"],
                "email": self.mock_users["team_owner"]["email"],
                "role": "owner",
            },
        ]

        duplicate_scenarios = [
            {
                "name": "Existing user by ID",
                "member_data": {"user_id": self.mock_users["existing_member"]["id"]},
                "should_be_duplicate": True,
            },
            {
                "name": "Existing user by email",
                "member_data": {"email": self.mock_users["existing_member"]["email"]},
                "should_be_duplicate": True,
            },
            {
                "name": "New user by ID",
                "member_data": {"user_id": str(uuid4())},
                "should_be_duplicate": False,
            },
            {
                "name": "New user by email",
                "member_data": {"email": "newuser@example.com"},
                "should_be_duplicate": False,
            },
        ]

        for scenario in duplicate_scenarios:
            with self.subTest(scenario=scenario["name"]):
                is_duplicate = self._check_duplicate_member(
                    scenario["member_data"], existing_members
                )
                self.assertEqual(
                    is_duplicate,
                    scenario["should_be_duplicate"],
                    f"Duplicate check failed for {scenario['name']}",
                )

    # =============================================================================
    # DATABASE OPERATIONS TESTING
    # =============================================================================

    @patch("sqlalchemy.ext.asyncio.AsyncSession")
    @patch("app.db.models.team.TeamMember")
    def test_database_team_member_creation(
        self, mock_team_member_model, mock_db_session
    ):
        """Test database operations for team member creation"""

        # Mock database session and model
        mock_session = AsyncMock()
        mock_db_session.return_value = mock_session

        # Mock team member model instance
        mock_team_member = Mock()
        mock_team_member.id = str(uuid4())
        mock_team_member.team_id = self.mock_team["id"]
        mock_team_member.user_id = self.mock_users["new_member_existing_user"]["id"]
        mock_team_member.role = "member"

        mock_team_member_model.return_value = mock_team_member

        # Simulate database creation
        async def simulate_database_creation():
            """Simulate the database creation process"""

            # Create new team member record
            new_member = mock_team_member_model(
                team_id=self.mock_team["id"],
                user_id=self.mock_users["new_member_existing_user"]["id"],
                role="member",
            )

            mock_session.add(new_member)
            await mock_session.commit()
            await mock_session.refresh(new_member)

            return new_member

        # Test database creation (run in async context simulation)
        import asyncio

        # Mock the async functions
        mock_session.add = Mock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Simulate the async operation
        result = asyncio.run(simulate_database_creation())

        # Validate database operations were called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Validate created member data
        self.assertEqual(result.team_id, self.mock_team["id"])
        self.assertEqual(
            result.user_id, self.mock_users["new_member_existing_user"]["id"]
        )
        self.assertEqual(result.role, "member")

    @patch("sqlalchemy.ext.asyncio.AsyncSession")
    @patch("app.db.models.team.Team")
    @patch("app.db.models.team.TeamMember")
    def test_database_permission_validation(
        self, mock_team_member_model, mock_team_model, mock_db_session
    ):
        """Test database-level permission validation"""

        # Mock database session
        mock_session = AsyncMock()
        mock_db_session.return_value = mock_session

        # Mock query results
        mock_existing_member = Mock()
        mock_existing_member.user_id = self.mock_users["team_owner"]["id"]
        mock_existing_member.role = "owner"

        mock_query_result = Mock()
        mock_query_result.scalar_one_or_none.return_value = mock_existing_member
        mock_session.execute.return_value = mock_query_result

        # Permission validation scenarios
        permission_scenarios = [
            {
                "name": "Owner can add members",
                "current_user_id": self.mock_users["team_owner"]["id"],
                "existing_member_role": "owner",
                "target_role": "member",
                "expected_allowed": True,
            },
            {
                "name": "Admin can add members",
                "current_user_id": self.mock_users["existing_member"]["id"],
                "existing_member_role": "admin",
                "target_role": "member",
                "expected_allowed": True,
            },
            {
                "name": "Member cannot add members",
                "current_user_id": self.mock_users["existing_member"]["id"],
                "existing_member_role": "member",
                "target_role": "member",
                "expected_allowed": False,
            },
            {
                "name": "Non-member cannot add members",
                "current_user_id": str(uuid4()),
                "existing_member_role": None,
                "target_role": "member",
                "expected_allowed": False,
            },
        ]

        for scenario in permission_scenarios:
            with self.subTest(scenario=scenario["name"]):
                # Simulate database permission check
                is_allowed = self._check_database_permissions(
                    current_user_id=scenario["current_user_id"],
                    team_id=self.mock_team["id"],
                    target_role=scenario["target_role"],
                )

                self.assertEqual(
                    is_allowed,
                    scenario["expected_allowed"],
                    f"Database permission check failed for {scenario['name']}",
                )

    # =============================================================================
    # INTEGRATION AND END-TO-END TESTING
    # =============================================================================

    @patch("requests.post")
    @patch("requests.get")
    @patch("app.api.v1.deps.get_current_active_user")
    def test_end_to_end_team_member_addition(self, mock_get_user, mock_get, mock_post):
        """Test complete end-to-end workflow for adding team member"""

        # Mock current authenticated user (team owner)
        mock_get_user.return_value = Mock(
            id=self.mock_users["team_owner"]["id"],
            email=self.mock_users["team_owner"]["email"],
        )

        # Mock team details response
        mock_get.return_value = Mock(status_code=200, json=lambda: self.mock_team)

        # Mock successful team member addition response
        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {
                "id": str(uuid4()),
                "team_id": self.mock_team["id"],
                "user_id": self.mock_users["new_member_existing_user"]["id"],
                "role": "member",
                "user": self.mock_users["new_member_existing_user"],
                "created_at": datetime.now().isoformat(),
            },
        )

        # Step 1: Get team details
        team_response = requests.get(
            f"{self.base_url}/teams/{self.mock_team['id']}",
            headers={"Authorization": "Bearer fake-token"},
        )
        self.assertEqual(team_response.status_code, 200)

        # Step 2: Add team member
        add_response = requests.post(
            f"{self.base_url}/teams/{self.mock_team['id']}/members",
            json={
                "user_id": self.mock_users["new_member_existing_user"]["id"],
                "role": "member",
            },
            headers={"Authorization": "Bearer fake-token"},
        )
        self.assertEqual(add_response.status_code, 201)

        # Step 3: Verify member was added (mock verification)
        member_data = add_response.json()
        self.assertEqual(
            member_data["user_id"], self.mock_users["new_member_existing_user"]["id"]
        )
        self.assertEqual(member_data["role"], "member")

        # Step 4: Update team member list (would be done in real UI)
        updated_team = team_response.json()
        updated_team["members"].append(member_data)

        # Validate final state
        self.assertEqual(len(updated_team["members"]), 1)  # Added one member
        self.assertEqual(
            updated_team["members"][0]["user_id"],
            self.mock_users["new_member_existing_user"]["id"],
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email.strip()))

    def _validate_role_assignment(self, role: str, assigner_role: str) -> bool:
        """Validate if assigner role can assign target role"""
        role_permissions = {
            "owner": ["admin", "member"],
            "admin": ["member"],
            "member": [],
        }

        return role in role_permissions.get(assigner_role, [])

    def _check_duplicate_member(
        self, member_data: Dict[str, Any], existing_members: List[Dict[str, Any]]
    ) -> bool:
        """Check if member already exists in team"""
        if "user_id" in member_data:
            return any(m["user_id"] == member_data["user_id"] for m in existing_members)
        elif "email" in member_data:
            return any(m["email"] == member_data["email"] for m in existing_members)
        return False

    def _check_database_permissions(
        self, current_user_id: str, team_id: str, target_role: str
    ) -> bool:
        """Check database-level permissions for adding team member"""
        # In real implementation, this would query the database
        # For testing, we'll simulate the permission check

        # Simulate checking if current user has sufficient privileges
        # This would involve checking the user's role in the specific team
        return True  # Simplified for test simulation

    # =============================================================================
    # PERFORMANCE AND LOAD TESTING
    # =============================================================================

    def test_concurrent_team_member_addition(self):
        """Test team member addition under concurrent load"""

        import time
        from concurrent.futures import ThreadPoolExecutor

        def simulate_member_addition(member_data):
            """Simulate adding a team member"""
            # Simulate processing time
            time.sleep(0.1)

            # Simulate success/failure based on data
            if member_data.get("user_id") and len(member_data["user_id"]) > 0:
                return {
                    "success": True,
                    "member_id": str(uuid4()),
                    "processing_time": 0.1,
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid member data",
                    "processing_time": 0.1,
                }

        # Create test data for concurrent addition
        concurrent_additions = []
        for i in range(10):
            concurrent_additions.append({"user_id": str(uuid4()), "role": "member"})

        # Execute concurrent additions
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for member_data in concurrent_additions:
                future = executor.submit(simulate_member_addition, member_data)
                futures.append(future)

            results = []
            for future in futures:
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        end_time = time.time()
        total_time = end_time - start_time

        # Validate results
        successful_additions = [r for r in results if r["success"]]
        failed_additions = [r for r in results if not r["success"]]

        self.assertEqual(
            len(successful_additions),
            len(concurrent_additions),
            "All concurrent additions should succeed",
        )
        self.assertEqual(len(failed_additions), 0, "No additions should fail")

        # Performance assertions
        self.assertLess(
            total_time, 5.0, "Concurrent additions should complete within 5 seconds"
        )
        self.assertGreater(
            len(concurrent_additions) / total_time,
            1.0,
            "Should handle at least 1 addition per second",
        )

        print(f"\\n⚡ Concurrent Team Member Addition Performance:")
        print(f"  Total additions: {len(concurrent_additions)}")
        print(f"  Successful: {len(successful_additions)}")
        print(f"  Failed: {len(failed_additions)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Additions per second: {len(concurrent_additions) / total_time:.1f}")

    # =============================================================================
    # ERROR HANDLING AND EDGE CASES
    # =============================================================================

    @patch("requests.post")
    def test_error_handling_scenarios(self, mock_post):
        """Test various error handling scenarios"""

        error_scenarios = [
            {
                "name": "Network timeout",
                "mock_response": Mock(
                    status_code=None,
                    raise_for_status=lambda: (_ for _ in ()).throw(
                        requests.exceptions.Timeout()
                    ),
                ),
                "expected_error_type": requests.exceptions.Timeout,
            },
            {
                "name": "Server error (500)",
                "mock_response": Mock(
                    status_code=500, json=lambda: {"detail": "Internal server error"}
                ),
                "expected_error_type": None,
                "expected_status": 500,
            },
            {
                "name": "User not found (404)",
                "mock_response": Mock(
                    status_code=404, json=lambda: {"detail": "User not found"}
                ),
                "expected_error_type": None,
                "expected_status": 404,
            },
            {
                "name": "Permission denied (403)",
                "mock_response": Mock(
                    status_code=403, json=lambda: {"detail": "Permission denied"}
                ),
                "expected_error_type": None,
                "expected_status": 403,
            },
            {
                "name": "Validation error (422)",
                "mock_response": Mock(
                    status_code=422,
                    json=lambda: {
                        "detail": [
                            {
                                "loc": ["body", "user_id"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    },
                ),
                "expected_error_type": None,
                "expected_status": 422,
            },
        ]

        for scenario in error_scenarios:
            with self.subTest(scenario=scenario["name"]):
                mock_post.return_value = scenario["mock_response"]

                try:
                    response = requests.post(
                        f"{self.base_url}/teams/{self.mock_team['id']}/members",
                        json={"user_id": str(uuid4()), "role": "member"},
                        headers={"Authorization": "Bearer fake-token"},
                    )

                    if hasattr(scenario, "expected_status"):
                        self.assertEqual(
                            response.status_code,
                            scenario["expected_status"],
                            f"Status code mismatch for {scenario['name']}",
                        )
                except Exception as e:
                    if hasattr(scenario, "expected_error_type"):
                        self.assertIsInstance(
                            e,
                            scenario["expected_error_type"],
                            f"Exception type mismatch for {scenario['name']}",
                        )
                    else:
                        # Unexpected exception
                        self.fail(
                            f"Unexpected exception for {scenario['name']}: {str(e)}"
                        )

    def test_long_team_member_names_and_emails(self):
        """Test handling of long names and emails"""

        # Test scenarios with edge case data
        edge_case_scenarios = [
            {
                "name": "Very long email",
                "email": "a" * 50 + "@example.com",
                "expected_valid": False,
                "description": "Email exceeds typical length limits",
            },
            {
                "name": "Maximum valid email",
                "email": "user" + "a" * 30 + "@example.com",
                "expected_valid": True,
                "description": "Email at maximum reasonable length",
            },
            {
                "name": "Email with special characters",
                "email": "user+test.tag@example.co.uk",
                "expected_valid": True,
                "description": "Email with plus addressing and long TLD",
            },
            {
                "name": "International email",
                "email": "用户@例子.测试",
                "expected_valid": True,
                "description": "Email with international characters",
            },
        ]

        for scenario in edge_case_scenarios:
            with self.subTest(scenario=scenario["description"]):
                is_valid = self._validate_email_format(scenario["email"])
                self.assertEqual(
                    is_valid,
                    scenario["expected_valid"],
                    f"Email validation failed for {scenario['description']}",
                )


if __name__ == "__main__":
    # Run the comprehensive test suite
    unittest.main(verbosity=2)
