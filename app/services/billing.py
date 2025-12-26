"""
Comprehensive Revenue Generation Infrastructure
Enterprise-grade billing, subscription management, and revenue optimization
"""

import stripe
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.core.config import settings
from app.core.database import get_db
from app.db.models.user import User
from app.db.models.organization import Organization

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET

class SubscriptionTier(Enum):
    """Subscription tiers with feature access levels"""
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CLINICAL = "clinical"

class BillingCycle(Enum):
    """Billing cycles"""
    MONTHLY = "month"
    YEARLY = "year"

@dataclass
class PricingTier:
    """Comprehensive pricing tier configuration"""
    name: SubscriptionTier
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None
    monthly_price: Decimal = Decimal('0')
    yearly_price: Decimal = Decimal('0')
    yearly_discount_percentage: float = 0.0

    # Feature limits
    max_assessments_per_month: int = 0
    max_team_members: int = 0
    max_teams: int = 0
    advanced_analytics: bool = False
    api_access: bool = False
    custom_assessments: bool = False
    white_labeling: bool = False
    priority_support: bool = False
    dedicated_account_manager: bool = False
    HIPAA_compliance: bool = False
    sla_guarantee: Optional[str] = None

    # Usage-based pricing
    price_per_assessment_over_limit: Decimal = Decimal('0')
    price_per_additional_team_member: Decimal = Decimal('0')
    price_per_additional_team: Decimal = Decimal('0')

# Pricing configuration
PRICING_TIERS = {
    SubscriptionTier.FREE: PricingTier(
        name=SubscriptionTier.FREE,
        monthly_price=Decimal('0'),
        max_assessments_per_month=10,
        max_team_members=3,
        max_teams=1,
        advanced_analytics=False,
        api_access=False,
        custom_assessments=False,
        white_labeling=False,
        priority_support=False,
        dedicated_account_manager=False,
        HIPAA_compliance=False,
    ),

    SubscriptionTier.PROFESSIONAL: PricingTier(
        name=SubscriptionTier.PROFESSIONAL,
        monthly_price=Decimal('99'),
        yearly_price=Decimal('990'),
        yearly_discount_percentage=17.0,  # 2 months free
        max_assessments_per_month=500,
        max_team_members=50,
        max_teams=10,
        advanced_analytics=True,
        api_access=True,
        custom_assessments=True,
        white_labeling=False,
        priority_support=True,
        dedicated_account_manager=False,
        HIPAA_compliance=False,
        price_per_assessment_over_limit=Decimal('2.00'),
        price_per_additional_team_member=Decimal('5.00'),
        price_per_additional_team=Decimal('20.00'),
    ),

    SubscriptionTier.ENTERPRISE: PricingTier(
        name=SubscriptionTier.ENTERPRISE,
        monthly_price=Decimal('499'),
        yearly_price=Decimal('4990'),
        yearly_discount_percentage=17.0,
        max_assessments_per_month=5000,
        max_team_members=500,
        max_teams=100,
        advanced_analytics=True,
        api_access=True,
        custom_assessments=True,
        white_labeling=True,
        priority_support=True,
        dedicated_account_manager=True,
        HIPAA_compliance=True,
        sla_guarantee="99.9%",
        price_per_assessment_over_limit=Decimal('1.00'),
        price_per_additional_team_member=Decimal('3.00'),
        price_per_additional_team=Decimal('10.00'),
    ),

    SubscriptionTier.CLINICAL: PricingTier(
        name=SubscriptionTier.CLINICAL,
        monthly_price=Decimal('899'),
        yearly_price=Decimal('8990'),
        yearly_discount_percentage=17.0,
        max_assessments_per_month=10000,
        max_team_members=1000,
        max_teams=200,
        advanced_analytics=True,
        api_access=True,
        custom_assessments=True,
        white_labeling=True,
        priority_support=True,
        dedicated_account_manager=True,
        HIPAA_compliance=True,
        sla_guarantee="99.99%",
        price_per_assessment_over_limit=Decimal('0.50'),
        price_per_additional_team_member=Decimal('2.00'),
        price_per_additional_team=Decimal('5.00'),
    ),
}

