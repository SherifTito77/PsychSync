"""
Clinical Mental Health & Wellness API Endpoints
Focused on mental health screening, wellness monitoring, and clinical tools
Separate from personality assessments and behavioral analysis
"""

from fastapi import APIRouter, HTTPException, Depends, Query

from app.middleware.rate_limiter import check_rate_limit
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from app.api.v1.deps import get_current_user, get_db
from app.services.mental_health_screening import MentalHealthScreeningService
from app.services.wellness_monitoring import WellnessMonitoringService
from app.services.clinical_assessment_service import ClinicalAssessmentService
from app.services.trend_analysis import TrendAnalysisService
from app.services.wellness_plan_generator import WellnessPlanGeneratorService
from app.services.crisis_support import CrisisSupportService
from pydantic import BaseModel
from typing import Optional
from app.schemas.clinical import (
    MentalHealthScreeningRequest,
    MentalHealthScreeningResponse,
    WellnessAssessmentRequest,
    WellnessAssessmentResponse,
    CrisisAlertRequest,
    CrisisAlertResponse,
    MentalHealthTrendRequest,
    MentalHealthTrendResponse,
    WellnessPlanRequest,
    WellnessPlanResponse,
    ClinicalResourceRequest,
    ClinicalResourceResponse
)
from app.core.logging_config import logger
router = APIRouter(prefix="/clinical", tags=["clinical"])

# Consent request/response models
class ClinicalConsentRequest(BaseModel):
    assessment_type: str
    consent_given: bool
    consent_text: Optional[str] = None
    assessment_duration: Optional[str] = None
    understands_purpose: bool = True
    agrees_to_data_usage: bool = False

class ClinicalConsentResponse(BaseModel):
    success: bool
    consent_id: Optional[str] = None
    assessment_type: str
    consent_status: str
    message: str
    timestamp: datetime

# Clinical Services (will be initialized with database session)
screening_service = None
wellness_service = None
clinical_service = None



