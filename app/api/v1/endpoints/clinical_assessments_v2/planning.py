"""
Wellness Planning Endpoints
TODO(human): Move planning endpoints from clinical_assessments.py

Endpoints to move:
- POST /wellness/plan (lines 537-602)
- GET /wellness/plan/existing (lines 1035-1057)
- POST /wellness/plan/generate (lines 1058-1100)
- PUT /wellness/plan/{plan_id}/update (lines 1101-1132)
- GET /wellness/plan/templates (lines 1133-1220)
- GET /wellness/plan/goal-suggestions (lines 1221-1415)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/clinical", tags=["clinical-planning"])

# TODO(human): Move wellness planning endpoints
