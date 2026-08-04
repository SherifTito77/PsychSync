"""
Deployment Monitoring Endpoints
TODO(human): Move deployment endpoints from monitoring.py
"""

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring-deployments"])
