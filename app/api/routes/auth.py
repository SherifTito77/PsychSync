# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import create_access_token, verify_password
from app.schemas.user import UserCreate, UserOut

router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # TODO: Replace with actual DB user lookup
    fake_user = {"username": "test@example.com", "password": "$2b$12$fakehashedpassword"}  # bcrypt hash
    if form_data.username != fake_user["username"] or not verify_password(form_data.password, fake_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=form_data.username)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    # TODO: Replace with actual DB create logic
    return {"id": 1, "email": user.email, "full_name": user.full_name, "is_active": True}
