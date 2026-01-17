#!/usr/bin/env python3
"""
Pricing and Subscription API Endpoints
REST API for pricing tiers, subscriptions, and revenue management
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl, validator
import uuid

from services.pricing_service import pricing_service, SubscriptionTier, BillingCycle
from services.subscription_service import subscription_service
from services.upgrade_recommendation_service import upgrade_recommendation_service

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CustomerRequest(BaseModel):
    email: str
    company_name: str
    plan_size: str = "small"  # small, medium, large, enterprise
    psychsync_app_url: Optional[HttpUrl] = None

class SubscriptionRequest(BaseModel):
    customer_id: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    trial_days: int = 0

class UpgradeRequest(BaseModel):
    subscription_id: str
    new_tier: SubscriptionTier
    proration: bool = True

class PaymentRequest(BaseModel):
    subscription_id: str
    amount: float
    payment_method: str = "credit_card"
    payment_token: Optional[str] = None

class MetricsRequest(BaseModel):
    monthly_revenue: float
    team_size: int
    assessment_completion_rate: float
    support_ticket_count: int
    nps_score: float
    revenue_at_risk: float
    critical_incidents_per_month: int
    features_used: List[str] = []
    feature_usage_intensity: float = 0.5

# Create router
router = APIRouter(prefix="/pricing", tags=["pricing"])

# Customer Management Endpoints

@router.post("/customers")
async def create_customer(customer_data: CustomerRequest):
    """Create a new customer account"""
    try:
        customer = subscription_service.create_customer(
            email=customer_data.email,
            company_name=customer_data.company_name,
            plan_size=customer_data.plan_size,
            psychsync_app_url=str(customer_data.psychsync_app_url) if customer_data.psychsync_app_url else None
        )

        return {
            "success": True,
            "customer_id": customer.customer_id,
            "message": "Customer created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Get customer information"""
    try:
        if customer_id not in subscription_service.customers:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer = subscription_service.customers[customer_id]
        subscriptions = subscription_service.get_customer_subscriptions(customer_id)

        return {
            "customer": {
                "customer_id": customer.customer_id,
                "email": customer.email,
                "company_name": customer.company_name,
                "created_at": customer.created_at.isoformat(),
                "plan_size": customer.plan_size,
                "psychsync_app_url": customer.psychsync_app_url
            },
            "subscriptions": [
                {
                    "subscription_id": sub.subscription_id,
                    "tier": sub.tier.value,
                    "status": sub.status,
                    "billing_cycle": sub.billing_cycle.value,
                    "start_date": sub.start_date.isoformat(),
                    "end_date": sub.end_date.isoformat()
                }
                for sub in subscriptions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to get customer")

# Subscription Management Endpoints

@router.post("/subscriptions")
async def create_subscription(subscription_data: SubscriptionRequest):
    """Create a new subscription"""
    try:
        subscription = subscription_service.create_subscription(
            customer_id=subscription_data.customer_id,
            tier=subscription_data.tier,
            billing_cycle=subscription_data.billing_cycle,
            trial_days=subscription_data.trial_days
        )

        return {
            "success": True,
            "subscription_id": subscription.subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle.value,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat(),
            "monthly_price": pricing_service.get_tier_pricing(subscription.tier, BillingCycle.MONTHLY),
            "yearly_price": pricing_service.get_tier_pricing(subscription.tier, BillingCycle.YEARLY)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")

@router.get("/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str):
    """Get subscription details and metrics"""
    try:
        metrics = subscription_service.get_subscription_metrics(subscription_id)
        return metrics

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")

@router.post("/subscriptions/{subscription_id}/upgrade")
async def upgrade_subscription(subscription_id: str, upgrade_data: UpgradeRequest):
    """Upgrade a subscription to a higher tier"""
    try:
        subscription = subscription_service.upgrade_subscription(
            subscription_id=subscription_id,
            new_tier=upgrade_data.new_tier,
            proration=upgrade_data.proration
        )

        # Get upgrade proposal details
        current_tier_config = pricing_service.tiers[subscription.tier]

        return {
            "success": True,
            "subscription_id": subscription.subscription_id,
            "new_tier": subscription.tier.value,
            "old_tier": current_tier_config.tier_id.value,
            "prorated_amount": upgrade_data.proration,
            "new_monthly_price": current_tier_config.monthly_price,
            "new_yearly_price": current_tier_config.yearly_price,
            "billing_cycle": subscription.billing_cycle.value
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")

@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, reason: str = "", immediate: bool = False):
    """Cancel a subscription"""
    try:
        subscription = subscription_service.cancel_subscription(
            subscription_id=subscription_id,
            reason=reason,
            immediate=immediate
        )

        return {
            "success": True,
            "subscription_id": subscription.subscription_id,
            "status": subscription.status,
            "end_date": subscription.end_date.isoformat(),
            "cancellation_reason": reason,
            "immediate": immediate
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

# Pricing Information Endpoints

@router.get("/pricing/tiers")
async def get_pricing_tiers():
    """Get all available pricing tiers"""
    try:
        tiers = {}
        for tier, config in pricing_service.tiers.items():
            tiers[tier.value] = {
                "name": config.name,
                "monthly_price": config.monthly_price,
                "yearly_price": config.yearly_price,
                "features": config.features,
                "limits": config.limits,
                "revenue_protection_limit": config.revenue_protection_limit,
                "support_level": config.support_level,
                "data_retention_days": config.data_retention_days,
                "team_size_limit": config.team_size_limit,
                "yearly_savings": pricing_service.calculate_yearly_savings(tier)
            }

        return {
            "tiers": tiers,
            "currency": "USD",
            "billing_cycles": ["monthly", "yearly"]
        }

    except Exception as e:
        logger.error(f"Error getting pricing tiers: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pricing tiers")

@router.post("/pricing/recommendation")
async def get_tier_recommendation(metrics: MetricsRequest):
    """Get recommended tier based on metrics"""
    try:
        # Convert Pydantic model to dict
        metrics_dict = {
            "monthly_revenue": metrics.monthly_revenue,
            "team_size": metrics.team_size,
            "assessments_per_month": metrics.support_ticket_count * 10,  # Estimate
            "support_ticket_count": metrics.support_ticket_count,
            "requires_sla_guarantee": metrics.revenue_at_risk > 50000,
            "wants_predictive_analytics": metrics.critical_incidents_per_month > 2
        }

        recommended_tier = pricing_service.get_recommended_tier(metrics_dict)
        value_prop = pricing_service.calculate_tier_value_proposition(recommended_tier, metrics_dict)

        return {
            "recommended_tier": recommended_tier.value,
            "value_proposition": value_prop,
            "reasoning": self._generate_recommendation_reasoning(recommended_tier, metrics_dict)
        }

    except Exception as e:
        logger.error(f"Error getting tier recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendation")

@router.post("/pricing/upgrade-analysis")
async def analyze_upgrade_opportunity(
    subscription_id: str,
    metrics: MetricsRequest,
    background_tasks: BackgroundTasks
):
    """Analyze upgrade opportunity and generate personalized recommendation"""
    try:
        if subscription_id not in subscription_service.subscriptions:
            raise HTTPException(status_code=404, detail="Subscription not found")

        subscription = subscription_service.subscriptions[subscription_id]

        # Convert metrics to dict
        metrics_dict = {
            "monthly_revenue": metrics.monthly_revenue,
            "team_size": metrics.team_size,
            "assessment_completion_rate": metrics.assessment_completion_rate,
            "support_ticket_count": metrics.support_ticket_count,
            "nps_score": metrics.nps_score,
            "revenue_at_risk": metrics.revenue_at_risk,
            "critical_incidents_per_month": metrics.critical_incidents_per_month,
            "features_used": metrics.features_used,
            "feature_usage_intensity": metrics.feature_usage_intensity
        }

        # Analyze usage patterns
        usage_patterns = await upgrade_recommendation_service.analyze_usage_patterns(
            subscription.customer_id, metrics_dict
        )

        # Generate upgrade recommendation
        recommendation = await upgrade_recommendation_service.generate_upgrade_recommendation(
            customer_id=subscription.customer_id,
            subscription=subscription,
            current_metrics=metrics_dict,
            usage_patterns=usage_patterns
        )

        # Generate detailed upgrade proposal
        upgrade_proposal = pricing_service.generate_upgrade_proposal(
            current_tier=recommendation.current_tier,
            target_tier=recommendation.recommended_tier,
            metrics=metrics_dict
        )

        # Track recommendation for analytics
        background_tasks.add_task(
            self._track_recommendation,
            subscription.customer_id,
            subscription_id,
            recommendation
        )

        return {
            "recommendation": {
                "current_tier": recommendation.current_tier.value,
                "recommended_tier": recommendation.recommended_tier.value,
                "urgency_score": recommendation.urgency_score,
                "confidence_score": recommendation.confidence_score,
                "timeline": recommendation.timeline_recommendation,
                "personalized_message": recommendation.personalized_message,
                "upgrade_triggers": recommendation.upgrade_triggers
            },
            "value_proposition": {
                "additional_monthly_value": upgrade_proposal["additional_monthly_value"],
                "additional_cost": upgrade_proposal["additional_cost"],
                "upgrade_roi": upgrade_proposal["upgrade_roi"],
                "payback_period_days": upgrade_proposal["payback_period_days"],
                "key_benefits": upgrade_proposal["key_benefits"]
            },
            "new_features": upgrade_proposal["new_features"],
            "upgraded_limits": upgrade_proposal["upgraded_limits"],
            "pricing_details": {
                "new_monthly_price": pricing_service.get_tier_pricing(recommendation.recommended_tier, BillingCycle.MONTHLY),
                "new_yearly_price": pricing_service.get_tier_pricing(recommendation.recommended_tier, BillingCycle.YEARLY),
                "yearly_savings": pricing_service.calculate_yearly_savings(recommendation.recommended_tier)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing upgrade opportunity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze upgrade opportunity")

# Revenue Analytics Endpoints

@router.get("/revenue/metrics")
async def get_revenue_metrics(time_period: str = Query("month", description="time period: month, quarter, year")):
    """Get revenue metrics for the platform"""
    try:
        metrics = subscription_service.get_revenue_metrics(time_period)
        return metrics

    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics")

@router.get("/revenue/forecast")
async def get_revenue_forecast():
    """Get revenue forecast based on current subscriptions"""
    try:
        revenue_metrics = subscription_service.get_revenue_metrics("month")
        return revenue_metrics.get("revenue_forecast", {})

    except Exception as e:
        logger.error(f"Error getting revenue forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue forecast")

# Helper Methods

def _generate_recommendation_reasoning(tier: SubscriptionTier, metrics: Dict[str, Any]) -> List[str]:
    """Generate reasoning for tier recommendation"""
    reasoning = []

    if tier == SubscriptionTier.ENTERPRISE:
        reasoning.append("Your scale requires enterprise-grade features and SLA guarantees")
        if metrics.get("monthly_revenue", 0) > 500000:
            reasoning.append("Revenue tracking exceeds Growth tier limits")
        if metrics.get("team_size", 0) > 50:
            reasoning.append("Team size exceeds Growth tier limits")
    elif tier == SubscriptionTier.GROWTH:
        reasoning.append("Growth tier provides advanced business intelligence for your scale")
        if metrics.get("monthly_revenue", 0) > 50000:
            reasoning.append("Revenue tracking requires advanced analytics")
        if metrics.get("team_size", 0) > 5:
            reasoning.append("Team collaboration features will be valuable")
    else:
        reasoning.append("Free tier is perfect for getting started with business intelligence")

    return reasoning

async def _track_recommendation(customer_id: str, subscription_id: str, recommendation):
    """Track upgrade recommendation for analytics"""
    try:
        # In production, this would save to analytics database
        logger.info(f"Tracking recommendation: {recommendation.recommended_tier.value} for {customer_id}")
    except Exception as e:
        logger.error(f"Error tracking recommendation: {e}")
