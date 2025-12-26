"""
Attribute-Based Access Control (ABAC) System

Provides dynamic authorization based on:
- User attributes (department, location, clearance level)
- Resource attributes (classification, owner, team)
- Environmental context (time, location, device)

Works WITH RBAC to provide defense-in-depth

SECURITY PRINCIPLES:
- Dynamic policy evaluation
- Context-aware access decisions
- Time-based restrictions
- Location-based restrictions
- Device trust verification

Author: Security Team
Version: 1.0 Enterprise
"""

import enum
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, time
from dataclasses import dataclass
from fastapi import HTTPException, status, Request

from app.db.models.user import User

logger = logging.getLogger(__name__)


class ClearanceLevel(enum.Enum):
    """Security clearance levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class DataClassification(enum.Enum):
    """Data classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DeviceTrust(enum.Enum):
    """Device trust levels"""
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


@dataclass
class UserAttributes:
    """User attributes for ABAC"""
    user_id: str
    role: str
    clearance_level: Optional[ClearanceLevel]
    department: Optional[str]
    location: Optional[str]
    manager_id: Optional[str]
    team_ids: Set[str]
    organization_id: Optional[str]
    is_superuser: bool


@dataclass
class ResourceAttributes:
    """Resource attributes for ABAC"""
    resource_id: str
    resource_type: str
    classification: DataClassification
    owner_id: str
    team_id: Optional[str]
    organization_id: Optional[str]
    created_at: datetime
    requires_clearance: Optional[ClearanceLevel] = None


@dataclass
class EnvironmentalContext:
    """Environmental context for ABAC"""
    current_time: datetime
    ip_address: str
    user_agent: str
    device_trust: DeviceTrust
    location: Optional[str] = None
    is_business_hours: bool = False
    is_on_premise: bool = False


class AccessPolicy:
    """
    Access policy for ABAC evaluation

    Combines user, resource, and environmental attributes
    to make dynamic access decisions
    """

    def __init__(
        self,
        name: str,
        description: str,
        condition: callable,
        denial_reason: str = "Access denied by policy"
    ):
        self.name = name
        self.description = description
        self.condition = condition
        self.denial_reason = denial_reason

    def evaluate(
        self,
        user_attrs: UserAttributes,
        resource_attrs: ResourceAttributes,
        env_ctx: EnvironmentalContext
    ) -> bool:
        """
        Evaluate policy against attributes

        Args:
            user_attrs: User attributes
            resource_attrs: Resource attributes
            env_ctx: Environmental context

        Returns:
            True if access is allowed
        """
        try:
            return self.condition(user_attrs, resource_attrs, env_ctx)
        except Exception as e:
            logger.error(f"Policy evaluation error ({self.name}): {str(e)}")
            return False  # Fail secure


