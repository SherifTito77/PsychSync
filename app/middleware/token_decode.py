# app/middleware/token_decode.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

class TokenDecodeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Example: decode JWT from headers
        token = request.headers.get("Authorization")
        request.state.user = None
        if token:
            try:
                # Decode token logic here
                payload = {"sub": "user@example.com"}  # Replace with actual decode
                request.state.user = payload
            except Exception:
                request.state.user = None
        response = await call_next(request)
        return response
