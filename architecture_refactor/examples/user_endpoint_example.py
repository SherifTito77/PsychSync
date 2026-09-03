# Example: Thin API Layer Endpoint
# This shows how endpoints should look after refactoring

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domain.entities.user_entity import User
from app.domain.services.user_service import UserService
from app.infrastructure.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get user repository instance"""
    return UserRepository(db)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Get user service instance"""
    return UserService(repo)


# ============================================================================
# ENDPOINTS (Thin - Only HTTP concerns)
# ============================================================================


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.

    **Thin endpoint responsibilities:**
    - Validate HTTP request (Pydantic does this)
    - Call domain service
    - Return HTTP response with appropriate status code

    **Business logic lives in UserService** - see:
    - app/domain/services/user_service.py
    """
    try:
        # Delegate to domain service
        user = await user_service.create_user(user_data)

        # Convert to response model
        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except ValueError as e:
        # Validation error from domain
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    """
    Get user by ID.

    **Endpoint responsibility:**
    - Parse UUID from path
    - Call service
    - Return 404 if not found (service raises NotFoundError)
    """
    try:
        user = await user_service.get_user_by_id(user_id)

        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user.

    **Notice:**
    - No business logic here
    - Just HTTP validation and status codes
    - All logic in UserService
    """
    try:
        user = await user_service.update_user(user_id, user_data)

        return UserRead(
            id=user.id,
            email=str(user.email),
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
):
    """
    Delete user.

    **Authorization:**
    - Only admins can delete users
    - Check is done in domain service
    """
    try:
        await user_service.delete_user(user_id, current_user)

    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ============================================================================
# COMPARISON: OLD vs NEW
# ============================================================================

"""
OLD APPROACH (Vibe Coding - ❌):
--------------------------------
@router.post("/users")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Mixed concerns!
    # 1. HTTP handling
    # 2. Database queries
    # 3. Business logic
    # 4. Validation
    # 5. Error handling

    # Database query mixed in
    existing_user = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(400, "Email already exists")

    # Business logic mixed in
    hashed_password = hash_password(user_data.password)

    # Database creation mixed in
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        ...
    )
    db.add(new_user)
    await db.commit()

    return new_user


NEW APPROACH (Clean Architecture - ✅):
---------------------------------------
@router.post("/users")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    # Only HTTP concerns!
    try:
        # Delegate to domain service
        user = await user_service.create_user(user_data)
        return user.to_dict()

    except ValidationError as e:
        raise HTTPException(400, str(e))

Benefits:
---------
✅ Single Responsibility: Endpoint only handles HTTP
✅ Testable: Can mock user_service
✅ Reusable: Service can be called from CLI, tests, etc.
✅ Clear separation: Easy to find where logic lives
✅ Type-safe: Domain entities enforce business rules
"""
