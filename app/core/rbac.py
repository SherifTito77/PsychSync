"""
Role-Based Access Control (RBAC) System

Provides comprehensive permission management with:
- Granular permissions for each resource
- Role assignments with inheritance
- Permission checking decorators
- Audit logging for authorization decisions

SECURITY PRINCIPLES:
- Least privilege: Grant minimum necessary access
- Separation of duties: Critical actions require multiple roles
- Defense in depth: Multiple authorization layers

Author: Security Team
Version: 2.0 Enterprise
"""

import enum
import logging
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from fastapi import HTTPException, status

from app.db.models.user import User, UserRole

logger = logging.getLogger(__name__)


class Permission(enum.Enum):
    """Granular permissions for all resources"""

    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_IMPERSONATE = "user:impersonate"

    # Organization Management
    ORG_CREATE = "organization:create"
    ORG_READ = "organization:read"
    ORG_UPDATE = "organization:update"
    ORG_DELETE = "organization:delete"
    ORG_MANAGE_MEMBERS = "organization:manage_members"

    # Team Management
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_MANAGE_MEMBERS = "team:manage_members"

    # Assessment Management
    ASSESSMENT_CREATE = "assessment:create"
    ASSESSMENT_READ = "assessment:read"
    ASSESSMENT_UPDATE = "assessment:update"
    ASSESSMENT_DELETE = "assessment:delete"
    ASSESSMENT_PUBLISH = "assessment:publish"

    # Response Management
    RESPONSE_CREATE = "response:create"
    RESPONSE_READ = "response:read"
    RESPONSE_UPDATE = "response:update"
    RESPONSE_DELETE = "response:delete"
    RESPONSE_EXPORT = "response:export"

    # Template Management
    TEMPLATE_CREATE = "template:create"
    TEMPLATE_READ = "template:read"
    TEMPLATE_UPDATE = "template:update"
    TEMPLATE_DELETE = "template:delete"

    # Analytics & Reporting
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    REPORTING_CREATE = "reporting:create"
    REPORTING_VIEW = "reporting:view"

    # Security & Compliance
    SECURITY_AUDIT_LOG = "security:audit_log"
    SECURITY_MANAGE_ROLES = "security:manage_roles"
    SECURITY_VIEW_INCIDENTS = "security:view_incidents"

    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"

    # Clinical/Sensitive Data (Higher Security)
    CLINICAL_DATA_VIEW = "clinical:view"
    CLINICAL_DATA_CREATE = "clinical:create"
    CLINICAL_DATA_UPDATE = "clinical:update"
    CLINICAL_PATIENT_ACCESS = "clinical:patient_access"

    # Email/Communication
    EMAIL_SEND = "email:send"
    EMAIL_VIEW = "email:view"
    EMAIL_ANALYZE = "email:analyze"


@dataclass
class RoleDefinition:
    """Role definition with permissions"""

    name: str
    permissions: set[Permission]
    description: str
    inherits_from: set[str] | None = None


