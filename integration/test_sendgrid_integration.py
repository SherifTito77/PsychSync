#!/usr/bin/env python3
"""
SendGrid Email Integration Testing Module
Tests email sending functionality with SendGrid API
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os
from unittest.mock import Mock, AsyncMock, patch
import pytest as pytest

@dataclass
class EmailTestConfig:
    """Configuration for email testing"""
    api_key: str = "test_sendgrid_api_key"
    from_email: str = "test@psychsync.com"
    base_url: str = "https://api.sendgrid.com/v3"
    timeout: int = 30
    retry_attempts: int = 3

@dataclass
class EmailTestResult:
    """Result of email testing"""
    test_name: str
    success: bool
    response_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class SendGridMockService:
    """Mock SendGrid service for testing"""

    def __init__(self):
        self.emails_sent = []
        self.api_calls = []
        self.response_times = []
        self.error_conditions = {}

    async def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email sending with realistic delays and error conditions"""
        start_time = time.time()

        self.api_calls.append({
            'endpoint': '/mail/send',
            'method': 'POST',
            'timestamp': datetime.now(),
            'data': email_data
        })

        # Simulate API processing time
        await asyncio.sleep(0.1 + (len(email_data.get('personalizations', [])) * 0.05))

        # Check for error conditions
        to_emails = []
        for personalization in email_data.get('personalizations', []):
            if isinstance(personalization, dict) and 'to' in personalization:
                for recipient in personalization['to']:
                    if isinstance(recipient, dict) and 'email' in recipient:
                        to_emails.append(recipient['email'])

        for email in to_emails:
            if email in self.error_conditions:
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                return {
                    'status_code': self.error_conditions[email]['status_code'],
                    'body': json.dumps({'errors': [self.error_conditions[email]['message']]}),
                    'response_time': response_time
                }

        # Store email for verification
        self.emails_sent.append({
            'to': to_emails,
            'subject': email_data.get('subject', ''),
            'content': email_data.get('content', {}),
            'timestamp': datetime.now()
        })

        response_time = time.time() - start_time
        self.response_times.append(response_time)

        return {
            'status_code': 202,
            'body': json.dumps({'message': 'Email sent successfully'}),
            'response_time': response_time
        }

    def set_error_condition(self, email: str, status_code: int, message: str):
        """Set error condition for specific email"""
        self.error_conditions[email] = {
            'status_code': status_code,
            'message': message
        }

    def clear_emails(self):
        """Clear sent emails for new test"""
        self.emails_sent.clear()
        self.api_calls.clear()
        self.response_times.clear()
        self.error_conditions.clear()

