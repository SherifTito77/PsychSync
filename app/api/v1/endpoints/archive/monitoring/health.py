"""
Health Monitoring Endpoints
TODO(human): Move health endpoints from monitoring.py
"""

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring-health"])
