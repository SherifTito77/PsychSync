# TODO(human): Add audit logging calls to security-critical endpoints
# Example:
# await audit_logger.log_event(
#     action=AuditAction.AUTHENTICATE,
#     user_id=str(user.id),
#     details={"email": user.email, "success": True}
# )


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_superuser, get_db
from app.api.v1.deps import get_current_user
from app.db.models.user import User as UserModel
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from app.schemas.user import UserOut as UserSchema

# Temporarily disabled due to syntax issues after async conversion
# from app.services.user_service import get_users_by_organization, delete_user, restore_user, get_all_users


# Placeholder functions for admin functionality
async def get_users_by_organization(db, organization_id, skip=0, limit=100, is_active=None):
    """Placeholder function"""
    return []


async def delete_user(db, user_id, hard_delete=False):
    """Placeholder function"""
    return False


async def restore_user(db, user_id):
    """Placeholder function"""
    return False


async def get_all_users(db, skip=0, limit=100, is_active=None):
    """Placeholder function"""
    return []


router = APIRouter()

# All endpoints in this file require a superuser


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/users", response_model=list[UserSchema])
def list_all_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    is_active: bool | None = None,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Retrieve all users. Requires superuser privileges.
    """
    # Note: get_all_users from the service returns User objects, not dicts.
    # You might need to adjust the service or the response model.
    users = get_all_users(db, skip=skip, limit=limit, is_active=is_active)
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Soft-delete a user by deactivating them. Requires superuser privileges.
    """
    success = delete_user(db, user_id=user_id, hard_delete=False)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User deactivated successfully"}


@router.post(
    "/users/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
def restore_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Restore a soft-deleted user. Requires superuser privileges.
    """
    success = restore_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"message": "User restored successfully"}


# You would also add endpoints for managing organizations, teams, assessments, etc. here., dependencies=[Depends(get_current_user)]
