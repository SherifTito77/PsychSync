# # app/api/v1/users.py
# app/api/v1/users.py
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.schemas.user import UserResponse
# from app.db.models.user import User
# import bcrypt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.db.models.user import User
import bcrypt

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password.decode('utf-8'),
        company=user.company,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse.from_orm(new_user)

@router.get("/me", response_model=UserResponse)
async def read_current_user(db: Session = Depends(get_db)):
    # replace with real DB query
    user = db.query(User).first()
    return user

# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel

# router = APIRouter (tags=["users"])  #prefix="/users",

# # @router.get("/me")
# # async def read_users_me():
# #     return {"message": "Current user"}

# @router.get("/me")
# async def read_users_me():
#     return {"msg": "current user"}

# @router.post("/")
# async def create_user():
#     return {"msg": "user created"}

# @router.post("/register")
# async def register_user():
#     return {"msg": "user registered"}


# # Minimal Pydantic schema
# class UserOut(BaseModel):
#     email: str
#     full_name: str

# # Dummy current user dependency
# async def get_current_user():
#     return UserOut(email="test@example.com", full_name="Test User")

# # Example protected endpoint
# # @router.get("/me", response_model=UserOut)
# # async def read_current_user(current_user: UserOut = Depends(get_current_user)):
# #     return current_user

# # This is a simple example. In a real application, you would integrate with your database and authentication system.
