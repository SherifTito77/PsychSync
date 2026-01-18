"""
EXAMPLE: Enhanced Team Service with Safe Operations and Monitoring

This file demonstrates how to apply the safe operations patterns and monitoring
to the team service. Use this as a reference for enhancing other services.

IMPLEMENTATION STATUS: This is an EXAMPLE showing the patterns.
To apply, integrate these patterns into app/services/team_service.py
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import safe operations utilities
from app.core.safe_db_operations import safe_create, safe_update, safe_delete
from app.monitoring.database_error_monitor import monitor_db_errors, db_monitor

from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate

import logging

logger = logging.getLogger(__name__)


class TeamServiceEnhanced:
    """
    Enhanced Team Service with safe operations and monitoring.

    Key improvements:
    1. @monitor_db_errors decorator on all database operations
    2. safe_create/safe_update/safe_delete utilities
    3. Row-level locking for updates
    4. Comprehensive error handling
    """

    @staticmethod
    @monitor_db_errors("team_service")
    async def create(
        db: AsyncSession,
        *,
        team_in: TeamCreate,
        creator_id: UUID
    ) -> Team:
        """
        Create a new team with safe operations.

        Uses @monitor_db_errors decorator for automatic error tracking.
        Uses safe_create for error handling and rollback.
        """
        # Validate input
        if not team_in.name or len(team_in.name.strip()) < 2:
            raise ValueError("Team name must be at least 2 characters")

        if len(team_in.name) > 100:
            raise ValueError("Team name cannot exceed 100 characters")

        # Get creator
        result = await db.execute(select(User).where(User.id == creator_id))
        creator = result.scalar_one_or_none()

        if not creator or not creator.organization_id:
            raise ValueError("Creator must belong to an organization")

        # Check for duplicate team name
        existing = await db.execute(
            select(Team).where(
                and_(
                    Team.name == team_in.name.strip(),
                    Team.organization_id == creator.organization_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Team '{team_in.name}' already exists")

        # Use safe_create to create team with error handling
        team = await safe_create(
            db,
            Team,
            name=team_in.name.strip(),
            description=getattr(team_in, "description", None),
            organization_id=creator.organization_id,
            created_by_id=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Add creator as owner using safe_create
        await safe_create(
            db,
            TeamMember,
            team_id=team.id,
            user_id=creator_id,
            role=TeamRole.OWNER,
            joined_at=datetime.utcnow(),
        )

        logger.info(f"Created team: {team.name} (ID: {team.id})")
        return team

    @staticmethod
    @monitor_db_errors("team_service")
    async def update(
        db: AsyncSession,
        *,
        team_id: UUID,
        team_in: TeamUpdate
    ) -> Optional[Team]:
        """
        Update team with row-level locking to prevent race conditions.

        Uses @monitor_db_errors decorator for automatic error tracking.
        Uses safe_update with row-level locking enabled.
        """
        # Build update data from schema
        update_data = team_in.dict(exclude_unset=True)

        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()

        # Use safe_update with automatic row-level locking
        team = await safe_update(
            db,
            Team,
            team_id,
            update_data,
            lock_for_update=True  # 🔒 Enables SELECT FOR UPDATE
        )

        if team:
            logger.info(f"Updated team: {team.name} (ID: {team_id})")
        else:
            logger.warning(f"Team not found for update: {team_id}")

        return team

    @staticmethod
    @monitor_db_errors("team_service")
    async def delete(
        db: AsyncSession,
        *,
        team_id: UUID
    ) -> bool:
        """
        Delete team with safe operations.

        Uses @monitor_db_errors decorator for automatic error tracking.
        Uses safe_delete for error handling.
        """
        # Use safe_delete for automatic error handling and rollback
        deleted = await safe_delete(db, Team, team_id)

        if deleted:
            logger.info(f"Deleted team: {team_id}")
        else:
            logger.warning(f"Team not found for deletion: {team_id}")

        return deleted

    @staticmethod
    @monitor_db_errors("team_service")
    async def add_member(
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        role: TeamRole = TeamRole.MEMBER
    ) -> TeamMember:
        """
        Add member to team with race condition protection.

        IMPORTANT: This uses a try/except pattern to handle the unique constraint
        violation that occurs when two concurrent requests try to add the same
        user to the same team simultaneously.

        The database unique constraint on (team_id, user_id) prevents duplicates.
        """
        try:
            # Validate team exists
            team_result = await db.execute(select(Team).where(Team.id == team_id))
            team = team_result.scalar_one_or_none()
            if not team:
                raise ValueError("Team not found")

            # Validate user exists
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError("User not found")

            # Validate same organization
            if user.organization_id != team.organization_id:
                raise ValueError("User must belong to the same organization")

            # Use safe_create - will raise IntegrityError if duplicate
            member = await safe_create(
                db,
                TeamMember,
                team_id=team_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.utcnow(),
            )

            logger.info(f"Added user {user_id} to team {team_id} as {role.value}")
            return member

        except IntegrityError as e:
            # Handle duplicate member (race condition protection)
            await db.rollback()
            logger.warning(f"User {user_id} is already a member of team {team_id}")
            raise ValueError("User is already a member of this team") from e

    @staticmethod
    @monitor_db_errors("team_service")
    async def update_member_role(
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        role: TeamRole
    ) -> Optional[TeamMember]:
        """
        Update member role with row-level locking.

        Uses @monitor_db_errors decorator for automatic error tracking.
        Uses safe_update with row-level locking.
        """
        # Find the team member record first
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            logger.warning(f"Team member not found: team_id={team_id}, user_id={user_id}")
            return None

        # Update with row-level locking
        member = await safe_update(
            db,
            TeamMember,
            member.id,
            {
                "role": role,
                "updated_at": datetime.utcnow(),
            },
            lock_for_update=True  # 🔒 Lock the row
        )

        if member:
            logger.info(f"Updated role for user {user_id} in team {team_id} to {role.value}")

        return member

    @staticmethod
    @monitor_db_errors("team_service")
    async def remove_member(
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove member from team.

        Uses @monitor_db_errors decorator for automatic error tracking.
        """
        # Find the member
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            logger.warning(f"Team member not found: team_id={team_id}, user_id={user_id}")
            return False

        # Delete the member
        await db.delete(member)
        await db.commit()

        logger.info(f"Removed user {user_id} from team {team_id}")
        return True


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

"""
HOW TO USE THE ENHANCED TEAM SERVICE:

1. Import the enhanced service:
   from app.services.team_service_enhanced import TeamServiceEnhanced

2. Use it like the regular service, but with enhanced safety:
   team = await TeamServiceEnhanced.create(db, team_in=team_data, creator_id=user_id)
   team = await TeamServiceEnhanced.update(db, team_id=team_id, team_in=update_data)
   await TeamServiceEnhanced.delete(db, team_id=team_id)

3. All operations are automatically:
   - Monitored for errors (@monitor_db_errors decorator)
   - Protected with row-level locking (safe_update)
   - Handled with proper rollback (safe_create/safe_delete)
   - Logged with full context

4. View monitoring statistics:
   python scripts/view_db_monitoring_stats.py

5. Check logs for database errors - all logged with full stack traces
"""
