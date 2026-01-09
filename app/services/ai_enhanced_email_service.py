"""
AI-Enhanced Email Service
Integrates AI engine with email communications for personalization and optimization
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ai.processors.big_five import BigFiveProcessor

# AI Engine imports
from ai.processors.mbti_processor import MBTIProcessor
from app.services.ai_behavioral_integration import AIBehavioralIntegrationService

# Behavioral and email imports
from app.services.behavioral_pattern_recognition import BehavioralPatternRecognizer
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class EmailType(Enum):
    """Types of emails with AI optimization"""
    NOTIFICATION = "notification"
    REMINDER = "reminder"
    ASSESSMENT_INVITATION = "assessment_invitation"
    RESULTS_DELIVERY = "results_delivery"
    TEAM_UPDATE = "team_update"
    DEVELOPMENT_RECOMMENDATION = "development_recommendation"
    CHECK_IN = "check_in"

class PersonalizationLevel(Enum):
    """Levels of AI-driven personalization"""
    BASIC = "basic"           # General personalization (name, basic preferences)
    BEHAVIORAL = "behavioral" # Based on behavioral patterns
    PERSONALITY = "personality" # Based on personality assessment
    PREDICTIVE = "predictive"  # AI-predicted optimal content and timing

@dataclass
class AIEmailContent:
    """AI-optimized email content"""
    subject: str
    body: str
    call_to_action: str
    personalization_level: PersonalizationLevel
    personality_adaptations: dict[str, str]
    optimal_send_time: datetime | None = None
    engagement_prediction: float | None = None
    tone: str = "professional"

@dataclass
class EmailOptimizationInsight:
    """AI-generated insight for email optimization"""
    user_id: str
    email_type: EmailType
    recommended_changes: list[str]
    predicted_engagement_increase: float
    reasoning: str
    confidence: float

class AIEnhancedEmailService:
    """
    AI-powered email service that optimizes communications based on:
    - Personality assessment data
    - Behavioral patterns
    - Engagement history
    - Predictive analytics
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.behavioral_integration = AIBehavioralIntegrationService(db)
        self.pattern_recognizer = BehavioralPatternRecognizer(db)
        self.base_email_service = EmailService()
        self.ai_processors = {
            "mbti": MBTIProcessor(),
            "big_five": BigFiveProcessor()
        }

    async def generate_personalized_email(
        self,
        user_id: str,
        email_type: EmailType,
        base_content: dict[str, Any],
        personalization_level: PersonalizationLevel = PersonalizationLevel.PERSONALITY
    ) -> AIEmailContent:
        """
        Generate AI-personalized email content based on user's personality and behavioral patterns

        Args:
            user_id: Target user ID
            email_type: Type of email to generate
            base_content: Base email content template
            personalization_level: Level of AI personalization to apply

        Returns:
            AI-optimized email content with personalization and timing recommendations
        """

        try:
            logger.info(f"Generating AI-personalized email for user {user_id}, type {email_type.value}")

            # Get user profile for personalization
            user_profile = await self._get_user_email_profile(user_id)

            # Apply AI personalization based on level
            if personalization_level == PersonalizationLevel.BASIC:
                return await self._apply_basic_personalization(base_content, user_profile)

            if personalization_level == PersonalizationLevel.BEHAVIORAL:
                return await self._apply_behavioral_personalization(user_id, email_type, base_content, user_profile)

            if personalization_level == PersonalizationLevel.PERSONALITY:
                return await self._apply_personality_personalization(user_id, email_type, base_content, user_profile)

            if personalization_level == PersonalizationLevel.PREDICTIVE:
                return await self._apply_predictive_personalization(user_id, email_type, base_content, user_profile)

            return await self._apply_basic_personalization(base_content, user_profile)

        except Exception as e:
            logger.error(f"Error generating personalized email: {e}")
            # Fallback to basic personalization
            return await self._apply_basic_personalization(base_content, {})

    async def optimize_email_campaign(
        self,
        campaign_id: str,
        user_ids: list[str],
        email_type: EmailType,
        base_template: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Optimize email campaign with AI-driven personalization and timing

        Returns:
            Campaign optimization results with personalized emails and send schedule
        """

        try:
            logger.info(f"Optimizing email campaign {campaign_id} for {len(user_ids)} users")

            optimization_results = {
                "campaign_id": campaign_id,
                "total_users": len(user_ids),
                "personalized_emails": [],
                "optimal_send_times": {},
                "engagement_predictions": {},
                "overall_campaign_score": 0.0
            }

            # Generate personalized emails for each user
            engagement_predictions = []

            for user_id in user_ids[:100]:  # Limit for performance
                try:
                    personalized_email = await self.generate_personalized_email(
                        user_id=user_id,
                        email_type=email_type,
                        base_content=base_template,
                        personalization_level=PersonalizationLevel.PREDICTIVE
                    )

                    optimization_results["personalized_emails"].append({
                        "user_id": user_id,
                        "content": {
                            "subject": personalized_email.subject,
                            "body": personalized_email.body,
                            "call_to_action": personalized_email.call_to_action
                        },
                        "personalization_level": personalized_email.personalization_level.value,
                        "engagement_prediction": personalized_email.engagement_prediction,
                        "optimal_send_time": personalized_email.optimal_send_time.isoformat() if personalized_email.optimal_send_time else None
                    })

                    if personalized_email.engagement_prediction:
                        engagement_predictions.append(personalized_email.engagement_prediction)

                    # Track optimal send times
                    if personalized_email.optimal_send_time:
                        optimization_results["optimal_send_times"][user_id] = personalized_email.optimal_send_time

                except Exception as e:
                    logger.warning(f"Error optimizing email for user {user_id}: {e}")
                    continue

            # Calculate overall campaign predictions
            if engagement_predictions:
                optimization_results["engagement_predictions"] = {
                    "average_predicted_engagement": sum(engagement_predictions) / len(engagement_predictions),
                    "high_engagement_users": len([p for p in engagement_predictions if p > 0.8]),
                    "total_engagement_predictions": len(engagement_predictions)
                }
                optimization_results["overall_campaign_score"] = sum(engagement_predictions) / len(engagement_predictions)

            return optimization_results

        except Exception as e:
            logger.error(f"Error optimizing email campaign: {e}")
            return {
                "campaign_id": campaign_id,
                "error": str(e),
                "fallback_strategy": "Use basic email template"
            }

    async def analyze_email_performance(
        self,
        email_campaign_id: str | None = None,
        time_period_days: int = 30
    ) -> dict[str, Any]:
        """
        Analyze email performance using AI to generate insights and recommendations

        Returns:
            Performance analysis with AI insights and optimization recommendations
        """

        try:
            logger.info(f"Analyzing email performance with AI for campaign {email_campaign_id}")

            # Get email performance data
            performance_data = await self._get_email_performance_data(email_campaign_id, time_period_days)

            # Generate AI insights
            insights = await self._generate_email_performance_insights(performance_data)

            # Identify optimization opportunities
            opportunities = await self._identify_email_optimization_opportunities(performance_data)

            # Predict future performance
            predictions = await self._predict_email_performance_trends(performance_data)

            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "campaign_id": email_campaign_id,
                "time_period_days": time_period_days,
                "performance_data": performance_data,
                "ai_insights": insights,
                "optimization_opportunities": opportunities,
                "performance_predictions": predictions,
                "recommended_actions": await self._generate_email_optimization_actions(insights, opportunities)
            }

        except Exception as e:
            logger.error(f"Error analyzing email performance: {e}")
            return {
                "error": str(e),
                "fallback_analysis": "Basic email metrics available"
            }

    async def _apply_personality_personalization(
        self,
        user_id: str,
        email_type: EmailType,
        base_content: dict[str, Any],
        user_profile: dict[str, Any]
    ) -> AIEmailContent:
        """Apply personality-based personalization to email content"""

        personality_insights = user_profile.get("personality_insights", {})
        unified_profile = personality_insights.get("unified_profile", {})

        # Extract key personality traits
        extraversion = unified_profile.get("extraversion", 0.5)
        openness = unified_profile.get("openness", 0.5)
        conscientiousness = unified_profile.get("conscientiousness", 0.5)
        agreeableness = unified_profile.get("agreeableness", 0.5)

        # Get MBTI type if available
        mbti_type = None
        assessments = personality_insights.get("available_assessments", [])
        for assessment in assessments:
            if assessment.get("framework") == "mbti":
                mbti_type = assessment.get("processed_result", {}).get("type")
                break

        # Personalize subject line based on personality
        base_subject = base_content.get("subject", "")
        subject = await self._personalize_subject_by_personality(base_subject, extraversion, openness, mbti_type)

        # Personalize body content based on personality
        base_body = base_content.get("body", "")
        body = await self._personalize_body_by_personality(
            base_body, extraversion, openness, conscientiousness, agreeableness, mbti_type
        )

        # Personalize call-to-action based on personality
        base_cta = base_content.get("call_to_action", "Learn More")
        call_to_action = await self._personalize_cta_by_personality(base_cta, extraversion, conscientiousness)

        # Determine optimal send time based on personality
        optimal_send_time = await self._calculate_optimal_send_time_by_personality(user_profile, email_type)

        # Predict engagement based on personality match
        engagement_prediction = await self._predict_engagement_by_personality(
            email_type, extraversion, openness, conscientiousness
        )

        # Set appropriate tone based on personality
        tone = "professional"
        if agreeableness > 0.7:
            tone = "warm_friendly"
        elif extraversion > 0.7:
            tone = "energetic_enthusiastic"
        elif conscientiousness > 0.7:
            tone = "structured_formal"

        return AIEmailContent(
            subject=subject,
            body=body,
            call_to_action=call_to_action,
            personalization_level=PersonalizationLevel.PERSONALITY,
            personality_adaptations={
                "extraversion_level": "high" if extraversion > 0.7 else "medium" if extraversion > 0.4 else "low",
                "openness_level": "high" if openness > 0.7 else "medium" if openness > 0.4 else "low",
                "conscientiousness_level": "high" if conscientiousness > 0.7 else "medium" if conscientiousness > 0.4 else "low",
                "mbti_type": mbti_type or "unknown",
                "tone_adjustment": tone
            },
            optimal_send_time=optimal_send_time,
            engagement_prediction=engagement_prediction,
            tone=tone
        )

    async def _personalize_subject_by_personality(
        self,
        base_subject: str,
        extraversion: float,
        openness: float,
        mbti_type: str | None
    ) -> str:
        """Personalize email subject based on personality traits"""

        subject = base_subject

        # Extraversion-based personalization
        if extraversion > 0.7:
            # More engaging and energetic for extraverts
            if "assessment" in subject.lower():
                subject = subject.replace("Assessment", "Exciting Assessment Opportunity")
            elif "results" in subject.lower():
                subject = subject.replace("Results", "Your Personal Results Are Ready!")
        elif extraversion < 0.3:
            # More direct and less flamboyant for introverts
            subject = re.sub(r"[!]+", ".", subject)  # Reduce exclamation points
            subject = subject.replace("Exciting", "Important").replace("Amazing", "Updated")

        # Openness-based personalization
        if openness > 0.7:
            # More creative and exploratory language
            if "update" in subject.lower():
                subject = subject.replace("Update", "New Insights & Discoveries")
        elif openness < 0.3:
            # More traditional and familiar language
            if "innovative" in subject.lower():
                subject = subject.replace("Innovative", "Improved")

        # MBTI-specific personalization
        if mbti_type:
            if mbti_type.startswith("T"):  # Thinking types
                subject = f"Analysis: {subject}"
            elif mbti_type.startswith("F"):  # Feeling types
                subject = f"Personal {subject}"

        return subject

    async def _personalize_body_by_personality(
        self,
        base_body: str,
        extraversion: float,
        openness: float,
        conscientiousness: float,
        agreeableness: float,
        mbti_type: str | None
    ) -> str:
        """Personalize email body content based on personality traits"""

        body = base_body

        # Extraversion personalization
        if extraversion > 0.7:
            # Add collaborative language and social context
            body += "\n\nJoin others who are already benefiting from these insights!"
        elif extraversion < 0.3:
            # Add self-reflection prompts and individual focus
            body += "\n\nTake your time to reflect on what these insights mean for you."

        # Conscientiousness personalization
        if conscientiousness > 0.7:
            # Add structure, deadlines, and clear next steps
            body += "\n\nRecommended next steps:\n1. Review your results\n2. Set specific goals\n3. Schedule follow-up"
        elif conscientiousness < 0.3:
            # Keep it flexible and pressure-free
            body += "\n\nFeel free to explore these insights at your own pace."

        # Openness personalization
        if openness > 0.7:
            # Add learning and growth opportunities
            body += "\n\nDiscover new perspectives and growth opportunities with these insights."
        elif openness < 0.3:
            # Focus on practical applications
            body += "\n\nApply these insights to improve your daily effectiveness."

        # Agreeableness personalization
        if agreeableness > 0.7:
            # Add collaborative and harmony-focused language
            body += "\n\nShare these insights with your team to enhance collaboration and understanding."

        # MBTI-specific additions
        if mbti_type:
            if mbti_type[2] == "T":  # Thinking preference
                body += "\n\nLogical analysis and objective insights are highlighted in your results."
            elif mbti_type[2] == "F":  # Feeling preference
                body += "\n\nYour values and personal impact are emphasized in these insights."

            if mbti_type[3] == "J":  # Judging preference
                body += "\n\nClear action items and structured recommendations are provided."
            elif mbti_type[3] == "P":  # Perceiving preference
                body += "\n\nExplore various possibilities and options in your personalized report."

        return body

    async def _personalize_cta_by_personality(
        self,
        base_cta: str,
        extraversion: float,
        conscientiousness: float
    ) -> str:
        """Personalize call-to-action based on personality"""

        if extraversion > 0.7 and conscientiousness > 0.7:
            return "Join the Discussion & Plan Your Next Steps"
        if extraversion > 0.7:
            return "Share & Discuss Your Insights"
        if conscientiousness > 0.7:
            return "Access Your Action Plan"
        return "Explore Your Results"

    async def _calculate_optimal_send_time_by_personality(
        self,
        user_profile: dict[str, Any],
        email_type: EmailType
    ) -> datetime | None:
        """Calculate optimal email send time based on personality and behavioral patterns"""

        behavioral_analysis = user_profile.get("behavioral_analysis", {})
        activity_patterns = behavioral_analysis.get("activity_patterns", {})

        # Get peak activity times
        peak_hours = activity_patterns.get("peak_activity_hours", [10, 14, 16])  # Default business hours

        # Get personality traits
        personality_insights = user_profile.get("personality_insights", {})
        unified_profile = personality_insights.get("unified_profile", {})
        conscientiousness = unified_profile.get("conscientiousness", 0.5)

        # Adjust timing based on personality
        if conscientiousness > 0.7:
            # Early morning for highly conscientious people
            optimal_hour = 8
        else:
            # Use peak activity hours
            optimal_hour = peak_hours[0] if peak_hours else 10

        # Calculate next optimal send time
        now = datetime.utcnow()
        next_send = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)

        # If optimal time has passed today, schedule for tomorrow
        if next_send <= now:
            next_send += timedelta(days=1)

        return next_send

    async def _predict_engagement_by_personality(
        self,
        email_type: EmailType,
        extraversion: float,
        openness: float,
        conscientiousness: float
    ) -> float:
        """Predict email engagement based on personality match"""

        base_engagement = 0.5  # Base 50% engagement rate

        # Adjust based on personality-email type match
        if email_type == EmailType.TEAM_UPDATE:
            if extraversion > 0.7:
                base_engagement += 0.2  # Extraverts more likely to engage with team updates
        elif email_type == EmailType.ASSESSMENT_INVITATION:
            if openness > 0.7:
                base_engagement += 0.15  # Open people more likely to try assessments
        elif email_type == EmailType.DEVELOPMENT_RECOMMENDATION:
            if conscientiousness > 0.7:
                base_engagement += 0.25  # Conscientious people more likely to act on recommendations

        # Cap at reasonable maximum
        return min(base_engagement, 0.95)

    # Helper methods
    async def _get_user_email_profile(self, user_id: str) -> dict[str, Any]:
        """Get user profile for email personalization"""
        try:
            return await self.behavioral_integration.get_comprehensive_user_profile(
                user_id, time_window_hours=720  # 30 days
            )
        except Exception as e:
            logger.warning(f"Error getting user profile for {user_id}: {e}")
            return {}

    async def _apply_basic_personalization(self, base_content: dict[str, Any], user_profile: dict[str, Any]) -> AIEmailContent:
        """Apply basic personalization (name, etc.)"""
        return AIEmailContent(
            subject=base_content.get("subject", ""),
            body=base_content.get("body", ""),
            call_to_action=base_content.get("call_to_action", ""),
            personalization_level=PersonalizationLevel.BASIC,
            personality_adaptations={}
        )

    async def _apply_behavioral_personalization(self, user_id: str, email_type: EmailType, base_content: dict[str, Any], user_profile: dict[str, Any]) -> AIEmailContent:
        """Apply behavioral pattern-based personalization"""
        # Implementation would use behavioral patterns from user_profile
        return await self._apply_basic_personalization(base_content, user_profile)

    async def _apply_predictive_personalization(self, user_id: str, email_type: EmailType, base_content: dict[str, Any], user_profile: dict[str, Any]) -> AIEmailContent:
        """Apply AI-predictive personalization"""
        # Start with personality personalization as foundation
        return await self._apply_personality_personalization(user_id, email_type, base_content, user_profile)

    async def _get_email_performance_data(self, campaign_id: str | None, time_period_days: int) -> dict[str, Any]:
        """Get email performance data for analysis"""
        # This would query actual email performance metrics
        return {"placeholder": "email performance data"}

    async def _generate_email_performance_insights(self, performance_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate AI insights from email performance data"""
        return [{"insight": "AI analysis of email performance", "confidence": 0.8}]

    async def _identify_email_optimization_opportunities(self, performance_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify opportunities for email optimization"""
        return [{"opportunity": "Personalize subject lines", "potential_impact": "high"}]

    async def _predict_email_performance_trends(self, performance_data: dict[str, Any]) -> dict[str, Any]:
        """Predict future email performance trends"""
        return {"predicted_engagement": 0.75, "trend": "improving"}

    async def _generate_email_optimization_actions(self, insights: list[dict[str, Any]], opportunities: list[dict[str, Any]]) -> list[str]:
        """Generate recommended actions for email optimization"""
        return ["Increase personalization", "Optimize send times", "A/B test subject lines"]
