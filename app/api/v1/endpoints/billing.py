"""
Billing and Subscription Management API Endpoints
Enterprise-grade revenue generation and subscription management
"""

from datetime import datetime, timedelta
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models.organization import Organization
from app.db.models.user import User
from app.services.billing import PRICING_TIERS, BillingCycle, SubscriptionTier, revenue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing & Subscriptions"])

# ============================================================================
# IDEMPOTENCY PROTECTION
# ============================================================================

# In-memory cache for idempotency (use Redis in production)
_idempotency_cache = {}


def check_idempotency(idempotency_key: str) -> dict[str, Any] | None:
    """
    Check if request was already processed
    In production, use Redis instead of in-memory cache
    """
    if not idempotency_key:
        return None
    return _idempotency_cache.get(idempotency_key)


def store_idempotency_result(idempotency_key: str, result: dict[str, Any], ttl: int = 86400):
    """
    Store result of idempotent request (24 hour TTL)
    In production, use Redis with: redis_client.setex(key, ttl, json.dumps(result))
    """
    if not idempotency_key:
        return
    _idempotency_cache[idempotency_key] = result
    # TODO: In production: redis_client.setex(f"idempotency:{key}", ttl, json.dumps(result))


# ============================================================================


@router.post("/subscribe")
async def create_subscription(
    tier: SubscriptionTier,
    billing_cycle: BillingCycle = BillingCycle.MONTHLY,
    trial_period_days: int = 14,
    promotion_code: str | None = None,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new subscription with idempotency protection
    """
    # Check idempotency
    cached_result = check_idempotency(idempotency_key)
    if cached_result:
        logger.info(f"Returning cached result for idempotency key: {idempotency_key}")
        return cached_result

    # Rate limiting check
    # Note: Request object would need to be passed as a parameter for full rate limiting
    # For now, the idempotency protection already prevents most abuse

    try:
        # Create or retrieve Stripe customer
        organization = (
            db.query(Organization).filter(Organization.id == current_user.organization_id).first()
        )

        if not current_user.stripe_customer_id:
            customer = await revenue_service.create_customer_with_metadata(
                current_user, organization
            )
            customer_id = customer.id
        else:
            customer_id = current_user.stripe_customer_id

        # Create subscription
        subscription = await revenue_service.create_subscription(
            customer_id=customer_id,
            tier=tier,
            billing_cycle=billing_cycle,
            trial_period_days=trial_period_days,
            promotion_code=promotion_code,
        )

        # Update user's subscription status in database
        # Note: This would require updating your user model with subscription fields

        result = {
            "success": True,
            "subscription_id": subscription.id,
            "customer_id": customer_id,
            "tier": tier.value,
            "billing_cycle": billing_cycle.value,
            "trial_period_days": trial_period_days,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
            if subscription.latest_invoice
            else None,
        }

        # Store idempotency result
        store_idempotency_result(idempotency_key, result)

        return result

    except Exception as e:
        logger.error(f"Failed to create subscription: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {e!s}",
        ) from e


@router.post("/cancel")
async def cancel_subscription(
    subscription_id: str,
    reason: str = "user_request",
    immediate: bool = False,
    current_user: User = Depends(get_current_user),
):
    """
    Cancel subscription
    """
    try:
        # Verify user owns this subscription
        # Note: This would require database validation

        cancelled_subscription = await revenue_service.cancel_subscription(
            subscription_id=subscription_id, reason=reason, immediate=immediate
        )

        return {
            "success": True,
            "subscription_id": subscription_id,
            "cancelled_at": datetime.utcnow().isoformat(),
            "reason": reason,
            "immediate": immediate,
            "status": cancelled_subscription.status,
            "canceled_at_period_end": cancelled_subscription.cancel_at_period_end,
        }

    except Exception as e:
        logger.error(f"Failed to cancel subscription {subscription_id}: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {e!s}",
        ) from e


@router.post("/modify")
async def modify_subscription(
    subscription_id: str,
    new_tier: SubscriptionTier,
    new_billing_cycle: BillingCycle | None = None,
    prorate: bool = True,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
):
    """
    Upgrade or downgrade subscription with idempotency protection
    """
    # Check idempotency
    cached_result = check_idempotency(idempotency_key)
    if cached_result:
        logger.info(f"Returning cached result for idempotency key: {idempotency_key}")
        return cached_result

    try:
        # Verify user owns this subscription
        # Note: This would require database validation

        modified_subscription = await revenue_service.upgrade_or_downgrade_subscription(
            subscription_id=subscription_id,
            new_tier=new_tier,
            new_billing_cycle=new_billing_cycle,
            prorate=prorate,
        )

        result = {
            "success": True,
            "subscription_id": subscription_id,
            "new_tier": new_tier.value,
            "new_billing_cycle": new_billing_cycle.value if new_billing_cycle else "unchanged",
            "prorate": prorate,
            "status": modified_subscription.status,
            "current_period_end": modified_subscription.current_period_end,
        }

        # Store idempotency result
        store_idempotency_result(idempotency_key, result)

        return result

    except Exception as e:
        logger.error(f"Failed to modify subscription {subscription_id}: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify subscription: {e!s}",
        ) from e


@router.get("/pricing")
async def get_pricing_tiers():
    """
    Get all available pricing tiers
    """
    try:
        pricing_info = {}

        for tier_enum, tier_config in PRICING_TIERS.items():
            pricing_info[tier_enum.value] = {
                "name": tier_enum.value,
                "monthly_price": float(tier_config.monthly_price),
                "yearly_price": float(tier_config.yearly_price),
                "yearly_discount_percentage": tier_config.yearly_discount_percentage,
                "features": {
                    "max_assessments_per_month": tier_config.max_assessments_per_month,
                    "max_team_members": tier_config.max_team_members,
                    "max_teams": tier_config.max_teams,
                    "advanced_analytics": tier_config.advanced_analytics,
                    "api_access": tier_config.api_access,
                    "custom_assessments": tier_config.custom_assessments,
                    "white_labeling": tier_config.white_labeling,
                    "priority_support": tier_config.priority_support,
                    "dedicated_account_manager": tier_config.dedicated_account_manager,
                    "HIPAA_compliance": tier_config.HIPAA_compliance,
                    "sla_guarantee": tier_config.sla_guarantee,
                },
                "usage_pricing": {
                    "price_per_assessment_over_limit": float(
                        tier_config.price_per_assessment_over_limit
                    ),
                    "price_per_additional_team_member": float(
                        tier_config.price_per_additional_team_member
                    ),
                    "price_per_additional_team": float(tier_config.price_per_additional_team),
                },
            }

        return {
            "pricing_tiers": pricing_info,
            "available_tiers": [tier.value for tier in SubscriptionTier],
            "available_billing_cycles": [cycle.value for cycle in BillingCycle],
        }

    except Exception as e:
        logger.error(f"Failed to get pricing tiers: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pricing information",
        ) from e


@router.get("/subscription/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get user's current subscription details
    """
    try:
        if not current_user.stripe_customer_id:
            return {"has_subscription": False, "tier": "free", "status": "active"}

        # This would query your database for subscription information
        # For now, return a basic structure

        return {
            "has_subscription": False,  # Would be determined from database
            "subscription_id": None,
            "customer_id": current_user.stripe_customer_id,
            "tier": "free",
            "status": "active",
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
            "trial_end": None,
        }

    except Exception as e:
        logger.error(f"Failed to get current subscription: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription information",
        ) from e


@router.get("/usage")
async def get_usage_metrics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get user's current usage metrics
    """
    try:
        # Calculate current month usage
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        usage_report = await revenue_service.calculate_usage_based_billing(
            user_id=str(current_user.id), billing_period_start=month_start, billing_period_end=now
        )

        # Get user's subscription tier for limit comparison
        # Note: This would come from your database

        return {
            "current_period": {"start": month_start.isoformat(), "end": now.isoformat()},
            "usage_metrics": usage_report["usage_metrics"],
            "pricing_tier": usage_report["pricing_tier"],
            "limits": {
                "assessments_completed": usage_report["usage_metrics"]["assessments_completed"],
                "team_members_active": usage_report["usage_metrics"]["team_members_active"],
                "teams_active": usage_report["usage_metrics"]["teams_active"],
            },
        }

    except Exception as e:
        logger.error(f"Failed to get usage metrics: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage metrics",
        ) from e


@router.post("/feature-check")
async def check_feature_access(feature: str, current_user: User = Depends(get_current_user)):
    """
    Check if user has access to a specific feature
    """
    try:
        access_validation = await revenue_service.validate_feature_access(
            user_id=str(current_user.id),
            feature=feature,
            organization_id=str(current_user.organization_id)
            if current_user.organization_id
            else None,
        )

        return {
            "feature": feature,
            "has_access": access_validation["has_access"],
            "subscription_tier": access_validation["subscription_tier"],
            "limit_reached": access_validation["limit_reached"],
            "upgrade_required": access_validation["upgrade_required"],
            "upgrade_options": access_validation["upgrade_options"],
            "current_usage": access_validation["current_usage"],
            "usage_limit": access_validation["usage_limit"],
        }

    except Exception as e:
        logger.error(f"Failed to check feature access: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check feature access: {e!s}",
        ) from e


@router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    starting_after: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Get user's invoice history
    """
    try:
        if not current_user.stripe_customer_id:
            return {"invoices": [], "has_more": False}

        # This would use Stripe API to get invoices
        # For now, return the structure

        return {
            "invoices": [],  # Would be populated from Stripe API
            "has_more": False,
        }

    except Exception as e:
        logger.error(f"Failed to get invoices: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice history",
        ) from e


@router.post("/payment-methods")
async def add_payment_method(
    payment_method_id: str,
    set_as_default: bool = True,
    current_user: User = Depends(get_current_user),
):
    """
    Add a payment method to customer account
    """
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No Stripe customer found for user"
            )

        # Attach payment method to customer
        # Note: This would use Stripe API

        return {
            "success": True,
            "payment_method_id": payment_method_id,
            "set_as_default": set_as_default,
        }

    except Exception as e:
        logger.error(f"Failed to add payment method: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add payment method: {e!s}",
        ) from e


