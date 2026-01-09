"""
Personality Assessment Endpoints
Dedicated endpoints for personality frameworks (MBTI, Enneagram, Big Five, etc.)
Separate from behavioral pattern analysis and clinical mental health
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_current_user, get_db
from app.db.models.assessment import Assessment, AssessmentResponse
from app.db.models.user import User
from app.middleware.rate_limiter import check_rate_limit

# AI Processing imports
try:
    from ai.processors import get_processor

    AI_PROCESSORS_AVAILABLE = True
except ImportError:
    AI_PROCESSORS_AVAILABLE = False
    logger.warning("AI processors not available")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/personality-assessments", tags=["personality-assessments"])

# Available personality frameworks
PERSONALITY_FRAMEWORKS = {
    "mbti": {
        "name": "Myers-Briggs Type Indicator",
        "description": "16 personality types based on cognitive preferences",
        "duration_minutes": 20,
        "questions_count": 93,
    },
    "big_five": {
        "name": "Big Five Personality Traits",
        "description": "Five-factor model (OCEAN): Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism",
        "duration_minutes": 15,
        "questions_count": 44,
    },
    "enneagram": {
        "name": "Enneagram Personality System",
        "description": "Nine personality types based on core motivations and fears",
        "duration_minutes": 25,
        "questions_count": 144,
    },
    "predictive_index": {
        "name": "Predictive Index",
        "description": "Behavioral assessment for workplace fit and team dynamics",
        "duration_minutes": 10,
        "questions_count": 86,
    },
    "disct": {
        "name": "DISC Assessment",
        "description": "Dominance, Influence, Steadiness, Conscientiousness behavioral styles",
        "duration_minutes": 12,
        "questions_count": 28,
    },
    "clifton_strengths": {
        "name": "CliftonStrengths",
        "description": "Identifies natural talents and strengths for development",
        "duration_minutes": 30,
        "questions_count": 177,
    },
    "social_styles": {
        "name": "Social Styles Assessment",
        "description": "Analytical, Driver, Amiable, Expressive behavioral patterns",
        "duration_minutes": 8,
        "questions_count": 24,
    },
}


@check_rate_limit(identifier="public", limit_name="public")
@router.get("/frameworks")
async def get_personality_frameworks():
    """
    Get available personality assessment frameworks

    Returns list of all supported personality assessment frameworks
    with their descriptions and metadata
    """
    return {
        "frameworks": PERSONALITY_FRAMEWORKS,
        "total_frameworks": len(PERSONALITY_FRAMEWORKS),
        "categories": {
            "trait_based": ["big_five", "predictive_index"],
            "type_based": ["mbti", "enneagram"],
            "behavioral": ["disct", "social_styles"],
            "strengths_based": ["clifton_strengths"],
        },
    }


@router.get("/user-assessments/{user_id}", dependencies=[Depends(get_current_user)])
async def get_user_personality_assessments(
    user_id: str,
    include_completed: bool = Query(True, description="Include only completed assessments"),
    framework_filter: str | None = Query(None, description="Filter by framework"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's personality assessment history

    - **user_id**: User ID to get assessments for
    - **include_completed**: Filter to only include completed assessments
    - **framework_filter**: Filter by specific personality framework

    Returns comprehensive assessment history with results and trends
    """
    try:
        # Check permissions
        if user_id != str(current_user.id) and not current_user.is_admin:
            # Check if user is in same organization/team
            if not hasattr(current_user, "organization_id"):
                raise HTTPException(
                    status_code=403, detail="Not authorized to view this user's assessments"
                )

        # Build query
        query = (
            select(Assessment, AssessmentResponse)
            .join(AssessmentResponse, Assessment.id == AssessmentResponse.assessment_id)
            .where(
                and_(
                    Assessment.category == "personality",
                    AssessmentResponse.respondent_id == user_id,
                )
            )
        )

        # Apply filters
        if include_completed:
            query = query.where(AssessmentResponse.status == "completed")

        if framework_filter:
            query = query.where(Assessment.framework_code == framework_filter.lower())

        query = query.order_by(AssessmentResponse.completed_at.desc().nullslast())

        result = await db.execute(query)
        assessments = result.all()

        # Process results
        user_assessments = []
        for assessment, response in assessments:
            assessment_data = {
                "assessment_id": str(assessment.id),
                "framework_code": assessment.framework_code,
                "framework_info": PERSONALITY_FRAMEWORKS.get(assessment.framework_code.lower()),
                "title": assessment.title,
                "description": assessment.description,
                "status": response.status.value,
                "created_at": assessment.created_at.isoformat(),
                "started_at": response.started_at.isoformat(),
                "completed_at": response.completed_at.isoformat()
                if response.completed_at
                else None,
                "duration_minutes": PERSONALITY_FRAMEWORKS.get(
                    assessment.framework_code.lower(), {}
                ).get("duration_minutes", 0),
                "responses": response.responses,
                "data_quality": _assess_data_quality(response.responses),
            }

            # Add processed results if completed
            if response.status.value == "completed" and response.responses:
                assessment_data["processed_results"] = await _process_personality_assessment(
                    assessment.framework_code, response.responses
                )

            user_assessments.append(assessment_data)

        # Add analytics
        return {
            "user_id": user_id,
            "total_assessments": len(user_assessments),
            "completed_assessments": len(
                [a for a in user_assessments if a["status"] == "completed"]
            ),
            "frameworks_completed": list(
                set(a["framework_code"] for a in user_assessments if a["status"] == "completed")
            ),
            "assessments": user_assessments,
            "assessment_trends": await _analyze_assessment_trends(user_assessments),
            "personality_summary": await _generate_personality_summary(user_assessments),
        }

    except Exception as e:
        logger.error(f"Error getting user personality assessments: {e}")
        raise HTTPException(status_code=500, detail="Failed to get personality assessments") from e


