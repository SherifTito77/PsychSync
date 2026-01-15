"""
Succession Planning API Endpoints

Advanced succession planning and leadership pipeline management endpoints.
"""

from typing import List, Optional, Dict, Any

from app.middleware.rate_limiter import check_rate_limit
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.succession_planning import (
    SuccessionPlanner,
    RoleProfile,
    CandidateProfile,
    SuccessionCandidate,
    LeadershipPipeline,
    SuccessionScenario,
    ReadinessLevel,
    RiskLevel
)
from pydantic import BaseModel, Field

router = APIRouter()

# Request/Response Models
class LeadershipPipelineResponse(BaseModel):
    pipeline_level: str
    total_positions: int
    ready_candidates: int
    gap_percentage: float
    bench_strength: float
    risk_level: str
    development_recommendations: List[str]

class CandidateProfileResponse(BaseModel):
    user_id: str
    current_role: str
    readiness_level: str
    readiness_score: float
    leadership_potential: float
    mobility_score: float
    risk_score: float
    promotion_timeline: int
    retention_risk: float

class SuccessionCandidateResponse(BaseModel):
    candidate: CandidateProfileResponse
    target_role: Dict[str, str]
    match_score: float
    success_probability: float
    gap_analysis: Dict[str, float]

class SuccessionScenarioRequest(BaseModel):
    scenario_name: str = Field(..., description="Name of the succession scenario")
    departing_roles: List[str] = Field(..., description="Roles that will become vacant")
    timeline_months: int = Field(..., description="Timeline for scenario in months")
    departure_reason: Optional[str] = Field(None, description="Reason for departure")
    include_external_hiring: bool = Field(False, description="Whether to consider external hiring")

class SuccessionScenarioResponse(BaseModel):
    scenario_name: str
    timeline_months: int
    readiness_status: str
    business_impact: Dict[str, float]
    financial_risk: float
    operational_risk: float
    required_actions: List[str]

class DevelopmentProgramRequest(BaseModel):
    program_name: str = Field(..., description="Name of the development program")
    target_level: str = Field(..., description="Target leadership level")
    duration_months: int = Field(..., description="Program duration in months")
    budget: float = Field(..., description="Program budget")
    participant_ids: List[str] = Field(..., description="List of participant user IDs")
    objectives: List[str] = Field(..., description="Program objectives")
    success_metrics: List[str] = Field(..., description="Success metrics")

class DashboardMetricsResponse(BaseModel):
    overall_bench_strength: float
    leadership_risk_score: float
    development_investment: float
    expected_roi: float
    diversity_score: float
    readiness_timeline: int

class SuccessionDashboardResponse(BaseModel):
    pipeline_analysis: Dict[str, LeadershipPipelineResponse]
    scenario_results: List[SuccessionScenarioResponse]
    risk_assessment: Dict[str, Any]
    diversity_metrics: Dict[str, Any]
    development_programs: Dict[str, Any]
    key_metrics: DashboardMetricsResponse
    recommendations: List[str]
    updated_date: str

class GapAnalysisRequest(BaseModel):
    role_id: str = Field(..., description="Target role for gap analysis")
    competency_categories: Optional[List[str]] = Field(None, description="Specific competency categories to analyze")
    min_gap_threshold: float = Field(10, description="Minimum gap percentage to consider")
    include_development_plan: bool = Field(True, description="Include development plan recommendations")

# Helper functions to convert dataclasses to response models
def _convert_leadership_pipeline(pipeline: LeadershipPipeline) -> LeadershipPipelineResponse:
    return LeadershipPipelineResponse(
        pipeline_level=pipeline.pipeline_level,
        total_positions=pipeline.total_positions,
        ready_candidates=pipeline.ready_candidates,
        gap_percentage=pipeline.gap_percentage,
        bench_strength=pipeline.bench_strength,
        risk_level=pipeline.risk_level.value,
        development_recommendations=pipeline.development_recommendations
    )

