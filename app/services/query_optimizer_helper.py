"""
Query Optimization Helper Functions

This module provides optimized query helpers to fix common N+1 query problems.
Use these functions instead of raw queries to avoid performance issues.

Usage Example:
    # OLD (N+1 problem):
    # for response in assessment.responses:
    #     user_email = response.user.email  # Additional query per response!

    # NEW (Optimized):
    assessment = await get_assessment_with_responses_and_users(db, assessment_id)
    for response in assessment.responses:
        user_email = response.user.email  # Already loaded, no query!
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models.assessment import Assessment
from app.db.models.response import Response
from app.db.models.user import User


async def get_assessment_with_responses_and_users(
    db: AsyncSession, assessment_id: str
) -> Optional[Assessment]:
    """
    Get assessment with responses and users eagerly loaded.

    This prevents N+1 query problems when accessing response.user data.

    Performance Impact:
    - OLD: 1 + N queries (1 for assessment, N for each response's user)
    - NEW: 1 query with joins (all data loaded in single query)

    Args:
        db: Database session
        assessment_id: Assessment UUID

    Returns:
        Assessment with responses and users pre-loaded, or None

    Example:
        >>> assessment = await get_assessment_with_responses_and_users(db, aid)
        >>> for response in assessment.responses:
        ...     print(response.user.email)  # No additional query!
    """
    query = (
        select(Assessment)
        .where(Assessment.id == assessment_id)
        .options(
            # Eager load responses with their users
            joinedload(Assessment.responses).joinedload(Response.user),
            # Eager load assessment owner
            joinedload(Assessment.user),
            # Eager load team if present
            joinedload(Assessment.team),
        )
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_assessments_with_responses(
    db: AsyncSession, user_id: str, limit: int = 100, offset: int = 0
) -> list[Assessment]:
    """
    Get user's assessments with responses eagerly loaded.

    This prevents N+1 queries when displaying assessment lists with response counts.

    Performance Impact:
    - OLD: 1 + N queries (1 for assessments, N for response counts)
    - NEW: 2 queries (1 for assessments, 1 for all responses)

    Args:
        db: Database session
        user_id: User UUID
        limit: Max number of assessments to return
        offset: Pagination offset

    Returns:
        List of assessments with responses pre-loaded

    Example:
        >>> assessments = await get_user_assessments_with_responses(db, uid)
        >>> for assessment in assessments:
        ...     print(len(assessment.responses))  # No additional query!
    """
    query = (
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(
            selectinload(Assessment.responses).selectinload(Response.user),
            joinedload(Assessment.team),
        )
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_team_members_with_users(db: AsyncSession, team_id: str) -> list[dict]:
    """
    Get team members with user data eagerly loaded.

    This prevents N+1 queries when listing team members.

    Performance Impact:
    - OLD: 1 + N queries (1 for team members, N for user details)
    - NEW: 1 query with join (all data loaded together)

    Args:
        db: Database session
        team_id: Team UUID

    Returns:
        List of team members with user data

    Example:
        >>> members = await get_team_members_with_users(db, tid)
        >>> for member in members:
        ...     print(member['user']['email'])  # No additional query!
    """
    from app.db.models.team import TeamMember

    query = (
        select(TeamMember)
        .where(TeamMember.team_id == team_id)
        .options(
            joinedload(TeamMember.user),
        )
    )

    result = await db.execute(query)
    members = result.scalars().all()

    # Convert to dict for JSON serialization
    return [
        {
            "id": str(member.id),
            "team_id": str(member.team_id),
            "user_id": str(member.user_id),
            "role": member.role,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "user": {
                "id": str(member.user.id),
                "email": member.user.email,
                "full_name": member.user.full_name,
            },
        }
        for member in members
    ]


async def get_organization_analytics_optimized(
    db: AsyncSession, organization_id: str
) -> dict:
    """
    Get organization analytics with optimized queries.

    This function prevents N+1 query problems by using eager loading
    and aggregate queries to load all data in a constant number of queries.

    Performance Impact:
    - OLD: 1 + T + M + A queries (teams, members, assessments per user)
    - NEW: 3 queries (constant regardless of organization size)

    Args:
        db: Database session
        organization_id: Organization UUID

    Returns:
        Dictionary with organization analytics including:
        - organization info
        - teams with member counts
        - total assessment counts
        - user participation metrics

    Example:
        >>> analytics = await get_organization_analytics_optimized(db, org_id)
        >>> print(f"Teams: {analytics['total_teams']}")
        >>> print(f"Members: {analytics['total_members']}")
        >>> print(f"Assessments: {analytics['total_assessments']}")
    """
    from sqlalchemy import func

    from app.db.models.organization import Organization
    from app.db.models.team import Team, TeamMember

    # Query 1: Load organization with teams (joinedload for 1:many)
    org_query = (
        select(Organization)
        .where(Organization.id == organization_id)
        .options(joinedload(Organization.teams))
    )

    org_result = await db.execute(org_query)
    organization = org_result.scalar_one_or_none()

    if not organization:
        return None

    # Query 2: Load all team members with user data (selectinload for multiple parents)
    teams_list = list(organization.teams)
    team_ids = [t.id for t in teams_list]

    if team_ids:
        members_query = (
            select(TeamMember)
            .where(TeamMember.team_id.in_(team_ids))
            .options(
                joinedload(TeamMember.user),
            )
            .order_by(TeamMember.team_id)
        )

        members_result = await db.execute(members_query)
        all_members = members_result.scalars().all()

        # Group members by team
        team_members = {}
        for member in all_members:
            team_id_str = str(member.team_id)
            if team_id_str not in team_members:
                team_members[team_id_str] = []
            team_members[team_id_str].append(
                {
                    "id": str(member.id),
                    "user_id": str(member.user_id),
                    "role": member.role,
                    "email": member.user.email if member.user else None,
                    "full_name": member.user.full_name if member.user else None,
                }
            )
    else:
        team_members = {}

    # Query 3: Aggregate assessment statistics
    from app.db.models.assessment import Assessment

    assessments_query = select(
        func.count(Assessment.id).label("total"),
        func.count(func.distinct(Assessment.user_id)).label("unique_users"),
        func.count(func.distinct(Assessment.team_id)).label("unique_teams"),
    ).where(Assessment.organization_id == organization_id)

    assessments_result = await db.execute(assessments_query)
    assessment_stats = assessments_result.one()

    # Query 4: Response statistics (optional, for participation metrics)
    from app.db.models.response import Response

    response_subquery = (
        select(Response.assessment_id, func.count(Response.id).label("response_count"))
        .join(Assessment, Assessment.id == Response.assessment_id)
        .where(Assessment.organization_id == organization_id)
        .group_by(Response.assessment_id)
        .subquery()
    )

    avg_responses_query = select(func.avg(response_subquery.c.response_count))

    avg_responses_result = await db.execute(avg_responses_query)
    avg_responses_per_assessment = avg_responses_result.scalar() or 0

    # Build team data with member counts
    teams_data = []
    for team in teams_list:
        team_id_str = str(team.id)
        members = team_members.get(team_id_str, [])

        teams_data.append(
            {
                "id": str(team.id),
                "name": team.name,
                "member_count": len(members),
                "created_at": team.created_at.isoformat() if team.created_at else None,
            }
        )

    # Calculate participation metrics
    total_members = sum(len(members) for members in team_members.values())
    total_assessments = assessment_stats.total or 0
    unique_participants = assessment_stats.unique_users or 0

    participation_rate = (
        (unique_participants / total_members * 100) if total_members > 0 else 0
    )

    return {
        "organization": {
            "id": str(organization.id),
            "name": organization.name,
            "created_at": (
                organization.created_at.isoformat() if organization.created_at else None
            ),
        },
        "teams": {
            "total": len(teams_data),
            "teams": teams_data,
        },
        "members": {
            "total": total_members,
            "unique_participants": unique_participants,
        },
        "assessments": {
            "total": total_assessments,
            "unique_users": assessment_stats.unique_users or 0,
            "unique_teams": assessment_stats.unique_teams or 0,
            "avg_responses_per_assessment": round(avg_responses_per_assessment, 2),
        },
        "participation_metrics": {
            "participation_rate": round(participation_rate, 2),
            "assessments_per_member": round(
                (total_assessments / total_members) if total_members > 0 else 0, 2
            ),
        },
        "query_count": 4,  # Constant regardless of org size!
    }
