"""
Role-Based Access Control (RBAC) API Endpoints

Provides endpoints for managing roles and permissions.
Admin-only access for security.

Access: Administrators only
"""

import logging
from typing import Any, Dict, List, Set
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.permissions import require_super_admin
from app.api.v1.endpoints.users import get_async_db, get_current_user
from app.db.models.user import User
from app.services.permission_service import (
    FieldType,
    Permission,
    Role,
    permission_service,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/rbac", tags=["rbac-management"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class RoleInfo(BaseModel):
    """Role information"""

    name: str
    permissions: Set[str]
    description: str


class PermissionCheckRequest(BaseModel):
    """Request schema for permission check"""

    permission: str
    resource_type: str | None = None
    resource_id: str | None = None


class PermissionCheckResponse(BaseModel):
    """Response schema for permission check"""

    has_permission: bool
    user_roles: Set[str]


class FieldAccessRequest(BaseModel):
    """Request schema for field access check"""

    table_name: str
    field_name: str
    action: str = Permission.READ


class FieldAccessResponse(BaseModel):
    """Response schema for field access check"""

    can_access: bool
    reason: str | None = None


class AssignRoleRequest(BaseModel):
    """Request schema for role assignment"""

    user_id: UUID
    role: str


class RevokeRoleRequest(BaseModel):
    """Request schema for role revocation"""

    user_id: UUID
    role: str


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/roles", response_model=List[RoleInfo])
async def list_roles(
    admin_user: User = Depends(require_super_admin()),
):
    """
    List all available roles and their permissions.

    **Super Admin Only**

    Returns a comprehensive list of all system roles with their
    associated permissions and descriptions.

    **Response:**
    ```json
    [
      {
        "name": "clinician",
        "permissions": ["view_patient_data", "edit_patient_data", ...],
        "description": "Clinical practitioner with patient data access"
      },
      ...
    ]
    ```
    """

    try:
        roles = []

        for role_name, permissions in permission_service.role_permissions.items():
            # Get description
            descriptions = {
                Role.SUPER_ADMIN: "Full system access with all permissions",
                Role.ADMIN: "System administrator with most permissions",
                Role.AUDITOR: "Read-only access for compliance auditing",
                Role.CLINICIAN: "Clinical practitioner with full patient data access",
                Role.THERAPIST: "Therapist with patient data view access",
                Role.PSYCHIATRIST: "Psychiatrist with clinical and prescribing access",
                Role.COUNSELOR: "Counselor with basic patient data access",
                Role.USER: "Regular user with basic access",
                Role.PREMIUM_USER: "Premium user with extended access",
                Role.TEAM_LEAD: "Team leader with team management access",
                Role.TEAM_MEMBER: "Team member with team data access",
                Role.TEAM_VIEWER: "Team viewer with read-only access",
            }

            roles.append(
                RoleInfo(
                    name=role_name,
                    permissions=set(permissions),
                    description=descriptions.get(role_name, ""),
                )
            )

        return roles

    except Exception as e:
        logger.error(f"Failed to list roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")


@router.get("/permissions", response_model=List[str])
async def list_permissions(
    admin_user: User = Depends(require_super_admin()),
):
    """
    List all available permissions.

    **Super Admin Only**

    Returns a list of all system permissions that can be assigned to roles.

    **Response:**
    ```json
    [
      "read",
      "create",
      "update",
      "delete",
      "view_patient_data",
      "edit_patient_data",
      ...
    ]
    ```
    """

    try:
        # Get all permissions from Permission class
        permissions = [
            getattr(Permission, attr)
            for attr in dir(Permission)
            if not attr.startswith("_") and isinstance(getattr(Permission, attr), str)
        ]

        return sorted(set(permissions))

    except Exception as e:
        logger.error(f"Failed to list permissions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list permissions: {str(e)}"
        )


@router.post("/check", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Check if current user has a specific permission.

    Useful for client-side permission checking before attempting actions.

    **Request Body:**
    ```json
    {
      "permission": "view_patient_data",
      "resource_type": "patient",
      "resource_id": "patient-uuid"
    }
    ```

    **Response:**
    ```json
    {
      "has_permission": true,
      "user_roles": ["clinician", "user"]
    }
    ```
    """

    try:
        # Check permission
        has_perm = await permission_service.has_permission(
            db=db,
            user=current_user,
            permission=request.permission,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
        )

        # Get user's roles
        user_roles = await permission_service._get_user_roles(db, current_user)

        return PermissionCheckResponse(
            has_permission=has_perm,
            user_roles=user_roles,
        )

    except Exception as e:
        logger.error(f"Failed to check permission: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check permission: {str(e)}"
        )


@router.post("/check-field-access", response_model=FieldAccessResponse)
async def check_field_access(
    request: FieldAccessRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Check if current user can access a specific field.

    Implements field-level access control for sensitive data.

    **Request Body:**
    ```json
    {
      "table_name": "users",
      "field_name": "email",
      "action": "read"
    }
    ```

    **Response:**
    ```json
    {
      "can_access": true,
      "reason": null
    }
    ```
    """

    try:
        can_access = await permission_service.can_access_field(
            db=db,
            user=current_user,
            table_name=request.table_name,
            field_name=request.field_name,
            action=request.action,
        )

        reason = None
        if not can_access:
            # Determine reason
            field_id = f"{request.table_name}.{request.field_name}"
            field_type = permission_service.protected_fields.get(field_id)

            if field_type == FieldType.PII:
                reason = "Field contains PII - requires user management permission"
            elif field_type == FieldType.PHI:
                reason = "Field contains PHI - requires clinical permission"
            elif field_type == FieldType.ADMIN:
                reason = "Field is admin-only - requires super admin access"
            elif field_type == FieldType.SENSITIVE:
                reason = "Field contains sensitive data - requires elevated permissions"

        return FieldAccessResponse(
            can_access=can_access,
            reason=reason,
        )

    except Exception as e:
        logger.error(f"Failed to check field access: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to check field access: {str(e)}"
        )


@router.get("/protected-fields")
async def list_protected_fields(
    admin_user: User = Depends(require_super_admin()),
):
    """
    List all protected fields and their access levels.

    **Super Admin Only**

    Returns a comprehensive list of fields that require special
    permissions to access.

    **Response:**
    ```json
    {
      "protected_fields": {
        "users.email": {
          "type": "pii",
          "description": "Personal Identifiable Information",
          "required_permission": "edit_user"
        },
        "clinical_screening.responses": {
          "type": "phi",
          "description": "Protected Health Information",
          "required_permission": "view_patient_data"
        },
        ...
      },
      "total_fields": 15
    }
    ```
    """

    try:
        protected_fields_info = {}

        for field_id, field_type in permission_service.protected_fields.items():
            descriptions = {
                FieldType.PII: "Personal Identifiable Information",
                FieldType.PHI: "Protected Health Information",
                FieldType.SENSITIVE: "Sensitive business data",
                FieldType.PUBLIC: "Non-sensitive data",
                FieldType.ADMIN: "Admin-only data",
            }

            # Determine required permission
            required_perm = None
            if field_type == FieldType.PII:
                required_perm = Permission.EDIT_USER
            elif field_type == FieldType.PHI:
                required_perm = Permission.VIEW_PATIENT_DATA
            elif field_type == FieldType.ADMIN:
                required_perm = Permission.MANAGE_SYSTEM
            elif field_type == FieldType.SENSITIVE:
                required_perm = Permission.VIEW_ANALYTICS

            protected_fields_info[field_id] = {
                "type": field_type,
                "description": descriptions.get(field_type, ""),
                "required_permission": required_perm,
            }

        return {
            "protected_fields": protected_fields_info,
            "total_fields": len(protected_fields_info),
        }

    except Exception as e:
        logger.error(f"Failed to list protected fields: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list protected fields: {str(e)}"
        )


@router.post("/roles/assign")
async def assign_role(
    request: AssignRoleRequest,
    admin_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Assign a role to a user.

    **Super Admin Only**

    Grants a user an additional role. The role's permissions will
    be added to the user's existing permissions.

    **Request Body:**
    ```json
    {
      "user_id": "user-uuid",
      "role": "clinician"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "message": "Role 'clinician' assigned to user successfully",
      "user_id": "user-uuid",
      "role": "clinician"
    }
    ```
    """

    try:
        success = await permission_service.assign_role(
            db=db,
            user_id=request.user_id,
            role=request.role,
            assigned_by=admin_user,
        )

        if not success:
            raise HTTPException(
                status_code=400, detail=f"Failed to assign role '{request.role}'"
            )

        return {
            "success": True,
            "message": f"Role '{request.role}' assigned to user successfully",
            "user_id": str(request.user_id),
            "role": request.role,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}")


@router.post("/roles/revoke")
async def revoke_role(
    request: RevokeRoleRequest,
    admin_user: User = Depends(require_super_admin()),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Revoke a role from a user.

    **Super Admin Only**

    Removes a role from a user. The role's permissions will be
    removed from the user's permissions.

    **Request Body:**
    ```json
    {
      "user_id": "user-uuid",
      "role": "clinician"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "message": "Role 'clinician' revoked from user successfully",
      "user_id": "user-uuid",
      "role": "clinician"
    }
    ```
    """

    try:
        success = await permission_service.revoke_role(
            db=db,
            user_id=request.user_id,
            role=request.role,
            revoked_by=admin_user,
        )

        if not success:
            raise HTTPException(
                status_code=400, detail=f"Failed to revoke role '{request.role}'"
            )

        return {
            "success": True,
            "message": f"Role '{request.role}' revoked from user successfully",
            "user_id": str(request.user_id),
            "role": request.role,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke role: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to revoke role: {str(e)}")


@router.get("/my-permissions")
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get current user's permissions.

    Returns all permissions granted to the current user through
    their roles.

    **Response:**
    ```json
    {
      "user_id": "user-uuid",
      "roles": ["clinician", "user"],
      "permissions": [
        "view_patient_data",
        "edit_patient_data",
        "view_clinical_notes",
        "take_assessment",
        ...
      ],
      "total_permissions": 15
    }
    ```
    """

    try:
        # Get user's roles
        user_roles = await permission_service._get_user_roles(db, current_user)

        # Collect all permissions from user's roles
        user_permissions = set()
        for role in user_roles:
            role_perms = permission_service.role_permissions.get(role, set())
            user_permissions.update(role_perms)

        return {
            "user_id": str(current_user.id),
            "roles": list(user_roles),
            "permissions": list(user_permissions),
            "total_permissions": len(user_permissions),
        }

    except Exception as e:
        logger.error(f"Failed to get user permissions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get permissions: {str(e)}"
        )
