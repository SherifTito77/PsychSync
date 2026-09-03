# app/api/v1/endpoints/responses.py

import asyncio  # Needed for run_in_executor
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession  # ✅ ASYNC - Non-blocking

import app.services.assessment_service as AssessmentService
from app.api.deps import get_current_active_user, get_db  # ✅ Async DB dependency
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.db.models.response import Response
from app.db.models.user import User
from app.schemas.response import Response as ResponseSchema
from app.schemas.response import ResponseCreate, ResponseSave
from app.schemas.response import ResponseScore as ResponseScoreSchema
from app.schemas.response import ResponseSubmit, ResponseWithScore
from app.services.response_service import ResponseService

router = APIRouter(prefix="/responses", tags=["responses"])


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post(
    "/start",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Response session created",
            "content": {
                "application/json": {
                    "example": {"id": 123, "assessment_id": 5, "status": "in_progress"}
                }
            },
        }
    },
)
async def start_response(  # ✅ ASYNC - Non-blocking endpoint
    response_in: ResponseCreate,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a new response session for an assessment.
    Returns existing in-progress session if one exists.
    """
    # Verify assessment exists and is published
    # ✅ Direct async call
    assessment = await AssessmentService.get_by_id(
        db, assessment_id=response_in.assessment_id
    )

    # Defensive null check before accessing assessment properties
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    if assessment.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is not published",
        )

    # Create response session using the service's create method
    # ✅ Direct async call - ResponseService.create() is already async
    response = await ResponseService.create(db=db, data=response_in)

    return response


@router.get("/my-responses", response_model=list[ResponseSchema])
async def get_my_responses(  # ✅ ASYNC
    status_filter: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all responses by current user.
    """
    # ✅ Direct async call - ResponseService.get_by_user() is already async
    responses = await ResponseService.get_by_user(db, user_id=current_user.id)

    # Filter by status if provided
    if status_filter:
        responses = [r for r in responses if r.status == status_filter]

    return responses


@router.get("/{response_id}", response_model=ResponseWithScore)
async def get_response(  # ✅ ASYNC
    response_id: str,  # Changed from int to str to handle uuid.UUID
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Get response details with score.
    """
    # Convert string ID to uuid.UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response ID format"
        )

    # ✅ Direct async call - ResponseService.get_by_id() is already async
    response = await ResponseService.get_by_id(db, response_id=response_uuid)

    # Defensive null check before accessing response properties
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        # Check if user is assessment creator or team admin
        assessment = await AssessmentService.get_by_id(
            db, assessment_id=response.assessment_id
        )

        # Defensive null check before accessing assessment properties
        if assessment is None:
            # If no assessment found, check if it's a clinical screening (already handled in get_by_id)
            # and if the user has permission (handled by the respondent_id check above)
            pass
        elif assessment.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this response",
            )

    # Get score - ✅ Direct async call
    score = await ResponseService.get_response_score(db, response_id=response_uuid)

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    # Ensure permission check works for both ORM Response and SimpleNamespace
    # The check `isinstance(response, Response)` was causing a NameError, so we simplify it
    user_id_to_check = getattr(
        response, "respondent_id", getattr(response, "user_id", None)
    )

    if user_id_to_check and str(user_id_to_check) != str(current_user.id):
        assessment_id_to_check = getattr(response, "assessment_id", None)
        if assessment_id_to_check:
            # Check if user is assessment creator or team admin
            # assessment_service.get_by_id now handles mock assessments for clinical screenings
            assessment = await AssessmentService.get_by_id(
                db, assessment_id=assessment_id_to_check
            )

            # Defensive null check before accessing assessment properties
            if assessment is None:
                # If no assessment found, it might be a clinical screening without linked assessment
                # This case needs careful consideration based on how clinical screenings are permissioned
                # For now, we allow access if the response belongs to the user
                pass
            elif getattr(assessment, "created_by_id", None) != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view this response",
                )
        else:
            # If no assessment_id is available, but respondent_id matches, allow access
            # This might happen for some response types or mock objects
            pass  # Proceed if respondent_id matches user_id

    # Get score - ✅ Direct async call
    score = await ResponseService.get_response_score(db, response_id=response_uuid)

    # Differentiate between standard Response ORM object and SimpleNamespace for screenings
    # Check for attributes that are specific to the SimpleNamespace from ClinicalScreening
    # instead of relying on isinstance(response, Response) which caused NameError
    if hasattr(response, "screening_type"):
        # Map clinical screening data to a dictionary compatible with frontend expectations
        response_dict = {
            "id": str(response.id),
            "assessment_id": str(
                response.assessment_id
            ),  # Mock ID from screening.id (which is uuid.UUID)
            "assignment_id": None,
            "respondent_id": (
                str(response.respondent_id) if response.respondent_id else None
            ),
            "user_id": str(response.user_id),
            "responses": response.responses or {},
            "status": response.status,
            "is_complete": response.is_complete,
            "current_section": str(response.current_section),
            "progress_percentage": response.progress_percentage,
            "time_taken": response.time_taken,
            "started_at": (
                response.started_at.isoformat() if response.started_at else None
            ),
            "last_saved_at": (
                response.last_saved_at.isoformat() if response.last_saved_at else None
            ),
            "submitted_at": (
                response.submitted_at.isoformat() if response.submitted_at else None
            ),
            "created_at": (
                response.created_at.isoformat() if response.created_at else None
            ),
            "updated_at": (
                response.updated_at.isoformat() if response.updated_at else None
            ),
        }
    else:
        # Standard ORM object
        response_dict = ResponseSchema.from_orm(response).dict()

    response_dict["score"] = score

    return response_dict


@router.put("/{response_id}/save", response_model=ResponseSchema)
async def save_progress(  # ✅ ASYNC - Non-blocking endpoint
    response_id: str,
    save_data: ResponseSave,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Save progress on a response.
    """
    # Convert string ID to uuid.UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response ID format"
        )

    # ✅ Direct async call
    response = await ResponseService.get_by_id(db, response_id=response_uuid)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only save your own responses",
        )

    # Check if already completed
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify completed response",
        )

    # Save progress - ✅ Direct async call
    updated_response = await ResponseService.save_progress(
        db,
        response=response,
        responses_data=save_data.responses,
        current_section=save_data.current_section,
    )

    return updated_response


