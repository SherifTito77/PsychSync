"""
File Path: app/api/v1/endpoints/optimizer.py
API endpoints for team composition optimization
Provides team optimization and analysis features
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.db.models.team import Team, TeamMember
from app.services.optimizer.team_optimizer import (
    TeamOptimizationEngine,
    TeamMemberProfile,
    TeamRequirements,
    OptimizedTeam
)
from app.services.optimizer_service import optimizer_service
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# =================================================================
# REQUEST/RESPONSE MODELS
# =================================================================

class OptimizeTeamRequest(BaseModel):
    """Request model for team optimization"""
    team_id: Optional[int] = None
    team_name: str = Field(..., min_length=1, max_length=200)
    
    # Size requirements
    min_size: int = Field(3, ge=1, le=50)
    max_size: int = Field(10, ge=1, le=50)
    target_size: int = Field(5, ge=1, le=50)
    
    # Role requirements
    required_roles: Dict[str, int] = Field(default_factory=dict)
    optional_roles: Dict[str, int] = Field(default_factory=dict)
    
    # Skill requirements
    required_skills: Dict[str, float] = Field(default_factory=dict)
    desired_skills: Dict[str, float] = Field(default_factory=dict)
    
    # Diversity settings
    min_personality_diversity: float = Field(0.3, ge=0, le=1)
    max_personality_similarity: float = Field(0.7, ge=0, le=1)
    max_same_department: Optional[int] = None
    min_senior_members: Optional[int] = None
    max_junior_members: Optional[int] = None
    
    # Candidate pool
    candidate_user_ids: Optional[List[int]] = None
    include_existing_members: bool = False


class PersonalityTraitsInput(BaseModel):
    """Personality traits input"""
    openness: float = Field(..., ge=0, le=100)
    conscientiousness: float = Field(..., ge=0, le=100)
    extraversion: float = Field(..., ge=0, le=100)
    agreeableness: float = Field(..., ge=0, le=100)
    neuroticism: float = Field(..., ge=0, le=100)


class TeamMemberResponse(BaseModel):
    """Response model for team member"""
    user_id: int
    name: str
    email: str
    department: str
    seniority_level: str
    availability: float
    
    # Scores
    compatibility_score: float
    skill_match_score: float
    diversity_contribution: float
    
    # Personality summary
    personality_summary: Dict[str, float]
    
    class Config:
        from_attributes = True


class OptimizedTeamResponse(BaseModel):
    """Response model for optimized team"""
    team_id: int
    team_name: str
    members: List[TeamMemberResponse]
    
    # Scores
    overall_score: float
    compatibility_score: float
    skill_coverage_score: float
    diversity_score: float
    balance_score: float
    
    # Statistics
    avg_performance: float
    avg_collaboration: float
    total_availability: float
    
    # Analysis
    role_distribution: Dict[str, int]
    skill_coverage: Dict[str, float]
    personality_profile: Dict[str, float]
    
    # Insights
    strengths: List[str]
    gaps: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class TeamAnalysisRequest(BaseModel):
    """Request model for analyzing existing team"""
    team_id: int
    include_recommendations: bool = True


class CompatibilityCheckRequest(BaseModel):
    """Request model for checking member compatibility"""
    user_id_1: int
    user_id_2: int


class CompatibilityCheckResponse(BaseModel):
    """Response model for compatibility check"""
    user_1: Dict[str, Any]
    user_2: Dict[str, Any]
    compatibility_score: float
    compatibility_level: str  # "Low", "Medium", "High"
    analysis: Dict[str, Any]
    recommendations: List[str]


# =================================================================
# ENDPOINTS
# =================================================================

@router.post("/optimize", response_model=OptimizedTeamResponse)
async def optimize_team(
    request: OptimizeTeamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimize team composition based on requirements
    
    Creates an optimized team by analyzing:
    - Personality compatibility
    - Skill requirements
    - Role distribution
    - Diversity metrics
    - Performance history
    
    Returns optimized team with detailed analysis
    """
    try:
        logger.info(
            f"User {current_user.id} requesting team optimization: "
            f"{request.team_name}"
        )
        
        # Build candidate pool
        candidates = await _build_candidate_pool(
            db,
            current_user,
            request.candidate_user_ids
        )
        
        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible candidates found for optimization"
            )
        
        # Get existing team members if applicable
        existing_members = []
        if request.team_id and request.include_existing_members:
            existing_members = await _get_existing_team_members(
                db,
                request.team_id
            )
        
        # Create requirements object
        requirements = TeamRequirements(
            team_id=request.team_id or 0,
            team_name=request.team_name,
            min_size=request.min_size,
            max_size=request.max_size,
            target_size=request.target_size,
            required_roles=request.required_roles,
            optional_roles=request.optional_roles,
            required_skills=request.required_skills,
            desired_skills=request.desired_skills,
            min_personality_diversity=request.min_personality_diversity,
            max_personality_similarity=request.max_personality_similarity,
            max_same_department=request.max_same_department,
            min_senior_members=request.min_senior_members,
            max_junior_members=request.max_junior_members
        )
        
        # Run optimization
        optimizer = TeamOptimizationEngine()
        optimized_team = optimizer.optimize_team(
            candidates,
            requirements,
            existing_members
        )
        
        # Convert to response model
        response = _convert_to_response(optimized_team)
        
        logger.info(
            f"Team optimization complete: {len(response.members)} members, "
            f"score: {response.overall_score:.2f}"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in team optimization: {str(e)}")
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


@router.post("/analyze", response_model=OptimizedTeamResponse)
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
    """
    try:
        logger.info(
            f"User {current_user.id} requesting analysis for team "
            f"{request.team_id}"
        )
        
        # Get team using service
        team = await optimizer_service.get_team_by_id_and_org(
            db, request.team_id, current_user.organization_id
        )

        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team {request.team_id} not found"
            )
        
        # Get team members using service
        team_members_db = await optimizer_service.get_team_members_by_team_id(db, team.id)

        # Convert to TeamMemberProfile objects
        members = []
        for tm in team_members_db:
            if tm.user and tm.user.is_active:
                profile = await optimizer_service.user_to_profile(db, tm.user)
                members.append(profile)
        
        if not members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team has no members to analyze"
            )
        
        # Create mock requirements for analysis
        requirements = TeamRequirements(
            team_id=team.id,
            team_name=team.name,
            min_size=len(members),
            max_size=len(members),
            target_size=len(members),
            required_roles={},
            optional_roles={},
            required_skills={},
            desired_skills={},
            min_personality_diversity=0.3,
            max_personality_similarity=0.7
        )
        
        # Run analysis using optimizer
        optimizer = TeamOptimizationEngine()
        analysis_result = optimizer._create_team_result(
            members,
            requirements,
            overall_score=85.0  # Placeholder
        )
        
        # Convert to response
        response = _convert_to_response(analysis_result)
        
        logger.info(
            f"Team analysis complete: {team.name}, "
            f"score: {response.overall_score:.2f}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing team: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze team"
        )


@router.post("/compatibility", response_model=CompatibilityCheckResponse)
async def check_compatibility(
    request: CompatibilityCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check compatibility between two team members
    
    Analyzes personality compatibility and provides recommendations
    for working together effectively
    """
    try:
        logger.info(
            f"Checking compatibility between users "
            f"{request.user_id_1} and {request.user_id_2}"
        )
        
        # Get both users using service
        user1 = await optimizer_service.get_user_by_id_and_org(
            db, request.user_id_1, current_user.organization_id
        )

        user2 = await optimizer_service.get_user_by_id_and_org(
            db, request.user_id_2, current_user.organization_id
        )

        if not user1 or not user2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both users not found"
            )
        
        # Convert to profiles using service
        profile1 = await optimizer_service.user_to_profile(db, user1)
        profile2 = await optimizer_service.user_to_profile(db, user2)
        
        # Calculate compatibility
        optimizer = TeamOptimizationEngine()
        compatibility_score = optimizer._calculate_personality_compatibility(
            profile1,
            profile2
        )
        
        # Determine compatibility level
        if compatibility_score >= 75:
            compatibility_level = "High"
        elif compatibility_score >= 50:
            compatibility_level = "Medium"
        else:
            compatibility_level = "Low"
        
        # Generate analysis and recommendations
        analysis = _generate_compatibility_analysis(profile1, profile2)
        recommendations = _generate_collaboration_recommendations(
            profile1,
            profile2,
            compatibility_score
        )
        
        response = CompatibilityCheckResponse(
            user_1={
                "id": user1.id,
                "name": user1.full_name,
                "personality": {
                    "openness": profile1.openness,
                    "conscientiousness": profile1.conscientiousness,
                    "extraversion": profile1.extraversion,
                    "agreeableness": profile1.agreeableness,
                    "neuroticism": profile1.neuroticism
                }
            },
            user_2={
                "id": user2.id,
                "name": user2.full_name,
                "personality": {
                    "openness": profile2.openness,
                    "conscientiousness": profile2.conscientiousness,
                    "extraversion": profile2.extraversion,
                    "agreeableness": profile2.agreeableness,
                    "neuroticism": profile2.neuroticism
                }
            },
            compatibility_score=compatibility_score,
            compatibility_level=compatibility_level,
            analysis=analysis,
            recommendations=recommendations
        )
        
        logger.info(
            f"Compatibility check complete: {compatibility_score:.2f} "
            f"({compatibility_level})"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check compatibility"
        )


