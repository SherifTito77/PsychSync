from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_superuser
from app.schemas.user import UserOut as UserSchema
from app.db.models.user import User as UserModel
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
@router.get("/users", response_model=List[UserSchema])
def list_all_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    is_active: Optional[bool] = None,
    current_user: UserModel = Depends(get_current_active_superuser)
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
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Soft-delete a user by deactivating them. Requires superuser privileges.
    """
    success = delete_user(db, user_id=user_id, hard_delete=False)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/restore", status_code=status.HTTP_200_OK)
def restore_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser)
):
    """
    Restore a soft-deleted user. Requires superuser privileges.
    """
    success = restore_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User restored successfully"}

# You would also add endpoints for managing organizations, teams, assessments, etc. here.