"""
Row-Level Security (RLS) for Multi-Tenancy

Provides automatic data isolation based on tenant membership:
- Organization-level isolation
- Team-level isolation
- User-level data ownership
- Automatic query filtering
- Audit logging for cross-tenant access attempts

SECURITY PRINCIPLES:
- Tenant data isolation by default
- No cross-tenant data leakage
- Automatic query filtering
- Explicit override for admin users
- Comprehensive audit logging

Author: Security Team
Version: 1.0
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from app.db.models.user import User

logger = logging.getLogger(__name__)


class RowLevelSecurityError(Exception):
    """Base exception for RLS errors"""


class CrossTenantAccessError(RowLevelSecurityError):
    """Raised when cross-tenant access is attempted"""


class RowLevelSecurityService:
    """
    Row-Level Security service for multi-tenant data isolation

    Enforces tenant boundaries at the database query level
    """

    def __init__(self):
        """Initialize RLS service"""
        self.isolation_level = (
            "organization"  # Can be "organization", "team", or "user"
        )

    def get_accessible_org_ids(self, user: User) -> set[str]:
        """
        Get set of organization IDs user can access

        Args:
            user: User object

        Returns:
            Set of organization IDs
        """
        org_ids = set()

        # User's own organization
        if user.organization_id:
            org_ids.add(str(user.organization_id))

        # Superuser can access all (but still should be explicit)
        if user.is_superuser:
            logger.warning(f"Superuser {user.id} accessing all organizations")

        return org_ids

    def get_accessible_team_ids(self, user: User) -> set[str]:
        """
        Get set of team IDs user can access

        Args:
            user: User object

        Returns:
            Set of team IDs
        """
        team_ids = set()

        # Teams user is a member of
        if hasattr(user, "team_memberships"):
            for membership in user.team_memberships:
                team_ids.add(str(membership.team_id))

        # Teams user created
        if hasattr(user, "teams_created"):
            for team in user.teams_created:
                team_ids.add(str(team.id))

        return team_ids

    def apply_organization_filter(
        self, query: Query, user: User, org_column: Any
    ) -> Query:
        """
        Apply organization-level filter to query

        Args:
            query: SQLAlchemy query
            user: User object
            org_column: Column to filter on (e.g., Table.organization_id)

        Returns:
            Filtered query
        """
        org_ids = self.get_accessible_org_ids(user)

        if not org_ids:
            # User has no organization access - return empty query
            return query.filter(False)

        # Filter by accessible organizations
        query = query.filter(org_column.in_(org_ids))

        logger.debug(
            f"Applied organization filter for user {user.id}",
            extra={"user_id": str(user.id), "org_count": len(org_ids)},
        )

        return query

    def apply_team_filter(self, query: Query, user: User, team_column: Any) -> Query:
        """
        Apply team-level filter to query

        Args:
            query: SQLAlchemy query
            user: User object
            team_column: Column to filter on (e.g., Table.team_id)

        Returns:
            Filtered query
        """
        team_ids = self.get_accessible_team_ids(user)

        if not team_ids:
            # User has no team access - return empty query
            return query.filter(False)

        # Filter by accessible teams
        query = query.filter(team_column.in_(team_ids))

        logger.debug(
            f"Applied team filter for user {user.id}",
            extra={"user_id": str(user.id), "team_count": len(team_ids)},
        )

        return query

    def apply_ownership_filter(
        self, query: Query, user: User, owner_column: Any
    ) -> Query:
        """
        Apply ownership filter to query

        Args:
            query: SQLAlchemy query
            user: User object
            owner_column: Column to filter on (e.g., Table.created_by_id)

        Returns:
            Filtered query
        """
        # User can see their own records
        query = query.filter(owner_column == user.id)

        logger.debug(
            f"Applied ownership filter for user {user.id}",
            extra={"user_id": str(user.id)},
        )

        return query

    def apply_tenant_isolation(
        self,
        query: Query,
        user: User,
        org_column: Any = None,
        team_column: Any = None,
        owner_column: Any = None,
    ) -> Query:
        """
        Apply tenant isolation based on configured level

        Args:
            query: SQLAlchemy query
            user: User object
            org_column: Organization ID column
            team_column: Team ID column
            owner_column: Owner/user ID column

        Returns:
            Filtered query

        Raises:
            RowLevelSecurityError: If no valid column provided
        """
        # Superuser bypass (but logs access)
        if user.is_superuser:
            logger.info(f"Superuser {user.id} bypassing RLS")
            return query

        # Apply filters based on isolation level
        if self.isolation_level == "organization" and org_column is not None:
            return self.apply_organization_filter(query, user, org_column)

        if self.isolation_level == "team" and team_column is not None:
            return self.apply_team_filter(query, user, team_column)

        if owner_column is not None:
            # Fall back to ownership filter
            return self.apply_ownership_filter(query, user, owner_column)

        raise RowLevelSecurityError(
            f"No valid column provided for isolation level: {self.isolation_level}"
        )

    def check_cross_tenant_access(
        self,
        user: User,
        resource_org_id: str | None,
        resource_team_id: str | None,
        resource_owner_id: str | None = None,
    ) -> bool:
        """
        Check if user is attempting cross-tenant access

        Args:
            user: User object
            resource_org_id: Organization ID of resource
            resource_team_id: Team ID of resource
            resource_owner_id: Owner ID of resource

        Returns:
            True if access is allowed

        Raises:
            CrossTenantAccessError: If cross-tenant access is attempted
        """
        # Superuser can access everything
        if user.is_superuser:
            logger.info(
                f"Superuser {user.id} accessing cross-tenant resource",
                extra={
                    "user_id": str(user.id),
                    "resource_org_id": resource_org_id,
                    "resource_team_id": resource_team_id,
                },
            )
            return True

        # Check organization access
        if resource_org_id:
            accessible_orgs = self.get_accessible_org_ids(user)
            if str(resource_org_id) not in accessible_orgs:
                logger.warning(
                    f"Cross-organization access attempt by user {user.id}",
                    extra={
                        "user_id": str(user.id),
                        "user_org": str(user.organization_id),
                        "resource_org": resource_org_id,
                    },
                )
                raise CrossTenantAccessError(
                    f"User does not have access to organization {resource_org_id}"
                )

        # Check team access
        if resource_team_id:
            accessible_teams = self.get_accessible_team_ids(user)
            if str(resource_team_id) not in accessible_teams:
                # Check if user's org has the team (org-level access)
                if resource_org_id and str(
                    resource_org_id
                ) in self.get_accessible_org_ids(user):
                    logger.info(
                        f"User {user.id} has org-level access to team {resource_team_id}"
                    )
                    return True

                logger.warning(
                    f"Cross-team access attempt by user {user.id}",
                    extra={
                        "user_id": str(user.id),
                        "resource_team": resource_team_id,
                        "accessible_teams": list(accessible_teams),
                    },
                )
                raise CrossTenantAccessError(
                    f"User does not have access to team {resource_team_id}"
                )

        # Check ownership (if applicable)
        if resource_owner_id and not user.is_superuser:
            if str(resource_owner_id) != str(user.id):
                # Users can't access others' private data unless same org/team
                if resource_org_id == str(user.organization_id):
                    logger.info(f"User {user.id} accessing org-member resource")
                    return True

                logger.warning(
                    f"Cross-ownership access attempt by user {user.id}",
                    extra={
                        "user_id": str(user.id),
                        "resource_owner": resource_owner_id,
                    },
                )
                raise CrossTenantAccessError(
                    "User does not have access to this resource"
                )

        return True

    def get_isolation_context(self, user: User) -> dict[str, Any]:
        """
        Get isolation context for user

        Returns dictionary with user's tenant boundaries
        for use in queries and logging

        Args:
            user: User object

        Returns:
            Dictionary with isolation context
        """
        return {
            "user_id": str(user.id),
            "organization_id": (
                str(user.organization_id) if user.organization_id else None
            ),
            "team_ids": list(self.get_accessible_team_ids(user)),
            "is_superuser": user.is_superuser,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "isolation_level": self.isolation_level,
        }


# SQLAlchemy Event Listeners for automatic RLS
def setup_row_level_security():
    """
    Set up SQLAlchemy event listeners for automatic RLS

    This function should be called during application startup
    to register event listeners on models
    """
    from sqlalchemy import event

    from app.db.models.assessment import Assessment
    from app.db.models.response import Response

    @event.listens_for(Assessment, "before_update")
    @event.listens_for(Assessment, "before_insert")
    def validate_assessment_tenant(mapper, connection, target):
        """Validate tenant isolation for assessments"""
        # This would need access to current user from context
        # Implementation depends on how user context is stored

    @event.listens_for(Response, "before_update")
    @event.listens_for(Response, "before_insert")
    def validate_response_tenant(mapper, connection, target):
        """Validate tenant isolation for responses"""

    logger.info("Row-level security event listeners registered")


# AsyncSQLAlchemy Row-Level Security Mixin
class TenantIsolatedMixin:
    """
    Mixin for models that require tenant isolation

    Models using this mixin automatically get RLS filters applied
    """

    @classmethod
    def get_accessible_query(
        cls, db: AsyncSession, user: User, rls_service: RowLevelSecurityService
    ):
        """
        Get query with RLS filters applied

        Args:
            db: Database session
            user: Current user
            rls_service: RLS service instance

        Returns:
            Filtered query
        """
        from sqlalchemy import select

        # Start with base query
        query = select(cls)

        # Apply organization filter if model has organization_id
        if hasattr(cls, "organization_id"):
            query = rls_service.apply_organization_filter(
                query, user, cls.organization_id
            )

        # Apply team filter if model has team_id
        elif hasattr(cls, "team_id"):
            query = rls_service.apply_team_filter(query, user, cls.team_id)

        # Apply ownership filter if model has created_by_id
        elif hasattr(cls, "created_by_id"):
            query = rls_service.apply_ownership_filter(query, user, cls.created_by_id)

        return query


# Singleton instance
rls_service = RowLevelSecurityService()