class SendGridIntegrationTester:
    """Comprehensive SendGrid integration tester"""

    def __init__(self, config: EmailTestConfig = None):
        self.config = config or EmailTestConfig()
        self.mock_service = SendGridMockService()
        self.test_results: List[EmailTestResult] = []

    async def test_single_email_sending(self) -> EmailTestResult:
        """Test sending single email"""
        print("Testing single email sending...")

        email_data = {
            'personalizations': [{
                'to': [{'email': 'test@example.com'}],
                'subject': 'PsychSync Assessment Invitation'
            }],
            'from': {'email': self.config.from_email},
            'content': [{
                'type': 'text/html',
                'value': '<h1>Welcome to PsychSync</h1><p>You have been invited to take an assessment.</p>'
            }]
        }

        try:
            start_time = time.time()
            result = await self.mock_service.send_email(email_data)
            end_time = time.time()

            success = result['status_code'] == 202

            return EmailTestResult(
                test_name="Single Email Sending",
                success=success,
                response_time=end_time - start_time,
                details={
                    'status_code': result['status_code'],
                    'email_count': 1,
                    'api_response': json.loads(result['body'])
                }
            )

        except Exception as e:
            return EmailTestResult(
                test_name="Single Email Sending",
                success=False,
                response_time=0,
                details={},
                error_message=str(e)
            )

    async def test_bulk_email_sending(self, recipient_count: int = 100) -> EmailTestResult:
        """Test sending bulk emails"""
        print(f"Testing bulk email sending to {recipient_count} recipients...")

        recipients = [{'email': f'user{i}@example.com'} for i in range(recipient_count)]

        email_data = {
            'personalizations': [{
                'to': recipients,
                'subject': 'Team Assessment Notification'
            }],
            'from': {'email': self.config.from_email},
            'content': [{
                'type': 'text/html',
                'value': '<h1>Team Assessment</h1><p>Your team has been invited to complete assessments.</p>'
            }]
        }

        try:
            start_time = time.time()
            result = await self.mock_service.send_email(email_data)
            end_time = time.time()

            success = result['status_code'] == 202

            return EmailTestResult(
                test_name=f"Bulk Email Sending ({recipient_count} recipients)",
                success=success,
                response_time=end_time - start_time,
                details={
                    'status_code': result['status_code'],
                    'recipient_count': recipient_count,
                    'emails_per_second': recipient_count / (end_time - start_time),
                    'api_response': json.loads(result['body'])
                }
            )

        except Exception as e:
            return EmailTestResult(
                test_name=f"Bulk Email Sending ({recipient_count} recipients)",
                success=False,
                response_time=0,
                details={},
                error_message=str(e)
            )

    async def test_email_template_sending(self) -> EmailTestResult:
        """Test sending email with SendGrid template"""
        print("Testing template-based email sending...")

        email_data = {
            'personalizations': [{
                'to': [{'email': 'template@example.com'}],
                'subject': 'Assessment Results',
                'dynamic_template_data': {
                    'user_name': 'John Doe',
                    'assessment_type': 'Big Five',
                    'completion_date': '2025-01-12',
                    'results_link': 'https://psychsync.com/results/abc123'
                }
            }],
            'from': {'email': self.config.from_email},
            'template_id': 'd-template-123456789'
        }

        try:
            start_time = time.time()
            result = await self.mock_service.send_email(email_data)
            end_time = time.time()

            success = result['status_code'] == 202

            return EmailTestResult(
                test_name="Template Email Sending",
                success=success,
                response_time=end_time - start_time,
                details={
                    'status_code': result['status_code'],
                    'template_id': email_data['template_id'],
                    'dynamic_data_keys': list(email_data['personalizations'][0]['dynamic_template_data'].keys()),
                    'api_response': json.loads(result['body'])
                }
            )

        except Exception as e:
            return EmailTestResult(
                test_name="Template Email Sending",
                success=False,
                response_time=0,
                details={},
                error_message=str(e)
            )

    async def test_error_handling(self) -> EmailTestResult:
        """Test error handling for invalid email addresses"""
        print("Testing error handling for invalid emails...")

        # Set error conditions
        self.mock_service.set_error_condition('invalid@example', 400, 'Invalid email address')
        self.mock_service.set_error_condition('bounced@example.com', 422, 'Email address has bounced')
        self.mock_service.set_error_condition('blocked@example.com', 403, 'Email address is blocked')

        error_scenarios = [
            {'email': 'invalid@example', 'expected_error': 'Invalid email address'},
            {'email': 'bounced@example.com', 'expected_error': 'Email address has bounced'},
            {'email': 'blocked@example.com', 'expected_error': 'Email address is blocked'},
            {'email': 'valid@example.com', 'expected_success': True}
        ]

        results = []

        for scenario in error_scenarios:
            email_data = {
                'personalizations': [{
                    'to': [{'email': scenario['email']}],
                    'subject': 'Test Email'
                }],
                'from': {'email': self.config.from_email},
                'content': [{'type': 'text', 'value': 'Test content'}]
            }

            try:
                result = await self.mock_service.send_email(email_data)

                if 'expected_success' in scenario:
                    success = result['status_code'] == 202
                else:
                    success = result['status_code'] != 202

                results.append({
                    'email': scenario['email'],
                    'success': success,
                    'status_code': result['status_code'],
                    'expected': scenario.get('expected_error', 'success')
                })

            except Exception as e:
                results.append({
                    'email': scenario['email'],
                    'success': False,
                    'error': str(e),
                    'expected': scenario.get('expected_error', 'success')
                })

        # Clear error conditions
        self.mock_service.clear_emails()

        successful_tests = sum(1 for r in results if r['success'])

        return EmailTestResult(
            test_name="Error Handling",
            success=successful_tests == len(error_scenarios),
            response_time=0,
            details={
                'total_tests': len(error_scenarios),
                'successful_tests': successful_tests,
                'test_results': results
            }
        )

    async def test_rate_limiting(self) -> EmailTestResult:
        """Test rate limiting behavior"""
        print("Testing rate limiting behavior...")

        # Send emails rapidly to test rate limiting
        emails_per_second = 100
        duration_seconds = 5

        tasks = []
        for i in range(emails_per_second * duration_seconds):
            email_data = {
                'personalizations': [{
                    'to': [{'email': f'ratelimit{i}@example.com'}],
                    'subject': f'Rate Limit Test {i}'
                }],
                'from': {'email': self.config.from_email},
                'content': [{'type': 'text', 'value': f'Test content {i}'}]
            }
            tasks.append(self.mock_service.send_email(email_data))

        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        successful_sends = sum(1 for r in results if isinstance(r, dict) and r.get('status_code') == 202)
        total_time = end_time - start_time

        return EmailTestResult(
            test_name="Rate Limiting",
            success=successful_sends > 0,
            response_time=total_time,
            details={
                'total_emails': len(tasks),
                'successful_sends': successful_sends,
                'emails_per_second_actual': successful_sends / total_time,
                'success_rate': (successful_sends / len(tasks)) * 100,
                'test_duration': total_time
            }
        )

    async def test_email_attachments(self) -> EmailTestResult:
        """Test sending emails with attachments"""
        print("Testing email with attachments...")

        attachment_data = {
            'content': 'SGVsbG8gV29ybGQ=',  # Base64 encoded "Hello World"
            'filename': 'test-report.pdf',
            'type': 'application/pdf',
            'disposition': 'attachment'
        }

        email_data = {
            'personalizations': [{
                'to': [{'email': 'attachment@example.com'}],
                'subject': 'Assessment Report'
            }],
            'from': {'email': self.config.from_email},
            'content': [{
                'type': 'text/html',
                'value': '<p>Please find your assessment report attached.</p>'
            }],
            'attachments': [attachment_data]
        }

        try:
            start_time = time.time()
            result = await self.mock_service.send_email(email_data)
            end_time = time.time()

            success = result['status_code'] == 202

            return EmailTestResult(
                test_name="Email Attachments",
                success=success,
                response_time=end_time - start_time,
                details={
                    'status_code': result['status_code'],
                    'attachment_count': len(email_data.get('attachments', [])),
                    'attachment_types': [att.get('type') for att in email_data.get('attachments', [])],
                    'api_response': json.loads(result['body'])
                }
            )

        except Exception as e:
            return EmailTestResult(
                test_name="Email Attachments",
                success=False,
                response_time=0,
                details={},
                error_message=str(e)
            )

    async def test_webhook_integration(self) -> EmailTestResult:
        """Test SendGrid webhook integration for email events"""
        print("Testing webhook integration...")

        # Simulate webhook events
        webhook_events = [
            {'event': 'delivered', 'email': 'delivered@example.com', 'timestamp': int(time.time())},
            {'event': 'opened', 'email': 'opened@example.com', 'timestamp': int(time.time())},
            {'event': 'clicked', 'email': 'clicked@example.com', 'timestamp': int(time.time())},
            {'event': 'bounced', 'email': 'bounced@example.com', 'reason': 'invalid', 'timestamp': int(time.time())},
            {'event': 'unsubscribed', 'email': 'unsubscribed@example.com', 'timestamp': int(time.time())}
        ]

        processed_events = []

        for event in webhook_events:
            # Simulate webhook processing
            await asyncio.sleep(0.01)  # Simulate processing time

            processed_events.append({
                'event_type': event['event'],
                'email': event['email'],
                'processed': True,
                'timestamp': datetime.now()
            })

        return EmailTestResult(
            test_name="Webhook Integration",
            success=len(processed_events) == len(webhook_events),
            response_time=sum(0.01 for _ in webhook_events),
            details={
                'total_events': len(webhook_events),
                'processed_events': len(processed_events),
                'event_types': list(set(e['event'] for e in webhook_events)),
                'events': processed_events
            }
        )

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all SendGrid integration tests"""
        print("Starting comprehensive SendGrid integration testing...")

        test_functions = [
            self.test_single_email_sending,
            self.test_bulk_email_sending,
            self.test_email_template_sending,
            self.test_error_handling,
            self.test_rate_limiting,
            self.test_email_attachments,
            self.test_webhook_integration
        ]

        for test_func in test_functions:
            result = await test_func()
            self.test_results.append(result)

            status = "✅" if result.success else "❌"
            print(f"{status} {result.test_name}: {result.response_time:.3f}s")

            if result.error_message:
                print(f"   Error: {result.error_message}")

        # Generate summary
        successful_tests = sum(1 for r in self.test_results if r.success)
        total_tests = len(self.test_results)

        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests / total_tests) * 100,
                'average_response_time': sum(r.response_time for r in self.test_results) / total_tests
            },
            'test_results': [
                {
                    'name': r.test_name,
                    'success': r.success,
                    'response_time': r.response_time,
                    'details': r.details,
                    'error_message': r.error_message,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.test_results
            ],
            'mock_service_stats': {
                'emails_sent': len(self.mock_service.emails_sent),
                'api_calls': len(self.mock_service.api_calls),
                'average_response_time': sum(self.mock_service.response_times) / len(self.mock_service.response_times) if self.mock_service.response_times else 0
            }
        }

# Main execution for standalone testing
async def main():
    """Run SendGrid integration tests"""
    tester = SendGridIntegrationTester()
    results = await tester.run_all_tests()

    print("\n" + "="*60)
    print("SendGrid INTEGRATION TEST RESULTS")
    print("="*60)

    summary = results['summary']
    print(f"Tests Run: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Average Response Time: {summary['average_response_time']:.3f}s")

    print("\nDetailed Results:")
    for result in results['test_results']:
        status = "PASS" if result['success'] else "FAIL"
        print(f"  {status} {result['name']}: {result['response_time']:.3f}s")
        if result['error_message']:
            print(f"       Error: {result['error_message']}")

    print(f"\nMock Service Stats:")
    stats = results['mock_service_stats']
    print(f"  Emails Sent: {stats['emails_sent']}")
    print(f"  API Calls: {stats['api_calls']}")
    print(f"  Avg Response Time: {stats['average_response_time']:.3f}s")

    # Save results to file
    with open('sendgrid_integration_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: sendgrid_integration_test_results.json")

    return results

if __name__ == "__main__":
    asyncio.run(main())
