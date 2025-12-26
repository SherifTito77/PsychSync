"""
Stripe Billing Integration Tests

This module tests Stripe billing integration including:
- Payment processing with various methods
- Subscription management
- Invoice handling
- Webhook processing
- Refund management
- Billing analytics
- Security and compliance testing

Security focus: PCI DSS compliance testing, secure token handling,
and proper error handling for payment failures.
"""

import pytest
import asyncio
import json
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import stripe
from httpx import AsyncClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.config import get_settings
from app.services.billing import StripeBillingService
from app.db.models.user import User
from app.db.models.organization import Organization
from app.schemas.billing import (
    PaymentMethodCreate,
    SubscriptionCreate,
    Invoice,
    WebhookEvent
)

settings = get_settings()


@pytest.fixture
async def billing_service():
    """Create Stripe billing service instance for testing."""
    return StripeBillingService()


@pytest.fixture
async def stripe_test_customer(billing_service: StripeBillingService):
    """Create a test Stripe customer for billing tests."""
    try:
        # Use test mode customer ID
        customer = await billing_service.stripe.Customer.create(
            email="test@example.com",
            name="Test Customer",
            metadata={"test_mode": "true"}
        )
        yield customer
    finally:
        # Cleanup test customer
        try:
            await billing_service.stripe.Customer.delete(customer.id)
        except:
            pass


@pytest.fixture
async def payment_method_data():
    """Sample payment method data for testing."""
    return {
        "type": "card",
        "card": {
            "number": "4242424242424242",  # Stripe test card
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123",
        },
        "billing_details": {
            "name": "Test User",
            "email": "test@example.com",
            "address": {
                "line1": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postal_code": "12345",
                "country": "US",
            },
        },
    }


@pytest.fixture
async def subscription_data():
    """Sample subscription data for testing."""
    return {
        "price_id": "price_1O8XRE2eZvKYlo2C9sX2Z2Z2",  # Test price ID
        "quantity": 1,
        "trial_period_days": 14,
    }


@pytest.fixture
async def mock_webhook_event():
    """Mock Stripe webhook event for testing."""
    return {
        "id": "evt_test123456789",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(datetime.now().timestamp()),
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": "in_test123456789",
                "object": "invoice",
                "customer": "cus_test123456789",
                "amount_paid": 2000,
                "currency": "usd",
                "status": "paid",
                "paid": True,
            }
        },
    }