@router.post("/take-assessment", dependencies=[Depends(get_current_user)])
async def create_personality_assessment(
    framework_code: str = Query(..., description="Personality framework code"),
    team_id: str | None = Query(None, description="Team ID if assessment is team-based"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new personality assessment

    - **framework_code**: Personality framework (mbti, big_five, enneagram, etc.)
    - **team_id**: Optional team ID for team-based assessments

    Returns assessment session details with access information
    """
    try:
        # Validate framework
        if framework_code.lower() not in PERSONALITY_FRAMEWORKS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid framework. Available: {list(PERSONALITY_FRAMEWORKS.keys())}",
            )

        framework_info = PERSONALITY_FRAMEWORKS[framework_code.lower()]

        # Create assessment
        assessment = Assessment(
            title=f"{framework_info['name']} Assessment",
            description=framework_info["description"],
            category="personality",
            framework_code=framework_code.lower(),
            status="in_progress",
            created_by_id=current_user.id,
            organization_id=getattr(current_user, "organization_id", None),
            team_id=team_id,
            started_at=datetime.utcnow(),
        )

        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)

        # Create initial response
        response = AssessmentResponse(
            assessment_id=assessment.id,
            respondent_id=current_user.id,
            status="in_progress",
            started_at=datetime.utcnow(),
        )

        db.add(response)
        await db.commit()
        await db.refresh(response)

        return {
            "assessment_id": str(assessment.id),
            "framework": framework_info,
            "access_code": f"PA-{assessment.id.hex[:8].upper()}",
            "estimated_duration": framework_info["duration_minutes"],
            "questions_count": framework_info["questions_count"],
            "started_at": assessment.started_at.isoformat(),
            "status": "started",
            "next_step": "Begin assessment questions",
            "web_interface_url": f"/assessments/personality/{assessment.id}",
        }

    except Exception as e:
        logger.error(f"Error creating personality assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create personality assessment") from e


@router.post("/submit-response/{assessment_id}")
async def submit_personality_assessment(
    assessment_id: str,
    responses: dict[str, Any],
    completion_data: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit personality assessment responses for processing

    - **assessment_id**: Assessment ID to submit responses for
    - **responses**: Assessment responses/answers
    - **completion_data**: Optional completion metadata

    Returns processed personality results with detailed analysis
    """
    try:
        # Get assessment
        assessment_result = await db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        assessment = assessment_result.scalar_one()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        if assessment.category != "personality":
            raise HTTPException(status_code=400, detail="This is not a personality assessment")

        # Get existing response
        response_result = await db.execute(
            select(AssessmentResponse).where(
                and_(
                    AssessmentResponse.assessment_id == assessment_id,
                    AssessmentResponse.respondent_id == str(current_user.id),
                )
            )
        )
        response = response_result.scalar_one_or_none()

        if not response:
            raise HTTPException(status_code=404, detail="Assessment response not found")

        # Update response
        response.responses = responses
        response.status = "completed"
        response.completed_at = datetime.utcnow()

        db.commit()

        # Process assessment with AI
        processed_results = await _process_personality_assessment(
            assessment.framework_code, responses
        )

        # Add completion data if provided
        if completion_data:
            for key, value in completion_data.items():
                setattr(response, key, value)

        await db.commit()

        return {
            "assessment_id": str(assessment_id),
            "framework": assessment.framework_code,
            "status": "completed",
            "completed_at": response.completed_at.isoformat(),
            "duration_minutes": (response.completed_at - response.started_at).total_seconds() / 60,
            "processed_results": processed_results,
            "data_quality": _assess_data_quality(responses),
            "confidence_score": processed_results.get("confidence", 0.0),
            "recommendations": await _generate_personality_recommendations(processed_results),
        }

    except Exception as e:
        logger.error(f"Error submitting personality assessment: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit personality assessment") from e


@router.get("/compare-results/{user_id}")
async def compare_personality_results(
    user_id: str,
    frameworks: list[str] = Query(["mbti", "big_five"], description="Frameworks to compare"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare results across different personality frameworks

    - **user_id**: User ID to compare results for
    -frameworks: List of frameworks to include in comparison

    Returns cross-framework analysis and correlations
    """
    try:
        # Get user's completed personality assessments
        query = (
            select(Assessment, AssessmentResponse)
            .join(AssessmentResponse, Assessment.id == AssessmentResponse.assessment_id)
            .where(
                and_(
                    Assessment.category == "personality",
                    AssessmentResponse.respondent_id == user_id,
                    AssessmentResponse.status == "completed",
                    Assessment.framework_code.in_([fw.lower() for fw in frameworks]),
                )
            )
        )

        result = await db.execute(query)
        assessments = result.all()

        framework_results = {}
        for assessment, response in assessments:
            if response.responses:
                processed = await _process_personality_assessment(
                    assessment.framework_code, response.responses
                )
                framework_results[assessment.framework_code] = processed

        # Cross-framework analysis
        comparison_analysis = await _analyze_cross_framework_comparison(framework_results)

        return {
            "user_id": user_id,
            "frameworks_analyzed": list(framework_results.keys()),
            "framework_results": framework_results,
            "cross_framework_analysis": comparison_analysis,
            "consistency_score": comparison_analysis.get("overall_consistency", 0.0),
            "integration_insights": comparison_analysis.get("integration_insights", []),
        }

    except Exception as e:
        logger.error(f"Error comparing personality results: {e}")
        raise HTTPException(status_code=500, detail="Failed to compare personality results") from e


@router.get("/team-personality-profile/{team_id}")
async def get_team_personality_profile(
    team_id: str,
    include_individuals: bool = Query(False, description="Include individual member profiles"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated personality profile for a team

    - **team_id**: Team ID to analyze
    - **include_individuals**: Whether to include individual member profiles

    Returns team personality composition and insights
    """
    try:
        # Get team member assessments
        query = (
            select(Assessment, AssessmentResponse)
            .join(AssessmentResponse, Assessment.id == AssessmentResponse.assessment_id)
            .where(
                and_(
                    Assessment.category == "personality",
                    Assessment.team_id == team_id,
                    AssessmentResponse.status == "completed",
                )
            )
            .order_by(AssessmentResponse.completed_at.desc())
        )

        result = await db.execute(query)
        assessments = result.all()

        if not assessments:
            return {
                "team_id": team_id,
                "profile": None,
                "message": "No personality assessments found for this team",
                "recommendation": "Encourage team members to take personality assessments",
            }

        # Aggregate personality data
        team_profile = await _aggregate_team_personality_profile(assessments, include_individuals)

        return team_profile

    except Exception as e:
        logger.error(f"Error getting team personality profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get team personality profile") from e


# Helper functions


def _assess_data_quality(responses: dict[str, Any]) -> dict[str, Any]:
    """Assess data quality of assessment responses"""
    if not responses:
        return {"score": 0.0, "issues": ["No responses provided"]}

    total_questions = len(responses)
    answered_questions = len([r for r in responses.values() if r is not None and r != ""])

    score = answered_questions / total_questions if total_questions > 0 else 0.0

    issues = []
    if score < 0.8:
        issues.append(f"Low completion rate: {answered_questions}/{total_questions}")
    if score < 0.5:
        issues.append("Very low completion rate - results may be unreliable")

    return {
        "score": score,
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "completion_rate": score,
        "issues": issues,
    }


async def _process_personality_assessment(
    framework_code: str, responses: dict[str, Any]
) -> dict[str, Any]:
    """Process personality assessment results using appropriate AI processor"""
    try:
        # Import appropriate processor
        if framework_code.lower() == "mbti":
            from ai.processors.mbti_processor import MBTIProcessor

            processor = MBTIProcessor()
        elif framework_code.lower() == "big_five":
            from ai.processors.big_five import BigFiveProcessor

            processor = BigFiveProcessor()
        elif framework_code.lower() == "enneagram":
            from ai.processors.enneagram import EnneagramProcessor

            processor = EnneagramProcessor()
        elif framework_code.lower() == "predictive_index":
            from ai.processors.predictive_index import PredictiveIndexProcessor

            processor = PredictiveIndexProcessor()
        else:
            # Default processor
            from ai.processors.processors_base import PersonalityFrameworkProcessor

            processor = PersonalityFrameworkProcessor()

        # Process assessment
        result = processor._safe_process(responses)

        # Add framework-specific metadata
        result["framework"] = framework_code
        result["processed_at"] = datetime.utcnow().isoformat()

        return result

    except Exception as e:
        logger.error(f"Error processing personality assessment: {e}")
        return {
            "framework": framework_code,
            "error": str(e),
            "confidence": 0.1,
            "fallback": True,
            "dimensions": {},
        }


async def _generate_personality_recommendations(results: dict[str, Any]) -> list[str]:
    """Generate personalized recommendations based on personality assessment results"""
    recommendations = []

    try:
        if results.get("framework") == "mbti" and "type" in results:
            mbti_type = results["type"]
            recommendations.extend(_generate_mbti_recommendations(mbti_type))

        elif results.get("framework") == "big_five" and "dimensions" in results:
            dimensions = results["dimensions"]
            recommendations.extend(_generate_big_five_recommendations(dimensions))

        elif results.get("framework") == "enneagram" and "type" in results:
            enneagram_type = results["type"]
            recommendations.extend(_generate_enneagram_recommendations(enneagram_type))

        # Add general personality development recommendations
        recommendations.extend(
            [
                "Consider regular self-reflection to track personality development",
                "Use personality insights for better self-awareness and growth",
                "Share results with trusted individuals for feedback and validation",
            ]
        )

        return recommendations[:8]  # Limit to top recommendations

    except Exception as e:
        logger.error(f"Error generating personality recommendations: {e}")
        return ["Complete more personality assessments for personalized recommendations"]


def _generate_mbti_recommendations(mbti_type: str) -> list[str]:
    """Generate MBTI-specific recommendations"""
    recommendations = []

    # Workplace recommendations based on type
    if mbti_type.startswith("E"):
        recommendations.extend(
            [
                "Leverage your natural energy in team settings and presentations",
                "Consider leadership or people-management roles",
                "Balance social time with periods of reflection",
            ]
        )
    elif mbti_type.startswith("I"):
        recommendations.extend(
            [
                "Allow adequate time for reflection and deep work",
                "Communicate insights through written channels when possible",
                "Build social connections one-on-one rather than in large groups",
            ]
        )

    # Decision-making recommendations
    if mbti_type[1] == "T":
        recommendations.extend(
            [
                "Use logical analysis for complex problem-solving",
                "Consider the objective impact of your decisions",
                "Balance analytical thinking with team collaboration",
            ]
        )
    elif mbti_type[1] == "F":
        recommendations.extend(
            [
                "Consider how decisions affect people and relationships",
                "Use values-based decision making for important choices",
                "Collaborate with analytical team members for balanced perspective",
            ]
        )

    return recommendations


def _generate_big_five_recommendations(dimensions: dict[str, float]) -> list[str]:
    """Generate Big Five-specific recommendations"""
    recommendations = []

    # Openness recommendations
    openness = dimensions.get("openness", 0.5)
    if openness > 0.7:
        recommendations.extend(
            [
                "Embrace your openness to new experiences and learning",
                "Consider roles that require creativity and innovation",
                "Share your ideas and inspire others to think differently",
            ]
        )
    elif openness < 0.3:
        recommendations.extend(
            [
                "Gradually expose yourself to new perspectives and ideas",
                "Try small changes to expand your comfort zone",
                "Consider learning from diverse viewpoints and approaches",
            ]
        )

    # Conscientiousness recommendations
    conscientiousness = dimensions.get("conscientiousness", 0.5)
    if conscientiousness > 0.7:
        recommendations.extend(
            [
                "Leverage your organizational skills for project management",
                "Consider roles requiring attention to detail and reliability",
                "Help others by sharing your planning and organizing strategies",
            ]
        )
    elif conscientiousness < 0.3:
        recommendations.extend(
            [
                "Implement simple organizational systems and routines",
                "Use calendars and reminders for important deadlines",
                "Find an accountability partner for structure and support",
            ]
        )

    return recommendations


def _generate_enneagram_recommendations(enneagram_type: str) -> list[str]:
    """Generate Enneagram-specific recommendations"""
    recommendations = []

    # Enneagram type-specific growth recommendations
    type_recommendations = {
        "1": [
            "Practice pausing before reacting to situations",
            "Develop self-awareness through meditation and reflection",
            "Focus on reality-based decision making",
        ],
        "2": [
            "Acknowledge and express your own needs and feelings",
            "Build healthy boundaries in relationships",
            "Practice self-compassion and self-acceptance",
        ],
        "3": [
            "Channel productivity toward meaningful goals",
            "Practice receiving and giving affirmation from others",
            "Balance work with rest and play",
        ],
        "4": [
            "Explore your emotional depth and authenticity",
            "Share your creative insights with trusted others",
            "Practice self-care and emotional regulation",
        ],
        "5": [
            "Practice observation before forming opinions",
            "Learn to detach from information and concepts",
            "Engage more in present-moment activities",
        ],
        "6": [
            "Ask for help and support when needed",
            "Challenge negative self-talk and doubt",
            "Practice assertiveness and self-confidence",
        ],
        "7": [
            "Find healthy outlets for your intensity and energy",
            "Practice moderation in work and pleasure",
            "Develop sensitivity to others' feelings and needs",
        ],
        "8": [
            "Practice assertiveness without aggression",
            "Protect your boundaries while staying connected",
            "Channel your protective instincts into constructive action",
        ],
        "9": [
            "Embrace peace and harmony in relationships",
            "Avoid avoiding necessary conflicts",
            "Develop independence and self-sufficiency",
        ],
    }

    return type_recommendations.get(enneagram_type, ["Continue your Enneagram growth journey"])


async def _analyze_assessment_trends(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze trends in personality assessment results over time"""
    if len(assessments) < 2:
        return {"message": "Insufficient data for trend analysis"}

    # Group assessments by framework
    frameworks = {}
    for assessment in assessments:
        framework = assessment.get("framework_code", "unknown")
        if framework not in frameworks:
            frameworks[framework] = []
        frameworks[framework].append(assessment)

    trends = {}
    for framework, framework_assessments in frameworks.items():
        if len(framework_assessessments) >= 2:
            # Sort by completion date
            framework_assessments.sort(key=lambda x: x.get("completed_at", ""))

            # Analyze consistency
            if framework == "mbti":
                types = [
                    a.get("processed_results", {}).get("type")
                    for a in framework_assessments
                    if a.get("processed_results")
                ]
                consistent_types = len(set(types)) <= 2
                trends[framework] = {
                    "type_consistency": "consistent" if consistent_types else "evolving",
                    "most_recent_type": types[-1] if types else None,
                    "type_stability": consistent_types,
                }

            elif framework == "big_five":
                # Analyze trait changes over time
                first_assessment = (
                    framework_assessments[0].get("processed_results", {}).get("dimensions", {})
                )
                last_assessment = (
                    framework_assessments[-1].get("processed_results", {}).get("dimensions", {})
                )

                trait_changes = {}
                for trait in [
                    "openness",
                    "conscientiousness",
                    "extraversion",
                    "agreeableness",
                    "neuroticism",
                ]:
                    if trait in first_assessment and trait in last_assessment:
                        change = last_assessment[trait] - first_assessment[trait]
                        trait_changes[trait] = round(change, 3)

                trends[framework] = {
                    "trait_changes": trait_changes,
                    "most_significant_change": max(
                        trait_changes.items(), key=lambda x: abs(x[1]), default=(None, 0)
                    )[0]
                    if trait_changes
                    else None,
                    "development_areas": [
                        trait for trait, change in trait_changes.items() if change > 0.1
                    ],
                }

    return trends


async def _generate_personality_summary(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate comprehensive personality summary across all assessments"""
    if not assessments:
        return {"message": "No personality assessments available"}

    # Most recent completed assessment per framework
    latest_assessments = {}
    for assessment in assessments:
        if assessment["status"] == "completed":
            framework = assessment["framework_code"]
            if (
                framework not in latest_assessments
                or assessment["completed_at"] > latest_assessments[framework]["completed_at"]
            ):
                latest_assessments[framework] = assessment

    summary = {
        "frameworks_completed": list(latest_assessments.keys()),
        "total_assessments": len(assessments),
        "latest_results": {
            framework: assessment["processed_results"]
            for framework, assessment in latest_assessments.items()
        },
    }

    # Overall insights
    all_frameworks = list(latest_assessments.keys())
    if len(all_frameworks) >= 2:
        summary["comprehensive_profile"] = "Multi-framework assessment completed"
        summary["insight"] = "Well-rounded personality understanding across multiple frameworks"
    else:
        summary["comprehensive_profile"] = "Single-framework assessment"
        summary["suggestion"] = (
            "Consider additional personality frameworks for deeper understanding"
        )

    return summary


async def _analyze_cross_framework_comparison(framework_results: dict[str, Any]) -> dict[str, Any]:
    """Analyze consistency and correlations across different personality frameworks"""
    frameworks = list(framework_results.keys())

    if len(frameworks) < 2:
        return {"message": "Need at least 2 frameworks for comparison"}

    analysis = {
        "frameworks_analyzed": frameworks,
        "integration_insights": [],
        "overall_consistency": 0.0,
    }

    # MBTI to Big Five correlation analysis
    if "mbti" in framework_results and "big_five" in framework_results:
        mbti_result = framework_results["mbti"]
        big_five_result = framework_results["big_five"]

        if "type" in mbti_result and "dimensions" in big_five_result:
            correlations = _calculate_mbti_big_five_correlation(
                mbti_result["type"], big_five_result["dimensions"]
            )
            analysis["mbti_big_five_correlation"] = correlations
            analysis["integration_insights"].extend(
                [
                    f"MBTI {mbti_result['type']} correlates with Big Five trait patterns",
                    f"Strongest correlation: {correlations.get('strongest', 'None')}",
                ]
            )

    # Overall consistency score (simplified)
    consistency_scores = []
    if "mbti_big_five_correlation" in analysis:
        consistency_scores.append(analysis["mbti_big_five_correlation"].get("consistency", 0.5))

    analysis["overall_consistency"] = (
        sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5
    )

    return analysis


def _calculate_mbti_big_five_correlation(
    mbti_type: str, big_five_dimensions: dict[str, float]
) -> dict[str, Any]:
    """Calculate correlation between MBTI type and Big Five dimensions"""
    correlations = {
        "ENFP": {"extraversion": 0.7, "openness": 0.8, "agreeableness": 0.6},
        "INTJ": {"openness": 0.8, "conscientiousness": 0.7, "introversion": 0.7},
        "ENTJ": {"extraversion": 0.8, "conscientiousness": 0.7, "openness": 0.6},
        "ENTP": {"extraversion": 0.8, "openness": 0.9, "agreeableness": 0.5},
        "INFJ": {"openness": 0.8, "agreeableness": 0.8, "introversion": 0.7},
        "INFP": {"openness": 0.8, "agreeableness": 0.8, "neuroticism": 0.6},
        "ENFJ": {"extraversion": 0.6, "agreeableness": 0.9, "openness": 0.5},
        "ENFP": {"extraversion": 0.8, "openness": 0.9, "agreeableness": 0.7},
        # Add other MBTI types as needed
    }

    mbti_correlations = correlations.get(mbti_type, {})
    big_five_keys = list(big_five_dimensions.keys())

    # Calculate actual correlations
    actual_correlations = {}
    for trait in mbti_correlations:
        if trait in big_five_keys:
            expected = mbti_correlations[trait]
            actual = big_five_dimensions[trait]
            actual_correlations[trait] = {
                "expected": expected,
                "actual": actual,
                "difference": abs(expected - actual),
                "correlation_strength": 1.0 - abs(expected - actual),
            }

    # Calculate overall consistency
    if actual_correlations:
        avg_correlation = sum(
            corr["correlation_strength"] for corr in actual_correlations.values()
        ) / len(actual_correlations)
        actual_correlations["consistency"] = avg_correlation
        actual_correlations["strongest"] = max(
            actual_correlations.items(),
            key=lambda x: x[1].get("correlation_strength", 0),
            default=(None, 0),
        )[0]

    return actual_correlations


async def _aggregate_team_personality_profile(
    assessments: list, include_individuals: bool
) -> dict[str, Any]:
    """Aggregate personality profile for a team"""
    if not assessments:
        return None

    # Group by user
    user_assessments = {}
    for assessment, response in assessments:
        user_id = response.respondent_id
        if user_id not in user_assessments:
            user_assessments[user_id] = []
        user_assessments[user_id].append(
            {
                "assessment": assessment,
                "response": response,
                "processed": await _process_personality_assessment(
                    assessment.framework_code, response.responses
                ),
            }
        )

    # Calculate team profile
    team_profile = {
        "team_size": len(user_assessments),
        "frameworks_used": list(set(a["assessment"].framework_code for a in assessments)),
        "diversity_metrics": await _calculate_personality_diversity(user_assessessments),
        "team_dynamics": await _analyze_team_dynamics(user_assessessments),
    }

    if include_individuals:
        team_profile["individual_profiles"] = {
            user_id: {
                "latest_assessment": max(
                    profiles, key=lambda x: x["assessment"].completed_at or ""
                ),
                "processed_results": profiles[-1]["processed"] if profiles else None,
            }
            for user_id, profiles in user_assessments.items()
        }

    return team_profile


async def _calculate_personality_diversity(user_assessments: dict[str, list]) -> dict[str, Any]:
    """Calculate personality diversity metrics for a team"""
    # This is a simplified implementation
    team_size = len(user_assessments)

    # Count different personality types/frameworks
    mbti_types = []
    for user_id, assessments in user_assessments.items():
        for assessment in assessments:
            if assessment["assessment"].framework_code == "mbti":
                processed = assessment["processed"]
                if processed and "type" in processed:
                    mbti_types.append(processed["type"])

    diversity_score = len(set(mbti_types)) / team_size if team_size > 0 else 0

    return {
        "personality_diversity_score": diversity_score,
        "unique_mbti_types": len(set(mbti_types)),
        "most_common_type": max(set(mbti_types), key=mbti_types.count) if mbti_types else None,
        "diversity_classification": "high"
        if diversity_score > 0.7
        else "medium"
        if diversity_score > 0.4
        else "low",
    }


async def _analyze_team_dynamics(user_assessments: dict[str, list]) -> dict[str, Any]:
    """Analyze team dynamics based on personality profiles"""
    team_size = len(user_assessessments)

    # Simplified team dynamics analysis
    dynamics = {
        "collaboration_potential": "high",
        "communication_style": "mixed",
        "decision_making_approach": "balanced",
        "conflict_landscape": "moderate",
    }

    # Would implement more sophisticated analysis here
    # based on personality combinations and team composition

    return dynamics


@router.post("/process")
async def process_personality_assessment(
    request: dict[str, Any], current_user: User = Depends(get_current_active_user)
) -> dict[str, Any]:
    """
    Process personality assessment data using AI engine
    """
    if not AI_PROCESSORS_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="AI processing service is currently unavailable"
        )

    # Extract framework and data from request
    framework = request.get("framework")
    data = request.get("data")

    if not framework or not data:
        raise HTTPException(status_code=400, detail="Missing 'framework' or 'data' in request body")

    try:
        # Get the appropriate processor
        processor = get_processor(framework.lower())

        # Process the assessment data
        result = processor._safe_process(data)

        if result.get("success", False):
            return {
                "success": True,
                "framework": framework,
                "processed_at": result.get("processed_at"),
                "confidence": result.get("confidence"),
                "results": result,
                "processed_by": "AI_Engine_v1.0",
            }
        return {
            "success": False,
            "framework": framework,
            "error": result.get("error", "Processing failed"),
            "fallback": result.get("fallback", False),
        }

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported framework: {framework}") from None
    except Exception as e:
        logger.error(f"Error processing {framework} assessment: {e!s}")
        raise HTTPException(status_code=500, detail=f"Processing error: {e!s}") from e
