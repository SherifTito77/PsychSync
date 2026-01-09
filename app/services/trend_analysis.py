"""
Trend Analysis Service - Advanced mental health and wellness tracking with AI-powered insights
"""

from datetime import datetime, timedelta
import logging
from typing import Any

import numpy as np
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.services.ai_enhanced_analytics import AIEnhancedAnalyticsService
from app.services.mental_health_screening import MentalHealthScreeningService
from app.services.wellness_monitoring import WellnessMonitoringService

logger = logging.getLogger(__name__)


class TrendAnalysisService:
    """Service for analyzing mental health and wellness trends over time"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_analytics = AIEnhancedAnalyticsService(db)
        self.screening_service = MentalHealthScreeningService(db)
        self.wellness_service = WellnessMonitoringService(db)

    async def get_user_trend_data(
        self, user_id: str, time_range: str = "3m", domains: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get comprehensive trend data for a user

        Args:
            user_id: User identifier
            time_range: Time period ('1m', '3m', '6m', '1y', 'all')
            domains: Specific wellness domains to analyze

        Returns:
            Trend data with AI insights and patterns
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(end_date, time_range)

            # Fetch assessment responses
            responses = await self._fetch_user_responses(user_id, start_date, end_date)

            if not responses:
                return {
                    "success": True,
                    "data": {
                        "trend_data": [],
                        "ai_insights": [],
                        "patterns": {},
                        "recommendations": [],
                    },
                }

            # Process trend data
            trend_data = await self._process_trend_data(responses, domains)

            # Generate AI insights
            ai_insights = await self._generate_trend_insights(trend_data, domains)

            # Identify patterns
            patterns = await self._identify_patterns(trend_data)

            # Generate recommendations
            recommendations = await self._generate_trend_recommendations(trend_data, patterns)

            return {
                "success": True,
                "data": {
                    "trend_data": trend_data,
                    "ai_insights": ai_insights,
                    "patterns": patterns,
                    "recommendations": recommendations,
                    "summary": self._generate_summary(trend_data),
                },
            }

        except Exception as e:
            logger.error(f"Error getting trend data for user {user_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _fetch_user_responses(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> list[Response]:
        """Fetch user responses within date range"""
        try:
            query = (
                select(Response)
                .where(
                    and_(
                        Response.user_id == user_id,
                        Response.completed_at >= start_date,
                        Response.completed_at <= end_date,
                        Response.is_completed == True,
                    )
                )
                .order_by(desc(Response.completed_at))
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error fetching user responses: {e}")
            return []

    async def _process_trend_data(
        self, responses: list[Response], domains: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Process responses into structured trend data"""
        trend_data = []

        for response in responses:
            try:
                # Parse response data
                response_data = response.response_data or {}

                # Determine assessment type
                assessment_type = self._get_assessment_type(response)

                # Calculate domain scores
                domain_scores = await self._calculate_domain_scores(
                    response_data, assessment_type, domains
                )

                # Calculate overall wellness score
                overall_score = self._calculate_overall_score(domain_scores)

                trend_point = {
                    "date": response.completed_at.isoformat()
                    if response.completed_at
                    else datetime.utcnow().isoformat(),
                    "overall_score": overall_score,
                    "domain_scores": domain_scores,
                    "assessment_type": assessment_type,
                    "response_id": response.id,
                }

                trend_data.append(trend_point)

            except Exception as e:
                logger.error(f"Error processing response {response.id}: {e}")
                continue

        return sorted(trend_data, key=lambda x: x["date"])

    def _get_assessment_type(self, response: Response) -> str:
        """Determine the type of assessment"""
        if response.assessment_template:
            template_name = response.assessment_template.name.lower()
            if "wellness" in template_name:
                return "Wellness Assessment"
            if "phq" in template_name or "gad" in template_name:
                return "Mental Health Screening"
            if "mbti" in template_name:
                return "Personality Assessment"
            if "big five" in template_name:
                return "Big Five Assessment"

        return "General Assessment"

    async def _calculate_domain_scores(
        self, response_data: dict[str, Any], assessment_type: str, domains: list[str] | None = None
    ) -> dict[str, float]:
        """Calculate domain-specific scores from response data"""

        # Default wellness domains
        default_domains = [
            "physical",
            "emotional",
            "social",
            "intellectual",
            "spiritual",
            "occupational",
            "environmental",
        ]

        if domains and "all" not in domains:
            target_domains = domains
        else:
            target_domains = default_domains

        domain_scores = {}

        if assessment_type == "Wellness Assessment":
            # Extract domain scores from wellness assessment
            for domain in target_domains:
                domain_scores[domain] = response_data.get(f"{domain}_score", 0.5)

        elif assessment_type == "Mental Health Screening":
            # Map mental health screening to wellness domains
            phq9_score = response_data.get("phq9_score", 0)
            gad7_score = response_data.get("gad7_score", 0)

            # Normalize scores (0-27 range to 0-1)
            normalized_phq9 = max(0, 1 - (phq9_score / 27))
            normalized_gad7 = max(0, 1 - (gad7_score / 21))

            for domain in target_domains:
                if domain == "emotional":
                    domain_scores[domain] = (normalized_phq9 + normalized_gad7) / 2
                elif domain == "physical":
                    domain_scores[domain] = normalized_phq9
                elif domain == "social":
                    domain_scores[domain] = normalized_gad7
                else:
                    # Default score for other domains
                    domain_scores[domain] = 0.6

        else:
            # Default scores for other assessment types
            for domain in target_domains:
                domain_scores[domain] = 0.6

        return domain_scores

    def _calculate_overall_score(self, domain_scores: dict[str, float]) -> float:
        """Calculate overall wellness score from domain scores"""
        if not domain_scores:
            return 0.5

        # Weight different domains
        weights = {
            "physical": 0.20,
            "emotional": 0.20,
            "social": 0.15,
            "intellectual": 0.15,
            "spiritual": 0.10,
            "occupational": 0.15,
            "environmental": 0.05,
        }

        weighted_score = 0.0
        total_weight = 0.0

        for domain, score in domain_scores.items():
            weight = weights.get(domain, 0.10)
            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.5

    async def _generate_trend_insights(
        self, trend_data: list[dict[str, Any]], domains: list[str] | None = None
    ) -> list[str]:
        """Generate AI-powered insights from trend data"""
        insights = []

        if len(trend_data) < 2:
            return ["Continue taking assessments to see trend insights and patterns."]

        try:
            # Calculate trends
            recent_data = trend_data[-5:] if len(trend_data) >= 5 else trend_data
            older_data = trend_data[:-5] if len(trend_data) > 5 else []

            # Overall trend analysis
            overall_trend = self._calculate_trend_direction(
                [d["overall_score"] for d in trend_data]
            )

            if overall_trend == "improving":
                insights.append(
                    "Your overall wellness is showing positive improvement over time. Keep up the great work!"
                )
            elif overall_trend == "declining":
                insights.append(
                    "Your wellness scores show a declining trend. Consider focusing on self-care and professional support."
                )
            else:
                insights.append(
                    "Your wellness levels are relatively stable. Small, consistent changes can lead to significant improvements."
                )

            # Domain-specific insights
            if not domains or "all" in domains:
                domain_trends = {}
                for domain in [
                    "physical",
                    "emotional",
                    "social",
                    "intellectual",
                    "spiritual",
                    "occupational",
                    "environmental",
                ]:
                    scores = [
                        d["domain_scores"].get(domain, 0.5)
                        for d in trend_data
                        if domain in d["domain_scores"]
                    ]
                    if scores:
                        domain_trends[domain] = self._calculate_trend_direction(scores)

                # Best improving domain
                improving_domains = [d for d, t in domain_trends.items() if t == "improving"]
                if improving_domains:
                    insights.append(
                        f"Your {improving_domains[0]} wellness is showing the most improvement. This is a great strength to build upon."
                    )

                # Areas needing attention
                declining_domains = [d for d, t in domain_trends.items() if t == "declining"]
                if declining_domains:
                    insights.append(
                        f"Consider focusing more attention on your {declining_domains[0]} wellness, which shows room for improvement."
                    )

            # Consistency insights
            assessment_frequency = self._calculate_assessment_frequency(trend_data)
            if assessment_frequency < 0.5:  # Less than 2 assessments per month
                insights.append(
                    "More frequent assessments can provide better insights and help track progress more effectively."
                )

            # Recent change insights
            if len(recent_data) >= 3:
                recent_change = recent_data[-1]["overall_score"] - recent_data[0]["overall_score"]
                if abs(recent_change) > 0.1:
                    if recent_change > 0:
                        insights.append(
                            "Recent assessments show significant improvement. Your current approach is working well!"
                        )
                    else:
                        insights.append(
                            "Recent scores indicate some challenges. This is normal - focus on self-compassion and consider reaching out for support."
                        )

        except Exception as e:
            logger.error(f"Error generating trend insights: {e}")
            insights.append(
                "Trend analysis is available. Continue regular assessments for more detailed insights."
            )

        return insights[:5]  # Limit to 5 insights

    def _calculate_trend_direction(self, scores: list[float]) -> str:
        """Calculate trend direction from a series of scores"""
        if len(scores) < 2:
            return "stable"

        # Use linear regression to determine trend
        x = np.arange(len(scores))
        y = np.array(scores)

        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.02:
            return "improving"
        if slope < -0.02:
            return "declining"
        return "stable"

    def _calculate_assessment_frequency(self, trend_data: list[dict[str, Any]]) -> float:
        """Calculate assessment frequency (assessments per month)"""
        if len(trend_data) < 2:
            return 0

        dates = [datetime.fromisoformat(d["date"].replace("Z", "+00:00")) for d in trend_data]
        time_span = (max(dates) - min(dates)).days

        if time_span == 0:
            return len(trend_data)

        return (len(trend_data) / time_span) * 30  # Convert to monthly frequency

    async def _identify_patterns(self, trend_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Identify patterns in the trend data"""
        patterns = {}

        try:
            if len(trend_data) < 3:
                return {"message": "More data needed for pattern analysis"}

            # Time-based patterns
            dates = [datetime.fromisoformat(d["date"].replace("Z", "+00:00")) for d in trend_data]
            scores = [d["overall_score"] for d in trend_data]

            # Weekly patterns
            weekly_scores = {}
            for date, score in zip(dates, scores):
                day_of_week = date.strftime("%A")
                if day_of_week not in weekly_scores:
                    weekly_scores[day_of_week] = []
                weekly_scores[day_of_week].append(score)

            # Average scores by day of week
            weekly_averages = {
                day: np.mean(scores) for day, scores in weekly_scores.items() if scores
            }
            if weekly_averages:
                best_day = max(weekly_averages, key=weekly_averages.get)
                worst_day = min(weekly_averages, key=weekly_averages.get)
                patterns["weekly_pattern"] = {
                    "best_day": best_day,
                    "worst_day": worst_day,
                    "average_range": max(weekly_averages.values()) - min(weekly_averages.values()),
                }

            # Variability analysis
            score_variance = np.var(scores)
            patterns["variability"] = {
                "variance": score_variance,
                "stability": "high"
                if score_variance < 0.01
                else "medium"
                if score_variance < 0.05
                else "low",
            }

            # Peak and low points
            peak_score = max(scores)
            low_score = min(scores)
            patterns["extremes"] = {
                "peak_score": peak_score,
                "low_score": low_score,
                "range": peak_score - low_score,
            }

        except Exception as e:
            logger.error(f"Error identifying patterns: {e}")
            patterns = {"error": "Pattern analysis unavailable"}

        return patterns

    async def _generate_trend_recommendations(
        self, trend_data: list[dict[str, Any]], patterns: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate personalized recommendations based on trends and patterns"""
        recommendations = []

        try:
            if len(trend_data) < 2:
                return [
                    {
                        "type": "general",
                        "title": "Start Your Wellness Journey",
                        "description": "Take regular assessments to establish your baseline and begin tracking progress.",
                        "priority": "medium",
                    }
                ]

            current_score = trend_data[-1]["overall_score"]

            # Score-based recommendations
            if current_score < 0.4:
                recommendations.append(
                    {
                        "type": "urgent",
                        "title": "Focus on Self-Care",
                        "description": "Your current wellness score indicates you may benefit from additional support and self-care practices.",
                        "priority": "high",
                    }
                )
            elif current_score > 0.8:
                recommendations.append(
                    {
                        "type": "maintenance",
                        "title": "Maintain Your Progress",
                        "description": "Your wellness score is excellent! Focus on maintaining these positive habits and consider helping others.",
                        "priority": "low",
                    }
                )

            # Pattern-based recommendations
            if "variability" in patterns:
                stability = patterns["variability"].get("stability", "medium")
                if stability == "high":
                    recommendations.append(
                        {
                            "type": "consistency",
                            "title": "Excellent Consistency",
                            "description": "Your wellness scores show great consistency. Consider introducing new healthy challenges to continue growing.",
                            "priority": "low",
                        }
                    )
                elif stability == "low":
                    recommendations.append(
                        {
                            "type": "stability",
                            "title": "Work on Stability",
                            "description": "Your scores show high variability. Focus on establishing consistent daily routines and stress management techniques.",
                            "priority": "medium",
                        }
                    )

            # Trend-based recommendations
            if len(trend_data) >= 5:
                recent_trend = self._calculate_trend_direction(
                    [d["overall_score"] for d in trend_data[-5:]]
                )

                if recent_trend == "declining":
                    recommendations.append(
                        {
                            "type": "intervention",
                            "title": "Address Recent Decline",
                            "description": "Recent scores show a declining pattern. Consider revisiting your wellness strategies or consulting with a healthcare professional.",
                            "priority": "high",
                        }
                    )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations = [
                {
                    "type": "general",
                    "title": "Continue Monitoring",
                    "description": "Keep tracking your wellness journey to build a more complete picture over time.",
                    "priority": "medium",
                }
            ]

        return recommendations[:4]  # Limit to 4 recommendations

    def _generate_summary(self, trend_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a summary of the trend analysis"""
        if not trend_data:
            return {
                "total_assessments": 0,
                "time_span_days": 0,
                "average_score": 0,
                "current_score": 0,
                "overall_trend": "no_data",
            }

        scores = [d["overall_score"] for d in trend_data]
        dates = [datetime.fromisoformat(d["date"].replace("Z", "+00:00")) for d in trend_data]

        return {
            "total_assessments": len(trend_data),
            "time_span_days": (max(dates) - min(dates)).days,
            "average_score": np.mean(scores),
            "current_score": scores[-1],
            "overall_trend": self._calculate_trend_direction(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
        }

    def _calculate_start_date(self, end_date: datetime, time_range: str) -> datetime:
        """Calculate start date based on time range"""
        time_ranges = {
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
        }

        if time_range == "all":
            return datetime(2020, 1, 1)  # Far past date for "all time"

        return end_date - time_ranges.get(time_range, timedelta(days=90))

    async def get_domain_comparison(self, user_id: str, time_range: str = "3m") -> dict[str, Any]:
        """Get domain-specific comparison and analysis"""
        try:
            trend_result = await self.get_user_trend_data(user_id, time_range)

            if not trend_result["success"] or not trend_result["data"]["trend_data"]:
                return {"success": False, "error": "No trend data available for comparison"}

            trend_data = trend_result["data"]["trend_data"]

            # Calculate domain averages and trends
            domain_analysis = {}
            domains = [
                "physical",
                "emotional",
                "social",
                "intellectual",
                "spiritual",
                "occupational",
                "environmental",
            ]

            for domain in domains:
                scores = [
                    d["domain_scores"].get(domain, 0.5)
                    for d in trend_data
                    if domain in d["domain_scores"]
                ]

                if scores:
                    domain_analysis[domain] = {
                        "average": np.mean(scores),
                        "current": scores[-1] if scores else 0.5,
                        "trend": self._calculate_trend_direction(scores),
                        "best": max(scores),
                        "worst": min(scores),
                        "improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
                    }

            return {
                "success": True,
                "data": {
                    "domain_analysis": domain_analysis,
                    "strongest_domain": max(
                        domain_analysis.keys(), key=lambda d: domain_analysis[d]["average"]
                    )
                    if domain_analysis
                    else None,
                    "most_improved_domain": max(
                        domain_analysis.keys(), key=lambda d: domain_analysis[d]["improvement"]
                    )
                    if domain_analysis
                    else None,
                    "attention_needed": [
                        d
                        for d, analysis in domain_analysis.items()
                        if analysis["trend"] == "declining"
                    ],
                },
            }

        except Exception as e:
            logger.error(f"Error getting domain comparison: {e}")
            return {"success": False, "error": str(e)}
