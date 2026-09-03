"""
Integration Tests for Query Optimization

Tests to verify N+1 query fixes and cache invalidation work correctly.
These tests help prevent performance regressions.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.team_personality_map import TeamPersonalityMap
from app.db.models.user import User
from app.services.cache_invalidation_service import CacheInvalidationService
from app.services.team_personality_service import TeamPersonalityService


@pytest.mark.asyncio
async def test_compare_teams_no_n_plus_1(db_session: AsyncSession, query_counter):
    """
    Test that compare_teams doesn't cause N+1 queries.
    This test ensures the batch query optimization is working.
    """
    # Setup: Create test teams with cached compositions
    team_ids = []
    for i in range(5):
        # Create test team
        team = Team(name=f"Test Team {i}")
        db_session.add(team)
        await db_session.flush()

        team_ids.append(str(team.id))

        # Create cached composition for each team
        composition = TeamPersonalityMap(
            team_id=str(team.id),
            team_size=5,
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

    # Start query counter
    query_counter.reset()

    # Execute compare_teams - should use batch query (1 query, not 5)
    results = await TeamPersonalityService.compare_teams(db_session, team_ids)

    # Assert results are correct
    assert len(results) == 5
    for result in results:
        assert "team_id" in result
        assert "composition_type" in result
        assert "diversity_score" in result

    # Assert query count - should be 1 query, not 5 (N+1)
    # Allow for small overhead (max 3 queries total)
    assert (
        query_counter.count <= 3
    ), f"Expected <= 3 queries, got {query_counter.count}. N+1 problem detected!"


@pytest.mark.asyncio
async def test_cache_invalidation_on_assessment_change(db_session: AsyncSession):
    """
    Test that cache is properly invalidated when assessments change.
    """
    # Setup: Create team with cached composition
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Create cached composition
    composition = TeamPersonalityMap(
        team_id=str(team.id),
        team_size=5,
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
    assert cached is not None, "Cache should exist before invalidation"

    # Invalidate cache
    success = await CacheInvalidationService.invalidate_team_composition_cache(
        db_session, str(team.id)
    )
    assert success is True, "Cache invalidation should succeed"

    # Verify cache is deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is None, "Cache should be deleted after invalidation"


@pytest.mark.asyncio
async def test_cache_invalidation_for_multiple_teams(db_session: AsyncSession):
    """
    Test that cache invalidation works efficiently for multiple teams.
    """
    # Setup: Create multiple teams with cached compositions
    team_ids = []
    for i in range(10):
        team = Team(name=f"Test Team {i}")
        db_session.add(team)
        await db_session.flush()

        team_ids.append(str(team.id))

        composition = TeamPersonalityMap(
            team_id=str(team.id),
            team_size=5,
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

    # Invalidate all team caches in one batch operation
    count = await CacheInvalidationService.invalidate_multiple_teams_cache(
        db_session, team_ids
    )

    assert count == 10, f"Should invalidate 10 teams, got {count}"

    # Verify all caches are deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id.in_(team_ids))
    )
    remaining = result.scalars().all()
    assert len(remaining) == 0, "All caches should be deleted"


@pytest.mark.asyncio
async def test_team_membership_change_invalidates_cache(db_session: AsyncSession):
    """
    Test that team membership changes invalidate the composition cache.
    """
    # Setup: Create team and user
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    user = User(email="test@example.com", full_name="Test User", hashed_password="hash")
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

    # Invalidate cache due to membership change
    success = await CacheInvalidationService.invalidate_team_membership_cache(
        db_session, str(team.id)
    )
    assert success is True

    # Verify cache is deleted
    result = await db_session.execute(
        select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == str(team.id))
    )
    cached = result.scalar_one_or_none()
    assert cached is None


# Test fixture for query counting
@pytest.fixture
def query_counter(db_session: AsyncSession):
    """Fixture to count database queries during test execution."""
    from unittest.mock import patch

    class QueryCounter:
        def __init__(self):
            self.count = 0
            self.original_execute = db_session.execute

        def reset(self):
            self.count = 0

        async def count_execute(self, statement, *args, **kwargs):
            self.count += 1
            return await self.original_execute(statement, *args, **kwargs)

        def __enter__(self):
            db_session.execute = self.count_execute
            return self

        def __exit__(self, *args):
            db_session.execute = self.original_execute

    counter = QueryCounter()

    # Patch the session
    original_execute = db_session.execute
    counter.original_execute = original_execute

    async def counting_execute(statement, *args, **kwargs):
        counter.count += 1
        return await original_execute(statement, *args, **kwargs)

    db_session.execute = counting_execute

    yield counter

    # Restore original
    db_session.execute = original_execute
