
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Optional
import logging
import redis
import os
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import custom modules
from app.db.database import get_db, init_db
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.assessment import Assessment
from app.db.models.team_member import TeamMember
from app.db.models.prediction import Prediction

from app.schemas import (
    OrganizationCreate,
    UserCreate,
    UserResponse,
    TeamCreate,
    TeamResponse,
    AssessmentCreate,
    AssessmentResponse,
    PredictionResponse,
    TeamOptimizationRequest,
    BehavioralInsight
)

from app.api.v1.api import api_router
from app.core.cache import set_key, get_key
from app.core.auth import create_access_token, verify_password

# Import AI components
from ai.engine import (
    BehavioralAIEngine, 
    TeamOptimizer, 
    PredictiveAnalytics,
    PersonalityFrameworkProcessor
)
from ai.processors.psychsync_assessment_processors import (
    EnneagramProcessor, 
    MBTIProcessor, 
    BigFiveProcessor,
    PIProcessor, 
    StrengthsProcessor, 
    SocialStylesProcessor
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# AI components
ai_engine = BehavioralAIEngine()
team_optimizer = TeamOptimizer()
predictive_analytics = PredictiveAnalytics()

assessment_processors = {
    "enneagram": EnneagramProcessor(),
    "mbti": MBTIProcessor(),
    "big_five": BigFiveProcessor(),
    "predictive_index": PIProcessor(),
    "strengths": StrengthsProcessor(),
    "social_styles": SocialStylesProcessor()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PsychSync AI app...")
    await init_db()
    await set_key("welcome", "Hello, PsychSync!")
    yield
    logger.info("Shutting down PsychSync AI app...")

app = FastAPI(
    title="PsychSync AI API",
    description="PsychSync TaskMaster API - Behavioral Analytics for High-Performance Agile Teams",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://psychsync.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {"password": {"tokenUrl": "/api/v1/auth/token", "scopes": {}}}
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Example endpoint
@app.get("/me")
async def read_current_user():
    return {"email": "test@example.com", "full_name": "Test User"}

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "PsychSync AI API is running!"}

@app.get("/welcome")
async def read_welcome():
    return {"message": await get_key("welcome")}

@app.get("/health")
async def health_check():
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "disconnected"
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "redis": redis_status,
            "ai_engine": "ready"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )