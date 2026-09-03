"""
Clinical Assessment Service
Provides clinical assessment and consent management functionality
"""

from datetime import datetime, timedelta
from typing import Any

from app.core.logging_config import logger


class ClinicalAssessmentService:
    """Service for managing clinical assessments and consent"""

    def __init__(self):
        self.logger = logger

    async def verify_screening_consent(self, user_id: int, screening_type: str) -> bool:
        """
        Verify if user has given consent for screening
        For now, returns True - in production would check database
        """
        try:
            # TODO: Implement actual consent verification from database
            # For now, we'll assume consent is given when called
            self.logger.info(
                f"Consent verification for user {user_id} - {screening_type}: granted"
            )
            return True
        except Exception as e:
            self.logger.error(f"Consent verification failed: {e!s}")
            return False

    async def assess_crisis_severity(
        self,
        user_id: int,
        alert_type: str,
        severity_indicators: dict[str, Any],
        immediate_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Assess crisis severity for immediate intervention
        """
        try:
            # Simple risk assessment logic
            high_risk_indicators = [
                "suicidal_ideation",
                "self_harm_intent",
                "harm_to_others",
                "psychosis",
            ]

            risk_score = 0
            for indicator in high_risk_indicators:
                if severity_indicators.get(indicator, False):
                    risk_score += 3

            if risk_score >= 3:
                risk_level = "critical"
            elif risk_score >= 1:
                risk_level = "high"
            elif severity_indicators.get("severe_distress", False):
                risk_level = "moderate"
            else:
                risk_level = "low"

            return {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "alert_type": alert_type,
                "assessment_time": datetime.utcnow(),
                "recommendations": self._get_crisis_recommendations(risk_level),
            }
        except Exception as e:
            self.logger.error(f"Crisis severity assessment failed: {e!s}")
            return {"risk_level": "unknown", "risk_score": 0}

    def _get_crisis_recommendations(self, risk_level: str) -> list[str]:
        """Get crisis recommendations based on risk level"""
        recommendations = {
            "critical": [
                "Call 911 or emergency services immediately",
                "Go to nearest emergency room",
                "Contact crisis hotline: 988",
                "Stay with the person until help arrives",
            ],
            "high": [
                "Contact crisis hotline: 988",
                "Seek immediate professional help",
                "Contact emergency services if symptoms worsen",
                "Remove access to means of harm",
            ],
            "moderate": [
                "Contact mental health professional within 24 hours",
                "Call crisis hotline for support: 988",
                "Reach out to trusted support person",
                "Use grounding techniques",
            ],
            "low": [
                "Schedule appointment with mental health provider",
                "Contact support system",
                "Practice self-care strategies",
                "Monitor symptoms",
            ],
        }
        return recommendations.get(risk_level, recommendations["low"])

    async def generate_immediate_crisis_response(
        self, crisis_assessment: dict[str, Any], alert_type: str
    ) -> list[str]:
        """Generate immediate crisis response actions"""
        risk_level = crisis_assessment.get("risk_level", "low")

        immediate_actions = []
        if risk_level == "critical":
            immediate_actions.extend(
                [
                    "CALL_EMERGENCY_SERVICES",
                    "STAY_WITH_PERSON",
                    "REMOVE_MEANS_OF_HARM",
                    "CONTACT_EMERGENCY_CONTACTS",
                ]
            )
        elif risk_level == "high":
            immediate_actions.extend(
                [
                    "CALL_CRISIS_HOTLINE",
                    "CONTACT_EMERGENCY_CONTACTS",
                    "SEEK_IMMEDIATE_PROFESSIONAL_HELP",
                ]
            )
        elif risk_level == "moderate":
            immediate_actions.extend(
                [
                    "CONTACT_MENTAL_HEALTH_PROFESSIONAL",
                    "USE_SUPPORT_NETWORK",
                    "PRACTICE_GROUNDING_TECHNIQUES",
                ]
            )

        return immediate_actions

    async def get_emergency_resources(
        self, risk_level: str, user_location: str | None, alert_type: str
    ) -> dict[str, Any]:
        """Get emergency resources based on risk and location"""
        resources = {
            "emergency_services": {
                "name": "Emergency Services",
                "phone": "911",
                "available": "24/7",
            },
            "crisis_hotline": {
                "name": "Suicide & Crisis Lifeline",
                "phone": "988",
                "available": "24/7",
                "website": "https://988lifeline.org",
            },
            "crisis_text_line": {
                "name": "Crisis Text Line",
                "text": "HOME to 741741",
                "available": "24/7",
            },
        }

        # Add local resources if location provided
        if user_location:
            resources["local_emergency"] = {
                "name": "Local Emergency Services",
                "phone": "911",
                "location": user_location,
            }

        return resources

    async def create_immediate_safety_plan(
        self, user_id: int, crisis_assessment: dict[str, Any]
    ) -> dict[str, Any]:
        """Create immediate safety plan"""
        risk_level = crisis_assessment.get("risk_level", "low")

        safety_plan = {
            "user_id": user_id,
            "risk_level": risk_level,
            "created_at": datetime.utcnow(),
            "steps": [],
        }

        if risk_level in ["critical", "high"]:
            safety_plan["steps"].extend(
                [
                    "Remove access to means of harm",
                    "Stay in a safe location",
                    "Contact trusted person immediately",
                    "Follow immediate actions provided",
                ]
            )

        safety_plan["steps"].extend(
            [
                "Keep crisis numbers available",
                "Use coping strategies",
                "Seek professional help",
            ]
        )

        return safety_plan

    async def assess_need_for_professional_intervention(
        self, crisis_assessment: dict[str, Any], alert_type: str
    ) -> dict[str, Any]:
        """Assess if professional intervention is needed"""
        risk_level = crisis_assessment.get("risk_level", "low")

        intervention_needed = risk_level in ["moderate", "high", "critical"]
        urgency = {
            "critical": "immediate",
            "high": "within_hours",
            "moderate": "within_24_hours",
            "low": "within_week",
        }

        return {
            "recommended": intervention_needed,
            "urgency": urgency.get(risk_level, "within_week"),
            "type": (
                "emergency"
                if risk_level == "critical"
                else "urgent_care" if risk_level == "high" else "outpatient"
            ),
        }

    async def log_crisis_alert(
        self,
        user_id: int,
        alert_type: str,
        severity_level: str,
        actions_taken: list[str],
    ):
        """Log crisis alert for follow-up (while maintaining privacy)"""
        try:
            # In production, this would store in secure database
            log_entry = {
                "user_id": user_id,
                "alert_type": alert_type,
                "severity_level": severity_level,
                "actions_taken": actions_taken,
                "timestamp": datetime.utcnow(),
                "logged_by": "clinical_system",
            }

            self.logger.info(
                f"Crisis alert logged: {alert_type} - {severity_level} - {len(actions_taken)} actions taken"
            )

        except Exception as e:
            self.logger.error(f"Failed to log crisis alert: {e!s}")

    async def schedule_crisis_follow_up(
        self, user_id: int, crisis_assessment: dict[str, Any]
    ) -> dict[str, Any]:
        """Schedule crisis follow-up"""
        risk_level = crisis_assessment.get("risk_level", "low")

        follow_up_intervals = {
            "critical": {"hours": 1, "then_hours": 24},
            "high": {"hours": 2, "then_hours": 48},
            "moderate": {"hours": 24, "then_hours": 72},
            "low": {"days": 7, "then_days": 30},
        }

        interval = follow_up_intervals.get(risk_level, follow_up_intervals["low"])

        return {
            "initial_follow_up": datetime.utcnow()
            + timedelta(hours=interval.get("hours", interval.get("days", 7) * 24)),
            "subsequent_follow_up": datetime.utcnow()
            + timedelta(
                hours=interval.get("then_hours", interval.get("then_days", 30) * 24)
            ),
            "method": (
                "phone_call" if risk_level in ["critical", "high"] else "secure_message"
            ),
            "automated": risk_level in ["moderate", "low"],
        }

    async def get_crisis_hotlines(self) -> list[dict[str, str]]:
        """Get crisis hotline information"""
        return [
            {
                "name": "Suicide & Crisis Lifeline",
                "number": "988",
                "description": "24/7 free, confidential support for people in distress",
                "website": "https://988lifeline.org",
            },
            {
                "name": "Crisis Text Line",
                "text": "HOME to 741741",
                "description": "24/7 support via text message",
                "website": "https://www.crisistextline.org",
            },
            {
                "name": "National Domestic Violence Hotline",
                "number": "1-800-799-7233",
                "description": "24/7 support for domestic violence",
                "website": "https://www.thehotline.org",
            },
            {
                "name": "SAMHSA National Helpline",
                "number": "1-800-662-4357",
                "description": "Treatment referral and information service",
                "website": "https://www.samhsa.gov",
            },
        ]

    async def get_clinical_resources(
        self,
        resource_type: str | None,
        condition: str | None,
        user_location: str | None,
    ) -> dict[str, Any]:
        """Get clinical resources"""
        # Basic resource categories
        resources = {
            "emergency_support": [
                {
                    "name": "Emergency Services",
                    "phone": "911",
                    "description": "For life-threatening emergencies",
                    "available_24_7": True,
                },
                {
                    "name": "Local Emergency Room",
                    "description": "Nearest hospital emergency department",
                    "available_24_7": True,
                    "location_based": True,
                },
            ],
            "professional_help": [
                {
                    "name": "Psychology Today Therapist Finder",
                    "website": "https://www.psychologytoday.com/us/therapists",
                    "description": "Find licensed therapists in your area",
                },
                {
                    "name": "NAMI Helpline",
                    "phone": "1-800-950-NAMI",
                    "description": "National Alliance on Mental Illness support",
                },
            ],
            "support_groups": [
                {
                    "name": "AA (Alcoholics Anonymous)",
                    "description": "Peer support for alcohol use recovery",
                    "website": "https://www.aa.org",
                },
                {
                    "name": "SMART Recovery",
                    "description": "Science-based addiction recovery",
                    "website": "https://www.smartrecovery.org",
                },
            ],
            "self_help_resources": [
                {
                    "name": "Mental Health America Screening Tools",
                    "website": "https://screening.mhanational.org",
                    "description": "Free mental health screenings",
                }
            ],
        }

        return resources

    async def prioritize_resources(
        self, resources: dict[str, list[dict[str, Any]]], user_location: str | None
    ) -> dict[str, Any]:
        """Prioritize resources based on availability and user preferences"""
        # For now, return resources as-is
        # In production, this would prioritize based on location, availability, user preferences
        return resources

    async def get_crisis_resources(self) -> list[dict[str, Any]]:
        """Get crisis resources (always included in responses)"""
        return [
            {
                "name": "Emergency Services",
                "phone": "911",
                "priority": 1,
                "available_24_7": True,
            },
            {
                "name": "Suicide & Crisis Lifeline",
                "phone": "988",
                "priority": 2,
                "available_24_7": True,
                "website": "https://988lifeline.org",
            },
            {
                "name": "Crisis Text Line",
                "text": "HOME to 741741",
                "priority": 3,
                "available_24_7": True,
                "website": "https://www.crisistextline.org",
            },
        ]