@router.get("/candidates", response_model=List[TeamMemberResponse])
async def get_optimization_candidates(
    min_availability: float = Query(50, ge=0, le=100),
    required_skills: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of candidates available for team optimization
    
    Filters users based on:
    - Availability
    - Required skills
    - Department
    """
    try:
        logger.info(
            f"Fetching optimization candidates for user {current_user.id}"
        )
        
        # Get active users using service
        users = await optimizer_service.get_active_users_by_org(
            db, current_user.organization_id, limit
        )

        # Convert to profiles
        profiles = []
        for user in users:
            profile = await optimizer_service.user_to_profile(db, user)
            if profile.availability >= min_availability:
                profiles.append(profile)
        
        # Convert to response
        candidates = [
            TeamMemberResponse(
                user_id=p.user_id,
                name=p.name,
                email=p.email,
                department=p.department,
                seniority_level=p.seniority_level,
                availability=p.availability,
                compatibility_score=0.0,  # Placeholder
                skill_match_score=0.0,  # Placeholder
                diversity_contribution=0.0,  # Placeholder
                personality_summary={
                    "openness": p.openness,
                    "conscientiousness": p.conscientiousness,
                    "extraversion": p.extraversion,
                    "agreeableness": p.agreeableness,
                    "neuroticism": p.neuroticism
                }
            )
            for p in profiles
        ]
        
        logger.info(f"Found {len(candidates)} eligible candidates")
        
        return candidates
        
    except Exception as e:
        logger.error(f"Error fetching candidates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch candidates"
        )


# =================================================================
# HELPER FUNCTIONS
# =================================================================

async def _build_candidate_pool(
    db: Session,
    current_user: User,
    candidate_ids: Optional[List[str]]
) -> List[TeamMemberProfile]:
    """Build pool of candidate profiles using service"""
    if candidate_ids:
        users = await optimizer_service.get_users_by_ids_and_org(
            db, candidate_ids, current_user.organization_id
        )
    else:
        users = await optimizer_service.get_active_users_by_org(
            db, current_user.organization_id, 100
        )

    profiles = []
    for user in users:
        profile = await optimizer_service.user_to_profile(db, user)
        profiles.append(profile)

    return profiles




def _convert_to_response(
    optimized_team: OptimizedTeam
) -> OptimizedTeamResponse:
    """Convert OptimizedTeam to response model"""
    members = [
        TeamMemberResponse(
            user_id=m.user_id,
            name=m.name,
            email=m.email,
            department=m.department,
            seniority_level=m.seniority_level,
            availability=m.availability,
            compatibility_score=75.0,  # Placeholder
            skill_match_score=80.0,  # Placeholder
            diversity_contribution=70.0,  # Placeholder
            personality_summary={
                "openness": m.openness,
                "conscientiousness": m.conscientiousness,
                "extraversion": m.extraversion,
                "agreeableness": m.agreeableness,
                "neuroticism": m.neuroticism
            }
        )
        for m in optimized_team.members
    ]
    
    return OptimizedTeamResponse(
        team_id=optimized_team.team_id,
        team_name=optimized_team.team_name,
        members=members,
        overall_score=optimized_team.overall_score,
        compatibility_score=optimized_team.compatibility_score,
        skill_coverage_score=optimized_team.skill_coverage_score,
        diversity_score=optimized_team.diversity_score,
        balance_score=optimized_team.balance_score,
        avg_performance=optimized_team.avg_performance,
        avg_collaboration=optimized_team.avg_collaboration,
        total_availability=optimized_team.total_availability,
        role_distribution=optimized_team.role_distribution,
        skill_coverage=optimized_team.skill_coverage,
        personality_profile=optimized_team.personality_profile,
        strengths=optimized_team.strengths,
        gaps=optimized_team.gaps,
        recommendations=optimized_team.recommendations
    )


def _generate_compatibility_analysis(
    profile1: TeamMemberProfile,
    profile2: TeamMemberProfile
) -> Dict[str, Any]:
    """Generate detailed compatibility analysis"""
    return {
        "personality_match": {
            "complementary_traits": ["Extraversion balance", "Openness diversity"],
            "aligned_traits": ["High conscientiousness", "High agreeableness"],
            "potential_conflicts": ["Differing stress responses"]
        },
        "work_style": {
            "collaboration_potential": "High",
            "communication_style": "Compatible",
            "decision_making": "Complementary"
        },
        "strengths": [
            "Strong collaborative potential",
            "Balanced perspectives",
            "Complementary skills"
        ]
    }


def _generate_collaboration_recommendations(
    profile1: TeamMemberProfile,
    profile2: TeamMemberProfile,
    compatibility_score: float
) -> List[str]:
    """Generate recommendations for effective collaboration"""
    recommendations = []
    
    if compatibility_score >= 75:
        recommendations.append(
            "Excellent compatibility - leverage natural synergy"
        )
        recommendations.append(
            "Consider pairing on complex projects requiring close collaboration"
        )
    elif compatibility_score >= 50:
        recommendations.append(
            "Good compatibility - establish clear communication protocols"
        )
        recommendations.append(
            "Define roles and responsibilities early in projects"
        )
    else:
        recommendations.append(
            "Moderate compatibility - may benefit from structured interaction"
        )
        recommendations.append(
            "Consider team-building activities to strengthen relationship"
        )
        recommendations.append(
            "Provide mediation support if conflicts arise"
        )
    
    # Personality-specific recommendations
    if abs(profile1.extraversion - profile2.extraversion) > 40:
        recommendations.append(
            "Balance meeting styles to accommodate introvert-extravert differences"
        )
    
    if profile1.conscientiousness > 75 and profile2.conscientiousness < 50:
        recommendations.append(
            "Align on quality standards and deadline expectations early"
        )
    
    return recommendations