def _convert_candidate_profile(candidate: CandidateProfile) -> CandidateProfileResponse:
    return CandidateProfileResponse(
        user_id=candidate.user_id,
        current_role=candidate.current_role,
        readiness_level=candidate.readiness_level.value,
        readiness_score=candidate.readiness_score,
        leadership_potential=candidate.leadership_potential,
        mobility_score=candidate.mobility_score,
        risk_score=candidate.risk_score,
        promotion_timeline=candidate.promotion_timeline,
        retention_risk=candidate.retention_risk
    )

def _convert_succession_candidate(candidate: SuccessionCandidate) -> SuccessionCandidateResponse:
    return SuccessionCandidateResponse(
        candidate=_convert_candidate_profile(candidate.candidate),
        target_role={
            "role_name": candidate.target_role.role_name,
            "level": candidate.target_role.level,
            "department": candidate.target_role.department
        },
        match_score=candidate.match_score,
        success_probability=candidate.success_probability,
        gap_analysis=candidate.gap_analysis
    )

def _convert_succession_scenario(scenario: SuccessionScenario) -> SuccessionScenarioResponse:
    return SuccessionScenarioResponse(
        scenario_name=scenario.scenario_name,
        timeline_months=scenario.timeline_months,
        readiness_status=scenario.readiness_status,
        business_impact=scenario.business_impact,
        financial_risk=scenario.financial_risk,
        operational_risk=scenario.operational_risk,
        required_actions=scenario.required_actions
    )

# API Endpoints

