# app/services/team_service.py
"""
Team Service - Uses organization_id (NOT org_id)
"""
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.user import User
from app.schemas.team import TeamCreate  # ✅ Use schema, not model

class TeamService:

    # ──────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────
    @staticmethod
    def create(db: Session, *, team_in: TeamCreate, creator_id: UUID) -> Team:
        """Create a new team, assign creator as owner."""
        creator = result = await db.execute(query)
        return result.scalars().all()
        if not creator:
            raise ValueError("Creator user not found")

        if not creator.organization_id:
            raise ValueError("Creator user has no organization")

        team = Team(
            name=team_in.name,
            description=getattr(team_in, "description", None),
            organization_id=creator.organization_id,
            created_by_id=creator_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(team)
        db.flush()

        # Add creator as team owner
        team_member = TeamMember(
            team_id=team.id,
            user_id=creator_id,
            role=TeamRole.OWNER,
        )
        db.add(team_member)
        await db.commit()
        await db.refresh(team)
        return team

    # ──────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────
    @staticmethod
    def get_by_id(db: Session, team_id: UUID) -> Optional[Team]:
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    def get_user_teams(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Team]:
        """Get all teams for a user (paginated)."""
        return (
            db.query(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .filter(TeamMember.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ──────────────────────────────────────────────
    # UPDATE
    # ──────────────────────────────────────────────
    @staticmethod
    def update(db: Session, *, team_id: UUID, team_in: TeamCreate) -> Team:
        team = result = await db.execute(query)
        return result.scalars().all()
        if not team:
            raise ValueError("Team not found")

        if getattr(team_in, "name", None):
            team.name = team_in.name
        if hasattr(team_in, "description"):
            team.description = team_in.description
        team.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(team)
        return team

    # ──────────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────────
    @staticmethod
    def delete(db: Session, team_id: UUID) -> bool:
        team = result = await db.execute(query)
        return result.scalars().all()
        if not team:
            raise ValueError("Team not found")

        db.delete(team)
        await db.commit()
        return True

    # ──────────────────────────────────────────────
    # MEMBERS
    # ──────────────────────────────────────────────
    @staticmethod
    def add_member(db: Session, team_id: UUID, user_id: UUID, role: TeamRole = TeamRole.MEMBER) -> TeamMember:
        existing = result = await db.execute(query)
        return result.scalars().all()
        if existing:
            raise ValueError("User already a member of this team")

        member = TeamMember(team_id=team_id, user_id=user_id, role=role)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    def remove_member(db: Session, team_id: UUID, user_id: UUID) -> None:
        member = result = await db.execute(query)
        return result.scalars().all()
        if not member:
            raise ValueError("Member not found in team")

        if member.role == TeamRole.OWNER:
            owner_count = (
                db.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.role == TeamRole.OWNER)
                .count()
            )
            if owner_count <= 1:
                raise ValueError("Cannot remove the last owner")

        db.delete(member)
        await db.commit()

    @staticmethod
    def update_member_role(db: Session, team_id: UUID, user_id: UUID, new_role: TeamRole) -> TeamMember:
        member = result = await db.execute(query)
        return result.scalars().all()
        if not member:
            raise ValueError("Member not found in team")

        if member.role == TeamRole.OWNER and new_role != TeamRole.OWNER:
            owner_count = (
                db.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.role == TeamRole.OWNER)
                .count()
            )
            if owner_count <= 1:
                raise ValueError("Cannot demote last owner")

        member.role = new_role
        await db.commit()
        await db.refresh(member)
        return member

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────
    @staticmethod
    def get_member(db: Session, team_id: UUID, user_id: UUID) -> Optional[TeamMember]:
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    def is_member(db: Session, team_id: UUID, user_id: UUID) -> bool:
        return (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .first()
            is not None
        )

    @staticmethod
    def is_admin_or_owner(db: Session, team_id: UUID, user_id: UUID) -> bool:
        member = result = await db.execute(query)
        return result.scalars().all()
        return bool(member and member.role in [TeamRole.ADMIN, TeamRole.OWNER])

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Team]:
        """Return all teams (non-deleted) with optional pagination."""
        return db.query(Team).offset(skip).limit(limit).all()

        
        #return db.query(Team).filter(Team.is_deleted == False).offset(skip).limit(limit).all()
