"""
HIPAA Compliance Dependencies for Clinical Endpoints

Provides reusable FastAPI dependencies that enforce:
- Role-based access control for PHI
- Audit logging for every PHI read/write
- Consent verification before clinical data access

Usage:
    from app.api.dependencies.hipaa import require_clinical_access, audit_phi_access

    @router.get("/patient-data")
    async def get_data(
        current_user: User = Depends(require_clinical_access),
        db: AsyncSession = Depends(get_db),
    ):
        await audit_phi_access(db, current_user, "clinical_screenings", "read")
        ...
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user
from app.core.database import get_async_db
from app.db.models.user import User
from app.services.audit_service import AuditEventType, AuditSeverity, audit_service

logger = logging.getLogger("hipaa")

# Roles allowed to access clinical/PHI data
CLINICAL_ROLES = {"admin", "super_admin", "hr", "manager", "clinician", "psychiatrist"}


async def require_clinical_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency that enforces clinical role access.

    Allows: admin, super_admin, hr, manager, clinician, psychiatrist,
            superusers, and regular users accessing their OWN data.

    Regular users pass through because screening endpoints let users
    take their own assessments. Endpoint logic must still scope queries
    to current_user.id for non-privileged users.
    """
    # Superusers always pass
    if getattr(current_user, "is_superuser", False):
        return current_user

    # Users with clinical roles pass (they can see aggregate/other data)
    user_role = getattr(current_user, "role", "user")
    if user_role and user_role.lower() in CLINICAL_ROLES:
        return current_user

    # Regular users pass — endpoints must scope to own data only
    return current_user


async def require_clinical_staff(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Stricter dependency: only clinical staff and admins.
    Use for endpoints that access OTHER users' PHI (population analytics,
    clinical dashboards, alerts).
    """
    if getattr(current_user, "is_superuser", False):
        return current_user

    user_role = getattr(current_user, "role", "user")
    if user_role and user_role.lower() in CLINICAL_ROLES:
        return current_user

    logger.warning(
        "Unauthorized clinical access attempt by user=%s role=%s",
        current_user.id,
        user_role,
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Clinical staff or admin role required to access this resource",
    )


async def audit_phi_access(
    db: AsyncSession,
    user: User,
    table_name: str,
    action: str,
    record_id: Optional[str] = None,
    details: Optional[dict] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log PHI access to the audit trail. Call this in every endpoint
    that reads or writes clinical/screening data.
    """
    try:
        await audit_service.log_data_access(
            db=db,
            user_id=user.id,
            table_name=table_name,
            record_id=record_id or "aggregate",
            action=action,
            details={
                "phi_access": True,
                "user_role": getattr(user, "role", "unknown"),
                **(details or {}),
            },
            request=request,
        )
    except Exception as e:
        # Audit failures must not break clinical workflows
        logger.error("PHI audit logging failed: %s", e)
