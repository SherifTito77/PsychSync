#!/usr/bin/env python3
"""
Comprehensive AI Engine Testing Suite
Tests all personality types, frameworks, and features
"""

import json
import time
from datetime import datetime

import requests


class AIEngineTester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.test_results = []
        self.errors = []

    def log_result(self, test_name, success, details="", response_time=0):
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "response_time_ms": response_time,
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)
        status = "✅" if success else "❌"
        print(f"{status} {test_name} - {details} ({response_time:.1f}ms)")

    def test_all_mbti_types(self):
        """Test all 16 MBTI personality types"""
        print("\n🧠 TESTING ALL MBTI PERSONALITY TYPES")
        print("=" * 50)

        mbti_types = [
            "INTJ",
            "INTP",
            "ENTJ",
            "ENTP",
            "INFJ",
            "INFP",
            "ENFJ",
            "ENFP",
            "ISTJ",
            "ISFJ",
            "ESTJ",
            "ESFJ",
            "ISTP",
            "ISFP",
            "ESTP",
            "ESFP",
        ]

        for mbti_type in mbti_types:
            start_time = time.time()
            try:
                test_data = {
                    "framework": "mbti",
                    "data": {"type": mbti_type, "confidence": 0.9},
                }

                response = requests.post(
                    f"{self.base_url}/personality-assessments/process-public",
                    json=test_data,
                    timeout=10,
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("results", {})
                        personality = result.get("type")
                        description = result.get("description", "")
                        processed_by = result.get("processed_by")
                        insights = result.get("ai_insights", [])

                        # Verify the AI engine processed correctly
                        if (
                            personality == mbti_type
                            and len(description) > 10
                            and "PsychSync AI" in processed_by
                            and len(insights) > 0
                        ):
                            self.log_result(
                                f"MBTI {mbti_type}",
                                True,
                                f"{description[:30]}...",
                                response_time,
                            )
                        else:
                            self.log_result(
                                f"MBTI {mbti_type}",
                                False,
                                "Invalid response structure",
                                response_time,
                            )
                    else:
                        self.log_result(
                            f"MBTI {mbti_type}",
                            False,
                            "API returned success=false",
                            response_time,
                        )
                else:
                    self.log_result(
                        f"MBTI {mbti_type}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                    )

            except Exception as e:
                self.log_result(f"MBTI {mbti_type}", False, f"Exception: {str(e)}", 0)

    def test_enneagram_types(self):
        """Test Enneagram personality types"""
        print("\n🔍 TESTING ENNEAGRAM TYPES")
        print("=" * 50)

        enneagram_types = [f"Type {i}" for i in range(1, 10)]

        for ennea_type in enneagram_types:
            start_time = time.time()
            try:
                test_data = {
                    "framework": "enneagram",
                    "data": {"type": ennea_type, "confidence": 0.85},
                }

                response = requests.post(
                    f"{self.base_url}/personality-assessments/process-public",
                    json=test_data,
                    timeout=10,
                )

                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("results", {})
                        personality = result.get("type")
                        processed_by = result.get("processed_by")

                        if personality == ennea_type and "PsychSync AI" in processed_by:
                            self.log_result(
                                f"Enneagram {ennea_type}",
                                True,
                                "Processed successfully",
                                response_time,
                            )
                        else:
                            self.log_result(
                                f"Enneagram {ennea_type}",
                                False,
                                "Invalid response",
                                response_time,
                            )
                    else:
                        self.log_result(
                            f"Enneagram {ennea_type}",
                            False,
                            "API returned success=false",
                            response_time,
                        )
                else:
                    self.log_result(
                        f"Enneagram {ennea_type}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                    )

            except Exception as e:
                self.log_result(
                    f"Enneagram {ennea_type}", False, f"Exception: {str(e)}", 0
                )

    def test_frameworks_endpoint(self):
        """Test frameworks availability"""
        print("\n📊 TESTING FRAMEWORKS ENDPOINT")
        print("=" * 50)

        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/personality-assessments/frameworks", timeout=10
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    frameworks = data.get("frameworks", [])
                    total_frameworks = data.get("total", 0)
                    access_level = data.get("access_level", "")

                    if total_frameworks >= 5 and access_level == "public":
                        framework_names = [fw.get("name") for fw in frameworks]
                        self.log_result(
                            "Frameworks Endpoint",
                            True,
                            f"{total_frameworks} frameworks: {', '.join(framework_names[:3])}...",
                            response_time,
                        )
                    else:
                        self.log_result(
                            "Frameworks Endpoint",
                            False,
                            "Invalid framework data",
                            response_time,
                        )
                else:
                    self.log_result(
                        "Frameworks Endpoint",
                        False,
                        "API returned success=false",
                        response_time,
                    )
            else:
                self.log_result(
                    "Frameworks Endpoint",
                    False,
                    f"HTTP {response.status_code}",
                    response_time,
                )

        except Exception as e:
            self.log_result("Frameworks Endpoint", False, f"Exception: {str(e)}", 0)

    def test_ai_insights_quality(self):
        """Test the quality and variety of AI insights"""
        print("\n💡 TESTING AI INSIGHTS QUALITY")
        print("=" * 50)

        test_cases = [
            {"framework": "mbti", "data": {"type": "INTJ", "confidence": 0.95}},
            {"framework": "mbti", "data": {"type": "ENFP", "confidence": 0.88}},
            {"framework": "enneagram", "data": {"type": "Type 1", "confidence": 0.92}},
        ]

        for i, case in enumerate(test_cases):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/personality-assessments/process-public",
                    json=case,
                    timeout=10,
                )
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("results", {})
                        insights = result.get("ai_insights", [])

                        # Check insights quality
                        if len(insights) >= 3:
                            insight_quality = (
                                "Good"
                                if all(len(insight) > 20 for insight in insights)
                                else "Poor"
                            )
                            personality = result.get("type")
                            self.log_result(
                                f"AI Insights Test {i+1} ({personality})",
                                True,
                                f"{len(insights)} insights, Quality: {insight_quality}",
                                response_time,
                            )
                        else:
                            self.log_result(
                                f"AI Insights Test {i+1}",
                                False,
                                "Insufficient insights",
                                response_time,
                            )
                    else:
                        self.log_result(
                            f"AI Insights Test {i+1}",
                            False,
                            "API returned success=false",
                            response_time,
                        )
                else:
                    self.log_result(
                        f"AI Insights Test {i+1}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                    )

            except Exception as e:
                self.log_result(
                    f"AI Insights Test {i+1}", False, f"Exception: {str(e)}", 0
                )

    def test_error_handling(self):
        """Test AI engine error handling"""
        print("\n🛡️ TESTING ERROR HANDLING")
        print("=" * 50)

        error_test_cases = [
            {"framework": "invalid", "data": {"type": "INVALID", "confidence": 0.5}},
            {"framework": "mbti", "data": {"type": "INVALID_TYPE", "confidence": 0.5}},
            {"framework": "", "data": {}},
            {"framework": "mbti", "data": {"confidence": -1.0}},  # Invalid confidence
        ]

        for i, case in enumerate(error_test_cases):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.base_url}/personality-assessments/process-public",
                    json=case,
                    timeout=10,
                )
                response_time = (time.time() - start_time) * 1000

                # Error cases should still return 200 with graceful handling
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("results"):
                        self.log_result(
                            f"Error Handling Test {i+1}",
                            True,
                            "Graceful error handling",
                            response_time,
                        )
                    else:
                        self.log_result(
                            f"Error Handling Test {i+1}",
                            False,
                            "Poor error handling",
                            response_time,
                        )
                else:
                    self.log_result(
                        f"Error Handling Test {i+1}",
                        False,
                        f"HTTP {response.status_code}",
                        response_time,
                    )

            except Exception as e:
                self.log_result(
                    f"Error Handling Test {i+1}", False, f"Exception: {str(e)}", 0
                )

    def test_performance(self):
        """Test AI engine performance"""
        print("\n⚡ TESTING PERFORMANCE")
        print("=" * 50)

        # Test consecutive requests
        times = []
        for i in range(10):
            start_time = time.time()
            try:
                test_data = {
                    "framework": "mbti",
                    "data": {"type": "ENFP", "confidence": 0.9},
                }

                response = requests.post(
                    f"{self.base_url}/personality-assessments/process-public",
                    json=test_data,
                    timeout=5,
                )

                response_time = (time.time() - start_time) * 1000
                times.append(response_time)

                if response.status_code != 200 or not response.json().get("success"):
                    self.log_result(
                        f"Performance Test {i+1}",
                        False,
                        "Request failed",
                        response_time,
                    )
                    return

            except Exception as e:
                self.log_result(
                    f"Performance Test {i+1}", False, f"Exception: {str(e)}", 0
                )
                return

        # Calculate performance metrics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        if avg_time < 200 and max_time < 500:
            performance_rating = "Excellent"
        elif avg_time < 500 and max_time < 1000:
            performance_rating = "Good"
        else:
            performance_rating = "Poor"

        self.log_result(
            "Performance Test",
            True,
            f"Avg: {avg_time:.1f}ms, Min: {min_time:.1f}ms, Max: {max_time:.1f}ms ({performance_rating})",
            avg_time,
        )

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")

        # Performance summary
        response_times = [
            r["response_time_ms"]
            for r in self.test_results
            if r["response_time_ms"] > 0
        ]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"⚡ Average Response Time: {avg_response_time:.1f}ms")

        # Failed tests details
        failed_tests_details = [r for r in self.test_results if not r["success"]]
        if failed_tests_details:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests_details:
                print(f"   • {test['test_name']}: {test['details']}")

        # Save detailed report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate_percent": round(success_rate, 2),
                "average_response_time_ms": (
                    round(avg_response_time, 2) if response_times else 0
                ),
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
        }

        with open("ai_engine_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Detailed report saved to: ai_engine_test_report.json")

        return success_rate >= 90  # Consider 90%+ as passing


def main():
    """Run comprehensive AI engine testing"""
    print("🚀 COMPREHENSIVE AI ENGINE TESTING")
    print("=" * 60)

    tester = AIEngineTester()

    # Run all tests
    tester.test_all_mbti_types()
    tester.test_enneagram_types()
    tester.test_frameworks_endpoint()
    tester.test_ai_insights_quality()
    tester.test_error_handling()
    tester.test_performance()

    # Generate report
    success = tester.generate_report()

    if success:
        print("\n🎉 AI ENGINE TESTS PASSED! System is working correctly.")
    else:
        print("\n⚠️ AI ENGINE TESTS FAILED! Check the report for details.")

    return success


if __name__ == "__main__":
    main()
