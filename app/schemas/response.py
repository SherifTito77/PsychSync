# app/schemas/response.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResponseAnswer(BaseModel):
    """Individual answer schema"""

    question_id: int
    answer: Any  # Can be string, int, list, etc.


class ResponseCreate(BaseModel):
    """Create new response session"""

    assessment_id: int
    assignment_id: int | None = None


class ResponseUpdate(BaseModel):
    """Update response with answers"""

    responses: dict[str, Any]
    current_section: int | None = None
    is_complete: bool = False


class ResponseSave(BaseModel):
    """Save progress"""

    responses: dict[str, Any]
    current_section: int | None = None


class ResponseSubmit(BaseModel):
    """Submit completed response"""

    responses: dict[str, Any]
    time_taken: int | None = None  # in seconds

    model_config = ConfigDict(
        json_schema_extra={
            "example": {'answers': [{'question_id': 1, 'value': 4}, {'question_id': 2, 'value': 5}, {'question_id': 3, 'value': 3}]}
        }
    )

class Response(BaseModel):
    """Response response schema"""

    id: int
    assessment_id: int
    assignment_id: int | None = None
    respondent_id: int | None = None
    responses: dict[str, Any]
    status: str
    is_complete: bool
    current_section: int
    progress_percentage: float
    time_taken: int | None = None
    started_at: datetime
    last_saved_at: datetime
    submitted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ResponseWithAssessment(Response):
    """Response with assessment details"""

    assessment_title: str
    assessment_category: str


class ResponseScore(BaseModel):
    """Response score schema"""

    id: int
    response_id: int
    total_score: float | None = None
    max_possible_score: float | None = None
    percentage_score: float | None = None
    subscale_scores: dict[str, float] | None = None
    interpretation: str | None = None
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResponseWithScore(Response):
    """Response with calculated score"""

    score: ResponseScore | None = None
