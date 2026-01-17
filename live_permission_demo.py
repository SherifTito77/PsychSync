#!/usr/bin/env python3
"""
Live Permission System Demo
==========================

Real-time demonstration of how admin vs normal users experience different access
when trying to access the same endpoints in the PsychSync platform.
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional

class LivePermissionDemo:
    """Live demo showing real permission enforcement in action"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []

    async def run_live_demo(self):
        """Run live permission demonstration"""
        print("🔐 LIVE PERMISSION SYSTEM DEMONSTRATION")
        print("=" * 70)
        print("Real-time testing of how different user roles access the same endpoints")
        print("=" * 70)

        # Simulate realistic API requests
        test_scenarios = [
            {
                "name": "Health Check (Public Endpoint)",
                "endpoint": "/api/v1/health",
                "description": "Basic health check - accessible to everyone",
                "admin_expected": "SUCCESS",
                "user_expected": "SUCCESS"
            },
            {
                "name": "User Profile (Self Access)",
                "endpoint": "/api/v1/users/me",
                "description": "Users accessing their own profile data",
                "admin_expected": "SUCCESS",
                "user_expected": "SUCCESS"
            },
            {
                "name": "All Users List (Admin Only)",
                "endpoint": "/api/v1/users",
                "description": "Listing all users in the system",
                "admin_expected": "SUCCESS",
                "user_expected": "FORBIDDEN"
            },
            {
                "name": "Organization Management",
                "endpoint": "/api/v1/organizations",
                "description": "Organization settings and management",
                "admin_expected": "SUCCESS",
                "user_expected": "FORBIDDEN"
            },
            {
                "name": "Team Management",
                "endpoint": "/api/v1/teams",
                "description": "Team creation and management",
                "admin_expected": "SUCCESS",
                "user_expected": "LIMITED"
            }
        ]

        # Create mock authentication headers
        admin_headers = {"Authorization": "Bearer admin_token_12345", "Content-Type": "application/json"}
        user_headers = {"Authorization": "Bearer user_token_67890", "Content-Type": "application/json"}

        print(f"\n🚀 EXECUTING LIVE PERMISSION TESTS")
        print(f"Testing {len(test_scenarios)} endpoint scenarios")
        print("-" * 70)

        # Test as Admin user
        print("\n👑 TESTING AS ADMIN USER")
        print("-" * 40)

        for scenario in test_scenarios:
            result = await self.test_with_headers(admin_headers, scenario, "ADMIN")
            self.test_results.append(result)
            self._print_result(result)

        # Test as Normal user
        print("\n👤 TESTING AS NORMAL USER")
        print("-" * 40)

        for scenario in test_scenarios:
            result = await self.test_with_headers(user_headers, scenario, "USER")
            self.test_results.append(result)
            self._print_result(result)

        # Generate comparison
        self._generate_permission_comparison(test_scenarios)

        # Show security metrics
        self._show_security_metrics()

        return self.test_results

    async def test_with_headers(self, headers: Dict[str, str], scenario: Dict[str, Any],
                               user_type: str) -> Dict[str, Any]:
        """Test endpoint with specific authentication headers"""
        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}{scenario['endpoint']}",
                    headers=headers
                )

            response_time = (time.time() - start_time) * 1000

            # Parse response
            try:
                response_data = response.json() if response.content else None
            except:
                response_data = response.text[:200] if response.text else None

            # Determine if result matches expectations
            expected = scenario.get(f"{user_type.lower()}_expected", "UNKNOWN")
            expectation_met = self._check_expectation(response.status_code, expected)

            return {
                "user_type": user_type,
                "scenario_name": scenario['name'],
                "endpoint": scenario['endpoint'],
                "status_code": response.status_code,
                "response_time_ms": response_time,
                "response_data": response_data,
                "expected": expected,
                "expectation_met": expectation_met,
                "description": scenario['description'],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "user_type": user_type,
                "scenario_name": scenario['name'],
                "endpoint": scenario['endpoint'],
                "status_code": 0,
                "response_time_ms": 0,
                "response_data": None,
                "expected": scenario.get(f"{user_type.lower()}_expected", "UNKNOWN"),
                "expectation_met": False,
                "description": scenario['description'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _check_expectation(self, status_code: int, expected: str) -> bool:
        """Check if the response matches expected outcome"""
        if expected == "SUCCESS" and status_code == 200:
            return True
        elif expected == "FORBIDDEN" and status_code in [401, 403]:
            return True
        elif expected == "LIMITED" and status_code == 200:
            return True
        elif expected == "UNKNOWN":
            return True
        return False

    def _print_result(self, result: Dict[str, Any]) -> None:
        """Print formatted test result"""
        if result.get("error"):
            print(f"   ❌ {result['scenario_name']}")
            print(f"      🌐 {result['endpoint']}")
            print(f"      ⚠️  Error: {result['error']}")
        else:
            status_icon = "✅" if result['expectation_met'] else "⚠️"
            print(f"   {status_icon} {result['scenario_name']}")
            print(f"      🌐 {result['endpoint']}")
            print(f"      📊 Status: {result['status_code']}")
            print(f"      ⏱️  Time: {result['response_time_ms']:.1f}ms")
            print(f"      📋 Expected: {result['expected']}")

            if result['response_data']:
                data_preview = str(result['response_data'])[:100]
                print(f"      📄 Response: {data_preview}{'...' if len(str(result['response_data'])) > 100 else ''}")

        print()

    def _generate_permission_comparison(self, scenarios: List[Dict[str, Any]]) -> None:
        """Generate side-by-side comparison of permissions"""
        print("📊 SIDE-BY-SIDE PERMISSION COMPARISON")
        print("=" * 70)

        print(f"{'Endpoint':<30} {'Admin':<8} {'Normal User':<12} {'Description'}")
        print("-" * 70)

        for scenario in scenarios:
            admin_result = self._find_result("ADMIN", scenario['name'])
            user_result = self._find_result("USER", scenario['name'])

            admin_status = "✅" if admin_result and admin_result['expectation_met'] else "❌"
            user_status = "✅" if user_result and user_result['expectation_met'] else "❌"

            # Truncate description to fit
            desc = scenario['description'][:25] + "..." if len(scenario['description']) > 25 else scenario['description']

            print(f"{scenario['name'][:30]:<30} {admin_status:<8} {user_status:<12} {desc}")

    def _show_security_metrics(self) -> None:
        """Display security and performance metrics"""
        print("\n📈 SECURITY & PERFORMANCE ANALYSIS")
        print("=" * 70)

        if not self.test_results:
            print("No test results available")
            return

        # Calculate metrics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['expectation_met'])
        admin_tests = [r for r in self.test_results if r['user_type'] == 'ADMIN']
        user_tests = [r for r in self.test_results if r['user_type'] == 'USER']

        admin_success = sum(1 for r in admin_tests if r['expectation_met'])
        user_success = sum(1 for r in user_tests if r['expectation_met'])

        # Performance metrics
        response_times = [r['response_time_ms'] for r in self.test_results if r['response_time_ms'] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        print(f"🔐 SECURITY VALIDATION")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Security Compliant: {successful_tests}/{total_tests}")
        print(f"   • Compliance Rate: {(successful_tests/total_tests*100):.1f}%")

        print(f"\n👤 USER TYPE PERFORMANCE")
        print(f"   • Admin Tests: {admin_success}/{len(admin_tests)} ({(admin_success/len(admin_tests)*100):.1f}%)")
        print(f"   • User Tests: {user_success}/{len(user_tests)} ({(user_success/len(user_tests)*100):.1f}%)")

        if response_times:
            print(f"\n⚡ PERFORMANCE METRICS")
            print(f"   • Average Response Time: {avg_response_time:.1f}ms")
            print(f"   • Fastest Response: {min(response_times):.1f}ms")
            print(f"   • Slowest Response: {max(response_times):.1f}ms")

        # Security analysis
        admin_only_endpoints = self._find_admin_only_endpoints()
        if admin_only_endpoints:
            print(f"\n🔒 ADMIN-ONLY ENDPOINTS")
            for endpoint in admin_only_endpoints:
                print(f"   • {endpoint}")

    def _find_result(self, user_type: str, scenario_name: str) -> Optional[Dict[str, Any]]:
        """Find test result by user type and scenario name"""
        for result in self.test_results:
            if result['user_type'] == user_type and result['scenario_name'] == scenario_name:
                return result
        return None

    def _find_admin_only_endpoints(self) -> List[str]:
        """Find endpoints that only admins should access"""
        admin_accessible = set()
        user_accessible = set()

        for result in self.test_results:
            if result['user_type'] == 'ADMIN' and result['expectation_met']:
                admin_accessible.add(result['scenario_name'])
            elif result['user_type'] == 'USER' and result['expectation_met']:
                user_accessible.add(result['scenario_name'])

        return list(admin_accessible - user_accessible)

async def main():
    """Main function to run the live demo"""
    demo = LivePermissionDemo()

    try:
        results = await demo.run_live_demo()

        # Save results to file
        report_file = f"live_permission_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Live demo results saved to: {report_file}")
        print(f"\n🎉 LIVE PERMISSION DEMONSTRATION COMPLETED")

        if all(r['expectation_met'] for r in results):
            print("✅ All permission controls working correctly!")
        else:
            print("⚠️  Some permission controls need attention")

        return results

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())
