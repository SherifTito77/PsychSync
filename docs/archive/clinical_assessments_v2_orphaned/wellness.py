"""
Wellness Assessment Endpoints
TODO(human): Move wellness endpoints from clinical_assessments.py

Endpoints to move:
- POST /wellness/assessment (lines 283-381)
- GET /wellness/questions (lines 846-865)
- POST /wellness/submit (lines 866-904)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/clinical", tags=["clinical-wellness"])

# TODO(human): Move wellness assessment endpoints
