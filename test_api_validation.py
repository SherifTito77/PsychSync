#!/usr/bin/env python3
"""
Comprehensive API validation test for PsychSync platform
"""
import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import uvicorn
    from fastapi.testclient import TestClient
    from app.main import app
    print(f"✅ Successfully imported API modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class PsychSyncAPIValidator:
    """Comprehensive API validation class"""

    def __init__(self):
        self.client = TestClient(app)
        self.test_results = []
        self.auth_token = None
        self.test_user_id = None

    def log_result(self, test_name: str, status: str, details: str = "", response_time: float = 0):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": time.time()
        }
        self.test_results.append(result)

        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status} ({response_time:.3f}s)")
        if details:
            print(f"   Details: {details}")

    def test_health_endpoint(self):
        """Test API health endpoint"""
        start_time = time.time()
        try:
            response = self.client.get("/health")
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Health Check",
                    "PASS",
                    f"Status: {data.get('status', 'unknown')}",
                    response_time
                )
                return True
            else:
                self.log_result(
                    "Health Check",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response_time
                )
                return False
        except Exception as e:
            self.log_result(
                "Health Check",
                "ERROR",
                str(e),
                time.time() - start_time
            )
            return False

    def test_api_docs(self):
        """Test API documentation endpoints"""
        endpoints = [
            ("/docs", "Swagger UI"),
            ("/redoc", "ReDoc"),
            ("/openapi.json", "OpenAPI Schema")
        ]

        all_passed = True
        for endpoint, name in endpoints:
            start_time = time.time()
            try:
                response = self.client.get(endpoint)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    self.log_result(
                        f"API Docs - {name}",
                        "PASS",
                        f"Endpoint accessible",
                        response_time
                    )
                else:
                    self.log_result(
                        f"API Docs - {name}",
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    all_passed = False
            except Exception as e:
                self.log_result(
                    f"API Docs - {name}",
                    "ERROR",
                    str(e),
                    time.time() - start_time
                )
                all_passed = False

        return all_passed

    def test_authentication(self):
        """Test authentication flow"""
        print("\n🔐 Testing Authentication Flow...")

        # Test registration
        start_time = time.time()
        test_email = f"testuser{int(time.time())}@psychsync.test"
        test_user_data = {
            "email": test_email,
            "password": "SecureTest123!",
            "name": "Test Validation User"
        }

        try:
            response = self.client.post("/api/v1/auth/register", json=test_user_data)
            response_time = time.time() - start_time

            if response.status_code in [200, 201]:
                register_data = response.json()
                self.log_result(
                    "User Registration",
                    "PASS",
                    f"User created: {test_email}",
                    response_time
                )
            elif response.status_code == 400:
                self.log_result(
                    "User Registration",
                    "PARTIAL",
                    "User may already exist - continuing",
                    response_time
                )
            else:
                self.log_result(
                    "User Registration",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response_time
                )
                return False

            # Test login
            start_time = time.time()
            login_data = {
                "username": test_email,
                "password": "SecureTest123!"
            }

            response = self.client.post(
                "/api/v1/auth/token",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                login_data = response.json()
                self.auth_token = login_data.get("access_token")
                self.log_result(
                    "User Login",
                    "PASS",
                    "Token received successfully",
                    response_time
                )
                return True
            else:
                self.log_result(
                    "User Login",
                    "FAIL",
                    f"HTTP {response.status_code}",
                    response_time
                )
                return False

        except Exception as e:
            self.log_result(
                "Authentication Flow",
                "ERROR",
                str(e),
                time.time() - start_time
            )
            return False

    def test_protected_endpoints(self):
        """Test protected endpoints with authentication"""
        if not self.auth_token:
            self.log_result(
                "Protected Endpoints",
                "SKIP",
                "No authentication token available"
            )
            return False

        print("\n🔒 Testing Protected Endpoints...")
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        protected_endpoints = [
            ("/api/v1/users/me", "User Profile"),
            ("/api/v1/users", "User List")
        ]

        all_passed = True
        for endpoint, name in protected_endpoints:
            start_time = time.time()
            try:
                response = self.client.get(endpoint, headers=headers)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    self.log_result(
                        f"Protected - {name}",
                        "PASS",
                        f"Endpoint accessible",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Protected - {name}",
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    all_passed = False
            except Exception as e:
                self.log_result(
                    f"Protected - {name}",
                    "ERROR",
                    str(e),
                    time.time() - start_time
                )
                all_passed = False

        return all_passed

    def test_public_endpoints(self):
        """Test public endpoints"""
        print("\n🌐 Testing Public Endpoints...")

        public_endpoints = [
            ("/api/v1/health", "Health Check"),
            ("/", "API Root")
        ]

        all_passed = True
        for endpoint, name in public_endpoints:
            start_time = time.time()
            try:
                response = self.client.get(endpoint)
                response_time = time.time() - start_time

                if response.status_code == 200:
                    self.log_result(
                        f"Public - {name}",
                        "PASS",
                        f"Endpoint accessible",
                        response_time
                    )
                else:
                    self.log_result(
                        f"Public - {name}",
                        "FAIL",
                        f"HTTP {response.status_code}",
                        response_time
                    )
                    all_passed = False
            except Exception as e:
                self.log_result(
                    f"Public - {name}",
                    "ERROR",
                    str(e),
                    time.time() - start_time
                )
                all_passed = False

        return all_passed

    def test_error_handling(self):
        """Test API error handling"""
        print("\n⚠️ Testing Error Handling...")

        # Test 404 error
        start_time = time.time()
        try:
            response = self.client.get("/api/v1/nonexistent/endpoint")
            response_time = time.time() - start_time

            if response.status_code == 404:
                self.log_result(
                    "404 Error Handling",
                    "PASS",
                    "Proper 404 response",
                    response_time
                )
            else:
                self.log_result(
                    "404 Error Handling",
                    "FAIL",
                    f"Expected 404, got {response.status_code}",
                    response_time
                )
                return False
        except Exception as e:
            self.log_result(
                "404 Error Handling",
                "ERROR",
                str(e),
                time.time() - start_time
            )
            return False

        # Test unauthorized access
        start_time = time.time()
        try:
            response = self.client.get("/api/v1/users/me")
            response_time = time.time() - start_time

            if response.status_code == 401:
                self.log_result(
                    "Unauthorized Access",
                    "PASS",
                    "Proper 401 response",
                    response_time
                )
            else:
                self.log_result(
                    "Unauthorized Access",
                    "FAIL",
                    f"Expected 401, got {response.status_code}",
                    response_time
                )
                return False
        except Exception as e:
            self.log_result(
                "Unauthorized Access",
                "ERROR",
                str(e),
                time.time() - start_time
            )
            return False

        return True

    def test_api_performance(self):
        """Test API response times"""
        print("\n⚡ Testing API Performance...")

        # Test multiple quick health checks
        response_times = []
        for i in range(5):
            start_time = time.time()
            response = self.client.get("/health")
            response_time = time.time() - start_time
            response_times.append(response_time)

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        if avg_response_time < 0.1:  # 100ms threshold
            status = "PASS"
        elif avg_response_time < 0.5:  # 500ms threshold
            status = "WARN"
        else:
            status = "FAIL"

        self.log_result(
            "API Performance",
            status,
            f"Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s",
            avg_response_time
        )

        return status == "PASS"

    def run_comprehensive_test(self):
        """Run all validation tests"""
        print("🔍 PsychSync API Comprehensive Validation")
        print("=" * 50)

        test_functions = [
            ("Health Endpoint", self.test_health_endpoint),
            ("API Documentation", self.test_api_docs),
            ("Public Endpoints", self.test_public_endpoints),
            ("Authentication Flow", self.test_authentication),
            ("Protected Endpoints", self.test_protected_endpoints),
            ("Error Handling", self.test_error_handling),
            ("API Performance", self.test_api_performance),
        ]

        results = {}
        for test_name, test_func in test_functions:
            print(f"\n🧪 Running: {test_name}")
            results[test_name] = test_func()

        # Generate summary
        self.generate_summary(results)

        return results

    def generate_summary(self, results: Dict[str, bool]):
        """Generate test summary"""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        passed = sum(1 for r in results.values() if r)
        total = len(results)

        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{status} {test_name}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All API validation tests completed successfully!")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed - review failures")
        else:
            print("❌ Multiple test failures - review required")

        # Performance summary
        avg_times = [r["response_time"] for r in self.test_results if r.get("response_time", 0) > 0]
        if avg_times:
            print(f"Average response time: {sum(avg_times)/len(avg_times):.3f}s")

async def main():
    """Main validation function"""
    validator = PsychSyncAPIValidator()
    results = validator.run_comprehensive_test()
    return 0 if sum(results.values()) == len(results) else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)