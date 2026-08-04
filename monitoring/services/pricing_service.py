#!/usr/bin/env python3
"""
PsychSync Monitor Pricing Service
Manages tiered pricing, subscriptions, and revenue optimization
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    FREE = "free"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class PricingTier:
    """Configuration for a pricing tier"""

    name: str
    tier_id: SubscriptionTier
    monthly_price: float
    yearly_price: float
    features: List[str]
    limits: Dict[str, Any]
    revenue_protection_limit: float  # Maximum revenue protection amount
    support_level: str
    data_retention_days: int
    team_size_limit: int
    business_intelligence_level: str


@dataclass
class Subscription:
    """Active subscription for a customer"""

    customer_id: str
    tier: SubscriptionTier
    billing_cycle: BillingCycle
    start_date: datetime
    end_date: datetime
    status: str  # active, cancelled, past_due
    revenue_impact: float
    usage_metrics: Dict[str, Any]
    upgrade_triggers: List[str]


class PricingService:
    """Manages pricing tiers, billing, and revenue optimization"""

    def __init__(self):
        self.tiers = self._initialize_pricing_tiers()
        self.revenue_multipliers = {
            SubscriptionTier.FREE: 0.0,
            SubscriptionTier.GROWTH: 1.5,
            SubscriptionTier.ENTERPRISE: 3.0,
        }

    def _initialize_pricing_tiers(self) -> Dict[SubscriptionTier, PricingTier]:
        """Initialize pricing tier configurations"""
        return {
            SubscriptionTier.FREE: PricingTier(
                name="Free",
                tier_id=SubscriptionTier.FREE,
                monthly_price=0.0,
                yearly_price=0.0,
                features=[
                    "Basic health monitoring",
                    "Core metrics collection",
                    "Email alerts for critical issues",
                    "30-day data retention",
                    "Community support",
                ],
                limits={
                    "monthly_revenue_tracking": 50000.0,
                    "team_members": 5,
                    "assessments_per_month": 100,
                    "alerts_per_month": 10,
                },
                revenue_protection_limit=50000.0,
                support_level="community",
                data_retention_days=30,
                team_size_limit=5,
                business_intelligence_level="basic",
            ),
            SubscriptionTier.GROWTH: PricingTier(
                name="Growth",
                tier_id=SubscriptionTier.GROWTH,
                monthly_price=99.0,
                yearly_price=990.0,  # 2 months free
                features=[
                    "Advanced PsychSync business dashboards",
                    "Revenue and user analytics",
                    "Predictive analytics (outage prevention)",
                    "Slack integration",
                    "90-day data retention",
                    "Priority support",
                    "Custom alerting rules",
                    "Team collaboration analytics",
                ],
                limits={
                    "monthly_revenue_tracking": 500000.0,
                    "team_members": 50,
                    "assessments_per_month": 1000,
                    "alerts_per_month": 100,
                },
                revenue_protection_limit=500000.0,
                support_level="priority",
                data_retention_days=90,
                team_size_limit=50,
                business_intelligence_level="advanced",
            ),
            SubscriptionTier.ENTERPRISE: PricingTier(
                name="Enterprise",
                tier_id=SubscriptionTier.ENTERPRISE,
                monthly_price=499.0,
                yearly_price=4990.0,  # 2 months free
                features=[
                    "Complete business intelligence",
                    "Custom metric collection",
                    "Advanced synthetic monitoring",
                    "Professional services setup",
                    "1-year data retention",
                    "Dedicated support",
                    "SLA guarantee",
                    "Custom integrations",
                    "Executive reporting",
                    "Revenue forecasting",
                ],
                limits={
                    "monthly_revenue_tracking": 10000000.0,  # $10M+
                    "team_members": -1,  # unlimited
                    "assessments_per_month": -1,  # unlimited
                    "alerts_per_month": -1,  # unlimited
                },
                revenue_protection_limit=10000000.0,
                support_level="dedicated",
                data_retention_days=365,
                team_size_limit=-1,  # unlimited
                business_intelligence_level="complete",
            ),
        }

    def get_tier_pricing(
        self, tier: SubscriptionTier, billing_cycle: BillingCycle
    ) -> float:
        """Get pricing for a specific tier and billing cycle"""
        tier_config = self.tiers[tier]
        if billing_cycle == BillingCycle.YEARLY:
            return tier_config.yearly_price
        return tier_config.monthly_price

    def calculate_yearly_savings(self, tier: SubscriptionTier) -> float:
        """Calculate savings for yearly billing"""
        tier_config = self.tiers[tier]
        monthly_total = tier_config.monthly_price * 12
        return monthly_total - tier_config.yearly_price

    def get_recommended_tier(self, metrics: Dict[str, Any]) -> SubscriptionTier:
        """Recommend tier based on customer metrics and usage patterns"""
        monthly_revenue = metrics.get("monthly_revenue", 0)
        team_size = metrics.get("team_size", 1)
        assessment_count = metrics.get("assessments_per_month", 0)

        # Enterprise tier triggers
        if (
            monthly_revenue > 500000
            or team_size > 50
            or assessment_count > 1000
            or metrics.get("requires_sla_guarantee", False)
        ):
            return SubscriptionTier.ENTERPRISE

        # Growth tier triggers
        if (
            monthly_revenue > 50000
            or team_size > 5
            or assessment_count > 100
            or metrics.get("wants_predictive_analytics", False)
        ):
            return SubscriptionTier.GROWTH

        return SubscriptionTier.FREE

    def calculate_tier_value_proposition(
        self, tier: SubscriptionTier, metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate value proposition for a specific tier"""
        tier_config = self.tiers[tier]

        # Calculate potential revenue protection
        revenue_protection = min(
            metrics.get("monthly_revenue", 0) * 0.25,  # 25% of monthly revenue
            tier_config.revenue_protection_limit,
        )

        # Calculate support cost savings
        support_tickets = metrics.get("support_ticket_count", 0)
        support_savings = support_tickets * 150  # $150 per ticket savings

        # Calculate productivity gains
        team_productivity_gain = (
            metrics.get("team_size", 1) * 200 * 0.3
        )  # $200/month per team member, 30% improvement

        total_monthly_value = (
            revenue_protection + support_savings + team_productivity_gain
        )
        tier_cost = self.get_tier_pricing(tier, BillingCycle.MONTHLY)

        roi = (
            (total_monthly_value - tier_cost) / tier_cost
            if tier_cost > 0
            else float("inf")
        )

        return {
            "monthly_value": total_monthly_value,
            "tier_cost": tier_cost,
            "monthly_roi": roi,
            "annual_roi": roi * 12,
            "revenue_protection": revenue_protection,
            "support_savings": support_savings,
            "productivity_gain": team_productivity_gain,
            "payback_period_days": (
                int((tier_cost / total_monthly_value) * 30)
                if total_monthly_value > 0
                else 0
            ),
        }

    def identify_upgrade_triggers(
        self, subscription: Subscription, current_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify triggers that would justify an upgrade"""
        triggers = []
        tier_config = self.tiers[subscription.tier]

        # Check revenue tracking limit
        if (
            current_metrics.get("monthly_revenue", 0)
            > tier_config.limits["monthly_revenue_tracking"] * 0.8
        ):
            triggers.append(
                {
                    "type": "revenue_limit",
                    "priority": "high",
                    "message": f"You're approaching your revenue tracking limit of ${tier_config.limits['monthly_revenue_tracking']:,.0f}/month",
                    "recommendation": "Upgrade to Growth tier to track up to $500,000/month",
                    "potential_value": current_metrics.get("monthly_revenue", 0)
                    * 0.05,  # 5% additional protection
                }
            )

        # Check team size limit
        if (
            current_metrics.get("team_size", 0)
            > tier_config.limits["team_members"] * 0.8
        ):
            triggers.append(
                {
                    "type": "team_size_limit",
                    "priority": "medium",
                    "message": f"Your team size is approaching the {tier_config.limits['team_members']} user limit",
                    "recommendation": "Upgrade to support your growing team",
                    "potential_value": (
                        current_metrics.get("team_size", 0)
                        - tier_config.limits["team_members"]
                    )
                    * 100,
                }
            )

        # Check high revenue impact (would benefit from advanced features)
        if (
            current_metrics.get("revenue_at_risk", 0) > 10000
            and subscription.tier == SubscriptionTier.FREE
        ):
            triggers.append(
                {
                    "type": "revenue_risk",
                    "priority": "high",
                    "message": f"${current_metrics.get('revenue_at_risk', 0):,.0f} of monthly revenue at risk - protect it with advanced monitoring",
                    "recommendation": "Growth tier includes predictive analytics to prevent outages",
                    "potential_value": current_metrics.get("revenue_at_risk", 0)
                    * 0.9,  # 90% of at-risk revenue
                }
            )

        # Check frequent incidents
        if current_metrics.get("critical_incidents_per_month", 0) > 2:
            triggers.append(
                {
                    "type": "incident_frequency",
                    "priority": "high",
                    "message": f"You've had {current_metrics.get('critical_incidents_per_month', 0)} incidents this month",
                    "recommendation": "Advanced monitoring can prevent 80% of incidents before they impact users",
                    "potential_value": current_metrics.get("revenue_at_risk", 0) * 0.8,
                }
            )

        return triggers

    def generate_upgrade_proposal(
        self,
        current_tier: SubscriptionTier,
        target_tier: SubscriptionTier,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate personalized upgrade proposal"""
        current_config = self.tiers[current_tier]
        target_config = self.tiers[target_tier]

        current_value = self.calculate_tier_value_proposition(current_tier, metrics)
        target_value = self.calculate_tier_value_proposition(target_tier, metrics)

        additional_monthly_value = (
            target_value["monthly_value"] - current_value["monthly_value"]
        )
        additional_cost = target_config.monthly_price - current_config.monthly_price
        upgrade_roi = (
            additional_monthly_value / additional_cost if additional_cost > 0 else 0
        )

        return {
            "current_tier": current_tier,
            "target_tier": target_tier,
            "additional_cost": additional_cost,
            "additional_monthly_value": additional_monthly_value,
            "upgrade_roi": upgrade_roi,
            "payback_period_days": (
                int((additional_cost / additional_monthly_value) * 30)
                if additional_monthly_value > 0
                else 0
            ),
            "key_benefits": [
                f"${additional_monthly_value:,.0f} additional monthly value",
                f"{upgrade_roi:.1f}x ROI on upgrade investment",
                f"Payback in {int((additional_cost / additional_monthly_value) * 30) if additional_monthly_value > 0 else 0} days",
            ],
            "new_features": target_config.features,
            "upgraded_limits": {
                "revenue_tracking": f"${target_config.limits['monthly_revenue_tracking']:,.0f}",
                "team_members": (
                    "Unlimited"
                    if target_config.limits["team_members"] == -1
                    else target_config.limits["team_members"]
                ),
                "data_retention": f"{target_config.data_retention_days} days",
            },
        }

    def calculate_revenue_forecast(
        self, subscription: Subscription, projected_growth: float = 0.1
    ) -> Dict[str, Any]:
        """Calculate 12-month revenue forecast for a subscription"""
        tier_config = self.tiers[subscription.tier]
        monthly_revenue = tier_config.monthly_price

        forecast = []
        cumulative_revenue = 0

        for month in range(12):
            # Apply growth rate (10% default)
            month_revenue = monthly_revenue * (1 + projected_growth) ** (month / 12)
            cumulative_revenue += month_revenue

            forecast.append(
                {
                    "month": month + 1,
                    "monthly_revenue": month_revenue,
                    "cumulative_revenue": cumulative_revenue,
                    "projected_growth_rate": projected_growth,
                }
            )

        return {
            "monthly_forecast": forecast,
            "total_annual_revenue": cumulative_revenue,
            "average_monthly_revenue": cumulative_revenue / 12,
            "growth_assumption": projected_growth,
        }


# Global pricing service instance
pricing_service = PricingService()