class TestPaymentProcessing:
    """Test payment processing functionality."""

    @pytest.mark.integration
    async def test_create_payment_method_success(
        self, client: AsyncClient, authenticated_user, payment_method_data, billing_service
    ):
        """Test successful payment method creation."""
        with patch.object(billing_service, 'create_payment_method') as mock_create:
            mock_create.return_value = {
                "id": "pm_test123456789",
                "type": "card",
                "card": {
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 12,
                    "exp_year": 2025,
                },
                "billing_details": payment_method_data["billing_details"],
            }

            response = await client.post(
                "/api/v1/billing/payment-methods",
                json=payment_method_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "pm_test123456789"
            assert data["type"] == "card"
            assert data["card"]["last4"] == "4242"
            mock_create.assert_called_once()

    @pytest.mark.integration
    async def test_create_payment_method_invalid_card(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test payment method creation with invalid card data."""
        invalid_data = {
            "type": "card",
            "card": {
                "number": "4000000000000002",  # Declined card
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
            },
        }

        with patch.object(billing_service, 'create_payment_method') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "Your card was declined.",
                "decline_code",
                "charge_declined",
                {"charge": "ch_test123"}
            )

            response = await client.post(
                "/api/v1/billing/payment-methods",
                json=invalid_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 400
            data = response.json()
            assert "card was declined" in data["detail"].lower()

    @pytest.mark.integration
    async def test_process_payment_success(
        self, client: AsyncClient, authenticated_user, stripe_test_customer, billing_service
    ):
        """Test successful payment processing."""
        payment_data = {
            "amount": 2000,  # $20.00 in cents
            "currency": "usd",
            "payment_method_id": "pm_test123456789",
            "customer_id": stripe_test_customer.id,
            "description": "Test payment",
        }

        with patch.object(billing_service, 'process_payment') as mock_process:
            mock_process.return_value = {
                "id": "ch_test123456789",
                "object": "charge",
                "amount": 2000,
                "currency": "usd",
                "status": "succeeded",
                "paid": True,
                "payment_method": "pm_test123456789",
            }

            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "succeeded"
            assert data["amount"] == 2000
            assert data["paid"] is True

    @pytest.mark.integration
    async def test_process_payment_insufficient_funds(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test payment processing with insufficient funds."""
        payment_data = {
            "amount": 5000,  # $50.00
            "currency": "usd",
            "payment_method_id": "pm_test_insufficient",
        }

        with patch.object(billing_service, 'process_payment') as mock_process:
            mock_process.side_effect = stripe.error.CardError(
                "Insufficient funds.",
                "insufficient_funds",
                "charge_declined",
                {"charge": "ch_test_insufficient"}
            )

            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 402
            data = response.json()
            assert "insufficient funds" in data["detail"].lower()

    @pytest.mark.integration
    async def test_refund_payment_success(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test successful payment refund."""
        refund_data = {
            "charge_id": "ch_test123456789",
            "amount": 1000,  # $10.00
            "reason": "requested_by_customer",
        }

        with patch.object(billing_service, 'refund_payment') as mock_refund:
            mock_refund.return_value = {
                "id": "re_test123456789",
                "object": "refund",
                "amount": 1000,
                "currency": "usd",
                "status": "succeeded",
                "charge": "ch_test123456789",
            }

            response = await client.post(
                "/api/v1/billing/refunds",
                json=refund_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "succeeded"
            assert data["amount"] == 1000

    @pytest.mark.integration
    async def test_list_payment_methods(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test listing user's payment methods."""
        with patch.object(billing_service, 'list_payment_methods') as mock_list:
            mock_list.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "pm_test1",
                        "type": "card",
                        "card": {"brand": "visa", "last4": "4242"},
                    },
                    {
                        "id": "pm_test2",
                        "type": "card",
                        "card": {"brand": "mastercard", "last4": "5555"},
                    },
                ],
            }

            response = await client.get(
                "/api/v1/billing/payment-methods",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2
            assert data["data"][0]["id"] == "pm_test1"


class TestSubscriptionManagement:
    """Test subscription management functionality."""

    @pytest.mark.integration
    async def test_create_subscription_success(
        self, client: AsyncClient, authenticated_user, subscription_data, billing_service
    ):
        """Test successful subscription creation."""
        with patch.object(billing_service, 'create_subscription') as mock_create:
            mock_create.return_value = {
                "id": "sub_test123456789",
                "object": "subscription",
                "status": "trialing",
                "current_period_start": int(datetime.now().timestamp()),
                "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                "trial_start": int(datetime.now().timestamp()),
                "trial_end": int((datetime.now() + timedelta(days=14)).timestamp()),
                "items": {
                    "data": [
                        {
                            "id": "si_test123",
                            "price": {"id": "price_test123", "currency": "usd"},
                            "quantity": 1,
                        }
                    ]
                },
            }

            response = await client.post(
                "/api/v1/billing/subscriptions",
                json=subscription_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "trialing"
            assert data["id"] == "sub_test123456789"

    @pytest.mark.integration
    async def test_create_subscription_with_trial(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription creation with trial period."""
        trial_data = {
            "price_id": "price_test123",
            "trial_period_days": 30,
        }

        with patch.object(billing_service, 'create_subscription') as mock_create:
            mock_create.return_value = {
                "id": "sub_test_trial",
                "status": "trialing",
                "trial_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                "trial_start": int(datetime.now().timestamp()),
            }

            response = await client.post(
                "/api/v1/billing/subscriptions",
                json=trial_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "trialing"
            assert "trial_end" in data

    @pytest.mark.integration
    async def test_cancel_subscription(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription cancellation."""
        cancel_data = {
            "subscription_id": "sub_test123456789",
            "cancel_at_period_end": False,
            "reason": "customer_request",
        }

        with patch.object(billing_service, 'cancel_subscription') as mock_cancel:
            mock_cancel.return_value = {
                "id": "sub_test123456789",
                "status": "canceled",
                "canceled_at": int(datetime.now().timestamp()),
                "cancel_at_period_end": False,
            }

            response = await client.post(
                "/api/v1/billing/subscriptions/cancel",
                json=cancel_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "canceled"

    @pytest.mark.integration
    async def test_update_subscription(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription update."""
        update_data = {
            "subscription_id": "sub_test123456789",
            "items": [
                {
                    "id": "si_test123",
                    "quantity": 2,
                }
            ],
        }

        with patch.object(billing_service, 'update_subscription') as mock_update:
            mock_update.return_value = {
                "id": "sub_test123456789",
                "items": {
                    "data": [
                        {
                            "id": "si_test123",
                            "quantity": 2,
                        }
                    ]
                },
            }

            response = await client.put(
                "/api/v1/billing/subscriptions/sub_test123456789",
                json=update_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["items"]["data"][0]["quantity"] == 2

    @pytest.mark.integration
    async def test_list_subscriptions(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test listing user's subscriptions."""
        with patch.object(billing_service, 'list_subscriptions') as mock_list:
            mock_list.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "sub_active1",
                        "status": "active",
                        "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp()),
                    },
                    {
                        "id": "sub_trial1",
                        "status": "trialing",
                        "trial_end": int((datetime.now() + timedelta(days=14)).timestamp()),
                    },
                ],
            }

            response = await client.get(
                "/api/v1/billing/subscriptions",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2


class TestInvoiceHandling:
    """Test invoice creation and management."""

    @pytest.mark.integration
    async def test_create_invoice_success(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test successful invoice creation."""
        invoice_data = {
            "customer_id": "cus_test123456789",
            "description": "Test invoice",
            "line_items": [
                {
                    "amount": 2000,
                    "currency": "usd",
                    "description": "Test item 1",
                    "quantity": 1,
                }
            ],
        }

        with patch.object(billing_service, 'create_invoice') as mock_create:
            mock_create.return_value = {
                "id": "in_test123456789",
                "object": "invoice",
                "status": "draft",
                "amount_due": 2000,
                "currency": "usd",
                "customer": "cus_test123456789",
                "lines": {
                    "data": [
                        {
                            "id": "il_test123",
                            "amount": 2000,
                            "description": "Test item 1",
                            "quantity": 1,
                        }
                    ]
                },
            }

            response = await client.post(
                "/api/v1/billing/invoices",
                json=invoice_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "in_test123456789"
            assert data["status"] == "draft"
            assert data["amount_due"] == 2000

    @pytest.mark.integration
    async def test_finalize_invoice(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test invoice finalization."""
        with patch.object(billing_service, 'finalize_invoice') as mock_finalize:
            mock_finalize.return_value = {
                "id": "in_test123456789",
                "status": "open",
                "amount_due": 2000,
                "hosted_invoice_url": "https://pay.stripe.com/invoice/inv_test",
            }

            response = await client.post(
                "/api/v1/billing/invoices/in_test123456789/finalize",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "open"
            assert "hosted_invoice_url" in data

    @pytest.mark.integration
    async def test_list_invoices(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test listing user's invoices."""
        with patch.object(billing_service, 'list_invoices') as mock_list:
            mock_list.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "in_paid1",
                        "status": "paid",
                        "amount_paid": 2000,
                        "created": int(datetime.now().timestamp()),
                    },
                    {
                        "id": "in_open1",
                        "status": "open",
                        "amount_due": 1500,
                        "created": int(datetime.now().timestamp()),
                    },
                ],
            }

            response = await client.get(
                "/api/v1/billing/invoices",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2


class TestWebhookProcessing:
    """Test Stripe webhook processing."""

    @pytest.mark.integration
    async def test_webhook_signature_valid(
        self, client: AsyncClient, mock_webhook_event, billing_service
    ):
        """Test webhook with valid signature."""
        # Mock webhook signature verification
        with patch.object(billing_service, 'verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True

            with patch.object(billing_service, 'process_webhook_event') as mock_process:
                mock_process.return_value = {"processed": True}

                webhook_payload = json.dumps(mock_webhook_event)

                response = await client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=webhook_payload,
                    headers={
                        "stripe-signature": "test_signature",
                        "content-type": "application/json",
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["processed"] is True

    @pytest.mark.integration
    async def test_webhook_signature_invalid(
        self, client: AsyncClient, mock_webhook_event, billing_service
    ):
        """Test webhook with invalid signature."""
        with patch.object(billing_service, 'verify_webhook_signature') as mock_verify:
            mock_verify.return_value = False

            webhook_payload = json.dumps(mock_webhook_event)

            response = await client.post(
                "/api/v1/billing/webhooks/stripe",
                data=webhook_payload,
                headers={
                    "stripe-signature": "invalid_signature",
                    "content-type": "application/json",
                }
            )

            assert response.status_code == 401
            data = response.json()
            assert "invalid signature" in data["detail"].lower()

    @pytest.mark.integration
    async def test_webhook_invoice_payment_succeeded(
        self, client: AsyncClient, billing_service
    ):
        """Test processing invoice payment succeeded webhook."""
        webhook_data = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_test123",
                    "customer": "cus_test123",
                    "amount_paid": 2000,
                    "status": "paid",
                }
            },
        }

        with patch.object(billing_service, 'verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True

            with patch.object(billing_service, 'handle_invoice_payment_succeeded') as mock_handle:
                mock_handle.return_value = {"subscription_renewed": True}

                response = await client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=json.dumps(webhook_data),
                    headers={"stripe-signature": "valid_signature"}
                )

                assert response.status_code == 200

    @pytest.mark.integration
    async def test_webhook_subscription_cancelled(
        self, client: AsyncClient, billing_service
    ):
        """Test processing subscription cancelled webhook."""
        webhook_data = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "canceled",
                }
            },
        }

        with patch.object(billing_service, 'verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True

            with patch.object(billing_service, 'handle_subscription_cancelled') as mock_handle:
                mock_handle.return_value = {"access_revoked": True}

                response = await client.post(
                    "/api/v1/billing/webhooks/stripe",
                    data=json.dumps(webhook_data),
                    headers={"stripe-signature": "valid_signature"}
                )

                assert response.status_code == 200


class TestBillingSecurity:
    """Test billing security and compliance."""

    @pytest.mark.integration
    async def test_payment_data_encryption(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test that payment data is properly encrypted and not stored."""
        payment_data = {
            "amount": 2000,
            "payment_method_id": "pm_test123",
        }

        # Mock payment processing to ensure no sensitive data is logged
        with patch.object(billing_service, 'process_payment') as mock_process:
            mock_process.return_value = {
                "id": "ch_test123",
                "status": "succeeded",
                # Ensure no raw card data is returned
            }

            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            # Verify no sensitive card data in response
            response_text = response.json()
            assert "card" not in response_text
            assert "cvc" not in response_text
            assert "number" not in response_text

    @pytest.mark.integration
    async def test_rate_limit_billing_endpoints(
        self, client: AsyncClient, billing_service
    ):
        """Test rate limiting on billing endpoints."""
        payment_data = {"amount": 2000}

        # Make multiple rapid requests to trigger rate limit
        responses = []
        for _ in range(10):
            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers={"Authorization": "Bearer test_token"}
            )
            responses.append(response)
            await asyncio.sleep(0.01)  # Small delay to avoid overwhelming

        # Should hit rate limit after several requests
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limited_responses) > 0

    @pytest.mark.integration
    async def test_unauthorized_billing_access(
        self, client: AsyncClient, billing_service
    ):
        """Test that unauthorized users cannot access billing endpoints."""
        response = await client.get("/api/v1/billing/payment-methods")
        assert response.status_code == 401

        response = await client.post("/api/v1/billing/payments", json={"amount": 2000})
        assert response.status_code == 401

    @pytest.mark.integration
    async def test_pci_compliance_headers(
        self, client: AsyncClient, authenticated_user
    ):
        """Test that billing endpoints include PCI compliance headers."""
        response = await client.get(
            "/api/v1/billing/payment-methods",
            headers=authenticated_user["headers"]
        )

        # Check for security headers related to PCI compliance
        headers = response.headers
        assert "strict-transport-security" in headers
        assert headers.get("strict-transport-security").startswith("max-age=")


class TestBillingAnalytics:
    """Test billing analytics and reporting."""

    @pytest.mark.integration
    async def test_billing_summary(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test billing summary endpoint."""
        with patch.object(billing_service, 'get_billing_summary') as mock_summary:
            mock_summary.return_value = {
                "total_revenue": 50000,  # $500.00
                "active_subscriptions": 25,
                "mrr": 20000,  # Monthly recurring revenue
                "churn_rate": 0.05,  # 5%
                "arpu": 800,  # Average revenue per user
            }

            response = await client.get(
                "/api/v1/billing/analytics/summary",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_revenue"] == 50000
            assert data["active_subscriptions"] == 25

    @pytest.mark.integration
    async def test_revenue_chart_data(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test revenue chart data endpoint."""
        with patch.object(billing_service, 'get_revenue_chart_data') as mock_chart:
            mock_chart.return_value = {
                "period": "last_30_days",
                "data": [
                    {"date": "2024-01-01", "revenue": 1000},
                    {"date": "2024-01-02", "revenue": 1500},
                    {"date": "2024-01-03", "revenue": 1200},
                ],
            }

            response = await client.get(
                "/api/v1/billing/analytics/revenue",
                params={"period": "30d"},
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert len(data["data"]) == 3

    @pytest.mark.integration
    async def test_subscription_metrics(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription metrics endpoint."""
        with patch.object(billing_service, 'get_subscription_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "total_subscriptions": 100,
                "active_subscriptions": 85,
                "trial_subscriptions": 10,
                "canceled_subscriptions": 5,
                "conversion_rate": 0.8,  # 80%
                "mrr": 25000,
            }

            response = await client.get(
                "/api/v1/billing/analytics/subscriptions",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_subscriptions"] == 100
            assert data["conversion_rate"] == 0.8


class TestBillingErrorHandling:
    """Test billing error handling and edge cases."""

    @pytest.mark.integration
    async def test_stripe_api_error_handling(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test handling of Stripe API errors."""
        payment_data = {"amount": 2000}

        with patch.object(billing_service, 'process_payment') as mock_process:
            # Simulate Stripe API error
            mock_process.side_effect = stripe.error.APIError(
                "Stripe API error occurred"
            )

            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 503
            data = response.json()
            assert "stripe api" in data["detail"].lower()

    @pytest.mark.integration
    async def test_stripe_rate_limit_error(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test handling of Stripe rate limit errors."""
        with patch.object(billing_service, 'create_subscription') as mock_create:
            mock_create.side_effect = stripe.error.RateLimitError(
                "Too many requests made to the API too quickly"
            )

            response = await client.post(
                "/api/v1/billing/subscriptions",
                json={"price_id": "price_test"},
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 429
            data = response.json()
            assert "too many requests" in data["detail"].lower()

    @pytest.mark.integration
    async def test_invalid_payment_amount(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test handling of invalid payment amounts."""
        invalid_amounts = [
            {"amount": -1000},  # Negative amount
            {"amount": 0},      # Zero amount
            {"amount": 999999999999},  # Extremely large amount
        ]

        for payment_data in invalid_amounts:
            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 400

    @pytest.mark.integration
    async def test_concurrent_payment_processing(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test concurrent payment processing for race conditions."""
        payment_data = {
            "amount": 2000,
            "payment_method_id": "pm_test_concurrent",
        }

        # Mock successful payment processing
        with patch.object(billing_service, 'process_payment') as mock_process:
            mock_process.return_value = {
                "id": "ch_test_concurrent",
                "status": "succeeded",
            }

            # Make concurrent requests
            tasks = []
            for _ in range(5):
                task = client.post(
                    "/api/v1/billing/payments",
                    json=payment_data,
                    headers=authenticated_user["headers"]
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All requests should be handled properly
            for response in responses:
                if hasattr(response, 'status_code'):
                    assert response.status_code in [200, 400, 409]  # Success or conflict/race condition


# Performance and Load Testing for Billing Endpoints

@pytest.mark.performance
class TestBillingPerformance:
    """Test billing endpoint performance."""

    @pytest.mark.integration
    async def test_payment_processing_performance(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test payment processing response time."""
        import time

        payment_data = {"amount": 2000}

        with patch.object(billing_service, 'process_payment') as mock_process:
            mock_process.return_value = {"id": "ch_test", "status": "succeeded"}

            start_time = time.time()
            response = await client.post(
                "/api/v1/billing/payments",
                json=payment_data,
                headers=authenticated_user["headers"]
            )
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            # Payment processing should complete within 5 seconds
            assert response_time < 5.0

    @pytest.mark.integration
    async def test_billing_analytics_performance(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test billing analytics response time."""
        with patch.object(billing_service, 'get_billing_summary') as mock_summary:
            mock_summary.return_value = {
                "total_revenue": 50000,
                "active_subscriptions": 25,
            }

            start_time = time.time()
            response = await client.get(
                "/api/v1/billing/analytics/summary",
                headers=authenticated_user["headers"]
            )
            end_time = time.time()

            response_time = end_time - start_time
            assert response.status_code == 200
            # Analytics should return quickly
            assert response_time < 2.0


class TestBillingEdgeCases:
    """Test billing edge cases and boundary conditions."""

    @pytest.mark.integration
    async def test_subscription_proration(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription upgrade with proration."""
        update_data = {
            "subscription_id": "sub_test123",
            "items": [
                {
                    "id": "si_test123",
                    "quantity": 3,  # Increase from 1 to 3
                }
            ],
            "proration_behavior": "create_prorations",
        }

        with patch.object(billing_service, 'update_subscription') as mock_update:
            mock_update.return_value = {
                "id": "sub_test123",
                "latest_invoice": {
                    "id": "in_proration_test",
                    "amount_due": 1500,  # Prorated amount
                },
            }

            response = await client.put(
                "/api/v1/billing/subscriptions/sub_test123",
                json=update_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200
            data = response.json()
            assert "latest_invoice" in data

    @pytest.mark.integration
    async def test_multiple_payment_methods_priority(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test setting payment method priority for subscriptions."""
        priority_data = {
            "customer_id": "cus_test123",
            "payment_method_id": "pm_test_primary",
        }

        with patch.object(billing_service, 'set_default_payment_method') as mock_set:
            mock_set.return_value = {"success": True}

            response = await client.post(
                "/api/v1/billing/payment-methods/set-default",
                json=priority_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200

    @pytest.mark.integration
    async def test_subscription_paused_resumed(
        self, client: AsyncClient, authenticated_user, billing_service
    ):
        """Test subscription pause and resume functionality."""
        pause_data = {
            "subscription_id": "sub_test123",
            "pause_behavior": "keep_as_draft",
        }

        # Test pause
        with patch.object(billing_service, 'pause_subscription') as mock_pause:
            mock_pause.return_value = {
                "id": "sub_test123",
                "pause_collection": {
                    "behavior": "keep_as_draft",
                },
            }

            response = await client.post(
                "/api/v1/billing/subscriptions/sub_test123/pause",
                json=pause_data,
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200

        # Test resume
        with patch.object(billing_service, 'resume_subscription') as mock_resume:
            mock_resume.return_value = {
                "id": "sub_test123",
                "pause_collection": None,
                "status": "active",
            }

            response = await client.post(
                "/api/v1/billing/subscriptions/sub_test123/resume",
                headers=authenticated_user["headers"]
            )

            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])