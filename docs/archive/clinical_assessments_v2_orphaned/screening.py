"""
Mental Health Screening Endpoints
TODO(human): Move screening endpoints from clinical_assessments.py

Endpoints to move:
- POST /screening/mental-health (lines 163-282)
- GET /screening/tools (lines 668-779)
- GET /screening/questions/{assessment_type} (lines 780-803)
- POST /screening/submit (lines 804-845)
"""

from fastapi import APIRouter

router = APIRouter(prefix="", tags=["clinical-screening"])

# TODO(human): Move screening endpoints
