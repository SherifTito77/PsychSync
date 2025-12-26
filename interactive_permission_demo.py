#!/usr/bin/env python3
"""
Interactive Permission System Demo
================================

Live demonstration of how the PsychSync permission system handles
admin vs normal user requests to the same endpoints.
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional

class InteractivePermissionDemo:
    """Interactive demo showing real permission enforcement"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []

    async def run_interactive_demo(self):
        """Run interactive permission demonstration"""
        print("🔐 INTERACTIVE PERMISSION SYSTEM DEMO")
        print("=" * 70)
        print("Testing real API endpoints with different user roles")
        print("=" * 70)

        # Simulate different user tokens
        test_users = {
            "admin": {
                "name": "Admin User",
                "token": "admin_token_12345",
                "role": "ADMIN",
                "permissions": ["read:all", "write:all", "delete:all", "manage:users", "manage:system"]
            },
            "normal": {
                "name": "Normal User",
                "token": "user_token_67890",
                "role": "USER",
                "permissions": ["read:own", "write:own"]
            },
            "team_lead": {
                "name": "Team Lead",
                "token": "team_lead_token_11111",
                "role": "TEAM_LEAD",
                "permissions": ["read:own", "write:own", "read:team", "manage:team"]
            }
        }

        # Test endpoints that show different behavior based on permissions
        test_endpoints = [
            {
                "name": "Health Check (Public)",
                "endpoint": "/api/v1/health",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "SUCCESS",
                "description": "Basic health check - should be accessible to all"
            },
            {
                "name": "User Profile (Self)",
                "endpoint": "/api/v1/users/me",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "SUCCESS",
                "description": "Users can always access their own profile"
            },
            {
                "name": "User List (Admin Only)",
                "endpoint": "/api/v1/users",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "FORBIDDEN",
                "description": "Only admins can list all users"
            },
            {
                "name": "Organization Settings",
                "endpoint": "/api/v1/organizations",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "FORBIDDEN",
                "description": "Organization management requires admin access"
            },
            {
                "name": "Team Management",
                "endpoint": "/api/v1/teams",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "LIMITED",
                "description": "Normal users see only their teams"
            },
            {
                "name": "System Analytics",
                "endpoint": "/api/v1/analytics",
                "method": "GET",
                "expected_admin": "SUCCESS",
                "expected_normal": "FORBIDDEN",
                "description": "System-wide analytics require admin access"
            }
        ]

        print(f"\n🚀 Starting Permission Tests")
        print(f"Test Users: {list(test_users.keys())}")
        print(f"Test Endpoints: {len(test_endpoints)}")
        print("-" * 70)

        # Run tests for each user role
        for user_type, user_info in test_users.items():
            print(f"\n👤 Testing as: {user_info['name']} ({user_info['role']})")
            print("-" * 50)

            for endpoint in test_endpoints:
                result = await self.test_endpoint_permission(
                    user_info, endpoint
                )
                self.test_results.append(result)

                # Display result
                status_icon = "✅" if result["success"] else "❌"
                print(f"   {status_icon} {endpoint['name']}")
                print(f"      🌐 {endpoint['endpoint']}")
                print(f"      📊 Status: {result['status_code']}")
                print(f"      🔍 Expected: {endpoint[f'expected_{user_type}']}")

                if result["response_data"]:
                    print(f"      📄 Response: {self._format_response_data(result['response_data'])}")

                if result["security_check"]:
                    print(f"      🔒 Security: {result['security_check']}")

                print()  # Empty line for readability

        # Generate comparative analysis
        await self._generate_comparative_analysis(test_users, test_endpoints)

        # Show security metrics
        await self._display_security_metrics()

        return self.test_results

    async def test_endpoint_permission(self, user_info: Dict[str, Any], endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific endpoint with a specific user role"""
        try:
            headers = {
                "Authorization": f"Bearer {user_info['token']}",
                "Content-Type": "application/json",
                "User-Agent": f"PermissionDemo/{user_info['role']}"
            }

            start_time = time.time()

            async with httpx.AsyncClient(timeout=10.0) as client:
                if endpoint["method"] == "GET":
                    response = await client.get(
                        f"{self.base_url}{endpoint['endpoint']}",
                        headers=headers
                    )
                else:
                    # For other methods, would implement accordingly
                    response = await client.get(
                        f"{self.base_url}{endpoint['endpoint']}",
                        headers=headers
                    )

            response_time = (time.time() - start_time) * 1000

            # Parse response
            try:
                response_data = response.json() if response.content else None
            except:
                response_data = response.text if response.text else None

            # Security check
            security_check = self._perform_security_check(
                user_info, endpoint, response.status_code, response_data
            )

            return {
                "user_role": user_info['role'],
                "user_name": user_info['name'],
                "endpoint_name": endpoint['name'],
                "endpoint_url": endpoint['endpoint'],
                "method": endpoint['method'],
                "status_code": response.status_code,
                "success": response.status_code in [200, 201],
                "response_time_ms": response_time,
                "response_data": response_data,
                "expected_result": endpoint[f"expected_{user_info['role']}"],
                "security_check": security_check,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "user_role": user_info['role'],
                "user_name": user_info['name'],
                "endpoint_name": endpoint['name'],
                "endpoint_url": endpoint['endpoint'],
                "method": endpoint['method'],
                "status_code": 0,
                "success": False,
                "response_time_ms": 0,
                "response_data": None,
                "expected_result": endpoint[f"expected_{user_info['role']}"],
                "security_check": f"Connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _format_response_data(self, data: Any) -> str:
        """Format response data for display"""
        if isinstance(data, dict):
            if len(str(data)) > 100:
                return f"{type(data).__name__} ({len(data)} keys)"
            else:
                return json.dumps(data, separators=(',', ':'))
        elif isinstance(data, str):
            if len(data) > 100:
                return f"{data[:100]}..."
            else:
                return data
        else:
            return str(data)[:100]

    def _perform_security_check(self, user_info: Dict[str, Any], endpoint: Dict[str, Any],
                               status_code: int, response_data: Any) -> str:
        """Perform security validation on the response"""
        user_role = user_info['role']
        expected = endpoint[f"expected_{user_role}']

        # Check if response matches expectations
        if expected == "SUCCESS" and status_code == 200:
            return "✅ Proper access granted"
        elif expected == "FORBIDDEN" and status_code == 403:
            return "✅ Properly blocked - 403 Forbidden"
        elif expected == "FORBIDDEN" and status_code == 401:
            return "✅ Properly blocked - 401 Unauthorized"
        elif expected == "LIMITED" and status_code == 200:
            return "✅ Limited access granted"
        else:
            return f"⚠️  Unexpected response (expected {expected}, got {status_code})"

    async def _generate_comparative_analysis(self, test_users: Dict[str, Any],
                                            test_endpoints: List[Dict[str, Any]]) -> None:
        """Generate comparative analysis of user permissions"""
        print("📊 COMPARATIVE PERMISSION ANALYSIS")
        print("=" * 70)

        # Create a table-like comparison
        print(f"{'Endpoint':<25} {'Admin':<10} {'Normal User':<12} {'Team Lead':<10}")
        print("-" * 70)

        for endpoint in test_endpoints:
            admin_result = self._find_test_result("ADMIN", endpoint['name'])
            normal_result = self._find_test_result("USER", endpoint['name'])
            team_lead_result = self._find_test_result("TEAM_LEAD", endpoint['name'])

            admin_status = "✅" if admin_result and admin_result['success'] else "❌"
            normal_status = "✅" if normal_result and normal_result['success'] else "❌"
            team_lead_status = "✅" if team_lead_result and team_lead_result['success'] else "❌"

            print(f"{endpoint['name'][:25]:<25} {admin_status:<10} {normal_status:<12} {team_lead_status:<10}")

        # Permission differences summary
        print(f"\n🔑 KEY PERMISSION DIFFERENCES")
        print("-" * 40)

        admin_only = self._find_admin_only_endpoints()
        user_accessible = self._find_user_accessible_endpoints()

        if admin_only:
            print("Admin-only endpoints:")
            for endpoint in admin_only:
                print(f"  • {endpoint}")

        if user_accessible:
            print("All user accessible endpoints:")
            for endpoint in user_accessible:
                print(f"  • {endpoint}")

    async def _display_security_metrics(self) -> None:
        """Display security and performance metrics"""
        print("\n📈 SECURITY & PERFORMANCE METRICS")
        print("=" * 70)

        # Calculate metrics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - successful_tests

        if self.test_results:
            avg_response_time = sum(r['response_time_ms'] for r in self.test_results) / len(self.test_results)
            max_response_time = max(r['response_time_ms'] for r in self.test_results)
            min_response_time = min(r['response_time_ms'] for r in self.test_results)

            print(f"Test Execution:")
            print(f"  • Total Tests: {total_tests}")
            print(f"  • Successful: {successful_tests}")
            print(f"  • Failed: {failed_tests}")
            print(f"  • Success Rate: {(successful_tests/total_tests*100):.1f}%")

            print(f"\nPerformance:")
            print(f"  • Average Response Time: {avg_response_time:.2f}ms")
            print(f"  • Maximum Response Time: {max_response_time:.2f}ms")
            print(f"  • Minimum Response Time: {min_response_time:.2f}ms")

            # Security validation
            proper_blocks = sum(1 for r in self.test_results if "Properly blocked" in str(r.get('security_check', '')))
            proper_grants = sum(1 for r in self.test_results if "Proper access granted" in str(r.get('security_check', '')))

            print(f"\nSecurity Validation:")
            print(f"  • Proper Access Granted: {proper_grants}")
            print(f"  • Proper Access Blocked: {proper_blocks}")
            print(f"  • Security Compliance: {((proper_blocks + proper_grants)/total_tests*100):.1f}%")

    def _find_test_result(self, role: str, endpoint_name: str) -> Optional[Dict[str, Any]]:
        """Find test result by role and endpoint name"""
        for result in self.test_results:
            if result['user_role'] == role and result['endpoint_name'] == endpoint_name:
                return result
        return None

    def _find_admin_only_endpoints(self) -> List[str]:
        """Find endpoints that only admins can access"""
        admin_accessible = set()
        normal_accessible = set()

        for result in self.test_results:
            if result['user_role'] == 'ADMIN' and result['success']:
                admin_accessible.add(result['endpoint_name'])
            elif result['user_role'] == 'USER' and result['success']:
                normal_accessible.add(result['endpoint_name'])

        return list(admin_accessible - normal_accessible)

    def _find_user_accessible_endpoints(self) -> List[str]:
        """Find endpoints that all users can access"""
        accessible_by_all = set()

        # Group results by endpoint
        endpoint_results = {}
        for result in self.test_results:
            if result['endpoint_name'] not in endpoint_results:
                endpoint_results[result['endpoint_name']] = []
            endpoint_results[result['endpoint_name']].append(result)

        for endpoint_name, results in endpoint_results.items():
            if all(r['success'] for r in results):
                accessible_by_all.add(endpoint_name)

        return list(accessible_by_all)

    async def save_demo_report(self) -> str:
        """Save detailed demo report"""
        report = {
            "demo_timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "successful_tests": sum(1 for r in self.test_results if r['success']),
            "test_results": self.test_results,
            "admin_only_endpoints": self._find_admin_only_endpoints(),
            "user_accessible_endpoints": self._find_user_accessible_endpoints()
        }

        report_file = f"interactive_permission_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return report_file

async def main():
    """Main function to run the interactive demo"""
    demo = InteractivePermissionDemo()

    try:
        results = await demo.run_interactive_demo()
        report_file = await demo.save_demo_report()

        print(f"\n📄 Detailed demo report saved to: {report_file}")
        print(f"\n🎉 INTERACTIVE PERMISSION DEMO COMPLETED")

        return results

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())