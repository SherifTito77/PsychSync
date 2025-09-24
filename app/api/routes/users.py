#app.api.routes.users.py



from app.schemas.user import UserOut, UserCreate
from app.middleware.token_decode import TokenDecodeMiddleware
from fastapi import Request

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import crud



from app.core.auth import create_access_token, verify_password, get_password_hash


router = APIRouter()

@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_pw = get_password_hash(user.password)
    # save to db (pseudo)
    return {"email": user.email, "id": 1}


router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def read_me(request: Request):
    if not request.state.user:
        raise Exception("Not authenticated")
    return request.state.user

@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate):
    return {"id": 1, "email": user.email}



@router.post("/register", response_model=UserOut)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.user.get_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.user.create(db=db, obj_in=user)




# # app/api/routes/users.py
# from fastapi import APIRouter, Depends
# from app.api.v1.deps import get_current_user
# from app.schemas.user import UserCreate, UserOut, UserResponse

# from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationOut


# router = APIRouter(prefix="/users", tags=["users"])

# @router.get("/me", response_model=UserOut)
# def read_me(current_user = Depends(get_current_user)):
#     return current_user



# from fastapi import APIRouter, Depends
# from app.api.v1.deps import get_current_user
# from app.schemas.user import UserOut, UserCreate, UserResponse

# router = APIRouter(prefix="/users", tags=["users"])

# @router.get("/me", response_model=UserOut)
# def read_me(current_user = Depends(get_current_user)):
#     return current_user




