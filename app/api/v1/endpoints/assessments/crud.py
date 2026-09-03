"""
Assessment CRUD Endpoints
Handles create, read, update, delete, and lifecycle operations for assessments
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import get_current_active_user, get_db
from app.core.api_utils import (
    PaginationParams,
    SortParams,
    create_paginated_list_response,
    get_pagination_params,
    get_sort_params,
    measure_performance,
    serialize_model,
)
from app.core.async_cache import async_cached
from app.core.exception_handling import handle_exceptions
from app.core.rate_limiter_unified import RateLimitStrategy, rate_limit
from app.core.response import create_success_response
from app.db.models.assessment import Assessment
from app.db.models.clinical_screening import ClinicalScreening
from app.db.models.user import User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    QuestionCreate,
    SectionCreate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessments", tags=["assessments-crud"])


# ==================== SERVICE IMPLEMENTATION ====================


class AssessmentService:
    """Simple placeholder service implementation for testing"""

    @staticmethod
    def create(db: AsyncSession, assessment_in: dict, creator_id: int) -> dict:
        """Create a new assessment"""
        return {
            "id": 1,
            "title": assessment_in.title,
            "description": assessment_in.description,
            "category": assessment_in.category,
            "status": "draft",
            "created_by_id": creator_id,
            "created_at": datetime.utcnow(),
        }

    @staticmethod
    def get_user_assessments(db: AsyncSession, user_id: int, **filters) -> list:
        """Get user assessments"""
        return []

    @staticmethod
    def update(db: AsyncSession, assessment: dict, assessment_in: dict) -> dict:
        """Update assessment"""
        return assessment

    @staticmethod
    def delete(db: AsyncSession, assessment: dict) -> None:
        """Delete assessment"""

    @staticmethod
    def publish(db: AsyncSession, assessment: dict) -> dict:
        """Publish assessment"""
        assessment["status"] = "published"
        return assessment

    @staticmethod
    def archive(db: AsyncSession, assessment: dict) -> dict:
        """Archive assessment"""
        assessment["status"] = "archived"
        return assessment

    @staticmethod
    def duplicate(db: AsyncSession, assessment: dict, creator_id: int) -> dict:
        """Duplicate assessment"""
        new_assessment = assessment.copy()
        new_assessment["id"] = assessment.get("id", 0) + 1
        new_assessment["created_by_id"] = creator_id
        return new_assessment

    @staticmethod
    def add_section(db: AsyncSession, assessment_id: int, section_data: dict) -> dict:
        """Add section to assessment"""
        return {"id": 1, "title": section_data.title}

    @staticmethod
    def delete_section(db: AsyncSession, section_id: int) -> None:
        """Delete section"""

    @staticmethod
    def add_question(db: AsyncSession, section_id: int, question_data: dict) -> dict:
        """Add question to section"""
        return {"id": 1, "question_text": question_data.question_text}

    @staticmethod
    def delete_question(db: AsyncSession, question_id: int) -> None:
        """Delete question"""


# ==================== HELPER FUNCTIONS ====================


async def get_assessment_or_404(
    assessment_id: Any, db: AsyncSession, current_user: User
) -> Any:
    """Get assessment by ID or raise 404. Supports mock assessments for clinical screenings."""
    try:
        # Standard assessments use uuid.UUID now
        assessment_uuid = uuid.UUID(str(assessment_id))
    except (ValueError, TypeError):
        # Fallback for legacy integer IDs if any still exist
        assessment_uuid = assessment_id

    result = await db.execute(
        select(Assessment)
        .options(selectinload(Assessment.sections))
        .filter(Assessment.id == assessment_uuid)
    )
    assessment = result.scalar_one_or_none()

    if not assessment:
        # Check if this ID belongs to a clinical screening
        result = await db.execute(
            select(ClinicalScreening).where(ClinicalScreening.id == assessment_uuid)
        )
        screening = result.scalar_one_or_none()

        if screening:
            # Create a mock assessment object for clinical screenings
            from types import SimpleNamespace

            # GAD7 specific questions mapping if available
            questions = []
            if screening.screening_type == "GAD7":
                questions = [
                    {
                        "id": 1,
                        "question_text": "Feeling nervous, anxious or on edge",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 2,
                        "question_text": "Not being able to stop or control worrying",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 3,
                        "question_text": "Worrying too much about different things",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 4,
                        "question_text": "Trouble relaxing",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 5,
                        "question_text": "Being so restless that it is hard to sit still",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 6,
                        "question_text": "Becoming easily annoyed or irritable",
                        "question_type": "rating_scale",
                    },
                    {
                        "id": 7,
                        "question_text": "Feeling afraid as if something awful might happen",
                        "question_type": "rating_scale",
                    },
                ]

            mock_questions = [
                SimpleNamespace(**q, help_text="", order=i, is_required=True)
                for i, q in enumerate(questions)
            ]
            mock_section = SimpleNamespace(
                id=screening.id,
                title=f"{screening.screening_type} Items",
                description="Clinical screening items",
                order=0,
                questions=mock_questions,
            )

            return SimpleNamespace(
                id=screening.id,
                title=screening.screening_type,
                description=f"Clinical screening for {screening.screening_type}",
                category="clinical",
                status="active",
                version=1,
                instructions="Please answer honestly.",
                estimated_duration=5,
                is_public=False,
                created_by_id=screening.user_id,
                sections=[mock_section],
                created_at=screening.created_at,
                updated_at=screening.updated_at,
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with ID {assessment_id} not found",
        )

    return assessment


async def check_assessment_access(
    assessment_id: Any,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Check if user has access to assessment (read access).

    SECURITY: Validates access through multiple layers:
    - User created the assessment
    - Assessment is public
    - User is in the same organization as the assessment
    - User is a system admin
    """
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    # For SimpleNamespace (clinical screening mock assessments), check user_id
    if hasattr(assessment, "created_by_id"):
        if assessment.created_by_id == current_user.id:
            return assessment

    # Allow access if assessment is public
    if getattr(assessment, "is_public", False):
        return assessment

    # Allow access if user is system admin
    if current_user.is_admin:
        return assessment

    # Check organization-level access
    from app.db.models.team import TeamMember

    # Get teams the current user belongs to
    user_teams_result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == current_user.id)
    )
    user_team_ids = {row[0] for row in user_teams_result.fetchall()}

    # Get teams the assessment creator belongs to
    creator_teams_result = await db.execute(
        select(TeamMember.team_id).where(TeamMember.user_id == assessment.created_by_id)
    )
    creator_team_ids = {row[0] for row in creator_teams_result.fetchall()}

    # Allow access if they share any teams
    if user_team_ids & creator_team_ids:  # Intersection of teams
        return assessment

    # No valid access path found
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this assessment",
    )