# Role Definitions with Inheritance
ROLE_DEFINITIONS: dict[str, RoleDefinition] = {
    # Super Admin - All permissions
    "super_admin": RoleDefinition(
        name="super_admin",
        permissions=set(Permission),  # ALL permissions
        description="Full system access",
    ),
    # Organization Admin - Org-level management
    "org_admin": RoleDefinition(
        name="org_admin",
        permissions={
            # User Management (org-scoped)
            Permission.USER_CREATE,
            Permission.USER_READ,
            Permission.USER_UPDATE,
            Permission.ORG_MANAGE_MEMBERS,
            # Organization Management
            Permission.ORG_READ,
            Permission.ORG_UPDATE,
            # Team Management
            Permission.TEAM_CREATE,
            Permission.TEAM_READ,
            Permission.TEAM_UPDATE,
            Permission.TEAM_DELETE,
            Permission.TEAM_MANAGE_MEMBERS,
            # Assessment Management
            Permission.ASSESSMENT_CREATE,
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_UPDATE,
            Permission.ASSESSMENT_DELETE,
            Permission.ASSESSMENT_PUBLISH,
            # Response Management
            Permission.RESPONSE_READ,
            Permission.RESPONSE_UPDATE,
            Permission.RESPONSE_EXPORT,
            # Template Management
            Permission.TEMPLATE_CREATE,
            Permission.TEMPLATE_READ,
            Permission.TEMPLATE_UPDATE,
            Permission.TEMPLATE_DELETE,
            # Analytics
            Permission.ANALYTICS_VIEW,
            Permission.ANALYTICS_EXPORT,
            Permission.REPORTING_CREATE,
            Permission.REPORTING_VIEW,
        },
        description="Organization administrator",
    ),
    # Team Lead - Team-level management
    "team_lead": RoleDefinition(
        name="team_lead",
        permissions={
            # Team Management (team-scoped)
            Permission.TEAM_READ,
            Permission.TEAM_UPDATE,
            Permission.TEAM_MANAGE_MEMBERS,
            # Assessment Management
            Permission.ASSESSMENT_CREATE,
            Permission.ASSESSMENT_READ,
            Permission.ASSESSMENT_UPDATE,
            # Response Management
            Permission.RESPONSE_CREATE,
            Permission.RESPONSE_READ,
            Permission.RESPONSE_UPDATE,
            # Analytics
            Permission.ANALYTICS_VIEW,
            Permission.REPORTING_VIEW,
        },
        description="Team lead with team-scoped access",
    ),
    # Standard User - Basic access
    "user": RoleDefinition(
        name="user",
        permissions={
            # Basic read access
            Permission.USER_READ,
            Permission.ORG_READ,
            Permission.TEAM_READ,
            # Assessment participation
            Permission.ASSESSMENT_READ,
            Permission.RESPONSE_CREATE,
            Permission.RESPONSE_READ,
            Permission.RESPONSE_UPDATE,  # Own responses only
            # Templates
            Permission.TEMPLATE_READ,
        },
        description="Standard user",
    ),
    # Analyst - Read-only analytics access
    "analyst": RoleDefinition(
        name="analyst",
        permissions={
            Permission.USER_READ,
            Permission.ORG_READ,
            Permission.TEAM_READ,
            Permission.ASSESSMENT_READ,
            Permission.RESPONSE_READ,
            Permission.RESPONSE_EXPORT,
            Permission.ANALYTICS_VIEW,
            Permission.ANALYTICS_EXPORT,
            Permission.REPORTING_CREATE,
            Permission.REPORTING_VIEW,
        },
        description="Analytics and reporting access",
    ),
    # Clinician - Clinical data access
    "clinician": RoleDefinition(
        name="clinician",
        permissions={
            Permission.USER_READ,
            Permission.ORG_READ,
            Permission.CLINICAL_DATA_VIEW,
            Permission.CLINICAL_DATA_CREATE,
            Permission.CLINICAL_DATA_UPDATE,
            Permission.CLINICAL_PATIENT_ACCESS,
            Permission.ASSESSMENT_READ,
            Permission.RESPONSE_READ,
        },
        description="Clinical practitioner access",
    ),
}


