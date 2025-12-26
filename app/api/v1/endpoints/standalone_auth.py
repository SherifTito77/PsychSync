"""
Standalone authentication endpoint that bypasses all complex dependencies
"""

from fastapi import APIRouter, HTTPException, Form, status, Request

from datetime import datetime, timedelta
import jwt

router = APIRouter()

@router.post("/standalone-login")
async def standalone_login(
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Standalone login with hardcoded test users - no database dependency
    """
    try:
        # Normalize username to lowercase for case-insensitive comparison
        normalized_username = username.lower().strip()

        # Hardcoded test users for development (all keys normalized to lowercase)
        test_users = {
            'test@example.com': {
                'id': '550e8400-e29b-41d4-a716-446655440004',
                'email': 'test@example.com',
                'name': 'Test User'
            },
            'admin@example.com': {
                'id': '550e8400-e29b-41d4-a716-446655440003',
                'email': 'admin@example.com',
                'name': 'Admin User'
            },
            # Add some common variations that might be sent
            'test@psychsync.com': {
                'id': '550e8400-e29b-41d4-a716-446655440004',
                'email': 'test@psychsync.com',
                'name': 'Test User'
            },
            'user@example.com': {
                'id': '550e8400-e29b-41d4-a716-446655440005',
                'email': 'user@example.com',
                'name': 'Regular User'
            },
            'test@test.com': {
                'id': '550e8400-e29b-41d4-a716-446655440006',
                'email': 'test@test.com',
                'name': 'Demo User'
            }
        }

        # Check if user exists in our test users (case-insensitive)
        if normalized_username not in test_users:
            # For development, accept any valid email format for testing
            if '@' in normalized_username and '.' in normalized_username.split('@')[1]:
                test_users[normalized_username] = {
                    'id': f'demo-{hash(normalized_username) % 100000}',
                    'email': normalized_username,
                    'name': normalized_username.split('@')[0].title()
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email format"
                )

        # For development, accept any password for test users
        user_data = test_users[normalized_username]

        # Create JWT token
        from app.core.config import settings
        token_data = {
            "sub": user_data["email"],
            "user_id": user_data["id"],
            "name": user_data["name"],
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow()
        }

        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

        return {
            "success": True,
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user_data["id"],
                "email": user_data["email"],
                "name": user_data["name"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Standalone login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/standalone-me")
async def standalone_get_user_info(request: Request):
    """
    Simple endpoint to get user info from Authorization header without database
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )

        token = auth_header.split(" ")[1]

        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        return {
            "success": True,
            "user": {
                "id": payload.get("user_id"),
                "email": payload.get("sub"),
                "name": payload.get("name"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Standalone me endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )