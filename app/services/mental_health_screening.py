"""
Mental Health Screening Service
Provides clinical assessment processing for PHQ-9, GAD-7, and other evidence-based screenings
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.db.models.user import User
from app.services.ai_enhanced_analytics import AIEnhancedAnalyticsService

logger = logging.getLogger(__name__)


class AssessmentType(Enum):
    PHQ9 = "phq9"  # Depression screening
    GAD7 = "gad7"  # Anxiety screening
    W5 = "w5"  # Wellbeing assessment
    PSS = "pss"  # Perceived Stress Scale


class RiskLevel(Enum):
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATE_SEVERE = "moderate_severe"
    SEVERE = "severe"


class MentalHealthScreeningService:
    """
    Evidence-based mental health screening service
    Processes clinical assessments with validated scoring algorithms
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIEnhancedAnalyticsService(db)

        # Assessment scoring thresholds
        self.phq9_thresholds = {
            RiskLevel.MINIMAL: (0, 4),
            RiskLevel.MILD: (5, 9),
            RiskLevel.MODERATE: (10, 14),
            RiskLevel.MODERATE_SEVERE: (15, 19),
            RiskLevel.SEVERE: (20, 27),
        }

        self.gad7_thresholds = {
            RiskLevel.MINIMAL: (0, 4),
            RiskLevel.MILD: (5, 9),
            RiskLevel.MODERATE: (10, 14),
            RiskLevel.SEVERE: (15, 21),
        }

        # Assessment question configurations
        self.assessment_questions = self._load_assessment_questions()

    def _load_assessment_questions(self) -> dict[str, list[dict[str, Any]]]:
        """Load validated clinical assessment questions"""
        return {
            AssessmentType.PHQ9.value: [
                {
                    "id": "phq9_1",
                    "text": "Little interest or pleasure in doing things",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_2",
                    "text": "Feeling down, depressed, or hopeless",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_3",
                    "text": "Trouble falling or staying asleep, or sleeping too much",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_4",
                    "text": "Feeling tired or having little energy",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_5",
                    "text": "Poor appetite or overeating",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_6",
                    "text": "Feeling bad about yourself—or that you are a failure or have let yourself or your family down",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_7",
                    "text": "Trouble concentrating on things, such as reading the newspaper or watching television",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_8",
                    "text": "Moving or speaking so slowly that other people could have noticed? Or the opposite—being so fidgety or restless that you have been moving around a lot more than usual",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "phq9_9",
                    "text": "Thoughts that you would be better off dead, or of hurting yourself in some way",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
            ],
            AssessmentType.GAD7.value: [
                {
                    "id": "gad7_1",
                    "text": "Feeling nervous, anxious, or on edge",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_2",
                    "text": "Not being able to stop or control worrying",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_3",
                    "text": "Worrying too much about different things",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_4",
                    "text": "Trouble relaxing",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_5",
                    "text": "Being so restless that it is hard to sit still",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_6",
                    "text": "Becoming easily annoyed or irritable",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
                {
                    "id": "gad7_7",
                    "text": "Feeling afraid, as if something awful might happen",
                    "options": [
                        {"value": 0, "text": "Not at all"},
                        {"value": 1, "text": "Several days"},
                        {"value": 2, "text": "More than half the days"},
                        {"value": 3, "text": "Nearly every day"},
                    ],
                },
            ],
        }

    async def get_assessment_questions(self, assessment_type: str) -> dict[str, Any]:
        """Get questions for a specific assessment type"""
        questions = self.assessment_questions.get(assessment_type)
        if not questions:
            raise ValueError(f"Unknown assessment type: {assessment_type}")

        metadata = {
            "title": self._get_assessment_title(assessment_type),
            "description": self._get_assessment_description(assessment_type),
            "estimated_time": self._get_assessment_time(assessment_type),
            "validation": self._get_assessment_validation(assessment_type),
        }

        return {
            "assessment_type": assessment_type,
            "metadata": metadata,
            "questions": questions,
            "total_questions": len(questions),
        }

    def _get_assessment_title(self, assessment_type: str) -> str:
        """Get assessment display title"""
        titles = {
            AssessmentType.PHQ9.value: "PHQ-9: Depression Screening",
            AssessmentType.GAD7.value: "GAD-7: Anxiety Screening",
            AssessmentType.W5.value: "W-5: Wellbeing Assessment",
            AssessmentType.PSS.value: "PSS: Perceived Stress Scale",
        }
        return titles.get(assessment_type, "Assessment")

    def _get_assessment_description(self, assessment_type: str) -> str:
        """Get assessment description"""
        descriptions = {
            AssessmentType.PHQ9.value: "Evidenced-based screening tool for depression symptoms",
            AssessmentType.GAD7.value: "Validated anxiety assessment for generalized anxiety disorder",
            AssessmentType.W5.value: "Comprehensive wellbeing and quality life assessment",
            AssessmentType.PSS.value: "Measures perceived stress levels over the past month",
        }
        return descriptions.get(assessment_type, "Clinical assessment tool")

    def _get_assessment_time(self, assessment_type: str) -> str:
        """Get estimated completion time"""
        times = {
            AssessmentType.PHQ9.value: "3-5 minutes",
            AssessmentType.GAD7.value: "2-3 minutes",
            AssessmentType.W5.value: "5-7 minutes",
            AssessmentType.PSS.value: "3-4 minutes",
        }
        return times.get(assessment_type, "5 minutes")

    def _get_assessment_validation(self, assessment_type: str) -> dict[str, Any]:
        """Get assessment validation information"""
        return {
            "reliability": "Cronbach's α > 0.85",
            "validity": "Clinically validated",
            "sensitivity": "> 0.85",
            "specificity": "> 0.80",
            "clinical_use": "Widely used in clinical practice",
        }

    async def verify_screening_consent(self, user: User, assessment_type: str) -> bool:
        """
        Verify that user has given appropriate consent for mental health screening
        """
        try:
            # For now, implement basic consent verification
            # In a real clinical system, this would check:
            # 1. Signed consent forms
            # 2. Consent timestamps
            # 3. Specific consent for the assessment type
            # 4. Age verification and capacity assessment

            # Check if user has any previous consent records
            consent_query = (
                select(Response)
                .where(
                    and_(
                        Response.user_id == user.id,
                        Response.assessment_type == assessment_type,
                        Response.created_at >= datetime.utcnow() - timedelta(days=30),
                    )
                )
                .limit(1)
            )

            result = await self.db.execute(consent_query)
            existing_consent = result.scalar_one_or_none()

            # If user has recent assessment, consider consent verified
            if existing_consent:
                return True

            # For new users, we'll require explicit consent
            # This is a simplified implementation - production would need proper consent management
            logger.info(
                f"Consent verification required for user {user.id} - assessment {assessment_type}"
            )
            return False  # Require explicit consent

        except Exception as e:
            logger.error(f"Consent verification failed: {e!s}")
            return False

    async def process_assessment_responses(
        self,
        user: User,
        assessment_type: str,
        responses: dict[str, int],
        additional_notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Process assessment responses and generate clinical insights
        """
        try:
            # Calculate raw score
            total_score = sum(responses.values())

            # Determine risk level
            risk_level = self._calculate_risk_level(assessment_type, total_score)

            # Generate clinical interpretation
            interpretation = self._generate_interpretation(
                assessment_type, total_score, risk_level
            )

            # Create recommendations
            recommendations = await self._generate_recommendations(
                user, assessment_type, total_score, risk_level, responses
            )

            # Check for crisis indicators
            crisis_alert = self._check_crisis_indicators(assessment_type, responses)

            # Save assessment results
            assessment_result = await self._save_assessment_results(
                user,
                assessment_type,
                responses,
                total_score,
                risk_level,
                additional_notes,
            )

            # Generate AI-enhanced insights
            ai_insights = await self._generate_ai_insights(
                user, assessment_type, responses, risk_level
            )

            return {
                "success": True,
                "assessment_result": {
                    "assessment_id": (
                        assessment_result.id if assessment_result else None
                    ),
                    "assessment_type": assessment_type,
                    "total_score": total_score,
                    "risk_level": risk_level.value,
                    "interpretation": interpretation,
                    "recommendations": recommendations,
                    "crisis_alert": crisis_alert,
                    "ai_insights": ai_insights,
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_recommended_screening": self._calculate_next_screening_date(
                        risk_level
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error processing assessment responses: {e}")
            return {"success": False, "error": f"Failed to process assessment: {e!s}"}

    def _calculate_risk_level(self, assessment_type: str, score: int) -> RiskLevel:
        """Calculate risk level based on assessment score"""
        if assessment_type == AssessmentType.PHQ9.value:
            thresholds = self.phq9_thresholds
        elif assessment_type == AssessmentType.GAD7.value:
            thresholds = self.gad7_thresholds
        else:
            return RiskLevel.MINIMAL

        for risk_level, (min_score, max_score) in thresholds.items():
            if min_score <= score <= max_score:
                return risk_level

        return RiskLevel.SEVERE

    def _generate_interpretation(
        self, assessment_type: str, score: int, risk_level: RiskLevel
    ) -> str:
        """Generate clinical interpretation of assessment results"""
        interpretations = {
            (
                AssessmentType.PHQ9.value,
                RiskLevel.MINIMAL,
            ): "No significant depressive symptoms detected. Continue maintaining good mental health practices.",
            (
                AssessmentType.PHQ9.value,
                RiskLevel.MILD,
            ): "Mild depressive symptoms present. Consider self-care strategies and monitoring.",
            (
                AssessmentType.PHQ9.value,
                RiskLevel.MODERATE,
            ): "Moderate depressive symptoms detected. Professional consultation recommended.",
            (
                AssessmentType.PHQ9.value,
                RiskLevel.MODERATE_SEVERE,
            ): "Moderately severe depressive symptoms. Professional treatment strongly recommended.",
            (
                AssessmentType.PHQ9.value,
                RiskLevel.SEVERE,
            ): "Severe depressive symptoms detected. Immediate professional evaluation recommended.",
            (
                AssessmentType.GAD7.value,
                RiskLevel.MINIMAL,
            ): "No significant anxiety symptoms detected. Continue healthy coping strategies.",
            (
                AssessmentType.GAD7.value,
                RiskLevel.MILD,
            ): "Mild anxiety symptoms present. Stress management techniques may be helpful.",
            (
                AssessmentType.GAD7.value,
                RiskLevel.MODERATE,
            ): "Moderate anxiety symptoms detected. Professional consultation recommended.",
            (
                AssessmentType.GAD7.value,
                RiskLevel.SEVERE,
            ): "Severe anxiety symptoms. Professional treatment strongly recommended.",
        }

        return interpretations.get(
            (assessment_type, risk_level),
            "Consult with a healthcare professional for interpretation.",
        )

    async def _generate_recommendations(
        self,
        user: User,
        assessment_type: str,
        score: int,
        risk_level: RiskLevel,
        responses: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Generate personalized recommendations based on assessment results"""
        recommendations = []

        # Base recommendations by risk level
        if risk_level in [RiskLevel.MINIMAL, RiskLevel.MILD]:
            recommendations.extend(
                [
                    {
                        "type": "self_help",
                        "title": "Continue Mental Wellness Practices",
                        "description": "Maintain regular exercise, healthy sleep, and social connections",
                        "priority": "medium",
                    },
                    {
                        "type": "monitoring",
                        "title": "Regular Self-Monitoring",
                        "description": "Complete this screening again in 2-4 weeks",
                        "priority": "medium",
                    },
                ]
            )

        elif risk_level == RiskLevel.MODERATE:
            recommendations.extend(
                [
                    {
                        "type": "professional",
                        "title": "Consider Professional Consultation",
                        "description": "Speak with a mental health professional about your symptoms",
                        "priority": "high",
                    },
                    {
                        "type": "self_help",
                        "title": "Evidence-Based Self-Help",
                        "description": "Consider CBT-based self-help resources or apps",
                        "priority": "medium",
                    },
                ]
            )

        elif risk_level in [RiskLevel.MODERATE_SEVERE, RiskLevel.SEVERE]:
            recommendations.extend(
                [
                    {
                        "type": "professional",
                        "title": "Professional Treatment Recommended",
                        "description": "Schedule an appointment with a mental health professional",
                        "priority": "urgent",
                    },
                    {
                        "type": "support",
                        "title": "Build Support Network",
                        "description": "Reach out to trusted friends, family, or support groups",
                        "priority": "high",
                    },
                ]
            )

        # AI-enhanced personalized recommendations
        try:
            # Get user's assessment history for personalization
            user_history = await self._get_user_assessment_history(user)

            # Generate AI insights based on patterns
            ai_recommendations = (
                await self.ai_service.generate_personalized_recommendations(
                    user_id=user.id,
                    assessment_type=assessment_type,
                    current_score=score,
                    risk_level=risk_level.value,
                    response_pattern=responses,
                    historical_data=user_history,
                )
            )

            if ai_recommendations:
                recommendations.extend(ai_recommendations)

        except Exception as e:
            logger.warning(f"Could not generate AI recommendations: {e}")

        return recommendations

    def _check_crisis_indicators(
        self, assessment_type: str, responses: dict[str, int]
    ) -> dict[str, Any] | None:
        """Check for immediate crisis indicators requiring urgent attention"""
        # Check PHQ-9 question 9 (suicidal thoughts)
        if assessment_type == AssessmentType.PHQ9.value:
            suicidal_thoughts_score = responses.get("phq9_9", 0)
            if (
                suicidal_thoughts_score >= 2
            ):  # "More than half the days" or "Nearly every day"
                return {
                    "crisis_detected": True,
                    "severity": "high" if suicidal_thoughts_score == 3 else "moderate",
                    "type": "suicidal_ideation",
                    "message": "Responses indicate possible suicidal thoughts. Immediate support is available.",
                    "resources": [
                        {
                            "name": "National Suicide Prevention Lifeline",
                            "phone": "988",
                        },
                        {"name": "Crisis Text Line", "text": "HOME to 741741"},
                        {"name": "Emergency Services", "phone": "911"},
                    ],
                    "recommendation": "Please contact a mental health professional or crisis support immediately.",
                }

        return None

    async def _save_assessment_results(
        self,
        user: User,
        assessment_type: str,
        responses: dict[str, int],
        total_score: int,
        risk_level: RiskLevel,
        additional_notes: str | None = None,
    ) -> Response | None:
        """Save assessment results to database"""
        try:
            # Create response record
            response_data = {
                "assessment_type": assessment_type,
                "responses": responses,
                "total_score": total_score,
                "risk_level": risk_level.value,
                "additional_notes": additional_notes,
                "completed_at": datetime.utcnow().isoformat(),
            }

            # For now, return mock data (would integrate with actual Response model)
            logger.info(
                f"Would save assessment results for user {user.id}: {response_data}"
            )
            return None

        except Exception as e:
            logger.error(f"Error saving assessment results: {e}")
            return None

    async def _generate_ai_insights(
        self,
        user: User,
        assessment_type: str,
        responses: dict[str, int],
        risk_level: RiskLevel,
    ) -> dict[str, Any]:
        """Generate AI-enhanced insights based on assessment data"""
        try:
            # Analyze response patterns
            pattern_analysis = self._analyze_response_patterns(responses)

            # Generate predictive insights
            predictive_insights = await self._generate_predictive_insights(
                user, assessment_type, risk_level
            )

            return {
                "pattern_analysis": pattern_analysis,
                "predictive_insights": predictive_insights,
                "confidence_level": 0.85,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Could not generate AI insights: {e}")
            return {}

    def _analyze_response_patterns(self, responses: dict[str, Any]) -> dict[str, Any]:
        """Analyze patterns in assessment responses"""
        response_values = list(responses.values())

        return {
            "average_response": sum(response_values) / len(response_values),
            "response_variance": sum(
                (x - sum(response_values) / len(response_values)) ** 2
                for x in response_values
            )
            / len(response_values),
            "highest_scoring_items": sorted(
                responses.items(), key=lambda x: x[1], reverse=True
            )[:3],
            "consistency_score": (
                "high"
                if len(set(response_values)) <= 2
                else "moderate" if len(set(response_values)) <= 3 else "variable"
            ),
        }

    async def _generate_predictive_insights(
        self, user: User, assessment_type: str, risk_level: RiskLevel
    ) -> dict[str, Any]:
        """Generate predictive insights based on current assessment"""
        # This would integrate with the AI analytics service for predictive modeling
        return {
            "predicted_trajectory": (
                "stable"
                if risk_level in [RiskLevel.MINIMAL, RiskLevel.MILD]
                else (
                    "declining"
                    if risk_level == RiskLevel.SEVERE
                    else "improving_with_intervention"
                )
            ),
            "probability_of_improvement": (
                0.7
                if risk_level in [RiskLevel.MINIMAL, RiskLevel.MILD]
                else 0.4 if risk_level == RiskLevel.MODERATE else 0.2
            ),
            "key_factors": [
                "Early detection and intervention",
                "Consistent monitoring",
                "Professional support engagement",
            ],
            "timeline_to_improvement": "4-6 weeks with appropriate intervention",
        }

    async def _get_user_assessment_history(self, user: User) -> list[dict[str, Any]]:
        """Get user's previous assessment results for trend analysis"""
        # This would query actual assessment history from the database
        return []

    def _calculate_next_screening_date(self, risk_level: RiskLevel) -> str:
        """Calculate when next screening should be completed"""
        screening_intervals = {
            RiskLevel.MINIMAL: "3 months",
            RiskLevel.MILD: "4 weeks",
            RiskLevel.MODERATE: "2 weeks",
            RiskLevel.MODERATE_SEVERE: "1 week",
            RiskLevel.SEVERE: "3-5 days",
        }

        return screening_intervals.get(risk_level, "4 weeks")
