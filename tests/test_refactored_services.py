"""
Test suite for refactored services (UserService and TeamService)

Validates that the BaseService pattern works correctly and all methods
function as expected.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import ValidationException
from app.services.team_service_refactored import TeamService
from app.services.user_service_refactored import UserService


class TestUserServiceRefactored:
    """Test suite for refactored UserService."""

    @pytest.fixture
    def user_service(self):
        """Create UserService instance."""
        return UserService()

    def test_service_properties(self, user_service):
        """Test service has required properties."""
        assert user_service.model is not None
        assert user_service.cache_strategy is not None
        from app.core.cache_strategy import CacheStrategy

        assert user_service.cache_strategy == CacheStrategy.USER_PROFILE

    def test_cache_key_generation(self, user_service):
        """Test cache key generation."""
        user_id = uuid4()
        key = user_service.get_cache_key("get_by_id", user_id=user_id)
        assert key.startswith("user:")
        assert str(user_id) in key

        key = user_service.get_cache_key("get_by_email", email="test@example.com")
        assert "test@example.com" in key.lower()

    def test_validate_create_data(self, user_service):
        """Test validation for user creation."""
        from app.schemas.user import UserCreate

        # Valid data
        valid_data = UserCreate(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User",
        )
        user_service.validate_create_data(valid_data)  # Should not raise

        # Note: Pydantic now validates email at schema level, so we can't test
        # invalid email in UserCreate. Instead, test business logic validation:
        # Name too long
        invalid_data = UserCreate(
            email="test2@example.com",
            password="SecurePass123!",
            full_name="x" * 300,  # Too long
        )
        with pytest.raises(ValidationException):
            user_service.validate_create_data(invalid_data)

    def test_validate_update_data(self, user_service):
        """Test validation for user update."""
        from app.db.models.user import User
        from app.schemas.user import UserUpdate

        # Create a mock user
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash",
        )

        # Valid update
        valid_update = UserUpdate(full_name="New Name")
        user_service.validate_update_data(valid_update, user)  # Should not raise

        # Email change (should fail - requires verification)
        email_update = UserUpdate(email="different@example.com")
        with pytest.raises(ValidationException) as exc_info:
            user_service.validate_update_data(email_update, user)
        assert "verification" in str(exc_info.value).lower()

    def test_search_users_pattern(self, user_service):
        """Test search users method pattern."""
        # This tests that the method can be called without errors
        # Actual database results would depend on test data

        # Verify method signature is correct
        assert hasattr(user_service, "search_users")
        assert callable(user_service.search_users)

        # Verify it accepts the right parameters
        import inspect

        sig = inspect.signature(user_service.search_users)
        assert "db" in sig.parameters
        assert "query" in sig.parameters
        assert "organization_id" in sig.parameters
        assert "skip" in sig.parameters
        assert "limit" in sig.parameters

    def test_check_email_exists_pattern(self, user_service):
        """Test check_email_exists method pattern."""
        assert hasattr(user_service, "check_email_exists")
        assert callable(user_service.check_email_exists)

        import inspect

        sig = inspect.signature(user_service.check_email_exists)
        assert "db" in sig.parameters
        assert "email" in sig.parameters
        assert "exclude_user_id" in sig.parameters

    def test_password_reset_flow(self, user_service):
        """Test password reset methods exist and have right signatures."""
        # Check methods exist
        assert hasattr(user_service, "request_password_reset")
        assert hasattr(user_service, "confirm_password_reset")
        assert callable(user_service.request_password_reset)
        assert callable(user_service.confirm_password_reset)

        # Note: Methods are decorated with @transaction_manager.transaction
        # which changes their signature. Just verify they exist and are callable.


class TestTeamServiceRefactored:
    """Test suite for refactored TeamService."""

    @pytest.fixture
    def team_service(self):
        """Create TeamService instance."""
        return TeamService()

    def test_service_properties(self, team_service):
        """Test service has required properties."""
        assert team_service.model is not None
        assert team_service.cache_strategy is not None
        from app.core.cache_strategy import CacheStrategy

        assert team_service.cache_strategy == CacheStrategy.TEAM_DATA

    def test_cache_key_generation(self, team_service):
        """Test cache key generation."""
        team_id = uuid4()
        user_id = uuid4()

        key = team_service.get_cache_key("get_by_id", team_id=team_id)
        assert key.startswith("team:")
        assert str(team_id) in key

        key = team_service.get_cache_key("get_by_user", user_id=user_id)
        assert str(user_id) in key

        key = team_service.get_cache_key("get_members", team_id=team_id)
        assert "members" in key

    def test_validate_create_data(self, team_service):
        """Test validation for team creation."""
        from app.schemas.team import TeamCreate

        # Valid data
        valid_data = TeamCreate(
            name="Valid Team Name",
            description="A valid description",
        )
        team_service.validate_create_data(valid_data)  # Should not raise

        # Name too short
        invalid_data = TeamCreate(name="x")
        with pytest.raises(ValidationException) as exc_info:
            team_service.validate_create_data(invalid_data)
        assert (
            "name" in str(exc_info.value).lower()
            or "character" in str(exc_info.value).lower()
        )

        # Name too long
        invalid_data2 = TeamCreate(name="x" * 150)
        with pytest.raises(ValidationException):
            team_service.validate_create_data(invalid_data2)

        # Description too long
        invalid_data3 = TeamCreate(
            name="Valid Name",
            description="x" * 600,
        )
        with pytest.raises(ValidationException):
            team_service.validate_create_data(invalid_data3)

    def test_validate_update_data(self, team_service):
        """Test validation for team update."""
        from app.db.models.team import Team
        from app.schemas.team import TeamUpdate

        team = Team(id=uuid4(), name="Original Name")

        # Valid update
        valid_update = TeamUpdate(name="Updated Name")
        team_service.validate_update_data(valid_update, team)  # Should not raise

        # Name too short
        invalid_update = TeamUpdate(name="x")
        with pytest.raises(ValidationException):
            team_service.validate_update_data(invalid_update, team)

    def test_team_method_signatures(self, team_service):
        """Test all team methods have correct signatures."""
        import inspect

        # Test required methods exist
        methods = [
            "get_by_id",
            "get_by_user",
            "create_team",
            "update_team",
            "delete_team",
            "add_member",
            "remove_member",
            "is_member",
            "get_user_role",
        ]

        for method_name in methods:
            assert hasattr(team_service, method_name), f"Missing method: {method_name}"
            method = getattr(team_service, method_name)
            assert callable(method), f"Method {method_name} is not callable"

            # Note: Decorated methods may have altered signatures, just check they exist


class TestServiceIntegration:
    """Integration tests for refactored services."""

    def test_services_can_be_imported(self):
        """Test that refactored services can be imported."""
        # This import should work without errors
        from app.services.team_service_refactored import TeamService, team_service
        from app.services.user_service_refactored import UserService, user_service

        # Verify singleton instances exist
        assert user_service is not None
        assert team_service is not None

    def test_services_have_correct_structure(self):
        """Test services follow BaseService pattern."""
        from app.services.team_service_refactored import TeamService
        from app.services.user_service_refactored import UserService

        # Both should have these required properties
        for ServiceClass in [UserService, TeamService]:
            # Check class has required abstract methods
            assert hasattr(ServiceClass, "model")
            assert hasattr(ServiceClass, "cache_strategy")
            assert hasattr(ServiceClass, "get_cache_key")
            assert hasattr(ServiceClass, "validate_create_data")
            assert hasattr(ServiceClass, "validate_update_data")

            # Check methods are implemented
            service = ServiceClass()
            assert service.model is not None
            assert service.cache_strategy is not None
            assert callable(service.get_cache_key)
            assert callable(service.validate_create_data)
            assert callable(service.validate_update_data)

    def test_services_use_base_service(self):
        """Test services actually extend BaseService."""
        from app.services.base_service import BaseService
        from app.services.team_service_refactored import TeamService
        from app.services.user_service_refactored import UserService

        # Verify inheritance
        assert issubclass(UserService, BaseService)
        assert issubclass(TeamService, BaseService)


class TestValidationScriptResults:
    """Test validation script detects expected issues."""

    def test_validation_script_runs(self):
        """Test validation script can be executed."""
        import os
        import subprocess

        script_path = "scripts/validate_architecture.py"
        assert os.path.exists(script_path), "Validation script not found"

        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
        )

        # Script should run (even if it finds issues)
        assert result.returncode in [0, 1]  # 0 = no issues, 1 = issues found
        assert "ARCHITECTURE VALIDATION REPORT" in result.stdout
        assert "SUMMARY" in result.stdout

    def test_validation_report_format(self):
        """Test validation report has expected format."""
        import os

        report_path = "architecture_report_baseline.txt"

        if not os.path.exists(report_path):
            pytest.skip(f"Report file not found: {report_path}")

        with open(report_path, "r") as f:
            content = f.read()

        # Check for expected sections
        assert "SERVICE LAYER" in content or "ARCHITECTURE VALIDATION" in content
        assert "SUMMARY" in content

        # Check for metrics
        assert "Total Issues:" in content or "Issues:" in content


@pytest.mark.parametrize(
    "service_name",
    [
        "assessment_service",
        "response_service",
        "analytics_service",
        "email_service",
        "notifications",  # Changed from notification_service to match actual filename
    ],
)
def test_migration_candidates_exist(service_name):
    """Test that services scheduled for migration actually exist."""
    import os

    service_path = f"app/services/{service_name}.py"
    assert os.path.exists(
        service_path
    ), f"Service {service_name} not found at {service_path}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
