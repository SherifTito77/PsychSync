#!/usr/bin/env python3
"""
Comprehensive Integration Testing Suite for PsychSync Platform
Tests critical third-party integrations and system behaviors:

1. SendGrid Email Integration Testing
2. SSO Integration Testing (Google & Microsoft)
3. API Downtime Graceful Handling
4. AI Recommendation Generation After Team Sync
5. Webhook Retry Logic Testing

Author: Integration Testing Team
Version: 1.0 Enterprise Integration
"""

import asyncio
import aiohttp
import json
import time
import uuid
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import jwt
import hashlib
import base64
import secrets
from unittest.mock import Mock, patch, AsyncMock
from urllib.parse import urlencode, urlparse, parse_qs

@dataclass
class IntegrationTestResult:
    """Integration test result with comprehensive metrics"""
    test_name: str
    success: bool
    duration: float
    details: str = ""
    error_message: str = ""
    metrics: Dict[str, Any] = None
    recommendations: List[str] = None

class IntegrationTester:
    """Comprehensive integration testing for PsychSync platform"""

    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5174"
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.mock_services = {}

    async def __aenter__(self):
        # Configure session for integration testing
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_headers(self):
        """Get authentication headers"""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    def setup_mocks(self):
        """Setup mock services for integration testing"""
        # Mock SendGrid service
        self.mock_services['sendgrid'] = {
            'api_key': 'SG.test_key_placeholder',
            'endpoint': 'https://api.sendgrid.com/v3/mail/send',
            'success_response': {"messageId": f"msg_{uuid.uuid4()}"},
            'error_response': {"errors": [{"message": "API limit exceeded"}]}
        }

        # Mock OAuth providers
        self.mock_services['oauth'] = {
            'google': {
                'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'client_id': 'google_test_client_id',
                'client_secret': 'google_test_client_secret'
            },
            'microsoft': {
                'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
                'client_id': 'microsoft_test_client_id',
                'client_secret': 'microsoft_test_client_secret'
            }
        }

        # Mock webhook endpoints
        self.mock_services['webhooks'] = {
            'retry_count': {},
            'success_rate': 0.8  # 80% success rate for testing
        }

    async def test_sendgrid_email_integration(self):
        """
        Test 1: SendGrid Email Integration
        Test email sending functionality and error handling
        """
        print("📧 SENDGRID EMAIL INTEGRATION TEST")
        print("=" * 50)

        self.setup_mocks()
        start_time = time.time()

        # Test scenarios for SendGrid integration
        test_scenarios = [
            {
                "name": "Welcome Email",
                "endpoint": "/api/v1/emails/send-welcome",
                "payload": {
                    "to": "test@example.com",
                    "subject": "Welcome to PsychSync",
                    "template": "welcome",
                    "data": {"user_name": "Test User", "company": "Test Company"}
                }
            },
            {
                "name": "Assessment Completion",
                "endpoint": "/api/v1/emails/send-assessment-completion",
                "payload": {
                    "to": "test@example.com",
                    "subject": "Assessment Results Ready",
                    "template": "assessment_results",
                    "data": {"assessment_type": "MBTI", "score": 85}
                }
            },
            {
                "name": "Team Invitation",
                "endpoint": "/api/v1/emails/send-team-invitation",
                "payload": {
                    "to": "team@example.com",
                    "subject": "Team Invitation - PsychSync",
                    "template": "team_invitation",
                    "data": {"team_name": "Test Team", "inviter": "Manager Name"}
                }
            },
            {
                "name": "Large Payload Email",
                "endpoint": "/api/v1/emails/send-large",
                "payload": {
                    "to": "test@example.com",
                    "subject": "Large Data Email Test",
                    "template": "report_delivery",
                    "data": {"report_data": "X" * 10000}  # Large data
                }
            },
            {
                "name": "Invalid Email",
                "endpoint": "/api/v1/emails/send-invalid",
                "payload": {
                    "to": "invalid-email-format",
                    "subject": "Invalid Email Test",
                    "template": "test"
                }
            }
        ]

        results = []

        for scenario in test_scenarios:
            print(f"\n🔄 Testing {scenario['name']}...")

            try:
                request_start = time.time()
                headers = self.get_headers()

                async with self.session.post(
                    f"{self.backend_url}{scenario['endpoint']}",
                    json=scenario['payload'],
                    headers=headers
                ) as response:
                    request_time = time.time() - request_start

                    if response.status == 200:
                        response_data = await response.json()

                        # Validate email structure
                        if "message_id" in response_data or "status" in response_data:
                            results.append({
                                "scenario": scenario["name"],
                                "success": True,
                                "response_time": request_time,
                                "response_data": response_data
                            })
                            print(f"   ✅ {scenario['name']}: Success ({request_time:.3f}s)")
                        else:
                            results.append({
                                "scenario": scenario["name"],
                                "success": False,
                                "response_time": request_time,
                                "error": "Invalid response structure"
                            })
                            print(f"   ⚠️  {scenario['name']}: Invalid structure ({request_time:.3f}s)")
                    else:
                        error_data = await response.text() if response.content_type != 'application/json' else str(response.status)
                        results.append({
                            "scenario": scenario["name"],
                            "success": False,
                            "response_time": request_time,
                            "error": f"HTTP {response.status}: {error_data}"
                        })
                        print(f"   ❌ {scenario['name']}: Failed ({response.status}) ({request_time:.3f}s)")

            except Exception as e:
                results.append({
                    "scenario": scenario["name"],
                    "success": False,
                    "response_time": 0.0,
                    "error": str(e)
                })
                print(f"   ❌ {scenario['name']}: Exception - {str(e)[:50]}")

            # Small delay between tests
            await asyncio.sleep(0.5)

        # Test SendGrid API error scenarios
        print(f"\n🔄 Testing SendGrid API Error Scenarios...")

        error_scenarios = [
            {"name": "Rate Limit Exceeded", "simulate_error": "rate_limit"},
            {"name": "Invalid API Key", "simulate_error": "invalid_key"},
            {"name": "Service Unavailable", "simulate_error": "service_down"},
            {"name": "Large Attachment", "simulate_error": "attachment_too_large"}
        ]

        for scenario in error_scenarios:
            try:
                headers = self.get_headers()

                # Add error simulation header
                headers["X-Simulate-Error"] = scenario["simulate_error"]

                async with self.session.post(
                    f"{self.backend_url}/api/v1/emails/send-test-error",
                    json={"to": "test@example.com", "subject": "Test"},
                    headers=headers
                ) as response:
                    if response.status in [429, 503, 400]:
                        print(f"   ✅ {scenario['name']}: Proper error handling ({response.status})")
                    else:
                        print(f"   ⚠️  {scenario['name']}: Unexpected response ({response.status})")

            except Exception as e:
                print(f"   ❌ {scenario['name']}: Exception - {str(e)[:50]}")

        # Calculate metrics
        total_time = time.time() - start_time
        successful_tests = sum(1 for r in results if r["success"])
        total_tests = len(results)
        success_rate = (successful_tests / total_tests) * 100

        if results:
            avg_response_time = sum(r["response_time"] for r in results) / len(results)

            print(f"\n📊 SENDGRID INTEGRATION RESULTS:")
            print(f"   Total Tests: {total_tests}")
            print(f"   Successful: {successful_tests}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Average Response Time: {avg_response_time:.3f}s")
            print(f"   Total Duration: {total_time:.1f}s")

            if success_rate >= 80:
                print(f"   ✅ EXCELLENT: High success rate for email integration")
            elif success_rate >= 60:
                print(f"   ⚠️  GOOD: Acceptable success rate")
            else:
                print(f"   ❌ POOR: Low success rate - investigation needed")

        return IntegrationTestResult(
            "SendGrid Email Integration",
            success_rate >= 60,
            total_time,
            f"Success rate: {success_rate:.1f}%, Avg response: {avg_response_time:.3f}s",
            recommendations=[
                "Monitor email delivery rates and bounce rates",
                "Implement email queuing for high-volume sending",
                "Add retry logic for transient failures"
            ],
            metrics={
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time
            }
        )

    async def test_sso_integration(self):
        """
        Test 2: SSO Integration Testing (Google & Microsoft)
        Test OAuth2 authentication flow and user profile synchronization
        """
        print("\n🔐 SSO INTEGRATION TEST")
        print("=" * 50)

        self.setup_mocks()
        start_time = time.time()

        providers = ["google", "microsoft"]
        results = []

        for provider in providers:
            print(f"\n🔄 Testing {provider.title()} SSO Integration...")
            provider_config = self.mock_services['oauth'][provider]

            # Test OAuth flow initiation
            oauth_scenarios = [
                {
                    "name": "Normal OAuth Flow",
                    "user_id": f"sso_test_{provider}_{int(time.time())}",
                    "state": "test_state_valid"
                },
                {
                    "name": "OAuth with Custom State",
                    "user_id": f"sso_test_{provider}_custom_{int(time.time())}",
                    "state": "custom_state_12345"
                },
                {
                    "name": "OAuth with Invalid State",
                    "user_id": f"sso_test_{provider}_invalid_{int(time.time())}",
                    "state": None
                }
            ]

            for scenario in oauth_scenarios:
                print(f"   🔄 {scenario['name']}...")

                try:
                    # Step 1: Initiate OAuth flow
                    auth_params = {
                        "client_id": provider_config["client_id"],
                        "redirect_uri": f"{self.backend_url}/api/v1/auth/{provider}/callback",
                        "response_type": "code",
                        "scope": "email profile openid",
                        "state": scenario["state"] or f"state_{uuid.uuid4()}"
                    }

                    auth_url = f"{provider_config['auth_url']}?{urlencode(auth_params)}"
                    print(f"      Auth URL: {auth_url[:100]}...")

                    # Simulate user authorization and callback
                    auth_code = f"mock_auth_code_{uuid.uuid4()}"
                    callback_data = {
                        "code": auth_code,
                        "state": scenario["state"],
                        "error": None
                    }

                    if scenario["name"] == "OAuth with Invalid State":
                        callback_data["state"] = "invalid_state"

                    # Step 2: Exchange code for access token
                    token_request_start = time.time()

                    token_response = {
                        "access_token": f"mock_access_token_{uuid.uuid4()}",
                        "refresh_token": f"mock_refresh_token_{uuid.uuid4()}",
                        "expires_in": 3600,
                        "token_type": "Bearer"
                    }

                    # Step 3: Get user profile
                    headers = self.get_headers()

                    async with self.session.get(
                        f"{self.backend_url}/api/v1/auth/{provider}/callback",
                        params=callback_data,
                        headers=headers
                    ) as response:
                        callback_time = time.time() - token_request_start

                        if response.status == 200:
                            user_data = await response.json()

                            # Validate user data structure
                            required_fields = ["user_id", "email", "name"]
                            missing_fields = [field for field in required_fields if field not in user_data]

                            if not missing_fields:
                                results.append({
                                    "provider": provider,
                                    "scenario": scenario["name"],
                                    "success": True,
                                    "callback_time": callback_time,
                                    "user_data": user_data
                                })
                                print(f"      ✅ {scenario['Name']}: Success (User: {user_data.get('email', 'Unknown')})")
                            else:
                                results.append({
                                    "provider": provider,
                                    "scenario": scenario["name"],
                                    "success": False,
                                    "callback_time": callback_time,
                                    "error": f"Missing fields: {missing_fields}"
                                })
                                print(f"      ❌ {scenario['Name']}: Missing data - {missing_fields}")
                        else:
                            error_data = await response.text()
                            results.append({
                                "provider": provider,
                                "scenario": scenario["name"],
                                "success": False,
                                "callback_time": callback_time,
                                "error": f"HTTP {response.status}: {error_data}"
                            })
                            print(f"      ❌ {scenario['Name']}: HTTP {response.status}")

                except Exception as e:
                    results.append({
                        "provider": provider,
                        "scenario": scenario["name"],
                        "success": False,
                        "callback_time": 0.0,
                        "error": str(e)
                    })
                    print(f"      ❌ {scenario['Name']}: Exception - {str(e)[:50]}")

                # Test SSO token refresh
                try:
                    print(f"   🔄 Testing token refresh for {provider.title()}...")

                    refresh_headers = self.get_headers()
                    refresh_data = {
                        "refresh_token": f"mock_refresh_token_{uuid.uuid4()}",
                        "grant_type": "refresh_token"
                    }

                    async with self.session.post(
                        f"{self.backend_url}/api/v1/auth/{provider}/refresh",
                        json=refresh_data,
                        headers=refresh_headers
                    ) as response:
                        if response.status == 200:
                            print(f"      ✅ Token refresh successful")
                        else:
                            print(f"      ⚠️  Token refresh failed ({response.status})")

                except Exception as e:
                    print(f"      ❌ Token refresh exception: {str(e)[:50]}")

                # Small delay between OAuth flows
                await asyncio.sleep(0.5)

        # Calculate SSO metrics
        total_time = time.time() - start_time
        successful_sso = sum(1 for r in results if r["success"])
        total_sso = len(results)
        success_rate = (successful_sso / total_sso) * 100

        if results:
            avg_callback_time = sum(r["callback_time"] for r in results) / len(results)

            print(f"\n📊 SSO INTEGRATION RESULTS:")
            print(f"   Total OAuth Flows: {total_sso}")
            print(f"   Successful: {successful_sso}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Average Callback Time: {avg_callback_time:.3f}s")
            print(f"   Total Duration: {total_time:.1f}s")

            # Provider-specific results
            for provider in providers:
                provider_results = [r for r in results if r["provider"] == provider]
                provider_success = sum(1 for r in provider_results if r["success"])
                provider_total = len(provider_results)
                provider_rate = (provider_success / provider_total) * 100 if provider_total > 0 else 0

                print(f"   {provider.title()} SSO: {provider_success}/{provider_total} ({provider_rate:.1f}%)")

        return IntegrationTestResult(
            "SSO Integration Testing",
            success_rate >= 70,
            total_time,
            f"Success rate: {success_rate:.1f}%, Avg callback: {avg_callback_time:.3f}s",
            recommendations=[
                "Implement proper OAuth2 state validation",
                "Add user profile synchronization",
                "Monitor SSO success rates and user satisfaction",
                "Implement automatic token refresh"
            ],
            metrics={
                "total_oauth_flows": total_sso,
                "successful_flows": successful_sso,
                "success_rate": success_rate,
                "avg_callback_time": avg_callback_time
            }
        )

    async def test_api_downtime_handling(self):
        """
        Test 3: API Downtime Graceful Handling
        Test frontend behavior when backend APIs are unavailable
        """
        print("\n🌐 API DOWNTIME HANDLING TEST")
        print("=" * 50)

        start_time = time.time()
        scenarios = [
            {
                "name": "Connection Timeout",
                "simulate": "timeout",
                "endpoint": "/api/v1/dashboard"
            },
            {
                "name": "Service Unavailable",
                "simulate": "503",
                "endpoint": "/api/v1/assessments"
            },
            {
                "name": "Rate Limited",
                "simulate": "429",
                "endpoint": "/api/v1/users/me"
            },
            {
                "name": "Database Error",
                "simulate": "500",
                "endpoint": "/api/v1/reports"
            },
            {
                "name": "Partial Service Degradation",
                "simulate": "degraded",
                "endpoint": "/api/v1/analytics"
            }
        ]

        results = []

        for scenario in scenarios:
            print(f"\n🔄 Testing {scenario['Name']}...")

            try:
                headers = self.get_headers()
                headers["X-Simulate-Failure"] = scenario["simulate"]

                request_start = time.time()

                async with self.session.get(
                    f"{self.backend_url}{scenario['endpoint']}",
                    headers=headers
                ) as response:
                    response_time = time.time() - request_start

                    # Check graceful handling indicators
                    graceful_indicators = [
                        "fallback" in response.headers.get("X-Response-Mode", "").lower(),
                        "cached" in response.headers.get("X-Data-Source", "").lower(),
                        response.status < 500 or response.status >= 600  # Client errors vs server errors
                    ]

                    is_graceful = any(graceful_indicators)

                    if scenario["simulate"] == "timeout":
                        # For timeouts, check if request was handled gracefully
                        if response_time < 30:  # Fast timeout handling
                            is_graceful = True

                    result = {
                        "scenario": scenario["name"],
                        "simulate": scenario["simulate"],
                        "response_status": response.status,
                        "response_time": response_time,
                        "graceful": is_graceful,
                        "headers": dict(response.headers)
                    }

                    results.append(result)

                    status_display = "✅" if is_graceful else "❌"
                    print(f"   {status_display} {scenario['Name']}: HTTP {response.status} ({response_time:.3f}s) - {'Graceful' if is_graceful else 'Not graceful'}")

            except Exception as e:
                error_time = time.time() - start_time
                results.append({
                    "scenario": scenario["name"],
                    "simulate": scenario["simulate"],
                    "error": str(e),
                    "error_time": error_time,
                    "graceful": False
                })
                print(f"   ❌ {scenario['Name']}: Exception - {str(e)[:50]}")

            # Small delay between tests
            await asyncio.sleep(0.3)

        # Test frontend fallback mechanisms
        print(f"\n🔄 Testing Frontend Fallback Mechanisms...")

        fallback_tests = [
            {"name": "Dashboard Data Cache", "endpoint": "/api/v1/dashboard"},
            {"name": "User Profile Cache", "endpoint": "/api/v1/users/me"},
            {"name": "Assessment Templates", "endpoint": "/api/v1/assessments/templates"},
            {"name": "Static Content", "endpoint": "/api/v1/static/config"}
        ]

        for test in fallback_tests:
            print(f"   🔄 Testing {test['Name']} fallback...")

            try:
                headers = self.get_headers()
                headers["X-Test-Fallback"] = "true"

                # First request (may fail)
                request1_start = time.time()
                async with self.session.get(
                    f"{self.backend_url}{test['endpoint']}",
                    headers=headers
                ) as response1:
                    response1_time = time.time() - request1_start
                    first_success = response1.status == 200

                # Second request (should use fallback if first failed)
                request2_start = time.time()
                async with self.session.get(
                    f"{self.backend_url}{test['endpoint']}",
                    headers=headers
                ) as response2:
                    response2_time = time.time() - request2_start
                    second_success = response2.status == 200

                    fallback_working = (not first_success and second_success) or (first_success and second_success)

                    print(f"      {'✅' if fallback_working else '❌'} {test['Name']}: First: {first_success}, Second: {second_success}")

            except Exception as e:
                print(f"   ❌ {test['Name']}: Exception - {str(e)[:50]}")

        # Calculate API downtime handling metrics
        total_time = time.time() - start_time
        graceful_handling = sum(1 for r in results if r.get("graceful", False))
        total_tests = len(results)
        grace_rate = (graceful_handling / total_tests) * 100

        if results:
            print(f"\n📊 API DOWNTIME HANDLING RESULTS:")
            print(f"   Total Test Scenarios: {total_tests}")
            print(f"   Graceful Handling: {graceful_handling}")
            print(f"   Grace Rate: {grace_rate:.1f}%")
            print(f"   Total Duration: {total_time:.1f}s")

            if grace_rate >= 80:
                print(f"   ✅ EXCELLENT: System handles downtime gracefully")
            elif grace_rate >= 60:
                print(f"   ⚠️  GOOD: Acceptable graceful handling")
            else:
                print(f"   ❌ POOR: Graceful handling needs improvement")

        return IntegrationTestResult(
            "API Downtime Graceful Handling",
            grace_rate >= 70,
            total_time,
            f"Graceful handling rate: {grace_rate:.1f}%",
            recommendations=[
                "Implement API response caching",
                "Add fallback data sources for critical information",
                "Implement user-friendly error messages",
                "Add offline mode capabilities",
                "Monitor API availability and performance"
            ],
            metrics={
                "total_tests": total_tests,
                "graceful_handling": graceful_handling,
                "grace_rate": grace_rate
            }
        )

    async def test_ai_recommendations_after_team_sync(self):
        """
        Test 4: AI Recommendation Generation After Team Sync
        Test AI-powered insights generation after team data synchronization
        """
        print("\n🤖 AI RECOMMENDATION GENERATION AFTER TEAM SYNC")
        print("=" * 50)

        start_time = time.time()

        # Test team sync scenarios
        sync_scenarios = [
            {
                "name": "Small Team Sync",
                "team_size": 5,
                "members": [
                    {"user_id": f"user_{i}", "role": ["analyst", "manager", "member", "leader"][i%4],
                     "performance": random.randint(70, 95),
                     "assessments": ["MBTI", "Enneagram", "Big Five"][random.randint(0, 2)]
                    }
                    for i in range(5)
                ]
            },
            {
                "name": "Medium Team Sync",
                "team_size": 15,
                "members": [
                    {"user_id": f"user_{i}", "role": ["analyst", "manager", "member", "leader"][i%4],
                     "performance": random.randint(60, 90),
                     "assessments": ["MBTI", "Enneagram", "Big Five", "DISC"][random.randint(0, 3)]
                    }
                    for i in range(15)
                ]
            },
            {
                "name": "Large Team Sync",
                "team_size": 50,
                "members": [
                    {"user_id": f"user_{i}", "role": ["analyst", "manager", "member", "leader"][i%4],
                     "performance": random.randint(50, 85),
                     "assessments": ["MBTI", "Team Roles", "Predictive Index"][random.randint(0, 2)]
                    }
                    for i in range(50)
                ]
            },
            {
                "name": "Mixed Performance Team",
                "team_size": 20,
                "members": [
                    {"user_id": f"user_{i}", "role": ["analyst", "manager", "member", "leader"][i%4],
                     "performance": random.randint(30, 100),
                     "assessments": ["MBTI", "Enneagram", "Big Five", "DISC", "Predictive Index"][random.randint(0, 4)]
                    }
                    for i in range(20)
                ]
            }
        ]

        results = []

        for scenario in sync_scenarios:
            print(f"\n🔄 Testing {scenario['Name']} (Team Size: {scenario['team_size']})...")

            try:
                # Step 1: Sync team data
                print(f"   📊 Syncing {scenario['team_size']} team members...")

                sync_data = {
                    "team_id": f"team_{uuid.uuid4()}",
                    "team_name": f"Test Team {scenario['name']}",
                    "members": scenario['members']
                }

                headers = self.get_headers()
                sync_start = time.time()

                async with self.session.post(
                    f"{self.backend_url}/api/v1/teams/sync",
                    json=sync_data,
                    headers=headers
                ) as sync_response:
                    sync_time = time.time() - sync_start

                    if sync_response.status == 200:
                        sync_data_result = await sync_response.json()
                        print(f"      ✅ Team sync successful ({sync_time:.3f}s)")

                        # Step 2: Generate AI recommendations
                        print(f"   🤖 Generating AI recommendations...")

                        recommend_start = time.time()

                        async with self.session.post(
                            f"{self.backend_url}/api/v1/ai/generate-team-recommendations",
                            json={"team_id": sync_data_result.get("team_id")},
                            headers=headers
                        ) as recommend_response:
                            recommend_time = time.time() - recommend_start

                            if recommend_response.status == 200:
                                ai_recommendations = await recommend_response.json()

                                # Validate recommendation structure
                                required_recommendation_fields = [
                                    "team_dynamics", "personality_fit",
                                    "role_suggestions", "growth_opportunities"
                                ]

                                missing_fields = [field for field in required_recommendation_fields
                                                  if field not in ai_recommendations]

                                if not missing_fields:
                                    # Validate recommendation quality
                                    rec_count = len(ai_recommendations.get("recommendations", []))
                                    confidence = ai_recommendations.get("confidence", 0)

                                    result = {
                                        "scenario": scenario["name"],
                                        "team_size": scenario["team_size"],
                                        "sync_time": sync_time,
                                        "recommend_time": recommend_time,
                                        "total_time": sync_time + recommend_time,
                                        "success": True,
                                        "recommendation_count": rec_count,
                                        "confidence": confidence,
                                        "data": ai_recommendations
                                    }

                                    results.append(result)

                                    print(f"      ✅ Recommendations generated ({rec_count} items, confidence: {confidence:.1f})")
                                else:
                                    print(f"      ⚠️  Recommendations incomplete (missing: {missing_fields})")
                                else:
                                    print(f"      ✅ Recommendations generated successfully")
                            else:
                                print(f"      ❌ Recommendation generation failed (HTTP {recommend_response.status})")
                            else:
                                error_data = await recommend_response.text()
                                print(f"      ❌ Recommendation failed: {error_data[:100]}")
                    else:
                        error_data = await sync_response.text()
                        print(f"      ❌ Team sync failed (HTTP {sync_response.status}): {error_data[:100]}")

            except Exception as e:
                print(f"   ❌ {scenario['Name']} Exception: {str(e)[:50]}")

            # Small delay between scenarios
            await asyncio.sleep(1)

        # Test AI recommendation quality metrics
        print(f"\n🔄 Testing AI Recommendation Quality Metrics...")

        quality_tests = [
            {
                "name": "Consistent Team Analysis",
                "test_type": "consistency"
            },
            {
                "name": "Actionable Recommendations",
                "test_type": "actionability"
            },
            {
                "name": "Data-Driven Insights",
                "test_type": "data_driven"
            }
        ]

        for test in quality_tests:
            print(f"   🔄 Testing {test['name']}...")

            try:
                headers = self.get_headers()

                test_data = {
                    "test_type": test["test_type"],
                    "team_id": f"quality_test_{uuid.uuid4()}"
                }

                async with self.session.post(
                    f"{self.backend_url}/api/v1/ai/test-recommendation-quality",
                    json=test_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        quality_result = await response.json()
                        print(f"      ✅ {test['Name']}: {quality_result.get('score', 0):.1f}/10 score")
                    else:
                        print(f"      ⚠️  {test['Name']}: HTTP {response.status}")

            except Exception as e:
                print(f"   ❌ {test['Name']}: Exception - {str(e)[:50]}")

        # Calculate AI recommendation metrics
        total_time = time.time() - start_time
        successful_scenarios = sum(1 for r in results if r.get("success", False))
        total_scenarios = len(results)
        success_rate = (successful_scenarios / total_scenarios) * 100

        if results:
            avg_sync_time = sum(r["sync_time"] for r in results) / len(results)
            avg_recommend_time = sum(r["recommendation_time"] for r in results) / len(results)
            avg_total_time = sum(r["total_time"] for r in results) / len(results)
            avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)
            avg_rec_count = sum(r.get("recommendation_count", 0) for r in results) / len(results)

            print(f"\n📊 AI RECOMMENDATION RESULTS:")
            print(f"   Total Team Scenarios: {total_scenarios}")
            print(f"   Successful: {successful_scenarios}")
            f"   Success Rate: {success_rate:.1f}%"
            print(f"   Avg Team Sync Time: {avg_sync_time:.3f}s")
            print(f"   Avg Recommendation Time: {avg_recommend_time:.3f}s")
            print(f"   Avg Total Time: {avg_total_time:.3f}s")
            print(f"   Avg Confidence: {avg_confidence:.1f}")
            print(f"   Avg Recommendations: {avg_rec_count:.1f}")
            print(f"   Total Duration: {total_time:.1f}s")

            # Performance analysis by team size
            team_size_analysis = {}
            for result in results:
                size = result["team_size"]
                if size not in team_size_analysis:
                    team_size_analysis[size] = []
                team_size_analysis[size].append(result)

            print(f"\n📈 PERFORMANCE BY TEAM SIZE:")
            for size in sorted(team_size_analysis.keys()):
                size_results = team_size_analysis[size]
                size_success = sum(1 for r in size_results if r.get("success", False))
                size_rate = (size_success / len(size_results)) * 100
                size_avg_time = sum(r.get("total_time", 0) for r in size_results) / len(size_results)

                print(f"   {size} Members: {size_success}/{len(size_results)} ({size_rate:.1f}%), Avg: {size_avg_time:.3f}s")

            if success_rate >= 80:
                print(f"   ✅ EXCELLENT: AI recommendations working well")
            elif success_rate >= 60:
                print(f"   ⚠️  GOOD: AI recommendations acceptable")
            else:
                print(f"   ❌ POOR: AI recommendations need improvement")

        return IntegrationTestResult(
            "AI Recommendation Generation After Team Sync",
            success_rate >= 70,
            total_time,
            f"Success rate: {success_rate:.1f}%, Avg confidence: {avg_confidence:.1f}",
            recommendations=[
                "Monitor AI recommendation accuracy and user feedback",
                "Implement recommendation explanation mechanisms",
                "Add confidence score calibration",
                "Implement recommendation diversity algorithms",
                "Add A/B testing for recommendation models"
            ],
            metrics={
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "success_rate": success_rate,
                "avg_sync_time": avg_sync_time,
                "avg_recommendation_time": avg_recommend_time,
                "avg_confidence": avg_confidence,
                "avg_recommendation_count": avg_rec_count
            }
        )

    async def test_webhook_retry_logic(self):
        """
        Test 5: Webhook Retry Logic Testing
        Test webhook delivery retry mechanisms and failure handling
        """
        print("\n🔗 WEBHOOK RETRY LOGIC TESTING")
        print("=" * 50)

        start_time = time.time()

        # Test webhook scenarios
        webhook_scenarios = [
            {
                "name": "Successful Delivery",
                "simulate": "success",
                "endpoint": "/webhooks/test/success",
                "retry_count": 0
            },
            {
                "name": "Transient Failure - Retry Success",
                "simulate": "transient_failure_then_success",
                "endpoint": "/webhooks/test/retry",
                "retry_count": 3
            },
            {
                "name": "Permanent Failure",
                "simulate": "permanent_failure",
                "endpoint": "/webhooks/test/failure",
                "retry_count": 5
            },
            {
                "webhook_type": "assessment_completed",
                "simulate": "success",
                "endpoint": "/webhooks/assessment/completed",
                "retry_count": 0
            },
            {
                "webhook_type": "team_updated",
                "simulate": "transient_failure_then_success",
                "endpoint": "/webhooks/team/updated",
                "retry_count": 2
            }
        ]

        results = []

        for scenario in webhook_scenarios:
            print(f"\n🔄 Testing {scenario.get('name', scenario.get('webhook_type'))}...")

            webhook_data = {
                "event_type": scenario.get("webhook_type", "test_event"),
                "data": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "webhook_id": f"webhook_{uuid.uuid4()}",
                    "payload": {"test": "data", "value": random.randint(1, 100)}
                },
                "simulate_failure": scenario["simulate"],
                "retry_count": scenario.get("retry_count", 0)
            }

            try:
                headers = self.get_headers()

                delivery_start = time.time()

                async with self.session.post(
                    f"{self.backend_url}/api/v1/webhooks/deliver",
                    json=webhook_data,
                    headers=headers
                ) as response:
                    delivery_time = time.time() - delivery_start

                    if response.status == 200:
                        webhook_result = await response.json()

                        # Check retry information
                        actual_retry_count = webhook_result.get("retry_count", 0)
                        delivery_status = webhook_result.get("delivery_status", "unknown")

                        result = {
                            "scenario": scenario.get("name", scenario.get("webhook_type")),
                            "simulate": scenario["simulate"],
                            "expected_retries": scenario.get("retry_count", 0),
                            "actual_retries": actual_retry_count,
                            "delivery_status": delivery_status,
                            "delivery_time": delivery_time,
                            "success": True,
                            "webhook_result": webhook_result
                        }

                        # Validate retry logic
                        retry_match = (
                            (scenario.get("simulate") == "success" and actual_retry_count == 0) or
                            (scenario.get("simulate") == "permanent_failure" and actual_retry_count >= scenario.get("retry_count", 0)) or
                            (scenario.get("simulate") == "transient_failure_then_success" and actual_retry_count > 0 and actual_retry_count <= scenario.get("retry_count", 0))
                        )

                        retry_status = "✅" if retry_match else "❌"

                        results.append(result)
                        print(f"      {retry_status} {scenario.get('name', scenario.get('webhook_type')): "
                              f"Expected {scenario.get('retry_count')}, Got {actual_retry_count}, "
                              f"Status: {delivery_status} ({delivery_time:.3f}s)")

                    else:
                        print(f"      ❌ Webhook delivery failed (HTTP {response.status})")

                except Exception as e:
                    print(f"      ❌ Webhook delivery exception: {str(e)[:50]}")

            # Small delay between webhook tests
            await asyncio.sleep(0.5)

        # Test webhook configuration and management
        print(f"\n🔄 Testing Webhook Configuration...")

        config_tests = [
            {
                "name": "Create Webhook",
                "action": "create",
                "data": {
                    "url": "https://test.example.com/webhook",
                    "events": ["assessment.completed", "team.updated"],
                    "secret": "test_webhook_secret"
                }
            },
            {
                "name": "Update Webhook",
                "action": "update",
                "data": {
                    "url": "https://test.example.com/webhook-updated",
                    "events": ["assessment.completed"],
                    "active": True
                }
            },
            {
                "name": "Test Webhook",
                "action": "test",
                "data": {
                    "url": "https://test.example.com/webhook"
                }
            },
            {
                "name": "Delete Webhook",
                "action": "delete",
                "data": {"id": "test_webhook_id"}
            }
        ]

        for config_test in config_tests:
            print(f"   🔄 Testing {config_test['name']}...")

            try:
                headers = self.get_headers()

                async with self.session.post(
                    f"{self.backend_url}/api/v1/webhooks/{config_test['action']}",
                    json=config_test["data"],
                    headers=headers
                ) as response:
                    if response.status in [200, 201, 204]:
                        print(f"      ✅ {config_test['name']}: HTTP {response.status}")
                    else:
                        print(f"      ⚠️  {config_test['name']}: HTTP {response.status}")

            except Exception as e:
                print(f"      ❌ {config_test['Name']}: Exception - {str(e)[:50]}")

        # Test webhook retry configuration
        print(f"\n🔄 Testing Webhook Retry Configuration...")

        retry_config_tests = [
            {"max_retries": 1, "backoff_strategy": "exponential"},
            {"max_retries": 3, "backoff_strategy": "linear"},
            {"max_retries": 5, "backoff_strategy": "fixed"},
            {"max_retries": 10, "backoff_strategy": "adaptive"}
        ]

        for config in retry_config_tests:
            print(f"   🔄 Testing retry configuration: {config['max_retries']} retries, {config['backoff_strategy']} backoff")

            try:
                headers = self.get_headers()

                test_data = {
                    "max_retries": config["max_retries"],
                    "backoff_strategy": config["backoff_strategy"],
                    "test_simulation": True
                }

                async with self.session.post(
                    f"{self.backend_url}/api/v1/webhooks/configure-retry",
                    json=test_data,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        config_result = await response.json()
                        print(f"      ✅ Retry configuration set: {config['max_retries']} retries")
                    else:
                        print(f"      ⚠️  Retry configuration failed: HTTP {response.status}")

            except Exception as e:
                print(f"      ❌ Retry configuration exception: {str(e)[:50]}")

        # Calculate webhook metrics
        total_time = time.time() - start_time
        successful_webhooks = sum(1 for r in results if r.get("success", False))
        total_webhooks = len(results)
        success_rate = (successful_webhooks / total_webhooks) * 100

        if results:
            avg_delivery_time = sum(r["delivery_time"] for r in results) / len(results)
            avg_retries = sum(r["actual_retries"] for r in results) / len(results)

            print(f"\n📊 WEBHOOK RETRY LOGIC RESULTS:")
            print(f"   Total Webhook Tests: {total_webhooks}")
            print(f"   Successful Deliveries: {successful_webhooks}")
            f"   Success Rate: {success_rate:.1f}%"
            print(f"   Average Delivery Time: {avg_delivery_time:.3f}s")
            print(f"   Average Retry Count: {avg_retries:.1f}")
            print(f"   Total Duration: {total_time:.1f}s")

            # Retry logic accuracy
            retry_accuracy_tests = [r for r in results if r.get("expected_retries") is not None]
            if retry_accuracy_tests:
                accurate_retries = sum(1 for r in retry_accuracy_tests if r.get("expected_retries") == r.get("actual_retries"))
                accuracy_rate = (accurate_retries / len(retry_accuracy_tests)) * 100

                print(f"   Retry Logic Accuracy: {accuracy_rate:.1f}% ({accurate_retries}/{len(retry_accuracy_tests)})")

            if success_rate >= 90:
                print(f"   ✅ EXCELLENT: Webhook delivery very reliable")
            elif success_rate >= 75:
                print(f"   ⚠️  GOOD: Webhook delivery acceptable")
            else:
                print(f"   ❌ POOR: Webhook delivery needs improvement")

        return IntegrationTestResult(
            "Webhook Retry Logic Testing",
            success_rate >= 80,
            total_time,
            f"Success rate: {success_rate:.1f}%, Avg delivery: {avg_delivery_time:.3f}s",
            recommendations=[
                "Implement webhook delivery monitoring",
                "Add webhook signature validation",
                "Configure appropriate retry policies",
                "Monitor webhook success rates and failures",
                "Implement dead letter queue for failed webhooks"
            ],
            metrics={
                "total_webhooks": total_webhooks,
                "successful_webhooks": successful_webhooks,
                "success_rate": success_rate,
                "avg_delivery_time": avg_delivery_time,
                "avg_retry_count": avg_retries
            }
        )

    async def run_integration_tests(self):
        """Run all integration tests and generate comprehensive report"""
        print("🔗 PSYNSYNC COMPREHENSIVE INTEGRATION TESTING SUITE")
        print("=" * 80)
        print("Testing critical third-party integrations and system behaviors")
        print("=" * 80)

        self.start_time = time.time()

        try:
            # Run all integration tests
            test_methods = [
                self.test_sendgrid_email_integration,
                self.test_sso_integration,
                self.test_api_downtime_handling,
                self.test_ai_recommendations_after_team_sync,
                self.test_webhook_retry_logic
            ]

            for test_method in test_methods:
                print(f"\n{'='*60}")
                test_result = await test_method()
                self.test_results.append(test_result)

                # Print test summary
                status = "✅ PASS" if test_result.success else "❌ FAIL"
                print(f"{status} {test_result.test_name}: {test_result.details}")
                if test_result.recommendations:
                    print(f"   💡 Top Recommendation: {test_result.recommendations[0]}")

            # Generate comprehensive report
            self.generate_integration_report()

        except KeyboardInterrupt:
            print("\n⚠️  Integration testing interrupted by user")
            return
        except Exception as e:
            print(f"\n💥 Integration testing failed: {e}")
            return

        total_time = time.time() - self.start_time
        print(f"\n🎉 COMPREHENSIVE INTEGRATION TESTING COMPLETED")
        print(f"⏱️  Total Duration: {total_time/60:.1f} minutes")

    def generate_integration_report(self):
        """Generate comprehensive integration testing report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE INTEGRATION TESTING REPORT")
        print("="*80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100

        print(f"\n📈 INTEGRATION TESTING SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")

        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"{result.duration:.1f}s"
            print(f"   {status} {result.test_name:<30} {duration:<10}")

        print(f"\n🔍 FAILED TESTS DETAILS:")
        for result in self.test_results:
            if not result.success:
                print(f"\n❌ {result.test_name}:")
                print(f"   Error: {result.error_message}")
                if result.recommendations:
                    print(f"   💡 Recommendations: {', '.join(result.recommendations[:2])}")

        print(f"\n💡 INTEGRATION TESTING RECOMMENDATIONS:")
        all_recommendations = []
        for result in self.test_results:
            all_recommendations.extend(result.recommendations or [])

        # Remove duplicates and prioritize
        unique_recommendations = list(set(all_recommendations))
        priority_recommendations = [
            "Monitor all third-party integrations continuously",
            "Implement comprehensive error handling and fallback mechanisms",
            "Add monitoring and alerting for all critical integrations",
            "Test integrations in staging before production deployment"
        ]

        # Show priority recommendations first
        for rec in priority_recommendations:
            if rec in unique_recommendations:
                print(f"   🔴 HIGH: {rec}")
                unique_recommendations.remove(rec)

        # Show remaining recommendations
        for i, rec in enumerate(unique_recommendations[:10], 1):
            print(f"   {i}. {rec}")

        print(f"\n🚀 PRODUCTION DEPLOYMENT READINESS:")
        if success_rate >= 80:
            print(f"   ✅ EXCELLENT: Integration testing demonstrates production readiness")
        elif success_rate >= 70:
            print(f"   ⚠️  GOOD: Integration testing shows acceptable production readiness")
        else:
            print(f"   ❌ NEEDS IMPROVEMENT: Address integration failures before production")

        print(f"\n📊 NEXT PHASE:")
        print(f"   1. Address failed integration tests")
        print(f"   2. Implement monitoring for all integrations")
        f"   3. Set up alerting for integration failures")
        print(f"   4. Create integration testing in CI/CD pipeline")

        print(f"\n" + "="*80)
        print("🎉 INTEGRATION TESTING ANALYSIS COMPLETE")
        print("="*80)

async def main():
    """Main integration testing execution"""
    try:
        async with IntegrationTester() as tester:
            await tester.run_integration_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Integration testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    import random  # Add missing import
    asyncio.run(main())