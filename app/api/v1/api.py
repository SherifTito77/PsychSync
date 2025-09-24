# # app/api/v1/api.py

from fastapi import APIRouter
from .users import router as users_router
from .organizations import router as organizations_router
from .auth import router as auth_router
from .teams import router as teams_router

api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(teams_router, prefix="/teams", tags=["teams"])


# # app/api/v1/api.py
# from fastapi import APIRouter

# from .users import router as users_router
# from .organizations import router as organizations_router
# from .auth import router as auth_router

# api_router = APIRouter()

# # Attach routers with prefixes here
# api_router.include_router(users_router, prefix="/users", tags=["users"])
# api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])




# # from fastapi import APIRouter
# # # from app.api.routes import users, organizations
# # # from app.api.v1 import users, organizations, auth  # import submodules normally
# # from .users import router as users_router
# # from .organizations import router as organizations_router
# # from .auth import router as auth_router



# # # api_router = APIRouter()
# # # api_router.include_router(users.router, prefix="/users", tags=["users"])
# # # api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
# # # api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# # api_router = APIRouter()
# # api_router.include_router(users_router, prefix="/users", tags=["users"])
# # api_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
# # api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# # # This file serves as a central place to include all v1 API routes



# # # from fastapi import APIRouter
# # # from app.api.v1.endpoints import example  # your endpoints


# # # from app.api.v1.endpoints import example,auth, users  # ok if endpoints is a folder with __init__.py




# # # from app.api.v1.endpoints.example import router as example_router
# # # from app.api.v1.endpoints.auth import router as auth_router
# # # from app.api.v1.endpoints.users import router as users_router

# # # api_router = APIRouter()
# # # api_router.include_router(example_router, prefix="/example", tags=["example"])
# # # api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# # # api_router.include_router(users_router, prefix="/users", tags=["users"])








