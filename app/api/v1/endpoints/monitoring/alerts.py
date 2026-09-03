"""
Alert Management Endpoints
TODO(human): Move alert endpoints from monitoring.py
"""

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring-alerts"])