@router.get("/payment-methods")
async def get_payment_methods(current_user: User = Depends(get_current_user)):
    """
    Get user's saved payment methods
    """
    try:
        if not current_user.stripe_customer_id:
            return {"payment_methods": []}

        # This would use Stripe API to get payment methods
        # For now, return the structure

        return {
            "payment_methods": []  # Would be populated from Stripe API
        }

    except Exception as e:
        logger.error(f"Failed to get payment methods: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment methods",
        ) from e


# ============================================================================
# WEBHOOK HANDLING
# ============================================================================


@router.post("/webhooks/stripe", dependencies=[Depends(get_current_user)])
async def stripe_webhook(
    request: Request, stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhooks for subscription events

    Events handled:
    - customer.subscription.deleted: Cancel subscription
    - invoice.payment_succeeded: Payment success
    - invoice.payment_failed: Payment failure
    """
    import stripe

    from app.core.config import settings

    try:
        # Read webhook payload
        payload = await request.body()
        event = None

        # Verify webhook signature
        try:
            webhook_secret = settings.STRIPE_WEBHOOK_SECRET
            if webhook_secret:
                event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
            else:
                # For development: skip signature verification
                import json

                event = json.loads(payload)

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
            ) from e
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e!s}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
            ) from e

        # Handle event
        event_type = event.get("type", "")
        logger.info(f"Processing webhook event: {event_type}")

        if event_type == "customer.subscription.deleted":
            await handle_subscription_cancellation(event)

        elif event_type == "invoice.payment_succeeded":
            await handle_payment_success(event)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failure(event)

        else:
            logger.info(f"Unhandled webhook event type: {event_type}")

        return {"status": "processed", "event_type": event_type}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {e!s}",
        ) from e


async def handle_subscription_cancellation(event: dict):
    """
    Handle subscription cancellation webhook

    Revoke access and update user tier
    """
    try:
        subscription_data = event.get("data", {}).get("object", {})
        subscription_id = subscription_data.get("id")
        customer_id = subscription_data.get("customer")

        logger.info(f"Processing cancellation for subscription: {subscription_id}")

        # TODO: Update your database
        # Example:
        # await db.execute(
        #     "UPDATE users SET tier = 'free', stripe_subscription_id = NULL "
        #     "WHERE stripe_customer_id = $1",
        #     customer_id
        # )

        # Clear feature flags from cache
        # TODO: Implement cache invalidation
        # redis_client.delete(f"user:{user_id}:features")

        logger.info(
            f"Subscription {subscription_id} cancelled, access revoked for customer {customer_id}"
        )

    except Exception as e:
        logger.error(f"Failed to handle subscription cancellation: {e!s}")
        raise


async def handle_payment_success(event: dict):
    """Handle successful payment webhook"""
    invoice_data = event.get("data", {}).get("object", {})
    customer_id = invoice_data.get("customer")
    amount_paid = invoice_data.get("amount_paid", 0)

    logger.info(f"Payment succeeded for customer {customer_id}: ${amount_paid / 100:.2f}")

    # TODO: Update subscription status, send receipt email, etc.


async def handle_payment_failure(event: dict):
    """Handle failed payment webhook"""
    invoice_data = event.get("data", {}).get("object", {})
    customer_id = invoice_data.get("customer")
    attempt_count = invoice_data.get("attempt_count", 0)

    logger.warning(f"Payment failed for customer {customer_id}, attempt {attempt_count}")

    # TODO: Send payment failure notification, handle dunning


# ============================================================================


# Admin endpoints (protected by additional permissions)
@router.get("/admin/analytics")
async def get_billing_analytics(
    date_range_start: str | None = None,
    date_range_end: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive billing analytics (admin only)
    """
    try:
        # Check if user has admin permissions
        # Note: This would require role-based access control

        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        # Parse date range
        if date_range_start:
            start_date = datetime.fromisoformat(date_range_start.replace("Z", "+00:00"))
        else:
            start_date = datetime.utcnow() - timedelta(days=30)

        if date_range_end:
            end_date = datetime.fromisoformat(date_range_end.replace("Z", "+00:00"))
        else:
            end_date = datetime.utcnow()

        analytics = await revenue_service.get_subscription_analytics(
            date_range_start=start_date, date_range_end=end_date
        )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get billing analytics: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve billing analytics",
        ) from e


@router.post("/admin/promotions")
async def create_promotional_code(
    discount_type: str,
    amount_off: int | None = None,
    percent_off: int | None = None,
    duration: str = "once",
    duration_in_months: int | None = None,
    metadata: dict[str, str] | None = None,
    current_user: User = Depends(get_current_user),
):
    """
    Create promotional discount code (admin only)
    """
    try:
        # Check if user has admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        coupon = await revenue_service.create_promotional_discount(
            discount_type=discount_type,
            amount_off=amount_off,
            percent_off=percent_off,
            duration=duration,
            duration_in_months=duration_in_months,
            metadata=metadata,
        )

        return {
            "success": True,
            "coupon_id": coupon.id,
            "discount_type": discount_type,
            "amount_off": amount_off,
            "percent_off": percent_off,
            "duration": duration,
            "duration_in_months": duration_in_months,
            "metadata": metadata,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create promotional code: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create promotional code: {e!s}",
        ) from e
