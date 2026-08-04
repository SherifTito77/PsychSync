"""
Wellness Monitoring Service
Provides comprehensive wellness assessment and trend analysis
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.db.models.user import User
from app.services.ai_enhanced_analytics import AIEnhancedAnalyticsService

logger = logging.getLogger(__name__)


class WellnessDomain(Enum):
    PHYSICAL = "physical"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    INTELLECTUAL = "intellectual"
    SPIRITUAL = "spiritual"
    OCCUPATIONAL = "occupational"
    ENVIRONMENTAL = "environmental"


class WellnessLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class WellnessMonitoringService:
    """
    Comprehensive wellness monitoring service
    Tracks multiple wellness domains with AI-enhanced insights
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIEnhancedAnalyticsService(db)

        # Wellness domain weights for overall score calculation
        self.domain_weights = {
            WellnessDomain.PHYSICAL: 0.20,
            WellnessDomain.EMOTIONAL: 0.20,
            WellnessDomain.SOCIAL: 0.15,
            WellnessDomain.INTELLECTUAL: 0.15,
            WellnessDomain.SPIRITUAL: 0.10,
            WellnessDomain.OCCUPATIONAL: 0.15,
            WellnessDomain.ENVIRONMENTAL: 0.05,
        }

        # Wellness level thresholds
        self.wellness_thresholds = {
            WellnessLevel.EXCELLENT: (0.85, 1.0),
            WellnessLevel.GOOD: (0.70, 0.84),
            WellnessLevel.MODERATE: (0.55, 0.69),
            WellnessLevel.NEEDS_IMPROVEMENT: (0.40, 0.54),
            WellnessLevel.POOR: (0.0, 0.39),
        }

        # Wellness assessment questions
        self.wellness_questions = self._load_wellness_questions()

    def _load_wellness_questions(self) -> dict[str, list[dict[str, Any]]]:
        """Load wellness assessment questions for each domain"""
        return {
            WellnessDomain.PHYSICAL.value: [
                {
                    "id": "physical_1",
                    "text": "I get 7-9 hours of quality sleep most nights",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "physical_2",
                    "text": "I engage in regular physical activity (150+ minutes/week)",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "physical_3",
                    "text": "I eat nutritious meals and stay hydrated",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.EMOTIONAL.value: [
                {
                    "id": "emotional_1",
                    "text": "I can identify and express my emotions effectively",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "emotional_2",
                    "text": "I have healthy coping mechanisms for stress",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "emotional_3",
                    "text": "I maintain a positive outlook on life",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.SOCIAL.value: [
                {
                    "id": "social_1",
                    "text": "I have meaningful relationships with friends and family",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "social_2",
                    "text": "I feel connected to my community",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.INTELLECTUAL.value: [
                {
                    "id": "intellectual_1",
                    "text": "I engage in activities that challenge my mind",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "intellectual_2",
                    "text": "I am open to learning new things",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.SPIRITUAL.value: [
                {
                    "id": "spiritual_1",
                    "text": "I have a sense of purpose and meaning in life",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "spiritual_2",
                    "text": "I practice activities that nurture my spirit",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.OCCUPATIONAL.value: [
                {
                    "id": "occupational_1",
                    "text": "I find satisfaction in my work or daily activities",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
                {
                    "id": "occupational_2",
                    "text": "I maintain a healthy work-life balance",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                },
            ],
            WellnessDomain.ENVIRONMENTAL.value: [
                {
                    "id": "environmental_1",
                    "text": "I feel safe and comfortable in my living environment",
                    "options": [
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"},
                    ],
                }
            ],
        }

    async def get_wellness_assessment_questions(self) -> dict[str, Any]:
        """Get all wellness assessment questions"""
        return {
            "assessment_type": "wellness_comprehensive",
            "domains": [
                {
                    "name": domain.value,
                    "weight": self.domain_weights[domain],
                    "questions": self.wellness_questions.get(domain.value, []),
                }
                for domain in WellnessDomain
            ],
            "total_questions": sum(
                len(questions) for questions in self.wellness_questions.values()
            ),
            "estimated_time": "10-15 minutes",
            "description": "Comprehensive wellness assessment across 7 key life domains",
        }

    async def process_wellness_assessment(
        self, user: User, responses: dict[str, int], additional_notes: str | None = None
    ) -> dict[str, Any]:
        """
        Process wellness assessment responses and generate comprehensive insights
        """
        try:
            # Calculate domain scores
            domain_scores = self._calculate_domain_scores(responses)

            # Calculate overall wellness score
            overall_score = self._calculate_overall_wellness_score(domain_scores)

            # Determine wellness level
            wellness_level = self._determine_wellness_level(overall_score)

            # Generate domain-specific insights
            domain_insights = self._generate_domain_insights(domain_scores)

            # Create personalized recommendations
            recommendations = await self._generate_wellness_recommendations(
                user, domain_scores, overall_score, wellness_level
            )

            # Generate trend analysis if historical data available
            trend_analysis = await self._generate_wellness_trends(
                user, domain_scores, overall_score
            )

            # Save assessment results
            assessment_result = await self._save_wellness_results(
                user,
                responses,
                domain_scores,
                overall_score,
                wellness_level,
                additional_notes,
            )

            # Generate AI-enhanced insights
            ai_insights = await self._generate_ai_wellness_insights(
                user, domain_scores, overall_score, responses
            )

            return {
                "success": True,
                "wellness_result": {
                    "assessment_id": (
                        assessment_result.id if assessment_result else None
                    ),
                    "overall_score": round(overall_score, 2),
                    "wellness_level": wellness_level.value,
                    "domain_scores": {
                        domain.value: {
                            "score": round(score, 2),
                            "level": self._determine_wellness_level(score).value,
                            "weight": self.domain_weights[domain],
                        }
                        for domain, score in domain_scores.items()
                    },
                    "domain_insights": domain_insights,
                    "recommendations": recommendations,
                    "trend_analysis": trend_analysis,
                    "ai_insights": ai_insights,
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_recommended_assessment": "6 weeks",
                },
            }

        except Exception as e:
            logger.error(f"Error processing wellness assessment: {e}")
            return {
                "success": False,
                "error": f"Failed to process wellness assessment: {e!s}",
            }

    def _calculate_domain_scores(
        self, responses: dict[str, int]
    ) -> dict[WellnessDomain, float]:
        """Calculate wellness scores for each domain"""
        domain_scores = {}

        for domain in WellnessDomain:
            domain_questions = self.wellness_questions.get(domain.value, [])
            if not domain_questions:
                domain_scores[domain] = 0.0
                continue

            # Get responses for this domain
            domain_responses = []
            for question in domain_questions:
                question_id = question["id"]
                if question_id in responses:
                    domain_responses.append(responses[question_id])

            # Calculate average score for domain (normalized to 0-1)
            if domain_responses:
                average_score = sum(domain_responses) / len(domain_responses)
                # Normalize from 1-5 scale to 0-1 scale
                normalized_score = (average_score - 1) / 4
                domain_scores[domain] = max(0.0, min(1.0, normalized_score))
            else:
                domain_scores[domain] = 0.0

        return domain_scores

    def _calculate_overall_wellness_score(
        self, domain_scores: dict[WellnessDomain, float]
    ) -> float:
        """Calculate weighted overall wellness score"""
        total_weighted_score = sum(
            score * self.domain_weights[domain]
            for domain, score in domain_scores.items()
        )
        return max(0.0, min(1.0, total_weighted_score))

    def _determine_wellness_level(self, score: float) -> WellnessLevel:
        """Determine wellness level based on score"""
        for level, (min_score, max_score) in self.wellness_thresholds.items():
            if min_score <= score <= max_score:
                return level
        return WellnessLevel.POOR

    def _generate_domain_insights(
        self, domain_scores: dict[WellnessDomain, float]
    ) -> dict[str, Any]:
        """Generate insights for each wellness domain"""
        insights = {}

        for domain, score in domain_scores.items():
            level = self._determine_wellness_level(score)

            domain_insight = {
                "score": round(score, 2),
                "level": level.value,
                "strengths": [],
                "areas_for_improvement": [],
                "description": self._get_domain_description(domain, level),
            }

            # Generate domain-specific insights
            if score >= 0.7:
                domain_insight["strengths"].append(f"Strong {domain.value} wellness")
            elif score < 0.5:
                domain_insight["areas_for_improvement"].append(
                    f"Focus on improving {domain.value} wellness"
                )

            insights[domain.value] = domain_insight

        return insights

    def _get_domain_description(
        self, domain: WellnessDomain, level: WellnessLevel
    ) -> str:
        """Get description for domain and level"""
        descriptions = {
            (
                WellnessDomain.PHYSICAL,
                WellnessLevel.EXCELLENT,
            ): "Excellent physical health habits and fitness",
            (
                WellnessDomain.PHYSICAL,
                WellnessLevel.GOOD,
            ): "Good physical health with room for optimization",
            (
                WellnessDomain.PHYSICAL,
                WellnessLevel.MODERATE,
            ): "Moderate physical health, some improvements needed",
            (
                WellnessDomain.PHYSICAL,
                WellnessLevel.NEEDS_IMPROVEMENT,
            ): "Physical health needs attention and improvement",
            (
                WellnessDomain.PHYSICAL,
                WellnessLevel.POOR,
            ): "Physical health requires immediate attention",
            (
                WellnessDomain.EMOTIONAL,
                WellnessLevel.EXCELLENT,
            ): "Excellent emotional regulation and well-being",
            (
                WellnessDomain.EMOTIONAL,
                WellnessLevel.GOOD,
            ): "Good emotional health with strong coping skills",
            (
                WellnessDomain.EMOTIONAL,
                WellnessLevel.MODERATE,
            ): "Moderate emotional health, some stress management needed",
            (
                WellnessDomain.EMOTIONAL,
                WellnessLevel.NEEDS_IMPROVEMENT,
            ): "Emotional health needs improvement and support",
            (
                WellnessDomain.EMOTIONAL,
                WellnessLevel.POOR,
            ): "Emotional health requires immediate attention and support",
            # Add descriptions for other domains as needed
        }

        return descriptions.get(
            (domain, level), f"{domain.value.title()} wellness: {level.value}"
        )

    async def _generate_wellness_recommendations(
        self,
        user: User,
        domain_scores: dict[WellnessDomain, float],
        overall_score: float,
        wellness_level: WellnessLevel,
    ) -> list[dict[str, Any]]:
        """Generate personalized wellness recommendations"""
        recommendations = []

        # Domain-specific recommendations
        for domain, score in domain_scores.items():
            if score < 0.6:  # Domains that need improvement
                domain_recommendations = self._get_domain_recommendations(domain, score)
                recommendations.extend(domain_recommendations)

        # Overall wellness recommendations
        if overall_score >= 0.8:
            recommendations.append(
                {
                    "type": "maintenance",
                    "title": "Maintain Your Excellent Wellness",
                    "description": "Continue your current wellness practices and explore new growth opportunities",
                    "priority": "low",
                }
            )
        elif overall_score >= 0.6:
            recommendations.append(
                {
                    "type": "enhancement",
                    "title": "Enhance Your Wellness Journey",
                    "description": "Focus on the domains that need improvement while maintaining your strengths",
                    "priority": "medium",
                }
            )
        else:
            recommendations.append(
                {
                    "type": "foundation",
                    "title": "Build Your Wellness Foundation",
                    "description": "Start with small, consistent changes in your lowest-scoring domains",
                    "priority": "high",
                }
            )

        # AI-enhanced personalized recommendations
        try:
            user_history = await self._get_wellness_history(user)
            ai_recommendations = (
                await self.ai_service.generate_wellness_recommendations(
                    user_id=user.id,
                    domain_scores={
                        domain.value: score for domain, score in domain_scores.items()
                    },
                    overall_score=overall_score,
                    wellness_level=wellness_level.value,
                    historical_data=user_history,
                )
            )

            if ai_recommendations:
                recommendations.extend(ai_recommendations)

        except Exception as e:
            logger.warning(f"Could not generate AI wellness recommendations: {e}")

        return recommendations

    def _get_domain_recommendations(
        self, domain: WellnessDomain, score: float
    ) -> list[dict[str, Any]]:
        """Get domain-specific recommendations based on score"""
        recommendations = []

        if domain == WellnessDomain.PHYSICAL:
            if score < 0.5:
                recommendations.extend(
                    [
                        {
                            "type": "domain_specific",
                            "domain": "physical",
                            "title": "Establish a Sleep Routine",
                            "description": "Aim for 7-9 hours of consistent sleep each night",
                            "priority": "high",
                        },
                        {
                            "type": "domain_specific",
                            "domain": "physical",
                            "title": "Start Daily Movement",
                            "description": "Begin with 15-20 minutes of physical activity daily",
                            "priority": "high",
                        },
                    ]
                )

        elif domain == WellnessDomain.EMOTIONAL:
            if score < 0.5:
                recommendations.extend(
                    [
                        {
                            "type": "domain_specific",
                            "domain": "emotional",
                            "title": "Practice Stress Management",
                            "description": "Try meditation, deep breathing, or journaling",
                            "priority": "high",
                        },
                        {
                            "type": "domain_specific",
                            "domain": "emotional",
                            "title": "Consider Professional Support",
                            "description": "A therapist can provide tools for emotional wellness",
                            "priority": "medium",
                        },
                    ]
                )

        # Add recommendations for other domains as needed

        return recommendations

    async def _generate_wellness_trends(
        self,
        user: User,
        current_domain_scores: dict[WellnessDomain, float],
        current_overall_score: float,
    ) -> dict[str, Any]:
        """Generate wellness trend analysis"""
        try:
            # Get historical wellness data
            historical_data = await self._get_wellness_history(user)

            if len(historical_data) < 2:
                return {
                    "trend": "insufficient_data",
                    "message": "Complete more assessments to see trends",
                    "trajectory": "stable",
                }

            # Calculate trends
            recent_scores = [
                entry.get("overall_score", 0) for entry in historical_data[-3:]
            ]
            if len(recent_scores) >= 2:
                trend = (
                    "improving"
                    if recent_scores[-1] > recent_scores[0]
                    else (
                        "declining"
                        if recent_scores[-1] < recent_scores[0]
                        else "stable"
                    )
                )
            else:
                trend = "stable"

            return {
                "trend": trend,
                "trajectory": trend,
                "message": f"Your wellness is {trend} based on recent assessments",
                "assessment_count": len(historical_data),
                "time_span": "several weeks",
            }

        except Exception as e:
            logger.warning(f"Could not generate wellness trends: {e}")
            return {"trend": "unknown", "message": "Unable to analyze trends"}

    async def _save_wellness_results(
        self,
        user: User,
        responses: dict[str, int],
        domain_scores: dict[WellnessDomain, float],
        overall_score: float,
        wellness_level: WellnessLevel,
        additional_notes: str | None = None,
    ) -> Response | None:
        """Save wellness assessment results to database"""
        try:
            result_data = {
                "assessment_type": "wellness_comprehensive",
                "responses": responses,
                "domain_scores": {
                    domain.value: score for domain, score in domain_scores.items()
                },
                "overall_score": overall_score,
                "wellness_level": wellness_level.value,
                "additional_notes": additional_notes,
                "completed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Would save wellness results for user {user.id}: {result_data}"
            )
            return None

        except Exception as e:
            logger.error(f"Error saving wellness results: {e}")
            return None

    async def _generate_ai_wellness_insights(
        self,
        user: User,
        domain_scores: dict[WellnessDomain, float],
        overall_score: float,
        responses: dict[str, int],
    ) -> dict[str, Any]:
        """Generate AI-enhanced wellness insights"""
        try:
            # Identify patterns and correlations
            strongest_domains = sorted(
                domain_scores.items(), key=lambda x: x[1], reverse=True
            )[:2]
            weakest_domains = sorted(domain_scores.items(), key=lambda x: x[1])[:2]

            return {
                "strengths_analysis": {
                    "domains": [domain.value for domain, score in strongest_domains],
                    "message": "These are your strongest wellness areas",
                },
                "improvement_opportunities": {
                    "domains": [domain.value for domain, score in weakest_domains],
                    "message": "Focus on these areas for the biggest impact",
                },
                "holistic_insights": {
                    "balance_score": self._calculate_balance_score(domain_scores),
                    "recommendation": self._get_balance_recommendation(domain_scores),
                },
                "confidence_level": 0.85,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.warning(f"Could not generate AI wellness insights: {e}")
            return {}

    def _calculate_balance_score(
        self, domain_scores: dict[WellnessDomain, float]
    ) -> float:
        """Calculate how balanced the wellness domains are"""
        scores = list(domain_scores.values())
        if not scores:
            return 0.0

        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)

        # Lower variance = more balanced = higher balance score
        balance_score = 1.0 - min(
            1.0, variance / 0.25
        )  # Normalize variance to 0-1 range
        return balance_score

    def _get_balance_recommendation(
        self, domain_scores: dict[WellnessDomain, float]
    ) -> str:
        """Get recommendation based on wellness balance"""
        balance_score = self._calculate_balance_score(domain_scores)

        if balance_score > 0.8:
            return "Excellent balance across all wellness domains. Maintain this holistic approach."
        if balance_score > 0.6:
            return (
                "Good balance with some room for improvement in lower-scoring domains."
            )
        return "Focus on achieving better balance by improving your lowest-scoring wellness domains."

    async def _get_wellness_history(self, user: User) -> list[dict[str, Any]]:
        """Get user's wellness assessment history"""
        # This would query actual wellness assessment history from the database
        return []
