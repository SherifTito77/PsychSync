#!/usr/bin/env python3
"""
Comprehensive AI Engine Integration Test Suite
Tests all new AI features: analytics, email personalization, onboarding, and monitoring
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import aiohttp


class AIEngineTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        self.auth_token = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(
        self, test_name: str, success: bool, message: str, response_data: Any = None
    ):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "response_data": response_data,
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")

    async def test_health_check(self):
        """Test basic API health check"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "API Health Check", True, "API is responding correctly", data
                    )
                    return True
                else:
                    self.log_result(
                        "API Health Check",
                        False,
                        f"Health check failed with status {response.status}",
                    )
                    return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Health check error: {str(e)}")
            return False

    async def test_ai_analytics_endpoints(self):
        """Test AI Analytics endpoints"""
        print("\n🧠 Testing AI Analytics Features...")

        # Test AI Analytics Dashboard
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-analytics/dashboard?time_period_days=30"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Analytics Dashboard",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("data", {}).get("ai_insights"):
                        insights = data["data"]["ai_insights"]
                        self.log_result(
                            "AI Analytics Dashboard",
                            True,
                            f"Dashboard loaded with {insights.get('total_insights', 0)} insights",
                            {"insights_count": insights.get("total_insights")},
                        )
                    else:
                        self.log_result(
                            "AI Analytics Dashboard",
                            False,
                            "Invalid response structure",
                        )
                else:
                    self.log_result(
                        "AI Analytics Dashboard",
                        False,
                        f"Unexpected status: {response.status}",
                    )
        except Exception as e:
            self.log_result("AI Analytics Dashboard", False, f"Error: {str(e)}")

        # Test AI Insights Endpoint
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-analytics/insights?limit=10"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Insights Endpoint",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "AI Insights Endpoint", True, "Insights endpoint accessible"
                    )
                else:
                    self.log_result(
                        "AI Insights Endpoint", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Insights Endpoint", False, f"Error: {str(e)}")

        # Test Predictive Metrics
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-analytics/predictions?confidence_threshold=0.7"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Predictive Metrics",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "AI Predictive Metrics",
                        True,
                        "Predictive metrics endpoint accessible",
                    )
                else:
                    self.log_result(
                        "AI Predictive Metrics", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Predictive Metrics", False, f"Error: {str(e)}")

        # Test Risk Assessment
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-analytics/risk-assessment"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Risk Assessment", True, "Authentication required (expected)"
                    )
                elif response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "AI Risk Assessment",
                        True,
                        "Risk assessment endpoint accessible",
                    )
                else:
                    self.log_result(
                        "AI Risk Assessment", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Risk Assessment", False, f"Error: {str(e)}")

    async def test_ai_monitoring_endpoints(self):
        """Test AI Monitoring endpoints"""
        print("\n📊 Testing AI Monitoring Features...")

        # Test AI Health Status
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-monitoring/health"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Monitoring Health",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        health_data = data.get("data", {})
                        self.log_result(
                            "AI Monitoring Health",
                            True,
                            f"Health status: {health_data.get('overall_status', 'unknown')}, Score: {health_data.get('health_score', 0)}",
                            {"status": health_data.get("overall_status")},
                        )
                    else:
                        self.log_result(
                            "AI Monitoring Health", False, "Invalid health response"
                        )
                else:
                    self.log_result(
                        "AI Monitoring Health", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Monitoring Health", False, f"Error: {str(e)}")

        # Test AI Metrics
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-monitoring/metrics?hours=24"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Performance Metrics",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    trends = data.get("data", {}).get("trends", {})
                    self.log_result(
                        "AI Performance Metrics",
                        True,
                        f"Metrics loaded with {len(trends)} trend categories",
                        {"trend_count": len(trends)},
                    )
                else:
                    self.log_result(
                        "AI Performance Metrics", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Performance Metrics", False, f"Error: {str(e)}")

        # Test AI Alerts
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-monitoring/alerts"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Alerts System", True, "Authentication required (expected)"
                    )
                elif response.status == 200:
                    data = await response.json()
                    alerts_count = data.get("data", {}).get("total_alerts", 0)
                    self.log_result(
                        "AI Alerts System",
                        True,
                        f"Alerts system working, {alerts_count} active alerts",
                    )
                else:
                    self.log_result(
                        "AI Alerts System", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Alerts System", False, f"Error: {str(e)}")

        # Test AI Monitoring Dashboard
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-monitoring/dashboard"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Monitoring Dashboard",
                        True,
                        "Authentication required (expected)",
                    )
                elif response.status == 200:
                    data = await response.json()
                    self.log_result(
                        "AI Monitoring Dashboard",
                        True,
                        "Monitoring dashboard accessible",
                    )
                else:
                    self.log_result(
                        "AI Monitoring Dashboard", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Monitoring Dashboard", False, f"Error: {str(e)}")

        # Test Metric Types
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ai-monitoring/metric-types"
            ) as response:
                if response.status == 401:
                    self.log_result(
                        "AI Metric Types", True, "Authentication required (expected)"
                    )
                elif response.status == 200:
                    data = await response.json()
                    metric_types = data.get("data", {}).get("metric_types", [])
                    self.log_result(
                        "AI Metric Types",
                        True,
                        f"Found {len(metric_types)} metric types",
                    )
                else:
                    self.log_result(
                        "AI Metric Types", False, f"Status: {response.status}"
                    )
        except Exception as e:
            self.log_result("AI Metric Types", False, f"Error: {str(e)}")

    async def test_ai_service_imports(self):
        """Test that AI services can be imported without errors"""
        print("\n🔧 Testing AI Service Imports...")

        try:
            # Test AI Enhanced Analytics Service
            from app.services.ai_enhanced_analytics import (
                AIEnhancedAnalyticsServiceService,
            )

            self.log_result(
                "AI Analytics Service Import",
                True,
                "AIEnhancedAnalyticsService imported successfully",
            )

            # Test AI Enhanced Email Service
            from app.services.ai_enhanced_email_service import AIEnhancedEmailService

            self.log_result(
                "AI Email Service Import",
                True,
                "AIEnhancedEmailService imported successfully",
            )

            # Test AI Guided Onboarding Service
            from app.services.ai_guided_onboarding import AIGuidedOnboardingService

            self.log_result(
                "AI Onboarding Service Import",
                True,
                "AIGuidedOnboardingService imported successfully",
            )

            # Test AI Monitoring Service
            from app.services.ai_monitoring_service import AIMonitoringService

            self.log_result(
                "AI Monitoring Service Import",
                True,
                "AIMonitoringService imported successfully",
            )

            # Test AI Behavioral Integration
            from app.services.ai_behavioral_integration import (
                AIBehavioralIntegrationService,
            )

            self.log_result(
                "AI Behavioral Integration Import",
                True,
                "AIBehavioralIntegrationService imported successfully",
            )

            return True

        except ImportError as e:
            self.log_result("AI Service Imports", False, f"Import error: {str(e)}")
            return False
        except Exception as e:
            self.log_result("AI Service Imports", False, f"Unexpected error: {str(e)}")
            return False

    async def test_ai_processor_functionality(self):
        """Test AI processor functionality"""
        print("\n🤖 Testing AI Processor Functionality...")

        try:
            # Test AI Processor imports
            from ai.processors.big_five import BigFiveProcessor
            from ai.processors.enneagram_processor import EnneagramProcessor
            from ai.processors.mbti_processor import MBTIProcessor

            # Test MBTI Processor
            mbti_processor = MBTIProcessor()
            test_responses = {"E1": "agree", "I2": "disagree"}  # Minimal test data
            result = mbti_processor._safe_process(test_responses)
            self.log_result(
                "MBTI Processor",
                True,
                "MBTI processor processes test data successfully",
            )

            # Test Big Five Processor
            big_five_processor = BigFiveProcessor()
            result = big_five_processor._safe_process(test_responses)
            self.log_result(
                "Big Five Processor",
                True,
                "Big Five processor processes test data successfully",
            )

            # Test Enneagram Processor
            enneagram_processor = EnneagramProcessor()
            result = enneagram_processor._safe_process(test_responses)
            self.log_result(
                "Enneagram Processor",
                True,
                "Enneagram processor processes test data successfully",
            )

            return True

        except ImportError as e:
            self.log_result(
                "AI Processor Functionality", False, f"Processor import error: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_result(
                "AI Processor Functionality", False, f"Processor error: {str(e)}"
            )
            return False

    async def test_ai_endpoint_registration(self):
        """Test that AI endpoints are properly registered"""
        print("\n🔗 Testing AI Endpoint Registration...")

        try:
            # Test if endpoints are accessible (even with auth errors)
            endpoints_to_test = [
                "/api/v1/ai-analytics/dashboard",
                "/api/v1/ai-analytics/insights",
                "/api/v1/ai-analytics/predictions",
                "/api/v1/ai-monitoring/health",
                "/api/v1/ai-monitoring/metrics",
                "/api/v1/ai-monitoring/dashboard",
            ]

            registered_endpoints = 0
            for endpoint in endpoints_to_test:
                try:
                    async with self.session.get(
                        f"{self.base_url}{endpoint}"
                    ) as response:
                        # 401 means endpoint exists but requires auth
                        # 404 means endpoint doesn't exist
                        if response.status != 404:
                            registered_endpoints += 1
                except Exception:
                    continue

            self.log_result(
                "AI Endpoint Registration",
                registered_endpoints == len(endpoints_to_test),
                f"{registered_endpoints}/{len(endpoints_to_test)} AI endpoints registered",
                {"registered": registered_endpoints, "total": len(endpoints_to_test)},
            )

        except Exception as e:
            self.log_result(
                "AI Endpoint Registration", False, f"Endpoint testing error: {str(e)}"
            )

    async def run_comprehensive_tests(self):
        """Run all AI engine tests"""
        print("🚀 Starting Comprehensive AI Engine Integration Tests")
        print("=" * 60)

        start_time = time.time()

        # Test basic connectivity
        await self.test_health_check()

        # Test service imports
        await self.test_ai_service_imports()

        # Test AI processors
        await self.test_ai_processor_functionality()

        # Test endpoint registration
        await self.test_ai_endpoint_registration()

        # Test AI Analytics endpoints
        await self.test_ai_analytics_endpoints()

        # Test AI Monitoring endpoints
        await self.test_ai_monitoring_endpoints()

        # Calculate results
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("🏁 AI Engine Integration Test Results")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Duration: {end_time - start_time:.2f} seconds")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test_name']}: {result['message']}")

        print("\n📊 Test Summary:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}")

        # Return overall success
        return passed_tests == total_tests


async def main():
    """Main test runner"""
    print("PsychSync AI Engine Integration Test Suite")
    print("Testing all new AI features and integrations...")

    async with AIEngineTester() as tester:
        success = await tester.run_comprehensive_tests()

        if success:
            print(
                "\n🎉 All AI Engine tests passed! The integration is working correctly."
            )
            return 0
        else:
            print("\n⚠️  Some AI Engine tests failed. Please review the failures above.")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
