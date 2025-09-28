# # # # app/api/v1/users.py

from fastapi import APIRouter,Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings



router = APIRouter()
# from app.schemas.user import UserOut
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

@router.get("/me")
async def read_current_user():
    # your logic here
    pass


# Your fake users DB (move this to a better location later)
fake_users_db = {
    "testuser@example.com": {
        "email": "testuser@example.com",
        "name": "Test User", 
        "is_active": True
    }
}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = fake_users_db.get(email)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user



# # # app/api/v1/users.py

# from fastapi import APIRouter, Depends, HTTPException, status
# from app.schemas.user import UserOut
# from app.api.v1.auth import oauth2_scheme, jwt, JWTError, SECRET_KEY, fake_users_db

# router = APIRouter()


# def get_current_user(token: str = Depends(oauth2_scheme)):
#     from jose import jwt, JWTError
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         email: str = payload.get("sub")
#         if email is None:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                                 detail="Could not validate credentials")
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="Could not validate credentials")
#     user = fake_users_db.get(email)
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
#                             detail="User not found")
#     return user


# # @router.get("/me", response_model=UserOut)
# # def read_users_me(current_user: dict = Depends(get_current_user)):
# #     return current_user

# @router.get("/me", response_model=UserOut)
# def read_users_me(current_user: dict = Depends(get_current_user)):
#     # Transform DB object to match UserOut
#     return {
#         "id": 1,
#         "name": current_user["name"],
#         "email": current_user["email"],
#         "is_active": current_user.get("is_active", True),
#         "created_at": None,
#         "updated_at": None
#     }








# # # from fastapi import APIRouter, Depends
# # # from sqlalchemy.orm import Session
# # # from app.db.database import get_db
# # # from app.schemas.user import UserResponse
# # # from app.db.models.user import User
# # # import bcrypt

# # from fastapi import APIRouter, Depends, HTTPException
# # from sqlalchemy.orm import Session
# # from app.db.database import get_db
# # from app.schemas.user import UserCreate, UserResponse
# # from app.db.models.user import User
# # import bcrypt

# # router = APIRouter()

# # @router.post("/", response_model=UserResponse)
# # async def create_user(user: UserCreate, db: Session = Depends(get_db)):
# #     db_user = db.query(User).filter(User.email == user.email).first()
# #     if db_user:
# #         raise HTTPException(status_code=400, detail="Email already registered")
# #     hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
# #     new_user = User(
# #         email=user.email,
# #         name=user.name,
# #         hashed_password=hashed_password.decode('utf-8'),
# #         company=user.company,
# #         role=user.role
# #     )
# #     db.add(new_user)
# #     db.commit()
# #     db.refresh(new_user)
# #     return UserResponse.from_orm(new_user)

# # @router.get("/me", response_model=UserResponse)
# # async def read_current_user(db: Session = Depends(get_db)):
# #     # replace with real DB query
# #     user = db.query(User).first()
# #     return user

# # # from fastapi import APIRouter, Depends, HTTPException
# # # from pydantic import BaseModel

# # # router = APIRouter (tags=["users"])  #prefix="/users",

# # # # @router.get("/me")
# # # # async def read_users_me():
# # # #     return {"message": "Current user"}

# # # @router.get("/me")
# # # async def read_users_me():
# # #     return {"msg": "current user"}

# # # @router.post("/")
# # # async def create_user():
# # #     return {"msg": "user created"}

# # # @router.post("/register")
# # # async def register_user():
# # #     return {"msg": "user registered"}


# # # # Minimal Pydantic schema
# # # class UserOut(BaseModel):
# # #     email: str
# # #     full_name: str

# # # # Dummy current user dependency
# # # async def get_current_user():
# # #     return UserOut(email="test@example.com", full_name="Test User")

# # # # Example protected endpoint
# # # # @router.get("/me", response_model=UserOut)
# # # # async def read_current_user(current_user: UserOut = Depends(get_current_user)):
# # # #     return current_user

# # # # This is a simple example. In a real application, you would integrate with your database and authentication system.
