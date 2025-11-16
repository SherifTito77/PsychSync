
# app/main.py - FastAPI Application Entry Point

import os
import logging
import redis
from contextlib import asynccontextmanager
from typing import Dict, Any

# Standard library imports
from datetime import datetime, timedelta

# Third-party imports
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn

# Local application imports
from app.core.cache import cache_set
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.constants import AppInfo, HttpStatus, Security, API, CORS_ORIGINS
from app.core.exceptions import PsychSyncException, create_error_response
from app.core.handlers import (
    psychsync_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from app.core.security_middleware import SecurityMiddleware

# Import the consolidated router from our clean API file
from app.api.v1.api import api_router

# Sentry and other initializations
import sentry_sdk
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )

# --- Initial Setup ---
load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

# --- Rate Limiting Setup ---
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

# --- Application Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    logger.info("Starting PsychSync AI app...")
    if not os.getenv("TESTING"):
        try:
            cache_set("welcome", "Hello, PsychSync!")
            logger.info("Redis initialized successfully.")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
    yield
    logger.info("Shutting down PsychSync AI app...")

# --- FastAPI Application Instance ---
app = FastAPI(
    title=AppInfo.API_TITLE,
    description=AppInfo.DESCRIPTION,
    version=AppInfo.VERSION,
    lifespan=lifespan,
    docs_url=AppInfo.DOCS_URL,
    redoc_url=AppInfo.REDOC_URL,
)

# --- Middleware Configuration ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Global Exception Handlers ---
app.add_exception_handler(PsychSyncException, psychsync_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# --- External Service Initialization ---
redis_client = redis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    decode_responses=True
)

# Add advanced security middleware
app.add_middleware(
    SecurityMiddleware,
    redis_client=redis_client,
    enable_rate_limiting=True,
    enable_request_validation=True,
    enable_ip_whitelist=False  # Set to True to enable IP whitelist
)

# --- API Routers ---
# Include the main API router (this already has /api/v1 prefix from routes.py)
app.include_router(api_router)

# --- Root and Health Check Endpoints ---
@app.get("/")
def read_root() -> Dict[str, str]:
    """API root endpoint"""
    return {
        "message": f"{AppInfo.API_TITLE} is running!",
        "version": AppInfo.VERSION,
        "docs": AppInfo.DOCS_URL,
        "redoc": AppInfo.REDOC_URL
    }

@app.get("/health")
async def health_check_main() -> Dict[str, Any]:
    """Health check endpoint"""
    redis_status = "disconnected"
    try:
        if await redis_client.ping():
            redis_status = "connected"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    # Check database health
    try:
        from app.core.database import check_db_health
        db_status = "connected" if await check_db_health() else "disconnected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return {
        "status": "healthy",
        "version": AppInfo.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": db_status,
            "redis": redis_status,
            "ai_engine": "ready"
        },
    }

# --- Uvicorn Runner ---
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )



