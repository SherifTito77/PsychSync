#!/usr/bin/env python3
"""
Comprehensive Rate Limiting Test Suite
Combines Postman collection testing with load testing for complete validation

Usage:
    python comprehensive_rate_limiting_tests.py --all
    python comprehensive_rate_limiting_tests.py --postman-only
    python comprehensive_rate_limiting_tests.py --load-test-only --scenario=comprehensive
"""

import asyncio
import subprocess
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import requests

class ComprehensiveRateLimitingTester:
    """Comprehensive testing suite for rate limiting"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {
            "postman_tests": {},
            "load_tests": {},
            "health_check": {},
            "summary": {}
        }

    def run_health_check(self) -> Dict[str, Any]:
        """Run basic health check before testing"""
        print("🏥 Running health check...")

        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)

            health_data = {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds() * 1000,
                "healthy": response.status_code == 200,
                "timestamp": datetime.now().isoformat()
            }

            if response.status_code == 200:
                try:
                    health_json = response.json()
                    health_data["server_info"] = health_json
                except:
                    pass

            print(f"✅ Health check passed - {response.status_code} ({health_data['response_time']:.0f}ms)")
            return health_data

        except Exception as e:
            health_data = {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ Health check failed: {e}")
            return health_data

    def run_postman_tests(self) -> Dict[str, Any]:
        """Run Postman collection tests"""
        print("\n📱 Running Postman collection tests...")

        try:
            # Check if Postman collection exists
            collection_file = Path("postman_rate_limiting_collection.json")
            if not collection_file.exists():
                return {
                    "success": False,
                    "error": f"Postman collection not found: {collection_file}"
                }

            # Run postman test runner
            cmd = [
                sys.executable,
                "postman_test_runner.py",
                "--url", self.base_url,
                "--collection", str(collection_file),
                "--suite", "Rate Limiting",
                "--report", "json",
                "--output", "postman_rate_limiting_results.json"
            ]

            print(f"   Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            success = result.returncode == 0

            # Parse results if output file was created
            results_data = {}
            try:
                with open("postman_rate_limiting_results.json", 'r') as f:
                    results_data = json.load(f)
            except:
                pass

            postman_results = {
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "results_data": results_data,
                "timestamp": datetime.now().isoformat()
            }

            if success:
                print("✅ Postman tests completed successfully")
                if results_data.get("summary"):
                    summary = results_data["summary"]
                    print(f"   Total tests: {summary.get('total_tests', 0)}")
                    print(f"   Passed: {summary.get('passed_tests', 0)}")
                    print(f"   Failed: {summary.get('failed_tests', 0)}")
                    print(f"   Success rate: {summary.get('success_rate', 0):.1f}%")
            else:
                print("❌ Postman tests failed")
                if result.stderr:
                    print(f"   Error: {result.stderr}")

            return postman_results

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Postman tests timed out after 5 minutes",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def run_load_tests(self, scenario: str = "comprehensive") -> Dict[str, Any]:
        """Run load testing scenarios"""
        print(f"\n⚡ Running load tests - {scenario} scenario...")

        try:
            # Import and run load tester
            import rate_limiting_load_test

            # Setup load tester
            async with rate_limiting_load_test.RateLimitingLoadTester(self.base_url) as tester:
                results = []

                if scenario == "basic":
                    # Basic constant load test
                    users = await tester.setup_users(20)
                    results = await tester.run_constant_load_test(
                        requests_per_second=50,
                        duration=30,
                        users=users,
                        endpoint_types=["public", "auth"]
                    )

                elif scenario == "burst":
                    # Burst test
                    users = await tester.setup_users(50)
                    results = await tester.run_burst_test(
                        users=users,
                        burst_size=500,
                        burst_interval=2.0
                    )

                elif scenario == "comprehensive":
                    # Comprehensive test
                    users = await tester.setup_users(30)

                    # Multiple scenarios
                    basic_results = await tester.run_constant_load_test(
                        requests_per_second=30,
                        duration=20,
                        users=users,
                        endpoint_types=["public"]
                    )
                    results.extend(basic_results)

                    burst_results = await tester.run_burst_test(
                        users=users,
                        burst_size=300,
                        burst_interval=1.5
                    )
                    results.extend(burst_results)

                # Calculate summary
                summary = tester.calculate_summary(results, scenario)

                load_test_results = {
                    "success": True,
                    "scenario": scenario,
                    "summary": summary.__dict__ if hasattr(summary, '__dict__') else summary,
                    "total_requests": len(results),
                    "timestamp": datetime.now().isoformat()
                }

                print("✅ Load tests completed successfully")
                print(f"   Total requests: {len(results)}")
                print(f"   Rate limited: {summary.rate_limit_hit_rate:.1f}%")
                print(f"   Average response time: {summary.average_response_time:.0f}ms")

                return load_test_results

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "scenario": scenario,
                "timestamp": datetime.now().isoformat()
            }

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        print("\n📊 Generating summary report...")

        health_ok = self.test_results.get("health_check", {}).get("healthy", False)
        postman_ok = self.test_results.get("postman_tests", {}).get("success", False)
        load_test_ok = self.test_results.get("load_tests", {}).get("success", False)

        # Extract key metrics
        summary = {
            "overall_success": health_ok and postman_ok and load_test_ok,
            "health_check": {
                "passed": health_ok,
                "details": self.test_results.get("health_check", {})
            },
            "postman_tests": {
                "passed": postman_ok,
                "details": self.test_results.get("postman_tests", {})
            },
            "load_tests": {
                "passed": load_test_ok,
                "details": self.test_results.get("load_tests", {})
            },
            "recommendations": []
        }

        # Generate recommendations
        if not health_ok:
            summary["recommendations"].append("❌ API server is not responding - check if server is running")

        if not postman_ok:
            summary["recommendations"].append("❌ Postman tests failed - check rate limiting endpoints")

        if not load_test_ok:
            summary["recommendations"].append("❌ Load tests failed - check rate limiting configuration")

        if health_ok and postman_ok and load_test_ok:
            # Check load test metrics
            load_test_data = self.test_results.get("load_tests", {}).get("details", {})
            if load_test_data.get("rate_limit_hit_rate", 0) == 0:
                summary["recommendations"].append("⚠️  Rate limiting may not be working - no requests were rate limited")

            if load_test_data.get("error_rate", 0) > 10:
                summary["recommendations"].append("⚠️  High error rate detected - check rate limiting configuration")

            if load_test_data.get("average_response_time", 0) > 2000:
                summary["recommendations"].append("⚠️  High response times - rate limiting may be too restrictive")

        return summary

    def save_comprehensive_report(self, filename: str = None) -> None:
        """Save comprehensive test report"""
        if filename is None:
            filename = f"comprehensive_rate_limiting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            "test_run_info": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "test_type": "comprehensive_rate_limiting"
            },
            "test_results": self.test_results,
            "summary": self.generate_summary_report()
        }

        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Comprehensive report saved to: {report_path}")

    async def run_all_tests(self, load_scenario: str = "comprehensive") -> bool:
        """Run all tests and return overall success"""
        print("🚀 Starting comprehensive rate limiting test suite")
        print("=" * 60)

        # 1. Health check
        self.test_results["health_check"] = self.run_health_check()

        if not self.test_results["health_check"]["healthy"]:
            print("❌ Health check failed - aborting remaining tests")
            return False

        # 2. Postman tests
        self.test_results["postman_tests"] = self.run_postman_tests()

        # 3. Load tests
        self.test_results["load_tests"] = await self.run_load_tests(load_scenario)

        # 4. Generate summary
        self.test_results["summary"] = self.generate_summary_report()

        # Print final results
        summary = self.test_results["summary"]
        print(f"\n🎯 Final Results")
        print("=" * 30)
        print(f"Overall Success: {'✅' if summary['overall_success'] else '❌'}")
        print(f"Health Check: {'✅' if summary['health_check']['passed'] else '❌'}")
        print(f"Postman Tests: {'✅' if summary['postman_tests']['passed'] else '❌'}")
        print(f"Load Tests: {'✅' if summary['load_tests']['passed'] else '❌'}")

        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   {rec}")

        # Save report
        self.save_comprehensive_report()

        return summary["overall_success"]

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Comprehensive rate limiting test suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for API")
    parser.add_argument("--scenario", choices=["basic", "burst", "comprehensive"],
                       default="comprehensive", help="Load test scenario")
    parser.add_argument("--postman-only", action="store_true", help="Run only Postman tests")
    parser.add_argument("--load-test-only", action="store_true", help="Run only load tests")
    parser.add_argument("--health-only", action="store_true", help="Run only health check")
    parser.add_argument("--output", help="Save report to custom filename")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    args = parser.parse_args()

    tester = ComprehensiveRateLimitingTester(args.url)

    try:
        success = True

        if args.health_only:
            tester.test_results["health_check"] = tester.run_health_check()
            success = tester.test_results["health_check"]["healthy"]

        elif args.postman_only:
            tester.test_results["postman_tests"] = tester.run_postman_tests()
            success = tester.test_results["postman_tests"]["success"]

        elif args.load_test_only:
            tester.test_results["load_tests"] = await tester.run_load_tests(args.scenario)
            success = tester.test_results["load_tests"]["success"]

        else:
            # Run all tests
            success = await tester.run_all_tests(args.scenario)

        # Save report if custom filename provided
        if args.output:
            tester.save_comprehensive_report(args.output)

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))