# app/api/v1/endpoints/analytics.py

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_async_db,
    get_current_active_user,
    get_current_admin_user
)
from app.db.models.user import User

# --- CORRECTED IMPORTS ---
from app.services import analytics_service as AnalyticsService
from app.services import assessment_service as AssessmentService
from app.services import team_service as TeamService
# --- END CORRECTED IMPORTS ---

router = APIRouter()


@router.get("/assessments/{assessment_id}")
def get_assessment_analytics(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a specific assessment.
    Requires assessment creator or team admin permission.
    """
    assessment = AssessmentService.get_by_id(db, assessment_id=assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check permission
    if assessment.created_by_id != current_user.id:
        if assessment.team_id:
            if not TeamService.is_admin_or_owner(db, team_id=assessment.team_id, user_id=current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to view these analytics"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view these analytics"
            )
    
    analytics = AnalyticsService.get_assessment_analytics(db, assessment_id=assessment_id)
    return analytics


@router.get("/users/me")
def get_my_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for current user.
    """
    analytics = AnalyticsService.get_user_analytics(db, user_id=current_user.id)
    return analytics


@router.get("/users/{user_id}")
def get_user_analytics(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a specific user.
    User can only view their own analytics unless they're an admin.
    """
    if user_id != current_user.id:
        # This import is already correct, which is great!
        import app.services.user_service as user_service
        if not user_service.is_admin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own analytics"
            )
    
    analytics = AnalyticsService.get_user_analytics(db, user_id=user_id)
    return analytics


@router.get("/teams/{team_id}")
def get_team_analytics(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get analytics for a team.
    Requires team membership.
    """
    if not TeamService.is_member(db, team_id=team_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a team member to view analytics"
        )
    
    analytics = AnalyticsService.get_team_analytics(db, team_id=team_id)
    return analytics


@router.get("/system")
def get_system_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get system-wide analytics.
    Admin only.
    """
    analytics = AnalyticsService.get_system_analytics(db)
    return analytics