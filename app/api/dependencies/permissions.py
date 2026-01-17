"""
Permission Dependencies for FastAPI

Provides dependency functions for enforcing RBAC in API endpoints.
Usage:
    @router.get("/protected")
    async def protected_endpoint(
        current_user: User = Depends(get_current_user),
        _: None = Depends(require_permission(Permission.VIEW_PATIENT_DATA))
    ):
        # Endpoint logic
"""

from typing import Optional, Union
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_async_db
from app.db.models.user import User
from app.services.permission_service import permission_service, Permission


# =============================================================================
# Permission Dependencies
# =============================================================================

def require_permission(permission: str, resource_type: Optional[str] = None):
    """
    Dependency that requires a specific permission.

    Args:
        permission: Required permission
        resource_type: Optional resource type for resource-level checks

    Returns:
        Dependency function

    Usage:
        @router.get("/admin")
        async def admin_endpoint(
            _: None = Depends(require_permission(Permission.MANAGE_SYSTEM))
        ):
            return {"message": "Admin access granted"}
    """

    async def check_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Check if user has required permission"""
        has_perm = await permission_service.has_permission(
            db=db,
            user=current_user,
            permission=permission,
            resource_type=resource_type,
        )

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )

    return check_permission


def require_roles(*roles: str):
    """
    Dependency that requires one of the specified roles.

    Args:
        *roles: Allowed roles

    Returns:
        Dependency function

    Usage:
        @router.get("/clinician-only")
        async def clinician_endpoint(
            _: None = Depends(require_roles(Role.CLINICIAN, Role.PSYCHIATRIST))
        ):
            return {"message": "Clinician access granted"}
    """

    async def check_roles(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Check if user has one of the required roles"""
        user_roles = await permission_service._get_user_roles(db, current_user)

        # Check if user has any of the required roles
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: one of {', '.join(roles)}"
            )

    return check_roles


def require_super_admin():
    """
    Dependency that requires super admin access.

    Usage:
        @router.delete("/users/{user_id}")
        async def delete_user(
            _: None = Depends(require_super_admin())
        ):
            return {"message": "Super admin access granted"}
    """

    async def check_super_admin(
        current_user: User = Depends(get_current_user),
    ) -> None:
        """Check if user is super admin"""
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )

    return check_super_admin


def can_access_field(table_name: str, field_name: str, action: str = Permission.READ):
    """
    Dependency that checks field-level access.

    Usage:
        @router.get("/users/{user_id}")
        async def get_user(
            user_id: UUID,
            _: None = Depends(can_access_field("users", "email")),
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_db),
        ):
            # User can only access the email field if they have permission
            return {"email": user.email}
    """

    async def check_field_access(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Check if user can access the field"""
        has_access = await permission_service.can_access_field(
            db=db,
            user=current_user,
            table_name=table_name,
            field_name=field_name,
            action=action,
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required to access {table_name}.{field_name}"
            )

    return check_field_access


def filter_fields_by_permission(table_name: str, fields: list, action: str = Permission.READ):
    """
    Dependency that filters fields based on user permissions.

    Returns only fields the user has access to.

    Usage:
        @router.get("/users/me")
        async def get_current_user(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_db),
            accessible_fields: list = Depends(
                filter_fields_by_permission(
                    "users",
                    ["id", "email", "full_name", "ssn"],
                    Permission.READ
                )
            ),
        ):
            # Only return fields user has access to
            return {
                field: getattr(current_user, field)
                for field in accessible_fields
            }
    """

    async def get_accessible_fields(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> list:
        """Return list of fields user can access"""
        return await permission_service.filter_protected_fields(
            db=db,
            user=current_user,
            table_name=table_name,
            fields=fields,
            action=action,
        )

    return get_accessible_fields


# =============================================================================
# Owner-Based Access Control
# =============================================================================

def require_owner_or_permission(
    permission: str,
    resource_type: str,
    get_owner_id_func,
):
    """
    Dependency that allows access if user is the resource owner or has permission.

    Args:
        permission: Required permission for non-owners
        resource_type: Type of resource
        get_owner_id_func: Function that extracts owner_id from request

    Usage:
        def get_assessment_owner_id(assessment_id: UUID) -> UUID:
            # Query database for assessment owner
            assessment = db.get(Assessment, assessment_id)
            return assessment.user_id

        @router.get("/assessments/{assessment_id}")
        async def get_assessment(
            assessment_id: UUID,
            _: None = Depends(
                require_owner_or_permission(
                    Permission.VIEW_ASSESSMENT_RESULTS,
                    "assessment",
                    lambda: get_assessment_owner_id(assessment_id)
                )
            ),
            current_user: User = Depends(get_current_user),
        ):
            return assessment
    """

    async def check_ownership_or_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Check if user is owner or has permission"""
        # Get the owner ID
        owner_id = await get_owner_id_func()

        # Check if user is the owner
        if str(owner_id) == str(current_user.id):
            return

        # Not the owner, check permission
        has_perm = await permission_service.has_permission(
            db=db,
            user=current_user,
            permission=permission,
            resource_type=resource_type,
            resource_id=owner_id,
        )

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Must be resource owner or have {permission} permission"
            )

    return check_ownership_or_permission


# =============================================================================
# Team-Based Access Control
# =============================================================================

def require_team_member_or_permission(
    permission: str,
    get_team_id_func,
):
    """
    Dependency that allows access if user is a team member or has permission.

    Args:
        permission: Required permission for non-members
        get_team_id_func: Function that extracts team_id from request

    Usage:
        @router.get("/teams/{team_id}/analytics")
        async def get_team_analytics(
            team_id: UUID,
            _: None = Depends(
                require_team_member_or_permission(
                    Permission.VIEW_ANALYTICS,
                    lambda: team_id
                )
            ),
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_async_db),
        ):
            return team_analytics
    """

    async def check_team_membership_or_permission(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db),
    ) -> None:
        """Check if user is team member or has permission"""
        # Get the team ID
        team_id = await get_team_id_func()

        # TODO: Query team membership
        # For now, just check permission
        has_perm = await permission_service.has_permission(
            db=db,
            user=current_user,
            permission=permission,
            resource_type="team",
            resource_id=team_id,
        )

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Must be team member or have {permission} permission"
            )

    return check_team_membership_or_permission
