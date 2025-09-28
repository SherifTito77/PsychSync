# main.py - Clean FastAPI Application Entry Point

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.core.cache import set_key
from app.core.middleware import setup_middleware
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting PsychSync AI app...")
    init_db()
    await set_key("welcome", "Hello, PsychSync!")
    yield
    logger.info("Shutting down PsychSync AI app...")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="PsychSync AI API",
        description="PsychSync TaskMaster API - Behavioral Analytics for High-Performance Agile Teams",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Global endpoints
    @app.get("/")
    def read_root():
        return {"message": "PsychSync AI API is running!"}
    
    @app.get("/welcome")
    async def read_welcome():
        return {"message": await set_key('welcome', 'Hello, PsychSync!')}
    
    @app.get("/health")
    async def health_check():
        from app.core.cache import get_redis_client
        
        try:
            redis_client = get_redis_client()
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
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )