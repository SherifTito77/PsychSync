#!/usr/bin/env python3
"""
Subscription Management Service
Handles customer subscriptions, billing cycles, and revenue management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .pricing_service import PricingService, SubscriptionTier, BillingCycle, Subscription

logger = logging.getLogger(__name__)

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    TRIAL = "trial"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class Customer:
    """Customer information"""
    customer_id: str
    email: str
    company_name: str
    created_at: datetime
    plan_size: str  # small, medium, large, enterprise
    psychsync_app_url: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class BillingEvent:
    """Billing event for revenue tracking"""
    event_id: str
    customer_id: str
    subscription_id: str
    event_type: str  # subscription_created, payment_received, upgrade, downgrade, cancellation
    amount: float
    currency: str
    timestamp: datetime
    metadata: Dict[str, Any]

class SubscriptionService:
    """Manages customer subscriptions, billing, and revenue tracking"""

    def __init__(self, pricing_service: PricingService):
        self.pricing_service = pricing_service
        self.customers: Dict[str, Customer] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.billing_events: List[BillingEvent] = []
        self.revenue_cache: Dict[str, Any] = {}

    def create_customer(
        self,
        email: str,
        company_name: str,
        plan_size: str = "small",
        psychsync_app_url: Optional[str] = None
    ) -> Customer:
        """Create a new customer account"""
        customer_id = f"cust_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{email.split('@')[0]}"

        customer = Customer(
            customer_id=customer_id,
            email=email,
            company_name=company_name,
            created_at=datetime.now(),
            plan_size=plan_size,
            psychsync_app_url=psychsync_app_url,
            metadata={}
        )

        self.customers[customer_id] = customer
        logger.info(f"Created customer: {customer_id}")

        return customer

    def create_subscription(
        self,
        customer_id: str,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        trial_days: int = 0
    ) -> Subscription:
        """Create a new subscription for a customer"""
        if customer_id not in self.customers:
            raise ValueError(f"Customer {customer_id} not found")

        subscription_id = f"sub_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Calculate end date
        start_date = datetime.now()
        if trial_days > 0:
            end_date = start_date + timedelta(days=trial_days)
            status = SubscriptionStatus.TRIAL
        else:
            end_date = start_date + timedelta(days=30) if billing_cycle == BillingCycle.MONTHLY else start_date + timedelta(days=365)
            status = SubscriptionStatus.ACTIVE

        subscription = Subscription(
            customer_id=customer_id,
            tier=tier,
            billing_cycle=billing_cycle,
            start_date=start_date,
            end_date=end_date,
            status=status.value,
            revenue_impact=0.0,
            usage_metrics={},
            upgrade_triggers=[]
        )

        self.subscriptions[subscription_id] = subscription

        # Create billing event
        self._create_billing_event(
            subscription_id=subscription_id,
            event_type="subscription_created",
            amount=self.pricing_service.get_tier_pricing(tier, billing_cycle),
            metadata={"tier": tier.value, "billing_cycle": billing_cycle.value, "trial_days": trial_days}
        )

        logger.info(f"Created subscription: {subscription_id} for customer: {customer_id}")
        return subscription

    def upgrade_subscription(
        self,
        subscription_id: str,
        new_tier: SubscriptionTier,
        proration: bool = True
    ) -> Subscription:
        """Upgrade a subscription to a higher tier"""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription = self.subscriptions[subscription_id]
        old_tier = subscription.tier

        # Calculate prorated amount if applicable
        prorated_amount = 0.0
        if proration and old_tier != new_tier:
            prorated_amount = self._calculate_proration(subscription, new_tier)

        # Update subscription
        subscription.tier = new_tier
        subscription.status = SubscriptionStatus.ACTIVE.value

        # Create billing event
        self._create_billing_event(
            subscription_id=subscription_id,
            event_type="upgrade",
            amount=prorated_amount,
            metadata={
                "old_tier": old_tier.value,
                "new_tier": new_tier.value,
                "prorated": proration
            }
        )

        logger.info(f"Upgraded subscription {subscription_id} from {old_tier} to {new_tier}")
        return subscription

    def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "",
        immediate: bool = False
    ) -> Subscription:
        """Cancel a subscription"""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription = self.subscriptions[subscription_id]

        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.end_date = datetime.now()
        else:
            subscription.status = SubscriptionStatus.CANCELLED.value

        # Create billing event
        self._create_billing_event(
            subscription_id=subscription_id,
            event_type="cancellation",
            amount=0.0,
            metadata={"reason": reason, "immediate": immediate}
        )

        logger.info(f"Cancelled subscription {subscription_id}, reason: {reason}")
        return subscription

    def record_payment(
        self,
        subscription_id: str,
        amount: float,
        payment_method: str = "credit_card"
    ) -> BillingEvent:
        """Record a successful payment"""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription = self.subscriptions[subscription_id]

        # Update subscription status if past due
        if subscription.status == SubscriptionStatus.PAST_DUE.value:
            subscription.status = SubscriptionStatus.ACTIVE.value

        # Extend subscription end date
        if subscription.billing_cycle == BillingCycle.MONTHLY:
            subscription.end_date = subscription.end_date + timedelta(days=30)
        else:
            subscription.end_date = subscription.end_date + timedelta(days=365)

        # Create billing event
        billing_event = self._create_billing_event(
            subscription_id=subscription_id,
            event_type="payment_received",
            amount=amount,
            metadata={"payment_method": payment_method}
        )

        return billing_event

    def get_customer_subscriptions(self, customer_id: str) -> List[Subscription]:
        """Get all subscriptions for a customer"""
        return [
            sub for sub_id, sub in self.subscriptions.items()
            if sub.customer_id == customer_id
        ]

    def get_subscription_metrics(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed metrics for a subscription"""
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")

        subscription = self.subscriptions[subscription_id]
        tier_config = self.pricing_service.tiers[subscription.tier]

        # Calculate revenue metrics
        monthly_revenue = tier_config.monthly_price
        annual_revenue = monthly_revenue * 12

        # Calculate total revenue from this subscription
        subscription_events = [
            event for event in self.billing_events
            if event.subscription_id == subscription_id and event.amount > 0
        ]
        total_revenue = sum(event.amount for event in subscription_events)

        # Calculate subscription age
        subscription_age = (datetime.now() - subscription.start_date).days

        return {
            "subscription_id": subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle.value,
            "monthly_revenue": monthly_revenue,
            "annual_revenue": annual_revenue,
            "total_revenue": total_revenue,
            "subscription_age_days": subscription_age,
            "days_until_renewal": (subscription.end_date - datetime.now()).days,
            "next_billing_amount": self._calculate_next_billing_amount(subscription),
            "upgrade_eligibility": self._check_upgrade_eligibility(subscription),
            "revenue_protection_limit": tier_config.revenue_protection_limit
        }

    def get_revenue_metrics(self, time_period: str = "month") -> Dict[str, Any]:
        """Get revenue metrics for the platform"""
        try:
            # Calculate time period
            if time_period == "month":
                start_date = datetime.now().replace(day=1)
            elif time_period == "quarter":
                quarter_start = ((datetime.now().month - 1) // 3) * 3 + 1
                start_date = datetime.now().replace(month=quarter_start, day=1)
            elif time_period == "year":
                start_date = datetime.now().replace(month=1, day=1)
            else:
                start_date = datetime.now() - timedelta(days=30)

            # Filter billing events for time period
            period_events = [
                event for event in self.billing_events
                if event.timestamp >= start_date and event.amount > 0
            ]

            # Calculate revenue by tier
            revenue_by_tier = {}
            for tier in SubscriptionTier:
                tier_events = [
                    event for event in period_events
                    if self._get_event_tier(event) == tier
                ]
                revenue_by_tier[tier.value] = sum(event.amount for event in tier_events)

            # Calculate MRR and ARR
            total_mrr = sum(sub.tier_config.monthly_price for sub in self.subscriptions.values() if sub.status == SubscriptionStatus.ACTIVE.value)
            total_arr = total_mrr * 12

            # Count subscriptions by tier
            active_subscriptions = {
                tier.value: sum(1 for sub in self.subscriptions.values()
                              if sub.tier == tier and sub.status == SubscriptionStatus.ACTIVE.value)
                for tier in SubscriptionTier
            }

            # Calculate growth metrics
            growth_rate = self._calculate_growth_rate(start_date)

            return {
                "time_period": time_period,
                "total_revenue": sum(event.amount for event in period_events),
                "revenue_by_tier": revenue_by_tier,
                "mrr": total_mrr,
                "arr": total_arr,
                "active_subscriptions": active_subscriptions,
                "total_active_subscriptions": sum(active_subscriptions.values()),
                "growth_rate": growth_rate,
                "average_revenue_per_customer": total_mrr / max(1, sum(active_subscriptions.values())),
                "revenue_forecast": self._generate_revenue_forecast(active_subscriptions)
            }

        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return {"error": str(e)}

    def _calculate_proration(self, subscription: Subscription, new_tier: SubscriptionTier) -> float:
        """Calculate prorated amount for upgrade"""
        try:
            old_tier_config = self.pricing_service.tiers[subscription.tier]
            new_tier_config = self.pricing_service.tiers[new_tier]

            old_daily_rate = old_tier_config.monthly_price / 30
            new_daily_rate = new_tier_config.monthly_price / 30

            days_remaining = (subscription.end_date - datetime.now()).days
            prorated_amount = (new_daily_rate - old_daily_rate) * days_remaining

            return max(0, prorated_amount)

        except Exception as e:
            logger.error(f"Error calculating proration: {e}")
            return 0.0

    def _create_billing_event(
        self,
        subscription_id: str,
        event_type: str,
        amount: float,
        metadata: Dict[str, Any] = None
    ) -> BillingEvent:
        """Create a billing event"""
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{subscription_id[:8]}"

        billing_event = BillingEvent(
            event_id=event_id,
            customer_id=self.subscriptions[subscription_id].customer_id,
            subscription_id=subscription_id,
            event_type=event_type,
            amount=amount,
            currency="USD",
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.billing_events.append(billing_event)
        return billing_event

    def _calculate_next_billing_amount(self, subscription: Subscription) -> float:
        """Calculate next billing amount for subscription"""
        return self.pricing_service.get_tier_pricing(subscription.tier, subscription.billing_cycle)

    def _check_upgrade_eligibility(self, subscription: Subscription) -> Dict[str, Any]:
        """Check if subscription is eligible for upgrade"""
        if subscription.tier == SubscriptionTier.ENTERPRISE:
            return {"eligible": False, "reason": "Already on highest tier"}

        return {
            "eligible": True,
            "next_tier": SubscriptionTier.GROWTH if subscription.tier == SubscriptionTier.FREE else SubscriptionTier.ENTERPRISE,
            "upgrade_cost": self._calculate_upgrade_cost(subscription)
        }

    def _calculate_upgrade_cost(self, subscription: Subscription) -> Dict[str, float]:
        """Calculate cost to upgrade to next tier"""
        current_config = self.pricing_service.tiers[subscription.tier]

        if subscription.tier == SubscriptionTier.FREE:
            next_tier = SubscriptionTier.GROWTH
        elif subscription.tier == SubscriptionTier.GROWTH:
            next_tier = SubscriptionTier.ENTERPRISE
        else:
            return {"monthly": 0, "yearly": 0}

        next_config = self.pricing_service.tiers[next_tier]

        return {
            "monthly": next_config.monthly_price - current_config.monthly_price,
            "yearly": next_config.yearly_price - current_config.yearly_price
        }

    def _get_event_tier(self, event: BillingEvent) -> SubscriptionTier:
        """Get tier associated with a billing event"""
        subscription = self.subscriptions.get(event.subscription_id)
        if subscription:
            return subscription.tier
        return SubscriptionTier.FREE  # Default

    def _calculate_growth_rate(self, start_date: datetime) -> float:
        """Calculate revenue growth rate since start date"""
        try:
            # Get revenue for current period and previous period
            current_events = [e for e in self.billing_events if e.timestamp >= start_date and e.amount > 0]
            current_revenue = sum(e.amount for e in current_events)

            # Get same period length from previous period
            period_length = datetime.now() - start_date
            previous_start = start_date - period_length
            previous_end = start_date

            previous_events = [e for e in self.billing_events if previous_start <= e.timestamp < previous_end and e.amount > 0]
            previous_revenue = sum(e.amount for e in previous_events)

            if previous_revenue == 0:
                return 0.0

            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
            return round(growth_rate, 2)

        except Exception as e:
            logger.error(f"Error calculating growth rate: {e}")
            return 0.0

    def _generate_revenue_forecast(self, active_subscriptions: Dict[str, int]) -> Dict[str, Any]:
        """Generate revenue forecast based on current subscriptions"""
        try:
            # Base monthly revenue from active subscriptions
            base_mrr = 0
            for tier, count in active_subscriptions.items():
                tier_config = self.pricing_service.tiers[SubscriptionTier(tier)]
                base_mrr += count * tier_config.monthly_price

            # Apply growth assumptions
            monthly_growth_rate = 0.05  # 5% monthly growth
            forecast = []
            cumulative_revenue = 0

            for month in range(12):
                month_revenue = base_mrr * (1 + monthly_growth_rate) ** month
                cumulative_revenue += month_revenue

                forecast.append({
                    "month": month + 1,
                    "projected_mrr": month_revenue,
                    "cumulative_revenue": cumulative_revenue
                })

            return {
                "base_mrr": base_mrr,
                "annual_forecast": forecast,
                "projected_annual_revenue": cumulative_revenue,
                "growth_assumption": f"{monthly_growth_rate * 100:.1f}% monthly"
            }

        except Exception as e:
            logger.error(f"Error generating revenue forecast: {e}")
            return {"base_mrr": 0, "annual_forecast": []}

# Global subscription service
subscription_service = SubscriptionService(pricing_service)
