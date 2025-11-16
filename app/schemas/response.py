# app/schemas/response.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator, ConfigDict
from datetime import datetime


class ResponseAnswer(BaseModel):
    """Individual answer schema"""
    question_id: int
    answer: Any  # Can be string, int, list, etc.


class ResponseCreate(BaseModel):
    """Create new response session"""
    assessment_id: int
    assignment_id: Optional[int] = None


class ResponseUpdate(BaseModel):
    """Update response with answers"""
    responses: Dict[str, Any]
    current_section: Optional[int] = None
    is_complete: bool = False


class ResponseSave(BaseModel):
    """Save progress"""
    responses: Dict[str, Any]
    current_section: Optional[int] = None


class ResponseSubmit(BaseModel):
    """Submit completed response"""
    responses: Dict[str, Any]
    time_taken: Optional[int] = None  # in seconds


class Response(BaseModel):
    """Response response schema"""
    id: int
    assessment_id: int
    assignment_id: Optional[int] = None
    respondent_id: Optional[int] = None
    responses: Dict[str, Any]
    status: str
    is_complete: bool
    current_section: int
    progress_percentage: float
    time_taken: Optional[int] = None
    started_at: datetime
    last_saved_at: datetime
    submitted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ResponseWithAssessment(Response):
    """Response with assessment details"""
    assessment_title: str
    assessment_category: str


class ResponseScore(BaseModel):
    """Response score schema"""
    id: int
    response_id: int
    total_score: Optional[float] = None
    max_possible_score: Optional[float] = None
    percentage_score: Optional[float] = None
    subscale_scores: Optional[Dict[str, float]] = None
    interpretation: Optional[str] = None
    calculated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ResponseWithScore(Response):
    """Response with calculated score"""
    score: Optional[ResponseScore] = None