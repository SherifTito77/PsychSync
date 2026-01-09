"""
Skill Gap Analysis API Endpoints

Advanced skill gap analysis and development planning endpoints.
"""

from typing import List, Optional, Dict, Any

from app.middleware.rate_limiter import check_rate_limit
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.skill_gap_analysis import (
    SkillGapAnalyzer,
    SkillAssessment,
    SkillDemand,
    LearningRecommendation,
    DevelopmentProgram,
    CareerTrajectory
)
from pydantic import BaseModel, Field

router = APIRouter()

# Request/Response Models
class SkillAssessmentResponse(BaseModel):
    skill_name: str
    category: str
    current_level: float
    required_level: float
    gap_percentage: float
    priority: str
    assessment_date: datetime
    confidence_score: float

class SkillDemandResponse(BaseModel):
    skill_name: str
    category: str
    current_demand: float
    predicted_demand_12m: float
    predicted_demand_24m: float
    growth_rate: float
    market_trend: str
    industry_relevance: float

class LearningResourceResponse(BaseModel):
    name: str
    provider: str
    duration: int
    cost: float
    style: str

class LearningRecommendationResponse(BaseModel):
    skill_name: str
    learning_style: str
    recommended_resources: List[LearningResourceResponse]
    estimated_duration: int
    difficulty_level: str
    completion_probability: float
    expected_improvement: float
    cost_estimate: Optional[float]

class DevelopmentProgramResponse(BaseModel):
    program_name: str
    target_skills: List[str]
    duration_weeks: int
    delivery_method: str
    provider: str
    estimated_cost: float
    expected_roi: float
    success_rate: float
    prerequisites: List[str]

class SkillGapSummaryResponse(BaseModel):
    critical_gaps: int
    high_priority_gaps: int
    medium_priority_gaps: int
    low_priority_gaps: int
    average_gap_size: float
    total_assessments: int

class OrganizationalSkillGapResponse(BaseModel):
    overall_gaps: Dict[str, Any]
    department_gaps: Dict[str, List[SkillAssessmentResponse]]
    critical_gaps: List[SkillAssessmentResponse]
    skill_supply_demand: Dict[str, Any]
    recommendations: List[str]

class SkillRequirementResponse(BaseModel):
    skill_name: str
    required_level: float
    current_level: Optional[float]
    gap_percentage: float

class CareerTrajectoryResponse(BaseModel):
    current_role: str
    target_role: str
    time_to_promotion: int
    required_skills: List[SkillRequirementResponse]
    skill_development_plan: List[LearningRecommendationResponse]
    promotion_probability: float
    salary_impact: float

class LearningPathRequest(BaseModel):
    target_skills: List[str] = Field(..., description="List of target skills to develop")
    learning_style_preference: Optional[str] = Field(None, description="Preferred learning style")
    max_duration_weeks: Optional[int] = Field(None, description="Maximum duration in weeks")
    max_budget: Optional[float] = Field(None, description="Maximum budget for learning")

class SkillAnalysisRequest(BaseModel):
    user_ids: Optional[List[str]] = Field(None, description="Specific users to analyze")
    department: Optional[str] = Field(None, description="Filter by department")
    role: Optional[str] = Field(None, description="Filter by role")
    skill_category: Optional[str] = Field(None, description="Filter by skill category")
    min_gap_percentage: Optional[float] = Field(0, description="Minimum gap percentage threshold")

# Helper functions to convert dataclasses to response models
def _convert_skill_assessment(assessment: SkillAssessment) -> SkillAssessmentResponse:
    return SkillAssessmentResponse(
        skill_name=assessment.skill_name,
        category=assessment.category.value,
        current_level=assessment.current_level,
        required_level=assessment.required_level,
        gap_percentage=assessment.gap_percentage,
        priority=assessment.priority,
        assessment_date=assessment.assessment_date,
        confidence_score=assessment.confidence_score
    )

def _convert_skill_demand(demand: SkillDemand) -> SkillDemandResponse:
    return SkillDemandResponse(
        skill_name=demand.skill_name,
        category=demand.category.value,
        current_demand=demand.current_demand,
        predicted_demand_12m=demand.predicted_demand_12m,
        predicted_demand_24m=demand.predicted_demand_24m,
        growth_rate=demand.growth_rate,
        market_trend=demand.market_trend,
        industry_relevance=demand.industry_relevance
    )

