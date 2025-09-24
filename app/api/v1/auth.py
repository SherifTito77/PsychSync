# # # app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.user import UserCreate, UserResponse
import bcrypt
from app.core.auth import create_access_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password.decode('utf-8'),
        company=user.company,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.from_orm(db_user)

@router.post("/login")
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }


# # app/api/v1/auth.py
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.db.models.user import User
# from app.schemas.user import UserCreate, UserResponse
# from app.core.security import create_access_token, verify_password, get_password_hash
# from datetime import timedelta

# router = APIRouter()

# @router.post("/register", response_model=UserResponse)
# async def register_user(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.email == user.email).first()
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     hashed_password = get_password_hash(user.password)
#     db_user = User(
#         email=user.email,
#         name=user.name,
#         hashed_password=hashed_password,
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# @router.post("/login")
# async def login_user(email: str, password: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.email == email).first()
#     if not user or not verify_password(password, user.hashed_password):
#         raise HTTPException(status_code=401, detail="Incorrect credentials")
#     access_token_expires = timedelta(minutes=30)
#     token = create_access_token({"sub": user.email}, expires_delta=access_token_expires)
#     return {"access_token": token, "token_type": "bearer"}


# # from fastapi import APIRouter, Depends, HTTPException
# # from sqlalchemy.orm import Session
# # from app.db.database import get_db
# # from app.db.models.user import User
# # from app.schemas.user import UserCreate, UserResponse
# # from app.core.security import create_access_token, verify_password

# # router = APIRouter()

# # @router.post("/register", response_model=UserResponse)
# # async def register_user(user: UserCreate, db: Session = Depends(get_db)):
# #     db_user = db.query(User).filter(User.email == user.email).first()
# #     if db_user:
# #         raise HTTPException(status_code=400, detail="Email already registered")
# #     hashed_password = verify_password(user.password)
# #     db_user = User(
# #         email=user.email,
# #         name=user.name,
# #         hashed_password=hashed_password,
# #     )
# #     db.add(db_user)
# #     db.commit()
# #     db.refresh(db_user)
# #     return db_user

# # @router.post("/login")
# # async def login_user(email: str, password: str, db: Session = Depends(get_db)):
# #     user = db.query(User).filter(User.email == email).first()
# #     if not user or not verify_password(password, user.hashed_password):
# #         raise HTTPException(status_code=401, detail="Incorrect credentials")
# #     token = create_access_token({"sub": user.email})
# #     return {"access_token": token, "token_type": "bearer"}
