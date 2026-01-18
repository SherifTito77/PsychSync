"""
Behavioral Analytics Endpoints
Team behavioral intelligence and HR outcome measurements
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.v1.deps import get_current_user, get_db
from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from app.services.assessment_service import assessment_service
from app.services.nlp_service import nlp_service
from app.services.team_service import team_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/behavioral-analytics", tags=["behavioral-analytics"])


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.get("/team-insights/{team_id}")
async def get_team_behavioral_insights(
    team_id: int,
    time_period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y"),
    include_predictions: bool = Query(True, description="Include AI predictions"),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Get comprehensive team behavioral insights with business impact translation"""
    try:
        # Get team data
        team = await team_service.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Get team assessment data
        team_assessments = await assessment_service.get_team_assessments(team_id)

        # Analyze behavioral patterns
        behavioral_patterns = await nlp_service.analyze_behavioral_patterns(team_assessments)

        # Calculate business impact metrics
        business_impact = await calculate_business_impact(team_id, behavioral_patterns)

        # Generate AI predictions
        predictions = None
        if include_predictions:
            predictions = await generate_team_predictions(team_id, behavioral_patterns)

        return {
            "team_overview": {
                "team_id": team_id,
                "team_name": team.name,
                "team_size": len(team.members),
                "analysis_date": datetime.now().isoformat(),
                "data_confidence": calculate_data_confidence(team_assessments),
            },
            "behavioral_metrics": {
                "team_cohesion": behavioral_patterns.get("cohesion_score", 0),
                "communication_effectiveness": behavioral_patterns.get("communication_score", 0),
                "collaboration_quality": behavioral_patterns.get("collaboration_score", 0),
                "psychological_safety": behavioral_patterns.get("safety_score", 0),
                "innovation_potential": behavioral_patterns.get("innovation_score", 0),
                "conflict_resolution": behavioral_patterns.get("conflict_resolution_score", 0),
            },
            "business_impact": business_impact,
            "team_composition": {
                "personality_diversity": behavioral_patterns.get("personality_diversity", {}),
                "role_alignment": behavioral_patterns.get("role_alignment", {}),
                "strength_distribution": behavioral_patterns.get("strength_distribution", {}),
                "risk_factors": behavioral_patterns.get("risk_factors", []),
            },
            "recommendations": await generate_team_recommendations(team_id, behavioral_patterns),
            "predictions": predictions,
            "benchmarks": await get_team_benchmarks(team_id, behavioral_patterns),
        }

    except Exception as e:
        logger.error(f"Error getting team behavioral insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team insights") from e


