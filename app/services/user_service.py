

"""
File Path: app/services/user_service.py
User service with Redis caching implementation
Handles all user-related business logic with performance optimization
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from app.db.models.user import User as UserModel
from app.db.models.user import User 
from app.db.models.organization import Organization
from app.schemas.user import UserCreate, UserUpdate
from app.core.cache import cached, cache_delete_pattern, cache_get, cache_set
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.db.models.organization import Organization






logger = logging.getLogger(__name__)


# =============================================================================
# USER RETRIEVAL (WITH CACHING)
# =============================================================================

@cached(expire=settings.CACHE_USER_EXPIRE, key_prefix="user")
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user by ID with caching

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User dictionary or None if not found

    Cache: 30 minutes (configurable via CACHE_USER_EXPIRE)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
if user:
        return user_to_dict(user)
return None


@cached(expire=settings.CACHE_USER_EXPIRE, key_prefix="user")
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email with caching
    
    Args:
        db: Database session
        email: User email address
    
    Returns:
        User dictionary or None if not found
    
    Cache: 30 minutes
    """
    user = result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()
if user:
        return user_to_dict(user)
return None


@cached(expire=settings.CACHE_USER_EXPIRE, key_prefix="user")
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[Dict[str, Any]]:
    """
    Get user by username with caching
    
    Args:
        db: Database session
        username: Username
    
    Returns:
        User dictionary or None if not found
    
    Cache: 30 minutes
    """
    user = result = await db.execute(query)
    return result.scalars().all()
if user:
        return user_to_dict(user)
return None


