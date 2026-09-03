"""
AI Agents Service - Standalone FastAPI Application

Runs on port 5000, separate from the main PsychSync application.
Provides all 20 AI automation agents as independent microservices.

Port: 5000
Documentation: http://localhost:5000/docs
"""

import logging
import os

# Add project root to Python path
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all agent routers
from app.api.v1.endpoints.ai_agents import router as ai_agents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    logger.info("🤖 AI Agents Service starting up...")
    yield
    logger.info("🤖 AI Agents Service shutting down...")


# Create FastAPI application
app = FastAPI(
    title="PsychSync AI Agents Service",
    description="""
    # 🤖 PsychSync AI Agents Automation Service

    **20 AI-powered agents for security, development, and operations automation**

    ## Security Agents (3)
    - Security Headers Validator - OWASP compliance checking
    - Encryption Strategy Advisor - Database encryption recommendations
    - Unsafe Script Detector - Frontend vulnerability scanning

    ## Development Agents (8)
    - Coding Style Enforcer - Code quality and style standards
    - Performance Regression Detector - Performance monitoring
    - Localization Key Detector - i18n coverage analysis
    - Slow Endpoint Tracker - API performance tracking
    - Release Notes Generator - Automated changelog creation
    - Permission Gap Detector - Security audit
    - Test Coverage Reporter - Test quality metrics
    - Refactoring Target Proposer - Code improvement suggestions

    ## Operations Agents (9)
    - UX Telemetry Tracker - User experience analysis
    - Environment Config Detector - Configuration validation
    - Incident Mitigation Planner - Incident response automation
    - Dependency Updater - Package management
    - PR-Jira Mapper - Integration automation
    - Uptime Monitor - System availability tracking
    - Stability Score Calculator - System health metrics
    - Architecture Drift Detector - Code quality monitoring
    - Bug Environment Creator - Testing automation

    **Base URL**: `/api/v1`
    **Authentication**: JWT token required for all endpoints
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://0.0.0.0:5000",
        "http://localhost:5000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Root Endpoints
# =============================================================================


@app.get("/")
async def root():
    """Root endpoint - service information"""
    return {
        "service": "PsychSync AI Agents Service",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api/v1",
            "agents_status": "/api/v1/ai-agents/status",
        },
        "agents": {
            "total": 20,
            "security": 3,
            "development": 8,
            "operations": 9,
        },
        "documentation": "https://docs.psychsync.com/ai-agents",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-agents",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


# =============================================================================
# Include AI Agents Router
# =============================================================================

app.include_router(
    ai_agents_router,
    prefix="/api/v1",
)


# =============================================================================
# Error Handlers
# =============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status": "error",
            "message": exc.detail,
            "data": {
                "path": str(request.url.path),
                "method": request.method,
            },
            "errors": [{"code": f"HTTP_{exc.status_code}", "message": exc.detail}],
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "ai-agents",
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "status": "error",
            "message": "Internal server error",
            "data": {
                "path": str(request.url.path),
                "method": request.method,
            },
            "errors": [
                {
                    "code": "INTERNAL_ERROR",
                    "message": (
                        str(exc)
                        if os.getenv("DEBUG")
                        else "An unexpected error occurred"
                    ),
                }
            ],
            "meta": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "service": "ai-agents",
            },
        },
    )


# =============================================================================
# Startup
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info("=" * 60)
    logger.info("🤖 PSYNCSYNC AI AGENTS SERVICE")
    logger.info("=" * 60)
    logger.info(f"Port: {port}")
    logger.info(f"Host: {host}")
    logger.info(f"Reload: {reload}")
    logger.info(f"Documentation: http://localhost:{port}/docs")
    logger.info(f"API Status: http://localhost:{port}/api/v1/ai-agents/status")
    logger.info("=" * 60)

    uvicorn.run(
        "ai_agents_service:app", host=host, port=port, reload=reload, log_level="info"
    )
