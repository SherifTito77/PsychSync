"""
Database Integration Tests with Actual Database Connections
Critical for testing database functionality, schema validation, and data integrity
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment before imports
os.environ['ENVIRONMENT'] = 'testing'
os.environ['TESTING'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'  # Use in-memory SQLite

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
from httpx import AsyncClient
from app.main import app
from app.core.database import get_async_db, Base
from app.db.models.user import User, UserRole
from app.db.models.organization import Organization
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
from app.core.config import settings


class TestDatabaseIntegration:
    """Comprehensive database integration tests"""

    @pytest.fixture(scope="class")
    async def test_db(self) -> AsyncGenerator[AsyncSession, None]:
        """Create test database session"""
        # Create in-memory SQLite database
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_maker() as session:
            yield session

        # Clean up
        await engine.dispose()

    @pytest.fixture
    async def client(self, test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
        """Create test client with database override"""
        app.dependency_overrides[get_async_db] = lambda: test_db

        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

        # Clean up
        app.dependency_overrides.clear()

    # TODO(human): Implement comprehensive database schema tests
    async def test_database_schema_creation(self, test_db: AsyncSession):
        """Test that database schema is created correctly"""
        # Test User table
        result = await test_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        user_table_exists = result.fetchone() is not None
        assert user_table_exists, "Users table should exist"

        # Test Organization table
        result = await test_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organizations'")
        org_table_exists = result.fetchone() is not None
        assert org_table_exists, "Organizations table should exist"

        # Test Team table
        result = await test_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teams'")
        team_table_exists = result.fetchone() is not None
        assert team_table_exists, "Teams table should exist"

        # Test Assessment table
        result = await test_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assessments'")
        assessment_table_exists = result.fetchone() is not None
        assert assessment_table_exists, "Assessments table should exist"

    # TODO(human): Implement user CRUD operations tests
    async def test_user_crud_operations(self, test_db: AsyncSession):
        """Test User CRUD operations"""
        # Create user
        user = User(
            email="test@example.com",
            full_name="Test User",
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None, "User should have ID after creation"
        assert user.email == "test@example.com", "User email should be preserved"
        assert user.created_at is not None, "User should have creation timestamp"

        # Read user
        result = await test_db.get(User, user.id)
        assert result is not None, "User should be retrievable"
        assert result.email == "test@example.com", "Retrieved user email should match"

        # Update user
        user.full_name = "Updated Test User"
        await test_db.commit()
        await test_db.refresh(user)
        assert user.full_name == "Updated Test User", "User name should be updated"

        # Delete user
        await test_db.delete(user)
        await test_db.commit()

        deleted_user = await test_db.get(User, user.id)
        assert deleted_user is None, "User should be deleted"

    # TODO(human): Implement organization relationship tests
    async def test_organization_relationships(self, test_db: AsyncSession):
        """Test organization-user relationships"""
        # Create organization
        org = Organization(
            name="Test Organization",
            description="Test Description",
            is_active=True
        )
        test_db.add(org)
        await test_db.commit()
        await test_db.refresh(org)

        # Create user in organization
        user = User(
            email="user@testorg.com",
            full_name="Org User",
            role=UserRole.USER,
            organization_id=org.id,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Test relationship
        assert user.organization_id == org.id, "User should belong to organization"

        # Test reverse relationship (if implemented)
        retrieved_org = await test_db.get(Organization, org.id)
        # Note: This would require relationship setup in models

    # TODO(human): Implement team membership tests
    async def test_team_membership_functionality(self, test_db: AsyncSession):
        """Test team creation and membership"""
        # Create organization
        org = Organization(name="Team Test Org", is_active=True)
        test_db.add(org)
        await test_db.commit()

        # Create team
        team = Team(
            name="Test Team",
            description="Test team description",
            organization_id=org.id,
            is_active=True
        )
        test_db.add(team)
        await test_db.commit()
        await test_db.refresh(team)

        # Create team members
        user1 = User(
            email="member1@test.com",
            full_name="Team Member 1",
            role=UserRole.USER,
            organization_id=org.id,
            is_active=True
        )
        user2 = User(
            email="member2@test.com",
            full_name="Team Member 2",
            role=UserRole.USER,
            organization_id=org.id,
            is_active=True
        )

        test_db.add_all([user1, user2])
        await test_db.commit()
        await test_db.refresh(user1)
        await test_db.refresh(user2)

        # Create team memberships
        membership1 = TeamMember(
            team_id=team.id,
            user_id=user1.id,
            role=TeamRole.MEMBER,
            organization_id=org.id
        )
        membership2 = TeamMember(
            team_id=team.id,
            user_id=user2.id,
            role=TeamRole.ADMIN,
            organization_id=org.id
        )

        test_db.add_all([membership1, membership2])
        await test_db.commit()
        await test_db.refresh(membership1)
        await test_db.refresh(membership2)

        # Verify team membership
        assert membership1.team_id == team.id, "First user should be team member"
        assert membership2.team_id == team.id, "Second user should be team member"
        assert membership1.role == TeamRole.MEMBER, "First user should have member role"
        assert membership2.role == TeamRole.ADMIN, "Second user should have admin role"

    # TODO(human): Implement assessment creation and response tests
    async def test_assessment_creation_and_responses(self, test_db: AsyncSession):
        """Test assessment creation and response functionality"""
        # Create organization and user
        org = Organization(name="Assessment Test Org", is_active=True)
        test_db.add(org)
        await test_db.commit()

        user = User(
            email="assessor@test.com",
            full_name="Assessment User",
            role=UserRole.USER,
            organization_id=org.id,
            is_active=True
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create assessment
        assessment = Assessment(
            title="Test Assessment",
            description="Test assessment description",
            category=AssessmentCategory.PERSONALITY,
            status=AssessmentStatus.DRAFT,
            organization_id=org.id,
            created_by_id=user.id
        )
        test_db.add(assessment)
        await test_db.commit()
        await test_db.refresh(assessment)

        # Verify assessment creation
        assert assessment.id is not None, "Assessment should have ID"
        assert assessment.title == "Test Assessment", "Assessment title should be preserved"
        assert assessment.organization_id == org.id, "Assessment should belong to organization"
        assert assessment.created_by_id == user.id, "Assessment should have creator"

        # Test assessment status transitions
        assessment.status = AssessmentStatus.PUBLISHED
        await test_db.commit()
        await test_db.refresh(assessment)
        assert assessment.status == AssessmentStatus.PUBLISHED, "Assessment status should update"

    # TODO(human): Implement database constraint validation tests
    async def test_database_constraints(self, test_db: AsyncSession):
        """Test database constraints are enforced"""
        # Test unique email constraint
        user1 = User(
            email="duplicate@test.com",
            full_name="User 1",
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user1)
        await test_db.commit()

        # Try to create user with same email
        user2 = User(
            email="duplicate@test.com",  # Same email
            full_name="User 2",
            role=UserRole.USER,
            is_active=True
        )
        test_db.add(user2)

        # This should fail due to unique constraint
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            await test_db.commit()

        await test_db.rollback()

        # Test foreign key constraints
        # Try to create user with non-existent organization
        invalid_user = User(
            email="invalid@test.com",
            full_name="Invalid User",
            role=UserRole.USER,
            organization_id=99999,  # Non-existent ID
            is_active=True
        )
        test_db.add(invalid_user)

        # This should fail due to foreign key constraint
        with pytest.raises(Exception):  # Should raise IntegrityError or similar
            await test_db.commit()

    # TODO(human): Implement database performance tests
    async def test_database_performance(self, test_db: AsyncSession):
        """Test database performance with multiple operations"""
        import time

        # Test bulk insert performance
        start_time = time.time()

        users = []
        for i in range(100):
            user = User(
                email=f"user{i}@performance.com",
                full_name=f"Performance User {i}",
                role=UserRole.USER,
                is_active=True
            )
            users.append(user)

        test_db.add_all(users)
        await test_db.commit()

        bulk_insert_time = time.time() - start_time
        assert bulk_insert_time < 5.0, f"Bulk insert took too long: {bulk_insert_time}s"

        # Test query performance
        start_time = time.time()

        result = await test_db.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
        count = result.scalar()

        query_time = time.time() - start_time
        assert query_time < 1.0, f"Query took too long: {query_time}s"
        assert count >= 100, "Should have inserted at least 100 users"

    # TODO(human): Implement database transaction rollback tests
    async def test_database_transaction_rollback(self, test_db: AsyncSession):
        """Test database transaction rollback functionality"""
        # Start with known state
        result = await test_db.execute("SELECT COUNT(*) FROM users")
        initial_count = result.scalar()

        try:
            # Create some users
            for i in range(5):
                user = User(
                    email=f"rollback_user{i}@test.com",
                    full_name=f"Rollback User {i}",
                    role=UserRole.USER,
                    is_active=True
                )
                test_db.add(user)

            # Force an error
            raise ValueError("Intentional error for rollback test")

        except ValueError:
            # Rollback should happen automatically
            await test_db.rollback()

        # Verify no users were added
        result = await test_db.execute("SELECT COUNT(*) FROM users")
        final_count = result.scalar()

        assert final_count == initial_count, "Rollback should have restored initial state"

    # TODO(human): Implement database connection resilience tests
    async def test_database_connection_resilience(self, test_db: AsyncSession):
        """Test database connection handling"""
        # Test multiple concurrent connections
        async def concurrent_query():
            result = await test_db.execute("SELECT 1")
            return result.scalar()

        # Run multiple concurrent queries
        tasks = [concurrent_query() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(r == 1 for r in results), "All concurrent queries should return 1"

        # Test connection after error
        try:
            # Intentionally invalid query
            await test_db.execute("SELECT * FROM non_existent_table")
        except Exception:
            pass  # Expected to fail

        # Connection should still work
        result = await test_db.execute("SELECT 1")
        assert result.scalar() == 1, "Connection should recover after error"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
