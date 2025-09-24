from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt, JWTError
from app.core.config import settings


# class TokenDecodeMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # Example: add decoded token to request.state
#         # token = request.headers.get("Authorization")
#         # request.state.user = decode_token(token)
#         response = await call_next(request)
#         return response


class TokenDecodeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.token_payload = None
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                request.state.token_payload = payload
            except JWTError:
                request.state.token_payload = None
        response = await call_next(request)
        return response