@cached(expire=600, key_prefix="user")
async def get_users_by_organization(
    db: Session, 
    organization_id: int, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get users by organization with caching
    
    Args:
        db: Database session
        organization_id: Organization ID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        is_active: Filter by active status (optional)
    
    Returns:
        List of user dictionaries
    
    Cache: 10 minutes (shorter cache for lists)
    """
    query = db.query(User).filter(User.organization_id == organization_id)
    
if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
return [user_to_dict(user) for user in users]


async def get_all_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[User]:
    """
    Get all users (no caching - admin only)
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status (optional)
    
    Returns:
        List of User objects
    
    Note: Not cached due to potentially large result set
    """
    query = db.query(User)
    
if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
return query.offset(skip).limit(limit).all()


async def get_user_count(db: AsyncSession, organization_id: Optional[int] = None) -> int:
    """
    Get total user count
    
    Args:
        db: Database session
        organization_id: Organization ID (optional, for org-specific count)
    
    Returns:
        Total number of users
    """
    query = db.query(User)
    
if organization_id:
        query = query.filter(User.organization_id == organization_id)
    
return query.count()


# =============================================================================
# USER CREATION AND UPDATE (WITH CACHE INVALIDATION)
# =============================================================================

def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create new user and invalidate related caches
    
    Args:
        db: Database session
        user_data: User creation data (Pydantic schema)
    
    Returns:
        Created User object
    
    Raises:
        ValueError: If email or username already exists
    """
    # Check if email already exists
    existing_email = result = await db.execute(select(User).where(User.email == user_data.email.lower()))
    return result.scalar_one_or_none()
if existing_email:
        raise ValueError(f"Email {user_data.email} is already registered")
    
    # Check if username already exists
if user_data.username:
        existing_username = result = await db.execute(query)
    return result.scalars().all()
    if existing_username:
            raise ValueError(f"Username {user_data.username} is already taken")
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user object
    db_user = User(
        email=user_data.email.lower(),
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization_id=user_data.organization_id if hasattr(user_data, 'organization_id') else None,
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow()
    )
    
    org = Organization(name=f"{db_user.full_name or db_user.email.split('@')[0]}'s Org")
    db.add(org)
    db.flush()  # get org.id
    db_user.organization_id = org.id 
    
    db.add(db_user)
        await db.commit()
    await db.refresh(db_user)
    
    # Invalidate organization users cache
if db_user.organization_id:
        cache_delete_pattern(f"user:get_users_by_organization:*{db_user.organization_id}*")
    
    logger.info(f"Created user: {db_user.email} (ID: {db_user.id} with organization {org.name})")
    cache_delete_pattern(f"user:get_users_by_organization:*{db_user.organization_id}*")
   
return db_user


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> Optional[User]:
    """
    Update user and invalidate caches
    
    Args:
        db: Database session
        user_id: User ID
        user_data: User update data (Pydantic schema)
    
    Returns:
        Updated User object or None if not found
    
    Raises:
        ValueError: If email/username conflict with existing users
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        logger.warning(f"User not found: ID {user_id}")
    return None
    
    # Get update data, excluding unset fields
    update_data = user_data.dict(exclude_unset=True)
    
    # Check email uniqueness if email is being updated
if "email" in update_data and update_data["email"] != user.email:
        existing = db.query(User).filter(
            User.email == update_data["email"].lower(),
            User.id != user_id
        ).first()
    if existing:
            raise ValueError(f"Email {update_data['email']} is already in use")
        update_data["email"] = update_data["email"].lower()
    
    # Check username uniqueness if username is being updated
if "username" in update_data and update_data["username"] != user.username:
        existing = result = await db.execute(query)
    return result.scalars().all()
    if existing:
            raise ValueError(f"Username {update_data['username']} is already taken")
    
    # Hash password if provided
if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Update timestamp
    update_data["updated_at"] = datetime.utcnow()
    
    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    # Invalidate all user-related caches
    cache_delete_pattern(f"user:get_user_by_id:*{user_id}*")
    cache_delete_pattern(f"user:get_user_by_email:*{user.email}*")
if user.username:
        cache_delete_pattern(f"user:get_user_by_username:*{user.username}*")
    
if user.organization_id:
        cache_delete_pattern(f"user:get_users_by_organization:*{user.organization_id}*")
    
    logger.info(f"Updated user: {user.email} (ID: {user.id})")
    
return user


def delete_user(db: Session, user_id: int, hard_delete: bool = False) -> bool:
    """
    Delete user (soft or hard delete) and invalidate caches
    
    Args:
        db: Database session
        user_id: User ID
        hard_delete: If True, permanently delete; if False, soft delete (deactivate)
    
    Returns:
        True if successful, False if user not found
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        logger.warning(f"User not found for deletion: ID {user_id}")
    return False
    
    organization_id = user.organization_id
    email = user.email
    username = user.username
    
if hard_delete:
        # Permanent deletion
        db.delete(user)
        await db.commit()
        logger.info(f"Hard deleted user: {email} (ID: {user_id})")
    else:
        # Soft delete (deactivate)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"Soft deleted user: {email} (ID: {user_id})")
    
    # Invalidate all user-related caches
    cache_delete_pattern(f"user:get_user_by_id:*{user_id}*")
    cache_delete_pattern(f"user:get_user_by_email:*{email}*")
if username:
        cache_delete_pattern(f"user:get_user_by_username:*{username}*")
    
if organization_id:
        cache_delete_pattern(f"user:get_users_by_organization:*{organization_id}*")
    
return True


def restore_user(db: Session, user_id: int) -> bool:
    """
    Restore soft-deleted user and invalidate caches
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if successful, False if user not found
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        return False
    
    user.is_active = True
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    # Invalidate caches
    cache_delete_pattern(f"user:get_user_by_id:*{user_id}*")
    cache_delete_pattern(f"user:get_user_by_email:*{user.email}*")
    
if user.organization_id:
        cache_delete_pattern(f"user:get_users_by_organization:*{user.organization_id}*")
    
    logger.info(f"Restored user: {user.email} (ID: {user_id})")
    
return True


# =============================================================================
# AUTHENTICATION
# =============================================================================

# def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
#     """
#     Authenticate user by email and password
    
#     Args:
#         db: Database session
#         email: User email
#         password: Plain text password
    
#     Returns:
#         User object if authenticated, None otherwise
    
#     Note: Does not use cache for security reasons
#     """
#     user = result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()
    
#     if not user:
#         logger.warning(f"Authentication failed: User not found - {email}")
#         return None
    
#     if not verify_password(password, user.password):
#         logger.warning(f"Authentication failed: Invalid password - {email}")
#         return None
    
#     if not user.is_active:
#         logger.warning(f"Authentication failed: User inactive - {email}")
#         return None
    
#     logger.info(f"User authenticated successfully: {email}")
#     return user
def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]:
    """
    Authenticate a user by email and password.
    """
    user = result = await db.execute(query)
    return result.scalars().all()
if not user:
        return None
if not user.is_active:
        return None
    
    # FIX: Use the 'hashed_password' property which points to the 'password_hash' column
if not verify_password(password, user.password_hash):
        return None
    
return user

def verify_user_email(db: Session, user_id: int) -> bool:
    """
    Verify user email and invalidate caches
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if successful, False if user not found
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        return False
    
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    # Invalidate caches
    cache_delete_pattern(f"user:get_user_by_id:*{user_id}*")
    cache_delete_pattern(f"user:get_user_by_email:*{user.email}*")
    
    logger.info(f"Verified user email: {user.email} (ID: {user_id})")
    
return True


def update_password(db: Session, user_id: int, new_password: str) -> bool:
    """
    Update user password
    
    Args:
        db: Database session
        user_id: User ID
        new_password: New plain text password
    
    Returns:
        True if successful, False if user not found
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        return False
    
    user.password_hash = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    # Invalidate caches
    cache_delete_pattern(f"user:get_user_by_id:*{user_id}*")
    
    logger.info(f"Password updated for user: {user.email} (ID: {user_id})")
    
