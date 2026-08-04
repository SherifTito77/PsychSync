# app/api/v1/endpoints/feature_requests.py
"""Feature Request Management API Endpoints

API endpoints for managing feature requests, voting, and relationships.
"""

import asyncio
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.db.models.feature_requests import FeatureRequest, FeatureRequestVote
from app.db.models.user import User

router = APIRouter()


# ========================================================================
# Helper Functions
# ========================================================================


async def _feature_request_to_response(
    request: FeatureRequest, db: AsyncSession
) -> FeatureRequestResponse:
    """Convert database model to response model"""
    from sqlalchemy import select

    # ✅ ASYNC - Use select() instead of db.query()
    vote_count_result = await db.execute(
        select(func.count(FeatureRequestVote.id)).where(
            FeatureRequestVote.feature_request_id == request.id
        )
    )
    vote_count = vote_count_result.scalar() or 0

    return FeatureRequestResponse(
        id=str(request.id),
        title=request.title,
        description=request.description,
        status=request.status,
        theme=request.theme,
        subcategory=request.subcategory,
        request_type=request.request_type,
        priority=request.priority,
        effort=request.effort,
        value=request.value,
        reach_score=request.reach_score,
        impact_score=request.impact_score,
        confidence_score=request.confidence_score,
        effort_score=request.effort_score,
        rice_score=request.rice_score,
        source_type=request.source_type,
        created_at=request.created_at.isoformat(),
        updated_at=request.updated_at.isoformat(),
        shipped_at=request.shipped_at.isoformat() if request.shipped_at else None,
        vote_count=vote_count,
    )


async def _get_vote_count(request_id: str, db: AsyncSession) -> int:
    """Get vote count for a feature request"""
    from sqlalchemy import select

    # ✅ ASYNC - Use select() instead of db.query()
    count_result = await db.execute(
        select(func.count(FeatureRequestVote.id)).where(
            FeatureRequestVote.feature_request_id == request_id
        )
    )
    count = count_result.scalar()

    return count or 0


async def _update_search_vector(request: FeatureRequest, db: AsyncSession):
    """Update full-text search vector"""
    # PostgreSQL will automatically update the search_vector column
    # via the GENERATED ALWAYS AS clause in the table definition


# ========================================================================
# Pydantic Models
# ========================================================================


class FeatureRequestCreate(BaseModel):
    """Request model for creating a feature request"""

    title: str = Field(
        ..., min_length=1, max_length=255, description="Feature request title"
    )
    description: str = Field(..., min_length=1, description="Detailed description")
    theme: str = Field(..., description="Theme category (e.g., ASSESS, ANALYT)")
    subcategory: Optional[str] = Field(None, description="Theme subcategory")
    request_type: str = Field(..., description="Type: NEW, ENH, BUG, PERF, etc.")
    source_type: str = Field(..., description="Source: customer, internal, data_driven")
    source_id: Optional[str] = Field(None, description="External source ID")
    customer_id: Optional[str] = Field(
        None, description="Customer user ID if from customer"
    )


class FeatureRequestUpdate(BaseModel):
    """Request model for updating a feature request"""

    status: Optional[str] = None
    priority: Optional[str] = None
    effort: Optional[str] = None
    value: Optional[str] = None
    target_release: Optional[str] = None
    assigned_to: Optional[str] = None
    estimated_start_date: Optional[date] = None
    estimated_end_date: Optional[date] = None


class RICEScores(BaseModel):
    """RICE scoring model"""

    reach: Optional[float] = None
    impact: Optional[float] = None
    confidence: Optional[float] = None
    effort: Optional[float] = None
    rice_score: Optional[float] = None


class FeatureRequestResponse(BaseModel):
    """Response model for feature request"""

    id: str
    title: str
    description: str
    status: str
    theme: str
    subcategory: Optional[str]
    request_type: str
    priority: str
    effort: str
    value: str
    # RICE scores
    reach_score: Optional[float]
    impact_score: Optional[float]
    confidence_score: Optional[float]
    effort_score: Optional[float]
    rice_score: Optional[float]
    # Metadata
    source_type: str
    created_at: str
    updated_at: str
    shipped_at: Optional[str]
    vote_count: int


class FeatureRequestListResponse(BaseModel):
    """Response model for feature request list"""

    total: int
    requests: List[FeatureRequestResponse]


# ========================================================================
# API Endpoints
# ========================================================================


