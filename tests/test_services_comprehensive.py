# tests/test_services_comprehensive.py
"""
Comprehensive service layer testing
- Business logic validation
- Database transaction handling
- Service integration testing
- Error handling and edge cases
- Performance optimization
- Caching behavior
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from unittest.mock import patch, AsyncMock
from typing import Dict, Any, List, Optional

from app.services.user_service import UserService, create_user, authenticate_user, update_user
from app.services.team_service import TeamService
from app.services.assessment_service import AssessmentService
from app.services.email_service import EmailService
from app.db.models.user import User, UserRole
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
from app.db.models.organization import Organization
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.team import TeamCreate, TeamUpdate
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate
from app.core.enhanced_cache import get_cache_manager


@pytest.mark.unit
class TestUserService:
    """Test user service functionality"""

    async def test_create_user_success(self, async_db: AsyncSession):
        """Test successful user creation"""
        user_data = UserCreate(
            email="test@example.com",
            full_name="Test User",
            password="SecurePassword123!"
        )

        user = await create_user(async_db, user_data)

        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.is_verified is False
        assert user.password_hash is not None
        assert user.password_hash != user_data.password

    async def test_create_user_duplicate_email(self, async_db: AsyncSession, test_user: User):
        """Test creating user with duplicate email fails"""
        user_data = UserCreate(
            email=test_user.email,
            full_name="Duplicate User",
            password="SecurePassword123!"
        )

        with pytest.raises(Exception):  # Should raise integrity error
            await create_user(async_db, user_data)

    async def test_authenticate_user_success(self, async_db: AsyncSession, test_user: User):
        """Test successful user authentication"""
        user = await authenticate_user(async_db, test_user.email, "TestSecurePassword123!")

        assert user is not None
        assert user.id == test_user.id

    async def test_authenticate_user_invalid_password(self, async_db: AsyncSession, test_user: User):
        """Test authentication with invalid password"""
        user = await authenticate_user(async_db, test_user.email, "wrongpassword")

        assert user is None

    async def test_authenticate_user_nonexistent(self, async_db: AsyncSession):
        """Test authentication with non-existent user"""
        user = await authenticate_user(async_db, "nonexistent@test.com", "password")

        assert user is None

    async def test_update_user_profile(self, async_db: AsyncSession, test_user: User):
        """Test updating user profile"""
        update_data = UserUpdate(
            full_name="Updated Name",
            department="Updated Department",
            job_title="Updated Title"
        )

        updated_user = await update_user(async_db, test_user.id, update_data)

        assert updated_user.full_name == update_data.full_name
        assert updated_user.department == update_data.department

    async def test_get_user_by_email(self, async_db: AsyncSession, test_user: User):
        """Test getting user by email"""
        user = await UserService.get_by_email(async_db, test_user.email)

        assert user is not None
        assert user.id == test_user.id

    async def test_get_user_by_email_case_insensitive(self, async_db: AsyncSession, test_user: User):
        """Test getting user by email (case insensitive)"""
        user = await UserService.get_by_email(async_db, test_user.email.upper())

        assert user is not None
        assert user.id == test_user.id

    async def test_user_email_verification(self, async_db: AsyncSession, test_user: User):
        """Test user email verification"""
        await UserService.verify_email(async_db, test_user.id)

        await async_db.refresh(test_user)
        assert test_user.is_verified
        assert test_user.email_verified_at is not None

    async def test_user_password_change(self, async_db: AsyncSession, test_user: User):
        """Test changing user password"""
        new_password = "NewSecurePassword123!"
        await UserService.change_password(async_db, test_user.id, new_password)

        # Test new password works
        authenticated_user = await authenticate_user(async_db, test_user.email, new_password)
        assert authenticated_user is not None

    async def test_user_deactivation(self, async_db: AsyncSession, test_user: User):
        """Test user deactivation"""
        await UserService.deactivate_user(async_db, test_user.id)

        await async_db.refresh(test_user)
        assert test_user.is_active is False

    async def test_user_role_change(self, async_db: AsyncSession, test_user: User):
        """Test changing user role"""
        await UserService.change_role(async_db, test_user.id, UserRole.MODERATOR)

        await async_db.refresh(test_user)
        assert test_user.role == UserRole.MODERATOR


@pytest.mark.unit
class TestTeamService:
    """Test team service functionality"""

    async def test_create_team_success(self, async_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test successful team creation"""
        team_data = TeamCreate(
            name="Test Team",
            description="A test team",
            department="Engineering"
        )

        team = await TeamService.create(async_db, team_data, test_user.id, test_organization.id)

        assert team.name == team_data.name
        assert team.created_by_id == test_user.id
        assert team.organization_id == test_organization.id

        # Verify creator is added as admin
        member = await TeamService.get_member(async_db, team.id, test_user.id)
        assert member is not None
        assert member.role == TeamRole.ADMIN

    async def test_add_team_member(self, async_db: AsyncSession, test_team: Team, async_db: AsyncSession, test_utils):
        """Test adding member to team"""
        # Create new user
        new_users = await test_utils.create_test_users(async_db, 1)
        new_user = new_users[0]

        member = await TeamService.add_member(async_db, test_team.id, new_user.id, TeamRole.MEMBER)

        assert member.user_id == new_user.id
        assert member.role == TeamRole.MEMBER
        assert member.joined_at is not None

    async def test_remove_team_member(self, async_db: AsyncSession, test_team: Team, test_user: User):
        """Test removing member from team"""
        # Add member first
        await TeamService.add_member(async_db, test_team.id, test_user.id, TeamRole.MEMBER)

        # Remove member
        success = await TeamService.remove_member(async_db, test_team.id, test_user.id)
        assert success is True

        # Verify member is removed
        member = await TeamService.get_member(async_db, test_team.id, test_user.id)
        assert member is None

    async def test_update_team_member_role(self, async_db: AsyncSession, test_team: Team, test_user: User):
        """Test updating team member role"""
        # Add member
        await TeamService.add_member(async_db, test_team.id, test_user.id, TeamRole.MEMBER)

        # Update role
        updated_member = await TeamService.update_member_role(
            async_db, test_team.id, test_user.id, TeamRole.ADMIN
        )

        assert updated_member.role == TeamRole.ADMIN

    async def test_get_team_members(self, async_db: AsyncSession, test_team: Team):
        """Test getting team members"""
        members = await TeamService.get_members(async_db, test_team.id)

        assert isinstance(members, list)
        assert len(members) >= 1  # At least the creator

    async def test_get_user_teams(self, async_db: AsyncSession, test_user: User, test_team: Team):
        """Test getting user's teams"""
        teams = await TeamService.get_user_teams(async_db, test_user.id)

        assert isinstance(teams, list)
        assert len(teams) >= 1
        assert any(team.id == test_team.id for team in teams)

    async def test_team_statistics(self, async_db: AsyncSession, test_team: Team):
        """Test getting team statistics"""
        stats = await TeamService.get_team_stats(async_db, test_team.id)

        assert "total_members" in stats
        assert "total_assessments" in stats
        assert "completed_assessments" in stats
        assert stats["total_members"] >= 1


