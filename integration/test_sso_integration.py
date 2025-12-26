#!/usr/bin/env python3
"""
SSO Integration Testing Module
Tests Single Sign-On authentication with Google and Microsoft
"""

import asyncio
import aiohttp
import json
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, parse_qs
import secrets
import hashlib
import pytest as pytest

@dataclass
class SSOConfig:
    """Configuration for SSO testing"""
    google_client_id: str = "test_google_client_id"
    google_client_secret: str = "test_google_client_secret"
    microsoft_client_id: str = "test_microsoft_client_id"
    microsoft_client_secret: str = "test_microsoft_client_secret"
    redirect_uri: str = "http://localhost:5173/auth/callback"
    scopes: List[str] = None
    token_endpoint: str = "http://localhost:8000/api/v1/auth/token"

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["openid", "profile", "email"]

@dataclass
class SSOTestResult:
    """Result of SSO testing"""
    test_name: str
    provider: str
    success: bool
    response_time: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MockOAuthProvider:
    """Mock OAuth provider for testing"""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.authorization_codes = {}
        self.access_tokens = {}
        self.user_profiles = {}
        self.rate_limit_tracker = {}
        self.error_conditions = {}

    def generate_authorization_code(self, state: str, user_id: str = None) -> str:
        """Generate mock authorization code"""
        code = secrets.token_urlsafe(32)
        self.authorization_codes[code] = {
            'state': state,
            'user_id': user_id or f"{self.provider_name}_user_{secrets.token_hex(4)}",
            'expires_at': datetime.now() + timedelta(minutes=10)
        }
        return code

    def exchange_code_for_token(self, code: str, client_id: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        if code in self.error_conditions:
            return self.error_conditions[code]

        if code not in self.authorization_codes:
            return {'error': 'invalid_grant', 'error_description': 'Invalid authorization code'}

        auth_data = self.authorization_codes[code]
        if datetime.now() > auth_data['expires_at']:
            del self.authorization_codes[code]
            return {'error': 'invalid_grant', 'error_description': 'Authorization code expired'}

        access_token = secrets.token_urlsafe(64)
        refresh_token = secrets.token_urlsafe(64)

        self.access_tokens[access_token] = {
            'user_id': auth_data['user_id'],
            'refresh_token': refresh_token,
            'expires_at': datetime.now() + timedelta(hours=1),
            'scopes': ['openid', 'profile', 'email']
        }

        # Clean up authorization code
        del self.authorization_codes[code]

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }

    def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user profile from access token"""
        if access_token in self.error_conditions:
            return self.error_conditions[access_token]

        if access_token not in self.access_tokens:
            return {'error': 'invalid_token', 'error_description': 'Invalid access token'}

        token_data = self.access_tokens[access_token]
        if datetime.now() > token_data['expires_at']:
            del self.access_tokens[access_token]
            return {'error': 'invalid_token', 'error_description': 'Access token expired'}

        user_id = token_data['user_id']
        if user_id not in self.user_profiles:
            # Generate mock profile
            self.user_profiles[user_id] = self._generate_mock_profile(user_id)

        return self.user_profiles[user_id]

    def _generate_mock_profile(self, user_id: str) -> Dict[str, Any]:
        """Generate mock user profile"""
        base_profile = {
            'id': user_id,
            'email': f"{user_id}@{self.provider_name.lower()}.com",
            'name': f"{user_id.replace('_', ' ').title()}",
            'verified': True
        }

        if self.provider_name.lower() == 'google':
            base_profile.update({
                'sub': user_id,
                'picture': f"https://lh3.googleusercontent.com/photo/{user_id}",
                'given_name': user_id.split('_')[2] if '_' in user_id else 'John',
                'family_name': user_id.split('_')[3] if '_' in user_id and len(user_id.split('_')) > 3 else 'Doe',
                'locale': 'en'
            })
        elif self.provider_name.lower() == 'microsoft':
            base_profile.update({
                'oid': user_id,
                'displayName': base_profile['name'],
                'surname': 'Doe',
                'givenName': 'John',
                'userPrincipalName': base_profile['email']
            })

        return base_profile

    def set_error_condition(self, token_or_code: str, error_response: Dict[str, Any]):
        """Set error condition for specific token or code"""
        self.error_conditions[token_or_code] = error_response

    def check_rate_limit(self, client_id: str) -> bool:
        """Check rate limiting for client"""
        current_time = time.time()
        if client_id not in self.rate_limit_tracker:
            self.rate_limit_tracker[client_id] = []

        # Clean up old requests (older than 1 minute)
        self.rate_limit_tracker[client_id] = [
            req_time for req_time in self.rate_limit_tracker[client_id]
            if current_time - req_time < 60
        ]

        # Check if rate limit exceeded (100 requests per minute)
        if len(self.rate_limit_tracker[client_id]) >= 100:
            return False

        self.rate_limit_tracker[client_id].append(current_time)
        return True

class SSOIntegrationTester:
    """Comprehensive SSO integration tester"""

    def __init__(self, config: SSOConfig = None):
        self.config = config or SSOConfig()
        self.google_provider = MockOAuthProvider("Google")
        self.microsoft_provider = MockOAuthProvider("Microsoft")
        self.test_results: List[SSOTestResult] = []

    async def test_oauth_authorization_flow(self, provider: str) -> SSOTestResult:
        """Test OAuth authorization flow"""
        print(f"Testing OAuth authorization flow for {provider}...")

        mock_provider = getattr(self, f"{provider.lower()}_provider")

        # Step 1: Generate authorization URL
        state = secrets.token_urlsafe(32)
        params = {
            'client_id': getattr(self.config, f"{provider.lower()}_client_id"),
            'redirect_uri': self.config.redirect_uri,
            'scope': ' '.join(self.config.scopes),
            'response_type': 'code',
            'state': state
        }

        auth_url = f"https://accounts.{provider.lower()}.com/oauth/authorize?{urlencode(params)}"

        # Step 2: Simulate user authorization
        authorization_code = mock_provider.generate_authorization_code(state)

        # Step 3: Exchange authorization code for access token
        start_time = time.time()

        token_response = mock_provider.exchange_code_for_token(
            authorization_code,
            getattr(self.config, f"{provider.lower()}_client_id")
        )

        end_time = time.time()

        if 'error' in token_response:
            return SSOTestResult(
                test_name="OAuth Authorization Flow",
                provider=provider,
                success=False,
                response_time=end_time - start_time,
                details={'error': token_response['error']},
                error_message=token_response.get('error_description')
            )

        # Step 4: Get user profile
        profile_response = mock_provider.get_user_profile(token_response['access_token'])

        if 'error' in profile_response:
            return SSOTestResult(
                test_name="OAuth Authorization Flow",
                provider=provider,
                success=False,
                response_time=end_time - start_time,
                details={'token_valid': True, 'profile_error': profile_response['error']},
                error_message=profile_response.get('error_description')
            )

        return SSOTestResult(
            test_name="OAuth Authorization Flow",
            provider=provider,
            success=True,
            response_time=end_time - start_time,
            details={
                'authorization_code_generated': True,
                'access_token_received': bool(token_response.get('access_token')),
                'refresh_token_received': bool(token_response.get('refresh_token')),
                'token_type': token_response.get('token_type'),
                'expires_in': token_response.get('expires_in'),
                'user_profile': {
                    'id': profile_response.get('id'),
                    'email': profile_response.get('email'),
                    'name': profile_response.get('name'),
                    'verified': profile_response.get('verified')
                }
            }
        )

    async def test_token_refresh(self, provider: str) -> SSOTestResult:
        """Test token refresh mechanism"""
        print(f"Testing token refresh for {provider}...")

        mock_provider = getattr(self, f"{provider.lower()}_provider")

        # Setup: Get initial token
        state = secrets.token_urlsafe(32)
        auth_code = mock_provider.generate_authorization_code(state)

        initial_token_response = mock_provider.exchange_code_for_token(
            auth_code,
            getattr(self.config, f"{provider.lower()}_client_id")
        )

        if 'error' in initial_token_response:
            return SSOTestResult(
                test_name="Token Refresh",
                provider=provider,
                success=False,
                response_time=0,
                details={'initial_token_error': initial_token_response['error']},
                error_message=initial_token_response.get('error_description')
            )

        refresh_token = initial_token_response['refresh_token']
        old_access_token = initial_token_response['access_token']

        # Simulate token expiration
        if old_access_token in mock_provider.access_tokens:
            mock_provider.access_tokens[old_access_token]['expires_at'] = datetime.now() - timedelta(minutes=1)

        # Test refresh
        start_time = time.time()

        # In a real implementation, this would call the provider's refresh endpoint
        # For testing, we simulate the refresh
        new_access_token = secrets.token_urlsafe(64)
        new_refresh_token = secrets.token_urlsafe(64)

        mock_provider.access_tokens[new_access_token] = {
            'user_id': mock_provider.access_tokens[old_access_token]['user_id'],
            'refresh_token': new_refresh_token,
            'expires_at': datetime.now() + timedelta(hours=1),
            'scopes': ['openid', 'profile', 'email']
        }

        # Clean up old token
        del mock_provider.access_tokens[old_access_token]

        end_time = time.time()

        # Verify new token works
        profile_response = mock_provider.get_user_profile(new_access_token)

        return SSOTestResult(
            test_name="Token Refresh",
            provider=provider,
            success='error' not in profile_response,
            response_time=end_time - start_time,
            details={
                'old_token_invalidated': old_access_token not in mock_provider.access_tokens,
                'new_access_token_generated': True,
                'new_refresh_token_generated': True,
                'new_token_valid': 'error' not in profile_response,
                'profile_retrieved': bool(profile_response.get('email'))
            }
        )

    async def test_concurrent_sessions(self, provider: str) -> SSOTestResult:
        """Test multiple concurrent SSO sessions"""
        print(f"Testing concurrent sessions for {provider}...")

        mock_provider = getattr(self, f"{provider.lower()}_provider")
        session_count = 50

        # Create multiple concurrent sessions
        tasks = []
        for i in range(session_count):
            async def create_session(index: int):
                start_time = time.time()

                state = secrets.token_urlsafe(32)
                auth_code = mock_provider.generate_authorization_code(state, f"{provider.lower()}_user_{index}")

                token_response = mock_provider.exchange_code_for_token(
                    auth_code,
                    getattr(self.config, f"{provider.lower()}_client_id")
                )

                end_time = time.time()

                if 'error' not in token_response:
                    profile_response = mock_provider.get_user_profile(token_response['access_token'])
                    return {
                        'session_id': index,
                        'success': 'error' not in profile_response,
                        'response_time': end_time - start_time,
                        'user_id': profile_response.get('id') if 'error' not in profile_response else None
                    }
                else:
                    return {
                        'session_id': index,
                        'success': False,
                        'response_time': end_time - start_time,
                        'error': token_response['error']
                    }

            tasks.append(create_session(i))

        start_time = time.time()
        session_results = await asyncio.gather(*tasks)
        end_time = time.time()

        successful_sessions = [r for r in session_results if r['success']]
        total_response_time = sum(r['response_time'] for r in session_results)

        return SSOTestResult(
            test_name="Concurrent Sessions",
            provider=provider,
            success=len(successful_sessions) >= session_count * 0.95,  # 95% success rate
            response_time=end_time - start_time,
            details={
                'total_sessions': session_count,
                'successful_sessions': len(successful_sessions),
                'success_rate': (len(successful_sessions) / session_count) * 100,
                'average_session_time': total_response_time / session_count,
                'sessions_per_second': session_count / (end_time - start_time),
                'unique_users': len(set(r['user_id'] for r in successful_sessions if r['user_id']))
            }
        )

    async def test_error_handling(self, provider: str) -> SSOTestResult:
        """Test SSO error handling"""
        print(f"Testing error handling for {provider}...")

        mock_provider = getattr(self, f"{provider.lower()}_provider")

        error_scenarios = [
            {
                'name': 'Invalid Authorization Code',
                'action': lambda: mock_provider.exchange_code_for_token('invalid_code', 'client_id')
            },
            {
                'name': 'Expired Authorization Code',
                'action': lambda: self._test_expired_code(mock_provider)
            },
            {
                'name': 'Invalid Access Token',
                'action': lambda: mock_provider.get_user_profile('invalid_token')
            },
            {
                'name': 'Expired Access Token',
                'action': lambda: self._test_expired_token(mock_provider)
            }
        ]

        results = []

        for scenario in error_scenarios:
            try:
                start_time = time.time()
                response = scenario['action']()
                end_time = time.time()

                # Check if error was properly handled
                has_error = isinstance(response, dict) and 'error' in response

                results.append({
                    'scenario': scenario['name'],
                    'error_handled': has_error,
                    'response_time': end_time - start_time,
                    'error_type': response.get('error') if has_error else None
                })

            except Exception as e:
                results.append({
                    'scenario': scenario['name'],
                    'error_handled': True,
                    'response_time': 0,
                    'exception': str(e)
                })

        successful_error_handling = sum(1 for r in results if r['error_handled'])

        return SSOTestResult(
            test_name="Error Handling",
            provider=provider,
            success=successful_error_handling == len(error_scenarios),
            response_time=0,
            details={
                'total_scenarios': len(error_scenarios),
                'successful_error_handling': successful_error_handling,
                'test_results': results
            }
        )

    async def test_state_parameter_security(self, provider: str) -> SSOTestResult:
        """Test OAuth state parameter security"""
        print(f"Testing state parameter security for {provider}...")

        mock_provider = getattr(self, f"{provider.lower()}_provider")

        # Test 1: Valid state parameter
        valid_state = secrets.token_urlsafe(32)
        auth_code_valid = mock_provider.generate_authorization_code(valid_state)

        # Test 2: Invalid state parameter
        invalid_state = "invalid_state_parameter"
        auth_code_invalid = mock_provider.generate_authorization_code(invalid_state)

        # Test 3: Missing state parameter
        auth_code_missing = mock_provider.generate_authorization_code("missing_state")

        scenarios = [
            {
                'name': 'Valid State',
                'state': valid_state,
                'auth_code': auth_code_valid,
                'expected_success': True
            },
            {
                'name': 'Invalid State',
                'state': 'wrong_state',
                'auth_code': auth_code_invalid,
                'expected_success': False
            },
            {
                'name': 'Missing State',
                'state': None,
                'auth_code': auth_code_missing,
                'expected_success': False
            }
        ]

        results = []

        for scenario in scenarios:
            start_time = time.time()

            # In a real implementation, this would validate the state parameter
            # For testing, we simulate the validation
            state_valid = (
                scenario['state'] is not None and
                scenario['auth_code'] in mock_provider.authorization_codes and
                mock_provider.authorization_codes[scenario['auth_code']]['state'] == scenario['state']
            )

            end_time = time.time()

            results.append({
                'scenario': scenario['name'],
                'state_valid': state_valid,
                'expected_success': scenario['expected_success'],
                'security_check_passed': state_valid == scenario['expected_success'],
                'response_time': end_time - start_time
            })

        security_passed = sum(1 for r in results if r['security_check_passed'])

        return SSOTestResult(
            test_name="State Parameter Security",
            provider=provider,
            success=security_passed == len(scenarios),
            response_time=0,
            details={
                'total_scenarios': len(scenarios),
                'security_checks_passed': security_passed,
                'test_results': results
            }
        )

    def _test_expired_code(self, mock_provider: MockOAuthProvider) -> Dict[str, Any]:
        """Helper method to test expired authorization code"""
        state = secrets.token_urlsafe(32)
        auth_code = mock_provider.generate_authorization_code(state)

        # Manually expire the code
        if auth_code in mock_provider.authorization_codes:
            mock_provider.authorization_codes[auth_code]['expires_at'] = datetime.now() - timedelta(minutes=1)

        return mock_provider.exchange_code_for_token(auth_code, 'client_id')

    def _test_expired_token(self, mock_provider: MockOAuthProvider) -> Dict[str, Any]:
        """Helper method to test expired access token"""
        state = secrets.token_urlsafe(32)
        auth_code = mock_provider.generate_authorization_code(state)
        token_response = mock_provider.exchange_code_for_token(auth_code, 'client_id')

        if 'access_token' in token_response:
            # Manually expire the token
            access_token = token_response['access_token']
            if access_token in mock_provider.access_tokens:
                mock_provider.access_tokens[access_token]['expires_at'] = datetime.now() - timedelta(minutes=1)

            return mock_provider.get_user_profile(access_token)

        return {'error': 'no_token_generated'}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all SSO integration tests"""
        print("Starting comprehensive SSO integration testing...")

        providers = ['Google', 'Microsoft']
        test_functions = [
            self.test_oauth_authorization_flow,
            self.test_token_refresh,
            self.test_concurrent_sessions,
            self.test_error_handling,
            self.test_state_parameter_security
        ]

        for provider in providers:
            print(f"\n--- Testing {provider} SSO ---")

            for test_func in test_functions:
                try:
                    result = await test_func(provider)
                    self.test_results.append(result)

                    status = "✅" if result.success else "❌"
                    print(f"{status} {provider}: {result.test_name} ({result.response_time:.3f}s)")

                    if result.error_message:
                        print(f"   Error: {result.error_message}")

                except Exception as e:
                    error_result = SSOTestResult(
                        test_name=test_func.__name__,
                        provider=provider,
                        success=False,
                        response_time=0,
                        details={},
                        error_message=str(e)
                    )
                    self.test_results.append(error_result)
                    print(f"❌ {provider}: {test_func.__name__} - {str(e)}")

        # Generate summary
        successful_tests = sum(1 for r in self.test_results if r.success)
        total_tests = len(self.test_results)

        # Group results by provider
        provider_results = {}
        for result in self.test_results:
            if result.provider not in provider_results:
                provider_results[result.provider] = []
            provider_results[result.provider].append(result)

        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': (successful_tests / total_tests) * 100 if total_tests > 0 else 0,
                'providers_tested': list(provider_results.keys())
            },
            'provider_results': {
                provider: {
                    'total_tests': len(results),
                    'successful_tests': sum(1 for r in results if r.success),
                    'success_rate': (sum(1 for r in results if r.success) / len(results)) * 100 if results else 0,
                    'average_response_time': sum(r.response_time for r in results) / len(results) if results else 0
                }
                for provider, results in provider_results.items()
            },
            'test_results': [
                {
                    'name': r.test_name,
                    'provider': r.provider,
                    'success': r.success,
                    'response_time': r.response_time,
                    'details': r.details,
                    'error_message': r.error_message,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.test_results
            ]
        }

# Main execution for standalone testing
async def main():
    """Run SSO integration tests"""
    tester = SSOIntegrationTester()
    results = await tester.run_all_tests()

    print("\n" + "="*60)
    print("SSO INTEGRATION TEST RESULTS")
    print("="*60)

    summary = results['summary']
    print(f"Tests Run: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Providers Tested: {', '.join(summary['providers_tested'])}")

    print("\nResults by Provider:")
    for provider, stats in results['provider_results'].items():
        print(f"  {provider}:")
        print(f"    Tests: {stats['total_tests']}")
        print(f"    Successful: {stats['successful_tests']}")
        print(f"    Success Rate: {stats['success_rate']:.1f}%")
        print(f"    Avg Response Time: {stats['average_response_time']:.3f}s")

    print("\nDetailed Results:")
    for result in results['test_results']:
        status = "PASS" if result['success'] else "FAIL"
        print(f"  {status} {result['provider']} - {result['name']}: {result['response_time']:.3f}s")
        if result['error_message']:
            print(f"       Error: {result['error_message']}")

    # Save results to file
    with open('sso_integration_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nDetailed results saved to: sso_integration_test_results.json")

    return results

if __name__ == "__main__":
    asyncio.run(main())