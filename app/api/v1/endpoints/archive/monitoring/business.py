"""
Business Metrics Endpoints
TODO(human): Move business metrics from monitoring.py
"""

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring-business"])
