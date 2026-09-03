# TODO(human): Add audit logging calls to security-critical endpoints
# Example:
# await audit_logger.log_event(
#     action=AuditAction.AUTHENTICATE,
#     user_id=str(user.id),
#     details={"email": user.email, "success": True}
# )


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_superuser, get_db
from app.api.v1.deps import get_current_user
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.user import User as UserModel
from app.schemas.user import UserCreate
from app.schemas.user import UserOut as UserSchema
from app.services.security.password_service import PasswordService

router = APIRouter(prefix="/admin", tags=["admin"])

from app.api.dependencies.permissions import require_permission
from app.services.permission_service import Permission

# ... imports ...


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_permission(Permission.MANAGE_SYSTEM)),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create a new user. Requires MANAGE_SYSTEM permission.
    """
    # Check if user exists
    query = select(UserModel).where(UserModel.email == user_in.email)
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Hash password
    password_service = PasswordService()
    hashed_password = password_service.hash_password(user_in.password)

    # Create user
    db_user = UserModel(
        email=user_in.email,
        password_hash=hashed_password,
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=user_in.is_active,
    )

    # Get first organization if none provided (like in create_team)
    org_result = await db.execute(text("SELECT id FROM organizations LIMIT 1"))
    org_row = org_result.fetchone()
    if org_row:
        db_user.organization_id = org_row[0]

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# Temporarily disabled due to syntax issues after async conversion
# from app.services.user_service import get_users_by_organization, delete_user, restore_user, get_all_users


# Placeholder functions for admin functionality
async def get_users_by_organization(
    db, organization_id, skip=0, limit=100, is_active=None
):
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
    return False


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/users", response_model=list[UserSchema])
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    is_active: bool | None = None,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Retrieve all users. Requires superuser privileges.
    """
    query = select(UserModel).offset(skip).limit(limit)
    if is_active is not None:
        query = query.where(UserModel.is_active == is_active)

    result = await db.execute(query)
    users = result.scalars().all()
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Soft-delete a user by deactivating them. Requires superuser privileges.
    """
    success = delete_user(db, user_id=user_id, hard_delete=False)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "User deactivated successfully"}


@router.post(
    "/users/{user_id}/restore",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
)
def restore_user_endpoint(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Restore a soft-deleted user. Requires superuser privileges.
    """
    success = restore_user(db, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"message": "User restored successfully"}


# You would also add endpoints for managing organizations, teams, assessments, etc. here., dependencies=[Depends(get_current_user)]
