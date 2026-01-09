# app/schemas/assessment.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, validator

# ==================== QUESTION SCHEMAS ====================


class QuestionConfig(BaseModel):
    """Question configuration base"""


class QuestionBase(BaseModel):
    """Base question schema"""

    question_type: str
    question_text: str
    help_text: str | None = None
    order: int = 0
    is_required: bool = True
    config: dict[str, Any] | None = None


class QuestionCreate(QuestionBase):
    """Question creation schema"""

    @validator("question_type")
    def validate_question_type(cls, v):
        valid_types = ["multiple_choice", "rating_scale", "text", "yes_no", "likert"]
        if v not in valid_types:
            raise ValueError(f"Question type must be one of: {valid_types}")
        return v


class QuestionUpdate(BaseModel):
    """Question update schema"""

    question_type: str | None = None
    question_text: str | None = None
    help_text: str | None = None
    order: int | None = None
    is_required: bool | None = None
    config: dict[str, Any] | None = None


class Question(QuestionBase):
    """Question response schema"""

    id: int
    section_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== SECTION SCHEMAS ====================


class SectionBase(BaseModel):
    """Base section schema"""

    title: str
    description: str | None = None
    order: int = 0


class SectionCreate(SectionBase):
    """Section creation schema"""

    questions: list[QuestionCreate] | None = []


class SectionUpdate(BaseModel):
    """Section update schema"""

    title: str | None = None
    description: str | None = None
    order: int | None = None


class Section(SectionBase):
    """Section response schema"""

    id: int
    assessment_id: int
    questions: list[Question] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== ASSESSMENT SCHEMAS ====================


class AssessmentBase(BaseModel):
    """Base assessment schema"""

    title: str
    description: str | None = None
    category: str
    instructions: str | None = None
    estimated_duration: int | None = None
    is_public: bool = False
    allow_anonymous: bool = False
    randomize_questions: bool = False
    show_progress: bool = True


class AssessmentCreate(AssessmentBase):
    """Assessment creation schema"""

    team_id: int | None = None
    sections: list[SectionCreate] | None = []

    @validator("category")
    def validate_category(cls, v):
        valid_categories = [
            "personality",
            "cognitive",
            "clinical",
            "behavioral",
            "developmental",
            "neuropsychological",
            "other",
        ]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {valid_categories}")
        return v

    @validator("title")
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        if len(v) > 200:
            raise ValueError("Title must not exceed 200 characters")
        return v


class AssessmentUpdate(BaseModel):
    """Assessment update schema"""

    title: str | None = None
    description: str | None = None
    category: str | None = None
    instructions: str | None = None
    estimated_duration: int | None = None
    status: str | None = None
    is_public: bool | None = None
    allow_anonymous: bool | None = None
    randomize_questions: bool | None = None
    show_progress: bool | None = None


class Assessment(AssessmentBase):
    """Assessment response schema"""

    id: int
    status: str
    version: int
    created_by_id: int
    team_id: int | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AssessmentWithSections(Assessment):
    """Assessment with sections and questions"""

    sections: list[Section] = []
    question_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AssessmentList(BaseModel):
    """Assessment list response"""

    assessments: list[Assessment]
    total: int


# ==================== ASSIGNMENT SCHEMAS ====================


class AssignmentBase(BaseModel):
    """Base assignment schema"""

    assessment_id: int
    team_id: int | None = None
    assigned_to_user_id: int | None = None
    due_date: datetime | None = None


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema"""

    @validator("team_id", "assigned_to_user_id")
    def validate_assignment_target(cls, v, values):
        # At least one of team_id or assigned_to_user_id must be provided
        if "team_id" in values and not values.get("team_id") and not v:
            raise ValueError("Either team_id or assigned_to_user_id must be provided")
        return v


class AssignmentUpdate(BaseModel):
    """Assignment update schema"""

    due_date: datetime | None = None
    is_active: bool | None = None


class Assignment(AssignmentBase):
    """Assignment response schema"""

    id: int
    assigned_by_id: int
    is_active: bool
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ==================== RESPONSE SCHEMAS ====================


class ResponseSubmit(BaseModel):
    """Response submission schema"""

    assignment_id: int | None = None
    responses: dict[str, Any]
    is_complete: bool = False


class ResponseUpdate(BaseModel):
    """Response update schema"""

    responses: dict[str, Any]
    is_complete: bool | None = None


class Response(BaseModel):
    """Response response schema"""

    id: int
    assessment_id: int
    assignment_id: int | None = None
    respondent_id: int | None = None
    responses: dict[str, Any]
    is_complete: bool
    time_taken: int | None = None
    started_at: datetime
    submitted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
