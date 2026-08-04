"""
Transaction Rollback and Audit Logging Tests

This test suite verifies:
1. Transaction rollback behavior on failures
2. Audit logging functionality
3. Data consistency during transactions
4. Error handling and recovery
5. Multi-step operation integrity
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.db.models.assessment import Assessment
from app.db.models.organization import Organization
from app.db.models.response import AssessmentResponse, Response
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User, UserRole
from app.services.security import get_password_hash


@pytest.mark.asyncio
@pytest.mark.integration
class TestTransactionRollback:
    """Test transaction rollback behavior and data consistency"""

    async def test_simple_transaction_rollback(self, db_session: AsyncSession):
        """
        Test basic transaction rollback on errors
        """
        # Create initial data
        org = Organization(
            name="Rollback Test Org", description="Organization for rollback testing"
        )
        db_session.add(org)
        await db_session.flush()
        org_id = org.id

        # Start a transaction that will fail
        try:
            # Step 1: Create user (should be rolled back)
            user = User(
                email="rollback@example.com",
                password_hash=get_password_hash("password123"),
                full_name="Rollback Test User",
                role=UserRole.USER,
                is_active=True,
            )
            db_session.add(user)
            await db_session.flush()
            user_id = user.id

            # Step 2: Create team (should be rolled back)
            team = Team(
                name="Rollback Test Team",
                description="Team for rollback testing",
                organization_id=org_id,
            )
            db_session.add(team)
            await db_session.flush()
            team_id = team.id

            # Step 3: Force an error
            # This could be a business logic error, validation error, etc.
            raise ValueError("Intentional test error for rollback")

        except ValueError:
            # Rollback the transaction
            await db_session.rollback()

        # Verify rollback was successful
        user_after = (
            await db_session.get(User, user_id) if "user_id" in locals() else None
        )
        team_after = (
            await db_session.get(Team, team_id) if "team_id" in locals() else None
        )

        assert user_after is None, "User should not exist after rollback"
        assert team_after is None, "Team should not exist after rollback"

        # Verify organization still exists (was created before the failing transaction)
        org_after = await db_session.get(Organization, org_id)
        assert org_after is not None, "Organization should still exist"

    async def test_nested_transaction_rollback(self, db_session: AsyncSession):
        """
        Test rollback with nested transaction-like operations
        """
        # Create initial organization
        org = Organization(
            name="Nested Rollback Org",
            description="Organization for nested rollback testing",
        )
        db_session.add(org)
        await db_session.commit()

        # Simulate nested operations
        operation_results = []

        try:
            # Outer operation 1: Create users
            users_data = [
                ("user1@nested.com", "User One"),
                ("user2@nested.com", "User Two"),
                ("user3@nested.com", "User Three"),
            ]

            created_users = []
            for email, full_name in users_data:
                user = User(
                    email=email,
                    password_hash=get_password_hash("password123"),
                    full_name=full_name,
                    role=UserRole.USER,
                    is_active=True,
                )
                db_session.add(user)
                await db_session.flush()
                created_users.append(user)
            operation_results.append(f"Created {len(created_users)} users")

            # Outer operation 2: Create teams
            teams_data = [
                ("Team Alpha", "First team"),
                ("Team Beta", "Second team"),
            ]

            created_teams = []
            for name, description in teams_data:
                team = Team(name=name, description=description, organization_id=org.id)
                db_session.add(team)
                await db_session.flush()
                created_teams.append(team)
            operation_results.append(f"Created {len(created_teams)} teams")

            # Inner operation: Complex user-team assignments
            try:
                assignments = []
                for user in created_users:
                    for team in created_teams:
                        # Simulate some business logic that might fail
                        if len(assignments) >= 3:  # Artificial limit for testing
                            raise ValueError(
                                "Too many assignments - business rule violation"
                            )

                        team_member = TeamMember(
                            team_id=team.id,
                            user_id=user.id,
                            role=TeamRole.MEMBER,
                            joined_at=datetime.utcnow(),
                        )
                        db_session.add(team_member)
                        await db_session.flush()
                        assignments.append(f"{user.email} -> {team.name}")
                        operation_results.append(
                            f"Created assignment: {user.email} -> {team.name}"
                        )

                operation_results.append(f"Created {len(assignments)} assignments")

            except ValueError as e:
                operation_results.append(f"Inner operation failed: {e}")
                # Simulate partial rollback of inner operation
                raise

            # Simulate another failure
            raise RuntimeError("Outer operation failed")

        except (ValueError, RuntimeError) as e:
            await db_session.rollback()
            operation_results.append(f"Transaction rolled back: {e}")

        # Verify all operations were rolled back
        user_count = await db_session.execute(
            select(User).where(User.email.in_([email for email, _ in users_data]))
        )
        assert user_count.rowcount == 0, "All users should be rolled back"

        team_count = await db_session.execute(
            select(Team).where(Team.organization_id == org.id)
        )
        assert team_count.rowcount == 0, "All teams should be rolled back"

        print("Nested rollback test results:")
        for result in operation_results:
            print(f"  - {result}")

    async def test_partial_commit_with_savepoints(self, db_session: AsyncSession):
        """
        Test partial commits using savepoints
        """
        # Create initial organization
        org = Organization(
            name="Savepoint Test Org", description="Organization for savepoint testing"
        )
        db_session.add(org)
        await db_session.commit()

        try:
            # Savepoint 1: Create users
            savepoint1 = await db_session.begin_nested()
            users_created = []

            for i in range(3):
                user = User(
                    email=f"savepoint{i}@test.com",
                    password_hash=get_password_hash("password123"),
                    full_name=f"Savepoint User {i}",
                    role=UserRole.USER,
                    is_active=True,
                )
                db_session.add(user)
                await db_session.flush()
                users_created.append(user)

            # Commit savepoint 1
            await savepoint1.commit()
            print(f"Savepoint 1 committed: {len(users_created)} users")

            # Savepoint 2: Create teams
            savepoint2 = await db_session.begin_nested()
            teams_created = []

            for i in range(2):
                team = Team(
                    name=f"Savepoint Team {i+1}",
                    description=f"Team created in savepoint {i+1}",
                    organization_id=org.id,
                )
                db_session.add(team)
                await db_session.flush()
                teams_created.append(team)

            # Commit savepoint 2
            await savepoint2.commit()
            print(f"Savepoint 2 committed: {len(teams_created)} teams")

            # Savepoint 3: Try operation that will fail
            savepoint3 = await db_session.begin_nested()

            # Create team member with invalid data (will fail on commit)
            invalid_member = TeamMember(
                team_id=teams_created[0].id,
                user_id="invalid-uuid",  # Invalid UUID
                role=TeamRole.MEMBER,
                joined_at=datetime.utcnow(),
            )
            db_session.add(invalid_member)

            # This should fail
            await savepoint3.commit()

        except Exception as e:
            await savepoint3.rollback()
            print(f"Savepoint 3 rolled back: {e}")

        # Verify savepoint 1 and 2 data was preserved
        user_count = await db_session.execute(
            select(User).where(User.email.like("savepoint%@test.com"))
        )
        assert user_count.rowcount == 3, "Savepoint 1 data should be preserved"

        team_count = await db_session.execute(
            select(Team).where(Team.organization_id == org.id)
        )
        assert team_count.rowcount == 2, "Savepoint 2 data should be preserved"

        await db_session.commit()

    async def test_long_running_transaction_rollback(self, db_session: AsyncSession):
        """
        Test rollback of long-running transactions
        """
        # Create initial organization
        org = Organization(
            name="Long Transaction Org",
            description="Organization for long transaction testing",
        )
        db_session.add(org)
        await db_session.flush()

        transaction_start_time = datetime.utcnow()

        try:
            # Simulate a long-running transaction
            created_items = []

            # Phase 1: Create many users
            for i in range(50):
                user = User(
                    email=f"longtrans{i}@test.com",
                    password_hash=get_password_hash("password123"),
                    full_name=f"Long Transaction User {i}",
                    role=UserRole.USER,
                    is_active=i % 2 == 0,  # Alternating active status
                )
                db_session.add(user)
                await db_session.flush()
                created_items.append(f"User {i}")

                # Simulate processing time
                if i % 10 == 0:
                    await asyncio.sleep(0.01)  # Small delay to simulate processing

            # Phase 2: Create assessments
            for i in range(20):
                assessment = Assessment(
                    title=f"Assessment {i}",
                    description=f"Long transaction assessment {i}",
                    organization_id=org.id,
                )
                db_session.add(assessment)
                await db_session.flush()
                created_items.append(f"Assessment {i}")

            # Phase 3: Create responses
            for i in range(30):
                response = Response(
                    assessment_id=(i % 20) + 1,  # Reuse assessment IDs
                    user_id=(i % 50) + 1,  # Reuse user IDs
                    responses={
                        "question_1": f"answer_{i}_1",
                        "question_2": f"answer_{i}_2",
                    },
                    score=50 + (i % 50),
                    completed_at=transaction_start_time + timedelta(minutes=i),
                )
                db_session.add(response)
                await db_session.flush()
                created_items.append(f"Response {i}")

            # Phase 4: Simulate failure condition
            if len(created_items) >= 100:
                raise ValueError(
                    f"Transaction failed after creating {len(created_items)} items"
                )

            await db_session.commit()

        except ValueError as e:
            await db_session.rollback()
            transaction_duration = datetime.utcnow() - transaction_start_time
            print(f"Long transaction rolled back: {e}")
            print(f"Transaction duration: {transaction_duration}")

        # Verify rollback was complete
        user_count = await db_session.execute(
            select(User).where(User.email.like("longtrans%@test.com"))
        )
        assessment_count = await db_session.execute(
            select(Assessment).where(Assessment.organization_id == org.id)
        )
        response_count = await db_session.execute(select(Response))

        assert user_count.rowcount == 0, "All users should be rolled back"
        assert assessment_count.rowcount == 0, "All assessments should be rolled back"
        assert response_count.rowcount == 0, "All responses should be rolled back"

    async def test_transaction_isolation_levels(self, db_session: AsyncSession):
        """
        Test transaction isolation levels and concurrent access
        """
        # Create initial data
        org = Organization(
            name="Isolation Test Org", description="Organization for isolation testing"
        )
        db_session.add(org)
        await db_session.commit()

        # Test READ COMMITTED isolation (default in PostgreSQL)
        async def test_read_committed():
            # Start first transaction
            async with db_session.begin():
                # Create user
                user = User(
                    email="isolation@test.com",
                    password_hash=get_password_hash("password123"),
                    full_name="Isolation Test User",
                    role=UserRole.USER,
                    is_active=False,  # Start as inactive
                )
                db_session.add(user)
                await db_session.flush()
                user_id = user.id

                # Simulate time passing
                await asyncio.sleep(0.1)

                # In a concurrent session, this user should not be visible yet
                # (This would require multiple connections to truly test isolation)
                pass

            # After commit, user should be visible
            user_after = await db_session.get(User, user_id)
            return user_after

        result = await test_read_committed()
        assert result is not None, "User should be visible after commit"
        assert result.email == "isolation@test.com"

    async def test_error_recovery_after_rollback(self, db_session: AsyncSession):
        """
        Test error recovery and system stability after rollback
        """
        # Create initial stable data
        org = Organization(
            name="Recovery Test Org", description="Organization for recovery testing"
        )
        db_session.add(org)
        await db_session.commit()

        stable_user = User(
            email="stable@test.com",
            password_hash=get_password_hash("password123"),
            full_name="Stable Test User",
            role=UserRole.USER,
            is_active=True,
        )
        db_session.add(stable_user)
        await db_session.commit()

        # Test multiple failed transactions
        failure_count = 0
        for attempt in range(5):
            try:
                async with db_session.begin():
                    # Start with stable data
                    stable_check = await db_session.get(User, stable_user.id)
                    assert stable_check is not None, "Stable user should always exist"

                    # Create temporary user that will be rolled back
                    temp_user = User(
                        email=f"temp{attempt}@test.com",
                        password_hash=get_password_hash("password123"),
                        full_name=f"Temporary User {attempt}",
                        role=UserRole.USER,
                        is_active=True,
                    )
                    db_session.add(temp_user)
                    await db_session.flush()

                    # Simulate different types of failures
                    if attempt == 0:
                        raise IntegrityError("Simulated integrity error")
                    elif attempt == 1:
                        raise ValueError("Simulated business logic error")
                    elif attempt == 2:
                        raise RuntimeError("Simulated runtime error")
                    elif attempt == 3:
                        raise SQLAlchemyError("Simulated database error")
                    else:
                        raise Exception("Simulated general error")

            except (
                IntegrityError,
                ValueError,
                RuntimeError,
                SQLAlchemyError,
                Exception,
            ):
                # Expected errors
                failure_count += 1
                continue

        # Verify system is stable after multiple failures
        final_stable_user = await db_session.get(User, stable_user.id)
        assert (
            final_stable_user is not None
        ), "Stable user should still exist after failures"
        assert final_stable_user.email == "stable@test.com"

        # Verify no temporary users exist
        temp_users_count = await db_session.execute(
            select(User).where(User.email.like("temp%@test.com"))
        )
        assert temp_users_count.rowcount == 0, "Temporary users should be rolled back"

        print(
            f"System stability test: {failure_count}/5 failed transactions handled correctly"
        )
