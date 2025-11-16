# app/schemas/user_service.py
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class user_service:
    """User service for database operations"""
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create(db: Session, user_in: UserCreate) -> User:
        """Create new user"""
        db_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            password_hash=get_password_hash(user_in.password),
            is_active=True
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
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        print(f"🔍 DEBUG: Attempting to authenticate user: {email}")
        
        user = user_service.get_by_email(db, email)
        if not user:
            print(f"❌ DEBUG: User not found with email: {email}")
            return None
        
        print(f"✓ DEBUG: User found: {user.id}, checking password...")
        print(f"✓ DEBUG: Stored hash: {user.password_hash[:30]}...")
        
        # CRITICAL FIX: Use password_hash NOT password_hash
        if not verify_password(password, user.password_hash):
            print(f"❌ DEBUG: Password verification failed")
            return None
        
        print(f"✓ DEBUG: Password verified successfully!")
        return user
    
    @staticmethod
    def is_active(user: User) -> bool:
        """Check if user is active"""
        return user.is_active