#📂 app/api/routes/assessments.py
from fastapi import APIRouter
from app.schemas.assessment import AssessmentCreate, AssessmentOut

router = APIRouter()

@router.post("/", response_model=AssessmentOut)
async def create_assessment(assessment: AssessmentCreate):
    # TODO: Replace with actual DB logic
    return {"id": 1, "title": assessment.title, "score": assessment.score}

@router.get("/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(assessment_id: int):
    # TODO: Replace with actual DB lookup
    return {"id": assessment_id, "title": "Demo Assessment", "score": 100}