return True


def update_last_login(db: Session, user_id: int) -> bool:
    """
    Update user's last login timestamp
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        True if successful, False if user not found
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
if not user:
        return False
    
    # Assuming you have a last_login field in User model
if hasattr(user, 'last_login'):
        user.last_login = datetime.utcnow()
        await db.commit()
        
        # Don't invalidate cache for last_login - it's not critical
        # and updates too frequently
    
return True


# =============================================================================
# SEARCH AND FILTERING
# =============================================================================

def search_users(
    db: Session,
    search_term: str,
    organization_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20
) -> List[User]:
    """
    Search users by name or email
    
    Args:
        db: Database session
        search_term: Search string
        organization_id: Organization ID (optional filter)
        skip: Pagination offset
        limit: Max results
    
    Returns:
        List of matching User objects
    
    Note: Not cached due to dynamic nature of searches
    """
    search_pattern = f"%{search_term.lower()}%"
    
    query = db.query(User).filter(
        or_(
            User.email.ilike(search_pattern),
            User.first_name.ilike(search_pattern),
            User.last_name.ilike(search_pattern),
            User.username.ilike(search_pattern)
        )
    )
    
if organization_id:
        query = query.filter(User.organization_id == organization_id)
    
return query.offset(skip).limit(limit).all()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# def user_to_dict(user: User) -> Dict[str, Any]:
#     """
#     Convert User object to dictionary for caching
    
#     Args:
#         user: User object
    
#     Returns:
#         User dictionary with serializable values
#     """
#     return {
#         "id": user.id,
#         "email": user.email,
#         "username": user.username,
#         "first_name": user.first_name,
#         "last_name": user.last_name,
#         "organization_id": user.organization_id,
#         "is_active": user.is_active,
#         "is_verified": user.is_verified,
#         "is_superuser": getattr(user, 'is_superuser', False),
#         "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
#         "updated_at": user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None,
#         "last_login": user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
#     }

# ... other functions ...
def user_to_dict(user: UserModel) -> dict:
    """
    Convert a User model instance to a dictionary.
    This is used for caching and serializing user data.
    """
return {
        "id": str(user.id),
        "email": user.email,
        # FIX: Changed from user.username to user.email
        "username": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        # Using getattr with defaults for fields that might not be on the base model
        # but could be added later or exist in a different version.
        "is_verified": getattr(user, 'is_verified', False),
        "is_superuser": getattr(user, 'is_superuser', False),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }

# ... other functions ...

def is_user_in_organization(db: Session, user_id: int, organization_id: int) -> bool:
    """
    Check if user belongs to organization
    
    Args:
        db: Database session
        user_id: User ID
        organization_id: Organization ID
    
    Returns:
        True if user is in organization, False otherwise
    """
    user = result = await db.execute(query)
    return result.scalars().all()
    
return user is not None


def check_email_exists(db: Session, email: str, exclude_user_id: Optional[int] = None) -> bool:
    """
    Check if email already exists in database
    
    Args:
        db: Database session
        email: Email address to check
        exclude_user_id: User ID to exclude from check (for updates)
    
    Returns:
        True if email exists, False otherwise
    """
    query = db.query(User).filter(User.email == email.lower())
    
if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
return query.first() is not None


def check_username_exists(db: Session, username: str, exclude_user_id: Optional[int] = None) -> bool:
    """
    Check if username already exists in database
    
    Args:
        db: Database session
        username: Username to check
        exclude_user_id: User ID to exclude from check (for updates)
    
    Returns:
        True if username exists, False otherwise
    """
    query = db.query(User).filter(User.username == username)
    
if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
return query.first() is not None


def get_user_full_name(user: User) -> str:
    """
    Get user's full name
    
    Args:
        user: User object
    
    Returns:
        Full name string
    """
if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.last_name:
        return user.last_name
    else:
        return user.email.split('@')[0]
    
# Add this to the END of app/services/user_service.py

class UserService:
    """
    Service class wrapper for user operations
    Provides class-based interface consistent with other services
    """
    
@staticmethod
def create(db: Session, user_in: UserCreate) -> User:
        """Create a new user"""
    return create_user(db, user_data=user_in)
    
@staticmethod
async def get_by_id(db: AsyncSession, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
    return get_user_by_id(db, user_id)
    
@staticmethod
async def get_by_email(db: AsyncSession, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
    return get_user_by_email(db, email)
    
@staticmethod
def update(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        """Update user"""
    return update_user(db, user_id, user_data=user_in)
    
@staticmethod
def delete(db: Session, user_id: int, hard_delete: bool = False) -> bool:
        """Delete user"""
    return delete_user(db, user_id, hard_delete)
    
@staticmethod
def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user"""
    return authenticate_user(db, email, password)
    
 