"""
Cache Invalidation Service

Centralized service for invalidating cached data across the application.
This ensures stale data is removed when underlying data changes.

CACHE INVALIDATION TRIGGERS:
- Assessment submission/response
- Team membership changes
- Assessment updates
- Team member additions/removals

This service handles BOTH database cache (TeamPersonalityMap) and Redis cache.
"""

import logging
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.async_cache import async_redis_client
from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.team import TeamMember
from app.db.models.team_personality_map import TeamPersonalityMap

logger = logging.getLogger(__name__)


class CacheInvalidationService:
    """
    Centralized cache invalidation service.
    Coordinates cache invalidation across different data domains.

    Handles both:
    - Database cache (TeamPersonalityMap table)
    - Redis cache (async_redis_client)
    """

    @staticmethod
    async def _invalidate_redis_pattern(pattern: str) -> int:
        """
        Invalidate Redis cache keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "team:123:*")

        Returns:
            Number of keys deleted
        """
        if not async_redis_client:
            logger.debug(
                "Redis client not available, skipping Redis cache invalidation"
            )
            return 0

        try:
            # Use SCAN for safe pattern matching in production
            keys = []
            async for key in async_redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await async_redis_client.delete(*keys)
                logger.debug(
                    f"Invalidated {len(keys)} Redis keys matching pattern: {pattern}"
                )
                return len(keys)

            return 0
        except Exception as e:
            logger.error(f"Error invalidating Redis cache pattern {pattern}: {e}")
            return 0

    @staticmethod
    async def invalidate_assessment_related_caches(
        db: AsyncSession, assessment_id: str
    ) -> bool:
        """
        Invalidate all caches related to an assessment.
        Call this when an assessment is created, updated, or deleted.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            assessment_id: Assessment UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the assessment to find its team
            result = await db.execute(
                select(Assessment.team_id).where(Assessment.id == assessment_id)
            )
            team_id = result.scalar_one_or_none()

            if team_id:
                team_id_str = str(team_id)

                # Invalidate database cache
                await CacheInvalidationService.invalidate_team_composition_cache(
                    db, team_id_str
                )

                # Invalidate Redis cache
                redis_patterns = [
                    f"assessment:{assessment_id}:*",
                    f"team:{team_id_str}:*",
                    f"team_data:*:{team_id_str}*",
                    f"cache:*:assessment:{assessment_id}:*",
                ]
                for pattern in redis_patterns:
                    await CacheInvalidationService._invalidate_redis_pattern(pattern)

            logger.info(
                f"Invalidated DB and Redis caches for assessment {assessment_id}, team {team_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error invalidating assessment caches: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def invalidate_response_related_caches(
        db: AsyncSession, response_id: str
    ) -> bool:
        """
        Invalidate all caches related to a response.
        Call this when a response is created, updated, or deleted.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            response_id: Response UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the response to find its assessment
            result = await db.execute(
                select(Response.assessment_id).where(Response.id == response_id)
            )
            assessment_id = result.scalar_one_or_none()

            if assessment_id:
                assessment_id_str = str(assessment_id)

                # Get the assessment to find its team
                result = await db.execute(
                    select(Assessment.team_id).where(Assessment.id == assessment_id)
                )
                team_id = result.scalar_one_or_none()

                if team_id:
                    team_id_str = str(team_id)

                    # Invalidate database cache
                    await CacheInvalidationService.invalidate_team_composition_cache(
                        db, team_id_str
                    )

                    # Invalidate Redis cache
                    redis_patterns = [
                        f"response:{response_id}:*",
                        f"assessment:{assessment_id_str}:*",
                        f"team:{team_id_str}:*",
                        f"team_data:*:{team_id_str}*",
                        f"cache:*:response:{response_id}:*",
                    ]
                    for pattern in redis_patterns:
                        await CacheInvalidationService._invalidate_redis_pattern(
                            pattern
                        )

            logger.info(f"Invalidated DB and Redis caches for response {response_id}")
            return True

        except Exception as e:
            logger.error(f"Error invalidating response caches: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def invalidate_team_composition_cache(db: AsyncSession, team_id: str) -> bool:
        """
        Invalidate cached team composition data.
        Call this when team-related data changes.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            team_id: Team UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete all cached compositions for this team
            await db.execute(
                delete(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == team_id)
            )
            await db.commit()

            # Invalidate Redis cache
            redis_patterns = [
                f"team:{team_id}:*",
                f"team_data:*:{team_id}*",
                f"cache:*:team:{team_id}:*",
            ]
            for pattern in redis_patterns:
                await CacheInvalidationService._invalidate_redis_pattern(pattern)

            logger.info(
                f"Invalidated DB and Redis team composition cache for team {team_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error invalidating team composition cache: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def invalidate_team_membership_cache(db: AsyncSession, team_id: str) -> bool:
        """
        Invalidate caches related to team membership.
        Call this when members are added to or removed from a team.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            team_id: Team UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Team membership changes affect team composition
            await CacheInvalidationService.invalidate_team_composition_cache(
                db, team_id
            )

            # Invalidate additional Redis patterns for team membership
            redis_patterns = [
                f"team_members:{team_id}:*",
                f"user:*:teams",  # Invalidate all users' team lists
            ]
            for pattern in redis_patterns:
                await CacheInvalidationService._invalidate_redis_pattern(pattern)

            logger.info(
                f"Invalidated DB and Redis team membership cache for team {team_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error invalidating team membership cache: {e}")
            await db.rollback()
            return False

    @staticmethod
    async def invalidate_user_related_team_caches(
        db: AsyncSession, user_id: str
    ) -> List[str]:
        """
        Invalidate caches for all teams a user belongs to.
        Useful when a user's assessments change.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            user_id: User UUID

        Returns:
            List of team IDs that were invalidated
        """
        try:
            # Get all teams the user belongs to
            result = await db.execute(
                select(TeamMember.team_id).where(TeamMember.user_id == user_id)
            )
            team_ids = [str(row[0]) for row in result.fetchall()]

            # Invalidate caches for all these teams
            invalidated_teams = []
            for team_id in team_ids:
                success = (
                    await CacheInvalidationService.invalidate_team_composition_cache(
                        db, team_id
                    )
                )
                if success:
                    invalidated_teams.append(team_id)

            # Invalidate user-specific Redis cache
            redis_patterns = [
                f"user:{user_id}:*",
                f"user_profile:*:{user_id}*",
                f"user_data:{user_id}:*",
            ]
            for pattern in redis_patterns:
                await CacheInvalidationService._invalidate_redis_pattern(pattern)

            logger.info(
                f"Invalidated DB and Redis caches for {len(invalidated_teams)} teams for user {user_id}"
            )
            return invalidated_teams

        except Exception as e:
            logger.error(f"Error invalidating user team caches: {e}")
            await db.rollback()
            return []

    @staticmethod
    async def invalidate_multiple_teams_cache(
        db: AsyncSession, team_ids: List[str]
    ) -> int:
        """
        Invalidate cached composition data for multiple teams.
        More efficient than calling invalidate_team_composition_cache multiple times.

        Handles both database cache (TeamPersonalityMap) and Redis cache.

        Args:
            db: Database session
            team_ids: List of team UUIDs

        Returns:
            Number of teams invalidated
        """
        try:
            result = await db.execute(
                delete(TeamPersonalityMap).filter(
                    TeamPersonalityMap.team_id.in_(team_ids)
                )
            )
            await db.commit()

            count = result.rowcount

            # Invalidate Redis cache for all teams
            for team_id in team_ids:
                redis_patterns = [
                    f"team:{team_id}:*",
                    f"team_data:*:{team_id}*",
                ]
                for pattern in redis_patterns:
                    await CacheInvalidationService._invalidate_redis_pattern(pattern)

            logger.info(f"Invalidated DB and Redis caches for {count} teams")
            return count

        except Exception as e:
            logger.error(f"Error invalidating multiple team caches: {e}")
            await db.rollback()
            return 0


# Global service instance
cache_invalidation_service = CacheInvalidationService()
