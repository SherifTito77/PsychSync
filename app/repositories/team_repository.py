# app/repositories/team_repository.py

"""
ENTERPRISE-GRADE TEAM REPOSITORY
Team-specific data access operations with security features

TEAM REPOSITORY FEATURES:
- Team management operations
- Member relationship queries
- Organization-based filtering
- Team analytics data access
"""

import logging
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.team import Team
from app.db.models.user import User
from app.repositories.base_repository import BaseRepository
from app.schemas.team import TeamCreate, TeamUpdate

# Initialize team repository logger
team_repo_logger = logging.getLogger("app.repositories.team")


class TeamRepository(BaseRepository[Team, TeamCreate, TeamUpdate]):
    """
    Team-specific repository with comprehensive team management operations
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize team repository

        Args:
            db: Database session
        """
        super().__init__(db, Team)

    async def get_by_organization(
        self,
        organization_id: Any,
        skip: int = 0,
        limit: int = 100,
        include_members: bool = False,
    ) -> tuple[list[Team], int]:
        """
        Get teams by organization with pagination

        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_members: Whether to include team members

        Returns:
            Tuple of (teams list, total count)
        """
        try:
            # Build base query
            base_query = select(Team).where(
                and_(
                    Team.organization_id == organization_id,
                    Team.deleted_at.is_(None),
                )
            )

            # Get total count
            count_query = select(func.count(Team.id)).where(
                and_(
                    Team.organization_id == organization_id,
                    Team.deleted_at.is_(None),
                )
            )

            # Execute count query
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()

            # Build main query with eager loading if needed
            query = base_query
            if include_members:
                query = query.options(selectinload(Team.members))

            # Apply pagination and ordering
            query = query.order_by(Team.created_at.desc()).offset(skip).limit(limit)
            result = await self.db.execute(query)
            teams = result.scalars().all()

            team_repo_logger.debug(
                f"Retrieved {len(teams)} teams for organization {organization_id}",
                extra={
                    "organization_id": organization_id,
                    "total_count": total_count,
                    "include_members": include_members,
                },
            )

            return teams, total_count

        except Exception as e:
            team_repo_logger.error(
                f"Error getting teams by organization {organization_id}: {e}"
            )
            raise

    async def get_with_members(self, team_id: Any) -> Team | None:
        """
        Get team with members loaded

        Args:
            team_id: Team ID

        Returns:
            Team instance with members loaded
        """
        try:
            query = (
                select(Team)
                .options(selectinload(Team.members))
                .where(
                    and_(
                        Team.id == team_id,
                        Team.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            team = result.scalar_one_or_none()

            if team:
                team_repo_logger.debug(f"Team with members loaded: {team_id}")

            return team

        except Exception as e:
            team_repo_logger.error(f"Error getting team with members {team_id}: {e}")
            raise

    async def get_team_statistics(self, team_id: Any) -> dict[str, Any]:
        """
        Get team statistics

        Args:
            team_id: Team ID

        Returns:
            Dictionary with team statistics
        """
        try:
            # Get team with members
            team = await self.get_with_members(team_id)
            if not team:
                return {}

            members = team.members if hasattr(team, "members") else []

            # Calculate statistics
            statistics = {
                "team_id": team_id,
                "team_name": team.name,
                "total_members": len(members),
                "active_members": sum(1 for m in members if m.is_active),
                "created_at": team.created_at.isoformat() if team.created_at else None,
                "organization_id": team.organization_id,
            }

            team_repo_logger.debug(
                f"Team statistics retrieved for team {team_id}",
                extra=statistics,
            )

            return statistics

        except Exception as e:
            team_repo_logger.error(f"Error getting team statistics for {team_id}: {e}")
            raise

    async def add_member(self, team_id: Any, user_id: Any) -> bool:
        """
        Add a member to a team

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if added, False otherwise
        """
        try:
            # Get team
            team = await self.get_by_id(team_id)
            if not team:
                team_repo_logger.warning(
                    f"Cannot add member to team {team_id}: not found"
                )
                return False

            # Get user
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                team_repo_logger.warning(
                    f"Cannot add user {user_id} to team: not found"
                )
                return False

            # Add member if not already a member
            if user not in team.members:
                team.members.append(user)
                await self.db.flush()

                team_repo_logger.info(
                    f"Added user {user_id} to team {team_id}",
                    extra={"team_id": team_id, "user_id": user_id},
                )

            return True

        except Exception as e:
            team_repo_logger.error(f"Error adding member to team {team_id}: {e}")
            await self.db.rollback()
            raise

    async def remove_member(self, team_id: Any, user_id: Any) -> bool:
        """
        Remove a member from a team

        Args:
            team_id: Team ID
            user_id: User ID

        Returns:
            True if removed, False otherwise
        """
        try:
            # Get team with members
            team = await self.get_with_members(team_id)
            if not team:
                team_repo_logger.warning(
                    f"Cannot remove member from team {team_id}: not found"
                )
                return False

            # Find and remove member
            members = team.members if hasattr(team, "members") else []
            for i, member in enumerate(members):
                if member.id == user_id:
                    team.members.pop(i)
                    await self.db.flush()

                    team_repo_logger.info(
                        f"Removed user {user_id} from team {team_id}",
                        extra={"team_id": team_id, "user_id": user_id},
                    )

                    return True

            team_repo_logger.debug(f"User {user_id} is not a member of team {team_id}")
            return False

        except Exception as e:
            team_repo_logger.error(f"Error removing member from team {team_id}: {e}")
            await self.db.rollback()
            raise
