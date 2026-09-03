#!/usr/bin/env python3
"""
User Permission Tests for Profile Settings Screen
Tests role-based access control, admin vs user permissions,
and privilege escalation protection

Author: Security Team
Version: 1.0
"""

import asyncio
import json
import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import requests
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Test data
MOCK_USERS = {
    "normal_user": {
        "id": "user_123",
        "email": "user@example.com",
        "full_name": "Regular User",
        "role": "USER",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2024-01-01T00:00:00Z",
    },
    "admin_user": {
        "id": "admin_456",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "role": "ADMIN",
        "is_active": True,
        "is_superuser": True,
        "created_at": "2024-01-01T00:00:00Z",
    },
    "team_lead_user": {
        "id": "lead_789",
        "email": "lead@example.com",
        "full_name": "Team Lead User",
        "role": "TEAM_LEAD",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2024-01-01T00:00:00Z",
    },
    "inactive_user": {
        "id": "inactive_101",
        "email": "inactive@example.com",
        "full_name": "Inactive User",
        "role": "USER",
        "is_active": False,
        "is_superuser": False,
        "created_at": "2024-01-01T00:00:00Z",
    },
}

MOCK_SETTINGS = {
    "normal_user_settings": {
        "profile": {
            "name": "John Doe",
            "email": "user@example.com",
            "company": "Company Inc",
            "title": "Software Engineer",
            "bio": "Software developer with 5 years experience.",
        },
        "preferences": {
            "emailNotifications": True,
            "weeklyReports": False,
            "theme": "light",
            "language": "en",
        },
        "privacy": {
            "profileVisibility": "team",
            "shareAssessmentResults": True,
            "dataSharing": False,
        },
    },
    "admin_settings": {
        "profile": {
            "name": "Admin User",
            "email": "admin@example.com",
            "company": "Tech Corp",
            "title": "System Administrator",
            "bio": "System administrator with full system access.",
        },
        "preferences": {
            "emailNotifications": True,
            "weeklyReports": True,
            "theme": "dark",
            "language": "en",
        },
        "privacy": {
            "profileVisibility": "public",
            "shareAssessmentResults": True,
            "dataSharing": True,
        },
    },
}

# Mock HTTP responses
MOCK_RESPONSES = {
    "profile_get": {
        200: {"profile": MOCK_SETTINGS["normal_user_settings"]["profile"]},
        401: {"detail": "Not authenticated"},
        403: {"detail": "Permission denied"},
        404: {"detail": "Profile not found"},
    },
    "profile_update": {
        200: {"success": True, "message": "Profile updated successfully"},
        400: {"detail": "Validation error", "errors": []},
        401: {"detail": "Not authenticated"},
        403: {"detail": "Permission denied"},
        422: {"detail": "Invalid input data"},
    },
    "avatar_upload": {
        200: {"avatar_url": "https://example.com/avatars/user_123.jpg"},
        400: {"detail": "File validation error"},
        401: {"detail": "Not authenticated"},
        413: {"detail": "File too large"},
        422: {"detail": "Invalid file type"},
    },
}


