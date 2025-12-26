from sqlalchemy import select

from app.middleware.rate_limiter import check_rate_limit
from sqlalchemy.orm import selectinload
# app/api/v1/endpoints/teams.py

from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
get_db = get_async_db  # Alias for consistency

# --- DEPENDENCIES ---
from app.api.v1.deps import (, get_current_user
    get_current_active_user,
)
from app.core.security_utils import sanitize_dict
from app.core.input_validation import InputValidator
from app.core.api_utils import cache_response

# --- SCHEMAS (for request/response) ---
# Consolidate all schema imports here. Use clear aliases.
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse as TeamSchema,  # Use a clear alias for the main team response
    TeamWithMembers,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse as TeamMemberSchema, # Use a clear alias for member response
    TeamListResponse as TeamList, # Use a clear alias for the list response
    TeamRole,
)

# --- MODELS (for database interaction) ---
# Consolidate all model imports here.
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.team import TeamMember as TeamMemberModel

# --- SERVICES ---
# Temporarily disabled due to file corruption
# from app.services.team_service import TeamService
# import app.services.user_service as user_service

router = APIRouter()


# ==================== TEAM CRUD ====================


@check_rate_limit(identifier="public", endpoint_type="public")
@router.get("/")
@cache_response(expire_seconds=120, key_prefix="teams_list", vary_on=["my_teams"])
async def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    my_teams: bool = Query(False, description="Filter to only teams I'm a member of"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List teams.
    Use my_teams=true to see only teams you're a member of.
    """
    # Simple placeholder implementation without corrupted TeamService
    query = select(Team).options(selectinload(Team.members))

    if my_teams:
        # Only return teams where the current user is a member
        query = query.join(TeamMemberModel).filter(
            TeamMemberModel.user_id == current_user.id
        )
    # No is_active filter - return all teams

    result = await db.execute(query)
    teams = result.scalars().all()

    # Convert teams to response format
    team_responses = []
    for team in teams:
        team_responses.append({
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "organization_id": str(team.organization_id) if team.organization_id else None,
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
            "created_by_id": str(team.created_by_id) if team.created_by_id else None,
            "members_count": len(team.members) if hasattr(team, 'members') and team.members else 0
        })

    total = len(team_responses)

    return {
        "teams": team_responses,
        "total": total,
        "success": True,
        "message": "Teams retrieved successfully"
    }


# ==================== TEMPORARILY DISABLED ENDPOINTS ====================
# The following endpoints are disabled due to corrupted service files
# They 
@check_rate_limit(identifier="public", endpoint_type="public")
will be re-enabled once the service layer issues are resolved


@router.post("/", response_model=TeamSchema)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new team
    """
    from sqlalchemy import text
    import uuid

    try:
        # For now, use the first organization (or create a default one)
        result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_row = result.fetchone()

        if not org_row:
            # Create a default organization with explicit UUID
            default_org_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO organizations (id, name, created_at, updated_at)
                VALUES (:org_id, :name, NOW(), NOW())
            """), {
                "org_id": default_org_id,
                "name": "Default Organization"
            })
            await db.commit()
            result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_row = result.fetchone()

        # Sanitize input data
        sanitized_data = sanitize_dict(
            team_data.dict(),
            text_fields=['name', 'description']
        )

        # Create the team using the Team model with sanitized data
        new_team = Team(
            name=sanitized_data['name'],
            description=sanitized_data.get('description', ''),
            created_by_id=current_user.id,
            organization_id=org_row[0]
        )

        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)

        return new_team

    except Exception as e:
        await db.rollback()
        raise HTTPException(

@check_rate_limit(identifier="public", endpoint_type="public")
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {str(e)}"
        )

@router.get("/{team_id}", response_model=TeamWithMembers)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific team by ID with its members
    Accepts both full UUIDs and partial IDs for backward compatibility
    """
    try:
        # Validate the input first
        if not team_id or team_id.strip() == "" or team_id.lower() == "nan":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invalid team ID: {team_id}"
            )

        team_id_str = str(team_id).strip()

        # Additional validation - prevent SQL injection in search
        if len(team_id_str) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team ID too long"
            )

        # Sanitize input to prevent injection
        team_id_str = InputValidator.sanitize_search_term(team_id_str)

        # Try to parse as UUID first
        try:
            from uuid import UUID
            team_uuid = UUID(team_id_str)
            # Query by exact UUID match
            result = await db.execute(
                select(Team)
                .options(selectinload(Team.members))
                .filter(Team.id == team_uuid)
            )
        except ValueError:
            # If not a valid UUID, try to find by prefix using cast to text
            result = await db.execute(
                select(Team)
                .options(selectinload(Team.members))
                .filter(text("CAST(teams.id AS VARCHAR) LIKE :prefix"))
                .params(prefix=team_id_str + "%")  # Safe parameter binding - no string interpolation
            )

        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team not found with ID: {team_id}"
            )

        return team

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team: {str(e)}"
        )

# @router.put("/{team_id}", response_model=TeamSchema, dependencies=[Depends(get_current_user)])
# async def update_team(...):

# @router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
# async def delete_team(...):

# @router.post("/{team_id}/members", response_model=TeamMemberSchema, status_code=status.HTTP_201_CREATED)
# async def add_team_member(...):

# @router.get("/{team_id}/members", response_model=List[TeamMemberSchema])
# async def list_team_members(...):

# @router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberSchema, dependencies=[Depends(get_current_user)])
# async def update_team_member_role(...):

# @router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_user)])
# async def remove_team_member(...):

# @router.post("/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
# async def leave_team(...):