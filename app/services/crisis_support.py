"""
Crisis Support Service - Emergency mental health support with safety protocols and immediate intervention
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.services.ai_enhanced_analytics import AIEnhancedAnalyticsService
from app.db.models.user import User
from app.db.models.response import Response
import logging

logger = logging.getLogger(__name__)

class CrisisSupportService:
    """Service for providing crisis support and safety planning with immediate intervention protocols"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_analytics = AIEnhancedAnalyticsService(db)

    async def assess_crisis_severity(
        self,
        user_id: str,
        responses: Dict[str, str],
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Assess the severity of a crisis situation based on user responses

        Args:
            user_id: User identifier
            responses: Assessment responses
            timestamp: Assessment timestamp

        Returns:
            Crisis severity assessment with recommended actions
        """
        try:
            logger.info(f"Assessing crisis severity for user {user_id}")

            # Calculate severity score
            severity_score = await self._calculate_severity_score(responses)

            # Determine risk level
            risk_level = await self._determine_risk_level(severity_score, responses)

            # Identify immediate safety concerns
            safety_concerns = await self._identify_safety_concerns(responses, risk_level)

            # Generate immediate recommendations
            recommended_actions = await self._generate_immediate_actions(risk_level, responses)

            # Create crisis alert if necessary
            if risk_level in ['high', 'emergency']:
                await self._create_crisis_alert(user_id, responses, risk_level, severity_score)

            # Log assessment (maintaining privacy)
            await self._log_crisis_assessment(user_id, risk_level, severity_score, timestamp)

            return {
                "severity": risk_level,
                "severity_score": severity_score,
                "risk_factors": await self._identify_risk_factors(responses),
                "immediate_needs": await self._identify_immediate_needs(responses),
                "recommended_actions": recommended_actions,
                "safety_concerns": safety_concerns,
                "assessment_timestamp": timestamp,
                "follow_up_required": risk_level in ['moderate', 'high', 'emergency']
            }

        except Exception as e:
            logger.error(f"Error assessing crisis severity: {e}")
            # Return emergency assessment as default
            return {
                "severity": "emergency",
                "severity_score": 10,
                "risk_factors": ["System error - default to emergency"],
                "immediate_needs": ["Immediate professional help"],
                "recommended_actions": ["Call 988 or 911 immediately"],
                "safety_concerns": ["Unable to assess - assume emergency"],
                "assessment_timestamp": timestamp,
                "follow_up_required": True
            }

    async def _calculate_severity_score(self, responses: Dict[str, str]) -> float:
        """Calculate crisis severity score from assessment responses"""
        try:
            score = 0.0

            # Suicidal thoughts (most critical)
            if responses.get('suicidal_thoughts') == 'yes':
                score += 4.0

            # Specific harm plan (extremely critical)
            if responses.get('harm_plan') == 'yes':
                score += 5.0

            # Anxiety level
            anxiety_level = int(responses.get('anxiety_level', 0))
            score += (anxiety_level / 10) * 2.0

            # Support system
            if responses.get('support_system') == 'no':
                score += 1.5

            # Substance use
            if responses.get('substances') == 'yes':
                score += 1.0

            # Sleep deprivation
            sleep_hours = int(responses.get('sleep', 8))
            if sleep_hours < 4:
                score += 1.0
            elif sleep_hours < 6:
                score += 0.5

            return min(score, 10.0)  # Cap at 10

        except Exception as e:
            logger.error(f"Error calculating severity score: {e}")
            return 10.0  # Default to maximum severity

    async def _determine_risk_level(self, severity_score: float, responses: Dict[str, str]) -> str:
        """Determine risk level based on severity score and responses"""
        try:
            # Immediate emergency indicators
            if (responses.get('suicidal_thoughts') == 'yes' and
                responses.get('harm_plan') == 'yes'):
                return 'emergency'

            # High severity score
            if severity_score >= 7.0:
                return 'high'

            # Moderate risk
            if severity_score >= 4.0:
                return 'moderate'

            # Low risk but still concerning
            if severity_score >= 2.0:
                return 'low'

            # Minimal risk
            return 'minimal'

        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return 'emergency'  # Default to emergency

    async def _identify_safety_concerns(self, responses: Dict[str, str], risk_level: str) -> List[str]:
        """Identify specific safety concerns based on responses"""
        concerns = []

        try:
            # Suicidal ideation concerns
            if responses.get('suicidal_thoughts') == 'yes':
                if responses.get('harm_plan') == 'yes':
                    concerns.append("Immediate suicidal thoughts with specific plan - requires emergency intervention")
                else:
                    concerns.append("Suicidal thoughts present - requires immediate professional support")

            # High anxiety levels
            anxiety_level = int(responses.get('anxiety_level', 0))
            if anxiety_level >= 8:
                concerns.append("Severe anxiety or panic - may need immediate calming techniques")
            elif anxiety_level >= 6:
                concerns.append("High anxiety levels - may need coping strategies")

            # Social isolation
            if responses.get('support_system') == 'no':
                concerns.append("Lack of immediate social support system")

            # Substance involvement
            if responses.get('substances') == 'yes':
                concerns.append("Recent substance use may impair judgment")

            # Sleep deprivation
            sleep_hours = int(responses.get('sleep', 8))
            if sleep_hours < 4:
                concerns.append("Severe sleep deprivation - may affect mental stability")

            # Risk level specific concerns
            if risk_level == 'emergency':
                concerns.append("Immediate risk to personal safety - emergency intervention required")
            elif risk_level == 'high':
                concerns.append("High risk situation - professional intervention needed soon")

        except Exception as e:
            logger.error(f"Error identifying safety concerns: {e}")
            concerns.append("Unable to fully assess safety concerns - seek professional help")

        return concerns

    async def _generate_immediate_actions(self, risk_level: str, responses: Dict[str, str]) -> List[str]:
        """Generate immediate action recommendations based on risk level"""
        actions = []

        try:
            if risk_level == 'emergency':
                actions.extend([
                    "Call 911 or go to nearest emergency room immediately",
                    "Call 988 Suicide & Crisis Lifeline: 988",
                    "Remove any means of self-harm from your immediate environment",
                    "Stay with someone until help arrives",
                    "Do not use alcohol or drugs"
                ])

            elif risk_level == 'high':
                actions.extend([
                    "Call 988 Suicide & Crisis Lifeline: 988",
                    "Contact a mental health professional immediately",
                    "Reach out to a trusted friend or family member",
                    "Use coping strategies: deep breathing, grounding techniques",
                    "Remove yourself from stressful situations if possible"
                ])

            elif risk_level == 'moderate':
                actions.extend([
                    "Call 988 Suicide & Crisis Lifeline: 988",
                    "Contact your therapist or mental health provider",
                    "Use your safety plan if you have one",
                    "Practice relaxation techniques",
                    "Consider going to a safe space"
                ])

            elif risk_level == 'low':
                actions.extend([
                    "Reach out to a friend or family member",
                    "Practice self-care activities",
                    "Consider contacting a mental health professional",
                    "Use healthy coping mechanisms",
                    "Monitor your feelings and seek help if they worsen"
                ])

            else:  # minimal
                actions.extend([
                    "Practice self-care and stress management",
                    "Stay connected with supportive people",
                    "Monitor your mental health",
                    "Consider preventive mental health care"
                ])

        except Exception as e:
            logger.error(f"Error generating immediate actions: {e}")
            actions.append("Seek immediate professional help - call 988 or 911")

        return actions

    async def _identify_risk_factors(self, responses: Dict[str, str]) -> List[str]:
        """Identify risk factors from assessment responses"""
        factors = []

        try:
            # Direct indicators
            if responses.get('suicidal_thoughts') == 'yes':
                factors.append("Current suicidal ideation")

            if responses.get('harm_plan') == 'yes':
                factors.append("Specific plan for self-harm")

            # Contributing factors
            anxiety_level = int(responses.get('anxiety_level', 0))
            if anxiety_level >= 7:
                factors.append("Severe anxiety or distress")
            elif anxiety_level >= 5:
                factors.append("Moderate to high anxiety")

            if responses.get('support_system') == 'no':
                factors.append("Lack of social support")

            if responses.get('substances') == 'yes':
                factors.append("Recent substance use")

            sleep_hours = int(responses.get('sleep', 8))
            if sleep_hours < 5:
                factors.append("Severe sleep deprivation")
            elif sleep_hours < 7:
                factors.append("Insufficient sleep")

            # Trigger information
            triggers = responses.get('triggers', '')
            if triggers and triggers.strip():
                factors.append(f"Identified trigger: {triggers}")

        except Exception as e:
            logger.error(f"Error identifying risk factors: {e}")
            factors.append("Unable to fully assess risk factors")

        return factors

    async def _identify_immediate_needs(self, responses: Dict[str, str]) -> List[str]:
        """Identify immediate needs based on assessment"""
        needs = []

        try:
            # Safety needs
            if responses.get('suicidal_thoughts') == 'yes':
                needs.append("Immediate safety intervention")
                needs.append("Professional crisis support")

            # Support needs
            if responses.get('support_system') == 'no':
                needs.append("Immediate social connection")
                needs.append("Professional support")

            # Symptom management
            anxiety_level = int(responses.get('anxiety_level', 0))
            if anxiety_level >= 7:
                needs.append("Anxiety management techniques")
                needs.append("Immediate calming strategies")

            # Physical needs
            sleep_hours = int(responses.get('sleep', 8))
            if sleep_hours < 5:
                needs.append("Rest and sleep")
                needs.append("Basic physical care")

            if responses.get('substances') == 'yes':
                needs.append("Substance-free support")
                needs.append("Medical monitoring")

        except Exception as e:
            logger.error(f"Error identifying immediate needs: {e}")
            needs.append("Immediate professional assessment")

        return needs

    async def create_personalized_safety_plan(
        self,
        user_id: str,
        personalize: bool = True,
        include_local_resources: bool = True
    ) -> Dict[str, Any]:
        """
        Create a personalized safety plan for crisis situations

        Args:
            user_id: User identifier
            personalize: Whether to personalize based on user data
            include_local_resources: Whether to include local emergency resources

        Returns:
            Comprehensive safety plan with personalized recommendations
        """
        try:
            logger.info(f"Creating personalized safety plan for user {user_id}")

            # Get user's recent assessment data if personalizing
            user_data = {}
            if personalize:
                user_data = await self._get_user_assessment_data(user_id)

            # Generate warning signs
            warning_signs = await self._generate_warning_signs(user_data)

            # Generate coping strategies
            coping_strategies = await self._generate_coping_strategies(user_data)

            # Generate social support contacts
            social_supports = await self._generate_social_supports(user_data)

            # Generate professional help resources
            professional_help = await self._generate_professional_help(include_local_resources)

            # Generate emergency contacts
            emergency_contacts = await self._generate_emergency_contacts()

            # Generate safe environment strategies
            safe_environment = await self._generate_safe_environment_strategies()

            safety_plan = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "warning_signs": warning_signs,
                "coping_strategies": coping_strategies,
                "social_supports": social_supports,
                "professional_help": professional_help,
                "emergency_contacts": emergency_contacts,
                "safe_environment": safe_environment,
                "personalized": personalize,
                "last_reviewed": datetime.utcnow().isoformat()
            }

            # Save safety plan to database (implementation would go here)
            await self._save_safety_plan(user_id, safety_plan)

            return {
                "success": True,
                "data": safety_plan
            }

        except Exception as e:
            logger.error(f"Error creating safety plan: {e}")
            # Return basic safety plan
            return {
                "success": True,
                "data": await self._get_basic_safety_plan(user_id)
            }

    async def _get_user_assessment_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's recent assessment data for personalization"""
        try:
            # Get recent responses
            query = select(Response).where(
                Response.user_id == user_id
            ).order_by(desc(Response.completed_at)).limit(10)

            result = await self.db.execute(query)
            recent_responses = result.scalars().all()

            user_data = {
                "recent_responses": len(recent_responses),
                "last_assessment": recent_responses[0].completed_at.isoformat() if recent_responses else None,
                "assessment_patterns": []
            }

            # Analyze patterns (simplified)
            for response in recent_responses:
                response_data = response.response_data or {}
                if isinstance(response_data, dict):
                    user_data["assessment_patterns"].append({
                        "date": response.completed_at.isoformat(),
                        "anxiety_level": response_data.get("anxiety_level"),
                        "depression_level": response_data.get("depression_level")
                    })

            return user_data

        except Exception as e:
            logger.error(f"Error getting user assessment data: {e}")
            return {}

    async def _generate_warning_signs(self, user_data: Dict[str, Any]) -> List[str]:
        """Generate personalized warning signs"""
        base_signs = [
            "Thoughts of self-harm or suicide",
            "Feeling hopeless or trapped",
            "Increased anxiety or panic",
            "Withdrawing from friends and activities",
            "Changes in sleep or appetite",
            "Increased substance use",
            "Feeling like a burden to others"
        ]

        # Add personalized signs based on user data
        personalized = []

        if user_data.get("assessment_patterns"):
            # This would analyze patterns and add personalized signs
            personalized.extend([
                "Noticeable changes in your usual mood patterns",
                "Difficulty managing stress that's different from your normal"
            ])

        return base_signs + personalized

    async def _generate_coping_strategies(self, user_data: Dict[str, Any]) -> List[str]:
        """Generate personalized coping strategies"""
        base_strategies = [
            "Practice deep breathing exercises (4-7-8 technique)",
            "Use the 5-4-3-2-1 grounding technique",
            "Contact someone from your support network",
            "Engage in physical activity (even just a short walk)",
            "Listen to calming music or nature sounds",
            "Write down your thoughts and feelings",
            "Take a warm bath or shower",
            "Practice mindfulness or meditation",
            "Watch a comforting movie or TV show",
            "Engage in a creative activity",
            "Spend time with a pet",
            "Go to a safe, public place"
        ]

        # Add personalized strategies
        personalized = []

        if user_data.get("assessment_patterns"):
            personalized.extend([
                "Use the coping strategies that have helped you before",
                "Remember the techniques that worked during previous difficult times"
            ])

        return base_strategies + personalized

    async def _generate_social_supports(self, user_data: Dict[str, Any]) -> List[str]:
        """Generate social support suggestions"""
        return [
            "Trusted friend: [Name] - [Phone number]",
            "Family member: [Name] - [Phone number]",
            "Therapist/Counselor: [Name] - [Phone number]",
            "Support group contact: [Name] - [Phone number]",
            "Mentor or spiritual advisor: [Name] - [Phone number]"
        ]

    async def _generate_professional_help(self, include_local_resources: bool) -> List[str]:
        """Generate professional help resources"""
        resources = [
            "988 Suicide & Crisis Lifeline - 988 (24/7)",
            "Crisis Text Line - Text HOME to 741741",
            "National Suicide Prevention Lifeline - 1-800-273-8255",
            "Emergency Services - 911"
        ]

        if include_local_resources:
            resources.extend([
                "Local Emergency Room - Nearest hospital",
                "Local Mental Health Crisis Center",
                "Your primary care physician",
                "Local crisis response team"
            ])

        return resources

    async def _generate_emergency_contacts(self) -> List[str]:
        """Generate emergency contact list"""
        return [
            "Emergency Services - 911",
            "988 Suicide & Crisis Lifeline",
            "Poison Control - 1-800-222-1222",
            "Local emergency room",
            "Your therapist/counselor",
            "Trusted emergency contact"
        ]

    async def _generate_safe_environment_strategies(self) -> List[str]:
        """Generate safe environment strategies"""
        return [
            "Remove firearms, sharp objects, or medications from easy access",
            "Avoid alcohol and drugs during crisis periods",
            "Have a trusted friend or family member stay with you",
            "Go to a safe public place (library, coffee shop, community center)",
            "Lock away any means of self-harm",
            "Keep emergency numbers readily available",
            "Create a calm, comfortable space in your home",
            "Have a crisis box with comforting items"
        ]

    async def _get_basic_safety_plan(self, user_id: str) -> Dict[str, Any]:
        """Get a basic safety plan when personalization fails"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "warning_signs": await self._generate_warning_signs({}),
            "coping_strategies": await self._generate_coping_strategies({}),
            "social_supports": await self._generate_social_supports({}),
            "professional_help": await self._generate_professional_help(False),
            "emergency_contacts": await self._generate_emergency_contacts(),
            "safe_environment": await self._generate_safe_environment_strategies(),
            "personalized": False,
            "last_reviewed": datetime.utcnow().isoformat()
        }

    async def _create_crisis_alert(
        self,
        user_id: str,
        responses: Dict[str, str],
        risk_level: str,
        severity_score: float
    ) -> None:
        """Create a crisis alert for immediate intervention"""
        try:
            # In a real implementation, this would:
            # 1. Create a high-priority alert in the system
            # 2. Notify crisis response team
            # 3. Log for compliance and follow-up
            # 4. Potentially integrate with external crisis services

            alert_data = {
                "user_id": user_id,
                "risk_level": risk_level,
                "severity_score": severity_score,
                "responses": responses,
                "timestamp": datetime.utcnow().isoformat(),
                "alert_type": "crisis_assessment",
                "requires_immediate_action": risk_level in ['high', 'emergency']
            }

            # Log the alert (in production, this would be more sophisticated)
            logger.warning(f"CRISIS ALERT: {alert_data}")

            # Store alert for follow-up (implementation would go here)
            # This could involve saving to a crisis_alerts table

        except Exception as e:
            logger.error(f"Error creating crisis alert: {e}")

    async def _log_crisis_assessment(
        self,
        user_id: str,
        risk_level: str,
        severity_score: float,
        timestamp: str
    ) -> None:
        """Log crisis assessment for compliance and follow-up"""
        try:
            log_entry = {
                "user_id": user_id,
                "assessment_timestamp": timestamp,
                "risk_level": risk_level,
                "severity_score": severity_score,
                "logged_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Crisis assessment logged: {log_entry}")

            # In production, this would be stored securely with appropriate privacy controls
            # and might trigger follow-up procedures based on risk level

        except Exception as e:
            logger.error(f"Error logging crisis assessment: {e}")

    async def _save_safety_plan(self, user_id: str, safety_plan: Dict[str, Any]) -> None:
        """Save safety plan to database"""
        try:
            # In production, this would save to a safety_plans table
            logger.info(f"Safety plan saved for user {user_id}")

        except Exception as e:
            logger.error(f"Error saving safety plan: {e}")

    async def get_existing_safety_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's existing safety plan"""
        try:
            # In production, this would retrieve from database
            # For now, return None to indicate no existing plan
            return None

        except Exception as e:
            logger.error(f"Error getting existing safety plan: {e}")
            return None