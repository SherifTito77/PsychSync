# app/api/v1/endpoints/responses.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.db.models.assessment import AssessmentResponse
from app.schemas.response import (
    ResponseCreate,
    ResponseSave,
    ResponseSubmit,
    Response as ResponseSchema,
    ResponseWithScore,
    ResponseScore as ResponseScoreSchema
)
from app.services.response_service import ResponseService
import app.services.assessment_service as AssessmentService

router = APIRouter()


@router.post("/start", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
def start_response(
    response_in: ResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a new response session for an assessment.
    Returns existing in-progress session if one exists.
    """
    # Verify assessment exists and is published
    assessment = AssessmentService.get_by_id(db, assessment_id=response_in.assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is not published"
        )
    
    # Create or get existing session
    response = ResponseService.create_response_session(
        db,
        assessment_id=response_in.assessment_id,
        respondent_id=current_user.id if not assessment.allow_anonymous else None,
        assignment_id=response_in.assignment_id
    )
    
    return response


@router.get("/my-responses", response_model=List[ResponseSchema])
def get_my_responses(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all responses by current user.
    """
    responses = ResponseService.get_user_responses(
        db,
        user_id=current_user.id,
        status=status_filter
    )
    return responses


@router.get("/{response_id}", response_model=ResponseWithScore)
def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get response details with score.
    """
    response = ResponseService.get_response(db, response_id=response_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Check permission
    if response.respondent_id != current_user.id:
        # Check if user is assessment creator or team admin
        assessment = AssessmentService.get_by_id(db, assessment_id=response.assessment_id)
        if assessment.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this response"
            )
    
    # Get score
    score = ResponseService.get_response_score(db, response_id=response_id)
    
    response_dict = ResponseSchema.from_orm(response).dict()
    response_dict['score'] = score
    
    return response_dict


@router.put("/{response_id}/save", response_model=ResponseSchema)
def save_progress(
    response_id: int,
    save_data: ResponseSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save progress on a response.
    """
    response = ResponseService.get_response(db, response_id=response_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only save your own responses"
        )
    
    # Check if already completed
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify completed response"
        )
    
    # Save progress
    updated_response = ResponseService.save_progress(
        db,
        response=response,
        responses_data=save_data.responses,
        current_section=save_data.current_section
    )
    
    return updated_response


@router.post("/{response_id}/submit", response_model=ResponseWithScore)
def submit_response(
    response_id: int,
    submit_data: ResponseSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit completed response.
    """
    response = ResponseService.get_response(db, response_id=response_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own responses"
        )
    
    # Check if already completed
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response already submitted"
        )
    
    # Merge and validate responses
    all_responses = response.responses.copy()
    all_responses.update(submit_data.responses)
    
    is_valid, error_msg = ResponseService.validate_response_data(
        db,
        assessment_id=response.assessment_id,
        responses_data=all_responses
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Submit response
    submitted_response = ResponseService.submit_response(
        db,
        response=response,
        responses_data=submit_data.responses,
        time_taken=submit_data.time_taken
    )
    
    # Get score
    score = ResponseService.get_response_score(db, response_id=response_id)
    
    response_dict = ResponseSchema.from_orm(submitted_response).dict()
    response_dict['score'] = score
    
    return response_dict


@router.delete("/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a response (only if not completed).
    """
    response = ResponseService.get_response(db, response_id=response_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Check permission
    if response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own responses"
        )
    
    # Cannot delete completed responses
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete completed response"
        )
    
    ResponseService.delete_response(db, response=response)
    return None


@router.get("/{response_id}/score", response_model=ResponseScoreSchema)
def get_response_score(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get score for a completed response.
    """
    response = ResponseService.get_response(db, response_id=response_id)
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found"
        )
    
    # Check permission
    if response.respondent_id != current_user.id:
        assessment = AssessmentService.get_by_id(db, assessment_id=response.assessment_id)
        if assessment.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this score"
            )
    
    if not response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response not yet completed"
        )
    
    score = ResponseService.get_response_score(db, response_id=response_id)
    
    if not score:
        # Calculate score if it doesn't exist
        score = ResponseService.calculate_score(db, response=response)
    
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score not available"
        )
    
    return score
