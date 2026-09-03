"""
Authorization Service - Role-Based Access Control

Single Responsibility: Handle ALL authorization and permission operations
- Role checking (has_role)
- Permission verification
- Resource ownership verification (is_owner)
- Team membership checking (is_team_member)
- Access control decisions

This service follows SOLID principles:
- SRP: Only handles authorization decisions
- OCP: Pluggable permission strategies
- DIP: Depends on abstractions, not concrete models

Author: Security Team
Version: 1.0 (Extracted from security.py)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

from app.db.models.team import Team
from app.db.models.user import User

# =============================================================================
# Data Classes & Enums
# =============================================================================


class Role(Enum):
    """Standard roles in the system"""

    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    MANAGER = "manager"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions for fine-grained access control"""

    # User permissions
    READ_OWN_PROFILE = "read_own_profile"
    UPDATE_OWN_PROFILE = "update_own_profile"
    DELETE_OWN_PROFILE = "delete_own_profile"

    # Team permissions
    READ_TEAM = "read_team"
    UPDATE_TEAM = "update_team"
    DELETE_TEAM = "delete_team"
    MANAGE_TEAM_MEMBERS = "manage_team_members"

    # Organization permissions
    READ_ORGANIZATION = "read_organization"
    UPDATE_ORGANIZATION = "update_organization"
    MANAGE_ORGANIZATION_MEMBERS = "manage_organization_members"

    # Assessment permissions
    CREATE_ASSESSMENT = "create_assessment"
    READ_ASSESSMENT = "read_assessment"
    UPDATE_ASSESSMENT = "update_assessment"
    DELETE_ASSESSMENT = "delete_assessment"
    PUBLISH_ASSESSMENT = "publish_assessment"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SYSTEM_SETTINGS = "manage_system_settings"


class AccessDecision(Enum):
    """Access control decision"""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"  # No decision, defer to other checks


@dataclass
class AuthorizationResult:
    """Result of an authorization check"""

    decision: AccessDecision
    reason: str | None = None
    permissions_used: List[Permission] | None = None


# =============================================================================
# Authorization Service
# =============================================================================


