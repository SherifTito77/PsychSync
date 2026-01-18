#!/usr/bin/env python3
"""
Quick API Testing Demonstration
Shows load testing and error handling capabilities
"""

import requests
import json
import time
import concurrent.futures
from datetime import datetime

class QuickAPITester:
    """Quick API testing demonstration"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []

    def test_error_scenarios(self):
        """Test various error scenarios"""
        print("🔍 Testing API Error Handling Scenarios")
        print("=" * 50)

        test_cases = [
            {
                "name": "Invalid Endpoint",
                "url": f"{self.base_url}/api/v1/nonexistent",
                "method": "GET",
                "expected_status": 404
            },
            {
                "name": "Wrong HTTP Method",
                "url": f"{self.base_url}/api/v1/health",
                "method": "POST",
                "expected_status": 405
            },
            {
                "name": "Invalid JSON Payload",
                "url": f"{self.base_url}/api/v1/auth/login",
                "method": "POST",
                "data": "invalid json",
                "expected_status": 400
            },
            {
                "name": "Missing Required Fields",
                "url": f"{self.base_url}/api/v1/auth/login",
                "method": "POST",
                "data": {"email": "incomplete"},
                "expected_status": 400
            },
            {
                "name": "Non-existent Resource",
                "url": f"{self.base_url}/api/v1/users/999999",
                "method": "GET",
                "expected_status": 401  # Will be auth error, which is good
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            try:
                start_time = time.time()

                if test_case["method"] == "GET":
                    response = requests.get(test_case["url"], timeout=10)
                elif test_case["method"] == "POST":
                    if isinstance(test_case.get("data"), str):
                        response = requests.post(test_case["url"],
                                                data=test_case["data"],
                                                headers={"Content-Type": "application/json"},
                                                timeout=10)
                    else:
                        response = requests.post(test_case["url"],
                                                json=test_case.get("data", {}),
                                                timeout=10)

                response_time = (time.time() - start_time) * 1000

                # Analyze response
                graceful = False
                if response.status_code == test_case["expected_status"]:
                    graceful = True

                # Check if response has proper error structure
                has_error_structure = False
                try:
                    response_json = response.json()
                    if "error" in response_json or "message" in response_json:
                        has_error_structure = True
                except Exception as e:
                    pass

                status = "✅" if graceful and has_error_structure else "⚠️" if graceful else "❌"

                print(f"{status} Test {i}: {test_case['name']}")
                print(f"    HTTP {response.status_code} ({response_time:.0f}ms) - Expected {test_case['expected_status']}")

                if response.status_code < 500:
                    print(f"    Graceful: Yes | Structure: {'✅' if has_error_structure else '❌'}")
                    if response.status_code != 200:
                        try:
                            error_data = response.json()
                            if "message" in error_data:
                                print(f"    Message: {error_data['message'][:80]}...")
                        except Exception as e:
                            pass
                else:
                    print(f"    ⚠️  Server error - needs investigation")

                print()

                self.results.append({
                    "test": test_case["name"],
                    "status_code": response.status_code,
                    "expected": test_case["expected_status"],
                    "response_time_ms": response_time,
                    "graceful": graceful,
                    "has_structure": has_error_structure
                })

            except Exception as e:
                print(f"❌ Test {i}: {test_case['name']} - Exception: {str(e)}")
                print()

    def run_mini_load_test(self, num_requests=50):
        """Run a mini load test"""
        print(f"⚡ Mini Load Test: {num_requests} concurrent requests")
        print("=" * 50)

        def make_request():
            """Make a single request"""
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
                response_time = (time.time() - start_time) * 1000
                return {
                    "status_code": response.status_code,
                    "response_time_ms": response_time,
                    "success": response.status_code == 401  # 401 is expected for unauthenticated health check
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "response_time_ms": 10000,  # timeout
                    "success": False,
                    "error": str(e)
                }

        start_time = time.time()

        # Run requests concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        total_time = time.time() - start_time

        # Calculate metrics
        successful = [r for r in results if r["success"]]
        response_times = [r["response_time_ms"] for r in results if r["response_time_ms"] > 0]

        if response_times:
            avg_response = sum(response_times) / len(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
        else:
            avg_response = min_response = max_response = 0

        print(f"📊 Results:")
        print(f"   • Total Requests: {len(results)}")
        print(f"   • Successful: {len(successful)} ({(len(successful)/len(results)*100):.1f}%)")
        print(f"   • Failed: {len(results) - len(successful)}")
        print(f"   • Requests/Second: {len(results)/total_time:.1f}")
        print(f"   • Avg Response Time: {avg_response:.0f}ms")
        print(f"   • Min/Max Response Time: {min_response:.0f}ms / {max_response:.0f}ms")
        print(f"   • Total Test Time: {total_time:.1f}s")

        # Performance assessment
        print(f"\n💡 Performance Assessment:")
        if len(successful)/len(results) >= 0.95:
            print("   ✅ Excellent success rate (≥95%)")
        elif len(successful)/len(results) >= 0.90:
            print("   ⚠️  Good success rate (90-95%)")
        else:
            print("   ❌ Low success rate (<90%)")

        if avg_response < 500:
            print("   ✅ Excellent response time (<500ms)")
        elif avg_response < 1000:
            print("   ⚠️  Acceptable response time (500-1000ms)")
        else:
            print("   ❌ Slow response time (>1000ms)")

        if len(results)/total_time > 50:
            print("   ✅ High throughput (>50 RPS)")
        else:
            print("   ⚠️  Moderate throughput (≤50 RPS)")

    def generate_summary(self):
        """Generate test summary"""
        if not self.results:
            return

        print("📋 ERROR HANDLING SUMMARY")
        print("=" * 50)

        graceful_count = sum(1 for r in self.results if r["graceful"])
        structured_count = sum(1 for r in self.results if r["has_structure"])

        print(f"Error Handling Tests: {len(self.results)}")
        print(f"Graceful Responses: {graceful_count}/{len(self.results)} ({graceful_count/len(self.results)*100:.1f}%)")
        print(f"Structured Responses: {structured_count}/{len(self.results)} ({structured_count/len(self.results)*100:.1f}%)")

        if graceful_count == len(self.results) and structured_count == len(self.results):
            print("\n✅ EXCELLENT: All error responses are graceful and properly structured!")
        elif graceful_count >= len(self.results) * 0.8:
            print("\n👍 GOOD: Most error responses are handled gracefully")
        else:
            print("\n⚠️  NEEDS IMPROVEMENT: Some error responses need better handling")

def main():
    """Main execution"""
    print("🚀 Quick API Testing Demonstration")
    print("Testing PsychSync API Load and Error Handling")
    print("=" * 60)

    tester = QuickAPITester()

    # Test error handling
    tester.test_error_scenarios()

    # Run mini load test
    tester.run_mini_load_test(num_requests=100)

    # Generate summary
    tester.generate_summary()

    print(f"\n🎯 Test completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

if __name__ == "__main__":
    main()