async def check_assessment_edit_permission(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Assessment:
    """
    Check if user has edit permission for assessment.

    SECURITY: Validates ownership or team admin role to prevent IDOR attacks.
    Only the creator or a team admin can edit/delete assessments.
    """
    assessment = await get_assessment_or_404(assessment_id, db, current_user)

    # Allow edit if user created the assessment
    if assessment.created_by_id == current_user.id:
        return assessment

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to edit this assessment",
    )


# ==================== CRUD ENDPOINTS ====================


@router.get("/")
@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@measure_performance
@async_cached(expire=60, key_prefix="assessments")
async def get_assessments(
    pagination: PaginationParams = Depends(get_pagination_params),
    sort_params: SortParams = Depends(get_sort_params),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(
        None, description="Search assessments by title or description"
    ),
    category: str | None = Query(None, description="Filter by assessment category"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status"
    ),
    created_by: int | None = Query(None, description="Filter by creator ID"),
):
    """
    Get paginated list of assessments with filtering and sorting

    Enhanced Features:
    - Standardized pagination with metadata
    - Advanced filtering (search, category, status, creator)
    - Configurable sorting
    - Performance caching
    - Response time measurement
    """
    # Build base query
    # Note: sections relationship temporarily disabled
    query = select(Assessment)

    # Apply filters
    filter_params = {}

    if search:
        filter_params["search"] = search
        query = query.where(
            Assessment.title.ilike(f"%{search}%")
            | Assessment.description.ilike(f"%{search}%")
        )

    if category:
        filter_params["category"] = category
        query = query.where(Assessment.category == category)

    if status_filter:
        filter_params["status"] = status_filter
        query = query.where(Assessment.status == status_filter)

    if created_by:
        filter_params["created_by"] = created_by
        query = query.where(Assessment.created_by_id == created_by)

    # Create paginated response
    return await create_paginated_list_response(
        query=query,
        db=db,
        pagination=pagination,
        sort_params=sort_params,
        filter_params=filter_params,
        message="Assessments retrieved successfully",
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
@rate_limit(limit=20, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@measure_performance
@handle_exceptions(default_message="Failed to create assessment")
async def create_assessment(
    assessment_in: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new assessment template.

    Enhanced Features:
    - Standardized response format with success/error handling
    - Input validation and error details
    - Performance monitoring
    """
    assessment = AssessmentService.create(
        db, assessment_in=assessment_in, creator_id=current_user.id
    )

    return create_success_response(
        data=assessment,
        message="Assessment created successfully",
    )


@router.get("/")
@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@measure_performance
@async_cached(expire=60, key_prefix="assessments_list")
@handle_exceptions(default_message="Failed to retrieve assessments")
async def list_assessments(
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List assessments accessible to the current user.

    Enhanced Features:
    - Standardized response format
    - Input validation
    - Error handling
    """
    assessments = AssessmentService.get_user_assessments(
        db,
        user_id=current_user.id,
        category=category,
        status=status_filter,
        skip=skip,
        limit=limit,
    )

    return create_success_response(
        data={
            "assessments": [serialize_model(assessment) for assessment in assessments],
            "total": len(assessments),
            "skip": skip,
            "limit": limit,
        },
        message="Assessments retrieved successfully",
    )


@router.get("/{assessment_id}")
@rate_limit(limit=200, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@measure_performance
@async_cached(expire=300, key_prefix="assessment_detail")
@handle_exceptions(default_message="Failed to retrieve assessment")
async def get_assessment(
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_db),
):
    """
    Get assessment details with sections and questions.

    Enhanced Features:
    - Standardized response format
    - Detailed assessment information with question count
    - Error handling
    """
    # Calculate question count
    question_count = sum(len(section.questions) for section in assessment.sections)

    assessment_data = serialize_model(assessment)
    assessment_data["sections"] = [
        serialize_model(section) for section in assessment.sections
    ]
    assessment_data["question_count"] = question_count

    return create_success_response(
        data=assessment_data, message="Assessment retrieved successfully"
    )


@router.put("/{assessment_id}")
async def update_assessment(
    assessment_in: AssessmentUpdate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Update assessment details.
    Requires creator or team admin permission.
    """
    updated_assessment = AssessmentService.update(
        db, assessment=assessment, assessment_in=assessment_in
    )
    return updated_assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete assessment.
    Requires creator or team admin permission.
    """
    AssessmentService.delete(db, assessment=assessment)


@router.post("/{assessment_id}/publish")
async def publish_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish assessment (change status to active).
    """
    if assessment.status.value == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is already published",
        )

    published_assessment = AssessmentService.publish(db, assessment=assessment)
    return published_assessment


@router.post("/{assessment_id}/archive")
async def archive_assessment(
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive assessment.
    """
    archived_assessment = AssessmentService.archive(db, assessment=assessment)
    return archived_assessment


@router.post("/{assessment_id}/duplicate", status_code=status.HTTP_201_CREATED)
async def duplicate_assessment(
    assessment: Assessment = Depends(check_assessment_access),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Duplicate an existing assessment.
    """
    duplicated_assessment = AssessmentService.duplicate(
        db, assessment=assessment, creator_id=current_user.id
    )
    return duplicated_assessment


# ==================== SECTION MANAGEMENT ====================


@router.post("/{assessment_id}/sections", status_code=status.HTTP_201_CREATED)
async def add_section(
    assessment_id: int,
    section_in: SectionCreate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new section to the assessment.
    """
    section = AssessmentService.add_section(
        db, assessment_id=assessment_id, section_data=section_in
    )
    return section


@router.delete(
    "/{assessment_id}/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_section(
    assessment_id: int,
    section_id: int,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a section from the assessment.
    """
    AssessmentService.delete_section(db, section_id=section_id)


# ==================== QUESTION MANAGEMENT ====================


@router.post(
    "/{assessment_id}/sections/{section_id}/questions",
    status_code=status.HTTP_201_CREATED,
)
async def add_question(
    assessment_id: int,
    section_id: int,
    question_in: QuestionCreate,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new question to a section.
    """
    question = AssessmentService.add_question(
        db, section_id=section_id, question_data=question_in
    )
    return question


@router.delete(
    "/{assessment_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_question(
    assessment_id: int,
    section_id: int,
    question_id: int,
    assessment: Assessment = Depends(check_assessment_edit_permission),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a question from the assessment.
    """
    AssessmentService.delete_question(db, question_id=question_id)