def _convert_learning_recommendation(rec: LearningRecommendation) -> LearningRecommendationResponse:
    return LearningRecommendationResponse(
        skill_name=rec.skill_name,
        learning_style=rec.learning_style.value,
        recommended_resources=[
            LearningResourceResponse(
                name=resource["name"],
                provider=resource["provider"],
                duration=resource["duration"],
                cost=resource["cost"],
                style=resource["style"]
            )
            for resource in rec.recommended_resources
        ],
        estimated_duration=rec.estimated_duration,
        difficulty_level=rec.difficulty_level,
        completion_probability=rec.completion_probability,
        expected_improvement=rec.expected_improvement,
        cost_estimate=rec.cost_estimate
    )

def _convert_development_program(program: DevelopmentProgram) -> DevelopmentProgramResponse:
    return DevelopmentProgramResponse(
        program_name=program.program_name,
        target_skills=program.target_skills,
        duration_weeks=program.duration_weeks,
        delivery_method=program.delivery_method,
        provider=program.provider,
        estimated_cost=program.estimated_cost,
        expected_roi=program.expected_roi,
        success_rate=program.success_rate,
        prerequisites=program.prerequisites
    )

def _convert_career_trajectory(trajectory: CareerTrajectory) -> CareerTrajectoryResponse:
    return CareerTrajectoryResponse(
        current_role=trajectory.current_role,
        target_role=trajectory.target_role,
        time_to_promotion=trajectory.time_to_promotion,
        required_skills=[
            SkillRequirementResponse(
                skill_name=skill["skill"],
                required_level=skill["required_level"],
                current_level=skill["current_level"],
                gap_percentage=skill["gap"]
            )
            for skill in trajectory.required_skills
        ],
        skill_development_plan=[
            _convert_learning_recommendation(rec)
            for rec in trajectory.skill_development_plan
        ],
        promotion_probability=trajectory.promotion_probability,
        salary_impact=trajectory.salary_impact
    )

# API Endpoints

