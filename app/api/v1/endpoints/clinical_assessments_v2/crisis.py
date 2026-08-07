"""
Crisis Intervention Endpoints
TODO(human): Move crisis endpoints from clinical_assessments.py

Endpoints to move:
- POST /crisis/alert (lines 382-471)
- POST /crisis/assessment (lines 1416-1489)
- POST /crisis/create-safety-plan (lines 1490-1546)
- GET /crisis/safety-plan (lines 1547-1573)
- GET /crisis/resources (lines 1574-1693)
- POST /crisis/check-in (lines 1694-1743)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/clinical", tags=["clinical-crisis"])

# TODO(human): Move crisis intervention endpoints
