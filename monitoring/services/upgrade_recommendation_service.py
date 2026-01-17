#!/usr/bin/env python3
"""
Upgrade Recommendation Service
Analyzes customer usage and behavior to recommend optimal subscription tiers
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .pricing_service import PricingService, SubscriptionTier, BillingCycle, Subscription

logger = logging.getLogger(__name__)

@dataclass
class UsagePattern:
    """Customer usage patterns for recommendation analysis"""
    revenue_growth_rate: float
    team_growth_rate: float
    incident_frequency: float
    feature_adoption_score: float
    business_impact_score: float
    engagement_level: str  # low, medium, high

@dataclass
class UpgradeRecommendation:
    """Personalized upgrade recommendation"""
    customer_id: str
    current_tier: SubscriptionTier
    recommended_tier: SubscriptionTier
    urgency_score: float  # 0-100, higher = more urgent
    confidence_score: float  # 0-100, higher = more confident
    value_proposition: Dict[str, Any]
    upgrade_triggers: List[str]
    timeline_recommendation: str
    personalized_message: str
    estimated_roi: float

class UpgradeRecommendationService:
    """Analyzes usage patterns and generates personalized upgrade recommendations"""

    def __init__(self, pricing_service: PricingService):
        self.pricing_service = pricing_service

    async def analyze_usage_patterns(self, customer_id: str, metrics: Dict[str, Any], historical_data: List[Dict[str, Any]] = None) -> UsagePattern:
        """Analyze customer usage patterns from metrics and historical data"""
        try:
            # Calculate revenue growth rate
            revenue_growth_rate = self._calculate_growth_rate(
                metrics.get("monthly_revenue", 0),
                historical_data
            )

            # Calculate team growth rate
            team_growth_rate = self._calculate_growth_rate(
                metrics.get("team_size", 1),
                historical_data,
                key="team_size"
            )

            # Assess incident frequency
            incident_frequency = metrics.get("critical_incidents_per_month", 0)

            # Calculate feature adoption score
            feature_adoption = self._calculate_feature_adoption(metrics)

            # Calculate business impact score
            business_impact = self._calculate_business_impact_score(metrics)

            # Determine engagement level
            engagement_level = self._determine_engagement_level(
                feature_adoption, business_impact, metrics
            )

            return UsagePattern(
                revenue_growth_rate=revenue_growth_rate,
                team_growth_rate=team_growth_rate,
                incident_frequency=incident_frequency,
                feature_adoption_score=feature_adoption,
                business_impact_score=business_impact,
                engagement_level=engagement_level
            )

        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return UsagePattern(0, 0, 0, 0, 0, "low")

    async def generate_upgrade_recommendation(
        self,
        customer_id: str,
        subscription: Subscription,
        current_metrics: Dict[str, Any],
        usage_patterns: UsagePattern
    ) -> UpgradeRecommendation:
        """Generate personalized upgrade recommendation"""
        try:
            # Get recommended tier based on current metrics
            recommended_tier = self.pricing_service.get_recommended_tier(current_metrics)

            # Skip if already on recommended tier
            if recommended_tier == subscription.tier:
                return self._create_maintenance_recommendation(customer_id, subscription, current_metrics)

            # Calculate urgency and confidence scores
            urgency_score = self._calculate_urgency_score(
                subscription.tier, recommended_tier, usage_patterns, current_metrics
            )

            confidence_score = self._calculate_confidence_score(usage_patterns, current_metrics)

            # Generate value proposition
            value_proposition = self.pricing_service.calculate_tier_value_proposition(
                recommended_tier, current_metrics
            )

            # Identify upgrade triggers
            upgrade_triggers = self.pricing_service.identify_upgrade_triggers(
                subscription, current_metrics
            )

            # Determine timeline
            timeline = self._determine_upgrade_timeline(urgency_score, usage_patterns)

            # Generate personalized message
            personalized_message = self._generate_personalized_message(
                subscription.tier, recommended_tier, usage_patterns, upgrade_triggers
            )

            # Calculate estimated ROI
            estimated_roi = value_proposition.get("annual_roi", 0)

            return UpgradeRecommendation(
                customer_id=customer_id,
                current_tier=subscription.tier,
                recommended_tier=recommended_tier,
                urgency_score=urgency_score,
                confidence_score=confidence_score,
                value_proposition=value_proposition,
                upgrade_triggers=[trigger.get("message", "") for trigger in upgrade_triggers],
                timeline_recommendation=timeline,
                personalized_message=personalized_message,
                estimated_roi=estimated_roi
            )

        except Exception as e:
            logger.error(f"Error generating upgrade recommendation: {e}")
            return self._create_default_recommendation(customer_id, subscription)

    def _calculate_growth_rate(self, current_value: float, historical_data: List[Dict[str, Any]], key: str = "monthly_revenue") -> float:
        """Calculate growth rate from historical data"""
        if not historical_data or len(historical_data) < 2:
            return 0.0

        try:
            # Get values from last 3 months for trend calculation
            recent_data = historical_data[-3:]
            if len(recent_data) < 2:
                return 0.0

            first_value = recent_data[0].get(key, 0)
            if first_value == 0:
                return 0.0

            current_comparison = recent_data[-1].get(key, current_value)
            growth_rate = ((current_comparison - first_value) / first_value) * 100

            # Cap at reasonable bounds
            return max(-100, min(200, growth_rate))

        except Exception:
            return 0.0

    def _calculate_feature_adoption(self, metrics: Dict[str, Any]) -> float:
        """Calculate feature adoption score (0-100)"""
        try:
            features_used = metrics.get("features_used", [])
            available_features = [
                "team_analytics", "custom_assessments", "advanced_reports",
                "slack_integration", "predictive_analytics", "custom_metrics"
            ]

            if not available_features:
                return 50.0  # Default middle score

            adoption_rate = (len(features_used) / len(available_features)) * 100

            # Boost score based on usage intensity
            usage_intensity = metrics.get("feature_usage_intensity", 0.5)
            adoption_score = adoption_rate * (0.7 + 0.3 * usage_intensity)

            return min(100, adoption_score)

        except Exception:
            return 0.0

    def _calculate_business_impact_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate business impact score (0-100)"""
        try:
            factors = []

            # Revenue at risk (0-30 points)
            revenue_at_risk = metrics.get("revenue_at_risk", 0)
            revenue_score = min(30, (revenue_at_risk / 10000) * 10)
            factors.append(revenue_score)

            # User satisfaction impact (0-25 points)
            nps_score = metrics.get("nps_score", 50)
            satisfaction_score = max(0, 25 - abs(nps_score - 75) / 2)
            factors.append(satisfaction_score)

            # Support ticket impact (0-20 points)
            support_tickets = metrics.get("support_ticket_count", 0)
            ticket_score = min(20, support_tickets * 2)
            factors.append(ticket_score)

            # Assessment completion impact (0-25 points)
            completion_rate = metrics.get("assessment_completion_rate", 0)
            completion_score = min(25, completion_rate / 3)
            factors.append(completion_score)

            return sum(factors)

        except Exception:
            return 0.0

    def _determine_engagement_level(self, feature_adoption: float, business_impact: float, metrics: Dict[str, Any]) -> str:
        """Determine customer engagement level"""
        combined_score = (feature_adoption + business_impact) / 2

        if combined_score >= 70:
            return "high"
        elif combined_score >= 40:
            return "medium"
        else:
            return "low"

    def _calculate_urgency_score(
        self,
        current_tier: SubscriptionTier,
        recommended_tier: SubscriptionTier,
        usage_patterns: UsagePattern,
        metrics: Dict[str, Any]
    ) -> float:
        """Calculate upgrade urgency score (0-100)"""
        try:
            urgency_factors = []

            # Tier jump urgency (0-30 points)
            tier_jump = {
                (SubscriptionTier.FREE, SubscriptionTier.GROWTH): 20,
                (SubscriptionTier.FREE, SubscriptionTier.ENTERPRISE): 30,
                (SubscriptionTier.GROWTH, SubscriptionTier.ENTERPRISE): 25
            }
            tier_urgency = tier_jump.get((current_tier, recommended_tier), 10)
            urgency_factors.append(tier_urgency)

            # Revenue at risk urgency (0-25 points)
            revenue_at_risk = metrics.get("revenue_at_risk", 0)
            revenue_urgency = min(25, (revenue_at_risk / 5000) * 5)
            urgency_factors.append(revenue_urgency)

            # Growth trajectory urgency (0-20 points)
            if usage_patterns.revenue_growth_rate > 20:
                urgency_factors.append(20)
            elif usage_patterns.team_growth_rate > 15:
                urgency_factors.append(15)
            else:
                urgency_factors.append(5)

            # Incident frequency urgency (0-15 points)
            incident_urgency = min(15, usage_patterns.incident_frequency * 3)
            urgency_factors.append(incident_urgency)

            # Feature limits urgency (0-10 points)
            approaching_limits = self._check_approaching_limits(current_tier, metrics)
            limits_urgency = approaching_limits * 10
            urgency_factors.append(limits_urgency)

            return min(100, sum(urgency_factors))

        except Exception:
            return 0.0

    def _calculate_confidence_score(self, usage_patterns: UsagePattern, metrics: Dict[str, Any]) -> float:
        """Calculate confidence in recommendation (0-100)"""
        try:
            confidence_factors = []

            # Data quality confidence (0-30 points)
            data_completeness = self._assess_data_quality(metrics)
            confidence_factors.append(data_completeness * 30)

            # Pattern consistency confidence (0-25 points)
            if usage_patterns.engagement_level == "high":
                confidence_factors.append(25)
            elif usage_patterns.engagement_level == "medium":
                confidence_factors.append(18)
            else:
                confidence_factors.append(10)

            # Growth signals confidence (0-25 points)
            if abs(usage_patterns.revenue_growth_rate) < 50:  # Stable growth
                confidence_factors.append(25)
            elif abs(usage_patterns.revenue_growth_rate) < 100:
                confidence_factors.append(15)
            else:
                confidence_factors.append(5)

            # Business impact clarity confidence (0-20 points)
            impact_clarity = min(20, usage_patterns.business_impact_score / 5)
            confidence_factors.append(impact_clarity)

            return min(100, sum(confidence_factors))

        except Exception:
            return 0.0

    def _check_approaching_limits(self, current_tier: SubscriptionTier, metrics: Dict[str, Any]) -> float:
        """Check if customer is approaching tier limits (0-1)"""
        try:
            tier_config = self.pricing_service.tiers[current_tier]
            limits = tier_config.limits

            approaching_count = 0
            total_limits = len(limits)

            for limit_key, limit_value in limits.items():
                if limit_value <= 0:  # Skip unlimited limits
                    continue

                current_usage = metrics.get(limit_key, 0)
                if current_usage > limit_value * 0.8:  # Approaching 80% limit
                    approaching_count += 1

            return approaching_count / total_limits if total_limits > 0 else 0

        except Exception:
            return 0.0

    def _assess_data_quality(self, metrics: Dict[str, Any]) -> float:
        """Assess quality of metrics data (0-1)"""
        try:
            required_fields = [
                "monthly_revenue", "team_size", "assessment_completion_rate",
                "support_ticket_count", "critical_incidents_per_month"
            ]

            present_fields = sum(1 for field in required_fields if metrics.get(field) is not None)
            return present_fields / len(required_fields)

        except Exception:
            return 0.0

    def _determine_upgrade_timeline(self, urgency_score: float, usage_patterns: UsagePattern) -> str:
        """Determine recommended upgrade timeline"""
        if urgency_score >= 80:
            return "Immediate - Critical business value at stake"
        elif urgency_score >= 60:
            return "This month - Significant ROI opportunity"
        elif urgency_score >= 40:
            return "Next 3 months - Growth preparation"
        elif usage_patterns.revenue_growth_rate > 15:
            return "Next 6 months - Scale for growth"
        else:
            return "Evaluate quarterly - Monitor usage patterns"

    def _generate_personalized_message(
        self,
        current_tier: SubscriptionTier,
        recommended_tier: SubscriptionTier,
        usage_patterns: UsagePattern,
        upgrade_triggers: List[Dict[str, Any]]
    ) -> str:
        """Generate personalized upgrade message"""
        try:
            current_config = self.pricing_service.tiers[current_tier]
            recommended_config = self.pricing_service.tiers[recommended_tier]

            # Base message on primary trigger
            if upgrade_triggers:
                primary_trigger = upgrade_triggers[0]
                if primary_trigger.get("type") == "revenue_risk":
                    return f"Protect your ${primary_trigger.get('potential_value', 0):,.0f} of at-risk revenue with advanced monitoring and predictive analytics."
                elif primary_trigger.get("type") == "team_size_limit":
                    return f"Your team is growing! Upgrade to support unlimited team members and collaboration features."
                elif primary_trigger.get("type") == "revenue_limit":
                    return f"You're outgrowing revenue tracking limits. Unlock advanced business intelligence for deeper insights."

            # Growth-focused message
            if usage_patterns.revenue_growth_rate > 20:
                return f"With {usage_patterns.revenue_growth_rate:.0f}% revenue growth, upgrade to {recommended_config.name} tier to scale your business intelligence and maintain momentum."

            # Feature-focused message
            if usage_patterns.feature_adoption_score > 70:
                return f"You're getting great value from our platform! Unlock advanced features like {recommended_config.features[2]} and {recommended_config.features[3]} to accelerate your insights."

            # Default message
            return f"Upgrade to {recommended_config.name} tier to unlock {len(recommended_config.features)} premium features and protect your growing revenue."

        except Exception:
            return f"Upgrade to {self.pricing_service.tiers[recommended_tier].name} tier to unlock advanced features and protect your business."

    def _create_maintenance_recommendation(self, customer_id: str, subscription: Subscription, metrics: Dict[str, Any]) -> UpgradeRecommendation:
        """Create recommendation for customers on optimal tier"""
        return UpgradeRecommendation(
            customer_id=customer_id,
            current_tier=subscription.tier,
            recommended_tier=subscription.tier,
            urgency_score=0,
            confidence_score=80,
            value_proposition={"monthly_value": 0, "tier_cost": 0, "monthly_roi": 0},
            upgrade_triggers=[],
            timeline_recommendation="You're on the optimal tier for your current usage",
            personalized_message="You're currently on the best tier for your usage patterns. Keep up the great work!",
            estimated_roi=0
        )

    def _create_default_recommendation(self, customer_id: str, subscription: Subscription) -> UpgradeRecommendation:
        """Create default recommendation when analysis fails"""
        return UpgradeRecommendation(
            customer_id=customer_id,
            current_tier=subscription.tier,
            recommended_tier=subscription.tier,
            urgency_score=0,
            confidence_score=0,
            value_proposition={"monthly_value": 0, "tier_cost": 0, "monthly_roi": 0},
            upgrade_triggers=[],
            timeline_recommendation="Contact us for personalized recommendation",
            personalized_message="We're analyzing your usage patterns to provide personalized recommendations.",
            estimated_roi=0
        )

# Global upgrade recommendation service
upgrade_recommendation_service = UpgradeRecommendationService(pricing_service)
