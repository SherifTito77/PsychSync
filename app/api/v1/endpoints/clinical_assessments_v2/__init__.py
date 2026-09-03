"""
Clinical Assessments Module
Split from clinical_assessments.py for better maintainability

This module contains clinical mental health & wellness endpoints split into focused sub-modules:
- consent: Clinical consent management
- screening: Mental health screening (PHQ-9, GAD-7, ASRS)
- wellness: Wellness assessments and monitoring
- crisis: Crisis intervention and safety planning
- trends: Mental health trend analysis
- planning: Wellness plan generation and management
- resources: Clinical resources and information
"""

from fastapi import APIRouter

from .consent import router as consent_router
from .crisis import router as crisis_router
from .planning import router as planning_router
from .resources import router as resources_router
from .screening import router as screening_router
from .trends import router as trends_router
from .wellness import router as wellness_router

# Create main router - sub-routers will inherit their own prefixes
router = APIRouter(tags=["clinical"])

# Include all sub-routers without adding prefix (they have their own)
router.include_router(consent_router)
router.include_router(screening_router)
router.include_router(wellness_router)
router.include_router(crisis_router)
router.include_router(trends_router)
router.include_router(planning_router)
router.include_router(resources_router)

# Export for use in main API
__all__ = ["router"]
