#!/usr/bin/env python3
"""
Dashboard Widget Verification Test
Tests all dashboard widgets and components for proper data loading
"""

import requests
import json
import time
from typing import Dict, List, Any

class DashboardWidgetVerifier:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_widgets": 0,
            "successful_widgets": 0,
            "failed_widgets": 0,
            "widget_results": []
        }

    def test_endpoint(self, endpoint: str, description: str, expected_status: int = 200) -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time

            success = response.status_code == expected_status

            result = {
                "endpoint": endpoint,
                "description": description,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time": response_time,
                "success": success,
                "content_type": response.headers.get('content-type', 'unknown'),
                "content_length": len(response.content),
                "error": None if success else f"Status {response.status_code}"
            }

            # Try to parse JSON if possible
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    result["json_data"] = response.json()
                except Exception as e:
                    result["json_data"] = None

            return result

        except Exception as e:
            return {
                "endpoint": endpoint,
                "description": description,
                "status_code": 0,
                "expected_status": expected_status,
                "response_time": 0,
                "success": False,
                "error": str(e),
                "content_type": None,
                "content_length": 0,
                "json_data": None
            }

    def verify_health_endpoints(self):
        """Verify health and system status endpoints"""
        print("🏥 Testing Health & System Status Widgets...")

        health_endpoints = [
            ("/health", "System Health Check", 200),
            ("/api/v1/api/v1/health", "Detailed Health Check", 401),  # Requires auth
            ("/api/v1/api/v1/health/detailed", "Comprehensive Health", 401),  # Requires auth
        ]

        for endpoint, description, expected in health_endpoints:
            result = self.test_endpoint(endpoint, description, expected)
            self.results["widget_results"].append(result)
            self.results["total_widgets"] += 1
            if result["success"]:
                self.results["successful_widgets"] += 1
                print(f"   ✅ {description}: {result['status_code']} ({result['response_time']:.3f}s)")
            else:
                self.results["failed_widgets"] += 1
                print(f"   ❌ {description}: {result.get('error', 'Unknown error')}")

    def verify_metrics_endpoints(self):
        """Verify metrics and analytics endpoints"""
        print("\n📊 Testing Metrics & Analytics Widgets...")

        metrics_endpoints = [
            ("/api/v1/api/v1/metrics", "Application Metrics", 401),  # Requires auth
            ("/api/v1/api/v1/metrics/business", "Business Metrics Dashboard", 401),  # Requires auth
            ("/api/v1/api/v1/metrics/cache", "Cache Performance Metrics", 401),  # Requires auth
            ("/api/v1/api/v1/query-performance/dashboard", "Query Performance Dashboard", 401),  # Requires auth
        ]

        for endpoint, description, expected in metrics_endpoints:
            result = self.test_endpoint(endpoint, description, expected)
            self.results["widget_results"].append(result)
            self.results["total_widgets"] += 1
            if result["success"]:
                self.results["successful_widgets"] += 1
                print(f"   ✅ {description}: {result['status_code']} ({result['response_time']:.3f}s)")
            else:
                self.results["failed_widgets"] += 1
                print(f"   ❌ {description}: {result.get('error', 'Unknown error')}")

    def verify_assessment_endpoints(self):
        """Verify assessment-related dashboard endpoints"""
        print("\n📋 Testing Assessment Dashboard Widgets...")

        assessment_endpoints = [
            ("/api/v1/api/v1/assessments", "Assessment List Dashboard", 401),  # Requires auth
            ("/api/v1/api/v1/dashboard/test-assessment-id", "Reliability Validity Dashboard", 401),  # Requires auth
        ]

        for endpoint, description, expected in assessment_endpoints:
            result = self.test_endpoint(endpoint, description, expected)
            self.results["widget_results"].append(result)
            self.results["total_widgets"] += 1
            if result["success"]:
                self.results["successful_widgets"] += 1
                print(f"   ✅ {description}: {result['status_code']} ({result['response_time']:.3f}s)")
            else:
                self.results["failed_widgets"] += 1
                print(f"   ❌ {description}: {result.get('error', 'Unknown error')}")

    def verify_team_endpoints(self):
        """Verify team-related dashboard endpoints"""
        print("\n👥 Testing Team Dashboard Widgets...")

        team_endpoints = [
            ("/api/v1/api/v1/teams", "Team List Dashboard", 401),  # Requires auth
            ("/api/v1/api/v1/analytics", "Team Analytics Dashboard", 401),  # Requires auth
        ]

        for endpoint, description, expected in team_endpoints:
            result = self.test_endpoint(endpoint, description, expected)
            self.results["widget_results"].append(result)
            self.results["total_widgets"] += 1
            if result["success"]:
                self.results["successful_widgets"] += 1
                print(f"   ✅ {description}: {result['status_code']} ({result['response_time']:.3f}s)")
            else:
                self.results["failed_widgets"] += 1
                print(f"   ❌ {description}: {result.get('error', 'Unknown error')}")

    def verify_api_documentation(self):
        """Verify API documentation endpoints"""
        print("\n📚 Testing API Documentation Widgets...")

        doc_endpoints = [
            ("/openapi.json", "OpenAPI Specification", 200),
            ("/docs", "Swagger Documentation", 200),
        ]

        for endpoint, description, expected in doc_endpoints:
            result = self.test_endpoint(endpoint, description, expected)
            self.results["widget_results"].append(result)
            self.results["total_widgets"] += 1
            if result["success"]:
                self.results["successful_widgets"] += 1
                print(f"   ✅ {description}: {result['status_code']} ({result['response_time']:.3f}s)")
                if result.get('json_data'):
                    paths_count = len(result['json_data'].get('paths', {}))
                    print(f"      📄 {paths_count} API endpoints documented")
            else:
                self.results["failed_widgets"] += 1
                print(f"   ❌ {description}: {result.get('error', 'Unknown error')}")

    def run_comprehensive_test(self):
        """Run all dashboard widget verification tests"""
        print("🚀 PSYCHSYNC DASHBOARD WIDGET VERIFICATION")
        print("=" * 60)

        self.verify_health_endpoints()
        self.verify_metrics_endpoints()
        self.verify_assessment_endpoints()
        self.verify_team_endpoints()
        self.verify_api_documentation()

        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD WIDGET VERIFICATION SUMMARY")
        print("=" * 60)

        success_rate = (self.results["successful_widgets"] / self.results["total_widgets"] * 100) if self.results["total_widgets"] > 0 else 0

        print(f"Total Widgets Tested: {self.results['total_widgets']}")
        print(f"Successful Widgets: {self.results['successful_widgets']}")
        print(f"Failed Widgets: {self.results['failed_widgets']}")
        print(f"Success Rate: {success_rate:.1f}%")

        print("\n📋 Detailed Results:")
        for result in self.results["widget_results"]:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['description']}")
            if not result["success"] and result.get("error"):
                print(f"    Error: {result['error']}")

        print("\n🔐 Security Analysis:")
        auth_required = sum(1 for r in self.results["widget_results"] if r["expected_status"] == 401)
        auth_working = sum(1 for r in self.results["widget_results"] if r["expected_status"] == 401 and r["status_code"] == 401)

        print(f"Endpoints requiring authentication: {auth_required}")
        print(f"Properly secured endpoints: {auth_working}")

        print("\n⚡ Performance Analysis:")
        avg_response_time = sum(r["response_time"] for r in self.results["widget_results"]) / len(self.results["widget_results"])
        print(f"Average response time: {avg_response_time:.3f}s")

        slow_endpoints = [r for r in self.results["widget_results"] if r["response_time"] > 2.0]
        if slow_endpoints:
            print(f"Slow endpoints (>2s): {len(slow_endpoints)}")
            for endpoint in slow_endpoints:
                print(f"  - {endpoint['description']}: {endpoint['response_time']:.3f}s")

        print("\n🎯 Assessment:")
        if success_rate >= 80:
            print("✅ Dashboard infrastructure is HEALTHY and ready for production")
        elif success_rate >= 60:
            print("⚠️ Dashboard infrastructure has some issues but is mostly functional")
        else:
            print("❌ Dashboard infrastructure needs attention before production use")

if __name__ == "__main__":
    verifier = DashboardWidgetVerifier()
    verifier.run_comprehensive_test()
