# app/services/team_service.py
"""
Team Service - Enhanced with standardized error handling and logging
"""
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate
from app.core.error_handling import handle_database_errors, ValidationException
from app.core.structured_logging import get_logger, EventType
from app.core.database_transactions import transaction_manager

logger = get_logger(__name__)

class TeamService:

    @staticmethod
    @handle_database_errors("team_creation")
    @transaction_manager.transaction
    async def create(db: AsyncSession, *, team_in: TeamCreate, creator_id: UUID) -> Team:
        """
        Create a new team, assign creator as owner.
        Uses transaction management and standardized error handling.
        """
        # Validate team name
        if not team_in.name or len(team_in.name.strip()) < 2:
            raise ValidationException(
                "Team name must be at least 2 characters long",
                field="name"
            )

        if len(team_in.name) > 100:
            raise ValidationException(
                "Team name cannot exceed 100 characters",
                field="name"
            )

        # Validate and get creator
        result = await db.execute(
            select(User).options(selectinload(User.organization))
            .where(User.id == creator_id)
        )
        creator = result.scalar_one_or_none()

        if not creator:
            raise ValidationException(
                "Creator user not found",
                field="creator_id"
            )

        if not creator.organization_id:
            raise ValidationException(
                "Creator user must belong to an organization to create teams",
                field="organization_id"
            )

        # Check for duplicate team name within organization
        existing_team = await db.execute(
            select(Team).where(and_(
                Team.name == team_in.name.strip(),
                Team.organization_id == creator.organization_id
            ))
        )
        if existing_team.scalar_one_or_none():
            raise ValidationException(
                f"Team '{team_in.name}' already exists in your organization",
                field="name"
            )

        # Create team with sanitized data
        team = Team(
            name=team_in.name.strip(),
            description=team_in.description.strip() if getattr(team_in, "description", None) else None,
            organization_id=creator.organization_id,
            created_by_id=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(team)
        await db.flush()  # Get ID without committing

        # Add creator as team owner
        team_member = TeamMember(
            team_id=team.id,
            user_id=creator_id,
            role=TeamRole.OWNER,
            joined_at=datetime.utcnow(),
        )
        db.add(team_member)

        await db.flush()  # Ensure both records are in transaction

        # Log business event
        logger.log_business_event(
            event_name="team_created",
            user_id=str(creator_id),
            resource_id=str(team.id),
            team_name=team.name,
            organization_id=str(creator.organization_id)
        )

        logger.info(
            EventType.DATABASE_OPERATION,
            f"Team '{team.name}' created successfully",
            operation_name="team_creation",
            team_id=str(team.id),
            creator_id=str(creator_id),
            organization_id=str(creator.organization_id)
        )

        return team

    @staticmethod
    @handle_database_errors("team_retrieval")
    async def get_by_id(db: AsyncSession, team_id: UUID) -> Optional[Team]:
        """
        Get team by ID with proper error handling and logging.
        """
        result = await db.execute(
            select(Team).options(
                selectinload(Team.members).selectinload(TeamMember.user)
            ).where(Team.id == team_id)
        )
        team = result.scalar_one_or_none()

        if team:
            logger.debug(
                EventType.DATABASE_OPERATION,
                f"Team retrieved: {team.name}",
                operation_name="team_retrieval",
                team_id=str(team_id),
                team_name=team.name
            )

        return team

    @staticmethod
    @handle_database_errors("user_teams_retrieval")
    async def get_by_user(db: AsyncSession, user_id: UUID) -> List[Team]:
        """
        Get teams where user is a member with optimized eager loading.
        """
        result = await db.execute(
            select(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .where(TeamMember.user_id == user_id)
            .options(selectinload(Team.members).selectinload(TeamMember.user))
            .order_by(Team.name)
        )
        teams = result.scalars().all()

        logger.info(
            EventType.DATABASE_OPERATION,
            f"Retrieved {len(teams)} teams for user",
            operation_name="user_teams_retrieval",
            user_id=str(user_id),
            team_count=len(teams)
        )

        return teams

    @staticmethod
    @handle_database_errors("team_members_retrieval")
    async def get_members(db: AsyncSession, team_id: UUID) -> List[User]:
        """
        Get all members of a team with eager loading.
        """
        result = await db.execute(
            select(User)
            .join(TeamMember, User.id == TeamMember.user_id)
            .where(TeamMember.team_id == team_id)
            .order_by(User.full_name)
        )
        members = result.scalars().all()

        logger.info(
            EventType.DATABASE_OPERATION,
            f"Retrieved {len(members)} members for team",
            operation_name="team_members_retrieval",
            team_id=str(team_id),
            member_count=len(members)
        )

        return members

    @staticmethod
    @handle_database_errors("team_member_addition")
    async def add_member(
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        role: TeamRole = TeamRole.MEMBER,
        added_by_id: UUID = None
    ) -> TeamMember:
        """
        Add a member to a team with validation and business logic.
        """
        # Validate team exists
        team_result = await db.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()
        if not team:
            raise ValidationException("Team not found", field="team_id")

        # Validate user exists
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValidationException("User not found", field="user_id")

        # Check if user already exists in team
        existing_result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValidationException(
                "User is already a member of this team",
                field="user_id"
            )

        # Validate user can be added to this team (same organization)
        if user.organization_id != team.organization_id:
            raise ValidationException(
                "User must belong to the same organization as the team",
                field="user_id"
            )

        # Create team member
        team_member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow(),
        )
        db.add(team_member)
        await db.flush()

        # Log business event
        logger.log_business_event(
            event_name="team_member_added",
            user_id=str(added_by_id) if added_by_id else str(user_id),
            resource_id=str(team_member.id),
            team_id=str(team_id),
            added_user_id=str(user_id),
            role=role.value
        )

        logger.info(
            EventType.DATABASE_OPERATION,
            f"Added user to team: {team.name}",
            operation_name="team_member_addition",
            team_id=str(team_id),
            user_id=str(user_id),
            role=role.value,
            team_name=team.name
        )

        return team_member

    @staticmethod
    async def remove_member(db: AsyncSession, *, team_id: UUID, user_id: UUID) -> bool:
        """Remove a member from a team."""
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        team_member = result.scalar_one_or_none()

        if not team_member:
            return False

        await db.delete(team_member)
        await db.commit()
        return True

    @staticmethod
    async def update_member_role(
        db: AsyncSession, *, team_id: UUID, user_id: UUID, role: TeamRole
    ) -> Optional[TeamMember]:
        """Update a member's role."""
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        team_member = result.scalar_one_or_none()

        if not team_member:
            return None

        team_member.role = role
        team_member.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(team_member)
        return team_member

    @staticmethod
    async def update(db: AsyncSession, *, team_id: UUID, team_in: TeamUpdate) -> Optional[Team]:
        """Update team information."""
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return None

        update_data = team_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        for field, value in update_data.items():
            setattr(team, field, value)

        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def delete(db: AsyncSession, *, team_id: UUID) -> bool:
        """Delete a team."""
        result = await db.execute(select(Team).where(Team.id == team_id))
        team = result.scalar_one_or_none()

        if not team:
            return False

        await db.delete(team)
        await db.commit()
        return True

    @staticmethod
    async def is_member(db: AsyncSession, *, team_id: UUID, user_id: UUID) -> bool:
        """Check if user is a member of the team."""
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_user_role(db: AsyncSession, *, team_id: UUID, user_id: UUID) -> Optional[TeamRole]:
        """Get user's role in the team."""
        result = await db.execute(
            select(TeamMember).where(
                and_(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            )
        )
        team_member = result.scalar_one_or_none()
        return team_member.role if team_member else None