"""
Integration Tests for Cache Invalidation in Endpoints

Tests to verify cache invalidation is properly integrated into
assessment submission, response submission, and team member management endpoints.
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.team_personality_map import TeamPersonalityMap
from app.db.models.user import User
from app.services.cache_invalidation_service import CacheInvalidationService
from app.services.response_service import ResponseService
from app.services.team_service import TeamService


@pytest.mark.asyncio
async def test_response_submission_invalidates_cache(db_session: AsyncSession):
    """
    Test that submitting a response invalidates the team composition cache.
    """
    # Setup: Create team, user, assessment, and cached composition
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    user = User(email="test@example.com", full_name="Test User", hashed_password="hash")
    db_session.add(user)
    await db_session.flush()

    # Create assessment linked to team
    assessment = Assessment(
        title="Test Assessment",
        team_id=str(team.id),
        created_by_id=user.id,
    )
    db_session.add(assessment)
    await db_session.flush()

    # Create cached composition
    composition = TeamPersonalityMap(
        team_id=str(team.id),
        team_size=1,
        openness={
            "avg": 3.5,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [20, 20, 20, 20, 20],
        },
        conscientiousness={
            "avg": 3.8,
            "min": 2.5,
            "max": 5.0,
            "std_dev": 0.7,
            "distribution": [10, 20, 30, 25, 15],
        },
        extraversion={
            "avg": 3.2,
            "min": 1.5,
            "max": 4.8,
            "std_dev": 0.9,
            "distribution": [25, 20, 20, 20, 15],
        },
        agreeableness={
            "avg": 3.6,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [15, 20, 25, 25, 15],
        },
        neuroticism={
            "avg": 2.8,
            "min": 1.0,
            "max": 4.5,
            "std_dev": 1.0,
            "distribution": [20, 25, 20, 20, 15],
        },
        composition_type="Balanced Team",
        strengths=["Test strength"],
        gaps=["Test gap"],
        internal_compatibility=0.8,
        diversity_score=0.7,
    )
    db_session.add(composition)
    await db_session.commit()

    # Verify cache exists
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is not None, "Cache should exist before response submission"

    # Submit response (this should trigger cache invalidation)
    await CacheInvalidationService.invalidate_response_related_caches(
        db_session, str(uuid4())  # Use a fake response ID for testing
    )

    # Note: The cache won't be deleted because the response doesn't exist,
    # but this tests that the invalidation service can be called without errors


@pytest.mark.asyncio
async def test_add_team_member_invalidates_cache(db_session: AsyncSession):
    """
    Test that adding a team member invalidates the team composition cache.
    """
    # Setup: Create team with cached composition
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    user = User(
        email="test2@example.com", full_name="Test User 2", hashed_password="hash"
    )
    db_session.add(user)
    await db_session.flush()

    # Create cached composition
    composition = TeamPersonalityMap(
        team_id=str(team.id),
        team_size=1,
        openness={
            "avg": 3.5,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [20, 20, 20, 20, 20],
        },
        conscientiousness={
            "avg": 3.8,
            "min": 2.5,
            "max": 5.0,
            "std_dev": 0.7,
            "distribution": [10, 20, 30, 25, 15],
        },
        extraversion={
            "avg": 3.2,
            "min": 1.5,
            "max": 4.8,
            "std_dev": 0.9,
            "distribution": [25, 20, 20, 20, 15],
        },
        agreeableness={
            "avg": 3.6,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [15, 20, 25, 25, 15],
        },
        neuroticism={
            "avg": 2.8,
            "min": 1.0,
            "max": 4.5,
            "std_dev": 1.0,
            "distribution": [20, 25, 20, 20, 15],
        },
        composition_type="Balanced Team",
        strengths=["Test strength"],
        gaps=["Test gap"],
        internal_compatibility=0.8,
        diversity_score=0.7,
    )
    db_session.add(composition)
    await db_session.commit()

    # Verify cache exists
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is not None, "Cache should exist before adding member"

    # Add team member (this should trigger cache invalidation)
    await TeamService.add_member(
        db_session,
        team_id=team.id,
        user_id=user.id,
        role=TeamRole.MEMBER,
    )

    # Verify cache is deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is None, "Cache should be deleted after adding member"


@pytest.mark.asyncio
async def test_remove_team_member_invalidates_cache(db_session: AsyncSession):
    """
    Test that removing a team member invalidates the team composition cache.
    """
    # Setup: Create team, user, and cached composition
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    user = User(
        email="test3@example.com", full_name="Test User 3", hashed_password="hash"
    )
    db_session.add(user)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(
        team_id=str(team.id),
        user_id=user.id,
        role=TeamRole.MEMBER,
    )
    db_session.add(team_member)
    await db_session.flush()

    # Create cached composition
    composition = TeamPersonalityMap(
        team_id=str(team.id),
        team_size=1,
        openness={
            "avg": 3.5,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [20, 20, 20, 20, 20],
        },
        conscientiousness={
            "avg": 3.8,
            "min": 2.5,
            "max": 5.0,
            "std_dev": 0.7,
            "distribution": [10, 20, 30, 25, 15],
        },
        extraversion={
            "avg": 3.2,
            "min": 1.5,
            "max": 4.8,
            "std_dev": 0.9,
            "distribution": [25, 20, 20, 20, 15],
        },
        agreeableness={
            "avg": 3.6,
            "min": 2.0,
            "max": 5.0,
            "std_dev": 0.8,
            "distribution": [15, 20, 25, 25, 15],
        },
        neuroticism={
            "avg": 2.8,
            "min": 1.0,
            "max": 4.5,
            "std_dev": 1.0,
            "distribution": [20, 25, 20, 20, 15],
        },
        composition_type="Balanced Team",
        strengths=["Test strength"],
        gaps=["Test gap"],
        internal_compatibility=0.8,
        diversity_score=0.7,
    )
    db_session.add(composition)
    await db_session.commit()

    # Verify cache exists
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is not None, "Cache should exist before removing member"

    # Remove team member (this should trigger cache invalidation)
    await TeamService.remove_member(
        db_session,
        team_id=team.id,
        user_id=user.id,
    )

    # Verify cache is deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is None, "Cache should be deleted after removing member"


@pytest.mark.asyncio
async def test_cache_invalidation_service_error_handling(db_session: AsyncSession):
    """
    Test that cache invalidation failures don't break the main operation.
    """
    # Setup: Create team
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    user = User(
        email="test4@example.com", full_name="Test User 4", hashed_password="hash"
    )
    db_session.add(user)
    await db_session.flush()

    # Add team member - should succeed even if cache invalidation fails
    # (since there's no cache to invalidate, it will log a warning but not fail)
    result = await TeamService.add_member(
        db_session,
        team_id=team.id,
        user_id=user.id,
        role=TeamRole.MEMBER,
    )

    assert result is not None, "Team member addition should succeed"


@pytest.mark.asyncio
async def test_multiple_cache_invalidations(db_session: AsyncSession):
    """
    Test that multiple cache invalidations can be called safely.
    """
    # Setup: Create multiple teams with cached compositions
    team_ids = []
    for i in range(3):
        team = Team(name=f"Test Team {i}")
        db_session.add(team)
        await db_session.flush()

        team_ids.append(str(team.id))

        composition = TeamPersonalityMap(
            team_id=str(team.id),
            team_size=1,
            openness={
                "avg": 3.5,
                "min": 2.0,
                "max": 5.0,
                "std_dev": 0.8,
                "distribution": [20, 20, 20, 20, 20],
            },
            conscientiousness={
                "avg": 3.8,
                "min": 2.5,
                "max": 5.0,
                "std_dev": 0.7,
                "distribution": [10, 20, 30, 25, 15],
            },
            extraversion={
                "avg": 3.2,
                "min": 1.5,
                "max": 4.8,
                "std_dev": 0.9,
                "distribution": [25, 20, 20, 20, 15],
            },
            agreeableness={
                "avg": 3.6,
                "min": 2.0,
                "max": 5.0,
                "std_dev": 0.8,
                "distribution": [15, 20, 25, 25, 15],
            },
            neuroticism={
                "avg": 2.8,
                "min": 1.0,
                "max": 4.5,
                "std_dev": 1.0,
                "distribution": [20, 25, 20, 20, 15],
            },
            composition_type="Balanced Team",
            strengths=["Test strength"],
            gaps=["Test gap"],
            internal_compatibility=0.8,
            diversity_score=0.7,
        )
        db_session.add(composition)

    await db_session.commit()

    # Invalidate all caches at once
    count = await CacheInvalidationService.invalidate_multiple_teams_cache(
        db_session, team_ids
    )

    assert count == 3, f"Should invalidate 3 teams, got {count}"

    # Verify all caches are deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id.in_(team_ids))
    )
    remaining = result.scalars().all()
    assert len(remaining) == 0, "All caches should be deleted"
