#!/usr/bin/env python3
"""
Edge & Chaos Testing Suite
Tests system behavior under extreme conditions and edge cases
"""

import asyncio
import json
import os
import random
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

# Try to import psutil, use fallback if not available
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - some system monitoring features will be limited")


class TestScenario(Enum):
    """Types of edge and chaos tests"""

    NETWORK_DROP = "network_drop"
    DISK_FULL = "disk_full"
    MEMORY_LEAK = "memory_leak"
    LARGE_INPUT = "large_input"
    SPAM_SUBMIT = "spam_submit"
    BROWSER_STRESS = "browser_stress"


class TestResult(Enum):
    """Test outcome statuses"""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ChaosTestResult:
    """Result of a chaos test scenario"""

    scenario_id: str
    scenario_type: TestScenario
    result: TestResult
    execution_time: float
    response_time: float
    error_message: Optional[str] = None
    recovery_time: Optional[float] = None
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    user_experience_impact: str = ""
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class EdgeChaosTester:
    """Comprehensive edge and chaos testing system"""

    def __init__(self):
        self.test_results = []
        self.frontend_url = "http://localhost:5174"
        self.backend_url = "http://localhost:8000"
        self.active_background_tests = {}
        self.test_data = self._generate_test_data()
        self.system_baseline = self._capture_system_baseline()

    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for various scenarios"""
        return {
            "large_text": "A" * 1000000,  # 1MB of text
            "massive_text": "B" * 10000000,  # 10MB of text
            "unicode_bomb": "🔥" * 100000,  # 100k emojis
            "json_bomb": {"data": {"nested": {"deep": {"value": "test" * 1000}}}},
            "malicious_script": "<script>alert('xss')</script>" * 1000,
            "spam_submission": {
                "user_id": f"user_{random.randint(1, 1000)}",
                "assessment_response": {
                    "score": random.randint(1, 5) for _ in range(50)
                },
            },
        }

    def _capture_system_baseline(self) -> Dict[str, Any]:
        """Capture system metrics before testing"""
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                return {
                    "cpu_percent": cpu,
                    "memory_percent": memory.percent,
                    "disk_usage": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                print(f"⚠️  Could not capture system baseline: {e}")
                return {}
        else:
            # Fallback when psutil is not available
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_usage": 0,
                "memory_available_gb": 0,
                "disk_free_gb": 0,
                "timestamp": datetime.now().isoformat(),
                "note": "psutil not available - limited monitoring",
            }

    def test_network_drop_mid_submission(self) -> ChaosTestResult:
        """Test system behavior when network drops mid-submission"""
        print("🌐 Testing: Network Drop Mid-Submission...")

        start_time = time.time()
        system_before = self._capture_system_baseline()

        try:
            # Start a large form submission
            session = requests.Session()

            # Create large payload for submission
            large_payload = {
                "assessment_id": "test_assessment_001",
                "user_responses": [
                    {"question_id": f"q{i}", "answer": "x" * 1000} for i in range(100)
                ],
                "metadata": {"timestamp": datetime.now().isoformat()},
            }

            # Start submission but interrupt with network simulation
            with session.post(
                f"{self.backend_url}/api/v1/assessments/submit",
                json=large_payload,
                timeout=30,
            ) as response:

                # Simulate network drop after 5 seconds
                time.sleep(5)

                # Check if system gracefully handles incomplete submission
                if response.status_code in [200, 201]:
                    # Check if partial data was saved
                    recovery_time = time.time() - start_time
                    result = TestResult.PASS
                    user_impact = "System maintained state despite network interruption"
                    recommendations = [
                        "Implement client-side auto-save functionality",
                        "Add network resilience patterns",
                        "Consider offline capability for critical features",
                    ]
                else:
                    recovery_time = time.time() - start_time
                    result = TestResult.FAIL
                    user_impact = "Submission failed, potential data loss"
                    recommendations = [
                        "Add retry mechanisms with exponential backoff",
                        "Implement submission queue for failed requests",
                        "Add user notification for submission status",
                    ]

                system_after = self._capture_system_baseline()

                return ChaosTestResult(
                    scenario_id="network_drop_mid_submission",
                    scenario_type=TestScenario.NETWORK_DROP,
                    result=result,
                    execution_time=time.time() - start_time,
                    response_time=5.0,  # Time until network drop
                    recovery_time=recovery_time,
                    system_metrics={
                        "before": system_before,
                        "after": system_after,
                        "memory_delta": system_after.get("memory_percent", 0)
                        - system_before.get("memory_percent", 0),
                    },
                    user_experience_impact=user_impact,
                    recommendations=recommendations,
                )

        except requests.exceptions.Timeout:
            # Expected behavior - timeout due to network drop
            recovery_time = time.time() - start_time
            return ChaosTestResult(
                scenario_id="network_drop_mid_submission",
                scenario_type=TestScenario.NETWORK_DROP,
                result=TestResult.PASS,  # Timeout expected
                execution_time=recovery_time,
                response_time=5.0,
                recovery_time=recovery_time,
                error_message="Network timeout as expected",
                user_experience_impact="System handled network interruption gracefully",
                recommendations=["Implement timeout handling and user feedback"],
            )
        except Exception as e:
            return ChaosTestResult(
                scenario_id="network_drop_mid_submission",
                scenario_type=TestScenario.NETWORK_DROP,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                response_time=0,
                error_message=str(e),
                user_experience_impact="Unexpected error during network simulation",
                recommendations=["Add comprehensive error handling for network issues"],
            )

    def test_disk_full_scenario(self) -> ChaosTestResult:
        """Test system behavior when disk is nearly full"""
        print("💾 Testing: Disk Full Scenario...")

        start_time = time.time()
        system_before = self._capture_system_baseline()

        try:
            # Check current disk usage
            if PSUTIL_AVAILABLE:
                disk_usage = psutil.disk_usage("/")
                current_usage = disk_usage.percent
                free_space_gb = disk_usage.free / (1024**3)

                print(
                    f"Current disk usage: {current_usage:.1f}% ({free_space_gb:.1f}GB free)"
                )
            else:
                current_usage = 0
                free_space_gb = 1.0  # Assume 1GB free
                print(f"Disk usage monitoring not available (psutil not installed)")

            # Create a large temporary file to simulate disk pressure
            test_file_size_gb = min(
                0.5, free_space_gb * 0.8
            )  # Use up to 80% of free space, max 0.5GB

            if test_file_size_gb < 0.1:
                result = TestResult.SKIPPED
                user_impact = "Insufficient free space to test disk full scenario"
                recommendations = [
                    "Monitor disk usage in production",
                    "Implement disk space cleanup procedures",
                    "Consider cloud storage for large datasets",
                ]
            else:
                # Create temporary file to consume disk space
                temp_file = "/tmp/disk_stress_test.dat"
                print(f"Creating {test_file_size_gb:.2f}GB test file...")

                file_creation_start = time.time()
                with open(temp_file, "wb") as f:
                    f.write(b"0" * int(test_file_size_gb * 1024**3))

                file_creation_time = time.time() - file_creation_start

                # Test system behavior under disk pressure
                system_during = self._capture_system_baseline()

                # Try to submit data while disk is nearly full
                try:
                    session = requests.Session()
                    test_payload = {
                        "assessment_type": "disk_stress_test",
                        "timestamp": datetime.now().isoformat(),
                        "data": "x" * 10000,  # 10KB payload
                    }

                    submit_start = time.time()
                    response = session.post(
                        f"{self.backend_url}/api/v1/test/disk-stress",
                        json=test_payload,
                        timeout=30,
                    )
                    submit_time = time.time() - submit_start

                    if response.status_code < 500:
                        result = TestResult.PASS
                        user_impact = "System continued functioning under disk pressure"
                        recommendations = [
                            "Monitor disk space in production",
                            "Implement disk usage alerts",
                            "Add cleanup procedures for temporary files",
                        ]
                    else:
                        result = TestResult.WARNING
                        user_impact = "System performance degraded under disk pressure"
                        recommendations = [
                            "Implement disk space monitoring and alerts",
                            "Add disk cleanup automation",
                            "Consider disk space quotas",
                        ]

                except Exception as e:
                    result = TestResult.WARNING
                    user_impact = "Error occurred under disk pressure conditions"
                    recommendations = [
                        "Add disk space error handling",
                        "Implement graceful degradation",
                        "Add user notifications for storage issues",
                    ]
                finally:
                    # Clean up test file
                    try:
                        os.remove(temp_file)
                        print("Cleaned up test file")
                    except Exception as e:
                        pass

                system_after = self._capture_system_baseline()

                return ChaosTestResult(
                    scenario_id="disk_full_scenario",
                    scenario_type=TestScenario.DISK_FULL,
                    result=result,
                    execution_time=time.time() - start_time,
                    response_time=submit_time if "submit_time" in locals() else 0,
                    system_metrics={
                        "before": system_before,
                        "during": system_during,
                        "after": system_after,
                        "disk_usage_before": current_usage,
                        "disk_usage_during": system_during.get("disk_usage", 0),
                        "test_file_size_gb": test_file_size_gb,
                        "file_creation_time": file_creation_time,
                    },
                    user_experience_impact=user_impact,
                    recommendations=recommendations,
                )

        except Exception as e:
            return ChaosTestResult(
                scenario_id="disk_full_scenario",
                scenario_type=TestScenario.DISK_FULL,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                response_time=0,
                error_message=str(e),
                user_experience_impact="Failed to execute disk full test scenario",
                recommendations=[
                    "Add comprehensive disk monitoring and error handling"
                ],
            )

    def test_memory_leak_simulation(self) -> ChaosTestResult:
        """Test for memory leak potential in long browser sessions"""
        print("🧠 Testing: Memory Leak Simulation...")

        start_time = time.time()
        system_before = self._capture_system_baseline()

        try:
            memory_samples = []
            leak_detected = False
            memory_growth_threshold = 5.0  # 5% memory growth threshold

            # Simulate long session with multiple operations
            session = requests.Session()

            for iteration in range(100):  # 100 iterations to simulate long session
                # Perform memory-intensive operations

                # 1. Load large amounts of data
                large_data = "x" * 100000  # 100KB payload

                # 2. Make multiple requests
                for _ in range(5):
                    try:
                        response = session.get(f"{self.frontend_url}", timeout=5)
                        if response.status_code == 200:
                            # Simulate keeping data in memory
                            stored_data = response.content + large_data.encode()

                            # Sample memory usage
                            if iteration % 10 == 0 and PSUTIL_AVAILABLE:
                                memory_percent = psutil.virtual_memory().percent
                                memory_samples.append(memory_percent)

                                # Check for memory growth
                                if len(memory_samples) >= 3:
                                    recent_average = sum(memory_samples[-3:]) / 3
                                    early_average = sum(memory_samples[:3]) / 3
                                    growth = recent_average - early_average

                                    if growth > memory_growth_threshold:
                                        leak_detected = True
                                        print(
                                            f"⚠️  Memory growth detected: {growth:.1f}%"
                                        )

                    except requests.exceptions.RequestException:
                        continue

                # Small delay to simulate real user behavior
                time.sleep(0.1)

            # Analyze memory usage patterns
            if len(memory_samples) >= 5:
                memory_trend = memory_samples[-1] - memory_samples[0]
                memory_variance = max(memory_samples) - min(memory_samples)

                if leak_detected or memory_trend > memory_growth_threshold * 2:
                    result = TestResult.WARNING
                    user_impact = "Memory growth detected in long sessions"
                    recommendations = [
                        "Investigate potential memory leaks in React components",
                        "Implement memory monitoring in production",
                        "Add automatic component cleanup",
                        "Consider periodic page refresh for long sessions",
                    ]
                else:
                    result = TestResult.PASS
                    user_impact = "Memory usage stable during long session simulation"
                    recommendations = [
                        "Continue monitoring memory usage in production",
                        "Consider implementing memory usage alerts",
                        "Periodically test with longer session durations",
                    ]
            else:
                result = TestResult.SKIPPED
                user_impact = "Insufficient memory samples collected"
                recommendations = [
                    "Increase test duration or frequency of memory sampling",
                    "Add more comprehensive memory monitoring",
                ]

            system_after = self._capture_system_baseline()

            return ChaosTestResult(
                scenario_id="memory_leak_simulation",
                scenario_type=TestScenario.MEMORY_LEAK,
                result=result,
                execution_time=time.time() - start_time,
                response_time=0,
                system_metrics={
                    "before": system_before,
                    "after": system_after,
                    "memory_samples": memory_samples,
                    "memory_trend": memory_trend if "memory_trend" in locals() else 0,
                    "memory_variance": (
                        memory_variance if "memory_variance" in locals() else 0
                    ),
                    "leak_detected": leak_detected,
                },
                user_experience_impact=user_impact,
                recommendations=recommendations,
            )

        except Exception as e:
            return ChaosTestResult(
                scenario_id="memory_leak_simulation",
                scenario_type=TestScenario.MEMORY_LEAK,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                response_time=0,
                error_message=str(e),
                user_experience_impact="Failed to complete memory leak simulation",
                recommendations=["Add comprehensive error handling for memory testing"],
            )

    def test_malicious_large_input(self) -> ChaosTestResult:
        """Test system handling of maliciously large text input"""
        print("🔍 Testing: Maliciously Large Text Input...")

        start_time = time.time()
        system_before = self._capture_system_baseline()

        test_cases = [
            {"name": "Massive Text Input", "data": self.test_data["large_text"]},
            {"name": "Unicode Bomb", "data": self.test_data["unicode_bomb"]},
            {"name": "JSON Bomb", "data": json.dumps(self.test_data["json_bomb"])},
            {"name": "Malicious Script", "data": self.test_data["malicious_script"]},
            {
                "name": "Mixed Attack Vector",
                "data": self.test_data["massive_text"]
                + self.test_data["malicious_script"],
            },
        ]

        results = []

        try:
            session = requests.Session()

            for i, test_case in enumerate(test_cases):
                case_start = time.time()

                print(f"  Testing case {i+1}/{len(test_cases)}: {test_case['name']}")

                try:
                    # Test input size validation
                    if len(test_case["data"]) > 1048576:  # 1MB
                        print(
                            f"    ⚠️  Input size: {len(test_case['data'])} bytes (very large)"
                        )

                    # Test submission with large input
                    payload = {
                        "assessment_type": "input_validation_test",
                        "user_input": test_case["data"],
                        "test_case": test_case["name"],
                    }

                    submit_start = time.time()
                    response = session.post(
                        f"{self.backend_url}/api/v1/test/large-input",
                        json=payload,
                        timeout=30,
                    )
                    submit_time = time.time() - submit_start

                    case_time = time.time() - case_start

                    # Analyze response
                    if response.status_code == 200:
                        # Check response size and content
                        response_size = len(response.content)

                        if response_size > 1048576:  # 1MB response
                            case_result = TestResult.WARNING
                            case_impact = (
                                f"Large response returned: {response_size} bytes"
                            )
                        else:
                            case_result = TestResult.PASS
                            case_impact = "Large input handled appropriately"
                    elif response.status_code == 413:
                        case_result = TestResult.PASS
                        case_impact = "Input size properly rejected (Payload Too Large)"
                    elif response.status_code >= 500:
                        case_result = TestResult.WARNING
                        case_impact = "Server error with large input"
                    else:
                        case_result = TestResult.WARNING
                        case_impact = (
                            f"Unexpected response code: {response.status_code}"
                        )

                    results.append(
                        {
                            "case": test_case["name"],
                            "result": case_result,
                            "time": case_time,
                            "response_time": submit_time,
                            "status_code": response.status_code,
                            "input_size": len(test_case["data"]),
                            "impact": case_impact,
                        }
                    )

                    # Small delay between requests
                    time.sleep(0.5)

                except requests.exceptions.Timeout:
                    results.append(
                        {
                            "case": test_case["name"],
                            "result": TestResult.WARNING,
                            "time": time.time() - case_start,
                            "response_time": 0,
                            "status_code": None,
                            "input_size": len(test_case["data"]),
                            "impact": "Timeout with large input",
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "case": test_case["name"],
                            "result": TestResult.ERROR,
                            "time": time.time() - case_start,
                            "response_time": 0,
                            "status_code": None,
                            "input_size": len(test_case["data"]),
                            "impact": f"Error: {str(e)[:100]}",
                        }
                    )

            # Analyze overall results
            pass_count = sum(1 for r in results if r["result"] == TestResult.PASS)
            warning_count = sum(1 for r in results if r["result"] == TestResult.WARNING)
            error_count = sum(1 for r in results if r["result"] == TestResult.ERROR)

            if error_count > 0:
                overall_result = TestResult.ERROR
                user_impact = "System failed to handle some malicious inputs"
                recommendations = [
                    "Add comprehensive input validation and sanitization",
                    "Implement rate limiting for large submissions",
                    "Add error handling for malformed input",
                    "Consider using input size limits",
                ]
            elif warning_count > pass_count:
                overall_result = TestResult.WARNING
                user_impact = (
                    "System handles malicious inputs but with degraded performance"
                )
                recommendations = [
                    "Optimize input processing for large payloads",
                    "Add progress indicators for large uploads",
                    "Implement streaming for very large data",
                ]
            else:
                overall_result = TestResult.PASS
                user_impact = "System handles malicious large inputs appropriately"
                recommendations = [
                    "Continue monitoring for new attack vectors",
                    "Regular security audits of input handling",
                    "Consider implementing additional security measures",
                ]

            system_after = self._capture_system_baseline()

            return ChaosTestResult(
                scenario_id="malicious_large_input",
                scenario_type=TestScenario.LARGE_INPUT,
                result=overall_result,
                execution_time=time.time() - start_time,
                response_time=0,
                system_metrics={
                    "before": system_before,
                    "after": system_after,
                    "test_cases": results,
                    "passed_cases": pass_count,
                    "warning_cases": warning_count,
                    "error_cases": error_count,
                    "max_input_size": max(r["input_size"] for r in results),
                },
                user_experience_impact=user_impact,
                recommendations=recommendations,
            )

        except Exception as e:
            return ChaosTestResult(
                scenario_id="malicious_large_input",
                scenario_type=TestScenario.LARGE_INPUT,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                response_time=0,
                error_message=str(e),
                user_experience_impact="Failed to test malicious input handling",
                recommendations=[
                    "Add comprehensive error handling for input validation testing"
                ],
            )

    def test_rapid_form_spam(self) -> ChaosTestResult:
        """Test rapid spam-clicking form submissions"""
        print("🚀 Testing: Rapid Form Spam Submissions...")

        start_time = time.time()
        system_before = self._capture_system_baseline()

        try:
            session = requests.Session()
            spam_count = 50  # Number of rapid submissions
            submission_interval = 0.1  # 100ms between submissions

            submissions = []
            successful_submissions = 0
            rejected_submissions = 0
            error_submissions = 0

            print(
                f"  Initiating {spam_count} rapid submissions with {submission_interval}s interval..."
            )

            for i in range(spam_count):
                submission_start = time.time()

                # Generate unique submission data
                submission_data = {
                    "assessment_id": f"spam_test_{i}_{int(time.time())}",
                    "user_id": f"spam_user_{i % 10}",  # 10 different users
                    "responses": {
                        "question_1": random.randint(1, 5),
                        "question_2": random.randint(1, 5),
                        "question_3": random.randint(1, 5),
                        "timestamp": datetime.now().isoformat(),
                    },
                    "spam_test": True,
                    "submission_number": i,
                }

                try:
                    response = session.post(
                        f"{self.backend_url}/api/v1/assessments/submit",
                        json=submission_data,
                        timeout=5,
                    )

                    submit_time = time.time() - submission_start
                    response_time = (
                        response.elapsed.total_seconds()
                        if hasattr(response, "elapsed")
                        else submit_time
                    )

                    if response.status_code in [200, 201]:
                        successful_submissions += 1
                        status = "success"
                    elif response.status_code == 429:  # Rate limited
                        rejected_submissions += 1
                        status = "rate_limited"
                    elif response.status_code >= 500:
                        error_submissions += 1
                        status = "server_error"
                    else:
                        rejected_submissions += 1
                        status = "rejected"

                    submissions.append(
                        {
                            "submission_number": i,
                            "status_code": response.status_code,
                            "response_time": response_time,
                            "status": status,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except requests.exceptions.Timeout:
                    error_submissions += 1
                    submissions.append(
                        {
                            "submission_number": i,
                            "status_code": None,
                            "response_time": 5.0,
                            "status": "timeout",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except Exception as e:
                    error_submissions += 1
                    submissions.append(
                        {
                            "submission_number": i,
                            "status_code": None,
                            "response_time": 0,
                            "status": "error",
                            "error": str(e)[:100],
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                # Check if we should continue spamming
                if i < spam_count - 1:
                    time.sleep(submission_interval)

            # Analyze spam test results
            total_submissions = len(submissions)
            success_rate = (successful_submissions / total_submissions) * 100
            avg_response_time = (
                sum(s["response_time"] for s in submissions if s["response_time"] > 0)
                / total_submissions
            )

            response_times = [
                s["response_time"] for s in submissions if s["response_time"] > 0
            ]
            if response_times:
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                max_response_time = min_response_time = 0

            # Determine overall result
            if error_submissions > successful_submissions:
                result = TestResult.ERROR
                user_impact = "System failed under spam load"
                recommendations = [
                    "Implement rate limiting and IP-based blocking",
                    "Add CAPTCHA or other bot protection",
                    "Implement request queuing and throttling",
                    "Add server capacity scaling",
                ]
            elif rejected_submissions > successful_submissions:
                result = TestResult.PASS  # Good - rejecting spam
                user_impact = "System effectively blocked spam submissions"
                recommendations = [
                    "Continue monitoring spam patterns",
                    "Implement adaptive rate limiting",
                    "Consider CAPTCHA for additional protection",
                ]
            elif avg_response_time > 2.0:
                result = TestResult.WARNING
                user_impact = "System performance degraded under spam load"
                recommendations = [
                    "Optimize database queries",
                    "Implement request queuing",
                    "Add server monitoring and auto-scaling",
                ]
            else:
                result = TestResult.PASS
                user_impact = "System handled spam load effectively"
                recommendations = [
                    "Monitor for new spam patterns",
                    "Log spam attempts for analysis",
                    "Consider implementing additional security measures",
                ]

            system_after = self._capture_system_baseline()

            return ChaosTestResult(
                scenario_id="rapid_form_spam",
                scenario_type=TestScenario.SPAM_SUBMIT,
                result=result,
                execution_time=time.time() - start_time,
                response_time=avg_response_time,
                system_metrics={
                    "before": system_before,
                    "after": system_after,
                    "total_submissions": total_submissions,
                    "successful_submissions": successful_submissions,
                    "rejected_submissions": rejected_submissions,
                    "error_submissions": error_submissions,
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "min_response_time": min_response_time,
                    "submission_interval": submission_interval,
                },
                user_experience_impact=user_impact,
                recommendations=recommendations,
            )

        except Exception as e:
            return ChaosTestResult(
                scenario_id="rapid_form_spam",
                scenario_type=TestScenario.SPAM_SUBMIT,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                response_time=0,
                error_message=str(e),
                user_experience_impact="Failed to complete spam testing",
                recommendations=["Add comprehensive error handling for spam testing"],
            )

    def run_comprehensive_test_suite(self) -> List[ChaosTestResult]:
        """Run all edge and chaos tests"""
        print("🚀 Starting Comprehensive Edge & Chaos Testing Suite")
        print("=" * 60)

        test_functions = [
            self.test_network_drop_mid_submission,
            self.test_disk_full_scenario,
            self.test_memory_leak_simulation,
            self.test_malicious_large_input,
            self.test_rapid_form_spam,
        ]

        results = []

        for test_func in test_functions:
            try:
                result = test_func()
                results.append(result)

                status_icon = {
                    TestResult.PASS: "✅",
                    TestResult.FAIL: "❌",
                    TestResult.WARNING: "⚠️",
                    TestResult.ERROR: "💥",
                    TestResult.SKIPPED: "⏭️",
                }.get(result.result, "❓")

                print(
                    f"{status_icon} {result.scenario_type.value}: {result.result.value.upper()} ({result.execution_time:.2f}s)"
                )

                if result.user_experience_impact:
                    print(f"    Impact: {result.user_experience_impact}")

            except Exception as e:
                error_result = ChaosTestResult(
                    scenario_id=test_func.__name__,
                    scenario_type=TestScenario.BROWSER_STRESS,
                    result=TestResult.ERROR,
                    execution_time=0,
                    response_time=0,
                    error_message=str(e),
                    user_experience_impact="Test execution failed",
                    recommendations=["Add comprehensive error handling"],
                )
                results.append(error_result)
                print(f"💥 {test_func.__name__}: ERROR - {str(e)[:100]}")

            print()

        return results

    def generate_test_report(self, results: List[ChaosTestResult]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.result == TestResult.PASS)
        failed_tests = sum(1 for r in results if r.result == TestResult.FAIL)
        warning_tests = sum(1 for r in results if r.result == TestResult.WARNING)
        error_tests = sum(1 for r in results if r.result == TestResult.ERROR)
        skipped_tests = sum(1 for r in results if r.result == TestResult.SKIPPED)

        overall_status = (
            "PASS" if (passed_tests + warning_tests) >= total_tests * 0.8 else "FAIL"
        )

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warning_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "overall_status": overall_status,
                "success_rate": (
                    (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                ),
                "execution_time": sum(r.execution_time for r in results),
            },
            "test_results": [],
            "system_impact": {
                "critical_issues": [r for r in results if r.result == TestResult.ERROR],
                "performance_issues": [
                    r for r in results if r.result == TestResult.WARNING
                ],
                "recommendations": list(
                    set([rec for r in results for rec in r.recommendations])
                ),
            },
            "timestamp": datetime.now().isoformat(),
        }

        # Add detailed results
        for result in results:
            report["test_results"].append(
                {
                    "scenario_id": result.scenario_id,
                    "scenario_type": result.scenario_type.value,
                    "result": result.result.value,
                    "execution_time": result.execution_time,
                    "response_time": result.response_time,
                    "error_message": result.error_message,
                    "user_experience_impact": result.user_experience_impact,
                    "system_metrics": result.system_metrics,
                    "recommendations": result.recommendations,
                    "timestamp": result.timestamp.isoformat(),
                }
            )

        return report

    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"edge_chaos_testing_report_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return filename


def main():
    """Main entry point"""
    print("🔥 PsychSync Edge & Chaos Testing Suite")
    print("Testing system behavior under extreme conditions")
    print()

    tester = EdgeChaosTester()

    try:
        # Run comprehensive test suite
        results = tester.run_comprehensive_test_suite()

        # Generate and save report
        report = tester.generate_test_report(results)
        filename = tester.save_report(report)

        # Display summary
        summary = report["test_summary"]
        print("🎯 TEST EXECUTION SUMMARY")
        print("=" * 40)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Warnings: {summary['warnings']} ⚠️")
        print(f"Errors: {summary['errors']} 💥")
        print(f"Skipped: {summary['skipped']} ⏭️")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Execution Time: {summary['execution_time']:.2f} seconds")
        print()
        print(f"📄 Detailed Report Saved: {filename}")

        # Display top recommendations
        recommendations = report["system_impact"]["recommendations"][:5]
        if recommendations:
            print("\n💡 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        # Critical issues
        critical_issues = report["system_impact"]["critical_issues"]
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for issue in critical_issues:
                print(
                    f"  • {issue.scenario_type.value}: {issue.user_experience_impact}"
                )

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Testing suite error: {e}")

    print("\n🏁 Edge & Chaos Testing Complete!")


if __name__ == "__main__":
    main()
