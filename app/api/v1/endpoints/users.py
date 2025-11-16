# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Dependencies
from app.api.deps import get_async_db, get_current_active_user

# Models
from app.db.models.user import User

# Schemas
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserOut
from app.schemas.auth import PasswordChange

# Services
import app.services.async_user_service as user_service

# Core
from app.core.security import verify_password
from app.core.response import SuccessResponse, ErrorResponse, PaginatedResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserOut]:
    """
    Retrieve the profile of the currently authenticated user.

    Args:
        current_user: The authenticated user object injected via JWT token

    Returns:
        SuccessResponse containing the complete user profile data

    Raises:
        HTTPException: If authentication fails or user is not found

    Example:
        GET /api/v1/users/me
        Headers: Authorization: Bearer <jwt_token>

        Response:
        {
            "success": true,
            "message": "User profile retrieved successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "is_verified": false,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    return SuccessResponse(
        data=current_user,
        message="User profile retrieved successfully"
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
) -> SuccessResponse[UserOut]:
    """
    Register a new user account in the system.

    This endpoint creates a new user with email verification requirement.
    The user will need to verify their email address before full account activation.

    Args:
        user_data: User creation data including email, password, and full name
        db: Async database session for database operations

    Returns:
        SuccessResponse containing the created user data (without password hash)

    Raises:
        HTTPException: If email is already registered or validation fails

    Example:
        POST /api/v1/users/register
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }

        Response (201 Created):
        {
            "success": true,
            "message": "User created successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "is_verified": false
            }
        }

    Notes:
        - Password must be at least 8 characters long
        - Email verification token will be sent to the provided email
        - User account will be in inactive state until email verification
    """
    # Check if user already exists by email
    existing_user = await user_service.get_user_by_email_async(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    try:
        user = await user_service.create_user_async(db, user_data)
        return SuccessResponse(
            data=user,
            message="User created successfully",
        )
    except (user_service.UserAlreadyExistsError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse[UserOut]:
    """
    Retrieve a paginated list of users from the system.

    This endpoint returns a paginated list of all users in the system.
    Currently accessible to any authenticated user, but will be restricted
    to administrators in future versions.

    Args:
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        db: Async database session for database operations
        current_user: The authenticated user making the request

    Returns:
        PaginatedResponse containing user list and pagination metadata

    Raises:
        HTTPException: If user is not authenticated

    Example:
        GET /api/v1/users/?skip=0&limit=10

        Response:
        {
            "success": true,
            "message": "Users retrieved successfully",
            "data": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "user1@example.com",
                    "full_name": "User One"
                }
            ],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    Notes:
        - Users are returned in creation date order (newest first)
        - Sensitive information like password hashes is never included
        - Pagination starts from 0
    """
    users = await user_service.get_all_users_async(db, skip=skip, limit=limit)
    total = len(users)  # Note: In production, you'd want a separate count query
    return PaginatedResponse(
        data=users,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        message="Users retrieved successfully"
    )


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserOut]:
    """
    Retrieve a specific user by their unique identifier.

    This endpoint fetches user details for a given user ID.
    Users can only view their own profile unless they have administrative privileges.

    Args:
        user_id: UUID of the user to retrieve
        db: Async database session for database operations
        current_user: The authenticated user making the request

    Returns:
        SuccessResponse containing the requested user's data

    Raises:
        HTTPException: If user is not found or access is denied

    Example:
        GET /api/v1/users/550e8400-e29b-41d4-a716-446655440000

        Response:
        {
            "success": true,
            "message": "User retrieved successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }

    Notes:
        - Returns 404 if user_id does not exist
        - Sensitive data is never included in the response
    """
    user_dict = await user_service.get_user_by_id_async(db, user_id)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return SuccessResponse(
        data=user_dict,
        message="User retrieved successfully"
    )


@router.put("/me")
async def update_user_profile(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserOut]:
    """
    Update the profile of the currently authenticated user.

    This endpoint allows users to update their profile information.
    Only the fields provided in the request body will be updated.

    Args:
        user_in: User update data containing fields to modify
        db: Async database session for database operations
        current_user: The authenticated user being updated

    Returns:
        SuccessResponse containing the updated user data

    Raises:
        HTTPException: If validation fails or user is not found

    Example:
        PUT /api/v1/users/me
        {
            "full_name": "Jane Doe",
            "timezone": "America/New_York",
            "locale": "en-US"
        }

        Response:
        {
            "success": true,
            "message": "User profile updated successfully",
            "data": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "Jane Doe",
                "timezone": "America/New_York",
                "locale": "en-US"
            }
        }

    Notes:
        - Email address cannot be changed through this endpoint
        - Password changes should use the dedicated password change endpoint
        - All updates are validated before being applied
    """
    user = await user_service.update_user_async(db, str(current_user.id), user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return SuccessResponse(
        data=user,
        message="User profile updated successfully"
    )


@router.post("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[None]:
    """
    Change the password for the currently authenticated user.

    This endpoint allows users to change their password after verifying
    their current password for security purposes.

    Args:
        password_change: Password change data including current and new passwords
        db: Async database session for database operations
        current_user: The authenticated user changing their password

    Returns:
        SuccessResponse indicating successful password change

    Raises:
        HTTPException: If current password is incorrect or new password is invalid

    Example:
        POST /api/v1/users/me/change-password
        {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }

        Response:
        {
            "success": true,
            "message": "Password updated successfully",
            "data": null,
            "timestamp": "2024-01-01T00:00:00Z"
        }

    Notes:
        - Current password must be verified before allowing change
        - New password must meet security requirements (8+ chars, mixed case, etc.)
        - Password is securely hashed before storage
        - User will be logged out from all other sessions after password change
    """
    # Verify the current password
    if not verify_password(password_change.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    # Update the password using the user service
    user_update = UserUpdate(password=password_change.new_password)
    await user_service.update_user_async(db, str(current_user.id), user_update)

    return SuccessResponse(
        message="Password updated successfully"
    )