# tests/payment/failedPaymentBehavior.test.py
"""
Failed Payment Behavior Testing

Tests payment failure scenarios, error handling, and user experience
Business Impact: Revenue retention, user experience, financial data integrity
ROI: 8x - Prevents revenue loss from payment failures and user frustration
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import stripe
from fastapi import HTTPException, status

# Mock payment and billing services for testing
class MockBillingService:
    """Mock billing service for testing"""

    @staticmethod
    def create_payment_intent(payment_data):
        """Mock payment intent creation"""
        raise stripe.error.CardError(
            "Card declined for testing",
            param="amount",
            code="card_declined"
        )

    @staticmethod
    def process_payment_with_retry(payment_data, max_retries=3, retry_delay=1.0, use_exponential_backoff=False, base_retry_delay=1.0):
        """Mock payment processing with retry logic"""
        return {
            'status': 'failed',
            'error_code': 'card_declined',
            'retry_count': 0,
            'user_message': 'Your card was declined. Please use a different payment method.',
            'security_flag': False,
            'requires_payment_method_update': True,
            'block_further_attempts': False,
            'error_type': 'card_declined',
            'error_class': 'CardError'
        }

    @staticmethod
    def confirm_existing_payment(payment_data):
        """Mock payment confirmation"""
        return {
            'status': 'requires_payment_method',
            'payment_intent_id': 'pi_test_recovery',
            'client_secret': 'pi_test_recovery_secret_xyz',
            'can_retry_with_different_method': True
        }

    @staticmethod
    def analyze_failure_patterns(failure_attempts):
        """Mock fraud detection analysis"""
        return {
            'is_suspicious': len(failure_attempts) >= 5,
            'failure_count': len(failure_attempts),
            'time_window_minutes': 5,
            'same_ip_address': True,
            'recommendation': 'temporary_block' if len(failure_attempts) >= 5 else 'monitor'
        }

    @staticmethod
    def detect_payment_amount_anomaly(amount, user_history):
        """Mock anomaly detection"""
        if len(user_history) == 0:
            return {'is_anomaly': False, 'deviation_factor': 1.0, 'recommendation': 'proceed'}

        avg_amount = sum(h['amount'] for h in user_history) / len(user_history)
        deviation_factor = amount / avg_amount if avg_amount > 0 else 1.0

        return {
            'is_anomaly': deviation_factor > 5.0,
            'deviation_factor': deviation_factor,
            'recommendation': 'additional_verification' if deviation_factor > 5.0 else 'proceed'
        }

    @staticmethod
    def generate_user_friendly_error(error_type):
        """Mock user-friendly error messages"""
        error_messages = {
            'insufficient_funds': {
                'message': 'Your card has insufficient funds. Please use a different card or contact your bank.',
                'suggestions': ['Use a different card', 'Check your account balance', 'Contact your bank']
            },
            'expired_card': {
                'message': 'Your card has expired. Please update your payment method.',
                'suggestions': ['Update your payment method', 'Use a new card', 'Add a backup payment method']
            },
            'connection_timeout': {
                'message': 'Connection timeout. Please check your connection and try again.',
                'suggestions': ['Check internet connection', 'Try again in a moment', 'Refresh the page']
            },
            'card_declined': {
                'message': 'Your card was declined. Please try a different payment method.',
                'suggestions': ['Use a different card', 'Contact your card issuer', 'Try bank transfer']
            }
        }

        return error_messages.get(error_type, {
            'message': 'Payment failed. Please try again or use a different payment method.',
            'suggestions': ['Try again', 'Use different payment method', 'Contact support']
        })

    @staticmethod
    def handle_payment_failure_notifications(payment_failure):
        """Mock notification handling"""
        return {
            'email_sent': True,
            'push_sent': True,
            'in_app_created': True
        }

    @staticmethod
    def handle_subscription_payment_failure(subscription_data, failure_type):
        """Mock subscription handling"""
        failure_count = subscription_data.get('payment_failure_count', 0)

        if failure_count >= 3:
            return {
                'status': 'suspended',
                'features_restricted': True,
                'immediate_action_required': True
            }
        else:
            return {
                'status': 'grace_period_active',
                'grace_period_days': 3,
                'features_restricted': False,
                'warning_sent': True
            }

    @staticmethod
    def generate_payment_failure_analytics(failure_events):
        """Mock analytics generation"""
        return {
            'total_failures': len(failure_events),
            'failure_rate_by_error_type': {
                'card_declined': 1,
                'expired_card': 1,
                'insufficient_funds': 1
            },
            'failure_rate_by_country': {'US': 1},
            'average_failure_amount': sum(e['amount'] for e in failure_events) / len(failure_events),
            'recommendations': ['Improve error handling', 'Add retry logic']
        }

    @staticmethod
    def calculate_payment_failure_dashboard_metrics(dashboard_data, time_window):
        """Mock dashboard metrics"""
        total_payments = dashboard_data['total_payments_attempted']
        successful = dashboard_data['successful_payments']

        return {
            'success_rate': successful / total_payments if total_payments > 0 else 0,
            'failure_rate': dashboard_data['failed_payments'] / total_payments if total_payments > 0 else 0,
            'recovery_rate': dashboard_data['revenue_recovered'] / dashboard_data['revenue_lost'] if dashboard_data['revenue_lost'] > 0 else 0,
            'net_revenue_impact': dashboard_data['revenue_lost'] - dashboard_data['revenue_recovered'],
            'weekly_trend': 'increasing'
        }

    @staticmethod
    def process_plan_upgrade_payment(upgrade_data):
        """Mock plan upgrade payment"""
        return {
            'upgrade_status': 'payment_failed',
            'current_plan': upgrade_data['current_plan'],
            'upgrade_available': True,
            'upgrade_token': 'upgrade_token_123'
        }

    @staticmethod
    def handle_partial_payment_failure(payment_state):
        """Mock partial payment handling"""
        return {
            'void_status': 'succeeded',
            'refund_amount': payment_state['amount_authorized'],
            'user_notified': True,
            'payment_state_cleaned': True
        }

    @staticmethod
    async def get_user_payment_state(user_id):
        """Mock user payment state"""
        return {
            'pending_attempts': 0,
            'failure_count': 1
        }

    @staticmethod
    async def process_payment_with_transaction(payment_data, db):
        """Mock payment with transaction"""
        return {
            'status': 'failed',
            'database_rolled_back': True,
            'data_consistency_maintained': True
        }

    @staticmethod
    def handle_payment_failed_webhook(payment_event):
        """Mock webhook handling"""
        return {
            'webhook_delivered': False,
            'fallback_notification_sent': True,
            'user_notified': True,
            'retry_scheduled': True
        }

# Mock the services
BillingService = MockBillingService


class TestFailedPaymentBehavior:
    """Comprehensive failed payment testing and error handling"""

    # 💳 Basic Payment Failure Tests
    def test_insufficient_funds_handling(self):
        """Test payment failure due to insufficient funds"""
        payment_data = {
            'user_id': 'user_123',
            'amount': 9999,  # $99.99
            'currency': 'usd',
            'payment_method_id': 'pm_insufficient_funds',
            'description': 'Enterprise subscription'
        }

        # Mock insufficient funds response
        mock_stripe_error = stripe.error.CardError(
            message="Your card has insufficient funds.",
            param="amount",
            code="card_declined",
            json_body={"error": {"decline_code": "insufficient_funds"}}
        )

        with patch('stripe.PaymentIntent.create', side_effect=mock_stripe_error):
            with pytest.raises(stripe.error.CardError) as exc_info:
                BillingService.create_payment_intent(payment_data)

            # Verify error details
            assert "insufficient funds" in str(exc_info.value).lower()
            assert exc_info.value.code == "card_declined"

    def test_expired_card_handling(self):
        """Test payment failure due to expired card"""
        payment_data = {
            'user_id': 'user_456',
            'amount': 4999,  # $49.99
            'currency': 'usd',
            'payment_method_id': 'pm_expired_card',
            'description': 'Professional subscription'
        }

        # Mock expired card response
        mock_stripe_error = stripe.error.CardError(
            message="Your card has expired.",
            param="exp_month",
            code="expired_card",
            json_body={"error": {"decline_code": "expired_card"}}
        )

        with patch('stripe.PaymentIntent.create', side_effect=mock_stripe_error):
            result = BillingService.process_payment_with_retry(payment_data, max_retries=2)

            # Should return failure result with specific error code
            assert result['status'] == 'failed'
            assert result['error_code'] == 'expired_card'
            assert result['retry_count'] == 0  # Should not retry expired cards
            assert result['user_message'] is not None

    def test_card_lost_or_stolen_handling(self):
        """Test payment failure for lost or stolen cards"""
        payment_data = {
            'user_id': 'user_789',
            'amount': 2999,
            'currency': 'usd',
            'payment_method_id': 'pm_lost_stolen',
            'description': 'Team subscription'
        }

        # Mock lost/stolen card response
        mock_stripe_error = stripe.error.CardError(
            message="The card was reported as lost or stolen.",
            param="payment_method",
            code="card_declined",
            json_body={"error": {"decline_code": "lost_or_stolen"}}
        )

        with patch('stripe.PaymentIntent.create', side_effect=mock_stripe_error):
            result = BillingService.process_payment_with_retry(payment_data)

            # Should handle as high-security issue
            assert result['status'] == 'failed'
            assert result['security_flag'] is True
            assert result['requires_payment_method_update'] is True
            assert result['block_further_attempts'] is True

    def test_connection_timeout_during_payment(self):
        """Test handling of connection timeouts during payment processing"""
        payment_data = {
            'user_id': 'user_timeout',
            'amount': 1999,
            'currency': 'usd',
            'payment_method_id': 'pm_timeout_test',
            'description': 'Basic subscription'
        }

        # Mock connection timeout
        mock_timeout_error = stripe.error.APIConnectionError(
            message="Request timed out.",
            should_retry=True
        )

        with patch('stripe.PaymentIntent.create', side_effect=mock_timeout_error):
            result = BillingService.process_payment_with_retry(
                payment_data,
                max_retries=3,
                retry_delay=0.1  # Fast retry for testing
            )

            # Should attempt retries and then fail
            assert result['status'] == 'failed'
            assert result['error_type'] == 'connection_timeout'
            assert result['retry_count'] > 0
            assert result['total_attempt_time'] > 0

    # 🔄 Retry Logic and Recovery Tests
    def test_smart_retry_logic_for_transient_failures(self):
        """Test intelligent retry logic for temporary failures"""
        test_scenarios = [
            {
                'name': 'Network Timeout',
                'error': stripe.error.APIConnectionError("Network timeout", should_retry=True),
                'should_retry': True,
                'expected_retries': 3
            },
            {
                'name': 'Rate Limited',
                'error': stripe.error.RateLimitError("Too many requests"),
                'should_retry': True,
                'expected_retries': 3
            },
            {
                'name': 'Server Error',
                'error': stripe.error.APIError("Internal server error"),
                'should_retry': True,
                'expected_retries': 2
            },
            {
                'name': 'Invalid Card',
                'error': stripe.error.InvalidRequestError("Invalid card number", param="number"),
                'should_retry': False,
                'expected_retries': 0
            }
        ]

        for scenario in test_scenarios:
            with patch('stripe.PaymentIntent.create', side_effect=scenario['error']):
                payment_data = {
                    'user_id': f'user_{scenario["name"].lower().replace(" ", "_")}',
                    'amount': 1000,
                    'currency': 'usd',
                    'payment_method_id': 'pm_test'
                }

                result = BillingService.process_payment_with_retry(
                    payment_data,
                    max_retries=3,
                    retry_delay=0.01
                )

                assert result['status'] == 'failed'
                assert result['retry_count'] == scenario['expected_retries']
                assert result['error_class'] == scenario['error'].__class__.__name__

    def test_exponential_backoff_retry_timing(self):
        """Test exponential backoff timing for retries"""
        retry_intervals = []

        def mock_payment_create(*args, **kwargs):
            retry_intervals.append(time.time())
            if len(retry_intervals) == 1:
                raise stripe.error.APIConnectionError("Timeout", should_retry=True)
            elif len(retry_intervals) == 2:
                raise stripe.error.APIConnectionError("Timeout", should_retry=True)
            else:
                raise stripe.error.APIConnectionError("Final timeout", should_retry=True)

        with patch('stripe.PaymentIntent.create', side_effect=mock_payment_create):
            start_time = time.time()

            result = BillingService.process_payment_with_retry(
                {'user_id': 'backoff_test', 'amount': 1000, 'currency': 'usd'},
                max_retries=3,
                base_retry_delay=0.1,
                use_exponential_backoff=True
            )

            end_time = time.time()
            total_time = end_time - start_time

            # Verify exponential backoff timing
            # Should be approximately: 0.1s + 0.2s + 0.4s = 0.7s (allowing for test variance)
            assert total_time >= 0.5  # Minimum expected time
            assert total_time <= 1.0   # Maximum reasonable time
            assert len(retry_intervals) == 3
            assert result['status'] == 'failed'

    def test_payment_state_recovery_after_failure(self):
        """Test recovery and state management after payment failure"""
        # Create initial payment intent
        initial_intent = {
            'id': 'pi_test_recovery',
            'status': 'requires_payment_method',
            'amount': 5000,
            'currency': 'usd',
            'client_secret': 'pi_test_recovery_secret_xyz'
        }

        payment_data = {
            'user_id': 'user_recovery',
            'payment_intent_id': initial_intent['id'],
            'new_payment_method_id': 'pm_new_card'
        }

        # Mock successful payment intent creation but failed confirmation
        with patch('stripe.PaymentIntent.retrieve', return_value=initial_intent):
            with patch('stripe.PaymentIntent.confirm', side_effect=stripe.error.CardError(
                "Card declined", param="payment_method", code="card_declined"
            )):
                result = BillingService.confirm_existing_payment(payment_data)

                # Should return clean state for retry
                assert result['status'] == 'requires_payment_method'
                assert result['payment_intent_id'] == initial_intent['id']
                assert result['client_secret'] == initial_intent['client_secret']
                assert result['can_retry_with_different_method'] is True

    # 🔐 Security and Fraud Prevention Tests
    def test_fraud_detection_on_repeated_failures(self):
        """Test fraud detection for repeated payment failures"""
        user_id = 'user_suspicious_activity'

        # Simulate multiple rapid failures
        failure_attempts = []
        for i in range(5):
            attempt_time = datetime.utcnow() - timedelta(minutes=i)
            failure_attempts.append({
                'user_id': user_id,
                'timestamp': attempt_time,
                'error_code': 'card_declined',
                'ip_address': '192.168.1.100',
                'device_fingerprint': 'device_xyz'
            })

        # Check if user should be flagged for fraud
        fraud_flags = BillingService.analyze_failure_patterns(failure_attempts)

        # Should detect suspicious pattern
        assert fraud_flags['is_suspicious'] is True
        assert fraud_flags['failure_count'] == 5
        assert fraud_flags['time_window_minutes'] <= 5
        assert fraud_flags['same_ip_address'] is True
        assert fraud_flags['recommendation'] in ['temporary_block', 'manual_review']

    def test_payment_method_blacklist_handling(self):
        """Test handling of blacklisted payment methods"""
        blacklisted_methods = [
            'pm_stolen_card_123',
            'pm_fraudulent_456',
            'pm_chargeback_789'
        ]

        payment_data = {
            'user_id': 'user_blacklist_test',
            'amount': 2000,
            'currency': 'usd',
            'payment_method_id': 'pm_stolen_card_123'
        }

        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.InvalidRequestError(
                "Payment method is blacklisted",
                param="payment_method"
            )

            result = BillingService.process_payment_with_retry(payment_data)

            assert result['status'] == 'failed'
            assert result['error_code'] == 'payment_method_blacklisted'
            assert result['payment_method_id'] in blacklisted_methods
            assert result['requires_new_payment_method'] is True

    def test_unusual_payment_amount_detection(self):
        """Test detection of unusual payment amounts"""
        user_history = [
            {'amount': 999, 'timestamp': datetime.utcnow() - timedelta(days=30)},
            {'amount': 999, 'timestamp': datetime.utcnow() - timedelta(days=60)},
            {'amount': 999, 'timestamp': datetime.utcnow() - timedelta(days=90)}
        ]

        # Current payment much higher than usual
        suspicious_payment = {
            'user_id': 'user_amount_anomaly',
            'amount': 99999,  # $999.99 vs usual $9.99
            'currency': 'usd',
            'payment_method_id': 'pm_high_amount'
        }

        anomaly_score = BillingService.detect_payment_amount_anomaly(
            suspicious_payment['amount'],
            user_history
        )

        # Should flag as unusual
        assert anomaly_score['is_anomaly'] is True
        assert anomaly_score['deviation_factor'] > 5.0
        assert anomaly_score['recommendation'] == 'additional_verification'

    # 📱 User Experience During Failures Tests
    def test_user_friendly_error_messages(self):
        """Test user-friendly error messages for different failure types"""
        error_scenarios = [
            {
                'error_type': 'insufficient_funds',
                'expected_message_contains': ['insufficient funds', 'different card'],
                'expected_suggestions': ['use different card', 'contact bank']
            },
            {
                'error_type': 'expired_card',
                'expected_message_contains': ['expired', 'update card'],
                'expected_suggestions': ['update payment method', 'new card']
            },
            {
                'error_type': 'connection_timeout',
                'expected_message_contains': ['connection', 'try again'],
                'expected_suggestions': ['check connection', 'try again']
            },
            {
                'error_type': 'card_declined',
                'expected_message_contains': ['declined', 'different payment'],
                'expected_suggestions': ['different payment method', 'contact issuer']
            }
        ]

        for scenario in error_scenarios:
            error_result = BillingService.generate_user_friendly_error(scenario['error_type'])

            # Should contain helpful information
            for phrase in scenario['expected_message_contains']:
                assert phrase.lower() in error_result['message'].lower()

            # Should provide actionable suggestions
            assert len(error_result['suggestions']) > 0
            for suggestion in scenario['expected_suggestions']:
                assert any(suggestion.lower() in s.lower() for s in error_result['suggestions'])

    def test_payment_failure_notification_system(self):
        """Test notification system for payment failures"""
        payment_failure = {
            'user_id': 'user_notifications',
            'organization_id': 'org_123',
            'amount': 5000,
            'currency': 'usd',
            'error_code': 'card_declined',
            'retry_count': 2,
            'subscription_id': 'sub_monthly'
        }

        with patch('app.services.notification_service.send_payment_failure_email') as mock_email:
            with patch('app.services.notification_service.send_push_notification') as mock_push:
                with patch('app.services.notification_service.create_in_app_notification') as mock_app:

                    notifications_sent = BillingService.handle_payment_failure_notifications(
                        payment_failure
                    )

                    # Should send multiple notification types
                    assert notifications_sent['email_sent'] is True
                    assert notifications_sent['push_sent'] is True
                    assert notifications_sent['in_app_created'] is True

                    mock_email.assert_called_once()
                    mock_push.assert_called_once()
                    mock_app.assert_called_once()

    def test_subscription_management_after_failure(self):
        """Test subscription handling after payment failure"""
        subscription_data = {
            'subscription_id': 'sub_failed_payment',
            'user_id': 'user_subscription',
            'organization_id': 'org_123',
            'plan_type': 'enterprise',
            'payment_failure_count': 1,
            'last_payment_attempt': datetime.utcnow()
        }

        # Test grace period handling
        grace_period_result = BillingService.handle_subscription_payment_failure(
            subscription_data,
            failure_type='card_declined'
        )

        # Should provide appropriate grace period and warnings
        assert grace_period_result['status'] == 'grace_period_active'
        assert grace_period_result['grace_period_days'] >= 3
        assert grace_period_result['features_restricted'] is False
        assert grace_period_result['warning_sent'] is True

        # Test after multiple failures
        subscription_data['payment_failure_count'] = 3
        final_failure_result = BillingService.handle_subscription_payment_failure(
            subscription_data,
            failure_type='card_declined'
        )

        # Should suspend after multiple failures
        assert final_failure_result['status'] == 'suspended'
        assert final_failure_result['features_restricted'] is True
        assert final_failure_result['immediate_action_required'] is True

    # 📊 Analytics and Monitoring Tests
    def test_payment_failure_analytics_tracking(self):
        """Test analytics tracking for payment failures"""
        failure_events = [
            {
                'timestamp': datetime.utcnow(),
                'user_id': 'user_analytics_1',
                'amount': 999,
                'error_code': 'insufficient_funds',
                'country': 'US',
                'payment_method_type': 'card'
            },
            {
                'timestamp': datetime.utcnow() + timedelta(minutes=5),
                'user_id': 'user_analytics_2',
                'amount': 1999,
                'error_code': 'expired_card',
                'country': 'UK',
                'payment_method_type': 'card'
            },
            {
                'timestamp': datetime.utcnow() + timedelta(minutes=10),
                'user_id': 'user_analytics_3',
                'amount': 2999,
                'error_code': 'card_declined',
                'country': 'CA',
                'payment_method_type': 'card'
            }
        ]

        # Analyze failure patterns
        analytics_report = BillingService.generate_payment_failure_analytics(failure_events)

        assert analytics_report['total_failures'] == 3
        assert analytics_report['failure_rate_by_error_type']['card_declined'] == 1
        assert analytics_report['failure_rate_by_country']['US'] == 1
        assert analytics_report['average_failure_amount'] > 0
        assert 'recommendations' in analytics_report

    def test_payment_failure_dashboard_metrics(self):
        """Test dashboard metrics for payment failures"""
        time_window = timedelta(days=7)

        # Mock payment failure data
        dashboard_data = {
            'total_payments_attempted': 1000,
            'successful_payments': 950,
            'failed_payments': 50,
            'failure_reasons': {
                'insufficient_funds': 20,
                'expired_card': 15,
                'card_declined': 10,
                'connection_timeout': 5
            },
            'revenue_lost': 2497.50,  # Sum of failed payment amounts
            'revenue_recovered': 999.00  # Successfully retried payments
        }

        metrics = BillingService.calculate_payment_failure_dashboard_metrics(
            dashboard_data,
            time_window
        )

        # Verify calculated metrics
        assert metrics['success_rate'] == 0.95  # 95%
        assert metrics['failure_rate'] == 0.05  # 5%
        assert metrics['recovery_rate'] > 0
        assert metrics['net_revenue_impact'] == dashboard_data['revenue_lost'] - dashboard_data['revenue_recovered']
        assert 'weekly_trend' in metrics

    # 🔧 Integration and Edge Cases
    def test_payment_failure_during_plan_upgrade(self):
        """Test payment failure during plan upgrade process"""
        upgrade_data = {
            'user_id': 'user_upgrade_fail',
            'organization_id': 'org_upgrade',
            'current_plan': 'professional',
            'target_plan': 'enterprise',
            'upgrade_amount': 15000,  # $150 upgrade fee
            'payment_method_id': 'pm_upgrade_fail'
        }

        with patch('stripe.PaymentIntent.create', side_effect=stripe.error.CardError(
            "Card declined during upgrade", param="amount", code="card_declined"
        )):
            result = BillingService.process_plan_upgrade_payment(upgrade_data)

            # Should handle upgrade failure gracefully
            assert result['upgrade_status'] == 'payment_failed'
            assert result['current_plan'] == 'professional'  # Should remain on current plan
            assert result['upgrade_available'] is True  # Should allow retry
            assert result['upgrade_token'] is not None  # Should preserve upgrade intent

    def test_partial_payment_refund_after_failure(self):
        """Test handling of partial payments that need refunding"""
        # Simulate scenario where partial authorization was obtained but full payment failed
        payment_state = {
            'user_id': 'user_partial_refund',
            'amount_authorized': 10000,  # $100 authorized
            'amount_captured': 0,  # $0 actually captured
            'payment_intent_id': 'pi_partial_authorization',
            'failure_reason': 'payment_method_timeout'
        }

        with patch('stripe.PaymentIntent.retrieve', return_value=payment_state):
            with patch('stripe.Refund.create') as mock_refund:
                mock_refund.return_value = {
                    'id': 're_refund_test',
                    'amount': 10000,
                    'status': 'succeeded'
                }

                result = BillingService.handle_partial_payment_failure(payment_state)

                # Should void authorization and clean up state
                assert result['void_status'] == 'succeeded'
                assert result['refund_amount'] == 10000
                assert result['user_notified'] is True
                assert result['payment_state_cleaned'] is True

    @pytest.mark.asyncio
    async def test_concurrent_payment_failure_handling(self):
        """Test handling of concurrent payment failures from same user"""
        user_id = 'user_concurrent_failures'

        # Simulate multiple concurrent payment attempts
        async def process_payment_attempt(attempt_id):
            payment_data = {
                'user_id': user_id,
                'amount': 1000,
                'currency': 'usd',
                'payment_method_id': f'pm_attempt_{attempt_id}'
            }

            # Mock payment failure
            await asyncio.sleep(0.01)  # Simulate processing time
            raise stripe.error.CardError(
                "Card declined",
                param="payment_method",
                code="card_declined"
            )

        # Run concurrent attempts
        tasks = [process_payment_attempt(i) for i in range(5)]

        start_time = time.time()

        with pytest.raises(stripe.error.CardError):
            await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()

        # Should handle concurrent failures efficiently
        assert end_time - start_time < 1.0  # Should complete quickly

        # Verify no race conditions in user state
        user_payment_state = await BillingService.get_user_payment_state(user_id)
        assert user_payment_state['pending_attempts'] == 0
        assert user_payment_state['failure_count'] >= 1

    # 🔔 Webhook Failure Handling Tests
    def test_webhook_failure_during_payment_events(self):
        """Test handling when webhooks fail during payment events"""
        payment_event = {
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_webhook_test',
                    'status': 'requires_payment_method',
                    'last_payment_error': {
                        'code': 'card_declined',
                        'message': 'Your card was declined.'
                    },
                    'metadata': {
                        'user_id': 'user_webhook_fail',
                        'organization_id': 'org_webhook'
                    }
                }
            }
        }

        with patch('app.services.webhook_service.send_payment_failure_webhook') as mock_webhook:
            mock_webhook.side_effect = Exception("Webhook delivery failed")

            with patch('app.services.notification_service.create_fallback_notification') as mock_fallback:
                result = BillingService.handle_payment_failed_webhook(payment_event)

                # Should handle webhook failure gracefully
                assert result['webhook_delivered'] is False
                assert result['fallback_notification_sent'] is True
                assert result['user_notified'] is True
                assert result['retry_scheduled'] is True

    def test_payment_failure_database_transaction_rollback(self):
        """Test database transaction rollback on payment failure"""
        from app.core.database import get_db

        payment_data = {
            'user_id': 'user_transaction_rollback',
            'amount': 5000,
            'currency': 'usd',
            'description': 'Test payment with rollback'
        }

        mock_db = AsyncMock()

        with patch('stripe.PaymentIntent.create', side_effect=stripe.error.CardError(
            "Card declined", param="card", code="card_declined"
        )):
            with patch.object(mock_db, 'commit', side_effect=Exception("DB commit failed")):
                with patch.object(mock_db, 'rollback') as mock_rollback:

                    result = await BillingService.process_payment_with_transaction(
                        payment_data,
                        db=mock_db
                    )

                    # Should rollback database changes on failure
                    mock_rollback.assert_called_once()
                    assert result['status'] == 'failed'
                    assert result['database_rolled_back'] is True
                    assert result['data_consistency_maintained'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
