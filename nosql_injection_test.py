#!/usr/bin/env python3
"""
NoSQL Injection Security Test Suite
Tests for injection vulnerabilities in database queries
"""

import asyncio
import json
import aiohttp
import time
from typing import List, Dict, Any

class NoSQLInjectionTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []

        # NoSQL injection payloads
        self.injection_payloads = [
            # Basic injection attempts
            {"$ne": None},
            {"$gt": ""},
            {"$where": "sleep(1000)"},
            {"$regex": ".*"},

            # JavaScript injection
            {"$where": "function() { return true; }"},
            {"$where": "return this.password == this.password"},
            {"$where": "return Date.now() > 0"},

            # Boolean-based injection
            {"$or": [{"username": {"$ne": None}}, {"password": {"$ne": None}}]},
            {"$and": [{"$where": "return true"}]},

            # Command injection
            {"$cmd": "sleep"},
            {"$expr": {"$gt": [{"$strLenCP": ""}, 0]}},

            # Array-based injection
            [{"$ne": None}],
            [{"$gt": ""}, {"$lt": "ZZZZ"}],

            # nested injection
            {"user": {"$ne": None}, "pass": {"$ne": None}},

            # Comment injection
            {"$comment": "injection test"},

            # Operator abuse
            {"$exists": True},
            {"$type": "string"},
            {"$mod": [2, 0]},

            # Advanced payloads
            {"$where": "this.password.match(/.*/)"},
            {"$where": "function() { for(var i=0;i<10;i++) { } return true; }"},
        ]

        # Test endpoints that might be vulnerable
        self.test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/",
            "/api/v1/assessments/",
            "/api/v1/responses/",
            "/api/v1/teams/",
            "/api/v1/analytics/",
        ]

    async def test_endpoint_injection(self, session: aiohttp.ClientSession, endpoint: str, payload: Dict) -> Dict[str, Any]:
        """Test a single endpoint with injection payload"""
        test_result = {
            "endpoint": endpoint,
            "payload": payload,
            "method": None,
            "status_code": None,
            "response_time": None,
            "response_size": None,
            "indicators": [],
            "vulnerable": False
        }

        try:
            start_time = time.time()

            # Test POST request with injection payload
            async with session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                test_result["method"] = "POST"
                test_result["status_code"] = response.status
                test_result["response_time"] = time.time() - start_time

                content = await response.text()
                test_result["response_size"] = len(content)

                # Check for injection success indicators
                await self.check_injection_indicators(test_result, content, response)

        except Exception as e:
            test_result["error"] = str(e)

        return test_result

    async def check_injection_indicators(self, test_result: Dict, content: str, response: aiohttp.ClientResponse):
        """Check for indicators of successful injection"""
        indicators = []

        # Time-based indicators (response took unusually long)
        if test_result["response_time"] and test_result["response_time"] > 5:
            indicators.append("slow_response")

        # Status code indicators
        if response.status == 200:
            indicators.append("success_response")
        elif response.status == 500:
            indicators.append("server_error")

        # Content indicators
        content_lower = content.lower()

        # Database error messages
        db_errors = [
            "mongodb", "nosql", "bson", "document", "collection",
            "invalid query", "syntax error", "timeout", "exception"
        ]

        for error in db_errors:
            if error in content_lower:
                indicators.append(f"db_error_{error}")

        # Success indicators (returned more data than expected)
        try:
            data = json.loads(content)
            if isinstance(data, list) and len(data) > 100:
                indicators.append("large_data_response")
            elif isinstance(data, dict) and "data" in data and len(str(data)) > 10000:
                indicators.append("extensive_data")
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            pass

        # Authentication bypass indicators
        if "token" in content_lower or "authenticated" in content_lower:
            indicators.append("auth_response")

        test_result["indicators"] = indicators

        # Determine vulnerability based on indicators
        critical_indicators = ["large_data_response", "auth_response", "slow_response"]
        if any(indicator in indicators for indicator in critical_indicators):
            test_result["vulnerable"] = True

    async def run_injection_tests(self) -> List[Dict[str, Any]]:
        """Run comprehensive NoSQL injection tests"""
        print("🔍 Starting NoSQL Injection Security Tests...")

        async with aiohttp.ClientSession() as session:
            tasks = []

            for endpoint in self.test_endpoints:
                for payload in self.injection_payloads:
                    task = self.test_endpoint_injection(session, endpoint, payload)
                    tasks.append(task)

            print(f"📊 Testing {len(self.test_endpoints)} endpoints with {len(self.injection_payloads)} payloads each...")
            print(f"🎯 Total tests: {len(tasks)}")

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and collect valid results
            valid_results = []
            for result in results:
                if isinstance(result, dict) and not isinstance(result, Exception):
                    valid_results.append(result)

            self.results = valid_results
            return valid_results

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security test report"""
        if not self.results:
            return {"error": "No test results available"}

        vulnerable_tests = [r for r in self.results if r.get("vulnerable", False)]
        total_tests = len(self.results)

        # Group by endpoint
        endpoint_vulnerabilities = {}
        for result in vulnerable_tests:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_vulnerabilities:
                endpoint_vulnerabilities[endpoint] = []
            endpoint_vulnerabilities[endpoint].append(result)

        # Most dangerous payloads
        payload_danger = {}
        for result in vulnerable_tests:
            payload_str = str(result["payload"])
            if payload_str not in payload_danger:
                payload_danger[payload_str] = 0
            payload_danger[payload_str] += 1

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "vulnerabilities_found": len(vulnerable_tests),
                "vulnerability_rate": f"{(len(vulnerable_tests)/total_tests)*100:.2f}%",
                "endpoints_tested": len(self.test_endpoints),
                "vulnerable_endpoints": len(endpoint_vulnerabilities)
            },
            "vulnerable_endpoints": endpoint_vulnerabilities,
            "dangerous_payloads": dict(sorted(payload_danger.items(), key=lambda x: x[1], reverse=True)[:10]),
            "recommendations": []
        }

        # Generate recommendations
        if len(vulnerable_tests) > 0:
            report["recommendations"] = [
                "Implement input validation and sanitization for all user inputs",
                "Use parameterized queries or ORM methods instead of raw queries",
                "Implement rate limiting to prevent time-based injection attacks",
                "Regular security testing and code reviews",
                "Update database drivers and libraries to latest versions",
                "Implement proper error handling to prevent information disclosure"
            ]
        else:
            report["recommendations"] = [
                "Continue regular security testing",
                "Monitor for new vulnerability patterns",
                "Maintain current security practices"
            ]

        return report

async def main():
    """Main execution function"""
    tester = NoSQLInjectionTester()

    try:
        # Run injection tests
        results = await tester.run_injection_tests()

        # Generate report
        report = tester.generate_report()

        # Display results
        print("\n" + "="*60)
        print("🔍 NOSQL INJECTION SECURITY TEST REPORT")
        print("="*60)

        summary = report["test_summary"]
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"🚨 Vulnerabilities Found: {summary['vulnerabilities_found']}")
        print(f"📈 Vulnerability Rate: {summary['vulnerability_rate']}")
        print(f"🎯 Endpoints Tested: {summary['endpoints_tested']}")
        print(f"⚠️  Vulnerable Endpoints: {summary['vulnerable_endpoints']}")

        if summary["vulnerabilities_found"] > 0:
            print("\n🚨 VULNERABLE ENDPOINTS:")
            for endpoint, vulns in report["vulnerable_endpoints"].items():
                print(f"\n📍 {endpoint} ({len(vulns)} vulnerabilities)")

            print("\n🔥 MOST DANGEROUS PAYLOADS:")
            for payload, count in list(report["dangerous_payloads"].items())[:5]:
                print(f"  💀 {payload} (worked {count} times)")

        print("\n💡 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"  ✓ {rec}")

        # Save detailed report
        with open("/Users/sheriftito/Downloads/psychsync/nosql_injection_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: nosql_injection_report.json")

    except Exception as e:
        print(f"❌ Error running tests: {e}")

if __name__ == "__main__":
    asyncio.run(main())