@check_rate_limit(identifier="public", limit_name="public")
@router.get("/leadership-pipeline", response_model=List[LeadershipPipelineResponse])
async def get_leadership_pipeline(
    organization_id: Optional[str] = Query(None, description="Organization ID to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive leadership pipeline analysis.
    """
    try:
        # Authorization check - require senior leadership or HR role
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "executive"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view leadership pipeline analysis"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        pipeline_analysis = await planner.analyze_leadership_pipeline(org_id)

        return [_convert_leadership_pipeline(pipeline) for pipeline in pipeline_analysis.values()]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/succession-candidates/{role_id}", response_model=List[SuccessionCandidateResponse])
async def get_succession_candidates(
    role_id: str,
    include_external: bool = Query(False, description="Include external candidates"),
    min_match_score: float = Query(50, description="Minimum match score threshold"),
    organization_id: Optional[str] = Query(None, description="Organization ID to search within"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get succession candidates for a specific role.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "executive"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view succession candidates"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        candidates = await planner.identify_succession_candidates(
            role_id, org_id, include_external
        )

        # Filter by minimum match score
        filtered_candidates = [
            candidate for candidate in candidates
            if candidate.match_score >= min_match_score
        ]

        return [_convert_succession_candidate(candidate)
@check_rate_limit(identifier="public", limit_name="public")
 for candidate in filtered_candidates]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gap-analysis", response_model=Dict[str, Any])
async def analyze_skill_gaps(
    request: GapAnalysisRequest,
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze skill gaps for succession planning.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to perform succession gap analysis"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        candidates = await planner.identify_succession_candidates(request.role_id, org_id)

        # Analyze gaps across all candidates
        gap_analysis = {
            "role_id": request.role_id,
            "total_candidates": len(candidates),
            "critical_gaps": {},
            "readiness_distribution": {
                "ready_now": 0,
                "ready_1_2_years": 0,
                "ready_3_5_years": 0,
                "potential": 0
            },
            "competency_gaps": {},
            "development_recommendations": []
        }

        # Analyze readiness distribution
        for candidate in candidates:
            readiness = candidate.candidate.readiness_level.value
            gap_analysis["readiness_distribution"][readiness] += 1

            # Aggregate competency gaps
            for competency, gap in candidate.gap_analysis.items():
                if competency not in gap_analysis["competency_gaps"]:
                    gap_analysis["competency_gaps"][competency] = []
                gap_analysis["competency_gaps"][competency].append(gap)

                # Identify critical gaps (above threshold)
                if gap >= request.min_gap_threshold:
                    if competency not in gap_analysis["critical_gaps"]:
                        gap_analysis["critical_gaps"][competency] = []
                    gap_analysis["critical_gaps"][competency].append({
                        "candidate_id": candidate.candidate.user_id,
                        "gap_size": gap,
                        "current_level": 100 - gap,  # Simplified calculation
                        "required_level": 100
                    })

        # Calculate average gaps
        for competency, gaps in gap_analysis["competency_gaps"].items():
            gap_analysis["competency_gaps"][competency] = {
                "average_gap": sum(gaps) / len(gaps),
                "max_gap": max(gaps),
                "min_gap": min(gaps),
                "candidates_with_gap": len([g for g in gaps if g >= request.min_gap_threshold])
            }

        # Generate development recommendations if requested
        if request.include_development_plan:
            gap_analysis["development_recommendations"] = await _generate_gap_recommendations(
                gap_analysis["critical_gaps"], org_id
            )

        return gap_analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate-scenarios", response_model=List[SuccessionScenarioResponse])
async def simulate_succession_scenarios(
    scenarios: List[SuccessionScenarioRequest],
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulate succession scenarios and assess organizational readiness.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "executive"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to simulate succession scenarios"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)

        # Convert request format
        scenario_configs = [
            {
                "scenario_name": scenario.scenario_name,
                "departing_roles": scenario.departing_roles,
                "timeline_months": scenario.timeline_months,
                "departure_reason": scenario.departure_reason,
                "include_external_hiring": scenario.include_external_hiring
            }
            for scenario in scenarios
        ]

        scenario_results = await planner.simulate_succession_scenarios(org_id, scenario_configs)

        return [_convert_succession_scenario(scenario) for scenario in scenario_results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/development-programs", response_model=Dict[str, Any])
async def create_development_programs(
    target_roles: Optional[List[str]] = Query(None, description="Target roles for development"),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create comprehensive development programs for succession candidates.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create development programs"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        development_programs = await planner.create_development_programs(org_id, target_roles)

        return development_programs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard", response_model=SuccessionDashboardResponse)
async def get_succession_dashboard(
    time_horizon_months: int = Query(24, description="Time horizon for analysis in months"),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive succession planning dashboard.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "executive"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view succession dashboard"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        dashboard_data = await planner.generate_succession_dashboard(org_id, time_horizon_months)

        # Convert response format
        return SuccessionDashboardResponse(
            pipeline_analysis={
                level: _convert_leadership_pipeline(pipeline)
                for level, pipeline in dashboard_data["pipeline_analysis"].items()
            },
            scenario_results=[
                _convert_succession_scenario(scenario)
                for scenario in dashboard_data["scenario_results"]
            ],
            risk_assessment=dashboard_data["risk_assessment"],
            diversity_metrics=dashboard_data["diversity_metrics"],
            development_programs=dashboard_data["development_programs"],
            key_metrics=DashboardMetricsResponse(**dashboard_data["key_metrics"]),
            recommendations=dashboard_data["recommendations"],
            updated_date=dashboard_data["updated_date"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-assessment", response_model=Dict[str, Any])
async def get_succession_risk_assessment(
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    include_mitigation_strategies: bool = Query(True, description="Include risk mitigation strategies"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive succession risk assessment.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr", "executive"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view succession risk assessment"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)
        pipeline_analysis = await planner.analyze_leadership_pipeline(org_id)

        # Calculate comprehensive risk metrics
        risk_assessment = {
            "overall_risk_score": 0,
            "risk_by_level": {},
            "key_risk_factors": [],
            "critical_roles": [],
            "mitigation_strategies": [] if include_mitigation_strategies else None,
            "risk_trends": [],
            "compliance_risks": []
        }

        # Calculate risk by level
        total_risk = 0
        level_count = 0

        for level, pipeline in pipeline_analysis.items():
            level_risk = 0

            # Risk factors calculation
            gap_risk = pipeline.gap_percentage / 100
            bench_risk = (100 - pipeline.bench_strength) / 100

            # Risk level weighting
            risk_weight = {
                "executive": 1.0,
                "senior_management": 0.8,
                "middle_management": 0.6,
                "team_lead": 0.4
            }.get(level.lower(), 0.5)

            level_risk = (gap_risk + bench_risk) / 2 * risk_weight * 100

            risk_assessment["risk_by_level"][level] = {
                "risk_score": level_risk,
                "risk_level": pipeline.risk_level.value,
                "gap_risk": gap_risk * 100,
                "bench_strength_risk": bench_risk * 100,
                "position_risk": (pipeline.gap_percentage / 100) * pipeline.total_positions
            }

            total_risk += level_risk
            level_count += 1

            # Identify critical roles (high gap percentage + low bench strength)
            if pipeline.gap_percentage > 50 and pipeline.bench_strength < 60:
                risk_assessment["critical_roles"].append({
                    "level": level,
                    "gap_percentage": pipeline.gap_percentage,
                    "bench_strength": pipeline.bench_strength,
                    "total_positions": pipeline.total_positions,
                    "ready_candidates": pipeline.ready_candidates
                })

        risk_assessment["overall_risk_score"] = total_risk / level_count if level_count > 0 else 0

        # Identify key risk factors
        risk_assessment["key_risk_factors"] = [
            {
                "factor": "Leadership Continuity",
                "impact": "High",
                "description": "Risk of leadership gaps in critical positions",
                "mitigation": "Accelerated development programs"
            },
            {
                "factor": "Talent Retention",
                "impact": "Medium",
                "description": "Risk of losing high-potential candidates",
                "mitigation": "Career path development and retention programs"
            },
            {
                "factor": "Skill Obsolescence",
                "impact": "Medium",
                "description": "Risk of skills becoming outdated",
                "mitigation": "Continuous learning and upskilling programs"
            }
        ]

        # Add mitigation strategies if requested
        if include_mitigation_strategies:
            risk_assessment["mitigation_strategies"] = [
                {
                    "strategy": "Accelerated Leadership Development",
                    "priority": "High",
                    "timeline": "12-18 months",
                    "estimated_cost": "$150,000",
                    "expected_impact": "40% risk reduction"
                },
                {
                    "strategy": "Succession Planning Documentation",
                    "priority": "Medium",
                    "timeline": "3-6 months",
                    "estimated_cost": "$25,000",
                    "expected_impact": "20% risk reduction"
                },
                {
                    "strategy": "External Talent Pipeline",
                    "priority": "Medium",
                    "timeline": "6-12 months",
                    "estimated_cost": "$75,000",
                    "expected_impact": "30% risk reduction"
                }
            ]

        return risk_assessment

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/readiness-timeline", response_model=Dict[str, Any])
async def get_readiness_timeline(
    role_id: Optional[str] = Query(None, description="Specific role to analyze"),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get readiness timeline for succession candidates.
    """
    try:
        # Authorization check
        if not (current_user.is_superuser or current_user.role in ["admin", "hr"]):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view readiness timeline"
            )

        org_id = organization_id if organization_id else current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="Organization ID is required"
            )

        planner = SuccessionPlanner(db)

        if role_id:
            # Analyze specific role
            candidates = await planner.identify_succession_candidates(role_id, org_id)
            role_profile = planner.role_profiles.get(role_id)

            if not role_profile:
                raise HTTPException(
                    status_code=404,
                    detail=f"Role profile not found for role_id: {role_id}"
                )

            timeline_data = {
                "role_name": role_profile.role_name,
                "role_level": role_profile.level,
                "candidates": []
            }

            for candidate in candidates:
                candidate_data = {
                    "user_id": candidate.candidate.user_id,
                    "current_role": candidate.candidate.current_role,
                    "readiness_level": candidate.candidate.readiness_level.value,
                    "readiness_score": candidate.candidate.readiness_score,
                    "promotion_timeline": candidate.candidate.promotion_timeline,
                    "success_probability": candidate.success_probability,
                    "development_needs": candidate.gap_analysis
                }
                timeline_data["candidates"].append(candidate_data)

            # Sort by promotion timeline
            timeline_data["candidates"].sort(key=lambda x: x["promotion_timeline"])

            return timeline_data

        else:
            # Analyze all critical roles
            pipeline_analysis = await planner.analyze_leadership_pipeline(org_id)
            timeline_data = {
                "overall_timeline": {},
                "readiness_distribution": {
                    "ready_now": [],
                    "ready_1_2_years": [],
                    "ready_3_5_years": [],
                    "potential": []
                }
            }

            # Analyze each pipeline level
            for level, pipeline in pipeline_analysis.items():
                role_profile = planner.role_profiles.get(level.lower().replace(" ", "_"))
                if role_profile:
                    candidates = await planner.identify_succession_candidates(
                        role_profile.role_id, org_id
                    )

                    ready_candidates = [
                        candidate for candidate in candidates
                        if candidate.candidate.readiness_level in [
                            ReadinessLevel.READY_NOW, ReadinessLevel.READY_1_2_YEARS
                        ]
                    ]

                    timeline_data["overall_timeline"][level] = {
                        "total_positions": pipeline.total_positions,
                        "ready_candidates": len(ready_candidates),
                        "average_timeline": sum(
                            candidate.candidate.promotion_timeline for candidate in ready_candidates
                        ) / len(ready_candidates) if ready_candidates else 0,
                        "bench_strength": pipeline.bench_strength
                    }

                    # Categorize candidates by readiness
                    for candidate in candidates:
                        readiness_category = {
                            ReadinessLevel.READY_NOW: "ready_now",
                            ReadinessLevel.READY_1_2_YEARS: "ready_1_2_years",
                            ReadinessLevel.READY_3_5_YEARS: "ready_3_5_years",
                            ReadinessLevel.POTENTIAL: "potential"
                        }.get(candidate.candidate.readiness_level, "potential")

                        timeline_data["readiness_distribution"][readiness_category].append({
                            "user_id": candidate.candidate.user_id,
                            "current_role": candidate.candidate.current_role,
                            "target_role": role_profile.role_name,
                            "timeline_months": candidate.candidate.promotion_timeline,
                            "success_probability": candidate.success_probability
                        })

            return timeline_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def _generate_gap_recommendations(
    critical_gaps: Dict[str, List[Dict]],
    organization_id: str
) -> List[Dict[str, Any]]:
    """Generate recommendations for addressing critical skill gaps"""
    recommendations = []

    for competency, gap_data in critical_gaps.items():
        avg_gap = sum(gap["gap_size"] for gap in gap_data) / len(gap_data)
        affected_candidates = len(gap_data)

        recommendation = {
            "competency": competency,
            "average_gap": avg_gap,
            "affected_candidates": affected_candidates,
            "recommendation_type": "development_program",
            "suggested_actions": [
                f"Create targeted {competency.replace('_', ' ')} development program",
                "Implement mentorship with subject matter experts",
                "Provide stretch assignments to build competency"
            ],
            "estimated_cost": avg_gap * affected_candidates * 1000,  # Simplified calculation
            "estimated_timeline": f"{int(avg_gap * 0.5)} months",
            "priority": "High" if avg_gap > 30 else "Medium"
        }

        recommendations.append(recommendation)

    # Sort by average gap size
    recommendations.sort(key=lambda x: x["average_gap"], reverse=True)

    return recommendations[:5]  # Return top 5 recommendations