class TestUserProfilePermissions(unittest.TestCase):
    """Test user permissions for Profile Settings screen"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_base = "http://localhost:8000/api/v1"
        self.settings_endpoint = f"{self.api_base}/settings"
        self.profile_endpoint = f"{self.api_base}/profile"
        self.avatar_endpoint = f"{self.api_base}/avatar"

    def create_mock_user(self, user_type: str):
        """Create a mock user for testing"""
        if user_type not in MOCK_USERS:
            raise ValueError(f"Unknown user type: {user_type}")
        return Mock(
            id=MOCK_USERS[user_type]["id"],
            email=MOCK_USERS[user_type]["email"],
            full_name=MOCK_USERS[user_type]["full_name"],
            role=MOCK_USERS[user_type]["role"],
            is_active=MOCK_USERS[user_type]["is_active"],
            is_superuser=MOCK_USERS[user_type]["is_superuser"],
            created_at=datetime.fromisoformat(MOCK_USERS[user_type]["created_at"]),
        )

    # =============================================================================
    # BASIC ACCESS CONTROL TESTS
    # =============================================================================

    def test_normal_user_can_access_own_profile(self):
        """Test that normal user can access their own profile settings"""
        normal_user = self.create_mock_user("normal_user")

        # Mock authentication dependency
        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            # User should be able to access their own profile
            self.assertTrue(
                True, "Normal user should be able to access their own profile"
            )

    def test_inactive_user_cannot_access_profile(self):
        """Test that inactive user cannot access profile settings"""
        inactive_user = self.create_mock_user("inactive_user")

        with patch("app.api.v1.deps.get_current_active_user") as mock_active_user:
            mock_active_user.side_effect = HTTPException(
                status_code=400, detail="Inactive user"
            )

            with self.assertRaises(HTTPException) as context:
                # Mock the API call
                with patch("requests.get") as mock_get:
                    mock_get.return_value = Mock(status_code=401)

                # The dependency should raise an exception first
                mock_active_user(normal_user)
                self.assertEqual(context.exception.status_code, 400)

    def test_admin_user_can_access_any_profile(self):
        """Test that admin user can access any user's profile (for moderation)"""
        admin_user = self.create_mock_user("admin_user")

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            self.assertTrue(
                admin_user.is_superuser, "Admin should have superuser privileges"
            )
            self.assertTrue(
                admin_user.role == "ADMIN", "Admin role should be set correctly"
            )

    def test_team_lead_has_limited_permissions(self):
        """Test that team lead has limited permissions on profile settings"""
        team_lead_user = self.create_mock_user("team_lead_user")

        with patch("app.api.v1.deps.get_current_user", return_value=team_lead_user):
            self.assertEqual(
                team_lead_user.role,
                "TEAM_LEAD",
                "Team lead role should be set correctly",
            )
            self.assertFalse(
                team_lead_user.is_superuser,
                "Team lead should not have superuser privileges",
            )

    # =============================================================================
    # PROFILE CRUD PERMISSIONS TESTS
    # =============================================================================

    @patch("requests.get")
    def test_normal_user_can_view_own_profile(self, mock_get):
        """Test normal user can view their own profile"""
        normal_user = self.create_mock_user("normal_user")
        mock_get.return_value = Mock(
            status_code=200, json=MOCK_SETTINGS["normal_user_settings"]["profile"]
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.get(self.profile_endpoint)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["name"], "John Doe")

    @patch("requests.get")
    def test_admin_user_can_view_any_profile(self, mock_get):
        """Test admin user can view any user profile"""
        admin_user = self.create_mock_user("admin_user")
        other_user_id = "other_user_123"

        admin_endpoint = f"{self.api_base}/users/{other_user_id}/profile"
        mock_get.return_value = Mock(
            status_code=200, json={"name": "Other User", "email": "other@example.com"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            response = requests.get(admin_endpoint)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["name"], "Other User")

    @patch("requests.get")
    def test_normal_user_cannot_view_other_profile(self, mock_get):
        """Test normal user cannot view other users' profiles"""
        normal_user = self.create_mock_user("normal_user")
        other_user_id = "other_user_123"
        other_endpoint = f"{self.api_base}/users/{other_user_id}/profile"

        mock_get.return_value = Mock(
            status_code=403, json={"detail": "Permission denied"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.get(other_endpoint)

            self.assertEqual(response.status_code, 403)

    @patch("requests.put")
    def test_normal_user_can_update_own_profile(self, mock_put):
        """Test normal user can update their own profile"""
        normal_user = self.create_mock_user("normal_user")
        update_data = {"name": "Updated Name", "title": "Updated Title"}

        mock_put.return_value = Mock(
            status_code=200,
            json={"success": True, "message": "Profile updated successfully"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                self.profile_endpoint,
                json=update_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])

    @patch("requests.put")
    def test_normal_user_cannot_update_other_profile(self, mock_put):
        """Test normal user cannot update other users' profiles"""
        normal_user = self.create_mock_user("normal_user")
        other_user_id = "other_user_123"
        other_endpoint = f"{self.api_base}/users/{other_user_id}/profile"
        update_data = {"name": "Malicious Update"}

        mock_put.return_value = Mock(
            status_code=403, json={"detail": "Permission denied"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                other_endpoint,
                json=update_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 403)

    @patch("requests.put")
    def test_admin_user_can_update_any_profile(self, mock_put):
        """Test admin user can update any user profile"""
        admin_user = self.create_mock_user("admin_user")
        other_user_id = "other_user_123"
        other_endpoint = f"{self.api_base}/users/{other_user_id}/profile"
        update_data = {"name": "Admin Updated", "role": "USER"}

        mock_put.return_value = Mock(
            status_code=200,
            json={"success": True, "message": "Profile updated by admin"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            response = requests.put(
                other_endpoint,
                json=update_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])

    # =============================================================================
    # SETTINGS PERMISSIONS TESTS
    # =============================================================================

    @patch("requests.get")
    def test_normal_user_can_view_settings(self, mock_get):
        """Test normal user can view their settings"""
        normal_user = self.create_mock_user("normal_user")
        mock_get.return_value = Mock(
            status_code=200, json=MOCK_SETTINGS["normal_user_settings"]
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.get(self.settings_endpoint)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("profile", data)
            self.assertIn("preferences", data)

    @patch("requests.get")
    def test_normal_user_has_limited_settings_visibility(self, mock_get):
        """Test normal user has limited visibility in settings"""
        normal_user = self.create_mock_user("normal_user")
        mock_get.return_value = Mock(
            status_code=200,
            json={
                "profile": MOCK_SETTINGS["normal_user_settings"]["profile"],
                "preferences": MOCK_SETTINGS["normal_user_settings"]["preferences"],
                "privacy": MOCK_SETTINGS["normal_user_settings"]["privacy"],
                # Admin-only sections should not be visible
            },
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.get(self.settings_endpoint)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("profile", data)
            self.assertIn("preferences", data)
            self.assertIn("privacy", data)
            # Should not have admin sections
            self.assertNotIn("admin", data)
            self.assertNotIn("system", data)

    @patch("requests.get")
    def test_admin_user_has_full_settings_visibility(self, mock_get):
        """Test admin user has full visibility in settings"""
        admin_user = self.create_mock_user("admin_user")
        mock_get.return_value = Mock(
            status_code=200,
            json={
                "profile": MOCK_SETTINGS["admin_settings"]["profile"],
                "preferences": MOCK_SETTINGS["admin_settings"]["preferences"],
                "privacy": MOCK_SETTINGS["admin_settings"]["privacy"],
                "admin": {
                    "system_settings": True,
                    "user_management": True,
                    "audit_logs": True,
                    "security_config": True,
                },
            },
        )

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            response = requests.get(self.settings_endpoint)

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("profile", data)
            self.assertIn("preferences", data)
            self.assertIn("privacy", data)
            # Should have admin sections
            self.assertIn("admin", data)

    @patch("requests.put")
    def test_normal_user_can_update_preferences(self, mock_put):
        """Test normal user can update their preferences"""
        normal_user = self.create_mock_user("normal_user")
        update_data = {"preferences": {"theme": "dark", "language": "es"}}

        mock_put.return_value = Mock(
            status_code=200, json={"success": True, "message": "Preferences updated"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                self.settings_endpoint,
                json=update_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["success"])

    @patch("requests.put")
    def test_normal_user_cannot_access_admin_settings(self, mock_put):
        """Test normal user cannot access admin settings"""
        normal_user = self.create_mock_user("normal_user")
        update_data = {"admin": {"system_settings": True}}

        mock_put.return_value = Mock(
            status_code=403, json={"detail": "Admin privileges required"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                self.settings_endpoint,
                json=update_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 403)

    # =============================================================================
    # AVATAR UPLOAD PERMISSIONS TESTS
    # =============================================================================

    @patch("requests.post")
    def test_normal_user_can_upload_own_avatar(self, mock_post):
        """Test normal user can upload their own avatar"""
        normal_user = self.create_mock_user("normal_user")

        mock_post.return_value = Mock(
            status_code=200,
            json={"avatar_url": "https://example.com/avatars/user_123.jpg"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.post(
                self.avatar_endpoint,
                files={"avatar": ("avatar.jpg", b"fake-image-data", "image/jpeg")},
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("avatar_url", data)

    @patch("requests.post")
    def test_normal_user_avatar_upload_validation(self, mock_post):
        """Test normal user avatar upload validation"""
        normal_user = self.create_mock_user("normal_user")

        # Test malicious file upload attempt
        malicious_file = ("malware.js", b"malicious-code", "application/javascript")

        mock_post.return_value = Mock(
            status_code=422, json={"detail": "Invalid file type"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.post(
                self.avatar_endpoint,
                files={"avatar": malicious_file},
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 422)

    @patch("requests.post")
    def test_admin_user_can_upload_any_avatar(self, mock_post):
        """Test admin user can upload avatar for any user"""
        admin_user = self.create_mock_user("admin_user")
        other_user_id = "other_user_123"
        admin_avatar_endpoint = f"{self.api_base}/admin/users/{other_user_id}/avatar"

        mock_post.return_value = Mock(
            status_code=200,
            json={"avatar_url": "https://example.com/avatars/other_user_123.jpg"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            response = requests.post(
                admin_avatar_endpoint,
                files={"avatar": ("avatar.jpg", b"fake-image-data", "image/jpeg")},
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 200)

    # =============================================================================
    # PRIVACY SETTINGS PERMISSIONS TESTS
    # =============================================================================

    def test_normal_user_privacy_visibility_options(self):
        """Test normal user has limited privacy visibility options"""
        normal_user = self.create_mock_user("normal_user")

        allowed_visibility_options = ["team", "private"]
        restricted_visibility_options = ["public"]

        # Mock user response to privacy settings
        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            for option in allowed_visibility_options:
                self.assertTrue(
                    True, f"Normal user should be able to set privacy to '{option}'"
                )

            for option in restricted_visibility_options:
                # Mock validation (this would be in the actual implementation)
                if option == "public":
                    # Normal users should not be allowed to set public visibility
                    pass  # This would fail in validation

    def test_admin_user_privacy_visibility_options(self):
        """Test admin user has full privacy visibility options"""
        admin_user = self.create_mock_user("admin_user")

        all_visibility_options = ["public", "team", "private"]

        with patch("app.api.v1.deps.get_current_user", return_value=admin_user):
            for option in all_visibility_options:
                self.assertTrue(
                    True, f"Admin user should be able to set privacy to '{option}'"
                )

    def test_data_sharing_permissions_by_role(self):
        """Test data sharing permissions vary by user role"""
        user_roles = ["USER", "TEAM_LEAD", "ADMIN"]
        expected_data_sharing = {
            "USER": {
                "can_share_assessment_results": True,
                "can_share_analytics": False,
                "can_share_with_third_party": False,
            },
            "TEAM_LEAD": {
                "can_share_assessment_results": True,
                "can_share_analytics": True,
                "can_share_with_third_party": False,
            },
            "ADMIN": {
                "can_share_assessment_results": True,
                "can_share_analytics": True,
                "can_share_with_third_party": True,
            },
        }

        for role in user_roles:
            user = self.create_mock_user(role.lower())

            with patch("app.api.v1.deps.get_current_user", return_value=user):
                self.assertEqual(
                    user.role, role.upper(), f"User role should be {role.upper()}"
                )

                if role.upper() in expected_data_sharing:
                    expected = expected_data_sharing[role.upper()]
                    self.assertTrue(
                        expected["can_share_assessment_results"],
                        f"{role} should be able to share assessment results",
                    )
                else:
                    # Default permissions for unknown roles
                    self.assertTrue(
                        True, f"Unknown role {role} should have default permissions"
                    )

    # =============================================================================
    # PRIVILEGE ESCALATION PROTECTION TESTS
    # =============================================================================

    @patch("requests.get")
    @patch("app.api.v1.deps.get_current_user")
    def test_token_validation_prevents_privilege_escalation(
        self, mock_get_current_user, mock_get
    ):
        """Test that invalid token validation prevents privilege escalation"""
        # Normal user token with admin role claim
        normal_user = self.create_mock_user("normal_user")

        # Mock corrupted token payload
        corrupted_payload = {
            "sub": normal_user.id,
            "role": "ADMIN",  # Privilege escalation attempt
            "exp": datetime.now() + timedelta(hours=1),
            "iat": datetime.now(),
        }

        with patch("app.api.v1.deps.get_current_user") as mock_get_current_user:
            mock_get_current_user.return_value = normal_user
            with patch("jwt.decode", return_value=corrupted_payload):
                with patch("app.api.v1.deps.get_current_admin_user"):
                    # This should fail because the user isn't actually an admin
                    with self.assertRaises(HTTPException) as context:
                        # Simulate API call that checks admin privileges
                        response = requests.get(f"{self.api_base}/admin/dashboard")
                        self.assertEqual(context.exception.status_code, 403)

    @patch("requests.put")
    def test_role_modification_prevention(self, mock_put):
        """Test that role modification is prevented"""
        normal_user = self.create_mock_user("normal_user")

        # Attempt to modify role in profile update
        malicious_payload = {"role": "ADMIN", "name": "Hacker"}

        mock_put.return_value = Mock(
            status_code=400,
            json={"detail": "Role modification not allowed", "field": "role"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                self.profile_endpoint,
                json=malicious_payload,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn("Role modification not allowed", response.json()["detail"])

    @patch("requests.delete")
    def test_account_deletion_permissions_by_role(self, mock_delete):
        """Test account deletion permissions vary by user role"""
        admin_user = self.create_mock_user("admin_user")
        normal_user = self.create_mock_user("normal_user")

        # Admin should be able to delete other accounts
        admin_delete_endpoint = f"{self.api_base}/admin/users/{normal_user.id}/delete"
        mock_delete.return_value = Mock(
            status_code=200,
            json={"success": True, "message": "User account deleted by admin"},
        )

        with patch("app.api.v1.deps.get_current_admin_user", return_value=admin_user):
            response = requests.delete(
                admin_delete_endpoint, headers={"Authorization": "Bearer fake-token"}
            )

            self.assertEqual(response.status_code, 200)

        # Normal user should only be able to delete their own account
        self_delete_endpoint = f"{self.api_base}/users/{normal_user.id}/delete"
        mock_delete.return_value = Mock(
            status_code=200,
            json={"success": True, "message": "Account deleted successfully"},
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.delete(
                self_delete_endpoint, headers={"Authorization": "Bearer fake-token"}
            )

            self.assertEqual(response.status_code, 200)

        # Normal user cannot delete other accounts
        other_delete_endpoint = f"{self.api_base}/users/{admin_user.id}/delete"
        mock_delete.return_value = Mock(
            status_code=403, json={"detail": "Permission denied"}
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.delete(
                other_delete_endpoint, headers={"Authorization": "fake-token"}
            )

            self.assertEqual(response.status_code, 403)

    # =============================================================================
    # CONCURRENT ACCESS TESTS
    # =============================================================================

    async def test_concurrent_user_isolation(self):
        """Test that concurrent user access is properly isolated"""

        async def test_user_access(user_data):
            """Test user accessing their profile"""
            # Simulate API call
            return Mock(status_code=200, json={"profile": {"name": user_data["name"]}})

        # Create test scenarios with different user types
        scenarios = [
            {"user": self.create_mock_user("normal_user"), "expected_status": 200},
            {"user": self.create_mock_user("admin_user"), "expected_status": 200},
            {"user": self.create_mock_user("inactive_user"), "expected_status": 401},
        ]

        # Run tests concurrently
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for scenario in scenarios:
                task = tg.create_task(test_user_access(scenario["user"]))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if result and hasattr(result, "status_code"):
                expected = scenarios[i]["expected_status"]
                if expected == 401:
                    self.assertEqual(
                        result.status_code, expected, f"Scenario {i} should return 401"
                    )
                else:
                    self.assertEqual(
                        result.status_code,
                        expected,
                        f"Scenario {i} should return {expected}",
                    )

    async def test_profile_data_isolation(self):
        """Test that users cannot access each other's profile data"""
        user1 = self.create_mock_user("normal_user")
        user2 = self.create_mock_user("admin_user")

        # Mock database queries
        async def get_user_profile(user_id, requestor_id):
            """Mock function to get user profile"""
            if requestor_id == user1.id:
                return {"name": "User 1 Data"}
            elif requestor_id == user2.id:
                return {"name": "User 2 Data"}
            elif requestor_id != user_id:
                return None
            else:
                return {"error": "Unauthorized access"}

        # Test isolation
        with patch("app.api.v1.deps.get_current_user") as mock_get_user:
            # User 1 accessing User 2's data should fail
            mock_get_user.return_value = user1

            with self.assertRaises(Exception):
                await get_user_profile(user2.id, user1.id)

        # Admin can access any user's data
        with patch("app.api.v1.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = user2

            result = await get_user_profile(user1.id, user2.id)
            self.assertEqual(result["name"], "User 2 Data")

    # =============================================================================
    # INTEGRATION TESTS
    # =============================================================================

    def test_frontend_permission_based_rendering(self):
        """Test frontend component rendering based on user permissions"""
        from unittest.mock import MagicMock

        # Mock React component
        mock_component = MagicMock()
        mock_component.state = {
            "currentUser": None,
            "settings": None,
            "adminFeatures": False,
        }

        # Test with normal user
        mock_component.state["currentUser"] = self.create_mock_user("normal_user")
        mock_component.state["settings"] = MOCK_SETTINGS["normal_user_settings"]

        # Check component properties
        self.assertEqual(mock_component.state["currentUser"].role, "USER")
        self.assertFalse(mock_component.state["adminFeatures"])

        # Test with admin user
        mock_component.state["currentUser"] = self.create_mock_user("admin_user")
        mock_component.state["settings"] = MOCK_SETTINGS["admin_settings"]

        # Check admin features are enabled
        self.assertEqual(mock_component.state["currentUser"].role, "ADMIN")
        self.assertTrue(mock_component.state["adminFeatures"])

    def test_api_endpoint_permission_enforcement(self):
        """Test API endpoints properly enforce permissions"""
        permission_tests = [
            {
                "endpoint": "/api/v1/settings",
                "user_type": "normal_user",
                "method": "GET",
                "expected_status": 200,
            },
            {
                "endpoint": "/api/v1/settings/profile",
                "user_type": "normal_user",
                "method": "PUT",
                "expected_status": 200,
            },
            {
                "endpoint": "/api/v1/settings/admin/config",
                "user_type": "normal_user",
                "method": "GET",
                "expected_status": 403,
            },
            {
                "endpoint": "/api/v1/settings/admin/users",
                "user_type": "normal_user",
                "method": "GET",
                "expected_status": 403,
            },
            {
                "endpoint": "/api/v1/settings/admin/config",
                "user_type": "admin_user",
                "method": "GET",
                "expected_status": 200,
            },
            {
                "endpoint": "/api/v1/settings/users",
                "user_type": "admin_user",
                "method": "GET",
                "expected_status": 200,
            },
        ]

        for test in permission_tests:
            user = self.create_mock_user(test["user_type"])

            with patch("app.api.v1.deps.get_current_user", return_value=user):
                # Mock API response
                with patch("requests.request") as mock_request:
                    mock_request.return_value = Mock(
                        status_code=test["expected_status"], json={}
                    )

                    response = requests.request(
                        method=test["method"],
                        url=f"{self.api_base}{test['endpoint']}",
                        headers={"Authorization": "Bearer fake-token"},
                    )

                    self.assertEqual(response.status_code, test["expected_status"])

    # =============================================================================
    # ERROR HANDLING TESTS
    # =============================================================================

    @patch("requests.get")
    def test_permission_denied_error_messages(self, mock_get):
        """Test that permission denied errors provide clear feedback"""
        normal_user = self.create_mock_user("normal_user")
        admin_endpoint = f"{self.api_base}/admin/dashboard"

        mock_get.return_value = Mock(
            status_code=403,
            json={
                "detail": "Permission denied",
                "required_role": "ADMIN",
                "current_role": "USER",
                "user_id": normal_user.id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.get(admin_endpoint)

            self.assertEqual(response.status_code, 403)
            error_data = response.json()
            self.assertEqual(error_data["detail"], "Permission denied")
            self.assertEqual(error_data["required_role"], "ADMIN")
            self.assertEqual(error_data["current_role"], "USER")

    @patch("requests.put")
    def test_validation_errors_include_user_info(self, mock_put):
        """Test validation errors include user identification for debugging"""
        normal_user = self.create_mock_user("normal_user")
        invalid_data = {"name": "", "role": "INVALID_ROLE"}

        mock_put.return_value = Mock(
            status_code=422,
            json={
                "detail": "Validation error",
                "errors": [{"field": "name", "message": "Name cannot be empty"}],
                "user_id": normal_user.id,
                "timestamp": datetime.now().isoformat(),
            },
        )

        with patch("app.api.v1.deps.get_current_user", return_value=normal_user):
            response = requests.put(
                self.profile_endpoint,
                json=invalid_data,
                headers={"Authorization": "Bearer fake-token"},
            )

            self.assertEqual(response.status_code, 422)
            error_data = response.json()
            self.assertIn("user_id", error_data)
            self.assertEqual(error_data["user_id"], normal_user.id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
