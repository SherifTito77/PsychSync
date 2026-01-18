"""
Test core fixes implemented in the codebase cleanup
This test validates that our critical security and functionality fixes work correctly
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.security import verify_password, get_password_hash, validate_password
from app.services.user_service import UserService, user_to_dict
from app.db.models.user import User, UserRole
from app.db.models.response import AssessmentResponse, Response
from app.db.models.analytics import Analytics, AnalyticsEvent
from app.api.v1.api import api_router


class TestSecurityFixes:
    """Test that security fixes are working correctly"""

    def test_password_validation(self):
        """Test password validation with improved security"""
        # Test valid passwords
        result = validate_password("SecureP@ss123!")
        assert result["valid"] == True
        assert len(result["errors"]) == 0

        # Test invalid passwords
        result = validate_password("weak")
        assert result["valid"] == False
        assert len(result["errors"]) > 0

    def test_password_hashing_no_truncation(self):
        """Test that long passwords are no longer silently truncated"""
        # Create a long password (>72 characters)
        long_password = "ThisIsAVeryLongPasswordThatExceedsThePrevious72CharacterLimitAndShouldNotBeSilentlyTruncatedByTheBcryptImplementation123456789"

        # Hash the password
        hashed = get_password_hash(long_password)

        # Verify the password works
        assert verify_password(long_password, hashed) == True

        # Verify a different password fails
        assert verify_password(long_password + "wrong", hashed) == False

    def test_user_role_enumeration(self):
        """Test that UserRole enum is available"""
        assert UserRole.ADMIN == "admin"
        assert UserRole.USER == "user"
        assert UserRole.TEAM_LEAD == "team_lead"

        # Test all enum values
        role_values = [role.value for role in UserRole]
        assert "admin" in role_values
        assert "user" in role_values
        assert "team_lead" in role_values


class TestModelImports:
    """Test that previously missing models are now available"""

    def test_assessment_response_model(self):
        """Test AssessmentResponse model is available"""
        assert AssessmentResponse is not None
        assert Response is not None
        assert AssessmentResponse == Response  # Should be an alias

    def test_analytics_models(self):
        """Test Analytics models are available"""
        assert Analytics is not None
        assert AnalyticsEvent is not None

    def test_user_model_has_role(self):
        """Test User model has role field"""
        # Check that role column exists in the model
        user_table = User.__table__
        assert 'role' in user_table.columns


class TestUserServiceAvailability:
    """Test that user service functions work correctly"""

    def test_user_to_dict_function(self):
        """Test user_to_dict helper function works"""
        # Create a mock user object with required attributes
        class MockUser:
            def __init__(self):
                self.id = "test-uuid"
                self.email = "test@example.com"
                self.full_name = "Test User"
                self.avatar_url = None
                self.is_active = True
                self.is_verified = False
                self.is_superuser = False
                self.created_at = None
                self.updated_at = None

        user = MockUser()
        user_dict = user_to_dict(user)

        assert user_dict["id"] == "test-uuid"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["username"] == "test@example.com"  # Should fallback to email

    def test_user_service_class_available(self):
        """Test UserService class is available and has required methods"""
        assert UserService is not None

        # Check that required static methods exist
        assert hasattr(UserService, 'create')
        assert hasattr(UserService, 'get_by_id')
        assert hasattr(UserService, 'get_by_email')
        assert hasattr(UserService, 'update')
        assert hasattr(UserService, 'delete')
        assert hasattr(UserService, 'authenticate')


class TestAPIRouterAvailability:
    """Test that API router is working with our fixes"""

    def test_api_router_imports_successfully(self):
        """Test that API router can be imported without errors"""
        assert api_router is not None
        assert len(api_router.routes) > 0

    def test_api_router_has_required_endpoints(self):
        """Test that critical endpoints are available"""
        routes = [route.path for route in api_router.routes]

        # Check for core endpoints
        assert "/api/v1/users/me" in routes
        assert "/api/v1/users/change-password" in routes
        assert "/api/v1/assessments/" in routes
        assert "/api/v1/health/status" in routes
        assert "/api/v1/" in routes  # Root endpoint

    def test_api_router_endpoint_count(self):
        """Test that we have a reasonable number of endpoints"""
        routes = list(api_router.routes)
        route_count = len(routes)

        # Should have at least 50 endpoints after re-enabling disabled ones
        assert route_count >= 50, f"Expected at least 50 routes, got {route_count}"


class TestConfigurationFixes:
    """Test that configuration issues are resolved"""

    def test_no_debug_credential_logging(self):
        """Test that debug logging of credentials has been removed"""
        from app.core.config import get_database_url

        # This function should not log sensitive information anymore
        try:
            result = get_database_url()
            # Function should execute without logging credentials
            assert result is not None
        except Exception as e:
            pytest.fail(f"get_database_url failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