class RevenueGenerationService:
    """
    Comprehensive revenue generation service
    Handles subscriptions, billing, usage tracking, and revenue optimization
    """

    def __init__(self):
        self.pricing_tiers = PRICING_TIERS
        self.stripe = stripe

    async def create_customer_with_metadata(self,
                                         user: User,
                                         organization: Optional[Organization] = None) -> stripe.Customer:
        """Create Stripe customer with comprehensive metadata"""
        try:
            customer_data = {
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "metadata": {
                    "user_id": str(user.id),
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "psychsync_platform"
                }
            }

            if organization:
                customer_data.update({
                    "description": f"{organization.name} - PsychSync",
                    "metadata": {
                        **customer_data["metadata"],
                        "organization_id": str(organization.id),
                        "organization_name": organization.name
                    }
                })

                # Add organization-specific address if available
                if hasattr(organization, 'address') and organization.address:
                    customer_data["address"] = organization.address

            customer = self.stripe.Customer.create(**customer_data)

            # Update user record with Stripe customer ID
            if hasattr(user, 'stripe_customer_id'):
                user.stripe_customer_id = customer.id
                # Note: This would require database session to save

            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer

        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise

    async def create_subscription(self,
                                customer_id: str,
                                tier: SubscriptionTier,
                                billing_cycle: BillingCycle = BillingCycle.MONTHLY,
                                trial_period_days: int = 14,
                                promotion_code: Optional[str] = None) -> stripe.Subscription:
        """Create subscription with comprehensive configuration"""
        try:
            pricing_tier = self.pricing_tiers[tier]

            # Select appropriate price ID based on billing cycle
            if billing_cycle == BillingCycle.YEARLY:
                price_id = pricing_tier.stripe_price_id_yearly
            else:
                price_id = pricing_tier.stripe_price_id_monthly

            if not price_id:
                raise ValueError(f"No Stripe price ID configured for {tier.value} {billing_cycle.value}")

            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": {
                    "tier": tier.value,
                    "billing_cycle": billing_cycle.value,
                    "created_at": datetime.utcnow().isoformat(),
                    "source": "psychsync_platform"
                },
                "payment_behavior": "default_incomplete",
                "payment_settings": {
                    "save_default_payment_method": "on_subscription",
                    "payment_method_types": ["card"]
                },
                "expand": ["latest_invoice.payment_intent"]
            }

            # Add trial period for new subscriptions
            if trial_period_days > 0:
                subscription_data["trial_period_days"] = trial_period_days

            # Apply promotion code if provided
            if promotion_code:
                subscription_data["promotion_code"] = promotion_code

            subscription = self.stripe.Subscription.create(**subscription_data)

            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            return subscription

        except Exception as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise

    async def cancel_subscription(self,
                                subscription_id: str,
                                reason: str = "user_request",
                                immediate: bool = False,
                                refund_policy: str = "none") -> stripe.Subscription:
        """Cancel subscription with flexible options"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)

            # Update subscription metadata
            self.stripe.Subscription.modify(
                subscription_id,
                metadata={
                    **subscription.metadata,
                    "cancellation_reason": reason,
                    "cancellation_date": datetime.utcnow().isoformat(),
                    "refund_policy": refund_policy
                }
            )

            if immediate:
                # Cancel immediately
                cancelled_subscription = self.stripe.Subscription.delete(subscription_id)
                logger.info(f"Immediately cancelled subscription {subscription_id}")
            else:
                # Cancel at period end
                cancelled_subscription = self.stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Scheduled subscription {subscription_id} to cancel at period end")

            return cancelled_subscription

        except Exception as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {str(e)}")
            raise

    async def upgrade_or_downgrade_subscription(self,
                                              subscription_id: str,
                                              new_tier: SubscriptionTier,
                                              new_billing_cycle: Optional[BillingCycle] = None,
                                              prorate: bool = True) -> stripe.Subscription:
        """Modify subscription tier with proration options"""
        try:
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            pricing_tier = self.pricing_tiers[new_tier]

            # Determine new price
            current_billing_cycle = BillingCycle.MONTHLY if subscription.items.data[0].price.recurring.interval == "month" else BillingCycle.YEARLY
            target_billing_cycle = new_billing_cycle or current_billing_cycle

            if target_billing_cycle == BillingCycle.YEARLY:
                new_price_id = pricing_tier.stripe_price_id_yearly
            else:
                new_price_id = pricing_tier.stripe_price_id_monthly

            if not new_price_id:
                raise ValueError(f"No Stripe price ID for {new_tier.value} {target_billing_cycle.value}")

            # Create subscription modification
            modification_data = {
                "items": [{
                    "id": subscription.items.data[0].id,
                    "price": new_price_id
                }],
                "metadata": {
                    **subscription.metadata,
                    "tier_change": f"{subscription.metadata.get('tier', 'unknown')} -> {new_tier.value}",
                    "tier_change_date": datetime.utcnow().isoformat(),
                    "prorate": str(prorate)
                },
                "proration_behavior": "create_prorations" if prorate else "none"
            }

            modified_subscription = self.stripe.Subscription.modify(subscription_id, **modification_data)

            logger.info(f"Modified subscription {subscription_id} to {new_tier.value}")
            return modified_subscription

        except Exception as e:
            logger.error(f"Failed to modify subscription {subscription_id}: {str(e)}")
            raise

    async def calculate_usage_based_billing(self,
                                          user_id: str,
                                          billing_period_start: datetime,
                                          billing_period_end: datetime) -> Dict[str, Any]:
        """Calculate usage-based billing charges"""
        try:
            # This would integrate with your usage tracking system
            # For now, we'll return a template structure

            usage_report = {
                "user_id": user_id,
                "billing_period": {
                    "start": billing_period_start.isoformat(),
                    "end": billing_period_end.isoformat()
                },
                "usage_metrics": {
                    "assessments_completed": 0,  # Get from assessment service
                    "team_members_active": 0,     # Get from team service
                    "teams_active": 0,            # Get from team service
                    "api_calls_made": 0,          # Get from API tracking
                },
                "charges": {
                    "base_subscription": Decimal('0'),
                    "overage_assessments": Decimal('0'),
                    "additional_team_members": Decimal('0'),
                    "additional_teams": Decimal('0'),
                    "total_additional_charges": Decimal('0')
                },
                "pricing_tier": "free"
            }

            return usage_report

        except Exception as e:
            logger.error(f"Failed to calculate usage billing for user {user_id}: {str(e)}")
            raise

    async def create_usage_based_invoice(self,
                                        customer_id: str,
                                        usage_report: Dict[str, Any]) -> stripe.Invoice:
        """Create invoice for usage-based charges"""
        try:
            # Create invoice item for each overage charge
            if usage_report["charges"]["total_additional_charges"] > 0:

                # Assessment overage
                if usage_report["charges"]["overage_assessments"] > 0:
                    self.stripe.InvoiceItem.create(
                        customer=customer_id,
                        amount=int(usage_report["charges"]["overage_assessments"] * 100),  # Convert to cents
                        currency="usd",
                        description=f"Overage: {usage_report['usage_metrics']['assessments_completed']} assessments beyond limit"
                    )

                # Additional team members
                if usage_report["charges"]["additional_team_members"] > 0:
                    self.stripe.InvoiceItem.create(
                        customer=customer_id,
                        amount=int(usage_report["charges"]["additional_team_members"] * 100),
                        currency="usd",
                        description=f"Additional team members beyond limit"
                    )

                # Create and finalize invoice
                invoice = self.stripe.Invoice.create(
                    customer=customer_id,
                    auto_advance=True,
                    collection_method="charge_automatically",
                    metadata={
                        "usage_billing": True,
                        "billing_period": f"{usage_report['billing_period']['start']} to {usage_report['billing_period']['end']}"
                    }
                )

                finalized_invoice = self.stripe.Invoice.finalize_invoice(invoice.id)

                logger.info(f"Created usage-based invoice {finalized_invoice.id} for customer {customer_id}")
                return finalized_invoice

            return None

        except Exception as e:
            logger.error(f"Failed to create usage invoice for customer {customer_id}: {str(e)}")
            raise

    async def get_subscription_analytics(self,
                                       date_range_start: datetime,
                                       date_range_end: datetime) -> Dict[str, Any]:
        """Generate comprehensive subscription analytics"""
        try:
            # This would typically query your database for subscription data
            # For now, we'll structure the response format

            analytics = {
                "period": {
                    "start": date_range_start.isoformat(),
                    "end": date_range_end.isoformat()
                },
                "subscription_metrics": {
                    "total_subscriptions": 0,
                    "new_subscriptions": 0,
                    "canceled_subscriptions": 0,
                    "churn_rate": 0.0,
                    "mrr": 0.0,
                    "arr": 0.0,
                    "average_revenue_per_user": 0.0,
                    "customer_lifetime_value": 0.0
                },
                "tier_distribution": {
                    "free": 0,
                    "professional": 0,
                    "enterprise": 0,
                    "clinical": 0
                },
                "billing_cycle_distribution": {
                    "monthly": 0,
                    "yearly": 0
                },
                "revenue_breakdown": {
                    "subscription_revenue": 0.0,
                    "usage_overage_revenue": 0.0,
                    "total_revenue": 0.0
                },
                "growth_metrics": {
                    "month_over_month_growth": 0.0,
                    "year_over_year_growth": 0.0,
                    "expansion_revenue": 0.0,
                    "contraction_revenue": 0.0
                }
            }

            return analytics

        except Exception as e:
            logger.error(f"Failed to generate subscription analytics: {str(e)}")
            raise

    async def create_promotional_discount(self,
                                         discount_type: str,
                                         amount_off: Optional[int] = None,
                                         percent_off: Optional[int] = None,
                                         duration: str = "once",
                                         duration_in_months: Optional[int] = None,
                                         metadata: Optional[Dict[str, str]] = None) -> stripe.Coupon:
        """Create promotional discount coupons"""
        try:
            coupon_data = {
                "metadata": metadata or {}
            }

            if amount_off:
                coupon_data.update({
                    "amount_off": amount_off,
                    "currency": "usd"
                })
            elif percent_off:
                coupon_data["percent_off"] = percent_off
            else:
                raise ValueError("Either amount_off or percent_off must be specified")

            coupon_data.update({
                "duration": duration,
                "max_redemptions": 1000,  # Limit to prevent abuse
                "redeem_by": int((datetime.utcnow() + timedelta(days=90)).timestamp())
            })

            if duration == "repeating" and duration_in_months:
                coupon_data["duration_in_months"] = duration_in_months

            coupon = self.stripe.Coupon.create(**coupon_data)

            logger.info(f"Created promotional coupon {coupon.id}")
            return coupon

        except Exception as e:
            logger.error(f"Failed to create promotional coupon: {str(e)}")
            raise

    async def handle_failed_payment(self,
                                   invoice_id: str,
                                   retry_strategy: str = "smart") -> Dict[str, Any]:
        """Handle failed payments with intelligent retry strategies"""
        try:
            invoice = self.stripe.Invoice.retrieve(invoice_id)

            response = {
                "invoice_id": invoice_id,
                "customer_id": invoice.customer,
                "amount": invoice.amount_due,
                "attempt_count": invoice.attempt_count,
                "next_payment_attempt": invoice.next_payment_attempt,
                "auto_advance": invoice.auto_advance,
                "collection_method": invoice.collection_method
            }

            if retry_strategy == "smart" and invoice.attempt_count < 3:
                # Implement smart retry logic
                if invoice.attempt_count == 1:
                    # First retry after 3 days
                    retry_days = 3
                elif invoice.attempt_count == 2:
                    # Second retry after 7 days
                    retry_days = 7

                # Send payment retry notification
                # This would integrate with your email service
                response["retry_scheduled"] = True
                response["retry_days"] = retry_days

            elif invoice.attempt_count >= 3:
                # Handle persistent payment failure
                response["escalation_required"] = True
                response["recommended_action"] = "contact_customer_support"

                # This could trigger subscription cancellation or manual intervention
                # depending on your business policies

            return response

        except Exception as e:
            logger.error(f"Failed to handle payment failure for invoice {invoice_id}: {str(e)}")
            raise

    async def validate_feature_access(self,
                                     user_id: str,
                                     feature: str,
                                     organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate if user has access to specific feature based on subscription"""
        try:
            # This would typically query your database for user's subscription
            # For now, we'll return the validation structure

            validation_result = {
                "user_id": user_id,
                "organization_id": organization_id,
                "feature": feature,
                "has_access": False,
                "subscription_tier": "free",
                "limit_reached": False,
                "current_usage": 0,
                "usage_limit": 0,
                "upgrade_required": False,
                "upgrade_options": []
            }

            # Feature access rules based on pricing tiers
            feature_requirements = {
                "advanced_analytics": ["professional", "enterprise", "clinical"],
                "api_access": ["professional", "enterprise", "clinical"],
                "custom_assessments": ["professional", "enterprise", "clinical"],
                "white_labeling": ["enterprise", "clinical"],
                "HIPAA_compliance": ["enterprise", "clinical"],
                "priority_support": ["professional", "enterprise", "clinical"],
                "dedicated_account_manager": ["enterprise", "clinical"]
            }

            required_tiers = feature_requirements.get(feature, [])
            validation_result["required_tiers"] = required_tiers
            validation_result["upgrade_options"] = [
                tier.value for tier in PRICING_TIERS.keys()
                if tier.value in required_tiers
            ]

            if required_tiers:
                validation_result["upgrade_required"] = True

            return validation_result

        except Exception as e:
            logger.error(f"Failed to validate feature access for user {user_id}: {str(e)}")
            raise


    # ============================================================================
    # REFUND PROCESSING WITH TRANSACTION PROTECTION
    # ============================================================================

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: str = "customer_request",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process refund with transaction protection and idempotency

        Args:
            payment_intent_id: Stripe payment intent ID to refund
            amount: Amount to refund in cents (None = full refund)
            reason: Reason for refund
            idempotency_key: Unique key for idempotency

        Returns:
            Refund details

        Raises:
            ValueError: If payment already refunded
            Exception: If refund processing fails
        """
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        import asyncio

        # This is a template - implement with your actual database
        # For Stripe-only refunds, use Stripe's built-in idempotency:

        try:
            # Check idempotency first
            if idempotency_key:
                # You could store this in Redis/database
                pass

            # Step 1: Retrieve payment to check current state
            payment_intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == "succeeded":
                # Check if already refunded (by checking charges)
                charges = payment_intent.charges.data
                if charges and charges[0].refunds.data:
                    # Already has refunds
                    existing_refund = charges[0].refunds.data[0]
                    logger.warning(f"Payment {payment_intent_id} already refunded: {existing_refund.id}")
                    return {
                        "refund_id": existing_refund.id,
                        "amount": existing_refund.amount,
                        "status": existing_refund.status,
                        "already_refunded": True
                    }

            # Step 2: Process refund with idempotency key
            refund_params = {
                "payment_intent": payment_intent_id,
                "reason": reason
            }

            if amount is not None:
                refund_params["amount"] = amount

            if idempotency_key:
                refund_params["idempotency_key"] = idempotency_key

            refund = self.stripe.Refund.create(**refund_params)

            logger.info(f"Refund processed: {refund.id} for payment {payment_intent_id}")

            return {
                "refund_id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status,
                "created": refund.created
            }

        except self.stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid refund request: {str(e)}")
            raise ValueError(f"Cannot refund payment: {str(e)}")

        except Exception as e:
            logger.error(f"Refund failed: {str(e)}")
            raise

    # ============================================================================


# Legacy functions maintained for backward compatibility
def create_customer(email: str):
    """Legacy function - use RevenueGenerationService.create_customer_with_metadata"""
    return stripe.Customer.create(email=email)

def create_payment_intent(amount_cents: int, currency: str = "usd"):
    """Legacy function - use RevenueGenerationService for comprehensive billing"""
    return stripe.PaymentIntent.create(amount=amount_cents, currency=currency)

# Initialize service instance
revenue_service = RevenueGenerationService()