@router.post(
    "/",
    responses={
        201: {
            "description": "Resource created successfully",
            "content": {
                "application/json": {
                    "example": {"id": 1, "created_at": "2025-01-13T10:00:00Z"}
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=FeatureRequestResponse,
)
async def create_feature_request(
    request: FeatureRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new feature request.
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    # Create feature request
    feature_request = FeatureRequest(
        title=request.title,
        description=request.description,
        status="backlog",
        theme=request.theme,
        subcategory=request.subcategory,
        request_type=request.request_type,
        priority="P3",
        effort="M",
        value="V3",
        source_type=request.source_type,
        source_id=request.source_id,
        submitted_by_id=current_user.id,
        customer_id=request.customer_id,
    )

    await loop.run_in_executor(None, lambda: db.add(feature_request))
    await loop.run_in_executor(None, db.commit)
    await loop.run_in_executor(None, lambda: db.refresh(feature_request))

    # Update search vector
    await _update_search_vector(feature_request, db)

    return await _feature_request_to_response(feature_request, db)


@router.get(
    "/",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=FeatureRequestListResponse,
)
async def list_feature_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    theme: Optional[str] = Query(None, description="Filter by theme"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List feature requests with optional filters.
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    def query_db():
        query = db.query(FeatureRequest)

        if status:
            query = query.filter(FeatureRequest.status == status)
        if theme:
            query = query.filter(FeatureRequest.theme == theme)
        if customer_id:
            query = query.filter(FeatureRequest.customer_id == customer_id)

        # Order by RICE score (descending), then created date
        query = query.order_by(
            desc(FeatureRequest.rice_score), desc(FeatureRequest.created_at)
        )

        total = query.count()
        requests = query.offset(offset).limit(limit).all()

        return total, requests

    total, requests = await loop.run_in_executor(None, query_db)

    # ✅ ASYNC - Convert list using async helper
    response_list = []
    for r in requests:
        response_item = await _feature_request_to_response(r, db)
        response_list.append(response_item)

    return FeatureRequestListResponse(total=total, requests=response_list)


@router.get(
    "/{request_id}",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=FeatureRequestResponse,
)
async def get_feature_request(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific feature request by ID.
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    feature_request = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequest)
        .filter(FeatureRequest.id == request_id)
        .first(),
    )

    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    return await _feature_request_to_response(feature_request, db)


@router.put(
    "/{request_id}",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=FeatureRequestResponse,
)
async def update_feature_request(
    request_id: str,
    updates: FeatureRequestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a feature request (product team only).
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    feature_request = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequest)
        .filter(FeatureRequest.id == request_id)
        .first(),
    )

    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    # Check permissions (TODO: add proper role check)
    # if current_user.role not in ['product_manager', 'admin']:
    #     raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feature_request, field, value)

    # Update timestamps
    if updates.status == "shipped":
        feature_request.shipped_at = datetime.utcnow()

    feature_request.updated_at = datetime.utcnow()

    await loop.run_in_executor(None, db.commit)
    await loop.run_in_executor(None, lambda: db.refresh(feature_request))

    return await _feature_request_to_response(feature_request, db)


@router.post(
    "/{request_id}/vote",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
)
async def vote_for_feature_request(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Vote for a feature request.
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    feature_request = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequest)
        .filter(FeatureRequest.id == request_id)
        .first(),
    )

    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    # Check if already voted
    existing_vote = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequestVote)
        .filter(
            FeatureRequestVote.feature_request_id == request_id,
            FeatureRequestVote.user_id == current_user.id,
        )
        .first(),
    )

    if existing_vote:
        vote_count = await _get_vote_count(request_id, db)
        return {"message": "Already voted", "vote_count": vote_count}

    # Add vote
    vote = FeatureRequestVote(feature_request_id=request_id, user_id=current_user.id)
    await loop.run_in_executor(None, lambda: db.add(vote))
    await loop.run_in_executor(None, db.commit)

    vote_count = await _get_vote_count(request_id, db)

    return {"message": "Vote recorded", "vote_count": vote_count}


@router.delete(
    "/{request_id}/vote",
    responses={
        204: {"description": "Resource deleted successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Resource not found"},
    },
)
async def remove_vote(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove vote from a feature request.
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    vote = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequestVote)
        .filter(
            FeatureRequestVote.feature_request_id == request_id,
            FeatureRequestVote.user_id == current_user.id,
        )
        .first(),
    )

    if vote:
        await loop.run_in_executor(None, lambda: db.delete(vote))
        await loop.run_in_executor(None, db.commit)

    return {"message": "Vote removed"}


@router.get(
    "/{request_id}/votes",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
)
async def get_feature_request_votes(
    request_id: str, db: AsyncSession = Depends(get_db)
):
    """
    Get vote count for a feature request.
    """
    # ✅ ASYNC - Call async helper directly
    count = await _get_vote_count(request_id, db)

    return {"count": count}


@router.put(
    "/{request_id}/rice",
    responses={
        200: {
            "description": "Request successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Operation completed successfully",
                    }
                }
            },
        },
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"},
    },
    response_model=FeatureRequestResponse,
)
async def update_rice_scores(
    request_id: str,
    scores: RICEScores,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update RICE scores for a feature request (product team only).
    """
    # ✅ Run sync db operations in thread pool to avoid blocking
    loop = asyncio.get_event_loop()

    feature_request = await loop.run_in_executor(
        None,
        lambda: db.query(FeatureRequest)
        .filter(FeatureRequest.id == request_id)
        .first(),
    )

    if not feature_request:
        raise HTTPException(status_code=404, detail="Feature request not found")

    # Update RICE scores
    feature_request.reach_score = scores.reach
    feature_request.impact_score = scores.impact
    feature_request.confidence_score = scores.confidence
    feature_request.effort_score = scores.effort
    feature_request.rice_score = scores.rice_score

    feature_request.updated_at = datetime.utcnow()

    await loop.run_in_executor(None, db.commit)
    await loop.run_in_executor(None, lambda: db.refresh(feature_request))

    return await _feature_request_to_response(feature_request, db)
