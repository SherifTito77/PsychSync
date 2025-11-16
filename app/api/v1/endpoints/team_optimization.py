"""
File Path: app/api/v1/endpoints/team_optimization.py
API endpoints for team optimization
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.team_optimization_service import TeamOptimizationService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# =================================================================
# REQUEST/RESPONSE MODELS
# =================================================================

class TeamOptimizationRequest(BaseModel):
    """Request model for team optimization"""
    team_name: str = Field(..., min_length=1, max_length=200)
    team_id: Optional[int] = None
    
    # Size requirements
    min_size: int = Field(3, ge=1, le=50)
    max_size: int = Field(10, ge=1, le=50)
    target_size: int = Field(5, ge=1, le=50)
    
    # Role and skill requirements
    required_roles: dict = Field(default_factory=dict)
    optional_roles: dict = Field(default_factory=dict)
    required_skills: dict = Field(default_factory=dict)
    desired_skills: dict = Field(default_factory=dict)
    
    # Diversity settings
    min_personality_diversity: float = Field(0.3, ge=0, le=1)
    max_personality_similarity: float = Field(0.7, ge=0, le=1)
    max_same_department: Optional[int] = None
    
    # Candidate pool
    candidate_user_ids: Optional[List[int]] = None
    include_existing_members: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "team_name": "Product Development Team",
                "target_size": 5,
                "required_roles": {"Developer": 2, "Designer": 1},
                "required_skills": {"Python": 70.0, "React": 60.0},
                "min_personality_diversity": 0.3
            }
        }


class MemberProfileResponse(BaseModel):
    """Response model for team member profile"""
    user_id: int
    name: str
    email: str
    department: str
    seniority_level: str
    availability: float
    skills: dict
    personality_traits: dict
    
    class Config:
        from_attributes = True


class OptimizedTeamResponse(BaseModel):
    """Response model for optimized team"""
    team_id: int
    team_name: str
    members: List[MemberProfileResponse]
    
    # Scores
    overall_score: float
    compatibility_score: float
    skill_coverage_score: float
    diversity_score: float
    balance_score: float
    
    # Statistics
    avg_performance: float
    avg_collaboration: float
    
    # Analysis
    role_distribution: dict
    skill_coverage: dict
    personality_profile: dict
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]


class TeamAnalysisRequest(BaseModel):
    """Request model for team analysis"""
    team_id: int
    include_recommendations: bool = True


class CompatibilityRequest(BaseModel):
    """Request model for compatibility check"""
    user_id_1: int
    user_id_2: int


class CompatibilityResponse(BaseModel):
    """Response model for compatibility check"""
    user_1: dict
    user_2: dict
    compatibility_score: float
    compatibility_level: str
    color_indicator: str
    recommendations: List[str]


# =================================================================
# ENDPOINTS
# =================================================================

@router.post("/optimize", response_model=OptimizedTeamResponse, status_code=status.HTTP_200_OK)
async def optimize_team(
    request: TeamOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimize team composition based on requirements
    
    This endpoint analyzes available candidates and creates an optimal team
    based on:
    - Personality compatibility
    - Skill requirements
    - Role distribution
    - Diversity metrics
    
    **Returns:** Optimized team with detailed analysis
    """
    try:
        logger.info(
            f"User {current_user.id} requesting team optimization: {request.team_name}"
        )
        
        service = TeamOptimizationService()
        
        # Build requirements dict
        requirements = {
            'team_id': request.team_id or 0,
            'team_name': request.team_name,
            'min_size': request.min_size,
            'max_size': request.max_size,
            'target_size': request.target_size,
            'required_roles': request.required_roles,
            'optional_roles': request.optional_roles,
            'required_skills': request.required_skills,
            'desired_skills': request.desired_skills,
            'min_personality_diversity': request.min_personality_diversity,
            'max_personality_similarity': request.max_personality_similarity,
            'max_same_department': request.max_same_department
        }
        
        # Run optimization
        optimized_team = await service.optimize_team_composition(
            db=db,
            team_requirements=requirements,
            organization_id=current_user.organization_id,
            existing_team_id=request.team_id
        )
        
        # Convert to response model
        members_response = [
            MemberProfileResponse(
                user_id=m.user_id,
                name=m.name,
                email=m.email,
                department=m.department,
                seniority_level=m.seniority_level,
                availability=m.availability,
                skills=m.skills,
                personality_traits={
                    'openness': m.openness,
                    'conscientiousness': m.conscientiousness,
                    'extraversion': m.extraversion,
                    'agreeableness': m.agreeableness,
                    'neuroticism': m.neuroticism
                }
            )
            for m in optimized_team.members
        ]
        
        response = OptimizedTeamResponse(
            team_id=optimized_team.team_id,
            team_name=optimized_team.team_name,
            members=members_response,
            overall_score=optimized_team.overall_score,
            compatibility_score=optimized_team.compatibility_score,
            skill_coverage_score=optimized_team.skill_coverage_score,
            diversity_score=optimized_team.diversity_score,
            balance_score=optimized_team.balance_score,
            avg_performance=optimized_team.avg_performance,
            avg_collaboration=optimized_team.avg_collaboration,
            role_distribution=optimized_team.role_distribution,
            skill_coverage=optimized_team.skill_coverage,
            personality_profile=optimized_team.personality_profile,
            strengths=optimized_team.strengths,
            gaps=optimized_team.gaps,
            recommendations=optimized_team.recommendations
        )
        
        logger.info(
            f"Team optimization complete: {len(members_response)} members, "
            f"score: {response.overall_score:.2f}"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error optimizing team: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize team composition"
        )


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_team(
    request: TeamAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze existing team composition
    
    Provides detailed analysis of current team including:
    - Compatibility scores
    - Skill coverage
    - Diversity metrics
    - Strengths and gaps
    - Recommendations for improvement
    
    **Returns:** Comprehensive team analysis
    """
    try:
        logger.info(
            f"User {current_user.id} analyzing team {request.team_id}"
        )
        
        service = TeamOptimizationService()
        
        analysis = await service.analyze_team(
            db=db,
            team_id=request.team_id,
            organization_id=current_user.organization_id
        )
        
        logger.info(
            f"Team analysis complete: {analysis['team_name']}, "
            f"score: {analysis['overall_score']:.2f}"
        )
        
        return analysis
        
    except ValueError as e:
        logger.error(f"Team not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing team: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze team"
        )


@router.post("/compatibility", response_model=CompatibilityResponse)
async def check_compatibility(
    request: CompatibilityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check compatibility between two team members
    
    Analyzes personality compatibility and provides recommendations
    for effective collaboration.
    
    **Returns:** Compatibility score and collaboration tips
    """
    try:
        logger.info(
            f"Checking compatibility: {request.user_id_1} <-> {request.user_id_2}"
        )
        
        service = TeamOptimizationService()
        
        result = await service.check_member_compatibility(
            db=db,
            user_id_1=request.user_id_1,
            user_id_2=request.user_id_2,
            organization_id=current_user.organization_id
        )
        
        return CompatibilityResponse(**result)
        
    except ValueError as e:
        logger.error(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check compatibility"
        )


@router.get("/candidates", response_model=List[MemberProfileResponse])
async def get_candidates(
    min_availability: float = Query(50, ge=0, le=100),
    department: Optional[str] = Query(None),
    skills: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of candidates available for team optimization
    
    **Query Parameters:**
    - min_availability: Minimum availability percentage
    - department: Filter by department
    - skills: Comma-separated list of required skills
    - limit: Maximum number of results
    
    **Returns:** List of candidate profiles
    """
    try:
        logger.info(
            f"Fetching candidates for user {current_user.id}"
        )
        
        service = TeamOptimizationService()
        
        # Build filters
        filters = {
            'min_availability': min_availability
        }
        if department:
            filters['department'] = department
        if skills:
            filters['skills'] = skills.split(',')
        
        candidates = await service.get_candidate_pool(
            db=db,
            organization_id=current_user.organization_id,
            filters=filters
        )
        
        # Convert to response model
        response = [
            MemberProfileResponse(
                user_id=c['user_id'],
                name=c['name'],
                email=c['email'],
                department=c['department'],
                seniority_level=c['seniority_level'],
                availability=c['availability'],
                skills=c['skills'],
                personality_traits=c['personality_traits']
            )
            for c in candidates[:limit]
        ]
        
        logger.info(f"Found {len(response)} eligible candidates")
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch candidates"
        )


@router.get("/recommendations/{team_id}")
async def get_team_recommendations(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get improvement recommendations for a team
    
    **Returns:** List of actionable recommendations
    """
    try:
        service = TeamOptimizationService()
        
        analysis = await service.analyze_team(
            db=db,
            team_id=team_id,
            organization_id=current_user.organization_id
        )
        
        return {
            'team_id': team_id,
            'team_name': analysis['team_name'],
            'recommendations': analysis['recommendations'],
            'gaps': analysis['gaps'],
            'priority_actions': analysis['recommendations'][:3]  # Top 3
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.post("/simulate")
async def simulate_team_change(
    team_id: int,
    add_user_ids: List[int] = [],
    remove_user_ids: List[int] = [],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulate impact of adding/removing team members
    
    **Parameters:**
    - team_id: Team to simulate changes for
    - add_user_ids: Users to add (simulation only)
    - remove_user_ids: Users to remove (simulation only)
    
    **Returns:** Comparison of current vs. simulated team scores
    """
    try:
        # This would simulate team changes and show impact
        # Implementation would fetch current team, modify it, and re-analyze
        
        return {
            'team_id': team_id,
            'simulation': 'not_implemented',
            'message': 'Feature coming soon'
        }
        
    except Exception as e:
        logger.error(f"Error simulating team change: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to simulate team change"
        )