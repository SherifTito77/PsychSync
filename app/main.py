# # # main.py - FastAPI app Application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import redis
import os
from dotenv import load_dotenv
from app.api.v1.api import api_router
from app.core.cache import set_key
from app.db.database import init_db

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PsychSync AI app...")
    init_db()
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


# Initialize Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)


# In your main.py, replace the startup event with:
@app.on_event("startup")
async def startup_event():
    try:
        # Don't create tables here in async context
        print("Starting PsychSync AI app...")
        # Remove any database table creation from here
    except Exception as e:
        print(f"Startup error: {e}")








# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://psychsync.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router (this brings in /users, /organizations, /auth, etc.)
app.include_router(api_router, prefix="/api/v1")

# Example global endpoint
@app.get("/")
def read_root():
    return {"message": "PsychSync AI API is running!"}

@app.get("/welcome")
async def read_welcome():
    return {"message": await set_key('welcome', 'Hello, PsychSync!')}

@app.get("/health")
async def health_check():
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except Exception:
        redis_status = "disconnected"
    return {
        "status": "healthy",
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



