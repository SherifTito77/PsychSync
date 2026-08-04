# Backend API Updates for Role-Based Access Control
# Add these schemas and updates to your FastAPI backend

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

# =============================================================================
# 1. UPDATE USER SCHEMAS (app/schemas/user.py)
# =============================================================================


class UserRole(str, Enum):
    """User role enumeration"""

    EMPLOYEE = "employee"
    USER = "user"  # Alias for employee
    HR = "hr"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: str
    role: Optional[UserRole] = UserRole.EMPLOYEE
    department: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user"""

    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    """Schema for user response (includes role field)"""

    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    department: Optional[str] = None
    is_hr: bool = False
    is_active: bool
    created_at: str
    updated_at: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2


# =============================================================================
# 2. UPDATE DATABASE MODEL (app/db/models/user.py)
# =============================================================================

import enum
import uuid

from sqlalchemy import Boolean, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID


class UserRole(str, enum.Enum):
    """User roles for database model"""

    EMPLOYEE = "employee"
    USER = "user"
    HR = "hr"
    MANAGER = "manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):  # Assuming you have a Base model
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Role-based access control fields
    role = Column(
        SQLEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE, index=True
    )
    department = Column(String(100), nullable=True, index=True)
    is_hr = Column(Boolean, default=False, nullable=False)

    # Existing fields
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    # Relationships
    # ... existing relationships

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


# =============================================================================
# 3. UPDATE AUTH ENDPOINT (app/api/v1/endpoints/auth.py)
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.role_middleware import UserRole, require_role_dependency
from app.db.models.user import User
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with role assignment.

    Default role is 'employee' unless specified by an admin.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),  # Your hash function
        role=user_data.role or UserRole.EMPLOYEE,
        department=user_data.department,
        is_hr=user_data.role in [UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN],
        is_active=True,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/me", response_model=UserOut)
async def get_current_user(
    current_user: User = Depends(get_current_user),  # Your existing auth dependency
):
    """
    Get current user with role information.
    This endpoint is called by the frontend to load user data.
    """
    return current_user


# =============================================================================
# 4. UPDATE USER MANAGEMENT ENDPOINT (app/api/v1/endpoints/users.py)
# =============================================================================


@router.get("/users", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role_dependency(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    """
    List all users (Admin/HR only).
    Can filter by role.
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    users = query.offset(skip).limit(limit).all()
    return users


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_role_dependency(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Update a user's role (Admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update role
    user.role = role
    user.is_hr = role in [UserRole.HR, UserRole.ADMIN, UserRole.SUPER_ADMIN]
    user.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(user)

    return user


# =============================================================================
# 5. EXAMPLE: PROTECT ENDPOINTS BY ROLE
# =============================================================================

from app.core.role_middleware import require_admin, require_hr, require_manager_or_hr


@router.get("/analytics/hris")
async def get_hris_analytics(
    db: Session = Depends(get_db),
    _: None = Depends(require_hr()),  # HR, Manager, Admin, Super Admin only
):
    """
    HRIS Analytics endpoint - HR and above only
    """
    # Your analytics logic here
    return {"analytics": "..."}


@router.get("/admin/system")
async def get_system_stats(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin()),  # Admin and Super Admin only
):
    """
    System statistics - Admin only
    """
    # Your admin logic here
    return {"stats": "..."}


@router.post("/teams/optimize")
async def optimize_team(
    team_data: TeamOptimizeRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_manager_or_hr()),  # Manager or HR only
):
    """
    Team optimization - Manager or HR only
    """
    # Your optimization logic here
    return {"optimized_team": "..."}


# =============================================================================
# 6. TESTING ROLES
# =============================================================================

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_hr_endpoint_with_employee_role(async_client: AsyncClient):
    """Test that employee cannot access HR endpoint"""
    # Login as employee
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "employee@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]

    # Try to access HR endpoint
    response = await async_client.get(
        "/api/v1/analytics/hris", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_hr_endpoint_with_hr_role(async_client: AsyncClient):
    """Test that HR user can access HR endpoint"""
    # Login as HR user
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "hr@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]

    # Access HR endpoint
    response = await async_client.get(
        "/api/v1/analytics/hris", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
