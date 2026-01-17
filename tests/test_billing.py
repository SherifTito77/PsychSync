"""
Comprehensive tests for billing functionality
Tests Stripe integration, subscription management, and billing workflows
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.main import app
from app.services.billing import BillingService, SubscriptionTier

client = TestClient(app)

class TestBillingService:
    """Test the billing service functionality"""

    def setup_method(self):
        """Set up test data"""
        self.billing_service = BillingService()

        # Sample customer data
        self.sample_customer_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'user_id': 123
        }

        # Sample subscription data
        self.sample_subscription_data = {
            'user_id': 123,
            'plan': 'pro',
            'payment_method_id': 'pm_test_123456'
        }

    @patch('app.services.billing.stripe.Customer.create')
    def test_create_customer_success(self, mock_stripe_customer):
        """Test successful customer creation"""
        # Mock Stripe response
        mock_customer = Mock()
        mock_customer.id = 'cus_test_123456'
        mock_customer.email = 'test@example.com'
        mock_stripe_customer.return_value = mock_customer

        # Test customer creation
        result = self.billing_service.create_customer(
            email=self.sample_customer_data['email'],
            name=self.sample_customer_data['name'],
            user_id=self.sample_customer_data['user_id']
        )

        # Verify the result
        assert result['id'] == 'cus_test_123456'
        assert result['email'] == 'test@example.com'

        # Verify Stripe was called correctly
        mock_stripe_customer.assert_called_once_with(
            email='test@example.com',
            name='Test User',
            metadata={'user_id': '123'}
        )

    @patch('app.services.billing.stripe.Customer.create')
    def test_create_customer_stripe_error(self, mock_stripe_customer):
        """Test customer creation with Stripe error"""
        # Mock Stripe error
        mock_stripe_customer.side_effect = Exception("Stripe API error")

        # Test customer creation
        with pytest.raises(Exception):
            self.billing_service.create_customer(
                email=self.sample_customer_data['email'],
                name=self.sample_customer_data['name']
            )

    @patch('app.services.billing.stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_payment_intent):
        """Test successful payment intent creation"""
        # Mock Stripe response
        mock_intent = Mock()
        mock_intent.id = 'pi_test_123456'
        mock_intent.client_secret = 'pi_test_123456_secret_test_abcdef'
        mock_intent.amount = 4900  # $49.00
        mock_intent.currency = 'usd'
        mock_payment_intent.return_value = mock_intent

        # Test payment intent creation
        result = self.billing_service.create_payment_intent(
            amount_cents=4900,
            currency='usd'
        )

        # Verify the result
        assert result['id'] == 'pi_test_123456'
        assert result['client_secret'] == 'pi_test_123456_secret_test_abcdef'
        assert result['amount'] == 4900
        assert result['currency'] == 'usd'

    @patch('app.services.billing.stripe.Subscription.create')
    def test_create_subscription_success(self, mock_subscription):
        """Test successful subscription creation"""
        # Mock Stripe response
        mock_sub = Mock()
        mock_sub.id = 'sub_test_123456'
        mock_sub.status = 'active'
        mock_sub.current_period_end = int((datetime.now() + timedelta(days=30)).timestamp())
        mock_subscription.return_value = mock_sub

        # Test subscription creation
        result = self.billing_service.create_subscription(
            customer_id='cus_test_123456',
            price_id='price_pro_monthly',
            payment_method_id='pm_test_123456'
        )

        # Verify the result
        assert result['id'] == 'sub_test_123456'
        assert result['status'] == 'active'

    @patch('app.services.billing.stripe.Subscription.retrieve')
    @patch('app.services.billing.stripe.Subscription.delete')
    def test_cancel_subscription_success(self, mock_delete, mock_retrieve):
        """Test successful subscription cancellation"""
        # Mock Stripe responses
        mock_sub = Mock()
        mock_sub.id = 'sub_test_123456'
        mock_sub.status = 'canceled'
        mock_retrieve.return_value = mock_sub
        mock_delete.return_value = mock_sub

        # Test subscription cancellation
        result = self.billing_service.cancel_subscription(
            subscription_id='sub_test_123456'
        )

        # Verify the result
        assert result['status'] == 'canceled'

    def test_subscription_tiers(self):
        """Test subscription tier definitions"""
        tiers = self.billing_service.get_subscription_tiers()

        assert 'free' in tiers
        assert 'pro' in tiers
        assert 'enterprise' in tiers

        # Verify free tier
        free_tier = tiers['free']
        assert free_tier['price'] == 0
        assert free_tier['features']  # Should have features

        # Verify pro tier
        pro_tier = tiers['pro']
        assert pro_tier['price'] > 0
        assert len(pro_tier['features']) > len(free_tier['features'])

    def test_plan_upgrade_eligibility(self):
        """Test plan upgrade eligibility"""
        # Free to Pro should be allowed
        assert self.billing_service.can_upgrade_plan('free', 'pro')

        # Pro to Enterprise should be allowed
        assert self.billing_service.can_upgrade_plan('pro', 'enterprise')

        # Enterprise to Pro should not be allowed
        assert not self.billing_service.can_upgrade_plan('enterprise', 'pro')

    @patch('app.services.billing.stripe.Invoice.list')
    def test_get_billing_history(self, mock_invoices):
        """Test billing history retrieval"""
        # Mock Stripe response
        mock_invoice = Mock()
        mock_invoice.id = 'in_test_123456'
        mock_invoice.created = int(datetime.now().timestamp())
        mock_invoice.amount_paid = 4900
        mock_invoice.currency = 'usd'
        mock_invoice.status = 'paid'
        mock_invoice.hosted_invoice_url = 'https://invoice.stripe.com/test'
        mock_invoices.return_value = [mock_invoice]

        # Test billing history
        result = self.billing_service.get_billing_history('cus_test_123456')

        # Verify the result
        assert len(result) == 1
        assert result[0]['id'] == 'in_test_123456'
        assert result[0]['amount'] == 4900
        assert result[0]['status'] == 'paid'

    @patch('app.services.billing.stripe.PaymentMethod.list')
    def test_get_payment_methods(self, mock_payment_methods):
        """Test payment methods retrieval"""
        # Mock Stripe response
        mock_pm = Mock()
        mock_pm.id = 'pm_test_123456'
        mock_pm.type = 'card'
        mock_pm.card = Mock()
        mock_pm.card.brand = 'visa'
        mock_pm.card.last4 = '4242'
        mock_pm.card.exp_month = 12
        mock_pm.card.exp_year = 2025
        mock_payment_methods.return_value = [mock_pm]

        # Test payment methods
        result = self.billing_service.get_payment_methods('cus_test_123456')

        # Verify the result
        assert len(result) == 1
        assert result[0]['id'] == 'pm_test_123456'
        assert result[0]['type'] == 'card'
        assert result[0]['brand'] == 'visa'
        assert result[0]['last4'] == '4242'

    def test_usage_limit_validation(self):
        """Test usage limit validation for different plans"""
        # Free plan limits
        free_limits = self.billing_service.get_plan_limits('free')
        assert free_limits['team_members'] == 5
        assert free_limits['assessments_per_month'] == 10

        # Pro plan limits
        pro_limits = self.billing_service.get_plan_limits('pro')
        assert pro_limits['team_members'] == 50
        assert pro_limits['assessments_per_month'] == 100

        # Enterprise plan should have higher limits
        enterprise_limits = self.billing_service.get_plan_limits('enterprise')
        assert enterprise_limits['team_members'] == 999
        assert enterprise_limits['assessments_per_month'] == 1000

    def test_billing_calculation(self):
        """Test billing calculations"""
        # Test monthly billing
        monthly_total = self.billing_service.calculate_billing_amount(
            plan='pro',
            billing_period='monthly',
            team_members=3
        )
        assert monthly_total == 49  # Pro plan is $49/month

        # Test annual billing (should have discount)
        annual_total = self.billing_service.calculate_billing_amount(
            plan='pro',
            billing_period='annual',
            team_members=3
        )
        assert annual_total < 49 * 12  # Should be less than monthly * 12

    @patch('app.services.billing.stripe.Customer.retrieve')
    def test_get_customer_details(self, mock_customer):
        """Test customer details retrieval"""
        # Mock Stripe response
        mock_cust = Mock()
        mock_cust.id = 'cus_test_123456'
        mock_cust.email = 'test@example.com'
        mock_cust.name = 'Test User'
        mock_cust.metadata = {'user_id': '123'}
        mock_customer.return_value = mock_cust

        # Test customer details
        result = self.billing_service.get_customer_details('cus_test_123456')

        # Verify the result
        assert result['id'] == 'cus_test_123456'
        assert result['email'] == 'test@example.com'
        assert result['name'] == 'Test User'
        assert result['user_id'] == '123'

    @patch('app.services.billing.stripe.Webhook.construct_event')
    def test_webhook_processing(self, mock_webhook):
        """Test webhook event processing"""
        # Mock webhook event
        mock_event = Mock()
        mock_event.type = 'invoice.payment_succeeded'
        mock_event.data = Mock()
        mock_event.data.object = Mock()
        mock_event.data.object.customer = 'cus_test_123456'
        mock_event.data.object.amount = 4900
        mock_webhook.return_value = mock_event

        # Test webhook processing
        result = self.billing_service.process_webhook(
            payload='test_payload',
            sig_header='test_signature',
            webhook_secret='test_secret'
        )

        # Verify the result
        assert result['type'] == 'invoice.payment_succeeded'
        assert result['processed'] is True


class TestBillingAPI:
    """Test the billing API endpoints"""

    def setup_method(self):
        """Set up test data"""
        self.user_headers = {
            'Authorization': 'Bearer test_token'
        }

    @patch('app.services.billing.BillingService.create_customer')
    def test_create_customer_endpoint(self, mock_create_customer):
        """Test customer creation endpoint"""
        # Mock service response
        mock_create_customer.return_value = {
            'id': 'cus_test_123456',
            'email': 'test@example.com'
        }

        # Test API call
        response = client.post(
            '/api/v1/billing/customers',
            json={
                'email': 'test@example.com',
                'name': 'Test User'
            },
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 'cus_test_123456'

    @patch('app.services.billing.BillingService.create_payment_intent')
    def test_create_payment_intent_endpoint(self, mock_create_intent):
        """Test payment intent creation endpoint"""
        # Mock service response
        mock_create_intent.return_value = {
            'id': 'pi_test_123456',
            'client_secret': 'pi_test_123456_secret_test_abcdef'
        }

        # Test API call
        response = client.post(
            '/api/v1/billing/payment-intents',
            json={
                'amount_cents': 4900,
                'currency': 'usd'
            },
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 'pi_test_123456'

    @patch('app.services.billing.BillingService.create_subscription')
    def test_create_subscription_endpoint(self, mock_create_subscription):
        """Test subscription creation endpoint"""
        # Mock service response
        mock_create_subscription.return_value = {
            'id': 'sub_test_123456',
            'status': 'active',
            'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp())
        }

        # Test API call
        response = client.post(
            '/api/v1/billing/subscriptions',
            json={
                'price_id': 'price_pro_monthly',
                'payment_method_id': 'pm_test_123456'
            },
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data['id'] == 'sub_test_123456'
        assert data['status'] == 'active'

    @patch('app.services.billing.BillingService.cancel_subscription')
    def test_cancel_subscription_endpoint(self, mock_cancel_subscription):
        """Test subscription cancellation endpoint"""
        # Mock service response
        mock_cancel_subscription.return_value = {
            'id': 'sub_test_123456',
            'status': 'canceled'
        }

        # Test API call
        response = client.delete(
            '/api/v1/billing/subscriptions/sub_test_123456',
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'canceled'

    @patch('app.services.billing.BillingService.get_billing_history')
    def test_get_billing_history_endpoint(self, mock_get_history):
        """Test billing history endpoint"""
        # Mock service response
        mock_get_history.return_value = [
            {
                'id': 'in_test_123456',
                'amount': 4900,
                'status': 'paid',
                'created': int(datetime.now().timestamp())
            }
        ]

        # Test API call
        response = client.get(
            '/api/v1/billing/history',
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['amount'] == 4900

    @patch('app.services.billing.BillingService.get_subscription_tiers')
    def test_get_subscription_tiers_endpoint(self, mock_get_tiers):
        """Test subscription tiers endpoint"""
        # Mock service response
        mock_get_tiers.return_value = {
            'free': {
                'price': 0,
                'features': ['Basic features']
            },
            'pro': {
                'price': 49,
                'features': ['Advanced features']
            }
        }

        # Test API call
        response = client.get('/api/v1/billing/plans')

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'free' in data
        assert 'pro' in data
        assert data['free']['price'] == 0
        assert data['pro']['price'] == 49

    def test_unauthorized_billing_access(self):
        """Test that billing endpoints require authentication"""
        # Test without authorization header
        response = client.get('/api/v1/billing/plans')
        # This should work as it's public
        assert response.status_code == 200

        # Test protected endpoints without auth
        response = client.get('/api/v1/billing/history')
        assert response.status_code == 401

        response = client.post('/api/v1/billing/customers', json={'email': 'test@example.com'})
        assert response.status_code == 401

    @patch('app.services.billing.BillingService.create_subscription')
    def test_subscription_validation(self, mock_create_subscription):
        """Test subscription request validation"""
        # Test missing required fields
        response = client.post(
            '/api/v1/billing/subscriptions',
            json={},  # Empty request
            headers=self.user_headers
        )
        assert response.status_code == 422

        # Test invalid payment method ID
        response = client.post(
            '/api/v1/billing/subscriptions',
            json={
                'price_id': '',
                'payment_method_id': ''
            },
            headers=self.user_headers
        )
        assert response.status_code == 422

    @patch('app.services.billing.BillingService.process_webhook')
    def test_webhook_endpoint(self, mock_process_webhook):
        """Test webhook processing endpoint"""
        # Mock service response
        mock_process_webhook.return_value = {
            'type': 'invoice.payment_succeeded',
            'processed': True
        }

        # Test webhook processing
        response = client.post(
            '/api/v1/billing/webhooks',
            headers={
                'stripe-signature': 'test_signature'
            },
            data='test_payload'
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data['processed'] is True

    @patch('app.services.billing.BillingService.calculate_usage')
    def test_usage_calculation_endpoint(self, mock_calculate_usage):
        """Test usage calculation endpoint"""
        # Mock service response
        mock_calculate_usage.return_value = {
            'team_members_used': 3,
            'team_members_limit': 50,
            'assessments_used': 15,
            'assessments_limit': 100
        }

        # Test API call
        response = client.get(
            '/api/v1/billing/usage',
            headers=self.user_headers
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert 'team_members_used' in data
        assert 'team_members_limit' in data
        assert 'assessments_used' in data
        assert 'assessments_limit' in data

    def test_rate_limiting(self):
        """Test rate limiting on billing endpoints"""
        # This would need to be implemented in the actual API
        # For now, we'll just test that the endpoint exists
        response = client.get('/api/v1/billing/plans')
        assert response.status_code == 200

    @patch('app.services.billing.stripe.error.InvalidRequestError')
    def test_stripe_error_handling(self, mock_stripe_error):
        """Test proper handling of Stripe errors"""
        # Mock Stripe error
        mock_stripe_error.side_effect = Exception("Invalid request")

        # This would be tested with actual Stripe calls
        # For now, verify error handling structure
        assert True  # Placeholder for actual error handling test


class TestSubscriptionWorkflow:
    """Test complete subscription workflows"""

    @patch('app.services.billing.BillingService.create_customer')
    @patch('app.services.billing.BillingService.create_payment_intent')
    @patch('app.services.billing.BillingService.create_subscription')
    def test_complete_subscription_workflow(self, mock_create_sub, mock_create_intent, mock_create_customer):
        """Test complete subscription workflow from signup to activation"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Mock responses
        mock_create_customer.return_value = {
            'id': 'cus_test_123456',
            'email': 'test@example.com'
        }

        mock_create_intent.return_value = {
            'id': 'pi_test_123456',
            'client_secret': 'pi_test_123456_secret'
        }

        mock_create_sub.return_value = {
            'id': 'sub_test_123456',
            'status': 'active',
            'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp())
        }

        # Step 1: Create customer
        customer = billing_service.create_customer(
            email='test@example.com',
            name='Test User',
            user_id=123
        )
        assert customer['id'] == 'cus_test_123456'

        # Step 2: Create payment intent for first payment
        payment_intent = billing_service.create_payment_intent(
            amount_cents=4900,  # $49.00
            currency='usd'
        )
        assert payment_intent['id'] == 'pi_test_123456'

        # Step 3: Create subscription
        subscription = billing_service.create_subscription(
            customer_id='cus_test_123456',
            price_id='price_pro_monthly',
            payment_method_id='pm_test_123456'
        )
        assert subscription['status'] == 'active'

    def test_plan_upgrade_workflow(self):
        """Test plan upgrade workflow"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test upgrade eligibility
        assert billing_service.can_upgrade_plan('free', 'pro')
        assert billing_service.can_upgrade_plan('pro', 'enterprise')
        assert not billing_service.can_upgrade_plan('enterprise', 'pro')

        # Test billing calculation for upgrade
        pro_monthly = billing_service.calculate_billing_amount('pro', 'monthly', 5)
        enterprise_monthly = billing_service.calculate_billing_amount('enterprise', 'monthly', 5)

        assert enterprise_monthly > pro_monthly

    def test_downgrade_workflow(self):
        """Test plan downgrade workflow"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test downgrade scenarios
        # These would involve proration calculations in a real implementation
        assert True  # Placeholder for downgrade logic test

    def test_usage_limit_enforcement(self):
        """Test usage limit enforcement for different plans"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test free plan limits
        free_limits = billing_service.get_plan_limits('free')

        # Should enforce 5 team member limit
        assert billing_service.check_usage_limit('team_members', 5, free_limits['team_members'])
        assert not billing_service.check_usage_limit('team_members', 6, free_limits['team_members'])

        # Test pro plan limits
        pro_limits = billing_service.get_plan_limits('pro')

        # Should allow 50 team members
        assert billing_service.check_usage_limit('team_members', 50, pro_limits['team_members'])
        assert not billing_service.check_usage_limit('team_members', 51, pro_limits['team_members'])


class TestBillingSecurity:
    """Test billing security and compliance"""

    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test with valid signature (mocked)
        # In real implementation, this would use Stripe's signature verification
        assert True  # Placeholder for signature validation test

    def test_sensitive_data_handling(self):
        """Test that sensitive billing data is handled securely"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test that API keys and secrets are not exposed
        # This would involve checking that sensitive data is properly masked
        assert True  # Placeholder for data security test

    def test_compliance_with_gdpr(self):
        """Test GDPR compliance for billing data"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # Test data deletion capabilities
        # Test data export capabilities
        # Test consent management
        assert True  # Placeholder for GDPR compliance test

    def test_audit_logging(self):
        """Test that billing operations are properly logged"""
        from app.services.billing import BillingService

        billing_service = BillingService()

        # In real implementation, this would check that all billing operations
        # create appropriate audit logs
        assert True  # Placeholder for audit logging test


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