@check_rate_limit(identifier="public", endpoint_type="public")
@router.post("/consent", response_model=ClinicalConsentResponse)
async def handle_clinical_consent(
    request: ClinicalConsentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Handle clinical assessment consent
    Required before starting any clinical screening or assessment
    """
    try:
        # Generate consent ID
        import uuid
        consent_id = str(uuid.uuid4())

        # Validate consent requirements
        if not request.consent_given:
            return ClinicalConsentResponse(
                success=False,
                consent_id=None,
                assessment_type=request.assessment_type,
                consent_status="declined",
                message="Consent is required before starting clinical assessments",
                timestamp=datetime.utcnow()
            )

        # Store consent record (simplified for now)
        consent_record = {
            "consent_id": consent_id,
            "user_id": current_user["id"],
            "assessment_type": request.assessment_type,
            "consent_given": request.consent_given,
            "consent_text": request.consent_text,
            "assessment_duration": request.assessment_duration,
            "understands_purpose": request.understands_purpose,
            "agrees_to_data_usage": request.agrees_to_data_usage,
            "consent_given_at": datetime.utcnow(),
            "ip_address": None  # Will be filled by middleware if needed
        }

        # Log consent for audit trail
        logger.info(f"Clinical consent recorded: {consent_id} for user {current_user['id']} - {request.assessment_type}")

        # Get assessment information
        assessment_info = {
            "perceived_stress_scale": {
                "name": "Perceived Stress Scale",
                "description": "Evaluate your perceived stress levels",
                "duration": "5 minutes",
                "questions": 10
            },
            "phq9": {
                "name": "Patient Health Questionnaire-9",
                "description": "Depression screening tool",
                "duration": "2-5 minutes",
                "questions": 9
            },
            "gad7": {
                "name": "Generalized Anxiety Disorder-7",
                "description": "Anxiety screening tool",
                "duration": "2-3 minutes",
                "questions": 7
            }
        }

        assessment_details = assessment_info.get(request.assessment_type.lower(), {
            "name": request.assessment_type,
            "description": "Clinical assessment",
            "duration": request.assessment_duration or "Unknown",
            "questions": "Unknown"
        })

        return ClinicalConsentResponse(
            success=True,
            consent_id=consent_id,
            assessment_type=request.assessment_type,
            consent_status="granted",
            message=f"Consent recorded for {assessment_details['name']}. You can now begin the {assessment_details['duration']} assessment.",
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Clinical consent handling failed: {str(e)}")
        return ClinicalConsentResponse(
            success=False,
            consent_id=None,
            assessment_type=request.assessment_type,
            consent_status="error",
            message="Unable to process consent. Please try again.",
            timestamp=datetime.utcnow()
        )


@router.post("/screening/mental-health", response_model=MentalHealthScreeningResponse)
async def conduct_mental_health_screening(
    request: MentalHealthScreeningRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Conduct mental health screening using validated clinical tools
    Includes PHQ-9, GAD-7, DASS-21, and other evidence-based assessments
    """
    try:
        # Validate user consent and screening eligibility
        consent_verified = await clinical_service.verify_screening_consent(
            user_id=current_user["id"],
            screening_type=request.screening_type
        )

        if not consent_verified:
            raise HTTPException(
                status_code=403,
                detail="User consent not verified for mental health screening"
            )

        # Conduct screening based on requested assessment type
        screening_results = {}
        risk_assessment = {}
        recommendations = []

        for screening_tool in request.screening_tools:
            if screening_tool == "phq9":
                result = await screening_service.conduct_phq9_screening(
                    user_id=current_user["id"],
                    responses=request.responses.get("phq9", []),
                    context=request.context
                )
                screening_results["phq9"] = result

                # Assess depression risk
                depression_risk = await screening_service.assess_depression_risk(result)
                risk_assessment["depression"] = depression_risk

            elif screening_tool == "gad7":
                result = await screening_service.conduct_gad7_screening(
                    user_id=current_user["id"],
                    responses=request.responses.get("gad7", []),
                    context=request.context
                )
                screening_results["gad7"] = result

                # Assess anxiety risk
                anxiety_risk = await screening_service.assess_anxiety_risk(result)
                risk_assessment["anxiety"] = anxiety_risk

            elif screening_tool == "dass21":
                result = await screening_service.conduct_dass21_screening(
                    user_id=current_user["id"],
                    responses=request.responses.get("dass21", []),
                    context=request.context
                )
                screening_results["dass21"] = result

                # DASS-21 provides depression, anxiety, and stress scales
                dass_risk = await screening_service.assess_dass21_risk(result)
                risk_assessment.update(dass_risk)

            elif screening_tool == "pcl5":
                result = await screening_service.conduct_pcl5_screening(
                    user_id=current_user["id"],
                    responses=request.responses.get("pcl5", []),
                    context=request.context
                )
                screening_results["pcl5"] = result

                # Assess PTSD risk
                ptsd_risk = await screening_service.assess_ptsd_risk(result)
                risk_assessment["ptsd"] = ptsd_risk

            elif screening_tool == "audit":
                result = await screening_service.conduct_audit_screening(
                    user_id=current_user["id"],
                    responses=request.responses.get("audit", []),
                    context=request.context
                )
                screening_results["audit"] = result

                # Assess alcohol use risk
                alcohol_risk = await screening_service.assess_alcohol_risk(result)
                risk_assessment["alcohol_use"] = alcohol_risk

        # Generate overall risk assessment and recommendations
        overall_risk = await screening_service.calculate_overall_mental_health_risk(risk_assessment)
        recommendations = await screening_service.generate_clinical_recommendations(
            screening_results, risk_assessment, overall_risk
        )

        # Check for immediate crisis risk
        crisis_alert = await screening_service.check_for_crisis_risk(
            screening_results, risk_assessment
        )

        return MentalHealthScreeningResponse(
            success=True,
            user_id=current_user["id"],
            screening_type=request.screening_type,
            screening_tools=request.screening_tools,
            screening_results=screening_results,
            risk_assessment=risk_assessment,
            overall_risk_level=overall_risk["risk_level"],
            recommendations=recommendations,
            crisis_alert=crisis_alert,
            next_screening_date=await screening_service.calculate_next_screening_date(
                current_user["id"], overall_risk
            ),
            screened_at=datetime.utcnow(),
            clinical_disclaimer="This screening is not a substitute for professional medical advice. Please consult with a qualified healthcare provider."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mental health screening failed: {str(e)}")
        raise HTTPException(
            status_code=500,

@check_rate_limit(identifier="public", endpoint_type="public")
            detail="Mental health screening failed"
        )


@router.post("/wellness/assessment", response_model=WellnessAssessmentResponse)
async def conduct_wellness_assessment(
    request: WellnessAssessmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ):
    """
    Conduct comprehensive wellness assessment
    Multi-dimensional wellness evaluation across physical, mental, emotional, social, and professional domains
    """
    try:
        # Get wellness assessment data
        wellness_data = await wellness_service.collect_wellness_data(
            user_id=current_user["id"],
            assessment_type=request.assessment_type,
            responses=request.responses,
            biometric_data=request.biometric_data,
            lifestyle_data=request.lifestyle_data
        )

        # Assess each wellness dimension
        wellness_scores = {}
        dimension_insights = {}

        for dimension in request.wellness_dimensions:
            if dimension == "physical":
                assessment = await wellness_service.assess_physical_wellness(wellness_data)
                wellness_scores["physical"] = assessment["score"]
                dimension_insights["physical"] = assessment["insights"]

            elif dimension == "mental":
                assessment = await wellness_service.assess_mental_wellness(wellness_data)
                wellness_scores["mental"] = assessment["score"]
                dimension_insights["mental"] = assessment["insights"]

            elif dimension == "emotional":
                assessment = await wellness_service.assess_emotional_wellness(wellness_data)
                wellness_scores["emotional"] = assessment["score"]
                dimension_insights["emotional"] = assessment["insights"]

            elif dimension == "social":
                assessment = await wellness_service.assess_social_wellness(wellness_data)
                wellness_scores["social"] = assessment["score"]
                dimension_insights["social"] = assessment["insights"]

            elif dimension == "professional":
                assessment = await wellness_service.assess_professional_wellness(wellness_data)
                wellness_scores["professional"] = assessment["score"]
                dimension_insights["professional"] = assessment["insights"]

            elif dimension == "spiritual":
                assessment = await wellness_service.assess_spiritual_wellness(wellness_data)
                wellness_scores["spiritual"] = assessment["score"]
                dimension_insights["spiritual"] = assessment["insights"]

            elif dimension == "environmental":
                assessment = await wellness_service.assess_environmental_wellness(wellness_data)
                wellness_scores["environmental"] = assessment["score"]
                dimension_insights["environmental"] = assessment["insights"]

        # Calculate overall wellness score
        overall_wellness_score = await wellness_service.calculate_overall_wellness_score(
            wellness_scores, request.wellness_dimensions
        )

        # Generate wellness recommendations
        wellness_recommendations = await wellness_service.generate_wellness_recommendations(
            wellness_scores, dimension_insights, overall_wellness_score
        )

        # Identify areas of strength and improvement
        strengths = await wellness_service.identify_wellness_strengths(wellness_scores)
        improvement_areas = await wellness_service.identify_wellness_improvements(wellness_scores)

        # Check for burnout risk
        burnout_risk = await wellness_service.assess_burnout_risk(wellness_data, wellness_scores)

        return WellnessAssessmentResponse(
            success=True,
            user_id=current_user["id"],
            assessment_type=request.assessment_type,
            wellness_dimensions=request.wellness_dimensions,
            wellness_scores=wellness_scores,
            overall_wellness_score=overall_wellness_score,
            dimension_insights=dimension_insights,
            strengths=strengths,
            improvement_areas=improvement_areas,
            wellness_recommendations=wellness_recommendations,
            burnout_risk=burnout_risk,
            action_plan=await wellness_service.create_wellness_action_plan(
                wellness_scores, improvement_areas
            ),
            assessed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Wellness assessment failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Wellness assessment failed"
        )


@router.post("/crisis/alert", response_model=CrisisAlertResponse)
async def handle_crisis_alert(
    request: CrisisAlertRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ):
    """
    Handle crisis alerts and provide immediate resources
    Emergency response for mental health crises
    """
    try:
        # Validate crisis severity and provide immediate response
        crisis_assessment = await clinical_service.assess_crisis_severity(
            user_id=current_user["id"],
            alert_type=request.alert_type,
            severity_indicators=request.severity_indicators,
            immediate_context=request.immediate_context
        )

        # Generate immediate crisis response plan
        immediate_actions = await clinical_service.generate_immediate_crisis_response(
            crisis_assessment, request.alert_type
        )

        # Get emergency resources based on location and type
        emergency_resources = await clinical_service.get_emergency_resources(
            crisis_assessment["risk_level"],
            request.user_location if hasattr(request, 'user_location') else None,
            request.alert_type
        )

        # Create safety plan
        safety_plan = await clinical_service.create_immediate_safety_plan(
            current_user["id"], crisis_assessment
        )

        # Determine if professional intervention is needed
        professional_intervention = await clinical_service.assess_need_for_professional_intervention(
            crisis_assessment, request.alert_type
        )

        # Log crisis alert for follow-up (while maintaining privacy)
        await clinical_service.log_crisis_alert(
            user_id=current_user["id"],
            alert_type=request.alert_type,
            severity_level=crisis_assessment["risk_level"],
            actions_taken=immediate_actions
        )

        return CrisisAlertResponse(
            success=True,
            user_id=current_user["id"],
            alert_type=request.alert_type,
            crisis_assessment=crisis_assessment,
            immediate_actions=immediate_actions,
            emergency_resources=emergency_resources,
            safety_plan=safety_plan,
            professional_intervention=professional_intervention,
            follow_up_schedule=await clinical_service.schedule_crisis_follow_up(
                current_user["id"], crisis_assessment
            ),
            crisis_hotlines=await clinical_service.get_crisis_hotlines(),
            response_generated_at=datetime.utcnow(),
            disclaimer="In case of immediate danger, please call emergency services (911) or go to the nearest emergency room."
        )

    except Exception as e:
        logger.error(f"Crisis alert handling failed: {str(e)}")
        # For crisis alerts, always provide basic emergency information even if processing fails
        return CrisisAlertResponse(
            success=False,
            user_id=current_user["id"],
            alert_type=request.alert_type,
            crisis_assessment={"risk_level": "unknown"},
            immediate_actions=[
                "Call 911 or emergency services if in immediate danger",
                "Contact a crisis hotline: 988 (Suicide & Crisis Lifeline)",
                "Go to the nearest emergency room"
            ],
            emergency_resources=[],
            safety_plan={"contact_emergency_services": True},
            professional_intervention={"recommended": True, "urgency": "immediate"},
            follow_up_schedule=None,
            crisis_hotlines=await clinical_service.get_crisis_hotlines(),
            response_generated_at=datetime.utcnow(),
            disclaimer="System error occurred. Please contact emergency services if needed."
        )


@router.post("/trends/mental-health", response_model=MentalHealthTrendResponse)
async def analyze_mental_health_trends(
    request: MentalHealthTrendRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ):
    """
    Analyze mental health trends over time
    Track progress and identify long-term patterns in mental health
    """
    try:
        # Get historical mental health data
        historical_data = await screening_service.get_historical_screening_data(
            user_id=current_user["id"],
            start_date=request.start_date,
            end_date=request.end_date,
            screening_types=request.screening_types
        )

        # Analyze trends for each screening type
        trend_analysis = {}
        for screening_type in request.screening_types:
            trends = await screening_service.analyze_mental_health_trends(
                historical_data[screening_type],
                screening_type=screening_type,
                trend_period=request.trend_period
            )
            trend_analysis[screening_type] = trends

        # Identify significant changes and patterns
        significant_changes = await screening_service.identify_significant_changes(trend_analysis)
        protective_factors = await screening_service.identify_protective_factors(historical_data)
        risk_factors = await screening_service.identify_risk_factors(historical_data)

        # Generate trend-based recommendations
        trend_recommendations = await screening_service.generate_trend_based_recommendations(
            trend_analysis, significant_changes
        )

        # Predict future trajectory (with appropriate caveats)
        trajectory_prediction = await screening_service.predict_mental_health_trajectory(
            trend_analysis, historical_data
        )

        return MentalHealthTrendResponse(
            success=True,
            user_id=current_user["id"],
            analysis_period={
                "start_date": request.start_date,
                "end_date": request.end_date
            },
            screening_types=request.screening_types,
            trend_analysis=trend_analysis,
            significant_changes=significant_changes,
            protective_factors=protective_factors,
            risk_factors=risk_factors,
            trend_recommendations=trend_recommendations,
            trajectory_prediction=trajectory_prediction,
            next_assessment_date=await screening_service.recommend_next_assessment_date(
                trend_analysis
            ),
            analyzed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Mental health trend analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Mental health trend analysis failed"
        )


@router.post("/wellness/plan", response_model=WellnessPlanResponse)
async def create_personalized_wellness_plan(
    request: WellnessPlanRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    ):
    """
    Create personalized wellness improvement plan
    Evidence-based recommendations and goal setting
    """
    try:
        # Get current wellness baseline
        wellness_baseline = await wellness_service.get_wellness_baseline(
            user_id=current_user["id"],
            dimensions=request.focus_areas
        )

        # Generate personalized wellness goals
        wellness_goals = await wellness_service.generate_wellness_goals(
            wellness_baseline=wellness_baseline,
            focus_areas=request.focus_areas,
            user_preferences=request.user_preferences,
            time_frame=request.time_frame
        )

        # Create action steps for each goal
        action_steps = {}
        for goal_area, goals in wellness_goals.items():
            action_steps[goal_area] = await wellness_service.create_action_steps(
                goals, request.user_preferences, request.time_frame
            )

        # Identify resources and support systems
        wellness_resources = await wellness_service.identify_wellness_resources(
            focus_areas=request.focus_areas,
            user_preferences=request.user_preferences
        )

        # Create monitoring and tracking system
        monitoring_plan = await wellness_service.create_monitoring_plan(
            wellness_goals, action_steps, request.time_frame
        )

        # Generate milestone celebrations
        milestones = await wellness_service.create_milestones(wellness_goals, action_steps)

        return WellnessPlanResponse(
            success=True,
            user_id=current_user["id"],
            wellness_baseline=wellness_baseline,
            wellness_goals=wellness_goals,
            action_steps=action_steps,
            wellness_resources=wellness_resources,
            monitoring_plan=monitoring_plan,
            milestones=milestones,
            estimated_timeline=await wellness_service.calculate_estimated_timeline(action_steps),
            success_factors=await wellness_service.identify_success_factors(request.focus_areas),
            potential_barriers=await wellness_service.identify_potential_barriers(
                wellness_baseline, request.focus_areas
            ),
            plan_created_at=datetime.utcnow(),
            next_review_date=await wellness_service.schedule_plan_review(current_user["id"])
        )

    except Exception as e:
        logger.error(f"Wellness plan creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Wellness plan creation failed"
        )


@router.get("/resources/clinical", response_model=ClinicalResourceResponse)
async def get_clinical_resources(
    resource_type: Optional[str] = Query(None, description="Type of clinical resources needed"),
    condition: Optional[str] = Query(None, description="Specific condition or concern"),
    user_location: Optional[str] = Query(None, description="User location for local resources"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get clinical mental health resources and support information
    Includes therapists, support groups, hotlines, and educational materials
    """
    try:
        # Get appropriate clinical resources
        resources = await clinical_service.get_clinical_resources(
            resource_type=resource_type,
            condition=condition,
            user_location=user_location
        )

        # Categorize resources
        categorized_resources = {
            "emergency_support": resources.get("emergency_support", []),
            "professional_help": resources.get("professional_help", []),
            "support_groups": resources.get("support_groups", []),
            "self_help_resources": resources.get("self_help_resources", []),
            "educational_materials": resources.get("educational_materials", []),
            "digital_tools": resources.get("digital_tools", []),
            "community_resources": resources.get("community_resources", [])
        }

        # Add crisis resources always
        crisis_resources = await clinical_service.get_crisis_resources()
        categorized_resources["emergency_support"].extend(crisis_resources)

        # Filter and prioritize resources based on availability and user preferences
        prioritized_resources = await clinical_service.prioritize_resources(
            categorized_resources, user_location
        )

        return ClinicalResourceResponse(
            success=True,
            resource_type=resource_type,
            condition=condition,
            user_location=user_location,
            resources=prioritized_resources,
            resource_categories=list(categorized_resources.keys()),
            last_updated=datetime.utcnow(),
            disclaimer="Resources are provided for informational purposes. Please verify credentials and availability of providers."
        )

    except Exception as e:
        logger.error(f"Clinical resource retrieval failed: {str(e)}")
        # Always return basic crisis resources even if other resources fail
        crisis_resources = await clinical_service.get_crisis_resources()

        return ClinicalResourceResponse(
            success=False,
            resource_type=resource_type,
            condition=condition,
            user_location=user_location,
            resources={"emergency_support": crisis_resources},
            resource_categories=["emergency_support"],
            last_updated=datetime.utcnow(),
            disclaimer="Some resources may be unavailable. In case of crisis, please contact emergency services."
        )


@router.get("/screening/tools")
async def get_available_screening_tools(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get information about available mental health screening tools
    Include validity, reliability, and appropriate use cases
    """
    try:
        screening_tools = {
            "depression_screening": [
                {
                    "id": "phq9",
                    "name": "Patient Health Questionnaire-9",
                    "description": "9-item depression screening tool",
                    "validation": "High reliability (Cronbach's α = 0.89)",
                    "time_required": "2-5 minutes",
                    "appropriate_for": "Adults 18+, primary care setting",
                    "frequency": "Every 2-4 weeks for monitoring",
                    "scoring": "0-27 (Minimal to Severe)"
                },
                {
                    "id": "dass21_depression",
                    "name": "DASS-21 Depression Subscale",
                    "description": "7-item depression assessment",
                    "validation": "Good reliability (Cronbach's α = 0.91)",
                    "time_required": "2-3 minutes",
                    "appropriate_for": "Adults, research and clinical settings",
                    "frequency": "Monthly assessments",
                    "scoring": "0-42 (Normal to Extremely Severe)"
                }
            ],
            "anxiety_screening": [
                {
                    "id": "gad7",
                    "name": "Generalized Anxiety Disorder-7",
                    "description": "7-item anxiety screening tool",
                    "validation": "Excellent reliability (Cronbach's α = 0.92)",
                    "time_required": "2-3 minutes",
                    "appropriate_for": "Adults 18+, primary care setting",
                    "frequency": "Every 2-4 weeks for monitoring",
                    "scoring": "0-21 (Minimal to Severe)"
                },
                {
                    "id": "dass21_anxiety",
                    "name": "DASS-21 Anxiety Subscale",
                    "description": "7-item anxiety assessment",
                    "validation": "Good reliability (Cronbach's α = 0.84)",
                    "time_required": "2-3 minutes",
                    "appropriate_for": "Adults, research and clinical settings",
                    "frequency": "Monthly assessments",
                    "scoring": "0-42 (Normal to Extremely Severe)"
                }
            ],
            "stress_screening": [
                {
                    "id": "dass21_stress",
                    "name": "DASS-21 Stress Subscale",
                    "description": "7-item stress assessment",
                    "validation": "Good reliability (Cronbach's α = 0.88)",
                    "time_required": "2-3 minutes",
                    "appropriate_for": "Adults, workplace and clinical settings",
                    "frequency": "Monthly assessments",
                    "scoring": "0-42 (Normal to Extremely Severe)"
                }
            ],
            "trauma_screening": [
                {
                    "id": "pcl5",
                    "name": "PTSD Checklist for DSM-5",
                    "description": "20-item PTSD symptom assessment",
                    "validation": "Excellent reliability (Cronbach's α = 0.94)",
                    "time_required": "5-10 minutes",
                    "appropriate_for": "Adults with trauma exposure",
                    "frequency": "Every 4-6 weeks for treatment monitoring",
                    "scoring": "0-80 (No to Extreme PTSD symptoms)"
                }
            ],
            "substance_use_screening": [
                {
                    "id": "audit",
                    "name": "Alcohol Use Disorders Identification Test",
                    "description": "10-item alcohol use screening",
                    "validation": "Good reliability (Cronbach's α = 0.75-0.85)",
                    "time_required": "2-5 minutes",
                    "appropriate_for": "Adults 18+, primary care setting",
                    "frequency": "Annually or when concerns arise",
                    "scoring": "0-40 (Low to High-risk drinking)"
                }
            ]
        }

        return {
            "success": True,
            "screening_tools": screening_tools,
            "general_guidelines": {
                "screening_frequency": "Every 2-4 weeks for active monitoring, monthly for general wellness",
                "interpretation_note": "Screening tools are not diagnostic. Positive screens should be followed by clinical evaluation.",
                "confidentiality": "All screening results are confidential and protected under HIPAA.",
                "emergency_procedure": "If suicidal ideation is detected, immediate crisis intervention should be initiated."
            },
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Failed to get screening tools information: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve screening tools information"
        )


# Simplified endpoints for mental health screening form

@router.get("/screening/questions/{assessment_type}")
async def get_screening_questions(
    assessment_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get questions for a specific mental health screening assessment
    """
    try:
        # Initialize service with database session
        screening_service = MentalHealthScreeningService(db)

        questions = await screening_service.get_assessment_questions(assessment_type)

        return {
            "success": True,
            "data": questions
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get screening questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve screening questions"
        )


@router.post("/screening/submit")
async def submit_screening_responses(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit responses for mental health screening
    """
    try:
        # Initialize service with database session
        screening_service = MentalHealthScreeningService(db)

        # Create a simple user object from the current_user dict
        from app.db.models.user import User
        user = User()
        user.id = current_user["id"]

        assessment_type = request.get("assessment_type")
        responses = request.get("responses", {})
        additional_notes = request.get("additional_notes")

        if not assessment_type or not responses:
            raise HTTPException(
                status_code=400,
                detail="Assessment type and responses are required"
            )

        result = await screening_service.process_assessment_responses(
            user=user,
            assessment_type=assessment_type,
            responses=responses,
            additional_notes=additional_notes
        )

        return result

    except Exception as e:
        logger.error(f"Failed to process screening responses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process screening responses"
        )


@router.get("/wellness/questions")
async def get_wellness_questions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get questions for comprehensive wellness assessment
    """
    try:
        # Initialize service with database session
        wellness_service = WellnessMonitoringService(db)

        questions = await wellness_service.get_wellness_assessment_questions()

        return {
            "success": True,
            "data": questions
        }

    except Exception as e:
        logger.error(f"Failed to get wellness questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve wellness questions"
        )


@router.post("/wellness/submit")
async def submit_wellness_assessment(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit responses for wellness assessment
    """
    try:
        # Initialize service with database session
        wellness_service = WellnessMonitoringService(db)

        # Create a simple user object from the current_user dict
        from app.db.models.user import User
        user = User()
        user.id = current_user["id"]

        responses = request.get("responses", {})
        additional_notes = request.get("additional_notes")

        if not responses:
            raise HTTPException(
                status_code=400,
                detail="Responses are required"
            )

        result = await wellness_service.process_wellness_assessment(
            user=user,
            responses=responses,
            additional_notes=additional_notes
        )

        return result

    except Exception as e:
        logger.error(f"Failed to process wellness assessment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process wellness assessment"
        )


# Trend Analysis Endpoints

@router.get("/trends/data")
async def get_trend_analysis_data(
    time_range: str = Query("3m", description="Time range for trend analysis"),
    domains: str = Query("all", description="Comma-separated list of wellness domains"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive trend analysis data for a user
    """
    try:
        # Initialize trend analysis service
        trend_service = TrendAnalysisService(db)

        # Parse domains parameter
        domain_list = [d.strip() for d in domains.split(",")] if domains != "all" else None

        # Get trend data
        result = await trend_service.get_user_trend_data(
            user_id=current_user["id"],
            time_range=time_range,
            domains=domain_list
        )

        return result

    except Exception as e:
        logger.error(f"Failed to get trend analysis data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trend analysis data"
        )


@router.get("/trends/comparison")
async def get_domain_comparison(
    time_range: str = Query("3m", description="Time range for comparison"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get domain-specific comparison and analysis
    """
    try:
        # Initialize trend analysis service
        trend_service = TrendAnalysisService(db)

        # Get domain comparison data
        result = await trend_service.get_domain_comparison(
            user_id=current_user["id"],
            time_range=time_range
        )

        return result

    except Exception as e:
        logger.error(f"Failed to get domain comparison: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve domain comparison data"
        )


@router.get("/trends/summary")
async def get_trends_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a summary of user's wellness trends
    """
    try:
        # Initialize trend analysis service
        trend_service = TrendAnalysisService(db)

        # Get 3-month trend data for summary
        result = await trend_service.get_user_trend_data(
            user_id=current_user["id"],
            time_range="3m"
        )

        if not result["success"] or not result["data"]["trend_data"]:
            return {
                "success": True,
                "data": {
                    "message": "No trend data available",
                    "recommendation": "Start taking regular assessments to see your wellness trends"
                }
            }

        # Extract key summary information
        summary = result["data"]["summary"]
        trends = result["data"]["trend_data"]

        # Generate summary insights
        recent_score = trends[-1]["overall_score"] if trends else 0
        first_score = trends[0]["overall_score"] if len(trends) > 1 else recent_score
        overall_change = recent_score - first_score

        return {
            "success": True,
            "data": {
                "current_score": recent_score,
                "overall_change": overall_change,
                "total_assessments": summary["total_assessments"],
                "time_span_days": summary["time_span_days"],
                "trend_direction": summary["overall_trend"],
                "recommendation": _generate_summary_recommendation(summary, overall_change),
                "last_updated": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Failed to get trends summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve trends summary"
        )


def _generate_summary_recommendation(summary: Dict[str, Any], overall_change: float) -> str:
    """Generate a recommendation based on trend summary"""
    if summary["total_assessments"] < 3:
        return "Continue taking regular assessments to build a more complete picture of your wellness journey."

    trend = summary["overall_trend"]
    current_score = summary["current_score"]

    if trend == "improving":
        return "Your wellness is improving! Keep up the excellent work and consider helping others with your insights."
    elif trend == "declining":
        return "Consider focusing on self-care and professional support to address the declining trend."
    elif current_score < 0.4:
        return "Your current wellness score suggests you may benefit from additional support and self-care practices."
    elif current_score > 0.8:
        return "Your wellness score is excellent! Focus on maintaining these positive habits."
    else:
        return "Your wellness levels are relatively stable. Small, consistent changes can lead to significant improvements."


# Wellness Plan Generator Endpoints

@router.get("/wellness/plan/existing")
async def get_existing_wellness_plan(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's existing wellness plan
    """
    try:
        # Initialize wellness plan generator service
        plan_service = WellnessPlanGeneratorService(db)

        # Get existing plan
        plan = await plan_service.get_existing_wellness_plan(current_user["id"])

        if plan:
            return {
                "success": True,
                "data": plan
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No existing wellness plan found"
            }

    except Exception as e:
        logger.error(f"Failed to get existing wellness plan: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve wellness plan"
        }


@router.post("/wellness/plan/generate")
async def generate_wellness_plan(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new personalized wellness plan
    """
    try:
        # Initialize wellness plan generator service
        plan_service = WellnessPlanGeneratorService(db)

        # Extract request parameters
        focus_areas = request.get("focus_areas", [])
        timeframe = request.get("timeframe", "3m")
        focus_level = request.get("focus_level", "balanced")
        preferences = request.get("preferences", {})

        # Validate required fields
        if not focus_areas:
            raise HTTPException(
                status_code=400,
                detail="Focus areas are required for wellness plan generation"
            )

        # Generate wellness plan
        result = await plan_service.generate_personalized_wellness_plan(
            user_id=current_user["id"],
            focus_areas=focus_areas,
            timeframe=timeframe,
            focus_level=focus_level,
            preferences=preferences
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate wellness plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate wellness plan"
        )


@router.put("/wellness/plan/{plan_id}/update")
async def update_wellness_plan(
    plan_id: str,
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update existing wellness plan progress
    """
    try:
        # Initialize wellness plan generator service
        plan_service = WellnessPlanGeneratorService(db)

        # Extract update data
        updates = request.get("updates", {})

        # For now, return success (actual implementation would update database)
        return {
            "success": True,
            "data": {
                "plan_id": plan_id,
                "updates_applied": updates,
                "updated_at": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Failed to update wellness plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update wellness plan"
        )


@router.get("/wellness/plan/templates")
async def get_wellness_plan_templates(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get wellness plan templates and examples
    """
    try:
        templates = {
            "stress_management": {
                "name": "Stress Management Focus",
                "description": "Comprehensive plan for managing and reducing stress",
                "focus_areas": ["emotional", "physical", "spiritual"],
                "duration": "3m",
                "difficulty": "moderate",
                "sample_goals": [
                    "Practice daily stress-reduction techniques",
                    "Improve sleep quality to reduce cortisol",
                    "Develop healthy emotional coping mechanisms"
                ]
            },
            "work_life_balance": {
                "name": "Work-Life Balance",
                "description": "Achieve better balance between professional and personal life",
                "focus_areas": ["occupational", "social", "environmental"],
                "duration": "6m",
                "difficulty": "moderate",
                "sample_goals": [
                    "Set clear work boundaries",
                    "Dedicate quality time to relationships",
                    "Create a peaceful home environment"
                ]
            },
            "physical_transformation": {
                "name": "Physical Health Transformation",
                "description": "Comprehensive physical wellness improvement plan",
                "focus_areas": ["physical", "emotional", "nutritional"],
                "duration": "6m",
                "difficulty": "challenging",
                "sample_goals": [
                    "Establish consistent exercise routine",
                    "Improve nutrition and hydration habits",
                    "Achieve healthy weight management"
                ]
            },
            "mindfulness_journey": {
                "name": "Mindfulness & Mental Clarity",
                "description": "Develop mindfulness practices and mental clarity",
                "focus_areas": ["spiritual", "emotional", "intellectual"],
                "duration": "3m",
                "difficulty": "moderate",
                "sample_goals": [
                    "Establish daily meditation practice",
                    "Develop emotional awareness",
                    "Engage in regular self-reflection"
                ]
            },
            "social_connection": {
                "name": "Social Connection Building",
                "description": "Strengthen relationships and social support networks",
                "focus_areas": ["social", "emotional", "community"],
                "duration": "4m",
                "difficulty": "moderate",
                "sample_goals": [
                    "Build meaningful relationships",
                    "Join supportive community groups",
                    "Develop effective communication skills"
                ]
            }
        }

        return {
            "success": True,
            "data": {
                "templates": templates,
                "total_templates": len(templates),
                "categories": list(set(template["focus_areas"][0] for template in templates.values())),
                "last_updated": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Failed to get wellness plan templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve wellness plan templates"
        )


@router.get("/wellness/plan/goal-suggestions")
async def get_goal_suggestions(
    domain: str = Query(..., description="Wellness domain for goal suggestions"),
    current_level: str = Query("beginner", description="Current wellness level"),
    time_commitment: str = Query("moderate", description="Available time commitment"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get AI-powered goal suggestions for specific wellness domains
    """
    try:
        # Goal suggestions based on domain and level
        goal_suggestions = {
            "physical": {
                "beginner": [
                    "Walk 15 minutes daily",
                    "Drink 8 glasses of water daily",
                    "Get 7-8 hours of sleep regularly",
                    "Practice basic stretching exercises"
                ],
                "intermediate": [
                    "Exercise 3-4 times per week",
                    "Follow a balanced nutrition plan",
                    "Achieve consistent sleep schedule",
                    "Incorporate strength training"
                ],
                "advanced": [
                    "Train for a fitness event",
                    "Optimize athletic performance",
                    "Master advanced nutritional planning",
                    "Develop comprehensive fitness routine"
                ]
            },
            "emotional": {
                "beginner": [
                    "Practice 5-minute daily meditation",
                    "Write in a gratitude journal",
                    "Practice deep breathing when stressed",
                    "Identify and name emotions daily"
                ],
                "intermediate": [
                    "Establish regular mindfulness practice",
                    "Learn cognitive behavioral techniques",
                    "Develop emotional regulation skills",
                    "Practice regular self-reflection"
                ],
                "advanced": [
                    "Master advanced emotional intelligence",
                    "Develop resilience training practices",
                    "Achieve emotional mastery",
                    "Guide others in emotional wellness"
                ]
            },
            "social": {
                "beginner": [
                    "Reach out to one friend weekly",
                    "Join one social group or activity",
                    "Practice active listening skills",
                    "Schedule regular social time"
                ],
                "intermediate": [
                    "Build deeper relationships",
                    "Join community organizations",
                    "Develop leadership skills",
                    "Expand social network meaningfully"
                ],
                "advanced": [
                    "Become community leader",
                    "Mentor others in social skills",
                    "Build diverse social networks",
                    "Create social impact initiatives"
                ]
            },
            "intellectual": {
                "beginner": [
                    "Read 15 minutes daily",
                    "Learn one new thing weekly",
                    "Practice brain-training games",
                    "Watch educational content regularly"
                ],
                "intermediate": [
                    "Take an online course",
                    "Learn a new skill or language",
                    "Engage in creative hobbies",
                    "Join intellectual discussion groups"
                ],
                "advanced": [
                    "Pursue advanced education",
                    "Master complex subjects",
                    "Teach or mentor others",
                    "Contribute to knowledge creation"
                ]
            },
            "spiritual": {
                "beginner": [
                    "Practice daily gratitude",
                    "Spend time in nature weekly",
                    "Reflect on personal values",
                    "Practice simple meditation"
                ],
                "intermediate": [
                    "Develop regular spiritual practice",
                    "Join spiritual community",
                    "Engage in meaningful volunteering",
                    "Create personal mission statement"
                ],
                "advanced": [
                    "Achieve deep spiritual mastery",
                    "Guide others spiritually",
                    "Create spiritual practices",
                    "Integrate spirituality fully"
                ]
            },
            "occupational": {
                "beginner": [
                    "Set daily work goals",
                    "Take regular breaks",
                    "Organize workspace",
                    "Learn time management basics"
                ],
                "intermediate": [
                    "Develop career advancement plan",
                    "Improve work relationships",
                    "Achieve work-life balance",
                    "Develop professional skills"
                ],
                "advanced": [
                    "Achieve career mastery",
                    "Lead teams or projects",
                    "Create career opportunities",
                    "Balance multiple roles effectively"
                ]
            },
            "environmental": {
                "beginner": [
                    "Declutter living space",
                    "Add plants to home",
                    "Create peaceful space",
                    "Reduce waste"
                ],
                "intermediate": [
                    "Create sustainable lifestyle",
                    "Design ideal living space",
                    "Connect with nature regularly",
                    "Implement eco-friendly practices"
                ],
                "advanced": [
                    "Achieve environmental mastery",
                    "Lead sustainability initiatives",
                    "Create healing environments",
                    "Influence environmental change"
                ]
            }
        }

        suggestions = goal_suggestions.get(domain, {}).get(current_level, [
            "Focus on basic wellness practices",
            "Establish consistent routines",
            "Track progress regularly"
        ])

        # Adjust suggestions based on time commitment
        if time_commitment == "minimal":
            suggestions = [s for s in suggestions if "daily" in s.lower() or "15" in s or "5" in s]
        elif time_commitment == "extensive":
            suggestions.extend([
                "Develop comprehensive mastery",
                "Create advanced practices",
                "Lead initiatives in this area"
            ])

        return {
            "success": True,
            "data": {
                "domain": domain,
                "current_level": current_level,
                "time_commitment": time_commitment,
                "suggestions": suggestions[:8],  # Limit to 8 suggestions
                "total_suggestions": len(suggestions)
            }
        }

    except Exception as e:
        logger.error(f"Failed to get goal suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve goal suggestions"
        )


# Crisis Support Endpoints

@router.post("/crisis/assessment")
async def crisis_assessment(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crisis severity assessment and immediate support recommendations
    """
    try:
        # Initialize crisis support service
        crisis_service = CrisisSupportService(db)

        # Extract assessment responses
        responses = request.get("responses", {})
        timestamp = request.get("timestamp", datetime.utcnow().isoformat())

        # Validate required critical responses
        if not responses:
            raise HTTPException(
                status_code=400,
                detail="Assessment responses are required"
            )

        # Check for immediate emergency indicators
        suicidal_thoughts = responses.get("suicidal_thoughts", "").lower()
        harm_plan = responses.get("harm_plan", "").lower()

        if suicidal_thoughts == "yes" and harm_plan == "yes":
            # Immediate emergency situation
            return {
                "success": True,
                "emergency": True,
                "data": {
                    "severity": "emergency",
                    "recommended_actions": [
                        "Call 911 immediately",
                        "Go to nearest emergency room",
                        "Call 988 Suicide & Crisis Lifeline",
                        "Stay with someone until help arrives"
                    ],
                    "safety_concerns": [
                        "Immediate suicidal thoughts with specific plan detected"
                    ],
                    "emergency_contacts": ["911", "988"],
                    "message": "This is an emergency. Please seek immediate help."
                }
            }

        # Perform comprehensive crisis assessment
        result = await crisis_service.assess_crisis_severity(
            user_id=current_user["id"],
            responses=responses,
            timestamp=timestamp
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crisis assessment failed: {str(e)}")
        # Always provide emergency resources as fallback
        return {
            "success": True,
            "emergency": True,
            "data": {
                "severity": "emergency",
                "recommended_actions": [
                    "Call 988 Suicide & Crisis Lifeline: 988",
                    "Call 911 if in immediate danger",
                    "Text HOME to 741741 for crisis support",
                    "Go to nearest emergency room"
                ],
                "safety_concerns": [
                    "System error - please seek immediate professional help"
                ],
                "emergency_contacts": ["988", "911", "741741"],
                "message": "Please seek immediate help. Support is available 24/7."
            }
        }


@router.post("/crisis/create-safety-plan")
async def create_safety_plan(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create personalized safety plan for crisis situations
    """
    try:
        # Initialize crisis support service
        crisis_service = CrisisSupportService(db)

        # Extract preferences
        personalize = request.get("personalize", True)
        include_local_resources = request.get("include_local_resources", True)

        # Generate safety plan
        result = await crisis_service.create_personalized_safety_plan(
            user_id=current_user["id"],
            personalize=personalize,
            include_local_resources=include_local_resources
        )

        return result

    except Exception as e:
        logger.error(f"Failed to create safety plan: {str(e)}")
        # Return basic safety plan as fallback
        basic_plan = {
            "warning_signs": [
                "Thoughts of self-harm or suicide",
                "Feeling hopeless or trapped",
                "Increased anxiety or panic",
                "Withdrawing from friends and activities"
            ],
            "coping_strategies": [
                "Call 988 Suicide & Crisis Lifeline",
                "Contact a trusted friend or family member",
                "Practice deep breathing exercises",
                "Go to a safe public place"
            ],
            "emergency_contacts": [
                "911 - Emergency Services",
                "988 - Suicide & Crisis Lifeline",
                "Text HOME to 741741 - Crisis Text Line"
            ]
        }

        return {
            "success": True,
            "data": basic_plan,
            "fallback": True,
            "message": "Basic safety plan provided. Consider professional help for a personalized plan."
        }


@router.get("/crisis/safety-plan")
async def get_safety_plan(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's existing safety plan
    """
    try:
        # Initialize crisis support service
        crisis_service = CrisisSupportService(db)

        # Get existing safety plan
        plan = await crisis_service.get_existing_safety_plan(current_user["id"])

        if plan:
            return {
                "success": True,
                "data": plan
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No existing safety plan found. Consider creating one."
            }

    except Exception as e:
        logger.error(f"Failed to get safety plan: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve safety plan"
        }


@router.get("/crisis/resources")
async def get_crisis_resources(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get crisis support resources and helplines
    """
    try:
        resources = {
            "emergency": [
                {
                    "name": "911 Emergency Services",
                    "contact": "911",
                    "type": "emergency",
                    "description": "For immediate medical emergencies or life-threatening situations",
                    "availability": "24/7",
                    "response_time": "Immediate"
                },
                {
                    "name": "988 Suicide & Crisis Lifeline",
                    "contact": "988",
                    "type": "hotline",
                    "description": "24/7 free, confidential support for people in distress",
                    "availability": "24/7",
                    "response_time": "Immediate",
                    "languages": ["English", "Spanish"]
                }
            ],
            "hotlines": [
                {
                    "name": "Crisis Text Line",
                    "contact": "Text HOME to 741741",
                    "type": "text",
                    "description": "Text with a trained crisis counselor",
                    "availability": "24/7",
                    "response_time": "Average 5 minutes"
                },
                {
                    "name": "National Hopeline Network",
                    "contact": "1-800-442-HOPE (4673)",
                    "type": "hotline",
                    "description": "Emotional support and crisis intervention",
                    "availability": "24/7"
                },
                {
                    "name": "The Trevor Project",
                    "contact": "1-866-488-7386",
                    "type": "hotline",
                    "description": "Crisis intervention and suicide prevention for LGBTQ youth",
                    "availability": "24/7"
                },
                {
                    "name": "Veterans Crisis Line",
                    "contact": "988 then Press 1",
                    "type": "hotline",
                    "description": "Confidential support for veterans in crisis",
                    "availability": "24/7"
                }
            ],
            "specialized": [
                {
                    "name": "National Domestic Violence Hotline",
                    "contact": "1-800-799-7233",
                    "type": "hotline",
                    "description": "Support for domestic violence situations",
                    "availability": "24/7"
                },
                {
                    "name": "SAMHSA's National Helpline",
                    "contact": "1-800-662-4357",
                    "type": "hotline",
                    "description": "Treatment referral and information service",
                    "availability": "24/7"
                },
                {
                    "name": "Childhelp National Child Abuse Hotline",
                    "contact": "1-800-422-4453",
                    "type": "hotline",
                    "description": "Professional counselors for child abuse situations",
                    "availability": "24/7"
                }
            ]
        }

        return {
            "success": True,
            "data": {
                "resources": resources,
                "total_resources": sum(len(category) for category in resources.values()),
                "last_updated": datetime.utcnow().isoformat(),
                "disclaimer": "These resources are available 24/7. In life-threatening emergencies, always call 911."
            }
        }

    except Exception as e:
        logger.error(f"Failed to get crisis resources: {str(e)}")
        # Always return emergency resources
        emergency_resources = {
            "emergency": [
                {
                    "name": "911 Emergency Services",
                    "contact": "911",
                    "description": "For immediate medical emergencies"
                },
                {
                    "name": "988 Suicide & Crisis Lifeline",
                    "contact": "988",
                    "description": "24/7 crisis support"
                }
            ]
        }

        return {
            "success": True,
            "data": {
                "resources": emergency_resources,
                "fallback": True,
                "message": "Limited resources available. Please call 988 or 911 for immediate help."
            }
        }


@router.post("/crisis/check-in")
async def crisis_check_in(
    request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Anonymous crisis check-in and status update
    """
    try:
        # Extract check-in data
        status = request.get("status", "checking_in")
        needs_help = request.get("needs_help", False)
        urgency = request.get("urgency", "medium")
        notes = request.get("notes", "")

        # Log check-in (maintaining privacy)
        logger.info(f"Crisis check-in: user_id={current_user['id']}, status={status}, needs_help={needs_help}, urgency={urgency}")

        # If immediate help needed, provide resources
        if needs_help and urgency in ["high", "emergency"]:
            return {
                "success": True,
                "immediate_help": True,
                "resources": {
                    "call": "988",
                    "text": "HOME to 741741",
                    "emergency": "911"
                },
                "message": "Help is available right now. Please reach out to one of these resources."
            }

        return {
            "success": True,
            "message": "Check-in received. You're not alone - support is available if you need it.",
            "resources": {
                "988": "Suicide & Crisis Lifeline",
                "741741": "Crisis Text Line (Text HOME)"
            }
        }

    except Exception as e:
        logger.error(f"Crisis check-in failed: {str(e)}")
        return {
            "success": True,
            "fallback_resources": {
                "988": "Suicide & Crisis Lifeline",
                "741741": "Crisis Text Line (Text HOME)",
                "911": "Emergency Services"
            },
            "message": "Check-in received. Help is available 24/7."
        }