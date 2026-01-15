"""
Simple authentication endpoint for testing purposes
Minimal implementation without complex security dependencies
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Form, HTTPException, Request, status
import jwt
from sqlalchemy import text

from app.core.config.settings import settings

router = APIRouter()


# Create a simple async engine for auth endpoints
async def get_auth_db_session():
    """Get a simple database session for authentication without complex dependencies"""
    from app.core.database import get_async_db_with_retry

    async for session in get_async_db_with_retry():
        yield session
        break


@router.post("/simple-login")
async def simple_login(username: str = Form(...), password: str = Form(...)):
    """
    Simple login endpoint that works without complex dependencies.
    For development/testing: Accepts any user that exists in the database with any password.
    """
    try:
        # Get database session
        from app.api.v1.deps import get_db

        # Get first session from the generator
        db_gen = get_db()
        db = await db_gen.__anext__()

        try:
            # Query user from database
            result = await db.execute(
                text("SELECT id, email, full_name FROM users WHERE email = :email"), {"email": username}
            )
            user = result.fetchone()

            if not user:
                print(f"❌ Login failed: User '{username}' not found in database")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

            print(f"✅ User found: {user.email}, attempting login...")

            # For demo/development purposes: accept ANY user with ANY password
            # In production, you would validate the password hash here
            # Create simple JWT token
            from app.core.config import settings

            token_data = {
                "sub": user.email,
                "user_id": str(user.id),
                "name": user.full_name,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
            }

            token = jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

            print(f"✅ Login successful for: {user.email}")

            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "user": {"id": str(user.id), "email": user.email, "name": user.full_name},
            }
        finally:
            try:
                await db_gen.aclose()
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        print(f"Simple login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        ) from e


@router.get("/verify-token/{token}")
async def verify_token(token: str):
    """
    Simple token verification endpoint
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return {"success": True, "valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "valid": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "valid": False, "error": "Invalid token"}


@router.get("/me")
async def get_current_user_info(request: Request):
    """
    Simple endpoint to get current user info from Authorization header
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header"
            )

        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        return {
            "success": True,
            "user": {
                "id": payload.get("user_id"),
                "email": payload.get("sub"),
                "name": payload.get("name"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Me endpoint error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
