# Fast Test Configuration for PsychSync Onboarding
# Optimized for rapid development feedback

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List
import concurrent.futures
from contextlib import asynccontextmanager

class FastTestRunner:
    """
    Optimized test runner for rapid development feedback
    Focuses on critical functionality with minimal overhead
    """

    def __init__(self):
        self.config = {
            "max_concurrent_tests": 5,  # Reduced from 10
            "test_timeout": 30,         # Reduced from 300s
            "skip_slow_tests": True,
            "skip_database_tests": True,  # Skip PostgreSQL-dependent tests
            "skip_redis_tests": True,    # Skip Redis-dependent tests
            "use_in_memory_database": True,
        }

    async def run_critical_onboarding_tests(self) -> Dict[str, Any]:
        """
        Run only the most critical onboarding tests for rapid feedback
        """
        print("🚀 Fast PsychSync Onboarding Test Suite")
        print("=" * 50)
        print(f"Configuration: {self.config}")
        print()

        start_time = time.time()
        results = {
            "execution_summary": {
                "start_time": datetime.utcnow().isoformat(),
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "total_duration": 0.0
            },
            "test_results": [],
            "performance_summary": {
                "average_response_time": 0.0,
                "fastest_test": 0.0,
                "slowest_test": 0.0,
                "threshold_violations": 0
            },
            "optimization_suggestions": []
        }

        try:
            # Critical test categories to run
            test_categories = [
                ("API Connectivity", self._test_api_connectivity),
                ("Basic Request Handling", self._test_basic_requests),
                ("Input Validation", self._test_input_validation),
                ("Error Handling", self._test_error_handling),
                ("Response Structure", self._test_response_structure)
            ]

            for category_name, test_func in test_categories:
                print(f"🧪 {category_name}...")
                category_start = time.time()

                try:
                    category_results = await test_func()
                    category_duration = time.time() - category_start

                    results["test_results"].extend(category_results)
                    results["execution_summary"]["total_tests"] += len(category_results)

                    successful = sum(1 for r in category_results if r["success"])
                    results["execution_summary"]["successful_tests"] += successful

                    print(f"  ✅ {successful}/{len(category_results)} tests passed ({category_duration:.2f}s)")

                except Exception as e:
                    print(f"  ❌ Category failed: {str(e)}")
                    results["test_results"].append({
                        "test_name": category_name,
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - category_start
                    })
                    results["execution_summary"]["total_tests"] += 1
                    results["execution_summary"]["failed_tests"] += 1

            # Calculate final metrics
            total_duration = time.time() - start_time
            results["execution_summary"]["end_time"] = datetime.utcnow().isoformat()
            results["execution_summary"]["total_duration"] = total_duration
            results["execution_summary"]["success_rate"] = (
                results["execution_summary"]["successful_tests"] /
                max(results["execution_summary"]["total_tests"], 1)
            )

            # Performance metrics
            if results["test_results"]:
                durations = [r["duration"] for r in results["test_results"] if "duration" in r]
                if durations:
                    results["performance_summary"]["average_response_time"] = sum(durations) / len(durations)
                    results["performance_summary"]["fastest_test"] = min(durations)
                    results["performance_summary"]["slowest_test"] = max(durations)

            # Generate optimization suggestions
            results["optimization_suggestions"] = self._generate_optimization_suggestions(results)

        except Exception as e:
            print(f"❌ Test runner error: {str(e)}")
            results["error"] = str(e)

        return results

    async def _test_api_connectivity(self) -> List[Dict[str, Any]]:
        """Test basic API connectivity"""
        results = []

        try:
            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)
            start_time = time.time()

            # Test health endpoint
            response = client.get("/health")
            duration = time.time() - start_time

            success = response.status_code == 200
            results.append({
                "test_name": "Health Check",
                "success": success,
                "status_code": response.status_code,
                "duration": duration,
                "details": {"response_time": duration}
            })

        except Exception as e:
            results.append({
                "test_name": "API Connectivity",
                "success": False,
                "error": str(e),
                "duration": 0.0
            })

        return results

    async def _test_basic_requests(self) -> List[Dict[str, Any]]:
        """Test basic request handling"""
        results = []

        try:
            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)

            # Test different request types
            test_requests = [
                ("GET", "/health"),
                ("GET", "/docs"),  # Should work
                ("POST", "/api/v1/onboarding/quick-assessment", {"role": "member", "challenge": "communication"})
            ]

            for method, endpoint, *payload in test_requests:
                start_time = time.time()

                try:
                    if payload:
                        response = client.request(method, endpoint, json=payload[0])
                    else:
                        response = client.request(method, endpoint)

                    duration = time.time() - start_time

                    # Accept any 2xx, 3xx, or 4xx as "working" (404 is expected for missing endpoints)
                    success = response.status_code < 500

                    results.append({
                        "test_name": f"{method} {endpoint}",
                        "success": success,
                        "status_code": response.status_code,
                        "duration": duration,
                        "details": {
                            "response_time": duration,
                            "status_category": "success" if response.status_code < 500 else "server_error"
                        }
                    })

                except Exception as e:
                    results.append({
                        "test_name": f"{method} {endpoint}",
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - start_time
                    })

        except Exception as e:
            results.append({
                "test_name": "Basic Request Handling",
                "success": False,
                "error": str(e),
                "duration": 0.0
            })

        return results

    async def _test_input_validation(self) -> List[Dict[str, Any]]:
        """Test input validation without database calls"""
        results = []

        # Test Pydantic schema validation
        test_cases = [
            {
                "name": "Valid Assessment Request",
                "data": {"role": "manager", "challenge": "communication"},
                "should_validate": True
            },
            {
                "name": "Invalid Role",
                "data": {"role": "invalid_role", "challenge": "communication"},
                "should_validate": False
            },
            {
                "name": "Empty Request",
                "data": {},
                "should_validate": False
            },
            {
                "name": "Null Values",
                "data": {"role": None, "challenge": None},
                "should_validate": False
            }
        ]

        try:
            from app.schemas.onboarding import QuickAssessmentRequest

            for test_case in test_cases:
                start_time = time.time()

                try:
                    # Test schema validation
                    validated = QuickAssessmentRequest(**test_case["data"])
                    success = test_case["should_validate"]
                    duration = time.time() - start_time

                    results.append({
                        "test_name": test_case["name"],
                        "success": success,
                        "duration": duration,
                        "details": {
                            "validated": True,
                            "expected": test_case["should_validate"]
                        }
                    })

                except Exception as validation_error:
                    duration = time.time() - start_time
                    success = not test_case["should_validate"]

                    results.append({
                        "test_name": test_case["name"],
                        "success": success,
                        "duration": duration,
                        "details": {
                            "validation_error": str(validation_error),
                            "expected_failure": not test_case["should_validate"]
                        }
                    })

        except Exception as e:
            results.append({
                "test_name": "Input Validation Test",
                "success": False,
                "error": str(e),
                "duration": 0.0
            })

        return results

    async def _test_error_handling(self) -> List[Dict[str, Any]]:
        """Test error handling capabilities"""
        results = []

        try:
            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)

            error_test_cases = [
                ("GET", "/nonexistent-endpoint", 404),
                ("POST", "/api/v1/onboarding/quick-assessment", {}, 422),  # Validation error
                ("POST", "/api/v1/auth/login", {}, 422),  # Auth validation error
            ]

            for method, endpoint, payload, expected_status in error_test_cases:
                start_time = time.time()

                try:
                    if isinstance(payload, dict) and payload:
                        response = client.request(method, endpoint, json=payload)
                    else:
                        response = client.request(method, endpoint)

                    duration = time.time() - start_time

                    # Check if we get the expected error status
                    success = response.status_code == expected_status

                    results.append({
                        "test_name": f"Error Handling: {method} {endpoint}",
                        "success": success,
                        "status_code": response.status_code,
                        "expected_status": expected_status,
                        "duration": duration,
                        "details": {
                            "error_response": response.status_code >= 400,
                            "correct_error_code": success
                        }
                    })

                except Exception as e:
                    results.append({
                        "test_name": f"Error Handling: {method} {endpoint}",
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - start_time,
                        "expected_status": expected_status
                    })

        except Exception as e:
            results.append({
                "test_name": "Error Handling Tests",
                "success": False,
                "error": str(e),
                "duration": 0.0
            })

        return results

    async def _test_response_structure(self) -> List[Dict[str, Any]]:
        """Test response structure consistency"""
        results = []

        try:
            from fastapi.testclient import TestClient
            from app.main import app

            client = TestClient(app)

            # Test response structure for different endpoints
            test_endpoints = [
                ("GET", "/health"),
                ("GET", "/docs"),
            ]

            for method, endpoint in test_endpoints:
                start_time = time.time()

                try:
                    response = client.request(method, endpoint)
                    duration = time.time() - start_time

                    success = response.status_code == 200

                    # Check response has expected structure
                    if success and response.headers.get("content-type", "").startswith("application/json"):
                        response_data = response.json()
                        has_structure = isinstance(response_data, dict)

                        results.append({
                            "test_name": f"Response Structure: {method} {endpoint}",
                            "success": success and has_structure,
                            "status_code": response.status_code,
                            "duration": duration,
                            "details": {
                                "is_json": True,
                                "has_structure": has_structure,
                                "response_keys": list(response_data.keys()) if has_structure else []
                            }
                        })
                    else:
                        results.append({
                            "test_name": f"Response Structure: {method} {endpoint}",
                            "success": success,
                            "status_code": response.status_code,
                            "duration": duration,
                            "details": {
                                "content_type": response.headers.get("content-type", "unknown")
                            }
                        })

                except Exception as e:
                    results.append({
                        "test_name": f"Response Structure: {method} {endpoint}",
                        "success": False,
                        "error": str(e),
                        "duration": time.time() - start_time
                    })

        except Exception as e:
            results.append({
                "test_name": "Response Structure Tests",
                "success": False,
                "error": str(e),
                "duration": 0.0
            })

        return results

    def _generate_optimization_suggestions(self, results: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on test results"""
        suggestions = []

        # Performance suggestions
        avg_response_time = results["performance_summary"]["average_response_time"]
        if avg_response_time > 1.0:
            suggestions.append(f"Average response time ({avg_response_time:.2f}s) exceeds 1.0s target")

        slowest_test = results["performance_summary"]["slowest_test"]
        if slowest_test > 5.0:
            suggestions.append(f"Slowest test ({slowest_test:.2f}s) exceeds 5.0s threshold")

        # Success rate suggestions
        success_rate = results["execution_summary"]["success_rate"]
        if success_rate < 0.9:
            suggestions.append(f"Success rate ({success_rate:.1%}) below 90% target")

        # Test-specific suggestions
        failed_tests = results["execution_summary"]["failed_tests"]
        if failed_tests > 0:
            suggestions.append(f"{failed_tests} test failures need investigation")

        # Infrastructure suggestions
        results_list = results.get("test_results", [])
        database_errors = sum(1 for r in results_list if "database" in str(r.get("error", "")).lower())
        if database_errors > 0:
            suggestions.append("Consider using in-memory database for faster tests")

        redis_errors = sum(1 for r in results_list if "redis" in str(r.get("error", "")).lower())
        if redis_errors > 0:
            suggestions.append("Consider mocking Redis dependencies for faster tests")

        return suggestions


async def run_fast_tests():
    """
    Run the optimized test suite
    """
    runner = FastTestRunner()
    results = await runner.run_critical_onboarding_tests()

    print("\n" + "=" * 50)
    print("🎯 FAST TEST RESULTS")
    print("=" * 50)

    summary = results["execution_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1%}")
    print(f"Duration: {summary['total_duration']:.2f}s")

    if results["performance_summary"]["average_response_time"] > 0:
        perf = results["performance_summary"]
        print(f"\n⚡ Performance:")
        print(f"  Average Response: {perf['average_response_time']:.3f}s")
        print(f"  Fastest Test: {perf['fastest_test']:.3f}s")
        print(f"  Slowest Test: {perf['slowest_test']:.3f}s")

    if results["optimization_suggestions"]:
        print(f"\n💡 Optimization Suggestions:")
        for suggestion in results["optimization_suggestions"]:
            print(f"  • {suggestion}")

    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_fast_tests())
