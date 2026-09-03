"""
Database Transaction Race Condition Tests

Tests to verify database-level race condition handling:
1. Concurrent team member additions (UNIQUE constraint enforcement)
2. Concurrent assessment response updates (lost updates prevention)
3. Concurrent team creation with same name (UNIQUE constraint)
4. Concurrent user profile updates (optimistic locking)
5. Transaction isolation level verification (READ_COMMITTED)

These tests verify that the database correctly handles concurrent operations
to prevent data corruption, lost updates, and race conditions.
"""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment, AssessmentResponse
from app.db.models.organization import Organization
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User

# ============================================================================
# Test 1: Concurrent Team Member Additions
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
async def test_concurrent_team_member_additions_no_duplicates(db_session: AsyncSession):
    """
    Test Case: TC_TEAM_002 - Concurrent Team Member Additions

    Verify that when multiple team members are added to a team concurrently,
    the UNIQUE constraint prevents duplicate records.

    Race Condition: Multiple concurrent INSERTs for the same (team_id, user_id)
    could create duplicate team members.

    Fix: Database UNIQUE constraint on (team_id, user_id) prevents duplicates.
    Application handles IntegrityError gracefully.
    """
    # Arrange - Create organization and team
    org = Organization(
        id=uuid4(),
        name="Test Organization for Concurrent Members",
        slug="test-concurrent-org",
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test Concurrent Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    # Create test users
    users = []
    for i in range(10):
        user = User(
            email=f"member{i:03d}@psychsync.test",
            hashed_password="hash",
            full_name=f"Test Member {i}",
        )
        db_session.add(user)
        users.append(user)

    await db_session.flush()

    # Act - Add all members concurrently (each user twice to test duplicates)
    async def add_member(team_id, user_id, role):
        """Add a team member"""
        try:
            member = TeamMember(team_id=team_id, user_id=user_id, role=role)
            db_session.add(member)
            await db_session.commit()
            await db_session.refresh(member)
            return {"success": True, "member_id": member.id}
        except IntegrityError as e:
            await db_session.rollback()
            return {"success": False, "error": str(e)}

    # For each user, add them twice concurrently (to test duplicate prevention)
    tasks = []
    for user in users:
        # Try adding same user twice
        tasks.append(add_member(team.id, user.id, TeamRole.MEMBER))
        tasks.append(add_member(team.id, user.id, TeamRole.MEMBER))

    # Execute all additions concurrently
    results = await asyncio.gather(*tasks)

    # Assert - No duplicate team members
    success_count = sum(1 for r in results if r["success"])
    failure_count = sum(1 for r in results if not r["success"])

    # Should have 10 successes (one per user) and 10 failures (duplicates)
    assert success_count == 10, f"Expected 10 successful additions, got {success_count}"
    assert failure_count == 10, f"Expected 10 duplicate failures, got {failure_count}"

    # Verify database state
    result = await db_session.execute(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
    )
    member_count = result.scalar_one()

    assert member_count == 10, f"Expected 10 unique team members, got {member_count}"

    # Verify no duplicates
    result = await db_session.execute(
        select(TeamMember.user_id, func.count(TeamMember.id))
        .where(TeamMember.team_id == team.id)
        .group_by(TeamMember.user_id)
        .having(func.count(TeamMember.id) > 1)
    )
    duplicates = result.all()

    assert len(duplicates) == 0, f"Found duplicate team members: {duplicates}"

    # Cleanup
    await db_session.execute(delete(TeamMember).where(TeamMember.team_id == team.id))
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(
        delete(User).where(User.email.like("member%@psychsync.test"))
    )
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
async def test_concurrent_team_member_additions_multiple_admins(
    db_session: AsyncSession,
):
    """
    Test concurrent team member additions by multiple admins.

    Simulates 3 admins adding different members to the same team simultaneously.
    Verifies all additions succeed without lost updates.
    """
    # Arrange - Create organization and team
    org = Organization(
        id=uuid4(),
        name="Test Organization for Multi-Admin",
        slug="test-multi-admin-org",
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test Multi-Admin Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    # Create 10 test users
    users = []
    for i in range(10):
        user = User(
            email=f"concurrent_member{i:03d}@psychsync.test",
            hashed_password="hash",
            full_name=f"Concurrent Member {i}",
        )
        db_session.add(user)
        users.append(user)

    await db_session.flush()

    # Act - Divide users among 3 "admins" and add concurrently
    async def add_members_batch(user_batch):
        """Add a batch of team members"""
        members = []
        for user in user_batch:
            member = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.MEMBER)
            db_session.add(member)
            members.append(member)

        await db_session.commit()
        return len(members)

    # Divide users: admin1 adds 4, admin2 adds 3, admin3 adds 3
    tasks = [
        add_members_batch(users[0:4]),  # Admin 1: 4 users
        add_members_batch(users[4:7]),  # Admin 2: 3 users
        add_members_batch(users[7:10]),  # Admin 3: 3 users
    ]

    # Execute all batches concurrently
    results = await asyncio.gather(*tasks)

    # Assert - All members added successfully
    total_added = sum(results)
    assert total_added == 10, f"Expected 10 total additions, got {total_added}"

    # Verify database state
    result = await db_session.execute(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
    )
    member_count = result.scalar_one()

    assert member_count == 10, f"Expected 10 team members, got {member_count}"

    # Verify all users are present
    result = await db_session.execute(
        select(TeamMember).where(TeamMember.team_id == team.id)
    )
    members = result.scalars().all()

    member_user_ids = {m.user_id for m in members}
    expected_user_ids = {u.id for u in users}

    assert member_user_ids == expected_user_ids, "Not all users were added to team"

    # Cleanup
    await db_session.execute(delete(TeamMember).where(TeamMember.team_id == team.id))
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(
        delete(User).where(User.email.like("concurrent_member%@psychsync.test"))
    )
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


# ============================================================================
# Test 2: Concurrent Assessment Response Updates
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.assessment
@pytest.mark.concurrent
async def test_concurrent_assessment_response_updates(db_session: AsyncSession):
    """
    Test concurrent updates to the same assessment response.

    Race Condition: Multiple concurrent UPDATEs to the same assessment response
    could cause lost updates (last write wins).

    Fix: Use SELECT ... FOR UPDATE to lock the row during updates, or
    use version-based optimistic locking.
    """
    # Arrange - Create user and assessment response
    user = User(
        email="concurrent_assessment_user@psychsync.test",
        hashed_password="hash",
        full_name="Concurrent Assessment User",
    )
    db_session.add(user)
    await db_session.flush()

    org = Organization(
        id=uuid4(), name="Test Organization for Assessment", slug="test-assessment-org"
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test Assessment Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    assessment = Assessment(
        id=uuid4(), name="Test Assessment", framework_code="MBTI", team_id=team.id
    )
    db_session.add(assessment)
    await db_session.flush()

    # Create initial assessment response
    response = AssessmentResponse(
        id=uuid4(),
        assessment_id=assessment.id,
        user_id=user.id,
        responses={"question_1": "A", "question_2": "B"},
        score=0,
    )
    db_session.add(response)
    await db_session.commit()
    await db_session.refresh(response)

    # Act - 10 concurrent updates to the same response
    async def update_response(response_id, question_num, answer):
        """Update assessment response with row locking"""
        async with db_session.begin():
            # Use SELECT FOR UPDATE to lock the row
            result = await db_session.execute(
                select(AssessmentResponse)
                .where(AssessmentResponse.id == response_id)
                .with_for_update()
            )
            resp = result.scalar_one()

            # Update responses
            resp.responses[f"question_{question_num}"] = answer
            resp.score += 10

            await db_session.commit()
            await db_session.refresh(resp)
            return resp.responses, resp.score

    # Execute 10 concurrent updates (each updates a different question)
    tasks = [
        update_response(response.id, i, chr(65 + i))  # A, B, C, D, E, F, G, H, I, J
        for i in range(1, 11)
    ]

    results = await asyncio.gather(*tasks)

    # Assert - All updates should be applied
    final_responses, final_score = results[-1]  # Last result

    # Should have all 10 questions
    assert (
        len(final_responses) == 10
    ), f"Expected 10 responses, got {len(final_responses)}"
    assert final_score == 100, f"Expected score 100, got {final_score}"

    # Verify all questions are present
    for i in range(1, 11):
        assert f"question_{i}" in final_responses, f"Missing question_{i}"

    # Cleanup
    await db_session.execute(
        delete(AssessmentResponse).where(AssessmentResponse.id == response.id)
    )
    await db_session.execute(delete(Assessment).where(Assessment.id == assessment.id))
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(
        delete(User).where(User.email == "concurrent_assessment_user@psychsync.test")
    )
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


# ============================================================================
# Test 3: Concurrent Team Creation with Same Name
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
async def test_concurrent_team_creation_same_name(db_session: AsyncSession):
    """
    Test concurrent team creation with the same name in same organization.

    Race Condition: Multiple concurrent team creations with same name and org
    could create duplicate teams.

    Fix: UNIQUE constraint on (organization_id, name) prevents duplicates.
    """
    # Arrange - Create organization
    org = Organization(
        id=uuid4(),
        name="Test Organization for Team Creation",
        slug="test-team-creation-org",
    )
    db_session.add(org)
    await db_session.flush()

    # Act - Try to create 5 teams with the same name concurrently
    async def create_team(org_id, team_name):
        """Create a team"""
        try:
            team = Team(name=team_name, organization_id=org_id)
            db_session.add(team)
            await db_session.commit()
            await db_session.refresh(team)
            return {"success": True, "team_id": team.id}
        except IntegrityError as e:
            await db_session.rollback()
            return {"success": False, "error": str(e)}

    tasks = [create_team(org.id, "Duplicate Team Name") for _ in range(5)]

    results = await asyncio.gather(*tasks)

    # Assert - Only one team should be created
    success_count = sum(1 for r in results if r["success"])
    failure_count = sum(1 for r in results if not r["success"])

    assert (
        success_count == 1
    ), f"Expected 1 successful team creation, got {success_count}"
    assert failure_count == 4, f"Expected 4 duplicate failures, got {failure_count}"

    # Verify database has exactly 1 team with this name
    result = await db_session.execute(
        select(func.count(Team.id))
        .where(Team.organization_id == org.id)
        .where(Team.name == "Duplicate Team Name")
    )
    team_count = result.scalar_one()

    assert team_count == 1, f"Expected 1 team, got {team_count}"

    # Cleanup
    await db_session.execute(delete(Team).where(Team.organization_id == org.id))
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


# ============================================================================
# Test 4: Concurrent User Profile Updates
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.user
@pytest.mark.concurrent
async def test_concurrent_user_profile_updates(db_session: AsyncSession):
    """
    Test concurrent updates to the same user profile.

    Race Condition: Multiple concurrent UPDATEs to the same user profile
    could cause lost updates (last write wins).

    Fix: Use version-based optimistic locking or row locking.
    """
    # Arrange - Create user
    user = User(
        email="concurrent_profile_user@psychsync.test",
        hashed_password="hash",
        full_name="Original Name",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - 10 concurrent updates to different fields
    async def update_user_field(user_id, field_name, value):
        """Update a user field"""
        async with db_session.begin():
            # Use SELECT FOR UPDATE to lock the row
            result = await db_session.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            usr = result.scalar_one()

            # Update field
            if field_name == "full_name":
                usr.full_name = value
            elif field_name == "bio":
                usr.bio = value
            elif field_name == "phone":
                usr.phone = value

            await db_session.commit()
            await db_session.refresh(usr)
            return getattr(usr, field_name)

    # Execute 10 concurrent updates
    tasks = (
        [update_user_field(user.id, "full_name", f"Name {i}") for i in range(5)]
        + [update_user_field(user.id, "bio", f"Bio {i}") for i in range(3)]
        + [update_user_field(user.id, "phone", f"Phone {i}") for i in range(2)]
    )

    results = await asyncio.gather(*tasks)

    # Assert - All updates should complete successfully
    assert len(results) == 10, f"Expected 10 successful updates, got {len(results)}"

    # Verify final state has one of the updates (order-dependent)
    result = await db_session.execute(select(User).where(User.id == user.id))
    final_user = result.scalar_one()

    # User should have one of the updated values
    assert final_user.full_name.startswith("Name "), "full_name should be updated"
    assert final_user.bio.startswith("Bio "), "bio should be updated"
    assert final_user.phone.startswith("Phone "), "phone should be updated"

    # Cleanup
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.commit()


# ============================================================================
# Test 5: Transaction Isolation Level Verification
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.database
@pytest.mark.concurrent
async def test_transaction_isolation_read_committed(db_session: AsyncSession):
    """
    Test that transaction isolation level prevents dirty reads.

    Verifies that READ_COMMITTED isolation level is working correctly.
    A transaction should not see uncommitted changes from another transaction.
    """
    # Arrange - Create user
    user = User(
        email="isolation_test_user@psychsync.test",
        hashed_password="hash",
        full_name="Original Name",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Act - Simulate concurrent transactions
    async def transaction1_update():
        """First transaction: Update user name but don't commit yet"""
        async with db_session.begin():
            result = await db_session.execute(
                select(User).where(User.id == user.id).with_for_update()
            )
            usr = result.scalar_one()
            usr.full_name = "Updated by Transaction 1"
            # Hold the transaction open (don't commit yet)
            await asyncio.sleep(1)
            # Commit will happen when context manager exits

    async def transaction2_read():
        """Second transaction: Read user while transaction 1 is active"""
        await asyncio.sleep(0.5)  # Start after transaction 1
        async with db_session.begin():
            result = await db_session.execute(select(User).where(User.id == user.id))
            usr = result.scalar_one()
            # Should NOT see "Updated by Transaction 1" (not committed yet)
            return usr.full_name

    # Run transactions concurrently
    results = await asyncio.gather(transaction1_update(), transaction2_read())

    # Assert - Transaction 2 should not see uncommitted changes
    read_name = results[1]
    assert (
        read_name == "Original Name"
    ), f"READ_COMMITTED should prevent dirty reads, but saw '{read_name}'"

    # Verify final state after transaction 1 commits
    result = await db_session.execute(select(User).where(User.id == user.id))
    final_user = result.scalar_one()

    assert (
        final_user.full_name == "Updated by Transaction 1"
    ), "Update should be visible after commit"

    # Cleanup
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.commit()


# ============================================================================
# Test 6: Concurrent Team Member Removal
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
async def test_concurrent_team_member_removals(db_session: AsyncSession):
    """
    Test concurrent removal of the same team member.

    Race Condition: Multiple concurrent DELETEs for the same team member
    could cause errors (second delete finds no record).

    Fix: Application should handle "not found" gracefully.
    """
    # Arrange - Create organization, team, user, and team member
    org = Organization(
        id=uuid4(), name="Test Organization for Removal", slug="test-removal-org"
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test Removal Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    user = User(
        email="removal_test_user@psychsync.test",
        hashed_password="hash",
        full_name="Removal Test User",
    )
    db_session.add(user)
    await db_session.flush()

    member = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.MEMBER)
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    # Act - Try to remove the same member 5 times concurrently
    async def remove_member(team_id, user_id):
        """Remove a team member"""
        result = await db_session.execute(
            delete(TeamMember)
            .where(TeamMember.team_id == team_id)
            .where(TeamMember.user_id == user_id)
        )
        await db_session.commit()
        return result.rowcount

    tasks = [remove_member(team.id, user.id) for _ in range(5)]

    results = await asyncio.gather(*tasks)

    # Assert - First delete should remove 1 row, others should remove 0
    total_deleted = sum(results)
    assert total_deleted == 1, f"Expected 1 total deletion, got {total_deleted}"

    # Verify member is gone
    result = await db_session.execute(
        select(func.count(TeamMember.id))
        .where(TeamMember.team_id == team.id)
        .where(TeamMember.user_id == user.id)
    )
    count = result.scalar_one()

    assert count == 0, "Team member should be removed"

    # Cleanup
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


# ============================================================================
# Test 7: Concurrent Role Updates
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
async def test_concurrent_team_member_role_updates(db_session: AsyncSession):
    """
    Test concurrent role updates for the same team member.

    Race Condition: Multiple concurrent UPDATEs to team member role
    could cause lost updates.

    Fix: Use row locking (SELECT FOR UPDATE) to serialize updates.
    """
    # Arrange - Create organization, team, user, and team member
    org = Organization(
        id=uuid4(),
        name="Test Organization for Role Updates",
        slug="test-role-updates-org",
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test Role Updates Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    user = User(
        email="role_update_user@psychsync.test",
        hashed_password="hash",
        full_name="Role Update User",
    )
    db_session.add(user)
    await db_session.flush()

    member = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.MEMBER)
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    # Act - 10 concurrent role updates
    role_sequence = [
        TeamRole.ADMIN,
        TeamRole.MEMBER,
        TeamRole.ADMIN,
        TeamRole.OWNER,
        TeamRole.ADMIN,
        TeamRole.MEMBER,
        TeamRole.OWNER,
        TeamRole.ADMIN,
        TeamRole.MEMBER,
        TeamRole.OWNER,
    ]

    async def update_role(member_id, new_role):
        """Update team member role"""
        async with db_session.begin():
            result = await db_session.execute(
                select(TeamMember).where(TeamMember.id == member_id).with_for_update()
            )
            mbr = result.scalar_one()
            mbr.role = new_role
            await db_session.commit()
            await db_session.refresh(mbr)
            return mbr.role

    tasks = [update_role(member.id, role) for role in role_sequence]

    results = await asyncio.gather(*tasks)

    # Assert - All updates should complete
    assert len(results) == 10, f"Expected 10 updates, got {len(results)}"

    # Final role should be one of the roles in the sequence
    result = await db_session.execute(
        select(TeamMember).where(TeamMember.id == member.id)
    )
    final_member = result.scalar_one()

    assert (
        final_member.role in role_sequence
    ), f"Final role should be in sequence, got {final_member.role}"

    # Cleanup
    await db_session.execute(delete(TeamMember).where(TeamMember.id == member.id))
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(delete(User).where(User.id == user.id))
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()


# ============================================================================
# Test 8: Stress Test - High Concurrency Team Operations
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.regression
@pytest.mark.team
@pytest.mark.concurrent
@pytest.mark.load_test
async def test_high_concurrency_team_operations(db_session: AsyncSession):
    """
    Stress test: 100 concurrent team member additions.

    Verifies the system can handle high concurrency without errors.
    """
    # Arrange - Create organization and team
    org = Organization(
        id=uuid4(),
        name="Test Organization for High Concurrency",
        slug="test-high-concurrency-org",
    )
    db_session.add(org)
    await db_session.flush()

    team = Team(id=uuid4(), name="Test High Concurrency Team", organization_id=org.id)
    db_session.add(team)
    await db_session.flush()

    # Create 100 test users
    users = []
    for i in range(100):
        user = User(
            email=f"high_concurrency_user{i:03d}@psychsync.test",
            hashed_password="hash",
            full_name=f"High Concurrency User {i}",
        )
        db_session.add(user)
        users.append(user)

    await db_session.flush()

    # Act - Add all 100 users concurrently
    async def add_member(user):
        """Add a team member"""
        member = TeamMember(team_id=team.id, user_id=user.id, role=TeamRole.MEMBER)
        db_session.add(member)
        await db_session.commit()
        return member.id

    start_time = datetime.now()

    tasks = [add_member(user) for user in users]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Assert - All additions should succeed
    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = sum(1 for r in results if isinstance(r, Exception))

    assert successes == 100, f"Expected 100 successes, got {successes}"
    assert failures == 0, f"Expected 0 failures, got {failures}"

    # Verify database state
    result = await db_session.execute(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team.id)
    )
    member_count = result.scalar_one()

    assert member_count == 100, f"Expected 100 team members, got {member_count}"

    # Performance check: Should complete in reasonable time
    assert duration < 10, f"Expected completion in < 10s, took {duration:.2f}s"

    print(f"\nHigh Concurrency Test Results:")
    print(f"  Total operations: 100")
    print(f"  Successful: {successes}")
    print(f"  Failed: {failures}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Throughput: {successes / duration:.2f} ops/s")

    # Cleanup
    await db_session.execute(delete(TeamMember).where(TeamMember.team_id == team.id))
    await db_session.execute(delete(Team).where(Team.id == team.id))
    await db_session.execute(
        delete(User).where(User.email.like("high_concurrency_user%@psychsync.test"))
    )
    await db_session.execute(delete(Organization).where(Organization.id == org.id))
    await db_session.commit()