class AuthorizationService:
    """
    Enterprise-grade authorization service for access control.

    Responsibilities:
    - Check if user has required role
    - Verify user permissions for resources
    - Check resource ownership
    - Verify team membership
    - Make access control decisions

    Usage:
        service = AuthorizationService()

        # Check role
        if service.has_role(user, Role.ADMIN):
            # User is admin

        # Check ownership
        if service.is_owner(user, resource):
            # User owns the resource

        # Check team membership
        if service.is_team_member(user, team):
            # User is a team member
    """

    def __init__(self):
        """Initialize authorization service."""
        self._logger = logging.getLogger("app.security.authorization")

        # Role hierarchy (higher roles inherit lower role permissions)
        self._role_hierarchy = {
            Role.GUEST: 0,
            Role.USER: 1,
            Role.MODERATOR: 2,
            Role.MANAGER: 3,
            Role.ADMIN: 4,
        }

        # Role to permissions mapping
        self._role_permissions = self._build_role_permissions()

    def has_role(self, user: User, role: str | Role) -> bool:
        """
        Check if user has required role.

        Args:
            user: User object
            role: Required role (string or Role enum)

        Returns:
            True if user has required role or higher role in hierarchy

        Examples:
            >>> service.has_role(user, "admin")
            True
            >>> service.has_role(user, Role.MODERATOR)
            False
        """
        if not user or not user.role:
            return False

        # Convert to Role enum if string
        if isinstance(role, str):
            try:
                required_role = Role(role.lower())
            except ValueError:
                self._logger.warning(f"Unknown role: {role}")
                return False
        else:
            required_role = role

        # Get user's role
        try:
            user_role = Role(user.role.lower())
        except ValueError:
            self._logger.warning(f"User has invalid role: {user.role}")
            return False

        # Check if user's role is at least the required level
        user_level = self._role_hierarchy.get(user_role, -1)
        required_level = self._role_hierarchy.get(required_role, -1)

        return user_level >= required_level

    def has_permission(self, user: User, permission: Permission) -> bool:
        """
        Check if user has specific permission.

        Args:
            user: User object
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise

        Note:
            Permissions are role-based. Higher roles inherit all
            permissions from lower roles.
        """
        if not user or not user.role:
            return False

        # Get user's role
        try:
            user_role = Role(user.role.lower())
        except ValueError:
            return False

        # Get permissions for user's role and all lower roles
        user_permissions = set()
        for role, level in self._role_hierarchy.items():
            if level <= self._role_hierarchy[user_role]:
                user_permissions.update(self._role_permissions.get(role, set()))

        return permission in user_permissions

    def has_any_permission(self, user: User, permissions: List[Permission]) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has at least one permission
        """
        return any(self.has_permission(user, perm) for perm in permissions)

    def has_all_permissions(self, user: User, permissions: List[Permission]) -> bool:
        """
        Check if user has all of the specified permissions.

        Args:
            user: User object
            permissions: List of permissions to check

        Returns:
            True if user has all permissions
        """
        return all(self.has_permission(user, perm) for perm in permissions)

    def is_owner(
        self, user: User, resource: Any, owner_field: str = "created_by_id"
    ) -> bool:
        """
        Check if user owns a resource.

        Args:
            user: User object
            resource: Resource object (e.g., Assessment, Team)
            owner_field: Field name that contains the owner ID (default: "created_by_id")

        Returns:
            True if user owns the resource

        Examples:
            >>> service.is_owner(user, assessment)
            True
            >>> service.is_owner(user, team, owner_field="owner_id")
            False
        """
        if not user or not resource:
            return False

        # Get owner ID from resource
        owner_id = getattr(resource, owner_field, None)

        if owner_id is None:
            return False

        # Compare with user ID
        return str(owner_id) == str(user.id)

    def can_modify_resource(self, user: User, resource: Any) -> AuthorizationResult:
        """
        Determine if user can modify a resource.

        Args:
            user: User object
            resource: Resource to modify

        Returns:
            AuthorizationResult with decision and reason

        Access Rules:
            1. Admin can modify anything
            2. Owner can modify own resources
            3. Otherwise, deny
        """
        # Admin can do anything
        if self.has_role(user, Role.ADMIN):
            return AuthorizationResult(
                decision=AccessDecision.ALLOW,
                reason="User has admin role",
                permissions_used=[Permission.MANAGE_SYSTEM_SETTINGS],
            )

        # Owner can modify own resources
        if self.is_owner(user, resource):
            return AuthorizationResult(
                decision=AccessDecision.ALLOW,
                reason="User owns the resource",
                permissions_used=[Permission.UPDATE_OWN_PROFILE],
            )

        # Deny access
        return AuthorizationResult(
            decision=AccessDecision.DENY,
            reason="User does not have permission to modify this resource",
            permissions_used=[],
        )

    def is_team_member(self, user: User, team: Team) -> bool:
        """
        Check if user is a member of a team.

        Args:
            user: User object
            team: Team object

        Returns:
            True if user is a member of the team

        Examples:
            >>> service.is_team_member(user, team)
            True
        """
        if not user or not team:
            return False

        # Check if team has members attribute
        if not hasattr(team, "members"):
            return False

        # Check if user is in team members
        return any(member.id == user.id for member in team.members)

    def is_team_admin(self, user: User, team: Team) -> bool:
        """
        Check if user is an admin of a team.

        Args:
            user: User object
            team: Team object

        Returns:
            True if user is a team admin
        """
        if not user or not team:
            return False

        # Check if team has members attribute
        if not hasattr(team, "members"):
            return False

        # Check if user is in team members with admin role
        for member in team.members:
            if member.id == user.id:
                # Check if member has admin role in team
                member_role = getattr(member, "role", None)
                return member_role in ("admin", "owner")

        return False

    def can_access_team(
        self, user: User, team: Team, permission: Permission = Permission.READ_TEAM
    ) -> bool:
        """
        Check if user can access team with specified permission.

        Args:
            user: User object
            team: Team object
            permission: Permission required (default: READ_TEAM)

        Returns:
            True if user can access team

        Access Rules:
            - Admin can access any team
            - Team members can read team
            - Team admins can manage team
        """
        # Admin can access anything
        if self.has_role(user, Role.ADMIN):
            return True

        # Check team membership
        if not self.is_team_member(user, team):
            return False

        # Team admins can do anything
        if self.is_team_admin(user, team):
            return True

        # Regular members can only read
        if permission == Permission.READ_TEAM:
            return True

        # Deny other permissions for regular members
        return False

    def _build_role_permissions(self) -> dict[Role, set[Permission]]:
        """
        Build permission mapping for each role.

        Returns:
            Dictionary mapping roles to their permissions
        """
        return {
            Role.GUEST: {
                Permission.READ_OWN_PROFILE,
            },
            Role.USER: {
                # User profile permissions
                Permission.READ_OWN_PROFILE,
                Permission.UPDATE_OWN_PROFILE,
                # Team permissions (read only)
                Permission.READ_TEAM,
                # Assessment permissions (create, read, update own)
                Permission.CREATE_ASSESSMENT,
                Permission.READ_ASSESSMENT,
            },
            Role.MODERATOR: {
                # Inherit all USER permissions
                Permission.READ_OWN_PROFILE,
                Permission.UPDATE_OWN_PROFILE,
                # Enhanced team permissions
                Permission.READ_TEAM,
                Permission.UPDATE_TEAM,
                # Enhanced assessment permissions
                Permission.CREATE_ASSESSMENT,
                Permission.READ_ASSESSMENT,
                Permission.UPDATE_ASSESSMENT,
                Permission.DELETE_ASSESSMENT,
            },
            Role.MANAGER: {
                # All moderator permissions
                Permission.READ_OWN_PROFILE,
                Permission.UPDATE_OWN_PROFILE,
                # Full team management
                Permission.READ_TEAM,
                Permission.UPDATE_TEAM,
                Permission.MANAGE_TEAM_MEMBERS,
                # Full assessment management
                Permission.CREATE_ASSESSMENT,
                Permission.READ_ASSESSMENT,
                Permission.UPDATE_ASSESSMENT,
                Permission.DELETE_ASSESSMENT,
                Permission.PUBLISH_ASSESSMENT,
                # Organization management
                Permission.READ_ORGANIZATION,
                Permission.UPDATE_ORGANIZATION,
                Permission.MANAGE_ORGANIZATION_MEMBERS,
            },
            Role.ADMIN: {
                # Admins have ALL permissions
                # User permissions
                Permission.READ_OWN_PROFILE,
                Permission.UPDATE_OWN_PROFILE,
                Permission.DELETE_OWN_PROFILE,
                # Team permissions
                Permission.READ_TEAM,
                Permission.UPDATE_TEAM,
                Permission.DELETE_TEAM,
                Permission.MANAGE_TEAM_MEMBERS,
                # Organization permissions
                Permission.READ_ORGANIZATION,
                Permission.UPDATE_ORGANIZATION,
                Permission.MANAGE_ORGANIZATION_MEMBERS,
                # Assessment permissions
                Permission.CREATE_ASSESSMENT,
                Permission.READ_ASSESSMENT,
                Permission.UPDATE_ASSESSMENT,
                Permission.DELETE_ASSESSMENT,
                Permission.PUBLISH_ASSESSMENT,
                # Admin permissions
                Permission.MANAGE_USERS,
                Permission.MANAGE_ROLES,
                Permission.VIEW_AUDIT_LOGS,
                Permission.MANAGE_SYSTEM_SETTINGS,
            },
        }


# =============================================================================
# Default Instance (Backward Compatibility)
# =============================================================================

_default_service: AuthorizationService | None = None


def get_authorization_service() -> AuthorizationService:
    """Get default authorization service instance (singleton pattern)."""
    global _default_service
    if _default_service is None:
        _default_service = AuthorizationService()
    return _default_service


# =============================================================================
# Convenience Functions (Backward Compatibility)
# =============================================================================


def has_role(user: User, role: str) -> bool:
    """Check if user has role using default service."""
    return get_authorization_service().has_role(user, role)


def is_owner(user: User, resource: Any) -> bool:
    """Check if user owns resource using default service."""
    return get_authorization_service().is_owner(user, resource)


def is_team_member(user: User, team: Team) -> bool:
    """Check if user is team member using default service."""
    return get_authorization_service().is_team_member(user, team)


def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions for endpoint access.

    Usage:
        @require_permissions("monitoring:read")
        async def get_metrics(user=Depends(get_current_user)):
            ...

    Args:
        *permissions: Permission strings required (e.g., "monitoring:read")

    Returns:
        Decorator function
    """
    from fastapi import HTTPException, status

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            user = kwargs.get("user") or kwargs.get("current_user")

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # For string permissions, do simple admin check
            # In production, you'd map these to Permission enum values
            if hasattr(user, "role") and user.role and user.role.lower() == "admin":
                return await func(*args, **kwargs)

            # Check if user has monitoring permissions
            auth_svc = get_authorization_service()
            for perm_str in permissions:
                # Convert "resource:action" format to permission check
                if hasattr(user, "permissions") and perm_str in user.permissions:
                    return await func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {', '.join(permissions)}",
            )

        return wrapper

    return decorator
