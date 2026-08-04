#!/usr/bin/env python3
"""
Internal API Access Control Security Tester
Tests internal API endpoints for proper access controls and restrictions
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


class InternalAPISecurityTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.test_results = []
        self.api_endpoints = []
        self.vulnerabilities = []

    def discover_api_endpoints(self) -> Dict[str, Any]:
        """Discover API endpoints from application code"""
        print("🔍 Discovering API endpoints...")

        result = {
            "test_name": "API Endpoint Discovery",
            "test_timestamp": datetime.now().isoformat(),
            "endpoints_found": [],
            "endpoint_files": [],
            "security_issues": [],
        }

        # Search for API endpoint definitions
        api_files = [
            "app/api/v1/api.py",
            "app/main.py",
            "app/api/v1/routes.py",
            "frontend/src/services/api.ts",
        ]

        endpoint_patterns = [
            r'app\.route\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'endpoint\s*:\s*["\']([^"\']+)["\']',
            r'url:\s*["\']([^"\']+)["\']',
            r'path:\s*["\']([^"\']+)["\']',
            r'"/api/([^"\']+)"',
        ]

        for api_file in api_files:
            file_path = self.base_path / api_file
            if file_path.exists():
                result["endpoint_files"].append(api_file)

                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    file_endpoints = []
                    for pattern in endpoint_patterns:
                        matches = re.findall(pattern, content)
                        file_endpoints.extend(matches)

                    # Clean and deduplicate endpoints
                    clean_endpoints = []
                    for endpoint in file_endpoints:
                        endpoint = endpoint.strip("/").strip("'").strip('"')
                        if endpoint and endpoint not in clean_endpoints:
                            clean_endpoints.append(endpoint)

                    if clean_endpoints:
                        result["endpoints_found"].extend(
                            [{"file": api_file, "endpoints": clean_endpoints}]
                        )

                    # Check for security issues
                    if "@app.route(" in content and "methods=" not in content:
                        result["security_issues"].append(
                            f"Missing HTTP method restrictions in {api_file}"
                        )

                    if "cors_origins=" in content and "*" in content:
                        result["security_issues"].append(
                            f"CORS configured to allow all origins in {api_file}"
                        )

                except Exception as e:
                    result["security_issues"].append(f"Error reading {api_file}: {e}")

        # Remove duplicates from all endpoints
        all_endpoints = []
        for file_info in result["endpoints_found"]:
            for endpoint in file_info["endpoints"]:
                if endpoint not in all_endpoints:
                    all_endpoints.append(endpoint)

        result["unique_endpoints"] = all_endpoints
        result["total_endpoints"] = len(all_endpoints)

        # Categorize endpoints
        internal_endpoints = []
        external_endpoints = []
        admin_endpoints = []

        for endpoint in all_endpoints:
            endpoint_lower = endpoint.lower()
            if any(
                keyword in endpoint_lower
                for keyword in ["admin", "config", "system", "debug", "health"]
            ):
                admin_endpoints.append(endpoint)
            elif any(
                keyword in endpoint_lower
                for keyword in ["users", "data", "internal", "manage"]
            ):
                internal_endpoints.append(endpoint)
            else:
                external_endpoints.append(endpoint)

        result["admin_endpoints"] = admin_endpoints
        result["internal_endpoints"] = internal_endpoints
        result["external_endpoints"] = external_endpoints

        result["vulnerable"] = len(result["security_issues"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["security_issues"]) > 2 else "MEDIUM"
        )

        return result

    def test_api_access_controls(self) -> Dict[str, Any]:
        """Test API access controls and restrictions"""
        print("🔍 Testing API access controls...")

        result = {
            "test_name": "API Access Controls Test",
            "test_timestamp": datetime.now().isoformat(),
            "access_tests": [],
            "vulnerabilities": [],
        }

        # Common API endpoints to test
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/",
            "/api/v1/teams/",
            "/api/v1/assessments/",
            "/api/v1/analytics/",
            "/api/v1/admin/",
            "/api/v1/health",
            "/api/v1/status",
        ]

        # Test without authentication
        unauth_test = {
            "name": "Unauthenticated Access Test",
            "description": "Test API access without authentication",
            "endpoints_tested": [],
            "vulnerable_endpoints": [],
        }

        for endpoint in test_endpoints:
            endpoint_result = {
                "endpoint": endpoint,
                "status_code": None,
                "response_data": None,
                "requires_auth": False,
                "error": None,
            }

            try:
                url = f"http://localhost:8000{endpoint}"
                response = requests.get(url, timeout=10)

                endpoint_result["status_code"] = response.status_code

                # Check if endpoint requires authentication
                if response.status_code == 401:
                    endpoint_result["requires_auth"] = True
                elif response.status_code == 200:
                    endpoint_result["requires_auth"] = False
                    endpoint_result["vulnerable"] = True
                    result["vulnerabilities"].append(
                        f"Unauthenticated access allowed: {endpoint}"
                    )

                try:
                    response_data = response.json()
                    endpoint_result["response_data"] = json.dumps(response_data)[
                        :200
                    ]  # Truncate
                except Exception as e:
                    endpoint_result["response_data"] = response.text[:200]

            except requests.exceptions.RequestException as e:
                endpoint_result["error"] = str(e)

            unauth_test["endpoints_tested"].append(endpoint_result)

        result["access_tests"].append(unauth_test)

        # Test role-based access controls
        role_test = {
            "name": "Role-Based Access Control Test",
            "description": "Test role-based access restrictions",
            "test_results": [],
        }

        # Test with fake authentication tokens
        test_scenarios = [
            {"name": "No Token", "headers": {}, "expected_status": [401, 403]},
            {
                "name": "Invalid Token",
                "headers": {"Authorization": "Bearer invalid_token"},
                "expected_status": [401, 403],
            },
            {
                "name": "Low Privilege Token",
                "headers": {"Authorization": "Bearer user_token_123"},
                "expected_status": [401, 403],
            },
        ]

        for scenario in test_scenarios:
            scenario_result = {
                "scenario": scenario["name"],
                "headers": scenario["headers"],
                "test_results": [],
            }

            for endpoint in test_endpoints:
                try:
                    url = f"http://localhost:8000{endpoint}"
                    response = requests.get(
                        url, headers=scenario["headers"], timeout=10
                    )

                    test_result = {
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "authorized": response.status_code
                        not in scenario["expected_status"],
                        "vulnerable": response.status_code
                        not in scenario["expected_status"],
                    }

                    scenario_result["test_results"].append(test_result)

                    if test_result["vulnerable"]:
                        result["vulnerabilities"].append(
                            f"Access control bypass: {endpoint} with {scenario['name']}"
                        )

                except requests.exceptions.RequestException:
                    # Connection failed - not a vulnerability
                    pass

            result["access_tests"].append(scenario_result)

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 5 else "MEDIUM"
        )

        return result

    def test_internal_api_exposure(self) -> Dict[str, Any]:
        """Test for internal API exposure to external networks"""
        print("🔍 Testing internal API exposure...")

        result = {
            "test_name": "Internal API Exposure Test",
            "test_timestamp": datetime.now().isoformat(),
            "exposure_tests": [],
            "vulnerabilities": [],
        }

        # Check if internal endpoints are accessible from localhost
        internal_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/config",
            "/api/v1/system/status",
            "/api/v1/debug/info",
            "/api/v1/health/internal",
            "/api/v1/logs/system",
        ]

        for endpoint in internal_endpoints:
            exposure_result = {
                "endpoint": endpoint,
                "accessible": False,
                "response_data": None,
                "security_measures": [],
            }

            try:
                url = f"http://localhost:8000{endpoint}"
                response = requests.get(url, timeout=5)

                exposure_result["accessible"] = True
                exposure_result["status_code"] = response.status_code

                if response.status_code == 200:
                    result["vulnerabilities"].append(
                        f"Internal endpoint exposed: {endpoint}"
                    )

                try:
                    response_data = response.json()
                    exposure_result["response_data"] = json.dumps(response_data)[:200]
                except Exception as e:
                    exposure_result["response_data"] = response.text[:200]

            except requests.exceptions.RequestException:
                # Endpoint not accessible - this is good for internal endpoints
                pass

            # Check for security headers
            try:
                response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
                security_headers = {
                    "auth_required": response.status_code in [401, 403],
                    "cors_restricted": "Access-Control-Allow-Origin"
                    not in response.headers,
                    "secure_headers": response.headers.get("X-Frame-Options")
                    is not None,
                }
                exposure_result["security_measures"] = security_headers

                if not security_headers["auth_required"]:
                    result["vulnerabilities"].append(
                        f"Missing authentication for {endpoint}"
                    )

            except requests.exceptions.RequestException:
                pass

            result["exposure_tests"].append(exposure_result)

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 2 else "MEDIUM"
        )

        return result

    def test_api_rate_limiting(self) -> Dict[str, Any]:
        """Test API rate limiting implementation"""
        print("🔍 Testing API rate limiting...")

        result = {
            "test_name": "API Rate Limiting Test",
            "test_timestamp": datetime.now().isoformat(),
            "rate_limit_tests": [],
            "vulnerabilities": [],
        }

        # Test endpoints that should have rate limiting
        rate_limit_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/",
            "/api/v1/assessments/",
        ]

        for endpoint in rate_limit_endpoints:
            rate_limit_result = {
                "endpoint": endpoint,
                "requests_per_second": 0,
                "rate_limit_detected": False,
                "test_results": [],
            }

            try:
                url = f"http://localhost:8000{endpoint}"
                requests_made = 0
                start_time = time.time()

                # Make rapid requests to test rate limiting
                for i in range(20):
                    try:
                        response = requests.get(url, timeout=2)
                        rate_limit_result["test_results"].append(
                            {
                                "request_number": i + 1,
                                "status_code": response.status_code,
                                "response_time": time.time() - start_time,
                            }
                        )
                        requests_made += 1

                        # Check if rate limited
                        if response.status_code == 429:
                            rate_limit_result["rate_limit_detected"] = True
                            break

                    except requests.exceptions.RequestException:
                        # Connection error - stop testing this endpoint
                        break

                rate_limit_result["requests_per_second"] = (
                    requests_made / (time.time() - start_time)
                    if time.time() > start_time
                    else 0
                )

                if not rate_limit_result["rate_limit_detected"] and requests_made >= 10:
                    result["vulnerabilities"].append(
                        f"No rate limiting detected: {endpoint} ({requests_made} requests made)"
                    )

            except requests.exceptions.RequestException:
                result["vulnerabilities"].append(
                    f"Rate limiting test failed for {endpoint}"
                )

            result["rate_limit_tests"].append(rate_limit_result)

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = "MEDIUM" if result["vulnerable"] else "LOW"

        return result

    def analyze_api_cors_configuration(self) -> Dict[str, Any]:
        """Analyze CORS configuration in APIs"""
        print("🔍 Analyzing API CORS configuration...")

        result = {
            "test_name": "CORS Configuration Analysis",
            "test_timestamp": datetime.now().isoformat(),
            "cors_settings": [],
            "vulnerabilities": [],
        }

        # Look for CORS configuration in application files
        cors_files = [
            "app/main.py",
            "app/core/cors.py",
            "app/core/security_middleware.py",
        ]

        for cors_file in cors_files:
            file_path = self.base_path / cors_file
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()

                    cors_patterns = [
                        (r'CORS_ORIGINS\s*=\s*([^"\n\r]+)', "CORS origins"),
                        (r'allowed_origins\s*=\s*([^"\n\r]+)', "Allowed origins"),
                        (r'allow_origins\s*=\s*([^"\n\r]+)', "Allow origins"),
                        (
                            r'Access-Control-Allow-Origin\s*:\s*([^"\n\r]+)',
                            "CORS header",
                        ),
                    ]

                    file_cors_settings = []
                    for pattern, description in cors_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            file_cors_settings.append(
                                {
                                    "type": description,
                                    "value": match.strip().strip('"').strip("'"),
                                    "insecure": "*" in match or "http://*" in match,
                                }
                            )

                    if file_cors_settings:
                        result["cors_settings"].append(
                            {"file": cors_file, "settings": file_cors_settings}
                        )

                    # Check for CORS security issues
                    insecure_patterns = [
                        (r'"\*"', "Wildcard origin allowed"),
                        (r"null", "CORS origin set to null"),
                        (r"http://\*", "HTTP wildcard allowed"),
                    ]

                    for pattern, description in insecure_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            result["vulnerabilities"].append(
                                f"Insecure CORS setting in {cors_file}: {description}"
                            )

                except Exception as e:
                    result["vulnerabilities"].append(
                        f"Error analyzing CORS in {cors_file}: {e}"
                    )

        result["vulnerable"] = len(result["vulnerabilities"]) > 0
        result["risk_level"] = (
            "HIGH" if len(result["vulnerabilities"]) > 2 else "MEDIUM"
        )

        return result

    def generate_api_security_recommendations(
        self, test_results: List[Dict]
    ) -> List[Dict]:
        """Generate API security recommendations"""
        recommendations = []

        for result in test_results:
            if result.get("vulnerable", False):
                if "API Endpoint Discovery" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "MEDIUM",
                            "category": "API Documentation",
                            "issue": "API endpoints may lack proper documentation",
                            "recommendation": "Document all API endpoints and their access requirements",
                        }
                    )
                elif "API Access Controls" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "CRITICAL",
                            "category": "Access Control",
                            "issue": "API access control vulnerabilities detected",
                            "recommendation": "Implement proper authentication and authorization for all API endpoints",
                        }
                    )
                elif "Internal API Exposure" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "API Security",
                            "issue": "Internal APIs exposed to unauthorized access",
                            "recommendation": "Secure internal endpoints with network segmentation and authentication",
                        }
                    )
                elif "Rate Limiting" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "MEDIUM",
                            "category": "API Protection",
                            "issue": "API rate limiting not implemented",
                            "recommendation": "Implement rate limiting for all API endpoints to prevent abuse",
                        }
                    )
                elif "CORS Configuration" in result.get("test_name", ""):
                    recommendations.append(
                        {
                            "priority": "HIGH",
                            "category": "API Security",
                            "issue": "CORS configuration vulnerabilities detected",
                            "recommendation": "Configure CORS with specific origins and disable wildcard policies",
                        }
                    )

        # Add general API security recommendations
        recommendations.extend(
            [
                {
                    "priority": "CRITICAL",
                    "category": "API Authentication",
                    "issue": "Comprehensive API authentication required",
                    "recommendation": "Implement JWT-based authentication with token refresh mechanism",
                },
                {
                    "priority": "HIGH",
                    "category": "API Authorization",
                    "issue": "Role-based access control required",
                    "recommendation": "Implement RBAC with fine-grained permissions for API resources",
                },
                {
                    "priority": "MEDIUM",
                    "category": "API Security",
                    "issue": "API input validation needed",
                    "recommendation": "Implement comprehensive input validation and sanitization for all API endpoints",
                },
                {
                    "priority": "MEDIUM",
                    "category": "API Monitoring",
                    "issue": "API security monitoring not implemented",
                    "recommendation": "Implement API request logging and security event monitoring",
                },
            ]
        )

        return recommendations

    def run_comprehensive_api_test(self) -> Dict[str, Any]:
        """Run comprehensive internal API security test"""
        print("🔐 STARTING COMPREHENSIVE INTERNAL API SECURITY TEST")
        print("=" * 60)

        results = []

        # Test 1: API endpoint discovery
        results.append(self.discover_api_endpoints())

        # Test 2: API access controls
        results.append(self.test_api_access_controls())

        # Test 3: Internal API exposure
        results.append(self.test_internal_api_exposure())

        # Test 4: API rate limiting
        results.append(self.test_api_rate_limiting())

        # Test 5: CORS configuration
        results.append(self.analyze_api_cors_configuration())

        # Generate recommendations
        recommendations = self.generate_api_security_recommendations(results)
        results.append({"recommendations": recommendations})

        # Generate summary
        total_tests = len(results) - 1  # Excluding recommendations
        vulnerable_tests = len([r for r in results if r.get("vulnerable", False)])

        summary = {
            "total_tests": total_tests,
            "vulnerable_tests": vulnerable_tests,
            "recommendations_count": len(recommendations),
            "total_endpoints": results[0].get("total_endpoints", 0) if results else 0,
            "overall_api_security_score": max(0, 100 - (vulnerable_tests * 18)),
        }

        return {
            "test_timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": summary,
        }


def main():
    """Main execution function"""
    tester = InternalAPISecurityTester()

    try:
        results = tester.run_comprehensive_api_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 INTERNAL API SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerable Tests: {summary['vulnerable_tests']}")
        print(f"🔗 Total Endpoints: {summary['total_endpoints']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")
        print(
            f"🎯 Overall API Security Score: {summary['overall_api_security_score']}/100"
        )

        # Show test results
        for i, test_result in enumerate(
            results["test_results"][:-1], 1
        ):  # Exclude recommendations
            print(f"\n{i}. {test_result['test_name']}:")
            if test_result.get("vulnerable", False):
                print(f"   ❌ VULNERABLE: {test_result.get('risk_level', 'HIGH')}")
                if "vulnerabilities" in test_result:
                    for vuln in test_result["vulnerabilities"]:
                        print(f"      • {vuln}")
                if "security_issues" in test_result:
                    for issue in test_result["security_issues"]:
                        print(f"      • {issue}")
            else:
                print(f"   ✅ SECURE: {test_result.get('risk_level', 'LOW')}")

        # Show endpoint discovery summary
        endpoint_discovery = results["test_results"][0] if results else None
        if endpoint_discovery:
            print(f"\n📋 API ENDPOINT SUMMARY:")
            print(
                f"   Admin Endpoints: {len(endpoint_discovery.get('admin_endpoints', []))}"
            )
            print(
                f"   Internal Endpoints: {len(endpoint_discovery.get('internal_endpoints', []))}"
            )
            print(
                f"   External Endpoints: {len(endpoint_discovery.get('external_endpoints', []))}"
            )

        # Show recommendations
        print(f"\n💡 API SECURITY RECOMMENDATIONS:")
        recommendations = results["test_results"][-1]["recommendations"]
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open(
            "/Users/sheriftito/Downloads/psychsync/internal_api_security_report.json",
            "w",
        ) as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: internal_api_security_report.json")

    except Exception as e:
        print(f"❌ Error running internal API security test: {e}")


if __name__ == "__main__":
    main()
