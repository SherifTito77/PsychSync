"""
Assessment Assignment and Response Endpoints
Handles assessment assignments to users and response submissions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_db
from app.db.models.assessment import Assessment
from app.db.models.user import User
from app.schemas.assessment import AssignmentCreate, ResponseSubmit

# Import schemas and helper from crud module
from .crud import (
    AssessmentService,
    check_assessment_access,
    check_assessment_edit_permission,
)

router = APIRouter(prefix="/assessments", tags=["assessment-responses"])


# ==================== ASSIGNMENT MANAGEMENT ====================


@router.post("/{assessment_id}/assignments", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assessment_id: int,
    assignment_in: AssignmentCreate,
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Assign assessment to a team or individual user.
    """
    # Verify assessment is published
    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign published assessments",
        )

    assignment = AssessmentService.create_assignment(
        db,
        assessment_id=assessment_id,
        team_id=assignment_in.team_id,
        user_id=assignment_in.assigned_to_user_id,
        assigned_by_id=current_user.id,
        due_date=assignment_in.due_date,
    )
    return assignment


@router.get("/assignments/me")
async def get_my_assignments(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get assessments assigned to the current user.
    """
    assignments = AssessmentService.get_user_assignments(
        db, user_id=current_user.id, is_active=is_active
    )
    return assignments


# ==================== RESPONSE MANAGEMENT ====================


@router.post("/{assessment_id}/responses", status_code=status.HTTP_201_CREATED)
async def submit_response(
    assessment_id: int,
    response_in: ResponseSubmit,
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a response to an assessment.
    """
    # Verify assessment is published
    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only respond to published assessments",
        )

    response = AssessmentService.create_response(
        db,
        assessment_id=assessment_id,
        respondent_id=current_user.id if not assessment.allow_anonymous else None,
        assignment_id=response_in.assignment_id,
        responses=response_in.responses,
        is_complete=response_in.is_complete,
    )
    return response


@router.get("/{assessment_id}/responses")
async def get_assessment_responses(
    assessment_id: int,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all responses for an assessment.
    Requires creator or team admin permission.
    """
    responses = AssessmentService.get_assessment_responses(
        db, assessment_id=assessment_id
    )
    return responses
