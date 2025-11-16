# app/api/v1/endpoints/assessments.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.api.deps import (
    get_current_active_user,
    get_assessment_or_404,
    check_assessment_access,
    check_assessment_edit_permission
)
from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    Assessment as AssessmentSchema,
    AssessmentWithSections,
    AssessmentList,
    SectionCreate,
    QuestionCreate,
    Section as SectionSchema,
    Question as QuestionSchema,
    AssignmentCreate,
    Assignment as AssignmentSchema,
    ResponseSubmit,
    Response as ResponseSchema
)
import app.services.assessment_service as AssessmentService

router = APIRouter()

# ==================== ASSESSMENT CRUD ====================

# FIX 1: Removed the placeholder "create_assessment" function.
# The real one is below.

# FIX 2: Removed the duplicate placeholder "list_assessments" functions.
# The real one is below.

# FIX 3: Changed path from "" to "/".
# This is the main fix for the FastAPIError.
# A POST to the collection's root ("/") creates a new item.
@router.post("/", response_model=AssessmentSchema, status_code=status.HTTP_201_CREATED)
def create_assessment(
    assessment_in: AssessmentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new assessment template.
    """
    assessment = AssessmentService.create(
        db,
        assessment_in=assessment_in,
        creator_id=current_user.id
    )
    return assessment


# FIX 4: Changed path from "" to "/".
# A GET to the collection's root ("/") lists the items.
@router.get("/", response_model=AssessmentList)
def list_assessments(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List assessments accessible to the current user.
    """
    assessments = AssessmentService.get_user_assessments(
        db,
        user_id=current_user.id,
        category=category,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return {
        "assessments": assessments,
        "total": len(assessments)
    }


@router.get("/{assessment_id}", response_model=AssessmentWithSections)
async def get_assessment(
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get assessment details with sections and questions.
    """
    # Calculate question count
    question_count = sum(len(section.questions) for section in assessment.sections)
    
    assessment_dict = AssessmentSchema.from_orm(assessment).dict()
    assessment_dict['sections'] = assessment.sections
    assessment_dict['question_count'] = question_count
    
    return {"assessment_dict" : []}


@router.put("/{assessment_id}", response_model=AssessmentSchema)
def update_assessment(
    assessment_in: AssessmentUpdate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update assessment details.
    Requires creator or team admin permission.
    """
    updated_assessment = AssessmentService.update(
        db,
        assessment=assessment,
        assessment_in=assessment_in
    )
    return updated_assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete assessment.
    Requires creator or team admin permission.
    """
    AssessmentService.delete(db, assessment=assessment)
    return None


@router.post("/{assessment_id}/publish", response_model=AssessmentSchema)
def publish_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Publish assessment (change status to active).
    """
    if assessment.status.value == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is already published"
        )
    
    published_assessment = AssessmentService.publish(db, assessment=assessment)
    return published_assessment


@router.post("/{assessment_id}/archive", response_model=AssessmentSchema)
def archive_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Archive assessment.
    """
    archived_assessment = AssessmentService.archive(db, assessment=assessment)
    return archived_assessment


@router.post("/{assessment_id}/duplicate", response_model=AssessmentSchema, status_code=status.HTTP_201_CREATED)
def duplicate_assessment(
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Duplicate an existing assessment.
    """
    duplicated_assessment = AssessmentService.duplicate(
        db,
        assessment=assessment,
        creator_id=current_user.id
    )
    return duplicated_assessment


# ==================== SECTION MANAGEMENT ====================

@router.post("/{assessment_id}/sections", response_model=SectionSchema, status_code=status.HTTP_201_CREATED)
def add_section(
    assessment_id: int,
    section_in: SectionCreate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add a new section to the assessment.
    """
    section = AssessmentService.add_section(
        db,
        assessment_id=assessment_id,
        section_data=section_in
    )
    return section


@router.delete("/{assessment_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_section(
    assessment_id: int,
    section_id: int,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a section from the assessment.
    """
    AssessmentService.delete_section(db, section_id=section_id)
    return None


# ==================== QUESTION MANAGEMENT ====================

@router.post("/{assessment_id}/sections/{section_id}/questions", response_model=QuestionSchema, status_code=status.HTTP_201_CREATED)
def add_question(
    assessment_id: int,
    section_id: int,
    question_in: QuestionCreate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Add a new question to a section.
    """
    question = AssessmentService.add_question(
        db,
        section_id=section_id,
        question_data=question_in
    )
    return question


@router.delete("/{assessment_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    assessment_id: int,
    section_id: int,
    question_id: int, # Added section_id here for consistency, though it wasn't used
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a question from the assessment.
    """
    AssessmentService.delete_question(db, question_id=question_id)
    return None


# ==================== ASSIGNMENT MANAGEMENT ====================

@router.post("/{assessment_id}/assignments", response_model=AssignmentSchema, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assessment_id: int,
    assignment_in: AssignmentCreate,
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Assign assessment to a team or individual user.
    """
    # Verify assessment is published
    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign published assessments"
        )
    
    assignment = AssessmentService.create_assignment(
        db,
        assessment_id=assessment_id,
        team_id=assignment_in.team_id,
        user_id=assignment_in.assigned_to_user_id,
        assigned_by_id=current_user.id,
        due_date=assignment_in.due_date
    )
    return assignment


@router.get("/assignments/me", response_model=List[AssignmentSchema])
def get_my_assignments(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get assessments assigned to the current user.
    """
    assignments = AssessmentService.get_user_assignments(
        db,
        user_id=current_user.id,
        is_active=is_active
    )
    return assignments


# ==================== RESPONSE MANAGEMENT ====================

@router.post("/{assessment_id}/responses", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
def submit_response(
    assessment_id: int,
    response_in: ResponseSubmit,
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit a response to an assessment.
    """
    # Verify assessment is published
    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only respond to published assessments"
        )
    
    response = AssessmentService.create_response(
        db,
        assessment_id=assessment_id,
        respondent_id=current_user.id if not assessment.allow_anonymous else None,
        assignment_id=response_in.assignment_id,
        responses=response_in.responses,
        is_complete=response_in.is_complete
    )
    return response


@router.get("/{assessment_id}/responses", response_model=List[ResponseSchema])
def get_assessment_responses(
    assessment_id: int,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all responses for an assessment.
    Requires creator or team admin permission.
    """
    responses = AssessmentService.get_assessment_responses(db, assessment_id=assessment_id)
    return responses