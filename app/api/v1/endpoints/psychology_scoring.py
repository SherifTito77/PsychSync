# app/api/v1/endpoints/psychology_scoring.py
"""
Psychological Assessment Scoring API Endpoints
Replaces basketball scoring with psychological wellness analytics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_async_db, get_current_active_user
from app.db.models.user import User
from app.db.models.assessment import Assessment
from app.db.models.response_score import ResponseScore
from app.services.scoring_service import ScoringService
from app.services.assessment_service import AssessmentService
from app.services.team_dynamics_service import TeamDynamicsService
from pydantic import BaseModel, Field

router = APIRouter()


class PsychologicalScoreResponse(BaseModel):
    """Psychological assessment score response model"""
    user_id: str
    assessment_id: str
    overall_score: float = Field(ge=0, le=100, description="Overall wellness score (0-100)")
    category_scores: Dict[str, float] = Field(description="Scores by psychological category")
    insights: List[str] = Field(description="AI-generated insights")
    recommendations: List[str] = Field(description="Personalized recommendations")
    assessment_date: datetime
    created_at: datetime


class PsychometricProfileResponse(BaseModel):
    """Psychometric profile response model"""
    user_id: str
    analysis_period_days: int
    baseline_score: float
    current_score: float
    improvement_trend: float
    category_trends: Dict[str, float]
    risk_factors: List[str]
    strengths: List[str]
    developmental_areas: List[str]


class TeamPsychologyResponse(BaseModel):
    """Team psychological analysis response"""
    team_id: str
    team_size: int
    average_score: float
    cohesion_score: float
    communication_effectiveness: float
    collaboration_score: float
    psychological_safety: float
    individual_profiles: List[Dict[str, Any]]
    team_insights: List[str]
    recommendations: List[str]


@router.get("/assessment/{assessment_id}/score", response_model=PsychologicalScoreResponse)
async def get_assessment_psychological_score(
    assessment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get psychological assessment score for a specific assessment.
    Provides comprehensive wellness analysis across multiple dimensions.
    """
    # Verify assessment exists and user has access
    assessment = await AssessmentService.get_by_id(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    # Check permissions (user can access their own assessments, or admins can access all)
    if assessment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this assessment"
        )

    try:
        # Calculate psychological score using the scoring service
        score_data = await ScoringService.calculate_psychological_score(
            db, assessment_id, current_user.id
        )

        return PsychologicalScoreResponse(**score_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating psychological score: {str(e)}"
        )


@router.get("/profile/{user_id}/psychometric", response_model=PsychometricProfileResponse)
async def get_psychometric_profile(
    user_id: str,
    period_days: int = Query(default=30, ge=7, le=365, description="Analysis period in days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive psychometric profile for a user.
    Analyzes trends, strengths, and developmental areas over time.
    """
    # Check permissions (user can access their own profile, or admins can access all)
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile"
        )

    try:
        # Generate psychometric profile
        profile_data = await ScoringService.generate_psychometric_profile(
            db, user_id, period_days
        )

        return PsychometricProfileResponse(**profile_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating psychometric profile: {str(e)}"
        )


@router.get("/team/{team_id}/psychology", response_model=TeamPsychologyResponse)
async def get_team_psychology_analysis(
    team_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comprehensive team psychological analysis.
    Provides insights into team dynamics, cohesion, and collaboration patterns.
    """
    # TODO: Verify user is member of the team or has admin privileges
    # This would require team membership checking logic

    try:
        # Generate team psychological analysis
        team_analysis = await TeamDynamicsService.analyze_team_psychology(
            db, team_id
        )

        return TeamPsychologyResponse(**team_analysis)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing team psychology: {str(e)}"
        )


@router.get("/user/{user_id}/wellness-trends")
async def get_wellness_trends(
    user_id: str,
    days_back: int = Query(default=90, ge=7, le=365, description="Days of trend data"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get wellness trends for a user over time.
    Useful for tracking progress and identifying patterns.
    """
    # Check permissions
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these trends"
        )

    try:
        # Get historical wellness data
        trends_data = await ScoringService.get_wellness_trends(
            db, user_id, days_back
        )

        return {
            "user_id": user_id,
            "period_days": days_back,
            "trends": trends_data,
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving wellness trends: {str(e)}"
        )


@router.post("/assessment/{assessment_id}/insights/generate")
async def generate_assessment_insights(
    assessment_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate AI-powered insights for an assessment.
    Uses PsychSync AI to provide personalized recommendations and analysis.
    """
    # Verify assessment exists and user has access
    assessment = await AssessmentService.get_by_id(db, assessment_id=assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    if assessment.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this assessment"
        )

    try:
        # Generate AI-powered insights
        insights = await ScoringService.generate_ai_insights(
            db, assessment_id, current_user.id
        )

        return {
            "assessment_id": assessment_id,
            "insights": insights,
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating insights: {str(e)}"
        )


@router.get("/psychological-frameworks")
async def get_available_psychological_frameworks():
    """
    Get list of available psychological assessment frameworks.
    Returns information about MBTI, Big Five, Enneagram, etc.
    """
    frameworks = {
        "mbti": {
            "name": "Myers-Briggs Type Indicator",
            "description": "Personality assessment based on psychological preferences",
            "dimensions": ["Extraversion-Introversion", "Sensing-Intuition", "Thinking-Feeling", "Judging-Perceiving"]
        },
        "big_five": {
            "name": "Big Five (OCEAN) Personality Traits",
            "description": "Five-factor model of personality traits",
            "dimensions": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
        },
        "enneagram": {
            "name": "Enneagram Personality Types",
            "description": "Nine personality types based on core motivations",
            "types": list(range(1, 10))
        },
        "disc": {
            "name": "DISC Assessment",
            "description": "Behavioral assessment focusing on four personality traits",
            "dimensions": ["Dominance", "Influence", "Steadiness", "Conscientiousness"]
        },
        "predictive_index": {
            "name": "Predictive Index Behavioral Assessment",
            "description": "Assessment of workplace behaviors and drives",
            "factors": ["Dominance", "Extraversion", "Patience", "Formality"]
        }
    }

    return {
        "available_frameworks": frameworks,
        "total_frameworks": len(frameworks),
        "last_updated": datetime.utcnow().isoformat()
    }