"""
Assessments Module
Split from assessments.py for better maintainability

This module contains assessment-related endpoints split into focused sub-modules:
- crud: Assessment CRUD operations
- questions: Framework-specific assessment questions
- responses: Assignments and response management
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .questions import router as questions_router
from .responses import router as responses_router

# Create main router - sub-routers will inherit their own prefixes
router = APIRouter(tags=["assessments"])

# Include all sub-routers without adding prefix (they have their own)
router.include_router(crud_router)
router.include_router(questions_router)
router.include_router(responses_router)

# Export for use in main API
__all__ = ["router"]
