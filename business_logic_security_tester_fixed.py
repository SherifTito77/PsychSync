#!/usr/bin/env python3
"""
Business Logic Security Tester (Fixed)
Tests for common business logic vulnerabilities in web applications
"""

import requests
import json
import time
import random
import string
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Represents the result of a security test"""
    test_name: str
    vulnerability_found: bool
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    timestamp: str

class BusinessLogicSecurityTester:
    def __init__(self, base_url: str, session: requests.Session = None):
        self.base_url = base_url.rstrip('/')
        self.session = session or requests.Session()
        self.results: List[TestResult] = []
        self.authenticated_user = None
        self.test_users = {}

    def add_result(self, test_name: str, vulnerability_found: bool, severity: str,
                   description: str, evidence: Dict[str, Any], recommendation: str):
        """Add a test result to the results list"""
        result = TestResult(
            test_name=test_name,
            vulnerability_found=vulnerability_found,
            severity=severity,
            description=description,
            evidence=evidence,
            recommendation=recommendation,
            timestamp=datetime.now().isoformat()
        )
        self.results.append(result)

        if vulnerability_found:
            logger.warning(f"🚨 VULNERABILITY FOUND: {test_name} - {description}")
        else:
            logger.info(f"✅ Test passed: {test_name}")

    def create_test_user(self, email: str, password: str) -> Dict[str, Any]:
        """Create a test user for testing purposes"""
        try:
            # Generate random user data
            username = ''.join(random.choices(string.ascii_lowercase, k=8))

            user_data = {
                'email': email,
                'password': password,
                'username': username,
                'first_name': f'Test_{username}',
                'last_name': 'User'
            }

            # Attempt to register user
            response = self.session.post(f"{self.base_url}/api/v1/auth/register", json=user_data)

            if response.status_code in [200, 201]:
                logger.info(f"Created test user: {email}")
                return {'success': True, 'data': user_data, 'response': response.json()}
            else:
                logger.warning(f"Failed to create test user {email}: {response.status_code}")
                return {'success': False, 'status_code': response.status_code, 'response': response.text}

        except Exception as e:
            logger.error(f"Error creating test user: {e}")
            return {'success': False, 'error': str(e)}

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and store session"""
        try:
            auth_data = {'email': email, 'password': password}
            response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=auth_data)

            if response.status_code == 200:
                auth_response = response.json()
                if 'access_token' in auth_response:
                    self.session.headers.update({
                        'Authorization': f"Bearer {auth_response['access_token']}"
                    })
                    self.authenticated_user = auth_response
                    logger.info(f"Successfully authenticated user: {email}")
                    return {'success': True, 'user_data': auth_response}

            logger.warning(f"Authentication failed for {email}: {response.status_code}")
            return {'success': False, 'status_code': response.status_code, 'response': response.text}

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return {'success': False, 'error': str(e)}

    def test_payment_bypass(self) -> None:
        """Test for payment bypass vulnerabilities"""
        logger.info("🔍 Testing payment bypass vulnerabilities...")

        test_scenarios = [
            {
                'name': 'Direct Premium Feature Access',
                'method': 'GET',
                'endpoint': '/api/v1/premium/features',
                'description': 'Attempt to access premium features without payment'
            },
            {
                'name': 'Premium Report Generation',
                'method': 'POST',
                'endpoint': '/api/v1/reports/generate',
                'data': {'report_type': 'premium', 'format': 'pdf'},
                'description': 'Attempt to generate premium reports without subscription'
            },
            {
                'name': 'API Rate Limit Bypass',
                'method': 'GET',
                'endpoint': '/api/v1/premium/analytics',
                'description': 'Test if premium API endpoints are properly protected'
            }
        ]

        for scenario in test_scenarios:
            try:
                endpoint_url = f"{self.base_url}{scenario['endpoint']}"
                if scenario['method'] == 'GET':
                    response = self.session.get(endpoint_url)
                else:
                    response = self.session.post(endpoint_url, json=scenario.get('data', {}))

                # Check if premium content is accessible without payment
                vulnerability_found = response.status_code in [200, 201]

                self.add_result(
                    test_name=scenario['name'],
                    vulnerability_found=vulnerability_found,
                    severity='HIGH' if vulnerability_found else 'LOW',
                    description=scenario['description'],
                    evidence={
                        'endpoint': scenario['endpoint'],
                        'method': scenario['method'],
                        'status_code': response.status_code,
                        'response_preview': response.text[:500] if response.text else None
                    },
                    recommendation="Implement proper payment verification middleware for premium features"
                )

            except Exception as e:
                logger.error(f"Error testing {scenario['name']}: {e}")
                self.add_result(
                    test_name=f"ERROR - {scenario['name']}",
                    vulnerability_found=True,
                    severity='MEDIUM',
                    description=f"Error during test suggests potential security issue",
                    evidence={'error': str(e)},
                    recommendation="Review endpoint security and error handling"
                )

    def test_authorization_bypass(self) -> None:
        """Test for authorization and permission bypass vulnerabilities"""
        logger.info("🔍 Testing authorization bypass vulnerabilities...")

        # Create test users with different roles
        test_user_1 = self.create_test_user("test1@example.com", "password123")
        test_user_2 = self.create_test_user("test2@example.com", "password456")

        if test_user_1['success'] and test_user_2['success']:
            # Authenticate as first user
            self.authenticate_user("test1@example.com", "password123")

            test_scenarios = [
                {
                    'name': 'Cross-User Report Access',
                    'method': 'GET',
                    'endpoint': '/api/v1/reports/999999',  # Try to access non-existent report
                    'description': 'Attempt to access reports from other users'
                },
                {
                    'name': 'Admin Endpoint Access',
                    'method': 'GET',
                    'endpoint': '/api/v1/admin/users',
                    'description': 'Attempt to access admin-only endpoints'
                },
                {
                    'name': 'Team Data Access',
                    'method': 'GET',
                    'endpoint': '/api/v1/teams/999999/members',  # Try to access other team data
                    'description': 'Attempt to access team data without membership'
                }
            ]

            for scenario in test_scenarios:
                try:
                    endpoint_url = f"{self.base_url}{scenario['endpoint']}"
                    response = self.session.get(endpoint_url)

                    # Check if unauthorized access is possible
                    vulnerability_found = response.status_code in [200, 201]

                    self.add_result(
                        test_name=scenario['name'],
                        vulnerability_found=vulnerability_found,
                        severity='HIGH' if vulnerability_found else 'LOW',
                        description=scenario['description'],
                        evidence={
                            'endpoint': scenario['endpoint'],
                            'status_code': response.status_code,
                            'response_size': len(response.text)
                        },
                        recommendation="Implement proper role-based access control (RBAC)"
                    )

                except Exception as e:
                    logger.error(f"Error testing {scenario['name']}: {e}")

    def test_deleted_account_access(self) -> None:
        """Test if deleted accounts can still access content"""
        logger.info("🔍 Testing deleted account access vulnerabilities...")

        # Create and authenticate a user
        test_user = self.create_test_user("deletetest@example.com", "password789")

        if test_user['success']:
            # Authenticate the user
            auth_result = self.authenticate_user("deletetest@example.com", "password789")

            if auth_result['success']:
                # Store session token
                session_token = self.session.headers.get('Authorization')

                # Attempt to delete account (if endpoint exists)
                try:
                    delete_response = self.session.delete(f"{self.base_url}/api/v1/users/me")

                    # Try to access content with deleted account token
                    test_endpoints = [
                        '/api/v1/users/me',
                        '/api/v1/assessments',
                        '/api/v1/reports'
                    ]

                    for endpoint in test_endpoints:
                        try:
                            endpoint_url = f"{self.base_url}{endpoint}"
                            access_response = self.session.get(endpoint_url)

                            # Check if deleted account can still access content
                            vulnerability_found = access_response.status_code in [200, 201]

                            self.add_result(
                                test_name=f'Deleted Account Access - {endpoint}',
                                vulnerability_found=vulnerability_found,
                                severity='CRITICAL' if vulnerability_found else 'LOW',
                                description=f'Deleted account can still access {endpoint}',
                                evidence={
                                    'endpoint': endpoint,
                                    'status_code': access_response.status_code,
                                    'delete_response': delete_response.status_code
                                },
                                recommendation="Implement proper account deletion and session invalidation"
                            )

                        except Exception as e:
                            logger.error(f"Error testing deleted account access to {endpoint}: {e}")

                except Exception as e:
                    logger.error(f"Error during account deletion test: {e}")

    def test_data_cloning_attacks(self) -> None:
        """Test for data cloning and indirect data access vulnerabilities"""
        logger.info("🔍 Testing data cloning attack vulnerabilities...")

        test_scenarios = [
            {
                'name': 'Data Export API Bypass',
                'method': 'POST',
                'endpoint': '/api/v1/data/export',
                'data': {'format': 'json', 'scope': 'all'},
                'description': 'Attempt to export data without proper authorization'
            },
            {
                'name': 'Bulk Data Access',
                'method': 'GET',
                'endpoint': '/api/v1/data/all',
                'description': 'Attempt to access bulk data that should be restricted'
            },
            {
                'name': 'Template Cloning',
                'method': 'POST',
                'endpoint': '/api/v1/templates/clone/999999',  # Try to clone non-existent template
                'description': 'Attempt to clone templates without proper authorization'
            }
        ]

        for scenario in test_scenarios:
            try:
                endpoint_url = f"{self.base_url}{scenario['endpoint']}"
                if scenario['method'] == 'GET':
                    response = self.session.get(endpoint_url)
                else:
                    response = self.session.post(endpoint_url, json=scenario.get('data', {}))

                # Check if data can be accessed/cloned inappropriately
                vulnerability_found = response.status_code in [200, 201]

                self.add_result(
                    test_name=scenario['name'],
                    vulnerability_found=vulnerability_found,
                    severity='HIGH' if vulnerability_found else 'LOW',
                    description=scenario['description'],
                    evidence={
                        'endpoint': scenario['endpoint'],
                        'status_code': response.status_code,
                        'response_data_size': len(response.text) if response.text else 0
                    },
                    recommendation="Implement proper data access controls and audit logging"
                )

            except Exception as e:
                logger.error(f"Error testing {scenario['name']}: {e}")

    def test_team_limits_bypass(self) -> None:
        """Test for team limits bypass via bulk operations"""
        logger.info("🔍 Testing team limits bypass vulnerabilities...")

        # Create test team if possible
        try:
            team_data = {
                'name': 'Test Security Team',
                'description': 'Team for security testing'
            }

            create_team_response = self.session.post(f"{self.base_url}/api/v1/teams", json=team_data)

            if create_team_response.status_code in [200, 201]:
                team_id = create_team_response.json().get('id')

                # Test bulk operations to bypass team limits
                bulk_scenarios = [
                    {
                        'name': 'Bulk Member Addition',
                        'method': 'POST',
                        'endpoint': f'/api/v1/teams/{team_id}/members/bulk',
                        'data': {
                            'members': [
                                {'email': f'member{i}@test.com', 'role': 'member'}
                                for i in range(100)  # Try to add 100 members at once
                            ]
                        },
                        'description': 'Attempt to bypass team member limits via bulk upload'
                    },
                    {
                        'name': 'Bulk Assessment Creation',
                        'method': 'POST',
                        'endpoint': f'/api/v1/teams/{team_id}/assessments/bulk',
                        'data': {
                            'assessments': [
                                {'title': f'Bulk Test {i}', 'type': 'survey'}
                                for i in range(50)  # Try to create 50 assessments at once
                            ]
                        },
                        'description': 'Attempt to bypass assessment limits via bulk creation'
                    }
                ]

                for scenario in bulk_scenarios:
                    try:
                        endpoint_url = f"{self.base_url}{scenario['endpoint']}"
                        response = self.session.post(endpoint_url, json=scenario.get('data', {}))

                        # Check if limits can be bypassed
                        vulnerability_found = response.status_code in [200, 201]

                        self.add_result(
                            test_name=scenario['name'],
                            vulnerability_found=vulnerability_found,
                            severity='MEDIUM' if vulnerability_found else 'LOW',
                            description=scenario['description'],
                            evidence={
                                'endpoint': scenario['endpoint'],
                                'status_code': response.status_code,
                                'bulk_size': len(scenario['data'].get('members', scenario['data'].get('assessments', [])))
                            },
                            recommendation="Implement proper rate limiting and quota enforcement for bulk operations"
                        )

                    except Exception as e:
                        logger.error(f"Error testing {scenario['name']}: {e}")
            else:
                logger.warning("Could not create test team for limits testing")

        except Exception as e:
            logger.error(f"Error in team limits testing: {e}")

    def run_all_tests(self) -> None:
        """Run all business logic security tests"""
        logger.info("🚀 Starting comprehensive business logic security testing...")

        # Create and authenticate a test user
        test_user = self.create_test_user("securitytest@example.com", "password123")
        if test_user['success']:
            self.authenticate_user("securitytest@example.com", "password123")

        # Run all test modules
        self.test_payment_bypass()
        self.test_authorization_bypass()
        self.test_deleted_account_access()
        self.test_data_cloning_attacks()
        self.test_team_limits_bypass()

        logger.info(f"✅ Security testing completed. Found {len([r for r in self.results if r.vulnerability_found])} potential vulnerabilities")

    def generate_report(self, save_to_file: bool = True) -> str:
        """Generate a comprehensive security report"""
        report = []
        report.append("# Business Logic Security Assessment Report")
        report.append(f"**Target:** {self.base_url}")
        report.append(f"**Assessment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Total Tests:** {len(self.results)}")
        report.append("")

        # Executive Summary
        vulnerabilities = [r for r in self.results if r.vulnerability_found]
        critical_vulns = [r for r in vulnerabilities if r.severity == 'CRITICAL']
        high_vulns = [r for r in vulnerabilities if r.severity == 'HIGH']

        report.append("## Executive Summary")
        report.append(f"- **Total Vulnerabilities Found:** {len(vulnerabilities)}")
        report.append(f"- **Critical:** {len(critical_vulns)}")
        report.append(f"- **High:** {len(high_vulns)}")
        report.append(f"- **Overall Risk Level:** {'CRITICAL' if critical_vulns else 'HIGH' if high_vulns else 'MEDIUM' if vulnerabilities else 'LOW'}")
        report.append("")

        # Detailed Findings
        report.append("## Detailed Findings")

        for result in self.results:
            if result.vulnerability_found:
                status_emoji = "🚨"
            else:
                status_emoji = "✅"

            report.append(f"### {status_emoji} {result.test_name}")
            report.append(f"**Severity:** {result.severity}")
            report.append(f"**Description:** {result.description}")
            report.append(f"**Evidence:** ```json\n{json.dumps(result.evidence, indent=2)}\n```")
            report.append(f"**Recommendation:** {result.recommendation}")
            report.append("")

        # Summary Table
        report.append("## Test Summary Table")
        report.append("| Test Name | Status | Severity | Description |")
        report.append("|-----------|--------|----------|-------------|")

        for result in self.results:
            status = "VULNERABLE" if result.vulnerability_found else "PASSED"
            severity = result.severity
            description = result.description[:50] + "..." if len(result.description) > 50 else result.description
            report.append(f"| {result.test_name} | {status} | {severity} | {description} |")

        report_text = "\n".join(report)

        if save_to_file:
            filename = f"business_logic_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w') as f:
                f.write(report_text)
            logger.info(f"📄 Security report saved to: {filename}")

        return report_text

def main():
    """Main execution function"""
    print("🔒 Business Logic Security Tester")
    print("=" * 50)

    # Configuration
    base_url = input("Enter target URL (e.g., http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"

    # Create tester instance
    tester = BusinessLogicSecurityTester(base_url)

    try:
        # Run all tests
        tester.run_all_tests()

        # Generate report
        report = tester.generate_report()

        # Print summary
        print("\n" + "=" * 50)
        print("🏁 Security Assessment Complete")
        print("=" * 50)

        vulnerabilities = [r for r in tester.results if r.vulnerability_found]
        print(f"Vulnerabilities Found: {len(vulnerabilities)}")

        if vulnerabilities:
            print("\n🚨 Critical Issues Found:")
            for vuln in vulnerabilities:
                if vuln.severity in ['CRITICAL', 'HIGH']:
                    print(f"  • {vuln.test_name}: {vuln.description}")
        else:
            print("✅ No critical business logic vulnerabilities detected")

    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()