@check_rate_limit(identifier="public", limit_name="public")
@router.get("/individual/skill-gaps", response_model=List[SkillAssessmentResponse])
async def get_individual_skill_gaps(
    user_id: Optional[str] = Query(None, description="User ID to analyze (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill gap analysis for an individual user.
    """
    try:
        analyzer = SkillGapAnalyzer(db)
        target_user_id = user_id if user_id else current_user.id

        # Authorization check - users can only see their own analysis unless admin
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view skill gaps for this user"
            )

        skill_gaps = await analyzer.analyze_individual_skill_gaps(target_user_id)

        return [_convert_skill_assessment(gap) for gap in skill_gaps]

    except Exception as
@check_rate_limit(identifier="public", limit_name="public")
e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/individual/summary", response_model=SkillGapSummaryResponse)
async def get_individual_skill_summary(
    user_id: Optional[str] = Query(None, description="User ID to analyze (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill gap summary for an individual user.
    """
    try:
        analyzer = SkillGapAnalyzer(db)
        target_user_id = user_id if user_id else current_user.id

        # Authorization check
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view skill summary for this user"
            )

        skill_gaps = await analyzer.analyze_individual_skill_gaps(target_user_id)

        critical_gaps = len([gap for gap in skill_gaps if gap.priority == "critical"])
        high_priority_gaps = len([gap for gap in skill_gaps if gap.priority == "high"])
        medium_priority_gaps = len([gap for gap in skill_gaps if gap.priority == "medium"])
        low_priority_gaps = len([gap for gap in skill_gaps if gap.priority == "low"])

        average_gap_size = sum(gap.gap_percentage for gap in skill_gaps) / len(skill_gaps) if skill_gaps else 0

        return SkillGapSummaryResponse(
            critical_gaps=critical_gaps,
            high_priority_gaps=high_priority_gaps,
            medium_priority_gaps=medium_priority_gaps,
            low_priority_gaps=low_priority_gaps,
            average_gap_size=average_gap_size,
            total
@check_rate_limit(identifier="public", limit_name="public")
_assessments=len(skill_gaps)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organization/skill-gaps", response_model=OrganizationalSkillGapResponse)
async def get_organizational_skill_gaps(
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get skill gap analysis for the entire organization or filtered subset.
    """
    try:
        # Authorization check - require admin or team lead role
        if not (current_user.is_superuser or current_user.role in ["admin", "team_lead"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view organizational skill analysis"
            )

        analyzer = SkillGapAnalyzer(db)
        org_id = current_user.organization_id

        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="User is not associated with an organization"
            )

        org_gaps = await analyzer.analyze_organizational_skill_gaps(org_id)

        # Convert department gaps
        converted_department_gaps = {}
        for dept, gaps in org_gaps["department_gaps"].items():
            converted_department_gaps[dept] = [_convert_skill_assessment(gap) for gap in gaps]

        # Convert critical gaps
        converted_critical_gaps = [_convert_skill_assessment(gap) for gap in org_gaps["critical_gaps"]]

        return OrganizationalSkillGapResponse(
            overall_gaps=org_gaps["overall_gaps"],
            department_gaps=converted_department_gaps,
            critical_gaps=converted_critical_gaps,
            skill_supply_demand=org_gaps["skill_supply_demand"],
            recommendations=org_gaps["recommendations"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organization/future-demands", response_model=List[SkillDemandResponse])
async def get_future_skill_demands(
    timeframe_months: int = Query(24, ge=1, le=60, description="Timeframe in months for prediction"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get future skill demand predictions for the organization.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "team_lead"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view organizational skill predictions"
            )

        analyzer = SkillGapAnalyzer(db)
        org_id = current_user.organization_id

        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="User is not associated with an organization"
            )

        skill_demands = await analyzer.predict_future_skill_demands(org_id, timeframe_months)

        return [_convert_skill_demand(demand) for demand in skill_demands]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/individual/learning-path", response_model=List[LearningRecommendationResponse])
async def generate_learning_path(
    request: LearningPathRequest,
    user_id: Optional[str] = Query(None, description="User ID to generate path for (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate personalized learning recommendations for target skills.
    """
    try:
        analyzer = SkillGapAnalyzer(db)
        target_user_id = user_id if user_id else current_user.id

        # Authorization check
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to generate learning path for this user"
            )

        recommendations = await analyzer.recommend_learning_path(target_user_id, request.target_skills)

        # Apply filters if specified
        if request.max_duration_weeks:
            recommendations = [
                rec for rec in recommendations
                if rec.estimated_duration <= request.max_duration_weeks * 7
            ]

        if request.max_budget:
            recommendations = [
                rec for rec in recommendations
                if not rec.cost_estimate or rec.cost_estimate <= request.max_budget
            ]

        return [_convert_learning_recommendation(rec) for rec in recommendations]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/individual/development-programs", response_model=List[DevelopmentProgramResponse])
async def get_development_programs(
    user_id: Optional[str] = Query(None, description="User ID to get programs for (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recommended development programs for a user.
    """
    try:
        analyzer = SkillGapAnalyzer(db)
        target_user_id = user_id if user_id else current_user.id

        # Authorization check
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view development programs for this user"
            )

        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="User is not associated with an organization"
            )

        programs = await analyzer.recommend_development_programs(target_user_id, org_id)

        return [_convert_development_program(program) for program in programs]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/individual/career-trajectories", response_model=List[CareerTrajectoryResponse])
async def get_career_trajectories(
    user_id: Optional[str] = Query(None, description="User ID to analyze (defaults to current user)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get career trajectory analysis with development requirements.
    """
    try:
        analyzer = SkillGapAnalyzer(db)
        target_user_id = user_id if user_id else current_user.id

        # Authorization check
        if user_id and user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view career trajectories for this user"
            )

        trajectories = await analyzer.analyze_career_trajectories(target_user_id)

        return [_convert_career_trajectory(trajectory) for trajectory in trajectories]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/skills/categories", response_model=List[str])
async def get_skill_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available skill categories.
    """
    try:
        from app.services.skill_gap_analysis import SkillCategory
        return [category.value for category in SkillCategory]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning/styles", response_model=List[str])
async def get_learning_styles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available learning styles.
    """
    try:
        from app.services.skill_gap_analysis import LearningStyle
        return [style.value for style in LearningStyle]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/batch", response_model=Dict[str, List[SkillAssessmentResponse]])
async def batch_skill_analysis(
    request: SkillAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform batch skill gap analysis for multiple users or organization.
    """
    try:
        # Authorization check - require admin role for batch analysis
        if not (current_user.is_superuser or current_user.role in ["admin", "hr"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to perform batch skill analysis"
            )

        analyzer = SkillGapAnalyzer(db)
        results = {}

        if request.user_ids:
            # Analyze specific users
            for user_id in request.user_ids:
                try:
                    user_gaps = await analyzer.analyze_individual_skill_gaps(user_id)

                    # Apply filters
                    if request.min_gap_percentage:
                        user_gaps = [
                            gap for gap in user_gaps
                            if gap.gap_percentage >= request.min_gap_percentage
                        ]

                    if request.skill_category:
                        user_gaps = [
                            gap for gap in user_gaps
                            if gap.category.value == request.skill_category
                        ]

                    results[user_id] = [_convert_skill_assessment(gap) for gap in user_gaps]

                except Exception as e:
                    results[user_id] = {"error": str(e)}

        else:
            # Analyze organization
            org_id = current_user.organization_id
            if not org_id:
                raise HTTPException(
                    status_code=400,
                    detail="User is not associated with an organization"
                )

            org_analysis = await analyzer.analyze_organizational_skill_gaps(org_id)

            # Apply filters to critical gaps
            filtered_gaps = org_analysis["critical_gaps"]

            if request.min_gap_percentage:
                filtered_gaps = [
                    gap for gap in filtered_gaps
                    if gap.gap_percentage >= request.min_gap_percentage
                ]

            if request.skill_category:
                filtered_gaps = [
                    gap for gap in filtered_gaps
                    if gap.category.value == request.skill_category
                ]

            results["organization"] = [_convert_skill_assessment(gap) for gap in filtered_gaps]
            results["departments"] = {
                dept: [_convert_skill_assessment(gap) for gap in gaps]
                for dept, gaps in org_analysis["department_gaps"].items()
            }

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/skill-distribution", response_model=Dict[str, Any])
async def get_skill_distribution_analytics(
    organization_id: Optional[str] = Query(None, description="Organization ID to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics on skill distribution across the organization.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "team_lead"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view skill distribution analytics"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        analyzer = SkillGapAnalyzer(db)
        org_gaps = await analyzer.analyze_organizational_skill_gaps(org_id)

        # Generate distribution analytics
        analytics = {
            "category_distribution": {},
            "priority_distribution": {},
            "gap_size_distribution": {
                "small": 0,    # 0-15%
                "medium": 0,   # 15-30%
                "large": 0,    # 30-50%
                "critical": 0  # >50%
            },
            "top_critical_skills": [],
            "department_comparison": {},
            "skill_health_score": 0
        }

        # Analyze all skill gaps
        all_gaps = []
        for dept_gaps in org_gaps["department_gaps"].values():
            all_gaps.extend(dept_gaps)
        all_gaps.extend(org_gaps["critical_gaps"])

        # Category distribution
        for gap in all_gaps:
            category = gap.category.value
            analytics["category_distribution"][category] = analytics["category_distribution"].get(category, 0) + 1

        # Priority distribution
        for gap in all_gaps:
            priority = gap.priority
            analytics["priority_distribution"][priority] = analytics["priority_distribution"].get(priority, 0) + 1

        # Gap size distribution
        for gap in all_gaps:
            if gap.gap_percentage <= 15:
                analytics["gap_size_distribution"]["small"] += 1
            elif gap.gap_percentage <= 30:
                analytics["gap_size_distribution"]["medium"] += 1
            elif gap.gap_percentage <= 50:
                analytics["gap_size_distribution"]["large"] += 1
            else:
                analytics["gap_size_distribution"]["critical"] += 1

        # Top critical skills
        critical_skills = sorted(
            [gap for gap in all_gaps if gap.priority in ["critical", "high"]],
            key=lambda x: x.gap_percentage,
            reverse=True
        )[:10]

        analytics["top_critical_skills"] = [
            {
                "skill_name": gap.skill_name,
                "gap_percentage": gap.gap_percentage,
                "category": gap.category.value,
                "affected_users": sum(
                    1 for dept_gaps in org_gaps["department_gaps"].values()
                    for dept_gap in dept_gaps
                    if dept_gap.skill_name == gap.skill_name
                )
            }
            for gap in critical_skills
        ]

        # Department comparison
        for dept, gaps in org_gaps["department_gaps"].items():
            avg_gap = sum(gap.gap_percentage for gap in gaps) / len(gaps) if gaps else 0
            analytics["department_comparison"][dept] = {
                "total_gaps": len(gaps),
                "average_gap": round(avg_gap, 1),
                "critical_gaps": len([gap for gap in gaps if gap.priority == "critical"])
            }

        # Overall skill health score (0-100, higher is better)
        if all_gaps:
            avg_gap = sum(gap.gap_percentage for gap in all_gaps) / len(all_gaps)
            analytics["skill_health_score"] = max(0, 100 - avg_gap)

        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
