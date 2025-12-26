#!/usr/bin/env python3
"""
Minimal FastAPI app to test authentication without middleware
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database_minimal import AsyncSessionLocalMinimal, get_async_db_minimal
from app.core.security import verify_password
from app.db.models.user import User
from datetime import timedelta
# from app.core.security import create_access_token  # Using basic JWT instead

# Basic JWT imports for simple token creation
import jwt
from datetime import datetime, timedelta

# Create minimal FastAPI app
app = FastAPI(title="Minimal Auth Test")

# Basic JWT settings (minimal - just for testing)
JWT_SECRET_KEY = "test-secret-key-for-minimal-auth-only"
JWT_ALGORITHM = "HS256"

# Minimal database dependency
async def get_db():
    async for session in get_async_db_minimal():
        yield session

@app.get("/")
async def root():
    return {"status": "minimal auth test running"}

@app.post("/token")
async def login_test(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Minimal token endpoint for testing authentication logic
    """
    try:
        print(f"🔐 Login attempt for: {form_data.username}")

        # Query user
        result = await db.execute(
            select(User).where(User.email == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        print(f"👤 Found user: {user.email}, is_active: {user.is_active}")

        # Verify password
        if not await verify_password(form_data.password, user.password_hash):
            print(f"❌ Password verification failed for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        print(f"✅ Password verified successfully for: {form_data.username}")

        # Create simple JWT token (bypassing complex enterprise logic)
        access_token_expires = timedelta(minutes=30)
        expire = datetime.utcnow() + access_token_expires

        token_data = {
            "sub": user.email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        access_token = jwt.encode(
            token_data,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )

        print(f"🎫 Token created successfully for: {form_data.username}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "email": user.email,
                "id": user.id,
                "role": user.role
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting minimal auth test server on port 8001...")
    uvicorn.run("minimal_auth_test:app", host="0.0.0.0", port=8001, reload=False)