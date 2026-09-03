# app/schemas/assessment_v2.py
"""
Assessment Schemas - Refactored Version

Standardized assessment schemas using base classes.
Demonstrates consistent patterns and validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, EntitySchema, ValidationRules
from app.schemas.common import AssessmentStatus

# ============================================================================
# QUESTION SCHEMAS
# ============================================================================


class QuestionConfig(BaseSchema):
    """
    Configuration for different question types.
    """

    options: list[str] | None = Field(
        default=None, description="Available options for multiple choice questions"
    )
    min_value: int | None = Field(
        default=None, description="Minimum value for rating scales"
    )
    max_value: int | None = Field(
        default=None, description="Maximum value for rating scales"
    )
    allow_multiple: bool = Field(default=False, description="Allow multiple selections")


class QuestionBase(BaseSchema):
    """
    Base question schema with common fields.
    """

    question_type: str = Field(
        description="Type of question (multiple_choice, rating_scale, text, etc.)"
    )
    question_text: str = Field(
        ..., min_length=1, max_length=2000, description="Question text"
    )
    help_text: str | None = Field(
        default=None, max_length=1000, description="Help text for the question"
    )
    order: int = Field(default=0, ge=0, description="Display order")
    is_required: bool = Field(
        default=True, description="Whether the question is required"
    )
    config: QuestionConfig | None = Field(
        default=None, description="Question-specific configuration"
    )


class QuestionCreate(QuestionBase):
    """
    Schema for creating a question.
    """

    @field_validator("question_type")
    @classmethod
    def validate_question_type(cls, v: str) -> str:
        """Validate question type is supported"""
        valid_types = {
            "multiple_choice",
            "rating_scale",
            "text",
            "yes_no",
            "likert",
            "dropdown",
            "checkbox",
            "date",
            "number",
        }
        if v not in valid_types:
            raise ValueError(
                f"Question type must be one of: {', '.join(sorted(valid_types))}"
            )
        return v


class QuestionUpdate(BaseSchema):
    """
    Schema for updating a question.

    All fields are optional.
    """

    question_type: str | None = Field(default=None, description="Question type")
    question_text: str | None = Field(default=None, min_length=1, max_length=2000)
    help_text: str | None = Field(default=None, max_length=1000)
    order: int | None = Field(default=None, ge=0)
    is_required: bool | None = Field(default=None)
    config: QuestionConfig | None = Field(default=None)


class QuestionResponse(EntitySchema, QuestionBase):
    """
    Question response schema with ID and timestamps.
    """

    section_id: UUID = Field(description="ID of the section this question belongs to")


# ============================================================================
# SECTION SCHEMAS
# ============================================================================


class SectionBase(BaseSchema):
    """
    Base section schema.
    """

    title: str = Field(..., **ValidationRules.name())
    description: str | None = Field(
        default=None, max_length=5000, description="Description"
    )
    order: int = Field(default=0, ge=0, description="Display order within assessment")
    time_limit: int | None = Field(
        default=None, ge=0, description="Time limit in seconds (null for no limit)"
    )


class SectionCreate(SectionBase):
    """
    Schema for creating a section with questions.
    """

    questions: list[QuestionCreate] = Field(
        default_factory=list, description="Questions in this section"
    )


class SectionUpdate(BaseSchema):
    """
    Schema for updating a section.
    """

    title: str | None = Field(min_length=1, max_length=255, description="Name")
    description: str | None = Field(
        default=None, max_length=5000, description="Description"
    )
    order: int | None = Field(default=None, ge=0)
    time_limit: int | None = Field(default=None, ge=0)


class SectionResponse(EntitySchema, SectionBase):
    """
    Section response schema.
    """

    assessment_id: UUID = Field(
        description="ID of the assessment this section belongs to"
    )
    question_count: int = Field(default=0, description="Number of questions in section")


class SectionWithQuestions(SectionResponse):
    """
    Section with embedded questions.
    """

    questions: list[QuestionResponse] = Field(
        default_factory=list, description="Questions in this section"
    )


# ============================================================================
# ASSESSMENT SCHEMAS
# ============================================================================


class AssessmentBase(BaseSchema):
    """
    Base assessment schema with common fields.
    """

    title: str = Field(
        ..., min_length=3, max_length=200, description="Assessment title"
    )
    description: str | None = Field(
        default=None, max_length=5000, description="Description"
    )
    category: str = Field(
        ..., description="Assessment category (personality, cognitive, clinical, etc.)"
    )
    instructions: str | None = Field(
        default=None,
        max_length=5000,
        description="Instructions for taking the assessment",
    )
    estimated_duration: int | None = Field(
        default=None, ge=0, description="Estimated duration in minutes"
    )
    is_public: bool = Field(
        default=False, description="Whether assessment is publicly accessible"
    )
    allow_anonymous: bool = Field(
        default=False, description="Whether anonymous responses are allowed"
    )
    randomize_questions: bool = Field(
        default=False, description="Whether to randomize question order"
    )
    show_progress: bool = Field(
        default=True, description="Whether to show progress to respondents"
    )


class AssessmentCreate(AssessmentBase):
    """
    Schema for creating an assessment.
    """

    team_id: UUID | None = Field(default=None, description="Team ID (if team-specific)")
    sections: list[SectionCreate] = Field(
        default_factory=list, description="Assessment sections"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate assessment category"""
        valid_categories = {
            "personality",
            "cognitive",
            "clinical",
            "behavioral",
            "developmental",
            "neuropsychological",
            "educational",
            "career",
            "other",
        }
        if v not in valid_categories:
            raise ValueError(
                f"Category must be one of: {', '.join(sorted(valid_categories))}"
            )
        return v


