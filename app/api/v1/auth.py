# # # # # app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.schemas.auth import Token
from app.api.dependencies.auth import fake_users_db

router = APIRouter()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or form_data.password != "testpassword":  # TODO: Verify actual password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# from datetime import datetime, timedelta
# from typing import Optional
# from jose import jwt, JWTError
# from passlib.context import CryptContext
# from app.schemas.user import Token

# # SECRET_KEY for JWT (in production, store in .env)
# SECRET_KEY = "supersecretkey"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # OAuth2 scheme
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# # Fake DB for example
# fake_users_db = {
#     "testuser@example.com": {
#         "name": "Test User",
#         "email": "testuser@example.com",
#         "hashed_password": pwd_context.hash("testpassword"),
#         "is_active": True
#     }
# }

# router = APIRouter()


# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)


# def authenticate_user(email: str, password: str):
#     user = fake_users_db.get(email)
#     if not user:
#         return False
#     if not verify_password(password, user["hashed_password"]):
#         return False
#     return user


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# @router.post("/token", response_model=Token)
# def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = authenticate_user(form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token(data={"sub": user["email"]})
#     return {"access_token": access_token, "token_type": "bearer"}



# # from fastapi import APIRouter, Depends, HTTPException
# # from sqlalchemy.orm import Session
# # from app.db.database import get_db
# # from app.db.models.user import User
# # from app.schemas.user import UserCreate, UserResponse
# # import bcrypt
# # from app.core.auth import create_access_token

# # router = APIRouter()

# # @router.post("/register", response_model=UserResponse)
# # async def register(user: UserCreate, db: Session = Depends(get_db)):
# #     db_user = db.query(User).filter(User.email == user.email).first()
# #     if db_user:
# #         raise HTTPException(status_code=400, detail="Email already registered")
# #     hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
# #     db_user = User(
# #         email=user.email,
# #         name=user.name,
# #         hashed_password=hashed_password.decode('utf-8'),
# #         company=user.company,
# #         role=user.role
# #     )
# #     db.add(db_user)
# #     db.commit()
# #     db.refresh(db_user)
# #     return UserResponse.from_orm(db_user)

# # @router.post("/login")
# # async def login(email: str, password: str, db: Session = Depends(get_db)):
# #     user = db.query(User).filter(User.email == email).first()
# #     if not user or not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
# #         raise HTTPException(status_code=401, detail="Incorrect email or password")
# #     access_token = create_access_token(data={"sub": user.email})
# #     return {
# #         "access_token": access_token,
# #         "token_type": "bearer",
# #         "user": UserResponse.from_orm(user)
# #     }


# # # # app/api/v1/auth.py
# # # from fastapi import APIRouter, Depends, HTTPException
# # # from sqlalchemy.orm import Session
# # # from app.db.database import get_db
# # # from app.db.models.user import User
# # # from app.schemas.user import UserCreate, UserResponse
# # # from app.core.security import create_access_token, verify_password, get_password_hash
# # # from datetime import timedelta

# # # router = APIRouter()

# # # @router.post("/register", response_model=UserResponse)
# # # async def register_user(user: UserCreate, db: Session = Depends(get_db)):
# # #     db_user = db.query(User).filter(User.email == user.email).first()
# # #     if db_user:
# # #         raise HTTPException(status_code=400, detail="Email already registered")
# # #     hashed_password = get_password_hash(user.password)
# # #     db_user = User(
# # #         email=user.email,
# # #         name=user.name,
# # #         hashed_password=hashed_password,
# # #     )
# # #     db.add(db_user)
# # #     db.commit()
# # #     db.refresh(db_user)
# # #     return db_user

# # # @router.post("/login")
# # # async def login_user(email: str, password: str, db: Session = Depends(get_db)):
# # #     user = db.query(User).filter(User.email == email).first()
# # #     if not user or not verify_password(password, user.hashed_password):
# # #         raise HTTPException(status_code=401, detail="Incorrect credentials")
# # #     access_token_expires = timedelta(minutes=30)
# # #     token = create_access_token({"sub": user.email}, expires_delta=access_token_expires)
# # #     return {"access_token": token, "token_type": "bearer"}


# # # # from fastapi import APIRouter, Depends, HTTPException
# # # # from sqlalchemy.orm import Session
# # # # from app.db.database import get_db
# # # # from app.db.models.user import User
# # # # from app.schemas.user import UserCreate, UserResponse
# # # # from app.core.security import create_access_token, verify_password

# # # # router = APIRouter()

# # # # @router.post("/register", response_model=UserResponse)
# # # # async def register_user(user: UserCreate, db: Session = Depends(get_db)):
# # # #     db_user = db.query(User).filter(User.email == user.email).first()
# # # #     if db_user:
# # # #         raise HTTPException(status_code=400, detail="Email already registered")
# # # #     hashed_password = verify_password(user.password)
# # # #     db_user = User(
# # # #         email=user.email,
# # # #         name=user.name,
# # # #         hashed_password=hashed_password,
# # # #     )
# # # #     db.add(db_user)
# # # #     db.commit()
# # # #     db.refresh(db_user)
# # # #     return db_user

# # # # @router.post("/login")
# # # # async def login_user(email: str, password: str, db: Session = Depends(get_db)):
# # # #     user = db.query(User).filter(User.email == email).first()
# # # #     if not user or not verify_password(password, user.hashed_password):
# # # #         raise HTTPException(status_code=401, detail="Incorrect credentials")
# # # #     token = create_access_token({"sub": user.email})
# # # #     return {"access_token": token, "token_type": "bearer"}