@pytest.mark.unit
class TestAssessmentService:
    """Test assessment service functionality"""

    async def test_create_assessment_success(self, async_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test successful assessment creation"""
        assessment_data = AssessmentCreate(
            title="Test Assessment",
            description="A test assessment",
            category=AssessmentCategory.PERSONALITY,
            estimated_duration_minutes=30,
            instructions="Complete this assessment"
        )

        assessment = await AssessmentService.create(
            async_db, assessment_data, test_user.id, test_organization.id
        )

        assert assessment.title == assessment_data.title
        assert assessment.category == assessment_data.category
        assert assessment.created_by_id == test_user.id
        assert assessment.organization_id == test_organization.id
        assert assessment.status == AssessmentStatus.DRAFT

    async def test_publish_assessment(self, async_db: AsyncSession, test_assessment: Assessment):
        """Test publishing assessment"""
        published_assessment = await AssessmentService.publish(async_db, test_assessment.id)

        assert published_assessment.status == AssessmentStatus.PUBLISHED
        assert published_assessment.published_at is not None

    async def test_duplicate_assessment(self, async_db: AsyncSession, test_assessment: Assessment, test_user: User):
        """Test duplicating assessment"""
        duplicate = await AssessmentService.duplicate(
            async_db, test_assessment.id, test_user.id, "Duplicated Assessment"
        )

        assert duplicate.id != test_assessment.id
        assert duplicate.title == "Duplicated Assessment"
        assert duplicate.created_by_id == test_user.id
        assert duplicate.status == AssessmentStatus.DRAFT

    async def test_get_assessment_with_sections(self, async_db: AsyncSession, test_assessment: Assessment):
        """Test getting assessment with sections and questions"""
        assessment = await AssessmentService.get_with_sections(async_db, test_assessment.id)

        assert assessment.id == test_assessment.id
        # Sections and questions would be loaded if they exist

    async def test_assessment_statistics(self, async_db: AsyncSession, test_assessment: Assessment):
        """Test getting assessment statistics"""
        stats = await AssessmentService.get_assessment_stats(async_db, test_assessment.id)

        assert "total_responses" in stats
        assert "completion_rate" in stats
        assert "average_score" in stats
        assert stats["total_responses"] >= 0

    async def test_search_assessments(self, async_db: AsyncSession, test_organization: Organization):
        """Test searching assessments"""
        # Create multiple assessments
        for i in range(5):
            assessment_data = AssessmentCreate(
                title=f"Search Test Assessment {i}",
                description="Test assessment for search",
                category=AssessmentCategory.PERSONALITY,
                estimated_duration_minutes=20
            )
            await AssessmentService.create(async_db, assessment_data, test_organization.created_by_id, test_organization.id)

        # Search for assessments
        results = await AssessmentService.search(async_db, "Search Test", organization_id=test_organization.id)

        assert len(results) >= 5
        for assessment in results:
            assert "Search Test" in assessment.title

    async def test_get_assessments_by_category(self, async_db: AsyncSession, test_organization: Organization):
        """Test getting assessments by category"""
        # Create assessments in different categories
        categories = [AssessmentCategory.PERSONALITY, AssessmentCategory.SKILLS, AssessmentCategory.COGNITIVE]
        for category in categories:
            assessment_data = AssessmentCreate(
                title=f"{category.value} Assessment",
                description=f"Test assessment for {category.value}",
                category=category,
                estimated_duration_minutes=25
            )
            await AssessmentService.create(async_db, assessment_data, test_organization.created_by_id, test_organization.id)

        # Get assessments by category
        personality_assessments = await AssessmentService.get_by_category(
            async_db, AssessmentCategory.PERSONALITY, test_organization.id
        )

        assert len(personality_assessments) >= 1
        for assessment in personality_assessments:
            assert assessment.category == AssessmentCategory.PERSONALITY


@pytest.mark.unit
@pytest.mark.cache
class TestServiceCaching:
    """Test service caching behavior"""

    async def test_user_caching(self, async_db: AsyncSession, test_user: User, mock_cache_manager):
        """Test user caching"""
        cache_key = f"user:{test_user.id}"

        # First call should check cache
        user = await UserService.get_by_id(async_db, test_user.id)

        # Verify cache was checked
        mock_cache_manager.get.assert_called_with(cache_key)

        # Verify cache was set
        mock_cache_manager.set.assert_called()

    async def test_user_cache_invalidation(self, async_db: AsyncSession, test_user: User, mock_cache_manager):
        """Test user cache invalidation"""
        # Update user
        update_data = UserUpdate(full_name="Updated Name")
        await update_user(async_db, test_user.id, update_data)

        # Verify cache was invalidated
        mock_cache_manager.delete.assert_called()

    async def test_team_caching(self, async_db: AsyncSession, test_team: Team, mock_cache_manager):
        """Test team caching"""
        cache_key = f"team:{test_team.id}"

        # Get team
        team = await TeamService.get_by_id(async_db, test_team.id)

        # Verify cache was checked and set
        mock_cache_manager.get.assert_called_with(cache_key)
        mock_cache_manager.set.assert_called()

    async def test_assessment_caching(self, async_db: AsyncSession, test_assessment: Assessment, mock_cache_manager):
        """Test assessment caching"""
        cache_key = f"assessment:{test_assessment.id}"

        # Get assessment
        assessment = await AssessmentService.get_by_id(async_db, test_assessment.id)

        # Verify cache was checked and set
        mock_cache_manager.get.assert_called_with(cache_key)
        mock_cache_manager.set.assert_called()


@pytest.mark.unit
class TestEmailService:
    """Test email service functionality"""

    async def test_send_welcome_email(self, mock_email_service):
        """Test sending welcome email"""
        user_data = {
            "email": "welcome@test.com",
            "full_name": "Welcome User"
        }

        await EmailService.send_welcome_email(user_data)

        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]["to_email"] == user_data["email"]
        assert "welcome" in call_args[1]["subject"].lower()

    async def test_send_verification_email(self, mock_email_service):
        """Test sending verification email"""
        user_data = {
            "email": "verify@test.com",
            "full_name": "Verify User",
            "verification_token": "test_token"
        }

        await EmailService.send_verification_email(user_data)

        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]["to_email"] == user_data["email"]
        assert "verification" in call_args[1]["subject"].lower()

    async def test_send_password_reset_email(self, mock_email_service):
        """Test sending password reset email"""
        user_data = {
            "email": "reset@test.com",
            "full_name": "Reset User",
            "reset_token": "reset_token"
        }

        await EmailService.send_password_reset_email(user_data)

        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]["to_email"] == user_data["email"]
        assert "password reset" in call_args[1]["subject"].lower()

    async def test_send_team_invitation_email(self, mock_email_service):
        """Test sending team invitation email"""
        invitation_data = {
            "email": "invite@test.com",
            "team_name": "Test Team",
            "inviter_name": "Inviter User",
            "invitation_token": "invite_token"
        }

        await EmailService.send_team_invitation(invitation_data)

        mock_email_service.send_email.assert_called_once()
        call_args = mock_email_service.send_email.call_args
        assert call_args[1]["to_email"] == invitation_data["email"]
        assert "invitation" in call_args[1]["subject"].lower()

    async def test_send_bulk_emails(self, mock_email_service):
        """Test sending bulk emails"""
        email_data = {
            "subject": "Bulk Test Email",
            "body": "This is a bulk email",
            "recipients": ["user1@test.com", "user2@test.com", "user3@test.com"]
        }

        result = await EmailService.send_bulk_emails(email_data)

        mock_email_service.send_bulk_emails.assert_called_once()
        assert isinstance(result, dict)


@pytest.mark.unit
class TestServiceTransactions:
    """Test service transaction handling"""

    async def test_rollback_on_error(self, async_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test transaction rollback on error"""
        initial_user_count = await async_db.scalar(select(User).where(User.id == test_user.id))

        # Try to create user with invalid data that should fail
        try:
            invalid_user_data = UserCreate(
                email="",  # Invalid email
                full_name="Invalid User",
                password="password"
            )
            await create_user(async_db, invalid_user_data)
        except Exception:
            pass  # Expected to fail

        # Verify no partial data was created
        final_user_count = await async_db.scalar(select(User).where(User.id == test_user.id))
        assert initial_user_count == final_user_count

    async def test_nested_transaction_rollback(self, async_db: AsyncSession, test_team: Team):
        """Test nested transaction rollback"""
        # Start a transaction
        async with async_db.begin():
            # Add team member
            await TeamService.add_member(async_db, test_team.id, test_team.created_by_id, TeamRole.MEMBER)

            # Simulate an error that should rollback
            raise Exception("Simulated error")

        # Verify member was not added
        member = await TeamService.get_member(async_db, test_team.id, test_team.created_by_id)
        assert member is None or member.role != TeamRole.MEMBER


@pytest.mark.unit
@pytest.mark.performance
class TestServicePerformance:
    """Test service performance"""

    async def test_user_creation_performance(self, async_db: AsyncSession, performance_timer):
        """Test user creation performance"""
        with performance_timer():
            user_data = UserCreate(
                email="perf@test.com",
                full_name="Performance User",
                password="SecurePassword123!"
            )
            await create_user(async_db, user_data)

    async def test_bulk_user_creation_performance(self, async_db: AsyncSession, performance_timer):
        """Test bulk user creation performance"""
        with performance_timer():
            tasks = []
            for i in range(10):
                user_data = UserCreate(
                    email=f"bulk{i}@test.com",
                    full_name=f"Bulk User {i}",
                    password="SecurePassword123!"
                )
                tasks.append(create_user(async_db, user_data))

            await asyncio.gather(*tasks)

    async def test_assessment_search_performance(self, async_db: AsyncSession, test_organization: Organization, performance_timer):
        """Test assessment search performance"""
        # Create multiple assessments first
        for i in range(20):
            assessment_data = AssessmentCreate(
                title=f"Search Performance Test {i}",
                description="Performance test assessment",
                category=AssessmentCategory.PERSONALITY,
                estimated_duration_minutes=15
            )
            await AssessmentService.create(async_db, assessment_data, test_organization.created_by_id, test_organization.id)

        with performance_timer():
            results = await AssessmentService.search(async_db, "Search Performance Test", test_organization.id)
            assert len(results) >= 20


@pytest.mark.unit
class TestServiceValidation:
    """Test service input validation"""

    async def test_user_email_validation(self, async_db: AsyncSession):
        """Test user email validation"""
        invalid_emails = [
            "invalid-email",
            "@test.com",
            "test@",
            "test.test.com",
            ""
        ]

        for email in invalid_emails:
            with pytest.raises(Exception):
                user_data = UserCreate(
                    email=email,
                    full_name="Invalid Email User",
                    password="SecurePassword123!"
                )
                await create_user(async_db, user_data)

    async def test_password_validation(self, async_db: AsyncSession):
        """Test password validation"""
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "weak",
            ""
        ]

        for password in weak_passwords:
            with pytest.raises(Exception):
                user_data = UserCreate(
                    email="weak@test.com",
                    full_name="Weak Password User",
                    password=password
                )
                await create_user(async_db, user_data)

    async def test_assessment_title_validation(self, async_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test assessment title validation"""
        invalid_titles = [
            "",
            "a" * 301,  # Too long
            "   "  # Only whitespace
        ]

        for title in invalid_titles:
            with pytest.raises(Exception):
                assessment_data = AssessmentCreate(
                    title=title,
                    description="Test assessment",
                    category=AssessmentCategory.PERSONALITY,
                    estimated_duration_minutes=30
                )
                await AssessmentService.create(async_db, assessment_data, test_user.id, test_organization.id)


@pytest.mark.unit
@pytest.mark.slow
class TestServiceIntegration:
    """Test service integration scenarios"""

    async def test_complete_user_onboarding(self, async_db: AsyncSession, test_organization: Organization, mock_email_service):
        """Test complete user onboarding flow"""
        # 1. Create user
        user_data = UserCreate(
            email="onboard@test.com",
            full_name="Onboarding User",
            password="SecurePassword123!"
        )
        user = await create_user(async_db, user_data)

        # 2. Create team for user
        team_data = TeamCreate(
            name="Onboarding Team",
            description="Team for onboarding test"
        )
        team = await TeamService.create(async_db, team_data, user.id, test_organization.id)

        # 3. Create assessment
        assessment_data = AssessmentCreate(
            title="Onboarding Assessment",
            description="Assessment for onboarding",
            category=AssessmentCategory.PERSONALITY,
            estimated_duration_minutes=20
        )
        assessment = await AssessmentService.create(async_db, assessment_data, user.id, test_organization.id)

        # 4. Verify all entities were created
        assert user.id is not None
        assert team.id is not None
        assert assessment.id is not None

        # 5. Verify relationships
        team_member = await TeamService.get_member(async_db, team.id, user.id)
        assert team_member is not None
        assert team_member.role == TeamRole.ADMIN

        # 6. Send welcome email
        await EmailService.send_welcome_email({
            "email": user.email,
            "full_name": user.full_name
        })
        mock_email_service.send_email.assert_called()

    async def test_team_assignment_workflow(self, async_db: AsyncSession, test_organization: Organization, test_utils):
        """Test team assignment workflow"""
        # 1. Create admin user
        admin_users = await test_utils.create_test_users(async_db, 1, UserRole.ADMIN)
        admin = admin_users[0]

        # 2. Create regular users
        users = await test_utils.create_test_users(async_db, 5)

        # 3. Create team
        team_data = TeamCreate(
            name="Workflow Test Team",
            description="Team for workflow testing"
        )
        team = await TeamService.create(async_db, team_data, admin.id, test_organization.id)

        # 4. Add all users to team
        for user in users:
            await TeamService.add_member(async_db, team.id, user.id, TeamRole.MEMBER)

        # 5. Verify team composition
        members = await TeamService.get_members(async_db, team.id)
        assert len(members) == 6  # 1 admin + 5 members

        # 6. Get team statistics
        stats = await TeamService.get_team_stats(async_db, team.id)
        assert stats["total_members"] == 6

    async def test_assessment_lifecycle(self, async_db: AsyncSession, test_user: User, test_organization: Organization):
        """Test complete assessment lifecycle"""
        # 1. Create assessment
        assessment_data = AssessmentCreate(
            title="Lifecycle Test Assessment",
            description="Assessment for lifecycle testing",
            category=AssessmentCategory.PERSONALITY,
            estimated_duration_minutes=25
        )
        assessment = await AssessmentService.create(async_db, assessment_data, test_user.id, test_organization.id)

        # 2. Verify draft status
        assert assessment.status == AssessmentStatus.DRAFT

        # 3. Publish assessment
        published_assessment = await AssessmentService.publish(async_db, assessment.id)
        assert published_assessment.status == AssessmentStatus.PUBLISHED

        # 4. Update assessment (should create new version)
        update_data = AssessmentUpdate(
            description="Updated description"
        )
        updated_assessment = await AssessmentService.update(async_db, assessment.id, update_data)

        # 5. Archive assessment
        archived_assessment = await AssessmentService.archive(async_db, assessment.id)
        assert archived_assessment.status == AssessmentStatus.ARCHIVED

        # 6. Get assessment statistics
        stats = await AssessmentService.get_assessment_stats(async_db, assessment.id)
        assert "total_responses" in stats
