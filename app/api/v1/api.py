# app/api/v1/api.py
"""
Single authoritative API router for PsychSync AI v1 endpoints
Consolidates all API routes with proper hierarchy and no conflicts
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    admin,
    # templates,  # Temporarily disabled to isolate registration issues
    health,
    # team_optimization,  # Temporarily disabled due to import issues
    # Temporarily disabled due to missing models
    # teams,  # Needs Team, TeamMember models
    # assessments,  # Needs Assessment model
    # responses,  # Needs AssessmentResponse model
    # analytics,  # Needs multiple models
)

# Temporarily disable all optional endpoints to resolve SQLAlchemy issues
# Optional endpoints that may not exist yet
# try:
#     from app.api.v1.endpoints import organizations
# except ImportError:
#     organizations = None

# Email analysis endpoints
# try:
#     from app.api.v1.endpoints import email_connections
# except (ImportError, IndentationError, SyntaxError):
#     email_connections = None

# Communication analysis endpoints
# try:
#     from app.api.v1.endpoints import communication_analysis
# except (ImportError, IndentationError, SyntaxError):
#     communication_analysis = None

# Simplified email connection endpoints
# try:
#     from app.api.v1.endpoints import email_simple
# except (ImportError, IndentationError, SyntaxError):
#     email_simple = None

# Anonymous feedback endpoints
# try:
#     from app.api.v1.endpoints import anonymous_feedback
# except (ImportError, IndentationError, SyntaxError):
#     anonymous_feedback = None

# Psychological scoring endpoints
# try:
#     from app.api.v1.endpoints import psychology_scoring
# except (ImportError, IndentationError, SyntaxError):
#     psychology_scoring = None

# Assessment endpoints
# try:
#     from app.api.v1.endpoints import assessments
# except (ImportError, IndentationError, SyntaxError):
#     assessments = None

# Scoring configuration endpoints
# try:
#     from app.api.v1.endpoints import scoring
# except (ImportError, IndentationError, SyntaxError):
#     scoring = None

# Set all to None to prevent imports
organizations = None
email_connections = None
communication_analysis = None
email_simple = None
anonymous_feedback = None
psychology_scoring = None
assessments = None
scoring = None

# Create the main API router
api_router = APIRouter(
    prefix="/api/v1",
    tags=["PsychSync API v1"]
)

# Include authentication routes (no additional prefix - available at /api/v1/token, /api/v1/register)
api_router.include_router(auth.router, tags=["Authentication"])

# Include core endpoints with proper prefixes
api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(templates.router, prefix="/templates", tags=["Assessment Templates"])

# Include optional endpoints
if organizations:
    api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])

# Email analysis endpoints
if email_connections:
    api_router.include_router(email_connections.router, prefix="/email", tags=["Email Connections"])

# Communication analysis endpoints
if communication_analysis:
    api_router.include_router(communication_analysis.router, prefix="/communication", tags=["Communication Analysis"])

# Simplified email connection endpoints
if email_simple:
    api_router.include_router(email_simple.router, prefix="/email-simple", tags=["Simplified Email Connection"])

# Anonymous feedback endpoints
if anonymous_feedback:
    api_router.include_router(anonymous_feedback.router, prefix="/anonymous-feedback", tags=["Anonymous Feedback"])

# Psychological scoring endpoints
if psychology_scoring:
    api_router.include_router(psychology_scoring.router, prefix="/psychology-scoring", tags=["Psychological Scoring"])

# Assessment endpoints
if assessments:
    api_router.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])

# Scoring configuration endpoints
if scoring:
    api_router.include_router(scoring.router, prefix="/scoring", tags=["Scoring Configuration"])

# Admin endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Team optimization endpoints (temporarily disabled due to import issues)
# api_router.include_router(team_optimization.router, tags=["Team Optimization"])

# Temporarily disabled endpoints due to missing models
# api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
# api_router.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
# api_router.include_router(responses.router, prefix="/responses", tags=["Assessment Responses"])
# api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Health check endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# Root health check
@api_router.get("/")
async def api_root():
    """API root endpoint with basic info"""
    return {
        "name": "PsychSync AI API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "redoc": "/redoc"
    }










