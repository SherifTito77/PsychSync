"""
AI-Behavioral Integration Service
Integrates AI personality processors with behavioral pattern recognition for enhanced insights
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

# Import AI processors
from ai.processors.big_five import BigFiveProcessor
from ai.processors.enneagram_processor import EnneagramProcessor
from ai.processors.mbti_processor import MBTIProcessor
from ai.processors.predictive_index import PredictiveIndexProcessor
from app.services.anomaly_detection import AdvancedAnomalyDetector

# Import behavioral services
from app.services.behavioral_pattern_recognition import (
    BehavioralPatternRecognizer,
    PatternType,
)

# Try to import NLP service - may fail due to spacy/pydantic incompatibility
try:
    from app.services.nlp_service import NLPService

    NLP_AVAILABLE = True
except (ImportError, Exception) as e:
    NLP_AVAILABLE = False
    NLPService = None
    logger.warning(f"NLP service not available: {e}")

logger = logging.getLogger(__name__)


class AIBehavioralIntegrationService:
    """
    Advanced AI service that combines personality framework processing
    with behavioral pattern recognition for comprehensive user insights
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_processors = {
            "big_five": BigFiveProcessor(),
            "mbti": MBTIProcessor(),
            "enneagram": EnneagramProcessor(),
            "predictive_index": PredictiveIndexProcessor(),
        }
        self.pattern_recognizer = BehavioralPatternRecognizer(db)
        self.anomaly_detector = AdvancedAnomalyDetector(db)
        # Only initialize NLP service if available
        self.nlp_service = NLPService() if NLP_AVAILABLE else None

    async def get_comprehensive_user_profile(
        self,
        user_id: str,
        time_window_hours: int = 720,  # 30 days
        include_predictions: bool = True,
    ) -> dict[str, Any]:
        """
        Generate comprehensive user profile combining AI processing and behavioral analysis

        Args:
            user_id: User to analyze
            time_window_hours: Time window for behavioral analysis
            include_predictions: Whether to include AI predictions

        Returns:
            Comprehensive user profile with AI-enhanced insights
        """
        try:
            logger.info(
                f"Generating comprehensive AI-behavioral profile for user {user_id}"
            )

            # Get behavioral pattern analysis
            behavioral_analysis = await self.pattern_recognizer.analyze_user_behavior(
                user_id, time_window_hours
            )

            # Get AI personality assessments
            personality_insights = await self._get_personality_insights(user_id)

            # AI-enhanced pattern interpretation
            enhanced_patterns = await self._enhance_patterns_with_ai(
                behavioral_analysis.get("patterns", []), personality_insights
            )

            # Predict behavioral trends
            predictions = {}
            if include_predictions:
                predictions = await self._predict_behavioral_trends(
                    behavioral_analysis, personality_insights
                )

            # Generate AI-powered recommendations
            ai_recommendations = await self._generate_ai_recommendations(
                behavioral_analysis, personality_insights, enhanced_patterns
            )

            # Calculate AI confidence scores
            confidence_scores = await self._calculate_ai_confidence(
                behavioral_analysis, personality_insights
            )

            return {
                "user_id": user_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "behavioral_analysis": behavioral_analysis,
                "personality_insights": personality_insights,
                "ai_enhanced_patterns": enhanced_patterns,
                "predictions": predictions,
                "ai_recommendations": ai_recommendations,
                "confidence_scores": confidence_scores,
                "integration_summary": await self._generate_integration_summary(
                    behavioral_analysis, personality_insights, confidence_scores
                ),
            }

        except Exception as e:
            logger.error(
                f"Error generating comprehensive profile for user {user_id}: {e}"
            )
            return {
                "user_id": user_id,
                "error": str(e),
                "fallback_profile": await self._generate_fallback_profile(user_id),
            }

    async def _get_personality_insights(self, user_id: str) -> dict[str, Any]:
        """Get personality assessment insights from AI processors"""

        personality_insights = {
            "available_assessments": [],
            "unified_profile": {},
            "cross_framework_analysis": {},
            "development_potential": {},
        }

        try:
            # Query user's personality assessments
            from app.db.models.assessment import Assessment, AssessmentResponse

            # Get completed personality assessments
            personality_query = (
                select(AssessmentResponse, Assessment)
                .join(Assessment, AssessmentResponse.assessment_id == Assessment.id)
                .where(
                    and_(
                        AssessmentResponse.respondent_id == user_id,
                        AssessmentResponse.status == "completed",
                        Assessment.category.in_(["personality", "behavioral"]),
                    )
                )
                .order_by(AssessmentResponse.completed_at.desc())
            )

            result = await self.db.execute(personality_query)
            assessments = result.all()

            # Process each assessment with appropriate AI processor
            for response, assessment in assessments:
                framework_code = assessment.framework_code.lower()

                if framework_code in self.ai_processors:
                    processor = self.ai_processors[framework_code]

                    try:
                        # Process assessment results with AI
                        processed_result = processor._safe_process(
                            response.responses or {}
                        )

                        personality_insights["available_assessments"].append(
                            {
                                "framework": framework_code,
                                "assessment_id": str(assessment.id),
                                "completed_at": (
                                    response.completed_at.isoformat()
                                    if response.completed_at
                                    else None
                                ),
                                "processed_result": processed_result,
                            }
                        )

                        # Add to unified profile
                        if "dimensions" in processed_result:
                            personality_insights["unified_profile"].update(
                                processed_result["dimensions"]
                            )

                    except Exception as e:
                        logger.warning(
                            f"Error processing {framework_code} assessment: {e}"
                        )
                        continue

            # Cross-framework analysis
            if len(personality_insights["available_assessments"]) > 1:
                personality_insights["cross_framework_analysis"] = (
                    await self._analyze_cross_framework_patterns(
                        personality_insights["available_assessments"]
                    )
                )

            # Development potential analysis
            personality_insights["development_potential"] = (
                await self._analyze_development_potential(
                    personality_insights["unified_profile"]
                )
            )

        except Exception as e:
            logger.error(f"Error getting personality insights for user {user_id}: {e}")

        return personality_insights

    async def _enhance_patterns_with_ai(
        self, patterns: list[dict[str, Any]], personality_insights: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Enhance behavioral patterns with AI personality insights"""

        enhanced_patterns = []

        for pattern in patterns:
            enhanced_pattern = pattern.copy()

            # Add personality context
            personality_context = await self._get_personality_pattern_context(
                pattern, personality_insights
            )
            enhanced_pattern["personality_context"] = personality_context

            # AI-based interpretation
            ai_interpretation = await self._ai_interpret_pattern(
                pattern, personality_insights
            )
            enhanced_pattern["ai_interpretation"] = ai_interpretation

            # Predictive insights
            predictive_insights = await self._predict_pattern_evolution(
                pattern, personality_insights
            )
            enhanced_pattern["predictive_insights"] = predictive_insights

            enhanced_patterns.append(enhanced_pattern)

        return enhanced_patterns

    async def _get_personality_pattern_context(
        self, pattern: dict[str, Any], personality_insights: dict[str, Any]
    ) -> dict[str, Any]:
        """Get personality context for a behavioral pattern"""

        context = {
            "personality_drivers": [],
            "compatibility_score": 0.0,
            "development_implications": [],
        }

        unified_profile = personality_insights.get("unified_profile", {})

        if pattern.get("pattern_type") == PatternType.SOCIAL.value:
            # Social patterns influenced by extraversion and agreeableness
            if "extraversion" in unified_profile:
                extraversion = unified_profile["extraversion"]
                context["personality_drivers"].append(
                    f"Extraversion level: {extraversion:.2f}"
                )
                context["compatibility_score"] = extraversion

            if "agreeableness" in unified_profile:
                agreeableness = unified_profile["agreeableness"]
                context["personality_drivers"].append(
                    f"Agreeableness level: {agreeableness:.2f}"
                )

        elif pattern.get("pattern_type") == PatternType.PERFORMANCE.value:
            # Performance patterns influenced by conscientiousness
            if "conscientiousness" in unified_profile:
                conscientiousness = unified_profile["conscientiousness"]
                context["personality_drivers"].append(
                    f"Conscientiousness level: {conscientiousness:.2f}"
                )
                context["compatibility_score"] = conscientiousness

        elif pattern.get("pattern_type") == PatternType.LEARNING.value:
            # Learning patterns influenced by openness
            if "openness" in unified_profile:
                openness = unified_profile["openness"]
                context["personality_drivers"].append(f"Openness level: {openness:.2f}")
                context["compatibility_score"] = openness

        elif pattern.get("pattern_type") == PatternType.RISK.value:
            # Risk patterns influenced by neuroticism and emotional stability
            if "neuroticism" in unified_profile:
                neuroticism = unified_profile["neuroticism"]
                context["personality_drivers"].append(
                    f"Neuroticism level: {neuroticism:.2f}"
                )
                # Higher neuroticism increases risk pattern likelihood
                context["compatibility_score"] = 1.0 - neuroticism

        return context

    async def _ai_interpret_pattern(
        self, pattern: dict[str, Any], personality_insights: dict[str, Any]
    ) -> dict[str, Any]:
        """Use AI to interpret patterns in personality context"""

        interpretation = {
            "ai_assessment": "",
            "confidence_factors": [],
            "personality_alignment": 0.0,
            "actionable_insights": [],
        }

        pattern_type = pattern.get("pattern_type", "")
        confidence = pattern.get("confidence", 0.0)
        personality_context = await self._get_personality_pattern_context(
            pattern, personality_insights
        )

        # AI assessment based on pattern type and personality
        if pattern_type == PatternType.SOCIAL.value:
            if personality_context.get("compatibility_score", 0) > 0.7:
                interpretation["ai_assessment"] = (
                    "Social patterns align well with personality profile"
                )
                interpretation["actionable_insights"].append(
                    "Leverage natural social tendencies for team collaboration"
                )
            else:
                interpretation["ai_assessment"] = (
                    "Social patterns may require conscious effort or adaptation"
                )
                interpretation["actionable_insights"].append(
                    "Consider structured social activities to build comfort"
                )

        elif pattern_type == PatternType.PERFORMANCE.value:
            if personality_context.get("compatibility_score", 0) > 0.6:
                interpretation["ai_assessment"] = (
                    "Performance patterns are consistent with natural work style"
                )
                interpretation["actionable_insights"].append(
                    "Optimize workflow to match natural performance patterns"
                )
            else:
                interpretation["ai_assessment"] = (
                    "Performance patterns may require adaptation or skill development"
                )
                interpretation["actionable_insights"].append(
                    "Focus on skill development in performance areas"
                )

        # Calculate personality alignment
        interpretation["personality_alignment"] = personality_context.get(
            "compatibility_score", 0.0
        )

        # Confidence factors
        interpretation["confidence_factors"] = [
            f"Pattern confidence: {confidence:.2f}",
            f"Personality alignment: {interpretation['personality_alignment']:.2f}",
            f"Data quality: {pattern.get('data_quality', 0.5):.2f}",
        ]

        return interpretation

    async def _predict_pattern_evolution(
        self, pattern: dict[str, Any], personality_insights: dict[str, Any]
    ) -> dict[str, Any]:
        """Predict how patterns might evolve based on personality traits"""

        predictions = {
            "evolution_trend": "stable",
            "confidence": 0.5,
            "time_horizon": "30 days",
            "influencing_factors": [],
            "recommendations": [],
        }

        unified_profile = personality_insights.get("unified_profile", {})

        # Predictions based on personality traits
        if "conscientiousness" in unified_profile:
            conscientiousness = unified_profile["conscientiousness"]
            if conscientiousness > 0.7:
                predictions["evolution_trend"] = "improving"
                predictions["confidence"] += 0.2
                predictions["influencing_factors"].append(
                    "High conscientiousness suggests positive development"
                )
                predictions["recommendations"].append(
                    "Maintain structured approach for continued improvement"
                )
            elif conscientiousness < 0.3:
                predictions["evolution_trend"] = "declining"
                predictions["confidence"] += 0.15
                predictions["influencing_factors"].append(
                    "Low conscientiousness may lead to pattern degradation"
                )
                predictions["recommendations"].append(
                    "Implement external accountability measures"
                )

        if "openness" in unified_profile:
            openness = unified_profile["openness"]
            if openness > 0.7:
                predictions["influencing_factors"].append(
                    "High openness suggests adaptability to new patterns"
                )
                predictions["recommendations"].append(
                    "Introduce variety to maintain engagement"
                )

        return predictions

    async def _predict_behavioral_trends(
        self, behavioral_analysis: dict[str, Any], personality_insights: dict[str, Any]
    ) -> dict[str, Any]:
        """Predict future behavioral trends using AI"""

        predictions = {
            "short_term_trends": {},  # 1-4 weeks
            "medium_term_trends": {},  # 1-3 months
            "long_term_trends": {},  # 3+ months
            "confidence_scores": {},
            "risk_factors": [],
            "opportunities": [],
        }

        unified_profile = personality_insights.get("unified_profile", {})
        risk_assessment = behavioral_analysis.get("risk_assessment", {})

        # Short-term predictions based on current patterns
        current_patterns = behavioral_analysis.get("patterns", [])
        pattern_types = [p.get("pattern_type") for p in current_patterns]

        if "social" in pattern_types and unified_profile.get("extraversion", 0.5) > 0.6:
            predictions["short_term_trends"]["social_engagement"] = "increasing"
            predictions["opportunities"].append(
                "Leadership opportunities in team settings"
            )

        if (
            "performance" in pattern_types
            and unified_profile.get("conscientiousness", 0.5) > 0.7
        ):
            predictions["short_term_trends"]["productivity"] = "improving"
            predictions["opportunities"].append("Complex project assignments")

        # Medium-term predictions based on personality stability
        personality_stability = len(unified_profile) / 5.0  # Assuming 5 main traits
        if personality_stability > 0.6:
            predictions["medium_term_trends"]["personality_consistency"] = "high"
            predictions["confidence_scores"]["medium_term"] = 0.8
        else:
            predictions["medium_term_trends"]["personality_consistency"] = "moderate"
            predictions["confidence_scores"]["medium_term"] = 0.5

        # Long-term predictions based on risk factors
        if risk_assessment.get("risk_score", 0) < 0.3:
            predictions["long_term_trends"]["career_trajectory"] = "positive"
            predictions["confidence_scores"]["long_term"] = 0.7
        elif risk_assessment.get("risk_score", 0) > 0.7:
            predictions["risk_factors"].append(
                "High behavioral risk may impact long-term performance"
            )
            predictions["recommendations"] = [
                "Address risk factors through targeted interventions"
            ]

        return predictions

    async def _generate_ai_recommendations(
        self,
        behavioral_analysis: dict[str, Any],
        personality_insights: dict[str, Any],
        enhanced_patterns: list[dict[str, Any]],
    ) -> list[str]:
        """Generate AI-powered recommendations based on combined analysis"""

        recommendations = []
        unified_profile = personality_insights.get("unified_profile", {})

        # Personality-based development recommendations
        if "openness" in unified_profile:
            openness = unified_profile["openness"]
            if openness > 0.8:
                recommendations.append(
                    "Leverage high openness through innovation projects and learning opportunities"
                )
            elif openness < 0.3:
                recommendations.append(
                    "Gradually increase exposure to new experiences to develop adaptability"
                )

        if "conscientiousness" in unified_profile:
            conscientiousness = unified_profile["conscientiousness"]
            if conscientiousness > 0.8:
                recommendations.append(
                    "Utilize strong organizational skills for leadership and mentoring roles"
                )
            elif conscientiousness < 0.3:
                recommendations.append(
                    "Implement structured systems and accountability partnerships"
                )

        # Pattern-based recommendations
        high_confidence_patterns = [
            p for p in enhanced_patterns if p.get("confidence", 0) > 0.7
        ]
        for pattern in high_confidence_patterns:
            ai_interpretation = pattern.get("ai_interpretation", {})
            actionable_insights = ai_interpretation.get("actionable_insights", [])
            recommendations.extend(actionable_insights)

        # Risk-based recommendations
        risk_assessment = behavioral_analysis.get("risk_assessment", {})
        if risk_assessment.get("risk_level") == "high":
            recommendations.append(
                "Prioritize addressing high-risk behavioral patterns through professional support"
            )
            recommendations.append(
                "Consider personality-aligned stress management techniques"
            )

        # Remove duplicates and limit to top recommendations
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:8]  # Top 8 recommendations

    async def _calculate_ai_confidence(
        self, behavioral_analysis: dict[str, Any], personality_insights: dict[str, Any]
    ) -> dict[str, float]:
        """Calculate confidence scores for different aspects of the analysis"""

        confidence_scores = {
            "behavioral_patterns": 0.0,
            "personality_insights": 0.0,
            "ai_integration": 0.0,
            "overall_confidence": 0.0,
        }

        # Behavioral pattern confidence
        data_quality = behavioral_analysis.get("data_quality", {}).get(
            "overall_quality", 0.0
        )
        patterns_count = len(behavioral_analysis.get("patterns", []))
        pattern_confidence = min(
            patterns_count / 10.0, 1.0
        )  # More patterns = higher confidence
        confidence_scores["behavioral_patterns"] = (
            data_quality + pattern_confidence
        ) / 2.0

        # Personality insights confidence
        assessments_count = len(personality_insights.get("available_assessments", []))
        personality_confidence = min(
            assessments_count / 3.0, 1.0
        )  # More assessments = higher confidence
        confidence_scores["personality_insights"] = personality_confidence

        # AI integration confidence
        unified_profile_size = len(personality_insights.get("unified_profile", {}))
        integration_confidence = min(
            unified_profile_size / 5.0, 1.0
        )  # More data = higher confidence
        confidence_scores["ai_integration"] = integration_confidence

        # Overall confidence (weighted average)
        confidence_scores["overall_confidence"] = (
            confidence_scores["behavioral_patterns"] * 0.4
            + confidence_scores["personality_insights"] * 0.3
            + confidence_scores["ai_integration"] * 0.3
        )

        return confidence_scores

    async def _analyze_cross_framework_patterns(
        self, assessments: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze patterns across different personality frameworks"""

        cross_analysis = {
            "framework_consistency": 0.0,
            "trait_correlations": {},
            "composite_profile": {},
            "confidence_indicators": {},
        }

        # Extract dimensions from all frameworks
        all_dimensions = {}
        for assessment in assessments:
            processed_result = assessment.get("processed_result", {})
            dimensions = processed_result.get("dimensions", {})
            all_dimensions.update(dimensions)

        # Calculate composite profile
        cross_analysis["composite_profile"] = all_dimensions

        # Calculate consistency (simplified)
        if len(assessments) > 1:
            cross_analysis["framework_consistency"] = (
                0.7  # Placeholder - would calculate actual consistency
            )

        return cross_analysis

    async def _analyze_development_potential(
        self, unified_profile: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze development potential based on personality profile"""

        development = {
            "growth_areas": [],
            "leadership_potential": 0.0,
            "team_fit_recommendations": [],
            "learning_recommendations": [],
        }

        # Leadership potential based on key traits
        leadership_traits = ["conscientiousness", "extraversion", "agreeableness"]
        leadership_score = 0.0
        count = 0

        for trait in leadership_traits:
            if trait in unified_profile:
                leadership_score += unified_profile[trait]
                count += 1

        if count > 0:
            development["leadership_potential"] = leadership_score / count

        # Growth areas (lower-scoring traits)
        for trait, score in unified_profile.items():
            if score < 0.4:
                development["growth_areas"].append(
                    {
                        "trait": trait,
                        "current_level": score,
                        "development_priority": "high" if score < 0.3 else "medium",
                    }
                )

        return development

    async def _generate_integration_summary(
        self,
        behavioral_analysis: dict[str, Any],
        personality_insights: dict[str, Any],
        confidence_scores: dict[str, float],
    ) -> dict[str, Any]:
        """Generate summary of the AI-behavioral integration"""

        summary = {
            "data_sources": [],
            "integration_quality": 0.0,
            "key_insights": [],
            "actionable_summary": [],
            "limitations": [],
        }

        # Data sources
        data_sources = []
        if behavioral_analysis.get("events_analyzed", 0) > 0:
            data_sources.append("Behavioral tracking")
        if len(personality_insights.get("available_assessments", [])) > 0:
            data_sources.append(
                f"Personality assessments ({len(personality_insights['available_assessments'])})"
            )

        summary["data_sources"] = data_sources

        # Integration quality
        summary["integration_quality"] = confidence_scores.get(
            "overall_confidence", 0.0
        )

        # Key insights
        risk_level = behavioral_analysis.get("risk_assessment", {}).get(
            "risk_level", "low"
        )
        if risk_level != "low":
            summary["key_insights"].append(f"Behavioral risk level: {risk_level}")

        leadership_potential = personality_insights.get(
            "development_potential", {}
        ).get("leadership_potential", 0.0)
        if leadership_potential > 0.7:
            summary["key_insights"].append("High leadership potential detected")

        # Limitations
        if confidence_scores.get("overall_confidence", 0.0) < 0.5:
            summary["limitations"].append(
                "Limited data available - increased usage will improve insights"
            )

        return summary

    async def _generate_fallback_profile(self, user_id: str) -> dict[str, Any]:
        """Generate fallback profile when comprehensive analysis fails"""

        return {
            "user_id": user_id,
            "profile_type": "fallback",
            "message": "Limited data available for comprehensive analysis",
            "recommendations": [
                "Complete personality assessments for deeper insights",
                "Increase platform usage for behavioral pattern detection",
                "Regular check-ins will improve analysis accuracy",
            ],
            "data_quality_score": 0.2,
            "next_steps": [
                "Take a personality assessment",
                "Engage more with platform features",
                "Schedule regular check-ins",
            ],
        }
