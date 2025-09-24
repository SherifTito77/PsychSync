from sqlalchemy.orm import Session
from app.db.models.user import User
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user(db: Session, user_id: int):
    return db.query(User).get(user_id)

def create_user(db: Session, email: str, password: str, full_name: str | None = None):
    hashed = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed, full_name=full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
