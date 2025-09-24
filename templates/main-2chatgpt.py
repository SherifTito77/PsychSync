
# # app/main.py - FastAPI Application

# from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from fastapi.openapi.utils import get_openapi
# from sqlalchemy.orm import Session
# from contextlib import asynccontextmanager
# from typing import List, Optional
# import uvicorn
# import logging
# import os
# from datetime import datetime, timedelta
# from jose import jwt
# import redis
# from dotenv import load_dotenv
# import bcrypt

# # Load environment variables
# load_dotenv()

# # Database
# from app.db.database import get_db
# from app.db.init_db import init_db
# from app.db.models.user import User
# from app.db.models.team import Team
# from app.db.models.team_member import TeamMember
# from app.db.models.assessment import Assessment
# from app.db.models.prediction import Prediction

# # Schemas
# from app.schemas import (
#     UserCreate, UserResponse,
#     TeamCreate, TeamResponse,
#     AssessmentCreate, AssessmentResponse,
#     PredictionResponse,
#     TeamOptimizationRequest,
#     BehavioralInsight,
#     OrganizationCreate
# )

# # Routers
# from app.api.v1.api import api_router  # central aggregator: users, auth, orgs

# # Core
# from app.core.auth import create_access_token, verify_password
# from app.core.cache import set_key, get_key

# # AI
# from ai.engine import BehavioralAIEngine, TeamOptimizer, PredictiveAnalytics
# from ai.processors.psychsync_assessment_processors import (
#     EnneagramProcessor,
#     MBTIProcessor,
#     BigFiveProcessor,
#     PIProcessor,
#     StrengthsProcessor,
#     SocialStylesProcessor
# )

# # Logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Redis
# redis_client = redis.Redis(
#     host=os.getenv("REDIS_HOST", "localhost"),
#     port=int(os.getenv("REDIS_PORT", 6379)),
#     db=0,
#     decode_responses=True
# )

# # Security
# security = HTTPBearer()
# SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# # Initialize AI components
# ai_engine = BehavioralAIEngine()
# team_optimizer = TeamOptimizer()
# predictive_analytics = PredictiveAnalytics()

# # Assessment processors
# assessment_processors = {
#     "enneagram": EnneagramProcessor(),
#     "mbti": MBTIProcessor(),
#     "big_five": BigFiveProcessor(),
#     "predictive_index": PIProcessor(),
#     "strengths": StrengthsProcessor(),
#     "social_styles": SocialStylesProcessor()
# }

# # FastAPI lifespan
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("Starting PsychSync AI app...")
#     await init_db()
#     await set_key("welcome", "Hello, PsychSync!")
#     yield
#     logger.info("Shutting down PsychSync AI app...")

# # FastAPI app
# app = FastAPI(
#     title="PsychSync AI API",
#     description="PsychSync TaskMaster API - Behavioral Analytics for High-Performance Agile Teams",
#     version="1.0.0",
#     lifespan=lifespan,
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json",
# )

# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000", "https://psychsync.ai"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include main API router (users, auth, orgs)
# app.include_router(api_router, prefix="/api/v1")

# # JWT auth helper
# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     db: Session = Depends(get_db)
# ):
#     try:
#         payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if not username:
#             raise HTTPException(status_code=401, detail="Could not validate credentials")
#     except jwt.JWTError:
#         raise HTTPException(status_code=401, detail="Could not validate credentials")
    
#     user = db.query(User).filter(User.email == username).first()
#     if not user:
#         raise HTTPException(status_code=401, detail="User not found")
#     return user

# # OpenAPI customization for auth
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title=app.title,
#         version=app.version,
#         description=app.description,
#         routes=app.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "OAuth2PasswordBearer": {
#             "type": "oauth2",
#             "flows": {"password": {"tokenUrl": "/api/v1/auth/token", "scopes": {}}}
#         }
#     }
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app.openapi = custom_openapi

# # Root & health endpoints
# @app.get("/")
# def read_root():
#     return {"message": "PsychSync AI API is running!"}

# @app.get("/welcome")
# async def read_welcome():
#     return {"message": await get_key("welcome")}

# @app.get("/health")
# async def health_check():
#     try:
#         redis_status = "connected" if redis_client.ping() else "disconnected"
#     except:
#         redis_status = "disconnected"
#     return {
#         "status": "healthy",
#         "timestamp": datetime.utcnow(),
#         "version": "1.0.0",
#         "services": {
#             "database": "connected",
#             "redis": redis_status,
#         }
#     }

# # Background tasks
# async def analyze_user_profile(user_id: int, assessment_id: int):
#     logger.info(f"Analyzing profile for user {user_id}, assessment {assessment_id}")
#     # Implement analysis logic here

# async def generate_team_insights(team_id: int, optimization_result: dict):
#     logger.info(f"Generating insights for team {team_id}")
#     # Implement insights generation logic

# async def generate_behavioral_insights(team_id: int, db: Session) -> List[BehavioralInsight]:
#     insights = [
#         BehavioralInsight(
#             type="team_compatibility",
#             title="High Team Compatibility Detected",
#             description="Your team shows strong personality compatibility",
#             confidence=0.85,
#             priority="high",
#             recommendations=["Leverage team's natural collaboration", "Focus on creative projects"]
#         ),
#         BehavioralInsight(
#             type="conflict_risk",
#             title="Potential Communication Conflicts",
#             description="Detected personality traits that may lead to communication challenges",
#             confidence=0.72,
#             priority="medium",
#             recommendations=["Establish clear communication protocols", "Schedule regular check-ins"]
#         )
#     ]
#     return insights

# # Run server
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