class ABACService:
    """
    Attribute-Based Access Control Service

    Evaluates dynamic access policies based on attributes
    """

    def __init__(self):
        """Initialize ABAC service with default policies"""
        self.policies: List[AccessPolicy] = []
        self._init_default_policies()

    def _init_default_policies(self):
        """Initialize default access policies"""

        # Policy 1: Clearance level requirement
        self.policies.append(AccessPolicy(
            name="clearance_check",
            description="User must have required clearance level",
            condition=lambda u, r, e: (
                r.requires_clearance is None or
                u.clearance_level is not None and
                self._compare_clearance(u.clearance_level, r.requires_clearance)
            ),
            denial_reason="Insufficient clearance level"
        ))

        # Policy 2: Data classification check
        self.policies.append(AccessPolicy(
            name="classification_check",
            description="User can access data based on classification",
            condition=lambda u, r, e: self._check_classification(
                u.clearance_level, r.classification
            ),
            denial_reason="Data classification exceeds clearance level"
        ))

        # Policy 3: Resource ownership
        self.policies.append(AccessPolicy(
            name="ownership_check",
            description="Users can access their own resources",
            condition=lambda u, r, e: (
                u.user_id == r.owner_id or
                u.is_superuser
            ),
            denial_reason="Not authorized to access this resource"
        ))

        # Policy 4: Team membership
        self.policies.append(AccessPolicy(
            name="team_membership_check",
            description="Team members can access team resources",
            condition=lambda u, r, e: (
                r.team_id is None or
                r.team_id in u.team_ids or
                u.is_superuser
            ),
            denial_reason="Not a member of this team"
        ))

        # Policy 5: Organization membership
        self.policies.append(AccessPolicy(
            name="organization_check",
            description="Organization members can access org resources",
            condition=lambda u, r, e: (
                r.organization_id is None or
                u.organization_id == r.organization_id or
                u.is_superuser
            ),
            denial_reason="Not authorized for this organization"
        ))

        # Policy 6: Time-based access
        self.policies.append(AccessPolicy(
            name="business_hours_check",
            description="Restrict sensitive operations to business hours",
            condition=lambda u, r, e: (
                r.classification in [DataClassification.PUBLIC, DataClassification.INTERNAL] or
                not env_ctx.is_business_hours or
                u.is_superuser
            ),
            denial_reason="Access restricted to business hours for this data"
        ))

        # Policy 7: Device trust
        self.policies.append(AccessPolicy(
            name="device_trust_check",
            description="Require trusted device for sensitive data",
            condition=lambda u, r, e: (
                r.classification in [DataClassification.PUBLIC, DataClassification.INTERNAL] or
                env_ctx.device_trust == DeviceTrust.TRUSTED or
                u.is_superuser
            ),
            denial_reason="Untrusted device cannot access this data"
        ))

        # Policy 8: Manager override
        self.policies.append(AccessPolicy(
            name="manager_check",
            description="Managers can access team member resources",
            condition=lambda u, r, e: (
                u.is_superuser or
                u.manager_id == r.owner_id or
                r.owner_id not in u.team_ids
            ),
            denial_reason="Manager access required"
        ))

    def _compare_clearance(
        self,
        user_clearance: ClearanceLevel,
        required_clearance: ClearanceLevel
    ) -> bool:
        """
        Compare user clearance with required level

        Clearance levels (highest to lowest):
        TOP_SECRET > SECRET > CONFIDENTIAL > INTERNAL > PUBLIC
        """
        clearance_hierarchy = {
            ClearanceLevel.TOP_SECRET: 4,
            ClearanceLevel.SECRET: 3,
            ClearanceLevel.CONFIDENTIAL: 2,
            ClearanceLevel.INTERNAL: 1,
            ClearanceLevel.PUBLIC: 0,
        }

        return clearance_hierarchy.get(user_clearance, 0) >= clearance_hierarchy.get(
            required_clearance, 0
        )

    def _check_classification(
        self,
        user_clearance: Optional[ClearanceLevel],
        data_classification: DataClassification
    ) -> bool:
        """
        Check if user can access data by classification

        Mapping:
        - PUBLIC: All users
        - INTERNAL: All authenticated users
        - CONFIDENTIAL: INTERNAL clearance or higher
        - RESTRICTED: CONFIDENTIAL clearance or higher
        """
        if data_classification == DataClassification.PUBLIC:
            return True

        if data_classification == DataClassification.INTERNAL:
            return user_clearance is not None

        if data_classification == DataClassification.CONFIDENTIAL:
            return user_clearance in [
                ClearanceLevel.CONFIDENTIAL,
                ClearanceLevel.SECRET,
                ClearanceLevel.TOP_SECRET
            ]

        if data_classification == DataClassification.RESTRICTED:
            return user_clearance in [
                ClearanceLevel.SECRET,
                ClearanceLevel.TOP_SECRET
            ]

        return False

    def extract_user_attributes(self, user: User) -> UserAttributes:
        """
        Extract ABAC attributes from User object

        Args:
            user: User object

        Returns:
            UserAttributes
        """
        # Get team IDs from relationships
        team_ids = set()
        if hasattr(user, 'team_memberships'):
            team_ids = {str(tm.team_id) for tm in user.team_memberships}

        # Map role to clearance level
        clearance_map = {
            "ADMIN": ClearanceLevel.TOP_SECRET,
            "USER": ClearanceLevel.INTERNAL,
            "TEAM_LEAD": ClearanceLevel.CONFIDENTIAL
        }
        clearance = clearance_map.get(
            user.role.value if hasattr(user.role, 'value') else user.role,
            ClearanceLevel.INTERNAL
        )

        return UserAttributes(
            user_id=str(user.id),
            role=user.role.value if hasattr(user.role, 'value') else user.role,
            clearance_level=clearance,
            department=user.preferences.get('department') if user.preferences else None,
            location=user.preferences.get('location') if user.preferences else None,
            manager_id=user.preferences.get('manager_id') if user.preferences else None,
            team_ids=team_ids,
            organization_id=str(user.organization_id) if user.organization_id else None,
            is_superuser=user.is_superuser
        )

    def extract_environmental_context(
        self,
        request: Request
    ) -> EnvironmentalContext:
        """
        Extract environmental context from request

        Args:
            request: FastAPI Request object

        Returns:
            EnvironmentalContext
        """
        # Get current time
        now = datetime.now()

        # Determine if business hours (9 AM - 5 PM, Mon-Fri)
        is_business_hours = (
            now.weekday() < 5 and  # Mon-Fri
            time(9, 0) <= now.time() <= time(17, 0)
        )

        # Get IP address
        ip_address = request.client.host if request.client else "unknown"

        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")

        # Determine device trust (simplified)
        # In production, would use device fingerprinting
        device_trust = DeviceTrust.TRUSTED  # Default to trusted
        if "unknown" in user_agent.lower() or "bot" in user_agent.lower():
            device_trust = DeviceTrust.UNTRUSTED

        # Determine location (from IP, simplified)
        location = None  # Would use geo-IP lookup in production

        return EnvironmentalContext(
            current_time=now,
            ip_address=ip_address,
            user_agent=user_agent,
            device_trust=device_trust,
            location=location,
            is_business_hours=is_business_hours,
            is_on_premise=False  # Would check IP ranges
        )

    def evaluate_access(
        self,
        user: User,
        resource_attrs: ResourceAttributes,
        request: Request
    ) -> tuple[bool, List[str]]:
        """
        Evaluate all access policies

        Args:
            user: User object
            resource_attrs: Resource attributes
            request: HTTP request

        Returns:
            Tuple of (access_granted, denial_reasons)
        """
        # Extract attributes
        user_attrs = self.extract_user_attributes(user)
        env_ctx = self.extract_environmental_context(request)

        # Evaluate all policies
        denial_reasons = []
        for policy in self.policies:
            try:
                if not policy.condition(user_attrs, resource_attrs, env_ctx):
                    denial_reasons.append(f"{policy.name}: {policy.denial_reason}")
            except Exception as e:
                logger.error(f"Policy evaluation error: {str(e)}")
                denial_reasons.append(f"{policy.name}: Policy evaluation failed")

        # Access granted if no denials
        access_granted = len(denial_reasons) == 0

        # Log decision
        logger.info(
            f"ABAC decision: user={user_attrs.user_id}, "
            f"resource={resource_attrs.resource_id}, "
            f"granted={access_granted}",
            extra={
                "user_id": user_attrs.user_id,
                "resource_id": resource_attrs.resource_id,
                "access_granted": access_granted,
                "denial_reasons": denial_reasons
            }
        )

        return access_granted, denial_reasons

    def check_access(
        self,
        user: User,
        resource_attrs: ResourceAttributes,
        request: Request
    ) -> bool:
        """
        Check if access is allowed (raises exception if not)

        Args:
            user: User object
            resource_attrs: Resource attributes
            request: HTTP request

        Returns:
            True if access allowed

        Raises:
            HTTPException: If access denied
        """
        access_granted, denial_reasons = self.evaluate_access(
            user, resource_attrs, request
        )

        if not access_granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "Access denied by ABAC policies",
                    "reasons": denial_reasons
                }
            )

        return True


# Singleton instance
abac_service = ABACService()


# Decorator for ABAC
def require_abac(resource_type: str, classification: DataClassification = DataClassification.INTERNAL):
    """
    Decorator for ABAC-protected endpoints

    Usage:
        @require_abac(resource_type="assessment", classification=DataClassification.CONFIDENTIAL)
        async def get_assessment(...):
            ...

    The endpoint must extract the resource and pass to the ABAC check
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract required parameters
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            resource_id = kwargs.get('id')  # Common resource ID parameter

            if not current_user or not request:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # In a real implementation, you would fetch the resource
            # and determine its attributes (owner, team, org, etc.)
            # For now, we'll create a simple resource attributes object
            resource_attrs = ResourceAttributes(
                resource_id=str(resource_id) if resource_id else "unknown",
                resource_type=resource_type,
                classification=classification,
                owner_id=str(current_user.id),  # Default to self-owned
                team_id=None,  # Would fetch from resource
                organization_id=current_user.organization_id,
                created_at=datetime.now()
            )

            # Check ABAC
            abac_service.check_access(current_user, resource_attrs, request)

            # Continue to endpoint
            return await func(*args, **kwargs)

        return wrapper
    return decorator