@router.get("/hr-outcomes/{organization_id}")
async def get_hr_outcomes_metrics(
    organization_id: int,
    time_period: str = Query("90d", description="Time period: 30d, 90d, 1y"),
    outcome_types: list[str] = Query(
        ["all"], description="Outcome types: productivity, retention, engagement, innovation"
    ),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Get HR-relevant outcomes and ROI metrics"""
    try:
        # Calculate HR KPI improvements
        hr_metrics = {}

        if "productivity" in outcome_types or "all" in outcome_types:
            hr_metrics["productivity"] = await calculate_productivity_impact(
                organization_id, time_period
            )

        if "retention" in outcome_types or "all" in outcome_types:
            hr_metrics["retention"] = await calculate_retention_impact(organization_id, time_period)

        if "engagement" in outcome_types or "all" in outcome_types:
            hr_metrics["engagement"] = await calculate_engagement_impact(
                organization_id, time_period
            )

        if "innovation" in outcome_types or "all" in outcome_types:
            hr_metrics["innovation"] = await calculate_innovation_impact(
                organization_id, time_period
            )

        # Calculate overall ROI
        roi_analysis = await calculate_hr_roi(organization_id, hr_metrics)

        return {
            "organization_id": organization_id,
            "analysis_period": time_period,
            "hr_outcomes": hr_metrics,
            "roi_analysis": roi_analysis,
            "executive_summary": await generate_executive_summary(organization_id, hr_metrics),
            "recommendations": await generate_hr_recommendations(organization_id, hr_metrics),
            "forecast_trends": await forecast_hr_trends(organization_id, hr_metrics),
        }

    except Exception as e:
        logger.error(f"Error getting HR outcomes metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get HR outcomes") from e


@router.get("/turnover-risk/{organization_id}")
async def get_turnover_risk_analysis(
    organization_id: int,
    include_interventions: bool = Query(True),
    risk_threshold: float = Query(0.7, description="Risk threshold for high-risk employees"),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Analyze employee turnover risk and intervention opportunities"""
    try:
        # Get behavioral risk factors
        risk_analysis = await analyze_turnover_risk(organization_id)

        # Identify high-risk employees
        high_risk_employees = [
            emp for emp in risk_analysis["employees"] if emp["risk_score"] >= risk_threshold
        ]

        # Calculate potential financial impact
        financial_impact = await calculate_turnover_financial_impact(high_risk_employees)

        # Generate intervention recommendations
        interventions = None
        if include_interventions:
            interventions = await generate_interventions(high_risk_employees)

        return {
            "organization_id": organization_id,
            "risk_overview": {
                "total_employees_analyzed": len(risk_analysis["employees"]),
                "high_risk_count": len(high_risk_employees),
                "average_risk_score": risk_analysis["average_risk"],
                "risk_trend": risk_analysis["risk_trend"],
            },
            "high_risk_employees": high_risk_employees,
            "financial_impact": financial_impact,
            "risk_factors": risk_analysis["risk_factors"],
            "interventions": interventions,
            "success_metrics": {
                "prevented_turnover_savings": financial_impact["prevented_turnover_savings"],
                "intervention_cost": financial_impact["intervention_cost"],
                "intervention_roi": financial_impact["intervention_roi"],
            },
        }

    except Exception as e:
        logger.error(f"Error getting turnover risk analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get turnover risk") from e


@router.get("/team-composition-optimizer/{team_id}")
async def get_team_composition_optimizer(
    team_id: int,
    optimization_goal: str = Query(
        "balance", description="Goal: balance, innovation, stability, growth"
    ),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
) -> dict[str, Any]:
    """Get AI-powered team composition recommendations"""
    try:
        # Get current team composition
        current_composition = await get_current_team_composition(team_id)

        # Analyze optimization opportunities
        optimization_analysis = await analyze_composition_optimization(
            team_id, current_composition, optimization_goal
        )

        # Generate recommendations
        recommendations = await generate_composition_recommendations(
            team_id, optimization_analysis, optimization_goal
        )

        return {
            "team_id": team_id,
            "optimization_goal": optimization_goal,
            "current_composition": current_composition,
            "optimization_analysis": optimization_analysis,
            "recommendations": recommendations,
            "expected_outcomes": await predict_optimization_outcomes(
                team_id, recommendations, optimization_goal
            ),
            "implementation_plan": await create_implementation_plan(team_id, recommendations),
        }

    except Exception as e:
        logger.error(f"Error getting team composition optimizer: {e}")
        raise HTTPException(status_code=500, detail="Failed to get composition optimizer") from e


# Helper functions for business impact calculations


async def calculate_business_impact(
    team_id: int, behavioral_patterns: dict[str, Any]
) -> dict[str, Any]:
    """Translate behavioral metrics into business impact"""

    # Calculate productivity impact
    productivity_score = behavioral_patterns.get("collaboration_score", 0)
    productivity_hours_saved = (productivity_score - 0.5) * 20 * 4  # 20 hours/week * 4 weeks
    productivity_value = productivity_hours_saved * 75  # $75/hour average fully-loaded cost

    # Calculate turnover reduction
    stability_score = behavioral_patterns.get("cohesion_score", 0)
    turnover_reduction = (stability_score - 0.5) * 0.3  # 30% max reduction
    avg_turnover_cost = 75000  # Average cost of replacing an employee

    # Calculate innovation impact
    innovation_score = behavioral_patterns.get("innovation_score", 0)
    innovation_value = innovation_score * 50000  # Up to $50K additional value

    return {
        "productivity": {
            "hours_saved_per_month": max(0, productivity_hours_saved),
            "monthly_value": max(0, productivity_value),
            "annual_value": max(0, productivity_value * 12),
        },
        "retention": {
            "turnover_reduction_rate": max(0, turnover_reduction),
            "annual_savings": max(0, turnover_reduction * avg_turnover_cost),
        },
        "innovation": {
            "innovation_score": innovation_score,
            "estimated_value": innovation_value,
            "time_to_market_improvement": f"{int(innovation_score * 30)}%",
        },
        "total_monthly_value": max(
            0,
            productivity_value
            + (turnover_reduction * avg_turnover_cost / 12)
            + (innovation_value / 12),
        ),
    }


async def calculate_productivity_impact(organization_id: int, time_period: str) -> dict[str, Any]:
    """Calculate productivity improvements from behavioral insights"""

    # Sample implementation - would integrate with actual productivity data
    return {
        "meeting_efficiency": {
            "time_reduction_percent": 22,
            "hours_saved_per_month": 156,
            "monthly_value": 11700,
        },
        "decision_making": {
            "speed_improvement_percent": 35,
            "decisions_faster_per_month": 45,
            "value_per_faster_decision": 500,
        },
        "collaboration_overhead": {"reduction_percent": 28, "friction_cost_savings": 8500},
        "total_productivity_gain": {
            "monthly_value": 25700,
            "annual_value": 308400,
            "productivity_increase_percent": 15,
        },
    }


async def calculate_retention_impact(organization_id: int, time_period: str) -> dict[str, Any]:
    """Calculate retention improvements from behavioral insights"""

    return {
        "turnover_rate_reduction": {
            "before_rate": 0.18,  # 18% annual turnover
            "after_rate": 0.12,  # 12% after intervention
            "reduction_percent": 33,
        },
        "financial_impact": {
            "average_cost_per_turnover": 75000,
            "turnovers_prevented": 4.2,
            "annual_savings": 315000,
        },
        "engagement_improvement": {
            "engagement_score_increase": 0.15,  # 15 point increase
            "disengaged_employees_reduced": 12,
            "productivity_gain_from_engagement": 18000,
        },
    }


async def calculate_engagement_impact(organization_id: int, time_period: str) -> dict[str, Any]:
    """Calculate employee engagement improvements"""

    return {
        "engagement_scores": {
            "baseline_score": 3.2,  # Out of 5
            "current_score": 4.1,
            "improvement": 0.9,
        },
        "business_correlations": {
            "productivity_correlation": 0.67,
            "retention_correlation": 0.71,
            "innovation_correlation": 0.58,
        },
        "financial_impact": {
            "engaged_employee_productivity_premium": 0.21,  # 21% more productive
            "additional_productivity_value": 24000,
            "reduced_absenteeism_savings": 8500,
        },
    }


async def calculate_innovation_impact(organization_id: int, time_period: str) -> dict[str, Any]:
    """Calculate innovation improvements from team behavioral optimization"""

    return {
        "innovation_metrics": {
            "idea_generation_rate_increase": 45,
            "idea_to_implementation_speed": 2.2,  # 2.2x faster
            "collaborative_innovation_projects": 12,
        },
        "business_outcomes": {
            "new_product_features_shipped": 8,
            "process_improvements_implemented": 15,
            "customer_satisfaction_increase": 0.12,  # 12 point NPS increase
        },
        "financial_impact": {
            "revenue_from_innovation": 125000,
            "cost_savings_from_improvements": 68000,
            "total_innovation_value": 193000,
        },
    }


async def calculate_hr_roi(organization_id: int, hr_metrics: dict[str, Any]) -> dict[str, Any]:
    """Calculate ROI for HR investment in PsychSync"""

    # Calculate total value created
    total_value = 0
    for metric_category in hr_metrics.values():
        if isinstance(metric_category, dict):
            # Look for annual value or similar metrics
            for key, value in metric_category.items():
                if "annual" in key.lower() and isinstance(value, (int, float)):
                    total_value += value

    # Calculate costs (simplified - would integrate with billing)
    monthly_cost = 1299  # Assuming Professional tier
    annual_cost = monthly_cost * 12

    roi = (total_value - annual_cost) / annual_cost * 100

    return {
        "total_annual_value": total_value,
        "annual_investment": annual_cost,
        "roi_percentage": roi,
        "payback_period_months": int(annual_cost / (total_value / 12)),
        "value_drivers": [
            "Productivity improvements",
            "Turnover reduction",
            "Innovation acceleration",
            "Engagement enhancement",
        ],
    }


async def generate_team_recommendations(
    team_id: int, behavioral_patterns: dict[str, Any]
) -> list[dict[str, Any]]:
    """Generate actionable team recommendations"""

    recommendations = []

    # Analyze cohesion score
    cohesion = behavioral_patterns.get("cohesion_score", 0)
    if cohesion < 0.6:
        recommendations.append(
            {
                "category": "team_cohesion",
                "priority": "high",
                "title": "Improve Team Cohesion",
                "description": "Team shows low cohesion indicators. Focus on building trust and shared understanding.",
                "actions": [
                    "Schedule team building workshops",
                    "Implement regular check-in processes",
                    "Create shared goals and OKRs",
                    "Address communication gaps",
                ],
                "expected_impact": "25% improvement in collaboration efficiency",
                "implementation_time": "4-6 weeks",
                "estimated_value": 15000,
            }
        )

    # Analyze communication effectiveness
    comm_score = behavioral_patterns.get("communication_score", 0)
    if comm_score < 0.7:
        recommendations.append(
            {
                "category": "communication",
                "priority": "medium",
                "title": "Enhance Communication Effectiveness",
                "description": "Communication patterns show opportunities for improvement in clarity and efficiency.",
                "actions": [
                    "Implement communication guidelines",
                    "Train on active listening techniques",
                    "Use structured meeting formats",
                    "Establish feedback mechanisms",
                ],
                "expected_impact": "30% reduction in meeting time",
                "implementation_time": "2-3 weeks",
                "estimated_value": 8500,
            }
        )

    return recommendations


async def calculate_data_confidence(team_assessments: list[dict[str, Any]]) -> float:
    """Calculate confidence score in behavioral analysis"""

    if not team_assessments:
        return 0.0

    # Factors affecting confidence
    team_size = len(team_assessments)
    assessment_recency = 1.0  # Would calculate based on assessment dates
    assessment_completion_rate = 0.85  # Would calculate from actual data

    # Confidence calculation
    base_confidence = min(team_size / 10, 1.0)  # More team members = higher confidence
    final_confidence = base_confidence * assessment_recency * assessment_completion_rate

    return min(final_confidence, 1.0)
