"""
Monitoring Module
Split from monitoring.py for better maintainability
"""

from fastapi import APIRouter

from .alerts import router as alerts_router
from .business import router as business_router
from .deployments import router as deployments_router
from .health import router as health_router
from .integration import router as integration_router

router = APIRouter(tags=["monitoring"])
router.include_router(health_router)
router.include_router(alerts_router)
router.include_router(deployments_router)
router.include_router(business_router)
router.include_router(integration_router)

__all__ = ["router"]
