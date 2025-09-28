# # app/api/v1/__init__.py

# from fastapi import APIRouter
# from app.api.v1 import auth, users

# api_router = APIRouter()
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])


# from fastapi import APIRouter
# from app.api.v1 import users, organizations, auth  # add others here

# # can clean main.py by importing from here

# # from app.api.v1.users import router as users_router
# # from app.api.v1.auth import router as auth_router
# # from app.api.v1.organizations import router as orgs_router


# api_router = APIRouter()
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])



# # # Add other routers as needed
# # You can also include other endpoints or routers her
# # from app.api.v1 import other_modules
# # api_router.include_router(other_modules.router, prefix="/other", tags=["other"])e
# # This file serves as a central place to include all v1 API routes