class RBACService:
    """
    Role-Based Access Control Service

    Handles:
    - Permission checking for users
    - Role resolution with inheritance
    - Resource ownership validation
    - Authorization decision logging
    """

    def __init__(self):
        """Initialize RBAC service"""
        self.role_definitions = ROLE_DEFINITIONS

    def get_user_permissions(self, user: User) -> set[Permission]:
        """
        Get all permissions for a user based on role

        Args:
            user: User object

        Returns:
            Set of permissions
        """
        # Get user's role
        role = user.role.value if hasattr(user.role, "value") else user.role

        # Get role definition
        role_def = self.role_definitions.get(role)

        if not role_def:
            logger.warning(f"Unknown role: {role} for user {user.id}")
            return set()

        # Start with direct permissions
        permissions = role_def.permissions.copy()

        # Add inherited permissions (if any)
        if role_def.inherits_from:
            for parent_role in role_def.inherits_from:
                parent_def = self.role_definitions.get(parent_role)
                if parent_def:
                    permissions.update(parent_def.permissions)

        # Superuser gets everything
        if user.is_superuser:
            permissions = set(Permission)

        return permissions

    def has_permission(self, user: User, required_permission: Permission) -> bool:
        """
        Check if user has specific permission

        Args:
            user: User object
            required_permission: Permission to check

        Returns:
            True if user has permission
        """
        permissions = self.get_user_permissions(user)
        has_perm = required_permission in permissions

        # Log authorization decision
        logger.debug(
            f"Authorization check: user={user.id}, "
            f"permission={required_permission.value}, granted={has_perm}"
        )

        return has_perm

    def has_all_permissions(
        self, user: User, required_permissions: list[Permission]
    ) -> bool:
        """
        Check if user has ALL specified permissions

        Args:
            user: User object
            required_permissions: List of permissions to check

        Returns:
            True if user has all permissions
        """
        return all(self.has_permission(user, perm) for perm in required_permissions)

    def has_any_permission(
        self, user: User, required_permissions: list[Permission]
    ) -> bool:
        """
        Check if user has ANY of the specified permissions

        Args:
            user: User object
            required_permissions: List of permissions to check

        Returns:
            True if user has any permission
        """
        return any(self.has_permission(user, perm) for perm in required_permissions)

    def check_ownership(self, user: User, resource_user_id: str) -> bool:
        """
        Check if user owns a resource

        Args:
            user: Current user
            resource_user_id: ID of user who owns the resource

        Returns:
            True if user owns resource or is admin
        """
        # User owns their own resources
        if str(user.id) == str(resource_user_id):
            return True

        # Admins can access all resources
        if user.is_superuser or user.role == UserRole.ADMIN:
            return True

        return False

    def can_modify_user(self, current_user: User, target_user: User) -> bool:
        """
        Check if current user can modify target user

        Args:
            current_user: User attempting modification
            target_user: User being modified

        Returns:
            True if modification is allowed
        """
        # Superuser can modify anyone
        if current_user.is_superuser:
            return True

        # Can't modify superusers
        if target_user.is_superuser:
            return False

        # Admins can modify non-admins
        if current_user.role == UserRole.ADMIN:
            return target_user.role != UserRole.ADMIN

        # Users can only modify themselves
        return current_user.id == target_user.id

    def get_accessible_resources(
        self, user: User, resource_type: str
    ) -> dict[str, Any]:
        """
        Get list of resources user can access based on role

        Args:
            user: User object
            resource_type: Type of resource (team, organization, etc.)

        Returns:
            Dictionary with accessible resource IDs
        """
        # This would typically query the database
        # For now, return empty dict - to be implemented based on needs
        return {}


# Singleton instance
rbac_service = RBACService()


# Decorators for authorization
def require_permission(permission: Permission):
    """
    Decorator to require specific permission

    Usage:
        @require_permission(Permission.USER_CREATE)
        async def create_user(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not rbac_service.has_permission(current_user, permission):
                logger.warning(
                    f"Access denied: user {current_user.id} lacks {permission.value}",
                    extra={
                        "user_id": str(current_user.id),
                        "permission": permission.value,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(*permissions: Permission):
    """
    Decorator to require ALL specified permissions

    Usage:
        @require_all_permissions(Permission.USER_CREATE, Permission.USER_READ)
        async def create_and_read_user(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not rbac_service.has_all_permissions(current_user, list(permissions)):
                missing = [
                    p.value
                    for p in permissions
                    if not rbac_service.has_permission(current_user, p)
                ]
                logger.warning(
                    f"Access denied: user {current_user.id} lacks permissions {missing}",
                    extra={"user_id": str(current_user.id), "missing": missing},
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permissions required: {', '.join(missing)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: UserRole):
    """
    Decorator to require specific role(s)

    Usage:
        @require_role(UserRole.ADMIN, UserRole.ORG_ADMIN)
        async def admin_only_function(...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Superuser bypasses role checks
            if current_user.is_superuser:
                return await func(*args, **kwargs)

            user_role = current_user.role
            if user_role not in roles:
                logger.warning(
                    f"Access denied: user {current_user.id} has role {user_role}, "
                    f"required one of {[r.value for r in roles]}",
                    extra={
                        "user_id": str(current_user.id),
                        "user_role": user_role.value,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: one of {', '.join([r.value for r in roles])}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
