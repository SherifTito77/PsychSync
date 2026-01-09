# app/schemas/user_service.py

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class user_service:
    """User service for database operations"""

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """Create new user"""
        db_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            password_hash=get_password_hash(user_in.password),
            is_active=True,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update(db: Session, user: User, user_in: UserUpdate) -> User:
        """Update user"""
        update_data = user_in.dict(exclude_unset=True)

        if "password" in update_data:
            password_hash = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["password_hash"] = password_hash

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        """Authenticate user with email and password"""
        # SECURITY: Removed debug print to prevent information leakage

        user = user_service.get_by_email(db, email)
        if not user:
            # SECURITY: Removed debug print to prevent information leakage
            return None

        # SECURITY: Removed debug prints showing password hash
        # CRITICAL FIX: Use password_hash NOT password_hash
        if not verify_password(password, user.password_hash):
            # SECURITY: Removed debug print to prevent information leakage
            return None

        return user

    @staticmethod
    def is_active(user: User) -> bool:
        """Check if user is active"""
        return user.is_active
