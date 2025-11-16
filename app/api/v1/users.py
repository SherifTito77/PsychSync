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

