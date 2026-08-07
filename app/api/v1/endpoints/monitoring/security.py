"""
Security Monitoring Endpoints
TODO(human): Move security monitoring from monitoring.py
"""

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring-security"])