class AssessmentUpdate(BaseSchema):
    """
    Schema for updating an assessment.

    All fields are optional.
    """

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None)
    instructions: str | None = Field(default=None, max_length=5000)
    estimated_duration: int | None = Field(default=None, ge=0)
    status: AssessmentStatus | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    allow_anonymous: bool | None = Field(default=None)
    randomize_questions: bool | None = Field(default=None)
    show_progress: bool | None = Field(default=None)


class AssessmentResponse(EntitySchema, AssessmentBase):
    """
    Assessment response schema.
    """

    status: AssessmentStatus = Field(description="Assessment status")
    version: int = Field(default=1, ge=1, description="Assessment version")
    created_by_id: UUID = Field(description="ID of user who created assessment")
    team_id: UUID | None = Field(default=None, description="Team ID (if team-specific)")
    published_at: datetime | None = Field(
        default=None, description="Publication timestamp"
    )
    question_count: int = Field(default=0, description="Total number of questions")


class AssessmentWithSections(AssessmentResponse):
    """
    Assessment with embedded sections.
    """

    sections: list[SectionWithQuestions] = Field(
        default_factory=list, description="Assessment sections with questions"
    )


class AssessmentListResponse(BaseSchema):
    """
    Paginated list of assessments.
    """

    assessments: list[AssessmentResponse]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# ASSIGNMENT SCHEMAS
# ============================================================================


class AssignmentBase(BaseSchema):
    """
    Base assignment schema.
    """

    assessment_id: UUID = Field(description="ID of assessment to assign")
    team_id: UUID | None = Field(default=None, description="Assign to entire team")
    assigned_to_user_id: UUID | None = Field(
        default=None, description="Assign to specific user"
    )
    due_date: datetime | None = Field(default=None, description="Assignment due date")
    instructions: str | None = Field(
        default=None, max_length=5000, description="Assignment instructions"
    )


class AssignmentCreate(AssignmentBase):
    """
    Schema for creating an assignment.

    Must specify either team_id or assigned_to_user_id (not both).
    """

    @field_validator("team_id", "assigned_to_user_id")
    @classmethod
    def validate_assignment_target(cls, v: UUID | None, info) -> UUID | None:
        """Ensure exactly one target is specified"""
        if v is not None:
            if "team_id" in info.data and "assigned_to_user_id" in info.data:
                team_id = info.data.get("team_id")
                user_id = info.data.get("assigned_to_user_id")
                if (team_id is not None and user_id is not None) or (
                    team_id is None and user_id is None
                ):
                    raise ValueError(
                        "Must specify exactly one of team_id or assigned_to_user_id"
                    )
        return v


class AssignmentUpdate(BaseSchema):
    """
    Schema for updating an assignment.
    """

    due_date: datetime | None = Field(default=None)
    is_active: bool | None = Field(
        default=None, description="Whether assignment is active"
    )


class AssignmentResponse(EntitySchema, AssignmentBase):
    """
    Assignment response schema.
    """

    assigned_by_id: UUID = Field(description="ID of user who created assignment")
    is_active: bool = Field(description="Whether assignment is currently active")
    completed_at: datetime | None = Field(
        default=None, description="Completion timestamp"
    )


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================


class ResponseSubmit(BaseSchema):
    """
    Schema for submitting assessment responses.
    """

    assignment_id: UUID | None = Field(
        default=None, description="Assignment ID (if assigned)"
    )
    responses: dict[str, Any] = Field(description="Response data (question_id: answer)")
    is_complete: bool = Field(default=False, description="Whether response is complete")
    time_taken: int | None = Field(
        default=None, ge=0, description="Time taken in seconds"
    )


class ResponseUpdate(BaseSchema):
    """
    Schema for updating responses (saving progress).
    """

    responses: dict[str, Any] = Field(description="Updated response data")
    current_section_id: UUID | None = Field(
        default=None, description="Current section ID"
    )
    is_complete: bool = Field(default=False, description="Mark as complete")


class ResponseResponse(EntitySchema):
    """
    Assessment response schema.
    """

    assessment_id: UUID = Field(description="ID of assessment")
    assignment_id: UUID | None = Field(
        default=None, description="Assignment ID (if assigned)"
    )
    respondent_id: UUID | None = Field(default=None, description="ID of respondent")
    responses: dict[str, Any] = Field(description="Response data")
    status: str = Field(description="Response status")
    is_complete: bool = Field(description="Whether response is complete")
    current_section_id: UUID | None = Field(
        default=None, description="Current section ID"
    )
    progress_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage"
    )
    time_taken: int | None = Field(
        default=None, ge=0, description="Time taken in seconds"
    )
    started_at: datetime = Field(description="Start timestamp")
    submitted_at: datetime | None = Field(
        default=None, description="Submission timestamp"
    )


class ResponseWithAssessment(ResponseResponse):
    """
    Response with embedded assessment details.
    """

    assessment_title: str = Field(description="Assessment title")
    assessment_category: str = Field(description="Assessment category")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Questions
    "QuestionConfig",
    "QuestionBase",
    "QuestionCreate",
    "QuestionUpdate",
    "QuestionResponse",
    # Sections
    "SectionBase",
    "SectionCreate",
    "SectionUpdate",
    "SectionResponse",
    "SectionWithQuestions",
    # Assessments
    "AssessmentBase",
    "AssessmentCreate",
    "AssessmentUpdate",
    "AssessmentResponse",
    "AssessmentWithSections",
    "AssessmentListResponse",
    # Assignments
    "AssignmentBase",
    "AssignmentCreate",
    "AssignmentUpdate",
    "AssignmentResponse",
    # Responses
    "ResponseSubmit",
    "ResponseUpdate",
    "ResponseResponse",
    "ResponseWithAssessment",
]
