#app.api.api_router.py

# app/api/api_router.py
from fastapi import APIRouter
from app.api import users, organizations, teams, assessments, predictions, optimization, insights

api_router = APIRouter()

# Attach all sub-routers here
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])




# from fastapi import APIRouter
# from app.api import users, organizations, teams

# api_router = APIRouter()

# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
# api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