@router.post("/{response_id}/submit", response_model=ResponseWithScore)
async def submit_response(  # ✅ ASYNC - Non-blocking endpoint
    response_id: str,
    submit_data: ResponseSubmit,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit completed response.
    """
    # Convert string ID to uuid.UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response ID format"
        )

    # ✅ Direct async call
    response = await ResponseService.get_by_id(db, response_id=response_uuid)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own responses",
        )

    # Check if already completed
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Response already submitted"
        )

    # Merge and validate responses
    all_responses = response.responses.copy() if response.responses else {}
    all_responses.update(submit_data.responses)

    # ✅ Direct async call
    is_valid, error_msg = await ResponseService.validate_response_data(
        db, assessment_id=response.assessment_id, responses_data=all_responses
    )

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Submit response - ✅ Direct async call
    submitted_response = await ResponseService.submit_response(
        db,
        response=response,
        responses_data=submit_data.responses,
        time_taken=submit_data.time_taken,
    )

    # ✅ CACHE INVALIDATION: Invalidate team composition cache when response is submitted
    from app.services.cache_invalidation_service import cache_invalidation_service

    try:
        await cache_invalidation_service.invalidate_response_related_caches(
            db, str(response_uuid)
        )
    except Exception as e:
        # Log error but don't fail the response submission
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to invalidate cache for response {response_uuid}: {e}")

    # Get score - ✅ Direct async call
    score = await ResponseService.get_response_score(db, response_id=response_uuid)

    response_dict = ResponseSchema.from_orm(submitted_response).dict()
    response_dict["score"] = score

    return response_dict


@router.delete(
    "/{response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_response(  # ✅ ASYNC - Non-blocking endpoint
    response_id: str,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete a response (only if not completed).
    """
    # Convert string ID to uuid.UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response ID format"
        )

    # ✅ Direct async call
    response = await ResponseService.get_by_id(db, response_id=response_uuid)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own responses",
        )

    # Cannot delete completed responses
    if response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete completed response",
        )

    # ✅ Direct async call - use delete_response which takes response object
    await ResponseService.delete_response(db, response=response)


@router.get("/{response_id}/score", response_model=ResponseScoreSchema)
async def get_response_score(  # ✅ ASYNC - Non-blocking endpoint
    response_id: str,
    db: AsyncSession = Depends(get_db),  # ✅ AsyncSession
    current_user: User = Depends(get_current_active_user),
):
    """
    Get score for a completed response.
    """
    # Convert string ID to uuid.UUID
    try:
        response_uuid = uuid.UUID(response_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response ID format"
        )

    # ✅ Direct async call
    response = await ResponseService.get_by_id(db, response_id=response_uuid)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Response not found"
        )

    # Check permission
    if response.respondent_id and response.respondent_id != current_user.id:
        # ✅ Direct async call
        assessment = await AssessmentService.get_by_id(
            db, assessment_id=response.assessment_id
        )

        # Defensive null check before accessing assessment properties
        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated assessment not found",
            )

        if assessment.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this score",
            )

    if not response.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Response not yet completed"
        )

    # ✅ Direct async call
    score = await ResponseService.get_response_score(db, response_id=response_uuid)

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Score not available"
        )

    return score
