# app/api/v1/endpoints/teams.py

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.async_cache import async_cached
from app.core.database import get_async_db
from app.core.input_validation import InputValidator
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.core.security_utils import sanitize_dict
from app.db.models.team import Team
from app.db.models.team import TeamMember as TeamMemberModel
from app.db.models.user import User
from app.schemas.team import TeamCreate
from app.schemas.team import TeamResponse as TeamSchema
from app.schemas.team import TeamWithMembers

get_db = get_async_db  # Alias for consistency

router = APIRouter()


# ==================== TEAM CRUD ====================


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/")
@async_cached(expire=120, key_prefix="teams_list")  # ✅ ASYNC: Non-blocking cache
async def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        50, ge=1, le=100
    ),  # ✅ OPTIMIZED: Reduced max limit from 1000 to 100
    my_teams: bool = Query(False, description="Filter to only teams I'm a member of"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List teams.
    Use my_teams=true to see only teams you're a member of.

    Performance optimizations:
    - Uses subquery for member counting (avoids loading all members into memory)
    - Reduced pagination limit (max 100 instead of 1000)
    - Single efficient query with aggregation
    """
    # ✅ OPTIMIZED: Use subquery for efficient member counting
    # This avoids loading all member objects into memory just to count them
    member_count_subquery = (
        select(func.count(TeamMemberModel.id))
        .where(TeamMemberModel.team_id == Team.id)
        .correlate(Team)
        .scalar_subquery()
    )

    # Build query with member count subquery
    query = select(
        Team.id,
        Team.name,
        Team.description,
        Team.organization_id,
        Team.created_at,
        Team.updated_at,
        Team.created_by_id,
        member_count_subquery.label("members_count"),
    )

    if my_teams:
        # Only return teams where the current user is a member
        query = query.join(TeamMemberModel, Team.id == TeamMemberModel.team_id).filter(
            TeamMemberModel.user_id == current_user.id
        )

    # Apply pagination
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    teams = result.all()

    # Convert teams to response format
    # Note: PERF401 suggests list comprehension, but current approach is more readable
    team_responses = [
        {
            "id": str(team.id),
            "name": team.name,
            "description": team.description,
            "organization_id": (
                str(team.organization_id) if team.organization_id else None
            ),
            "created_at": team.created_at.isoformat() if team.created_at else None,
            "updated_at": team.updated_at.isoformat() if team.updated_at else None,
            "created_by_id": str(team.created_by_id) if team.created_by_id else None,
            "members_count": team.members_count
            or 0,  # ✅ OPTIMIZED: Already counted by database
        }
        for team in teams
    ]

    total = len(team_responses)

    return {
        "teams": team_responses,
        "total": total,
        "success": True,
        "message": "Teams retrieved successfully",
    }


# ==================== TEMPORARILY DISABLED ENDPOINTS ====================
# The following endpoints are disabled due to corrupted service files
# They will be re-enabled once the service layer issues are resolved


@router.post(
    "/",
    response_model=TeamSchema,
    responses={
        201: {
            "description": "Team created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "Product Team",
                        "description": "Product management team",
                        "organization_id": 1,
                    }
                }
            },
        }
    },
)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new team
    """
    try:
        # For now, use the first organization (or create a default one)
        result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
        org_row = result.fetchone()

        if not org_row:
            # Create a default organization with explicit UUID
            default_org_id = str(uuid.uuid4())
            await db.execute(
                text(
                    """
                INSERT INTO organizations (id, name, created_at, updated_at)
                VALUES (:org_id, :name, NOW(), NOW())
            """
                ),
                {"org_id": default_org_id, "name": "Default Organization"},
            )
            await db.commit()
            result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_row = result.fetchone()

        # Defensive null check - ensure we have a valid organization
        if org_row is None or len(org_row) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve or create organization",
            )

        # Sanitize input data
        sanitized_data = sanitize_dict(
            team_data.model_dump(), text_fields=["name", "description"]
        )

        # Create the team using the Team model with sanitized data
        new_team = Team(
            name=sanitized_data["name"],
            description=sanitized_data.get("description", ""),
            created_by_id=current_user.id,
            organization_id=org_row[0],
        )

        db.add(new_team)
        await db.commit()
        await db.refresh(new_team)

        return new_team

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {e!s}",
        ) from e


@router.get("/{team_id}", response_model=TeamWithMembers)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
                detail=f"Invalid team ID: {team_id}",
            )

        team_id_str = str(team_id).strip()

        # Additional validation - prevent SQL injection in search
        if len(team_id_str) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Team ID too long"
            )

        # Sanitize input to prevent injection
        team_id_str = InputValidator.sanitize_search_term(team_id_str)

        # Try to parse as UUID first
        try:
            team_uuid = uuid.UUID(team_id_str)
            # Query by exact UUID match
            result = await db.execute(
                select(Team)
                .options(selectinload(Team.members))
                .filter(Team.id == team_uuid)
            )
        except ValueError:
            # If not a valid UUID, try to find by prefix using cast to text
            # Safe parameter binding - no string interpolation
            result = await db.execute(
                select(Team)
                .options(selectinload(Team.members))
                .filter(text("CAST(teams.id AS VARCHAR) LIKE :prefix"))
                .params(prefix=f"{team_id_str}%")
            )

        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team not found with ID: {team_id}",
            )

        return team

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team: {e!s}",
        ) from e


# ==================== TEMPORARILY DISABLED ENDPOINTS ====================
# The following endpoints are disabled due to corrupted service files
# They will be re-enabled once the service layer issues are resolved
#
# Endpoint templates (commented to avoid ERA001 linter errors):
# - PUT /{team_id} - Update team details
# - DELETE /{team_id} - Delete team
# - POST /{team_id}/members - Add team member
# - GET /{team_id}/members - List team members
# - PATCH /{team_id}/members/{user_id} - Update member role
# - DELETE /{team_id}/members/{user_id} - Remove team member
# - POST /{team_id}/leave - Leave team
