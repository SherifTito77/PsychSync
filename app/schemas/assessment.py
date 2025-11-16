# app/schemas/assessment.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, ConfigDict 
from datetime import datetime


# ==================== QUESTION SCHEMAS ====================

class QuestionConfig(BaseModel):
    """Question configuration base"""
    pass


class QuestionBase(BaseModel):
    """Base question schema"""
    question_type: str
    question_text: str
    help_text: Optional[str] = None
    order: int = 0
    is_required: bool = True
    config: Optional[Dict[str, Any]] = None


class QuestionCreate(QuestionBase):
    """Question creation schema"""
    @validator('question_type')
    def validate_question_type(cls, v):
        valid_types = ['multiple_choice', 'rating_scale', 'text', 'yes_no', 'likert']
        if v not in valid_types:
            raise ValueError(f'Question type must be one of: {valid_types}')
        return v


class QuestionUpdate(BaseModel):
    """Question update schema"""
    question_type: Optional[str] = None
    question_text: Optional[str] = None
    help_text: Optional[str] = None
    order: Optional[int] = None
    is_required: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


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
    description: Optional[str] = None
    order: int = 0


class SectionCreate(SectionBase):
    """Section creation schema"""
    questions: Optional[List[QuestionCreate]] = []


class SectionUpdate(BaseModel):
    """Section update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class Section(SectionBase):
    """Section response schema"""
    id: int
    assessment_id: int
    questions: List[Question] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== ASSESSMENT SCHEMAS ====================

class AssessmentBase(BaseModel):
    """Base assessment schema"""
    title: str
    description: Optional[str] = None
    category: str
    instructions: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_public: bool = False
    allow_anonymous: bool = False
    randomize_questions: bool = False
    show_progress: bool = True


class AssessmentCreate(AssessmentBase):
    """Assessment creation schema"""
    team_id: Optional[int] = None
    sections: Optional[List[SectionCreate]] = []
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = [
            'personality', 'cognitive', 'clinical', 'behavioral',
            'developmental', 'neuropsychological', 'other'
        ]
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError('Title must be at least 3 characters')
        if len(v) > 200:
            raise ValueError('Title must not exceed 200 characters')
        return v


class AssessmentUpdate(BaseModel):
    """Assessment update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    instructions: Optional[str] = None
    estimated_duration: Optional[int] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None
    allow_anonymous: Optional[bool] = None
    randomize_questions: Optional[bool] = None
    show_progress: Optional[bool] = None


class Assessment(AssessmentBase):
    """Assessment response schema"""
    id: int
    status: str
    version: int
    created_by_id: int
    team_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentWithSections(Assessment):
    """Assessment with sections and questions"""
    sections: List[Section] = []
    question_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class AssessmentList(BaseModel):
    """Assessment list response"""
    assessments: List[Assessment]
    total: int


# ==================== ASSIGNMENT SCHEMAS ====================

class AssignmentBase(BaseModel):
    """Base assignment schema"""
    assessment_id: int
    team_id: Optional[int] = None
    assigned_to_user_id: Optional[int] = None
    due_date: Optional[datetime] = None


class AssignmentCreate(AssignmentBase):
    """Assignment creation schema"""
    @validator('team_id', 'assigned_to_user_id')
    def validate_assignment_target(cls, v, values):
        # At least one of team_id or assigned_to_user_id must be provided
        if 'team_id' in values and not values.get('team_id') and not v:
            raise ValueError('Either team_id or assigned_to_user_id must be provided')
        return v


class AssignmentUpdate(BaseModel):
    """Assignment update schema"""
    due_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class Assignment(AssignmentBase):
    """Assignment response schema"""
    id: int
    assigned_by_id: int
    is_active: bool
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== RESPONSE SCHEMAS ====================

class ResponseSubmit(BaseModel):
    """Response submission schema"""
    assignment_id: Optional[int] = None
    responses: Dict[str, Any]
    is_complete: bool = False


class ResponseUpdate(BaseModel):
    """Response update schema"""
    responses: Dict[str, Any]
    is_complete: Optional[bool] = None


class Response(BaseModel):
    """Response response schema"""
    id: int
    assessment_id: int
    assignment_id: Optional[int] = None
    respondent_id: Optional[int] = None
    responses: Dict[str, Any]
    is_complete: bool
    time_taken: Optional[int] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

