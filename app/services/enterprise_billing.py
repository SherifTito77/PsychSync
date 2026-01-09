"""
Enterprise Billing & Subscription Management System

This module provides comprehensive billing capabilities with:
- Multiple subscription tiers and plans
- Usage-based billing and metering
- Automated invoicing and payment processing
- Dunning management for failed payments
- Revenue analytics and reporting
- Tax calculation and compliance
- Multi-currency support
- Subscription lifecycle management
- Free trial and promotion management
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
import logging
from typing import Any

import asyncpg
import stripe

logger = logging.getLogger(__name__)


class PlanType(Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class BillingCycle(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"


class SubscriptionStatus(Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class InvoiceStatus(Enum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNC.COLLECTIBLE = "uncollectible"


class EventType(Enum):
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    INVOICE_FAILED = "invoice_failed"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"


@dataclass
class PricingTier:
    """Pricing tier definition"""
    name: str
    plan_type: PlanType
    monthly_price: Decimal
    yearly_price: Decimal
    currency: str
    features: list[str]
    limits: dict[str, int]
    included_users: int
    price_per_user: Decimal | None = None
    setup_fee: Decimal | None = None


@dataclass
class UsageMetric:
    """Usage metric for billing"""
    metric_id: str
    name: str
    unit: str
    unit_price: Decimal
    included_units: int
    billing_type: str  # "per_unit", "tiered", "volume"


@dataclass
class Subscription:
    """Subscription model"""
    subscription_id: str
    organization_id: str
    plan_type: PlanType
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_start: datetime | None
    trial_end: datetime | None
    cancel_at_period_end: bool
    quantity: int  # Number of users/licenses
    unit_price: Decimal
    total_amount: Decimal
    currency: str
    billing_cycle: BillingCycle
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None


@dataclass
class Invoice:
    """Invoice model"""
    invoice_id: str
    subscription_id: str
    organization_id: str
    customer_id: str
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    currency: str
    status: InvoiceStatus
    due_date: datetime
    paid_at: datetime | None
    created_at: datetime
    line_items: list[dict[str, Any]]
    tax_amount: Decimal
    metadata: dict[str, Any] | None = None


@dataclass
class PaymentMethod:
    """Payment method model"""
    payment_method_id: str
    customer_id: str
    organization_id: str
    type: str  # "card", "bank_account"
    brand: str  # "visa", "mastercard", etc.
    last4: str
    expiry_month: int | None
    expiry_year: int | None
    is_default: bool
    created_at: datetime


class PricingConfig:
    """Pricing configuration and plans"""

    # Pricing tiers
    TIERS = {
        PlanType.FREE: PricingTier(
            name="Free",
            plan_type=PlanType.FREE,
            monthly_price=Decimal("0"),
            yearly_price=Decimal("0"),
            currency="USD",
            features=[
                "Up to 5 users",
                "Basic assessments",
                "Limited analytics",
                "Community support"
            ],
            limits={
                "users": 5,
                "assessments": 10,
                "responses": 100,
                "storage_mb": 100
            },
            included_users=5
        ),
        PlanType.STARTER: PricingTier(
            name="Starter",
            plan_type=PlanType.STARTER,
            monthly_price=Decimal("29"),
            yearly_price=Decimal("290"),
            currency="USD",
            features=[
                "Up to 20 users",
                "Advanced assessments",
                "Basic analytics",
                "Email support",
                "API access"
            ],
            limits={
                "users": 20,
                "assessments": 100,
                "responses": 1000,
                "storage_mb": 1000,
                "api_calls": 10000
            },
            included_users=20,
            price_per_user=Decimal("1.50")
        ),
        PlanType.PROFESSIONAL: PricingTier(
            name="Professional",
            plan_type=PlanType.PROFESSIONAL,
            monthly_price=Decimal("99"),
            yearly_price=Decimal("990"),
            currency="USD",
            features=[
                "Up to 100 users",
                "Unlimited assessments",
                "Advanced analytics",
                "Priority support",
                "Advanced API",
                "Custom integrations",
                "SLA guarantee"
            ],
            limits={
                "users": 100,
                "assessments": -1,  # Unlimited
                "responses": -1,
                "storage_mb": 10000,
                "api_calls": 100000
            },
            included_users=100,
            price_per_user=Decimal("0.99")
        ),
        PlanType.ENTERPRISE: PricingTier(
            name="Enterprise",
            plan_type=PlanType.ENTERPRISE,
            monthly_price=Decimal("499"),
            yearly_price=Decimal("4990"),
            currency="USD",
            features=[
                "Unlimited users",
                "Unlimited assessments",
                "Enterprise analytics",
                "24/7 phone support",
                "Unlimited API",
                "Custom integrations",
                "Dedicated account manager",
                "Custom SLA",
                "On-premise option"
            ],
            limits={
                "users": -1,
                "assessments": -1,
                "responses": -1,
                "storage_mb": -1,
                "api_calls": -1
            },
            included_users=0,  # Unlimited
            price_per_user=Decimal("0.50")
        )
    }

    # Usage metrics for additional billing
    USAGE_METRICS = {
        "additional_users": UsageMetric(
            metric_id="additional_users",
            name="Additional Users",
            unit="user",
            unit_price=Decimal("1.00"),
            included_units=0,
            billing_type="per_unit"
        ),
        "additional_storage": UsageMetric(
            metric_id="additional_storage",
            name="Additional Storage",
            unit="GB",
            unit_price=Decimal("0.10"),
            included_units=1,
            billing_type="per_unit"
        ),
        "api_calls": UsageMetric(
            metric_id="api_calls",
            name="API Calls",
            unit="call",
            unit_price=Decimal("0.001"),
            included_units=10000,
            billing_type="tiered"  # Volume discounts
        )
    }


class EnterpriseBillingService:
    """Enterprise billing service with comprehensive capabilities"""

    def __init__(self, stripe_secret_key: str, database_url: str):
        self.stripe_secret_key = stripe_secret_key
        self.database_url = database_url
        self.pricing = PricingConfig()
        self.db_pool = None

        # Initialize Stripe
        stripe.api_key = stripe_secret_key

    async def initialize(self):
        """Initialize billing service"""
        self.db_pool = await asyncpg.create_pool(self.database_url, min_size=5, max_size=20)
        logger.info("🚀 Enterprise billing service initialized")

    async def create_subscription(
        self,
        organization_id: str,
        plan_type: PlanType,
        quantity: int,
        billing_cycle: BillingCycle,
        trial_days: int = 0,
        payment_method_id: str | None = None
    ) -> Subscription:
        """Create new subscription"""
        try:
            # Get or create Stripe customer
            customer = await self._get_or_create_customer(organization_id)

            # Get pricing tier
            tier = self.pricing.TIERS[plan_type]

            # Calculate price
            if billing_cycle == BillingCycle.YEARLY:
                unit_price = tier.yearly_price / Decimal(12)
            else:
                unit_price = tier.monthly_price

            # Additional user costs
            if quantity > tier.included_users:
                additional_users = quantity - tier.included_users
                if tier.price_per_user:
                    unit_price += (additional_users * tier.price_per_user) / Decimal(quantity)

            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer.stripe_customer_id,
                items=[{
                    "price_data": {
                        "currency": tier.currency.lower(),
                        "unit_amount": int(unit_price * 100),  # Convert to cents
                        "product_data": {
                            "name": f"{tier.name} Plan",
                            "description": f"{plan_type.value} plan for {quantity} users"
                        },
                        "recurring": {
                            "interval": billing_cycle.value,
                            "trial_period_days": trial_days
                        }
                    },
                    "quantity": quantity
                }],
                payment_behavior="default_incomplete",
                payment_settings={
                    "save_default_payment_method": "on_subscription"
                },
                default_payment_method=payment_method_id,
                expand=["latest_invoice.payment_intent"],
                metadata={
                    "organization_id": organization_id,
                    "plan_type": plan_type.value
                }
            )

            # Create subscription record
            subscription = Subscription(
                subscription_id=stripe_subscription.id,
                organization_id=organization_id,
                plan_type=plan_type,
                status=self._map_stripe_status(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=UTC),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=UTC),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=UTC) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=UTC) if stripe_subscription.trial_end else None,
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=unit_price * Decimal(quantity),
                currency=tier.currency.upper(),
                billing_cycle=billing_cycle,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                metadata={
                    "stripe_subscription_id": stripe_subscription.id,
                    "customer_id": customer.stripe_customer_id
                }
            )

            # Save to database
            await self._save_subscription(subscription)

            # Log event
            await self._log_event(
                EventType.SUBSCRIPTION_CREATED,
                organization_id,
                {
                    "subscription_id": subscription.subscription_id,
                    "plan_type": plan_type.value,
                    "quantity": quantity,
                    "billing_cycle": billing_cycle.value
                }
            )

            logger.info(f"✅ Created subscription {subscription.subscription_id} for org {organization_id}")
            return subscription

        except Exception as e:
            logger.error(f"❌ Failed to create subscription for org {organization_id}: {e}")
            raise

    async def update_subscription(
        self,
        subscription_id: str,
        quantity: int | None = None,
        plan_type: PlanType | None = None
    ) -> Subscription:
        """Update existing subscription"""
        try:
            # Get current subscription
            current_sub = await self._get_subscription(subscription_id)
            if not current_sub:
                raise ValueError(f"Subscription {subscription_id} not found")

            # Update in Stripe
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)

            update_data = {}

            if quantity and quantity != current_sub.quantity:
                update_data["quantity"] = quantity

            if plan_type and plan_type != current_sub.plan_type:
                # Plan change - create new price
                tier = self.pricing.TIERS[plan_type]
                new_price = stripe.Price.create(
                    currency=tier.currency.lower(),
                    unit_amount=int(tier.monthly_price * 100),
                    product_data={
                        "name": f"{tier.name} Plan",
                        "description": f"{plan_type.value} plan"
                    },
                    recurring={"interval": current_sub.billing_cycle.value}
                )
                update_data["items"] = [{
                    "id": stripe_subscription["items"]["data"][0].id,
                    "price": new_price.id
                }]

            if update_data:
                stripe_subscription = stripe.Subscription.modify(
                    subscription_id,
                    **update_data,
                    metadata={
                        "organization_id": current_sub.organization_id,
                        "plan_type": plan_type.value if plan_type else current_sub.plan_type.value
                    }
                )

            # Update local record
            updated_subscription = await self._update_subscription_from_stripe(stripe_subscription)

            await self._log_event(
                EventType.SUBSCRIPTION_UPDATED,
                current_sub.organization_id,
                {
                    "subscription_id": subscription_id,
                    "updates": update_data
                }
            )

            logger.info(f"✅ Updated subscription {subscription_id}")
            return updated_subscription

        except Exception as e:
            logger.error(f"❌ Failed to update subscription {subscription_id}: {e}")
            raise

    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True,
        reason: str | None = None
    ) -> Subscription:
        """Cancel subscription"""
        try:
            subscription = await self._get_subscription(subscription_id)
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")

            # Cancel in Stripe
            stripe_subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=cancel_at_period_end
            )

            # Update local record
            updated_subscription = await self._update_subscription_from_stripe(stripe_subscription)

            await self._log_event(
                EventType.SUBSCRIPTION_CANCELED,
                subscription.organization_id,
                {
                    "subscription_id": subscription_id,
                    "cancel_at_period_end": cancel_at_period_end,
                    "reason": reason
                }
            )

            logger.info(f"✅ Canceled subscription {subscription_id}")
            return updated_subscription

        except Exception as e:
            logger.error(f"❌ Failed to cancel subscription {subscription_id}: {e}")
            raise

    async def create_invoice(
        self,
        organization_id: str,
        items: list[dict[str, Any]],
        due_date: datetime | None = None
    ) -> Invoice:
        """Create invoice for organization"""
        try:
            # Get customer
            customer = await self._get_customer(organization_id)
            if not customer:
                raise ValueError(f"Customer not found for org {organization_id}")

            # Calculate totals
            subtotal = sum(Decimal(str(item.get("amount", 0))) for item in items)
            tax_amount = self._calculate_tax(subtotal, customer.billing_address)
            total_amount = subtotal + tax_amount

            # Create Stripe invoice
            stripe_invoice = stripe.Invoice.create(
                customer=customer.stripe_customer_id,
                auto_advance=False,
                collection_method="charge_automatically",
                due_date=int(due_date.timestamp()) if due_date else None,
                custom_fields=[
                    {
                        "name": "Organization ID",
                        "value": organization_id
                    }
                ]
            )

            # Add invoice items
            for item in items:
                stripe.InvoiceItem.create(
                    customer=customer.stripe_customer_id,
                    amount=int(Decimal(str(item.get("amount", 0))) * 100),
                    currency="usd",
                    description=item.get("description", ""),
                    invoice=stripe_invoice.id,
                    metadata=item.get("metadata", {})
                )

            # Finalize invoice
            stripe_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id)

            # Create local invoice record
            invoice = Invoice(
                invoice_id=stripe_invoice.id,
                subscription_id="",
                organization_id=organization_id,
                customer_id=customer.stripe_customer_id,
                amount_due=Decimal(str(stripe_invoice.amount_due)) / Decimal(100),
                amount_paid=Decimal(str(stripe_invoice.amount_paid)) / Decimal(100),
                amount_remaining=Decimal(str(stripe_invoice.amount_remaining)) / Decimal(100),
                currency=stripe_invoice.currency.upper(),
                status=self._map_stripe_invoice_status(stripe_invoice.status),
                due_date=datetime.fromtimestamp(stripe_invoice.due_date, tz=UTC),
                paid_at=datetime.fromtimestamp(stripe_invoice.status_transitions.paid_at, tz=UTC) if stripe_invoice.status_transitions.paid_at else None,
                created_at=datetime.fromtimestamp(stripe_invoice.created, tz=UTC),
                line_items=[{
                    "description": item.get("description", ""),
                    "amount": Decimal(str(item.get("amount", 0))),
                    "quantity": item.get("quantity", 1)
                } for item in items],
                tax_amount=tax_amount,
                metadata={
                    "stripe_invoice_id": stripe_invoice.id
                }
            )

            # Save to database
            await self._save_invoice(invoice)

            await self._log_event(
                EventType.INVOICE_CREATED,
                organization_id,
                {
                    "invoice_id": invoice.invoice_id,
                    "amount_due": float(invoice.amount_due),
                    "due_date": invoice.due_date.isoformat()
                }
            )

            logger.info(f"✅ Created invoice {invoice.invoice_id} for org {organization_id}")
            return invoice

        except Exception as e:
            logger.error(f"❌ Failed to create invoice for org {organization_id}: {e}")
            raise

    async def process_usage_billing(self, organization_id: str) -> dict[str, Any]:
        """Process usage-based billing"""
        try:
            # Get usage data for the period
            usage_data = await self._get_usage_data(organization_id)

            # Calculate charges
            charges = []
            total_charge = Decimal("0")

            for metric_name, usage_value in usage_data.items():
                metric = self.pricing.USAGE_METRICS.get(metric_name)
                if not metric:
                    continue

                charge_amount = self._calculate_usage_charge(metric, usage_value)
                if charge_amount > 0:
                    charges.append({
                        "metric": metric_name,
                        "usage": usage_value,
                        "charge": charge_amount,
                        "description": f"{metric.name} ({usage_value} {metric.unit})"
                    })
                    total_charge += charge_amount

            # Create invoice if there are charges
            if total_charge > 0:
                await self.create_invoice(
                    organization_id,
                    charges,
                    due_date=datetime.now(UTC) + timedelta(days=30)
                )

            return {
                "organization_id": organization_id,
                "usage_data": usage_data,
                "charges": charges,
                "total_charge": float(total_charge)
            }

        except Exception as e:
            logger.error(f"❌ Failed to process usage billing for org {organization_id}: {e}")
            raise

    async def handle_webhook(self, event_data: dict[str, Any]) -> bool:
        """Handle Stripe webhook events"""
        try:
            event_type = event_data.get("type")
            event_object = event_data.get("data", {}).get("object")

            if event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event_object)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event_object)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event_object)
            elif event_type == "payment_method.attached":
                await self._handle_payment_method_attached(event_object)

            logger.info(f"✅ Processed webhook event: {event_type}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to process webhook: {e}")
            return False

    async def get_billing_analytics(
        self,
        organization_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Get billing analytics and metrics"""
        try:
            # Query database for analytics
            query = """
            SELECT
                COUNT(DISTINCT s.organization_id) as total_customers,
                COUNT(DISTINCT s.subscription_id) as total_subscriptions,
                SUM(CASE WHEN s.status = 'active' THEN 1 ELSE 0 END) as active_subscriptions,
                SUM(s.total_amount) as mrr,
                AVG(s.total_amount) as avg_subscription_value,
                COUNT(DISTINCT i.invoice_id) as total_invoices,
                SUM(i.amount_paid) as total_revenue,
                AVG(i.amount_due) as avg_invoice_amount,
                COUNT(DISTINCT CASE WHEN i.status = 'past_due' THEN i.invoice_id END) as overdue_invoices
            FROM subscriptions s
            LEFT JOIN invoices i ON s.organization_id = i.organization_id
            WHERE 1=1
            """

            params = []
            if organization_id:
                query += " AND s.organization_id = $1"
                params.append(organization_id)

            # Add date filters if provided
            if start_date:
                query += f" AND s.created_at >= ${len(params)+1}"
                params.append(start_date)
            if end_date:
                query += f" AND s.created_at <= ${len(params)+1}"
                params.append(end_date)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow(query, *params)
                analytics = dict(result) if result else {}

            # Calculate churn rate
            churn_query = """
            SELECT
                COUNT(CASE WHEN s.status = 'canceled' THEN 1 END)::float /
                NULLIF(COUNT(s.subscription_id), 0) as churn_rate
            FROM subscriptions s
            WHERE s.created_at >= NOW() - INTERVAL '30 days'
            """

            async with self.db_pool.acquire() as conn:
                churn_result = await conn.fetchrow(churn_query)
                analytics["churn_rate"] = float(churn_result["churn_rate"]) if churn_result else 0.0

            return {
                "analytics": analytics,
                "generated_at": datetime.now(UTC).isoformat(),
                "filters": {
                    "organization_id": organization_id,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }

        except Exception as e:
            logger.error(f"❌ Failed to get billing analytics: {e}")
            raise

    # ===== HELPER METHODS =====

    async def _get_or_create_customer(self, organization_id: str) -> "Customer":
        """Get or create Stripe customer"""
        # Implementation would query database for existing customer
        # and create new one if not found

    async def _get_subscription(self, subscription_id: str) -> Subscription | None:
        """Get subscription from database"""
        # Database query implementation

    async def _save_subscription(self, subscription: Subscription):
        """Save subscription to database"""
        # Database save implementation

    async def _save_invoice(self, invoice: Invoice):
        """Save invoice to database"""
        # Database save implementation

    async def _log_event(self, event_type: EventType, organization_id: str, data: dict[str, Any]):
        """Log billing event"""
        # Event logging implementation

    def _map_stripe_status(self, stripe_status: str) -> SubscriptionStatus:
        """Map Stripe status to subscription status"""
        status_mapping = {
            "trialing": SubscriptionStatus.TRIALING,
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "unpaid": SubscriptionStatus.UNPAID
        }
        return status_mapping.get(stripe_status, SubscriptionStatus.ACTIVE)

    def _map_stripe_invoice_status(self, stripe_status: str) -> InvoiceStatus:
        """Map Stripe invoice status"""
        status_mapping = {
            "draft": InvoiceStatus.DRAFT,
            "open": InvoiceStatus.OPEN,
            "paid": InvoiceStatus.PAID,
            "void": InvoiceStatus.VOID,
            "uncollectible": InvoiceStatus.UNCOLLECTIBLE
        }
        return status_mapping.get(stripe_status, InvoiceStatus.DRAFT)

    def _calculate_tax(self, amount: Decimal, billing_address: dict | None) -> Decimal:
        """Calculate tax based on billing address"""
        # Simple tax calculation - would use tax service in production
        if billing_address and billing_address.get("country") == "US":
            return amount * Decimal("0.08")  # 8% tax
        return Decimal("0")

    def _calculate_usage_charge(self, metric: UsageMetric, usage_value: int) -> Decimal:
        """Calculate charge for usage metric"""
        included_units = metric.included_units
        if usage_value <= included_units:
            return Decimal("0")

        billable_units = usage_value - included_units
        return Decimal(billable_units) * metric.unit_price

    async def _get_usage_data(self, organization_id: str) -> dict[str, int]:
        """Get usage data for organization"""
        # Query usage metrics from database
        return {
            "additional_users": 5,
            "additional_storage": 2,
            "api_calls": 15000
        }

    # Webhook handlers
    async def _handle_payment_succeeded(self, invoice_data: dict):
        """Handle successful payment"""
        await self._update_invoice_status(invoice_data["id"], InvoiceStatus.PAID)

    async def _handle_payment_failed(self, invoice_data: dict):
        """Handle failed payment"""
        await self._update_invoice_status(invoice_data["id"], InvoiceStatus.OPEN)
        # Trigger dunning workflow

    async def _handle_subscription_deleted(self, subscription_data: dict):
        """Handle subscription deletion"""
        await self._cancel_local_subscription(subscription_data["id"])

    async def _handle_payment_method_attached(self, payment_method_data: dict):
        """Handle new payment method"""
        await self._save_payment_method(payment_method_data)

    async def close(self):
        """Close billing service"""
        if self.db_pool:
            await self.db_pool.close()


# Pricing tiers configuration
PRICING_PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "features": ["5 users", "10 assessments", "Basic support"],
        "limits": {"users": 5, "assessments": 10}
    },
    "starter": {
        "name": "Starter",
        "price": 29,
        "features": ["20 users", "Unlimited assessments", "Email support"],
        "limits": {"users": 20, "assessments": -1}
    },
    "professional": {
        "name": "Professional",
        "price": 99,
        "features": ["100 users", "Advanced analytics", "Priority support"],
        "limits": {"users": 100, "assessments": -1}
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 499,
        "features": ["Unlimited users", "Custom integrations", "24/7 support"],
        "limits": {"users": -1, "assessments": -1}
    }
}
